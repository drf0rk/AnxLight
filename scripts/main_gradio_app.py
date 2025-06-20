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
import importlib # For dynamic imports

# --- Robust Path Setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
MODULES_PATH = os.path.join(PROJECT_ROOT, 'modules')
SCRIPTS_PATH = os.path.join(PROJECT_ROOT, 'scripts')
DATA_MODULE_PATH = os.path.join(SCRIPTS_PATH, 'data')

# Ensure paths are set up early
for p in [DATA_MODULE_PATH, SCRIPTS_PATH, SCRIPT_DIR, PROJECT_ROOT, MODULES_PATH]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from anxlight_version import (
        MAIN_GRADIO_APP_VERSION, 
        LAUNCH_PY_VERSION,       
        ANXLIGHT_OVERALL_SYSTEM_VERSION,
        PRE_FLIGHT_SETUP_PY_VERSION 
    )
    APP_DISPLAY_VERSION = f"AnxLight Gradio App v{MAIN_GRADIO_APP_VERSION}"
    SYSTEM_DISPLAY_VERSION = f"AnxLight System v{ANXLIGHT_OVERALL_SYSTEM_VERSION}"
    print(f"--- {APP_DISPLAY_VERSION} (System: {SYSTEM_DISPLAY_VERSION}, Pre-Flight: v{PRE_FLIGHT_SETUP_PY_VERSION}) ---")
except ImportError as e_ver:
    print(f"[CRITICAL] Failed to import versions from anxlight_version.py: {e_ver}")
    APP_DISPLAY_VERSION = "AnxLight Gradio App v?.?.? (Version File Error)"
    LAUNCH_PY_VERSION = "unknown" 
    PRE_FLIGHT_SETUP_PY_VERSION = "unknown"

# --- Dummy classes for critical module fallbacks ---
class _DummyWebUIUtilsModule:
    def update_current_webui(self, webui_name): print(f"[_DummyWebUIUtilsModule] update_current_webui for {webui_name}")
    def get_webui_asset_path(self, webui_name, asset_type, asset_filename=""): return str(Path(PROJECT_ROOT) / "models" / asset_type / asset_filename)
    def get_webui_installation_root(self, webui_name: str) -> str: return str(Path(PROJECT_ROOT) / webui_name)

class _DummyManagerModule:
    def download_file(self, url, filename, log=False, **kwargs):
        print(f"[_DummyManagerModule] download_file for {url} to {filename}")
        return not ("fail" in filename) # Simulate success unless "fail" in name

# Initialize placeholders for critical modules
json_utils = None
webui_utils = _DummyWebUIUtilsModule() # Instantiate dummy
manager_utils = _DummyManagerModule()  # Instantiate dummy

print(f"[DEBUG] Initial sys.path: {sys.path}")

try:
    # Import critical utility modules
    from modules import json_utils as real_json_utils
    json_utils = real_json_utils
    print("Successfully imported real json_utils.")

    from modules import webui_utils as real_webui_utils_module
    webui_utils = real_webui_utils_module # Assign module directly, assuming functions are module-level
    print("Successfully imported real webui_utils module.")
    
    from modules import Manager as RealManagerModule
    manager_utils = RealManagerModule # Assign module directly
    print("Successfully imported real Manager module.")

except ImportError as e_utils:
    print(f"Warning: Error importing one or more critical utility modules (json_utils, webui_utils, Manager): {e_utils}. Using dummies where possible.")
    # Dummies are already initialized. json_utils being None is a critical failure handled later.

# --- UI Lists & Data ---
WEBUI_CHOICES = ["A1111", "ComfyUI", "Forge"] 
SD_VERSION_CHOICES = ["SD1.5", "SDXL"]
THEME_CHOICES = ["Default", "anxety", "blue", "green", "peach", "pink", "red", "yellow"] 
INPAINTING_FILTER_CHOICES = ["Show All Models", "Inpainting Models Only", "No Inpainting Models"]
WEBUI_DEFAULT_ARGS = {'A1111': "--xformers --no-half-vae", 'ComfyUI': "--preview-method auto", 'Forge': "--xformers --cuda-stream --pin-shared-memory"}
SETTINGS_KEYS = [ # Reviewed for v3 relevance
    'XL_models', 'model', 'model_num', 'inpainting_model', 'vae', 'vae_num',
    'check_custom_nodes_deps', 'change_webui', 'detailed_download',
    'controlnet', 'controlnet_num', 'commit_hash', 
    'civitai_token', 'huggingface_token', 'zrok_token', 'ngrok_token', 'commandline_arguments', 'theme_accent',
    'anxlight_selected_models_list', 'anxlight_selected_vaes_list', 
    'anxlight_selected_controlnets_list', 'anxlight_selected_loras_list'
]

