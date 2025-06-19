# scripts/main_gradio_app.py
import gradio as gr
import os
import sys
import threading
import subprocess
import time
import json
from pathlib import Path
import traceback

# --- Robust Path Setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
MODULES_PATH = os.path.join(PROJECT_ROOT, 'modules')
SCRIPTS_PATH = os.path.join(PROJECT_ROOT, 'scripts')

# Ensure paths are set up early for anxlight_version import
sys.path.insert(0, SCRIPTS_PATH) # For direct import of anxlight_version from scripts/
if SCRIPT_DIR not in sys.path: # SCRIPT_DIR is scripts/
    sys.path.insert(0, SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(1, PROJECT_ROOT) # PROJECT_ROOT
if MODULES_PATH not in sys.path: # modules/
    sys.path.insert(0, MODULES_PATH)

try:
    from anxlight_version import (
        MAIN_GRADIO_APP_VERSION, # Changed from MAIN_APP_VERSION
        LAUNCH_PY_VERSION,       # Changed from LAUNCH_SCRIPT_VERSION
        ANXLIGHT_OVERALL_SYSTEM_VERSION,
        PRE_FLIGHT_SETUP_PY_VERSION # For display
    )
    APP_DISPLAY_VERSION = f"AnxLight Gradio App v{MAIN_GRADIO_APP_VERSION}"
    SYSTEM_DISPLAY_VERSION = f"AnxLight System v{ANXLIGHT_OVERALL_SYSTEM_VERSION}"
    print(f"--- {APP_DISPLAY_VERSION} (System: {SYSTEM_DISPLAY_VERSION}, Pre-Flight: v{PRE_FLIGHT_SETUP_PY_VERSION}) ---")
except ImportError as e_ver:
    print(f"[CRITICAL] Failed to import versions from anxlight_version.py: {e_ver}")
    APP_DISPLAY_VERSION = "AnxLight Gradio App v?.?.? (Version File Error)"
    LAUNCH_PY_VERSION = "unknown" # Fallback
    PRE_FLIGHT_SETUP_PY_VERSION = "unknown"

# --- Dummy classes (can remain for non-critical fallbacks) ---
class _DummyDataModule:
    sd15_model_data = {"ERROR: Module Load Failed": {}}
    sd15_vae_data = {}
    sd15_controlnet_data = {}
    sdxl_model_data = {"ERROR: Module Load Failed": {}}
    sdxl_vae_data = {}
    sdxl_controlnet_data = {}

class _DummyLoraDataModule:
    lora_data = {"sd15_loras": {}, "sdxl_loras": {}}

class _DummyWebUIUtilsModule:
    def update_current_webui(self, webui_name):
        print(f"[_DummyWebUIUtilsModule] update_current_webui called for {webui_name} - REAL MODULE NOT LOADED")
    def get_webui_asset_path(self, webui_name, asset_type, asset_filename=""): # New dummy method
        print(f"[_DummyWebUIUtilsModule] get_webui_asset_path for {webui_name}, {asset_type} - REAL MODULE NOT LOADED")
        # Return a generic path for dummy purposes
        return os.path.join(PROJECT_ROOT, "models", asset_type, asset_filename)


sd15_data = _DummyDataModule()
sdxl_data = _DummyDataModule()
lora_data = _DummyLoraDataModule()
json_utils = None
webui_utils = _DummyWebUIUtilsModule()
manager_utils = None # For modules.Manager

print(f"[DEBUG main_gradio_app] SCRIPT_DIR: {SCRIPT_DIR}")
print(f"[DEBUG main_gradio_app] PROJECT_ROOT: {PROJECT_ROOT}")
print(f"[DEBUG main_gradio_app] MODULES_PATH: {MODULES_PATH}")
print(f"[DEBUG main_gradio_app] Initial sys.path: {sys.path}")

try:
    # Assuming data modules are in PROJECT_ROOT/scripts/data/ as per plan
    # Adjust if they remain in scripts/ or move fully into a 'data' package
    DATA_MODULE_PATH = os.path.join(SCRIPTS_PATH, 'data')
    if DATA_MODULE_PATH not in sys.path:
        sys.path.insert(0, DATA_MODULE_PATH)
    print(f"[DEBUG main_gradio_app] Attempting data module import from: {DATA_MODULE_PATH}, sys.path: {sys.path}")

    from sd15_data import sd15_model_data, sd15_vae_data, sd15_controlnet_data
    sd15_data.sd15_model_data = sd15_model_data
    sd15_data.sd15_vae_data = sd15_vae_data
    sd15_data.sd15_controlnet_data = sd15_controlnet_data

    from sdxl_data import sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data
    sdxl_data.sdxl_model_data = sdxl_model_data
    sdxl_data.sdxl_vae_data = sdxl_vae_data
    sdxl_data.sdxl_controlnet_data = sdxl_controlnet_data
    
    from lora_data import lora_data as lora_data_dict
    lora_data.lora_data = lora_data_dict
    print("Successfully imported real data modules.")

except ImportError as e:
    print(f"Warning: Error importing data modules: {e}. Using dummy data.")
    # Fallback to trying to load from scripts/ if not in scripts/data/
    try:
        print("[DEBUG main_gradio_app] Retrying data module import from scripts/ directly.")
        # Remove DATA_MODULE_PATH if it was added, to avoid conflict if files are in scripts/
        if DATA_MODULE_PATH in sys.path: sys.path.remove(DATA_MODULE_PATH)
        # Re-add SCRIPT_DIR (scripts/) if it got removed somehow, to ensure it's checked
        if SCRIPT_DIR not in sys.path: sys.path.insert(0, SCRIPT_DIR)
        
        from _models_data import sd15_model_data, sd15_vae_data, sd15_controlnet_data # Assuming original names if in scripts/
        sd15_data.sd15_model_data = sd15_model_data
        sd15_data.sd15_vae_data = sd15_vae_data
        sd15_data.sd15_controlnet_data = sd15_controlnet_data

        from _xl_models_data import sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data # Assuming original names
        sdxl_data.sdxl_model_data = sdxl_model_data
        sdxl_data.sdxl_vae_data = sdxl_vae_data
        sdxl_data.sdxl_controlnet_data = sdxl_controlnet_data
        
        # Assuming lora_data.py might exist in scripts/ too
        # from lora_data import lora_data as lora_data_dict # This was likely a combined file before
        # lora_data.lora_data = lora_data_dict
        print("Successfully imported real data modules from scripts/ (fallback).")
    except ImportError as e_fallback:
        print(f"FATAL: Error importing data modules (fallback attempt from scripts/ failed): {e_fallback}")
        print("Using dummy data. Asset selection will be limited/non-functional.")


try:
    from modules import json_utils as real_json_utils, webui_utils as real_webui_utils, Manager as real_manager_utils
    json_utils = real_json_utils
    webui_utils = real_webui_utils
    manager_utils = real_manager_utils # For downloading assets
    print("Successfully imported real backend utility modules (json_utils, webui_utils, Manager).")
except ImportError as e:
    print(f"FATAL: Error importing backend utility modules: {e}. Using dummy placeholders where possible.")
    if not isinstance(webui_utils, _DummyWebUIUtilsModule): webui_utils = _DummyWebUIUtilsModule() # Ensure it's a dummy if real failed
    # json_utils and manager_utils being None will be handled in launch_anxlight_main_process

# --- UI Lists & Data (largely unchanged) ---
WEBUI_CHOICES = ["A1111", "ComfyUI", "Forge"] # Simplified for v3 initial, Classic/Reforge/SD-UX might be added later
SD_VERSION_CHOICES = ["SD1.5", "SDXL"]
THEME_CHOICES = ["Default", "anxety", "blue", "green", "peach", "pink", "red", "yellow"] # Gradio's default themes
INPAINTING_FILTER_CHOICES = ["Show All Models", "Inpainting Models Only", "No Inpainting Models"]

WEBUI_DEFAULT_ARGS = {
    'A1111':   "--xformers --no-half-vae",
    'ComfyUI': "--preview-method auto", # Changed from --use-sage-attention --dont-print-server
    'Forge':   "--xformers --cuda-stream --pin-shared-memory",
}

# SETTINGS_KEYS might need review based on what launch.py actually needs from config for v3
SETTINGS_KEYS = [
    'XL_models', 'model', 'model_num', 'inpainting_model', 'vae', 'vae_num',
    # 'latest_webui', 'latest_extensions', # These are less relevant if pre_flight handles full setup
    'check_custom_nodes_deps', 'change_webui', 'detailed_download',
    'controlnet', 'controlnet_num', 'commit_hash', # commit_hash for WebUI might be used by pre_flight
    'civitai_token', 'huggingface_token', 'zrok_token', 'ngrok_token', 'commandline_arguments', 'theme_accent',
    # 'empowerment', 'empowerment_output', # May remove if not used
    # Urls for individual file downloads might be less used if Manager handles assets based on names
    # 'Model_url', 'Vae_url', 'LoRA_url', 'Embedding_url', 'Extensions_url', 'ADetailer_url',
    # 'custom_file_urls'
]


def get_asset_choices(sd_version, inpainting_filter_mode="Show All Models"):
    # This function remains largely the same, relying on the (now hopefully real) data modules
    models_data_source = sd15_data.sd15_model_data if sd_version == "SD1.5" else sdxl_data.sdxl_model_data
    filtered_models_keys = [name for name, data in models_data_source.items() if name != "ERROR: Module Load Failed" and (
                            (inpainting_filter_mode == "Show All Models") or
                            (inpainting_filter_mode == "Inpainting Models Only" and data.get("inpainting", False)) or
                            (inpainting_filter_mode == "No Inpainting Models" and not data.get("inpainting", False)))]
    models = filtered_models_keys
    if sd_version == "SD1.5":
        vaes = [name for name in sd15_data.sd15_vae_data.keys() if name != "ERROR: Module Load Failed"]
        controlnets = [name for name in sd15_data.sd15_controlnet_data.keys() if name != "ERROR: Module Load Failed"]
        loras = [name for name in lora_data.lora_data.get("sd15_loras", {}).keys() if name != "ERROR: Module Load Failed"]
    elif sd_version == "SDXL":
        vaes = [name for name in sdxl_data.sdxl_vae_data.keys() if name != "ERROR: Module Load Failed"]
        controlnets = [name for name in sdxl_data.sdxl_controlnet_data.keys() if name != "ERROR: Module Load Failed"]
        loras = [name for name in lora_data.lora_data.get("sdxl_loras", {}).keys() if name != "ERROR: Module Load Failed"]
    else:
        vaes, controlnets, loras = [], [], []
    return models, vaes, controlnets, loras

# update_all_ui_elements, save_keys_to_file_fn, load_keys_from_file_fn remain similar
def update_all_ui_elements(sd_version_selected, inpainting_filter_selected, webui_selected):
    models, vaes, controlnets, loras = get_asset_choices(sd_version_selected, inpainting_filter_selected)
    default_args = WEBUI_DEFAULT_ARGS.get(webui_selected, "")
    is_comfy = (webui_selected == 'ComfyUI')
    update_ext_visible = not is_comfy # Placeholder, actual visibility might change based on v3
    check_nodes_visible = is_comfy
    theme_accent_visible = not is_comfy # Assuming themes mostly apply to non-Comfy Gradio wrappers
    
    # Preserve current theme if theme dropdown is visible, otherwise default
    current_theme_value = THEME_CHOICES[0] # Default to "Default"
    # Accessing global UI elements by string name is risky. Better to pass them if needed.
    # For now, this approach is fragile. If 'theme_accent_dd' is not in globals() or has no 'value', it'll error.
    # This part of UI update logic might need to be rethought if theme_accent_dd is not always available.
    # A safer way is to have the Gradio controls themselves passed into this function if their values are needed.
    # However, for setting output, gr.update() is fine.
    
    return (gr.update(choices=models, value=[] if models else None), 
            gr.update(choices=vaes, value=[] if vaes else None), 
            gr.update(choices=controlnets, value=[] if controlnets else None),
            gr.update(choices=loras, value=[] if loras else None), 
            gr.update(value=default_args), 
            gr.update(visible=update_ext_visible),
            gr.update(visible=check_nodes_visible), 
            gr.update(visible=theme_accent_visible, value=current_theme_value if theme_accent_visible else None))

def save_keys_to_file_fn(civitai, hf, ngrok, zrok):
    keys_data = {"civitai_token": civitai, "huggingface_token": hf, "ngrok_token": ngrok, "zrok_token": zrok}
    temp_file_path = "anxlight_keys.json" # This saves to CWD, which is fine for a temp download
    try:
        with open(temp_file_path, 'w') as f: json.dump(keys_data, f, indent=2)
        gr.Info("Keys saved! Your browser should prompt a download.")
        return gr.update(value=temp_file_path, visible=True) # For gr.File component to offer download
    except Exception as e:
        gr.Error(f"Failed to save keys: {e}")
        return gr.update(value=None, visible=False)

def load_keys_from_file_fn(file_obj):
    if file_obj is None: return gr.update(), gr.update(), gr.update(), gr.update()
    try:
        with open(file_obj.name, 'r') as f: keys_data = json.load(f)
        gr.Info("Keys loaded successfully!")
        return (gr.update(value=keys_data.get("civitai_token", "")), 
                gr.update(value=keys_data.get("huggingface_token", "")),
                gr.update(value=keys_data.get("ngrok_token", "")), 
                gr.update(value=keys_data.get("zrok_token", "")))
    except Exception as e:
        gr.Error(f"Error loading keys: {e}. Make sure it's a valid JSON file.")
        return gr.update(), gr.update(), gr.update(), gr.update()


def _execute_backend_script(script_path, script_version, log_file_name_base, ui_log_prefix, detailed_logging_enabled, log_session_dir, current_log_output_list):
    # This helper function is still useful for launch.py
    log_output_list = current_log_output_list
    full_log_file_path = None
    script_success = False

    if detailed_logging_enabled and log_session_dir:
        full_log_file_path = os.path.join(log_session_dir, log_file_name_base)
        log_output_list.append(f"Detailed log for this step will be at: {full_log_file_path}\n")
        yield "".join(log_output_list)
    
    log_output_list.append(f"Executing: {sys.executable} {script_path} (Target Version: v{script_version})...\n")
    yield "".join(log_output_list)
    
    process = None
    log_file = None
    try:
        process_env = os.environ.copy()
        existing_pythonpath = process_env.get('PYTHONPATH', '')
        paths_to_prepend = [MODULES_PATH, PROJECT_ROOT, SCRIPTS_PATH] 
        new_pythonpath_parts = paths_to_prepend
        if existing_pythonpath: new_pythonpath_parts.extend(existing_pythonpath.split(os.pathsep))
        seen_paths = set()
        unique_pythonpath_parts = [p for p in new_pythonpath_parts if not (p in seen_paths or seen_paths.add(p))]
        process_env['PYTHONPATH'] = os.pathsep.join(unique_pythonpath_parts)
        
        log_output_list.append(f"{ui_log_prefix} Subprocess PYTHONPATH: {process_env['PYTHONPATH']}\n")
        yield "".join(log_output_list)

        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True,
            env=process_env, cwd=PROJECT_ROOT
        )

        if full_log_file_path:
            try: log_file = open(full_log_file_path, 'a', encoding='utf-8')
            except Exception as e_file:
                log_output_list.append(f"Warning: Could not open log file {full_log_file_path}: {e_file}\n")
                yield "".join(log_output_list)

        for line in process.stdout:
            line_stripped = line.strip()
            log_output_list.append(f"{ui_log_prefix} {line_stripped}\n")
            if log_file:
                try: log_file.write(line)
                except Exception as e_write:
                    print(f"Error writing to log file {full_log_file_path}: {e_write}")
                    if log_file: log_file.close(); log_file = None
            yield "".join(log_output_list)
        
        process.wait()
        script_success = (process.returncode == 0)
        log_output_list.append(f"{ui_log_prefix} Script finished with return code {process.returncode}.\n")
        yield "".join(log_output_list)

    except FileNotFoundError:
        log_output_list.append(f"{ui_log_prefix} Error: Script not found at {script_path}.\n")
    except Exception as e:
        log_output_list.append(f"{ui_log_prefix} An unexpected error occurred: {type(e).__name__}: {e}\nTraceback: {traceback.format_exc()}\n")
    finally:
        if log_file: log_file.close()
        if process and process.poll() is None:
            log_output_list.append(f"{ui_log_prefix} Terminating script {script_path}.\n"); yield "".join(log_output_list)
            process.terminate()
            try: process.wait(timeout=5) # Wait for termination
            except subprocess.TimeoutExpired:
                 process.kill(); log_output_list.append(f"{ui_log_prefix} Script force-killed.\n"); yield "".join(log_output_list)
    
    yield "SCRIPT_EXECUTION_SUCCESS" if script_success else "SCRIPT_EXECUTION_FAILURE"