# Global dictionaries to hold loaded asset data
# These will be populated by get_asset_choices based on sd_version
current_model_data = {}
current_vae_data = {}
current_controlnet_data = {}
current_lora_data = {}

def load_data_for_sd_version(sd_version):
    """Loads model, VAE, ControlNet, and LoRA data for the selected SD version."""
    global current_model_data, current_vae_data, current_controlnet_data, current_lora_data
    data_loaded_successfully = True
    try:
        if sd_version == "SD1.5":
            data_module = importlib.import_module("sd15_data")
            current_model_data = getattr(data_module, "sd15_model_data", {})
            current_vae_data = getattr(data_module, "sd15_vae_data", {})
            current_controlnet_data = getattr(data_module, "sd15_controlnet_data", {})
            current_lora_data = getattr(data_module, "sd15_lora_data", {})
        elif sd_version == "SDXL":
            data_module = importlib.import_module("sdxl_data")
            current_model_data = getattr(data_module, "sdxl_model_data", {})
            current_vae_data = getattr(data_module, "sdxl_vae_data", {})
            current_controlnet_data = getattr(data_module, "sdxl_controlnet_data", {})
            current_lora_data = getattr(data_module, "sdxl_lora_data", {})
        else:
            current_model_data, current_vae_data, current_controlnet_data, current_lora_data = {}, {}, {}, {}
            data_loaded_successfully = False
        
        if not (current_model_data or current_vae_data or current_controlnet_data or current_lora_data):
            print(f"Warning: No data loaded for SD version {sd_version}. Check data files.")
            data_loaded_successfully = False
            # Ensure they are empty dicts if load failed to prevent errors later
            current_model_data, current_vae_data, current_controlnet_data, current_lora_data = {}, {}, {}, {}


    except ImportError as e:
        print(f"FATAL: Could not import data module for SD version {sd_version}: {e}")
        current_model_data, current_vae_data, current_controlnet_data, current_lora_data = {}, {}, {}, {}
        data_loaded_successfully = False
    
    if data_loaded_successfully:
        print(f"Successfully loaded data for {sd_version}.")
    else:
        print(f"Failed to load complete data for {sd_version}.")


def get_asset_choices(sd_version, inpainting_filter_mode="Show All Models"):
    load_data_for_sd_version(sd_version) # Ensure correct data is loaded globally

    # Models
    models = []
    if current_model_data:
        for name, data_val in current_model_data.items():
            is_inpainting_model = False
            if isinstance(data_val, dict): # Expected structure: {"url": ..., "name": ..., "inpainting": True/False}
                is_inpainting_model = data_val.get("inpainting", "inpainting" in name.lower() or "inpaint" in name.lower())
            elif isinstance(data_val, list) and data_val: # Original list structure
                 # Simplistic check on first item's name for inpainting if no explicit flag
                is_inpainting_model = "inpainting" in data_val[0].get("name","").lower() or "inpaint" in data_val[0].get("name","").lower()

            if (inpainting_filter_mode == "Show All Models") or \
               (inpainting_filter_mode == "Inpainting Models Only" and is_inpainting_model) or \
               (inpainting_filter_mode == "No Inpainting Models" and not is_inpainting_model):
                models.append(name)
    
    vaes = list(current_vae_data.keys()) if current_vae_data else []
    controlnets = list(current_controlnet_data.keys()) if current_controlnet_data else []
    loras = list(current_lora_data.keys()) if current_lora_data else []
    
    return models, vaes, controlnets, loras

# update_all_ui_elements, save_keys_to_file_fn, load_keys_from_file_fn (largely same, ensure they use global current_theme_value if needed)
# _execute_backend_script (largely same)
# download_selected_asset (needs to use current_model_data, etc.)
# launch_anxlight_main_process (largely same orchestration, but asset download calls new download_selected_asset)