def download_selected_asset(asset_name, asset_type, sd_version, webui_choice, log_output_list, hf_token_val, civitai_token_val):
    """
    Downloads a single selected asset.
    Uses webui_utils to determine target path and manager_utils for downloading.
    """
    if not manager_utils or not webui_utils or isinstance(webui_utils, _DummyWebUIUtilsModule):
        log_output_list.append(f"Warning: Download utilities (Manager/WebUIUtils) not fully loaded. Cannot download {asset_type} '{asset_name}'.\n")
        return False

    data_source = None
    if asset_type == "model": data_source = sd15_data.sd15_model_data if sd_version == "SD1.5" else sdxl_data.sdxl_model_data
    elif asset_type == "vae": data_source = sd15_data.sd15_vae_data if sd_version == "SD1.5" else sdxl_data.sdxl_vae_data
    elif asset_type == "lora": data_source = lora_data.lora_data.get("sd15_loras" if sd_version == "SD1.5" else "sdxl_loras", {})
    elif asset_type == "controlnet": data_source = sd15_data.sd15_controlnet_data if sd_version == "SD1.5" else sdxl_data.sdxl_controlnet_data
    
    if not data_source or asset_name not in data_source:
        log_output_list.append(f"Warning: Metadata for {asset_type} '{asset_name}' not found. Cannot download.\n"); return False

    asset_info = data_source[asset_name]
    download_url = asset_info.get("url")
    filename_in_repo = asset_info.get("filename")
    
    if not download_url or not filename_in_repo:
        log_output_list.append(f"Warning: Download URL/filename missing for {asset_type} '{asset_name}'.\n"); return False

    asset_type_plural_map = {"model": "models", "vae": "vaes", "lora": "loras", "controlnet": "controlnet"}
    target_dir_type = asset_type_plural_map.get(asset_type)
    if not target_dir_type:
        log_output_list.append(f"Warning: Unknown asset type '{asset_type}' for path. Cannot download '{asset_name}'.\n"); return False
        
    target_path_full = webui_utils.get_webui_asset_path(webui_choice, target_dir_type, filename_in_repo)
    target_directory = os.path.dirname(target_path_full)
    
    log_output_list.append(f"Downloading {asset_type} '{asset_name}' from {download_url} to {target_path_full}...\n")
    try: os.makedirs(target_directory, exist_ok=True)
    except Exception as e_mkdir:
        log_output_list.append(f"Error creating dir {target_directory}: {e_mkdir}.\n"); return False

    # Prepare anxt_config_minimal for Manager.download_file
    anxt_config_minimal = {
        "WIDGETS": {
            "huggingface_token": hf_token_val,
            "civitai_token": civitai_token_val
        },
        "ENVIRONMENT": { # Manager might need some env paths
            "home_path": os.environ.get('home_path', PROJECT_ROOT)
        }
    }

    try:
        # Assuming Manager.download_file(url, target_dir, target_filename, anxt_config, hf_token_override)
        # The anxt_config is for Manager to access tokens if needed.
        # Manager.py's download_file needs to be robust.
        success = manager_utils.download_file(download_url, target_directory, filename_in_repo, anxt_config=anxt_config_minimal)
        
        if success:
            log_output_list.append(f"Successfully downloaded {asset_type} '{asset_name}'.\n"); return True
        else:
            log_output_list.append(f"Failed to download {asset_type} '{asset_name}'. Manager returned failure.\n"); return False
    except Exception as e_dl:
        log_output_list.append(f"Error during download of {asset_type} '{asset_name}': {e_dl}\nTraceback: {traceback.format_exc()}\n"); return False