def update_all_ui_elements(sd_version_selected, inpainting_filter_selected, webui_selected):
    models, vaes, controlnets, loras = get_asset_choices(sd_version_selected, inpainting_filter_selected)
    default_args = WEBUI_DEFAULT_ARGS.get(webui_selected, "")
    is_comfy = (webui_selected == 'ComfyUI')
    update_ext_visible = not is_comfy 
    check_nodes_visible = is_comfy
    theme_accent_visible = not is_comfy 
    current_theme_value = THEME_CHOICES[0] 
    return (gr.update(choices=models, value=[] if models else None, interactive=bool(models)), 
            gr.update(choices=vaes, value=[] if vaes else None, interactive=bool(vaes)), 
            gr.update(choices=controlnets, value=[] if controlnets else None, interactive=bool(controlnets)),
            gr.update(choices=loras, value=[] if loras else None, interactive=bool(loras)), 
            gr.update(value=default_args), 
            gr.update(visible=update_ext_visible),
            gr.update(visible=check_nodes_visible), 
            gr.update(visible=theme_accent_visible, value=current_theme_value if theme_accent_visible else None))

def save_keys_to_file_fn(civitai, hf, ngrok, zrok):
    keys_data = {"civitai_token": civitai, "huggingface_token": hf, "ngrok_token": ngrok, "zrok_token": zrok}
    temp_file_path = "anxlight_keys.json" 
    try:
        with open(temp_file_path, 'w') as f: json.dump(keys_data, f, indent=2)
        gr.Info("Keys saved! Your browser should prompt a download.")
        return gr.update(value=temp_file_path, visible=True) 
    except Exception as e:
        gr.Error(f"Failed to save keys: {e}"); return gr.update(value=None, visible=False)

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
    log_output_list = current_log_output_list
    full_log_file_path = None; script_success = False
    if detailed_logging_enabled and log_session_dir:
        full_log_file_path = os.path.join(log_session_dir, log_file_name_base)
        log_output_list.append(f"Detailed log for this step will be at: {full_log_file_path}\n"); yield "".join(log_output_list)
    log_output_list.append(f"Executing: {sys.executable} {script_path} (Target Version: v{script_version})...\n"); yield "".join(log_output_list)
    process = None; log_file = None
    try:
        process_env = os.environ.copy()
        existing_pythonpath = process_env.get('PYTHONPATH', ''); paths_to_prepend = [MODULES_PATH, PROJECT_ROOT, SCRIPTS_PATH]
        new_pythonpath_parts = paths_to_prepend + ([p for p in existing_pythonpath.split(os.pathsep) if p] if existing_pythonpath else [])
        seen_paths = set(); unique_pythonpath_parts = [p for p in new_pythonpath_parts if not (p in seen_paths or seen_paths.add(p))]
        process_env['PYTHONPATH'] = os.pathsep.join(unique_pythonpath_parts)
        log_output_list.append(f"{ui_log_prefix} Subprocess PYTHONPATH: {process_env['PYTHONPATH']}\n"); yield "".join(log_output_list)
        process = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True, env=process_env, cwd=PROJECT_ROOT)
        if full_log_file_path:
            try: log_file = open(full_log_file_path, 'a', encoding='utf-8')
            except Exception as e_file: log_output_list.append(f"Warning: Could not open log file {full_log_file_path}: {e_file}\n"); yield "".join(log_output_list)
        for line in process.stdout:
            line_stripped = line.strip(); log_output_list.append(f"{ui_log_prefix} {line_stripped}\n")
            if log_file:
                try: log_file.write(line)
                except Exception as e_write: print(f"Error writing to log file {full_log_file_path}: {e_write}");_ = (log_file.close(), setattr(log_file, 'closed', True)) if log_file else None; log_file = None
            yield "".join(log_output_list)
        process.wait(); script_success = (process.returncode == 0)
        log_output_list.append(f"{ui_log_prefix} Script finished with return code {process.returncode}.\n"); yield "".join(log_output_list)
    except FileNotFoundError: log_output_list.append(f"{ui_log_prefix} Error: Script not found at {script_path}.\n")
    except Exception as e: log_output_list.append(f"{ui_log_prefix} An unexpected error occurred: {type(e).__name__}: {e}\nTraceback: {traceback.format_exc()}\n")
    finally:
        if log_file and not log_file.closed: log_file.close()
        if process and process.poll() is None:
            log_output_list.append(f"{ui_log_prefix} Terminating script {script_path}.\n"); yield "".join(log_output_list); process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill(); log_output_list.append(f"{ui_log_prefix} Script force-killed.\n"); yield "".join(log_output_list)
    yield "SCRIPT_EXECUTION_SUCCESS" if script_success else "SCRIPT_EXECUTION_FAILURE"

def download_selected_asset(asset_name, asset_type, sd_version, webui_choice, log_output_list, hf_token_val, civitai_token_val):
    global current_model_data, current_vae_data, current_controlnet_data, current_lora_data # Use globally loaded data

    if isinstance(manager_utils, _DummyManagerModule):
        log_output_list.append(f"Warning: Manager module not fully loaded (dummy). Cannot download {asset_type} '{asset_name}'.\n"); return False
    if isinstance(webui_utils, _DummyWebUIUtilsModule): # Check if it's the dummy instance
        log_output_list.append(f"Warning: WebUIUtils module not fully loaded (dummy). Cannot determine path for {asset_type} '{asset_name}'.\n"); return False

    data_source_map = {
        "model": current_model_data, "vae": current_vae_data,
        "controlnet": current_controlnet_data, "lora": current_lora_data
    }
    data_source = data_source_map.get(asset_type)
    
    if not data_source or asset_name not in data_source:
        log_output_list.append(f"Warning: Metadata for {asset_type} '{asset_name}' not found in loaded data. Cannot download.\n"); return False

    asset_info_list = data_source[asset_name] # This is now a list of file dicts
    if not isinstance(asset_info_list, list): # Ensure it's a list
        asset_info_list = [asset_info_list] # Wrap if it's a single dict (for old model/vae structure)

    overall_success_for_asset_group = True
    for file_info in asset_info_list:
        download_url = file_info.get("url")
        # Derive filename from 'name' key, or from URL if 'name' is missing
        filename_from_data = file_info.get("name")
        if not filename_from_data and download_url:
            try:
                filename_from_data = Path(urlparse(download_url).path).name
                if not filename_from_data: # if path ends in /
                    log_output_list.append(f"Warning: Could not derive filename from URL '{download_url}' for {asset_name}. Skipping this file.\n")
                    yield "".join(log_output_list)
                    overall_success_for_asset_group = False
                    continue
            except Exception as e_fn:
                log_output_list.append(f"Warning: Error deriving filename from URL '{download_url}': {e_fn}. Skipping this file.\n")
                yield "".join(log_output_list)
                overall_success_for_asset_group = False
                continue
        elif not download_url:
             log_output_list.append(f"Warning: Download URL missing for an item in {asset_type} '{asset_name}'. Skipping this file.\n")
             yield "".join(log_output_list)
             overall_success_for_asset_group = False
             continue
        
        target_filename = filename_from_data # Use derived/provided name

        asset_type_plural_map = {"model": "models", "vae": "vaes", "lora": "loras", "controlnet": "controlnet"}
        path_key_for_webui_utils = asset_type_plural_map.get(asset_type, asset_type)
        target_path_full_str = webui_utils.get_webui_asset_path(webui_choice, path_key_for_webui_utils, target_filename)
        
        if not target_path_full_str:
            log_output_list.append(f"Error: Could not determine target path for {asset_type} '{target_filename}'. Download aborted for this file.\n")
            overall_success_for_asset_group = False; continue
        
        target_path_full = Path(target_path_full_str); target_directory = target_path_full.parent
        log_output_list.append(f"Preparing to download {asset_type} '{target_filename}' (part of '{asset_name}') from {download_url} to {target_path_full}...\n")
        yield "".join(log_output_list)
        try: os.makedirs(target_directory, exist_ok=True)
        except Exception as e_mkdir:
            log_output_list.append(f"Error creating directory {target_directory}: {e_mkdir}.\n"); overall_success_for_asset_group = False; continue

        original_cwd = os.getcwd(); file_download_success = False
        try:
            log_output_list.append(f"Changing CWD to: {target_directory} for downloading '{target_filename}'\n"); yield "".join(log_output_list)
            os.chdir(target_directory)
            # Pass tokens to Manager.py if its download_file is adapted to take them, or rely on its internal constants
            manager_call_result = manager_utils.download_file(url=download_url, filename=target_filename, log=True, hf_token=hf_token_val) # Pass hf_token
            
            if Path(target_filename).exists():
                file_download_success = True
                log_output_list.append(f"Successfully downloaded '{target_filename}'.\n")
            elif manager_call_result is None: log_output_list.append(f"Manager.py returned None for '{target_filename}'. File not found.\n")
            else: log_output_list.append(f"Download of '{target_filename}' did not result in a found file. Manager status: {manager_call_result}.\n")
        except Exception as e_dl_wrapper:
            log_output_list.append(f"Exception during download process for '{target_filename}': {e_dl_wrapper}\nTraceback: {traceback.format_exc()}\n")
        finally:
            os.chdir(original_cwd)
            log_output_list.append(f"Restored CWD to: {original_cwd}\n") # Moved yield to after CWD restoration
            yield "".join(log_output_list) # Ensure UI gets this CWD restoration message too
        
        if not file_download_success: overall_success_for_asset_group = False
    
    return overall_success_for_asset_group