def launch_anxlight_main_process(
    webui_choice, sd_version, inpainting_models_filter_val,
    selected_models, selected_vaes, selected_controlnets, selected_loras,
    update_webui_val, update_extensions_val, check_custom_nodes_val, detailed_download_val,
    commit_hash_val, civitai_token_val, huggingface_token_val, zrok_token_val, ngrok_token_val,
    custom_args_val, theme_accent_val
):
    log_output_list = [f"--- {APP_DISPLAY_VERSION} Backend Process Initializing (System: {SYSTEM_DISPLAY_VERSION}) ---\n"]
    log_output_list.append(f"Pre-Flight Setup Script Version (expected by this app): v{PRE_FLIGHT_SETUP_PY_VERSION}\n") # Display expected pre-flight version
    yield "".join(log_output_list)

    if json_utils is None:
        log_output_list.append("FATAL: json_utils module not loaded. Config generation failed.\n"); yield "".join(log_output_list); return
    if webui_utils is None or isinstance(webui_utils, _DummyWebUIUtilsModule):
        log_output_list.append("Warning: webui_utils module not fully loaded. Asset path determination may be incorrect.\n")
    if manager_utils is None:
        log_output_list.append("Warning: manager_utils (Manager.py) not loaded. Asset downloads will be skipped/fail.\n")

    local_project_root = PROJECT_ROOT
    log_output_list.append(f"Project Root: {local_project_root}\n")
    
    log_session_dir = None
    if detailed_download_val:
        try:
            log_dir_base = os.path.join(local_project_root, 'logs') # Ensure logs dir is in project root
            log_session_dir = os.path.join(log_dir_base, f'session_{time.strftime("%Y%m%d-%H%M%S")}')
            os.makedirs(log_session_dir, exist_ok=True)
            log_output_list.append(f"Detailed logging enabled. Session logs will be in: {log_session_dir}\n")
        except Exception as e:
            log_output_list.append(f"Warning: Could not create log directory {log_session_dir}: {e}\n"); log_session_dir = None
    else:
        log_output_list.append("Detailed file logging is disabled.\n")
    yield "".join(log_output_list)

    log_output_list.append(f"\n--- Step 1: Verifying WebUI '{webui_choice}' Installation ---\n")
    log_output_list.append(f"NOTE: WebUI installation is handled by 'scripts/pre_flight_setup.py'. Assuming '{webui_choice}' is installed.\n")
    yield "".join(log_output_list) # Update UI

    log_output_list.append(f"\n--- Step 2: Downloading Selected Session Assets ---\n")
    yield "".join(log_output_list) # Update UI
    
    assets_to_process = [
        ("model", selected_models), ("vae", selected_vaes),
        ("controlnet", selected_controlnets), ("lora", selected_loras)
    ]
    overall_asset_download_success = True
    if manager_utils is None:
        log_output_list.append("Skipping all asset downloads as Manager module is not available.\n")
    else:
        for asset_type, asset_names_list in assets_to_process:
            if asset_names_list:
                for asset_name in asset_names_list:
                    if not download_selected_asset(asset_name, asset_type, sd_version, webui_choice, log_output_list, huggingface_token_val, civitai_token_val):
                        overall_asset_download_success = False 
                    yield "".join(log_output_list) # Update UI after each asset attempt
            else:
                log_output_list.append(f"No {asset_type}s selected.\n")
                yield "".join(log_output_list)
    
    if not overall_asset_download_success:
        log_output_list.append("Warning: One or more assets failed to download.\n")
    yield "".join(log_output_list)


    log_output_list.append(f"\n--- Step 3: Generating Configuration File ---\n")
    widgets_data = {}
    try:
        widgets_data['XL_models'] = (sd_version == "SDXL")
        widgets_data['model'] = selected_models[0] if selected_models else "none"
        widgets_data['model_num'] = ",".join(selected_models) if selected_models else ""
        widgets_data['inpainting_model'] = (inpainting_models_filter_val == "Inpainting Models Only")
        widgets_data['vae'] = selected_vaes[0] if selected_vaes else "none"
        widgets_data['vae_num'] = ",".join(selected_vaes) if selected_vaes else ""
        widgets_data['latest_webui'] = update_webui_val # Role of this flag might change with pre-flight
        widgets_data['latest_extensions'] = update_extensions_val # Role of this flag might change
        widgets_data['check_custom_nodes_deps'] = check_custom_nodes_val
        widgets_data['change_webui'] = webui_choice
        widgets_data['detailed_download'] = "on" if detailed_download_val else "off"
        widgets_data['controlnet'] = selected_controlnets[0] if selected_controlnets else "none"
        widgets_data['controlnet_num'] = ",".join(selected_controlnets) if selected_controlnets else ""
        widgets_data['commit_hash'] = commit_hash_val or ""
        widgets_data['civitai_token'] = civitai_token_val or ""
        widgets_data['huggingface_token'] = huggingface_token_val or ""
        widgets_data['zrok_token'] = zrok_token_val or ""
        widgets_data['ngrok_token'] = ngrok_token_val or ""
        widgets_data['commandline_arguments'] = custom_args_val or WEBUI_DEFAULT_ARGS.get(webui_choice, "")
        widgets_data['theme_accent'] = theme_accent_val
        widgets_data['anxlight_selected_models_list'] = selected_models or [] # For launch.py if it needs full list
        widgets_data['anxlight_selected_vaes_list'] = selected_vaes or []
        widgets_data['anxlight_selected_controlnets_list'] = selected_controlnets or []
        widgets_data['anxlight_selected_loras_list'] = selected_loras or []

        environment_data = {}
        is_colab_env = 'COLAB_GPU' in os.environ
        environment_data['env_name'] = "Google Colab" if is_colab_env else "AnxLight_Generic_Platform"
        environment_data['lang'] = "en"
        environment_data['home_path'] = os.environ.get('home_path', PROJECT_ROOT) # Should be set by notebook
        environment_data['scr_path'] = os.environ.get('scr_path', PROJECT_ROOT)   # Should be set by notebook
        environment_data['settings_path'] = os.environ.get('settings_path', os.path.join(environment_data['home_path'], 'anxlight_config.json'))
        environment_data['venv_path'] = os.environ.get('venv_path', os.path.join(PROJECT_ROOT, VENV_NAME)) # VENV_NAME from pre_flight
        current_branch_name = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=PROJECT_ROOT).strip().decode('utf-8')
        environment_data['fork'] = "drf0rk/AnxLight"; environment_data['branch'] = current_branch_name
        environment_data['start_timer'] = int(time.time() - 5); environment_data['public_ip'] = ""

        anxlight_config = {"WIDGETS": widgets_data, "ENVIRONMENT": environment_data, "UI_SELECTION": {"webui_choice": webui_choice}}
        log_output_list.append("Configuration dictionary constructed.\n")
    except Exception as e:
        log_output_list.append(f"Error constructing config: {e}\nTraceback: {traceback.format_exc()}\n"); yield "".join(log_output_list); return

    config_file_path = Path(environment_data['settings_path'])
    try:
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, 'w') as f: json.dump(anxlight_config, f, indent=4)
        log_output_list.append(f"Config saved to: {config_file_path}\n")
    except Exception as e:
        log_output_list.append(f"Error saving config to {config_file_path}: {e}\nTraceback: {traceback.format_exc()}\n"); yield "".join(log_output_list); return
    yield "".join(log_output_list)

    log_output_list.append(f"\n--- Step 4: Updating WebUI Paths in Config ---\n")
    try:
        if webui_utils and not isinstance(webui_utils, _DummyWebUIUtilsModule):
             webui_utils.update_current_webui(webui_choice) 
             log_output_list.append(f"Called webui_utils.update_current_webui for '{webui_choice}'.\n")
        else:
            log_output_list.append(f"Warning: webui_utils dummy/not loaded. update_current_webui for '{webui_choice}' skipped/dummy.\n")
            if webui_utils: webui_utils.update_current_webui(webui_choice)
    except Exception as e:
        log_output_list.append(f"Error calling webui_utils.update_current_webui: {e}\nTraceback: {traceback.format_exc()}\n")
    yield "".join(log_output_list)
        
    log_output_list.append(f"\n--- Step 5: Initiating Launch Script ---\n")
    launch_script_path = os.path.join(environment_data['scr_path'], 'scripts', 'launch.py')
    log_output_list.append(f"Attempting to run launch script (v{LAUNCH_PY_VERSION}): {launch_script_path}\n")
    yield "".join(log_output_list)
    
    launch_success = False
    for exec_status in _execute_backend_script(launch_script_path, LAUNCH_PY_VERSION, "launch.log", "[Launcher]", detailed_download_val, log_session_dir, log_output_list):
        if exec_status == "SCRIPT_EXECUTION_SUCCESS": launch_success = True
        elif exec_status == "SCRIPT_EXECUTION_FAILURE": launch_success = False
        else: yield exec_status # This is a log chunk
    
    log_output_list.append(f"--- Launch script {'finished successfully' if launch_success else 'failed or status unclear'}. WebUI may be starting. ---\n")
    yield "".join(log_output_list)