# launch_anxlight_main_process and UI definition follow, mostly unchanged from SCIE #7 refactor,
# but ensuring that the new global data dicts (current_model_data etc.) are used by download_selected_asset indirectly.
# The primary changes are in load_data_for_sd_version, get_asset_choices, and download_selected_asset.

def launch_anxlight_main_process(
    webui_choice, sd_version, inpainting_models_filter_val,
    selected_models, selected_vaes, selected_controlnets, selected_loras,
    update_webui_val, update_extensions_val, check_custom_nodes_val, detailed_download_val,
    commit_hash_val, civitai_token_val, huggingface_token_val, zrok_token_val, ngrok_token_val,
    custom_args_val, theme_accent_val
):
    log_output_list = [f"--- {APP_DISPLAY_VERSION} Backend Process Initializing (System: {SYSTEM_DISPLAY_VERSION}) ---\n"]
    log_output_list.append(f"Pre-Flight Setup Script Version (expected by this app): v{PRE_FLIGHT_SETUP_PY_VERSION}\n"); yield "".join(log_output_list)

    if json_utils is None: log_output_list.append("FATAL: json_utils module not loaded.\n"); yield "".join(log_output_list); return
    if isinstance(webui_utils, _DummyWebUIUtilsModule): log_output_list.append("Warning: webui_utils module not fully loaded (dummy).\n")
    if isinstance(manager_utils, _DummyManagerModule): log_output_list.append("Warning: Manager module not fully loaded (dummy). Asset downloads may fail or use dummy.\n")
    
    load_data_for_sd_version(sd_version) # Ensure data for the current SD version is loaded into globals

    local_project_root = PROJECT_ROOT; log_output_list.append(f"Project Root: {local_project_root}\n")
    log_session_dir = None
    if detailed_download_val:
        try:
            log_dir_base = os.path.join(local_project_root, 'logs'); log_session_dir = os.path.join(log_dir_base, f'session_{time.strftime("%Y%m%d-%H%M%S")}')
            os.makedirs(log_session_dir, exist_ok=True); log_output_list.append(f"Detailed logging enabled. Session logs: {log_session_dir}\n")
        except Exception as e: log_output_list.append(f"Warning: Could not create log dir {log_session_dir}: {e}\n"); log_session_dir = None
    else: log_output_list.append("Detailed file logging disabled.\n")
    yield "".join(log_output_list)

    log_output_list.append(f"\n--- Step 1: Verifying WebUI '{webui_choice}' Installation ---\n")
    log_output_list.append(f"NOTE: WebUI installation is handled by 'scripts/pre_flight_setup.py'. Assuming '{webui_choice}' is installed.\n")
    if not isinstance(webui_utils, _DummyWebUIUtilsModule): # Only check if real util is loaded
        webui_root_path_str = webui_utils.get_webui_installation_root(webui_choice)
        if not webui_root_path_str or not Path(webui_root_path_str).exists():
            log_output_list.append(f"CRITICAL WARNING: Installation directory for '{webui_choice}' not found at '{webui_root_path_str}'. Pre-flight setup may be needed or path is incorrect.\n")
        else: log_output_list.append(f"Verified installation directory for '{webui_choice}' at '{webui_root_path_str}'.\n")
    yield "".join(log_output_list)

    log_output_list.append(f"\n--- Step 2: Downloading Selected Session Assets ---\n"); yield "".join(log_output_list)
    assets_to_process = [("model", selected_models), ("vae", selected_vaes), ("controlnet", selected_controlnets), ("lora", selected_loras)]
    overall_asset_download_success = True
    for asset_type, asset_names_list in assets_to_process:
        if asset_names_list:
            for asset_name in asset_names_list:
                if not download_selected_asset(asset_name, asset_type, sd_version, webui_choice, log_output_list, huggingface_token_val, civitai_token_val):
                    overall_asset_download_success = False 
                yield "".join(log_output_list) 
        else: log_output_list.append(f"No {asset_type}s selected for download.\n"); yield "".join(log_output_list)
    if not overall_asset_download_success: log_output_list.append("Warning: One or more assets may have failed to download. Check logs above.\n")
    yield "".join(log_output_list)

    log_output_list.append(f"\n--- Step 3: Generating Configuration File ---\n"); widgets_data = {}
    try:
        widgets_data.update({
            'XL_models': (sd_version == "SDXL"), 'model': selected_models[0] if selected_models else "none",
            'model_num': ",".join(selected_models) if selected_models else "",
            'inpainting_model': (inpainting_models_filter_val == "Inpainting Models Only"), # This flag might need to come from model metadata
            'vae': selected_vaes[0] if selected_vaes else "none", 'vae_num': ",".join(selected_vaes) if selected_vaes else "",
            'latest_webui': update_webui_val, 'latest_extensions': update_extensions_val,
            'check_custom_nodes_deps': check_custom_nodes_val, 'change_webui': webui_choice,
            'detailed_download': "on" if detailed_download_val else "off",
            'controlnet': selected_controlnets[0] if selected_controlnets else "none",
            'controlnet_num': ",".join(selected_controlnets) if selected_controlnets else "",
            'commit_hash': commit_hash_val or "", 'civitai_token': civitai_token_val or "",
            'huggingface_token': huggingface_token_val or "", 'zrok_token': zrok_token_val or "",
            'ngrok_token': ngrok_token_val or "", 
            'commandline_arguments': custom_args_val or WEBUI_DEFAULT_ARGS.get(webui_choice, ""),
            'theme_accent': theme_accent_val,
            'anxlight_selected_models_list': selected_models or [], 'anxlight_selected_vaes_list': selected_vaes or [],
            'anxlight_selected_controlnets_list': selected_controlnets or [], 'anxlight_selected_loras_list': selected_loras or []
        })
        environment_data = {'env_name': "Google Colab" if 'COLAB_GPU' in os.environ else "AnxLight_Generic_Platform", 'lang': "en",
                            'home_path': os.environ.get('home_path', PROJECT_ROOT), 'scr_path': os.environ.get('scr_path', PROJECT_ROOT),
                            'settings_path': os.environ.get('settings_path', str(Path(os.environ.get('home_path', PROJECT_ROOT)) / 'anxlight_config.json')),
                            'venv_path': os.environ.get('venv_path', str(Path(PROJECT_ROOT) / "anxlight_venv")), # VENV_NAME from pre_flight
                            'fork': "drf0rk/AnxLight", 'branch': subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=PROJECT_ROOT).strip().decode('utf-8'),
                            'start_timer': int(time.time() - 5), 'public_ip': ""}
        anxlight_config = {"WIDGETS": widgets_data, "ENVIRONMENT": environment_data, "UI_SELECTION": {"webui_choice": webui_choice}}
        log_output_list.append("Configuration dictionary constructed.\n")
    except Exception as e: log_output_list.append(f"Error constructing config: {e}\nTraceback: {traceback.format_exc()}\n"); yield "".join(log_output_list); return
    config_file_path = Path(environment_data['settings_path'])
    try:
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, 'w') as f: json.dump(anxlight_config, f, indent=4)
        log_output_list.append(f"Config saved to: {config_file_path}\n")
    except Exception as e: log_output_list.append(f"Error saving config to {config_file_path}: {e}\nTraceback: {traceback.format_exc()}\n"); yield "".join(log_output_list); return
    yield "".join(log_output_list)

    log_output_list.append(f"\n--- Step 4: Updating WebUI Paths in Config ---\n")
    try:
        if not isinstance(webui_utils, _DummyWebUIUtilsModule): webui_utils.update_current_webui(webui_choice); log_output_list.append(f"Called webui_utils.update_current_webui for '{webui_choice}'.\n")
        else: log_output_list.append(f"Warning: webui_utils dummy/not loaded. update_current_webui for '{webui_choice}' skipped/dummy.\n");_ = webui_utils.update_current_webui(webui_choice) # call dummy
    except Exception as e: log_output_list.append(f"Error calling webui_utils.update_current_webui: {e}\nTraceback: {traceback.format_exc()}\n")
    yield "".join(log_output_list)
        
    log_output_list.append(f"\n--- Step 5: Initiating Launch Script ---\n")
    launch_script_path = os.path.join(environment_data['scr_path'], 'scripts', 'launch.py')
    log_output_list.append(f"Attempting to run launch script (v{LAUNCH_PY_VERSION}): {launch_script_path}\n"); yield "".join(log_output_list)
    launch_success = False
    for exec_status in _execute_backend_script(launch_script_path, LAUNCH_PY_VERSION, "launch.log", "[Launcher]", detailed_download_val, log_session_dir, log_output_list):
        if exec_status == "SCRIPT_EXECUTION_SUCCESS": launch_success = True
        elif exec_status == "SCRIPT_EXECUTION_FAILURE": launch_success = False
        else: yield exec_status 
    log_output_list.append(f"--- Launch script {'finished successfully' if launch_success else 'failed or status unclear'}. WebUI may be starting. ---\n")
    yield "".join(log_output_list)