# --- Gradio UI Definition ---
with gr.Blocks(css=".gradio-container {max-width: 90% !important; margin: auto !important;}") as demo:
    gr.Markdown(f"# AnxLight Launcher ({APP_DISPLAY_VERSION})")
    
    _initial_models, _initial_vaes, _initial_controlnets, _initial_loras = get_asset_choices(SD_VERSION_CHOICES[0], INPAINTING_FILTER_CHOICES[0])
    _initial_webui = WEBUI_CHOICES[0]
    _initial_is_comfy = (_initial_webui == 'ComfyUI')

    with gr.Tabs():
        with gr.TabItem("Session Configuration"): # Renamed tab
            gr.Markdown("## Main Configuration")
            with gr.Row():
                webui_choice_dd = gr.Dropdown(label="Select WebUI", choices=WEBUI_CHOICES, value=_initial_webui, interactive=True)
                sd_version_rb = gr.Radio(label="Model Version", choices=SD_VERSION_CHOICES, value=SD_VERSION_CHOICES[0], interactive=True)
            
            inpainting_filter_rg = gr.Radio(label="Model Type Filter", info="Filters the 'Select Models' list below.", choices=INPAINTING_FILTER_CHOICES, value=INPAINTING_FILTER_CHOICES[0], interactive=True)
            
            with gr.Row(equal_height=False):
                update_webui_chk = gr.Checkbox(label="Update WebUI Components (Daily)", value=False, info="If pre-flight setup allows for daily/minor updates of WebUI components (not full reinstall).")
                update_extensions_chk = gr.Checkbox(label="Update Extensions (Daily)", value=False, info="If pre-flight setup allows for daily/minor updates of extensions.", visible=not _initial_is_comfy)
                check_custom_nodes_deps_chk = gr.Checkbox(label="Check ComfyUI Nodes Deps (on Launch)", value=True, visible=_initial_is_comfy, info="For ComfyUI, check custom node dependencies during launch process.")
                detailed_download_chk = gr.Checkbox(label="Detailed Session Log", value=True, info="Enable detailed UI and file logging for this session's processes.")

            gr.Markdown("### Assets Selection (for this session)")
            with gr.Row():
                models_cbg = gr.CheckboxGroup(label="Select Models", choices=_initial_models, value=[])
                vaes_cbg = gr.CheckboxGroup(label="Select VAEs", choices=_initial_vaes, value=[])
            with gr.Row():
                controlnets_cbg = gr.CheckboxGroup(label="Select ControlNets", choices=_initial_controlnets, value=[])
                loras_cbg = gr.CheckboxGroup(label="Select LoRAs", choices=_initial_loras, value=[])

            gr.Markdown("### Advanced Options")
            commit_hash_tb = gr.Textbox(label="WebUI Commit Hash (For Pre-Flight Setup)", info="If pre-flight needs to install a specific WebUI version. Run Cell 1 after setting.", placeholder="e.g., a1b2c3d...")
            
            gr.Markdown("### Tokens & Access Keys")
            with gr.Row():
                civitai_token_tb = gr.Textbox(label="CivitAI API Key", type="password", placeholder="Optional")
                huggingface_token_tb = gr.Textbox(label="HuggingFace Token", type="password", placeholder="Optional for private HF assets")
            with gr.Row():
                ngrok_token_tb = gr.Textbox(label="NGROK Token", type="password", placeholder="Optional for NGROK tunnel")
                zrok_token_tb = gr.Textbox(label="Zrok Token", type="password", placeholder="Optional for Zrok tunnel")
            with gr.Row():
                save_keys_btn = gr.Button("Save Keys to File")
                download_keys_file_display = gr.File(label="Download Saved Keys", visible=False, interactive=False)
            load_keys_file_upload = gr.File(label="Load Keys from File", file_types=[".json"], scale=2)
            
            gr.Markdown("### Launch & UI Settings")
            custom_args_tb = gr.Textbox(label="Custom Launch Arguments for WebUI", value=WEBUI_DEFAULT_ARGS.get(_initial_webui, ""), placeholder="e.g., --xformers --no-half-vae")
            theme_accent_dd = gr.Dropdown(label="Launcher UI Theme Accent", choices=THEME_CHOICES, value=THEME_CHOICES[0], info="Select a visual theme.", visible=not _initial_is_comfy)

        with gr.TabItem("Launch & Live Log"):
            gr.Markdown("## Launch Controls")
            launch_button = gr.Button("Download Assets & Launch WebUI", variant="primary")
            live_log_ta = gr.Textbox(label="Live Log Output", lines=20, interactive=False, max_lines=50, show_copy_button=True)
            # download_session_logs_btn = gr.Button("Download Session Logs") # Add this later
            # session_log_file_display = gr.File(label="Download Session Log Archive", visible=False, interactive=False)

    event_inputs_master_filter = [sd_version_rb, inpainting_filter_rg, webui_choice_dd]
    event_outputs_master_filter = [
        models_cbg, vaes_cbg, controlnets_cbg, loras_cbg,
        custom_args_tb, 
        update_extensions_chk,
        check_custom_nodes_deps_chk,
        theme_accent_dd
    ]
    
    sd_version_rb.change(fn=update_all_ui_elements, inputs=event_inputs_master_filter, outputs=event_outputs_master_filter)
    inpainting_filter_rg.change(fn=update_all_ui_elements, inputs=event_inputs_master_filter, outputs=event_outputs_master_filter)
    webui_choice_dd.change(fn=update_all_ui_elements, inputs=event_inputs_master_filter, outputs=event_outputs_master_filter)
    
    save_keys_btn.click(
        fn=save_keys_to_file_fn, 
        inputs=[civitai_token_tb, huggingface_token_tb, ngrok_token_tb, zrok_token_tb],
        outputs=[download_keys_file_display]
    )
    load_keys_file_upload.upload(
        fn=load_keys_from_file_fn,
        inputs=[load_keys_file_upload],
        outputs=[civitai_token_tb, huggingface_token_tb, ngrok_token_tb, zrok_token_tb]
    )
    
    all_launch_inputs = [
        webui_choice_dd, sd_version_rb, inpainting_filter_rg,
        models_cbg, vaes_cbg, controlnets_cbg, loras_cbg,
        update_webui_chk, update_extensions_chk, check_custom_nodes_deps_chk, detailed_download_chk,
        commit_hash_tb, civitai_token_tb, huggingface_token_tb, zrok_token_tb, ngrok_token_tb,
        custom_args_tb, theme_accent_dd
    ]
    launch_button.click(fn=launch_anxlight_main_process, inputs=all_launch_inputs, outputs=live_log_ta)

if __name__ == "__main__":
    print(f"Launching Gradio App for AnxLight ({APP_DISPLAY_VERSION})...")
    demo.queue().launch(debug=True, share=os.environ.get("GRADIO_SHARE", "true").lower() == "true", prevent_thread_lock=True, show_error=True)