with gr.Blocks(css=".gradio-container {max-width: 90% !important; margin: auto !important;}") as demo:
    gr.Markdown(f"# AnxLight Launcher ({APP_DISPLAY_VERSION})")
    # Initial population of choices - call get_asset_choices once at an appropriate scope
    # Or trigger an update on first load. For now, let's do it here.
    # This will load data for the default SD_VERSION_CHOICES[0]
    load_data_for_sd_version(SD_VERSION_CHOICES[0]) 
    _initial_models, _initial_vaes, _initial_controlnets, _initial_loras = get_asset_choices(SD_VERSION_CHOICES[0], INPAINTING_FILTER_CHOICES[0])
    _initial_webui = WEBUI_CHOICES[0]; _initial_is_comfy = (_initial_webui == 'ComfyUI')
    
    with gr.Tabs():
        with gr.TabItem("Session Configuration"): 
            gr.Markdown("## Main Configuration")
            with gr.Row(): webui_choice_dd = gr.Dropdown(label="Select WebUI", choices=WEBUI_CHOICES, value=_initial_webui, interactive=True); sd_version_rb = gr.Radio(label="Model Version", choices=SD_VERSION_CHOICES, value=SD_VERSION_CHOICES[0], interactive=True)
            inpainting_filter_rg = gr.Radio(label="Model Type Filter", info="Filters the 'Select Models' list below.", choices=INPAINTING_FILTER_CHOICES, value=INPAINTING_FILTER_CHOICES[0], interactive=True)
            with gr.Row(equal_height=False): 
                update_webui_chk = gr.Checkbox(label="Update WebUI Components (Daily)", value=False, info="If pre-flight setup allows for daily/minor updates of WebUI components."); update_extensions_chk = gr.Checkbox(label="Update Extensions (Daily)", value=False, info="If pre-flight setup allows for daily/minor updates of extensions.", visible=not _initial_is_comfy)
                check_custom_nodes_deps_chk = gr.Checkbox(label="Check ComfyUI Nodes Deps (on Launch)", value=True, visible=_initial_is_comfy, info="For ComfyUI, check custom node dependencies during launch process."); detailed_download_chk = gr.Checkbox(label="Detailed Session Log", value=True, info="Enable detailed UI and file logging for this session's processes.")
            gr.Markdown("### Assets Selection (for this session)")
            with gr.Row(): models_cbg = gr.CheckboxGroup(label="Select Models", choices=_initial_models, value=[], interactive=bool(_initial_models)); vaes_cbg = gr.CheckboxGroup(label="Select VAEs", choices=_initial_vaes, value=[], interactive=bool(_initial_vaes))
            with gr.Row(): controlnets_cbg = gr.CheckboxGroup(label="Select ControlNets", choices=_initial_controlnets, value=[], interactive=bool(_initial_controlnets)); loras_cbg = gr.CheckboxGroup(label="Select LoRAs", choices=_initial_loras, value=[], interactive=bool(_initial_loras))
            gr.Markdown("### Advanced Options"); commit_hash_tb = gr.Textbox(label="WebUI Commit Hash (For Pre-Flight Setup)", info="If pre-flight needs to install a specific WebUI version. Run Cell 1 after setting.", placeholder="e.g., a1b2c3d...")
            gr.Markdown("### Tokens & Access Keys")
            with gr.Row(): civitai_token_tb = gr.Textbox(label="CivitAI API Key", type="password", placeholder="Optional"); huggingface_token_tb = gr.Textbox(label="HuggingFace Token", type="password", placeholder="Optional for private HF assets")
            with gr.Row(): ngrok_token_tb = gr.Textbox(label="NGROK Token", type="password", placeholder="Optional for NGROK tunnel"); zrok_token_tb = gr.Textbox(label="Zrok Token", type="password", placeholder="Optional for Zrok tunnel")
            with gr.Row(): save_keys_btn = gr.Button("Save Keys to File"); download_keys_file_display = gr.File(label="Download Saved Keys", visible=False, interactive=False)
            load_keys_file_upload = gr.File(label="Load Keys from File", file_types=[".json"], scale=2)
            gr.Markdown("### Launch & UI Settings"); custom_args_tb = gr.Textbox(label="Custom Launch Arguments for WebUI", value=WEBUI_DEFAULT_ARGS.get(_initial_webui, ""), placeholder="e.g., --xformers --no-half-vae"); theme_accent_dd = gr.Dropdown(label="Launcher UI Theme Accent", choices=THEME_CHOICES, value=THEME_CHOICES[0], info="Select a visual theme.", visible=not _initial_is_comfy)
        with gr.TabItem("Launch & Live Log"):
            gr.Markdown("## Launch Controls"); launch_button = gr.Button("Download Assets & Launch WebUI", variant="primary"); live_log_ta = gr.Textbox(label="Live Log Output", lines=20, interactive=False, max_lines=50, show_copy_button=True)
    event_inputs_master_filter = [sd_version_rb, inpainting_filter_rg, webui_choice_dd]
    event_outputs_master_filter = [models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, custom_args_tb, update_extensions_chk, check_custom_nodes_deps_chk, theme_accent_dd]
    sd_version_rb.change(fn=update_all_ui_elements, inputs=event_inputs_master_filter, outputs=event_outputs_master_filter)
    inpainting_filter_rg.change(fn=update_all_ui_elements, inputs=event_inputs_master_filter, outputs=event_outputs_master_filter)
    webui_choice_dd.change(fn=update_all_ui_elements, inputs=event_inputs_master_filter, outputs=event_outputs_master_filter)
    save_keys_btn.click(fn=save_keys_to_file_fn, inputs=[civitai_token_tb, huggingface_token_tb, ngrok_token_tb, zrok_token_tb], outputs=[download_keys_file_display])
    load_keys_file_upload.upload(fn=load_keys_from_file_fn, inputs=[load_keys_file_upload], outputs=[civitai_token_tb, huggingface_token_tb, ngrok_token_tb, zrok_token_tb])
    all_launch_inputs = [webui_choice_dd, sd_version_rb, inpainting_filter_rg, models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, update_webui_chk, update_extensions_chk, check_custom_nodes_deps_chk, detailed_download_chk, commit_hash_tb, civitai_token_tb, huggingface_token_tb, zrok_token_tb, ngrok_token_tb, custom_args_tb, theme_accent_dd]
    launch_button.click(fn=launch_anxlight_main_process, inputs=all_launch_inputs, outputs=live_log_ta)
if __name__ == "__main__":
    print(f"Launching Gradio App for AnxLight ({APP_DISPLAY_VERSION})..."); 
    # Ensure DATA_MODULE_PATH is in sys.path when run directly for testing
    if DATA_MODULE_PATH not in sys.path: sys.path.insert(0, DATA_MODULE_PATH)
    demo.queue().launch(debug=True, share=os.environ.get("GRADIO_SHARE", "true").lower() == "true", prevent_thread_lock=True, show_error=True)