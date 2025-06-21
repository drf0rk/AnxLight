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
    LAUNCH_PY_VERSION = "unknown"; PRE_FLIGHT_SETUP_PY_VERSION = "unknown"

# --- UI Constants ---
SD_VERSION_CHOICES = ["SD1.5", "SDXL"]
INPAINTING_FILTER_CHOICES = ["Show All Models", "Inpainting Models Only", "No Inpainting Models"]
WEBUI_CHOICES = ["A1111", "Classic", "ComfyUI", "Forge", "ReForge", "SD-UX"]
THEME_CHOICES = ["Default", "Glass", "Monochrome", "Soft"]

WEBUI_DEFAULT_ARGS = {
    "A1111": "--xformers --no-half-vae",
    "Classic": "--xformers --no-half-vae",
    "ComfyUI": "--windows-standalone-build",
    "Forge": "--xformers --no-half-vae",
    "ReForge": "--xformers --no-half-vae",
    "SD-UX": ""
}

class _DummyWebUIUtilsModule:
    def update_current_webui(self, webui_name): print(f"[_DummyWebUIUtilsModule] update_current_webui for {webui_name}")
    def get_webui_asset_path(self, webui_name, asset_type, asset_filename=""): return str(Path(PROJECT_ROOT) / "models" / asset_type / asset_filename)
    def get_webui_installation_root(self, webui_name: str) -> str: return str(Path(PROJECT_ROOT) / webui_name)

class _DummyManagerModule:
    def download_url_to_path(self, url, target_full_path, log=False, hf_token=None, cai_token=None):
        print(f"[_DummyManagerModule] download_url_to_path for {url} to {target_full_path}")
        return not ("fail" in Path(target_full_path).name)

json_utils = None; webui_utils = _DummyWebUIUtilsModule(); manager_utils = _DummyManagerModule()
print(f"[DEBUG] Initial sys.path: {sys.path}")
try:
    from modules import json_utils as real_json_utils; json_utils = real_json_utils
    from modules import webui_utils as real_webui_utils_module; webui_utils = real_webui_utils_module
    from modules import Manager as RealManagerModule; manager_utils = RealManagerModule
    print("Successfully imported real backend utility modules.")
except ImportError as e_utils:
    print(f"Warning: Error importing one or more critical utility modules: {e_utils}. Using dummies.")

current_model_data, current_vae_data, current_controlnet_data, current_lora_data = {}, {}, {}, {}

def load_data_for_sd_version(sd_version):
    global current_model_data, current_vae_data, current_controlnet_data, current_lora_data
    data_loaded_successfully = True
    module_name = "sd15_data" if sd_version == "SD1.5" else "sdxl_data" if sd_version == "SDXL" else None
    if not module_name:
        current_model_data, current_vae_data, current_controlnet_data, current_lora_data = {}, {}, {}, {}; return
    try:
        data_module = importlib.import_module(module_name)
        current_model_data = getattr(data_module, f"{sd_version.lower().replace('.', '')}_model_data", {})
        current_vae_data = getattr(data_module, f"{sd_version.lower().replace('.', '')}_vae_data", {})
        current_controlnet_data = getattr(data_module, f"{sd_version.lower().replace('.', '')}_controlnet_data", {})
        current_lora_data = getattr(data_module, f"{sd_version.lower().replace('.', '')}_lora_data", {})
        if not any([current_model_data, current_vae_data, current_controlnet_data, current_lora_data]): data_loaded_successfully = False
    except ImportError as e:
        print(f"FATAL: Could not import {module_name}: {e}"); data_loaded_successfully = False
        current_model_data, current_vae_data, current_controlnet_data, current_lora_data = {}, {}, {}, {}
    print(f"{'Successfully' if data_loaded_successfully else 'Failed to load complete'} data for {sd_version}.")

def get_asset_choices(sd_version, inpainting_filter_mode="Show All Models"):
    load_data_for_sd_version(sd_version)
    models = [name for name, data_val in current_model_data.items() if 
              (inpainting_filter_mode == "Show All Models") or
              (inpainting_filter_mode == "Inpainting Models Only" and isinstance(data_val, dict) and data_val.get("inpainting", "inpainting" in name.lower())) or
              (inpainting_filter_mode == "No Inpainting Models" and not (isinstance(data_val, dict) and data_val.get("inpainting", "inpainting" in name.lower())))]
    return models, list(current_vae_data), list(current_controlnet_data), list(current_lora_data)

def update_all_ui_elements(sd_version_selected, inpainting_filter_selected, webui_selected):
    models, vaes, controlnets, loras = get_asset_choices(sd_version_selected, inpainting_filter_selected)
    default_args = WEBUI_DEFAULT_ARGS.get(webui_selected, "")
    is_comfy = (webui_selected == 'ComfyUI'); theme_accent_visible = not is_comfy
    return (gr.update(choices=models, value=[], interactive=bool(models)), 
            gr.update(choices=vaes, value=[], interactive=bool(vaes)), 
            gr.update(choices=controlnets, value=[], interactive=bool(controlnets)),
            gr.update(choices=loras, value=[], interactive=bool(loras)), 
            gr.update(value=default_args), gr.update(visible=not is_comfy),
            gr.update(visible=is_comfy), gr.update(visible=theme_accent_visible, value=THEME_CHOICES[0] if theme_accent_visible else None))

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
        log_output_list.append(f"Detailed log for this step will be at: {full_log_file_path}\\n"); yield "".join(log_output_list)
    log_output_list.append(f"Executing: {sys.executable} {script_path} (Target Version: v{script_version})...\\n"); yield "".join(log_output_list)
    process = None; log_file = None
    try:
        process_env = os.environ.copy()
        existing_pythonpath = process_env.get('PYTHONPATH', ''); paths_to_prepend = [MODULES_PATH, PROJECT_ROOT, SCRIPTS_PATH]
        new_pythonpath_parts = paths_to_prepend + ([p for p in existing_pythonpath.split(os.pathsep) if p] if existing_pythonpath else [])
        seen_paths = set(); unique_pythonpath_parts = [p for p in new_pythonpath_parts if not (p in seen_paths or seen_paths.add(p))]
        process_env['PYTHONPATH'] = os.pathsep.join(unique_pythonpath_parts)
        log_output_list.append(f"{ui_log_prefix} Subprocess PYTHONPATH: {process_env['PYTHONPATH']}\\n"); yield "".join(log_output_list)
        process = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True, env=process_env, cwd=PROJECT_ROOT)
        if full_log_file_path:
            try: log_file = open(full_log_file_path, 'a', encoding='utf-8')
            except Exception as e_file: log_output_list.append(f"Warning: Could not open log file {full_log_file_path}: {e_file}\\n"); yield "".join(log_output_list)
        for line in process.stdout:
            line_stripped = line.strip(); log_output_list.append(f"{ui_log_prefix} {line_stripped}\\n")
            if log_file:
                try: log_file.write(line)
                except Exception as e_write: print(f"Error writing to log file {full_log_file_path}: {e_write}");_ = (log_file.close(), setattr(log_file, 'closed', True)) if log_file else None; log_file = None
            yield "".join(log_output_list)
        process.wait(); script_success = (process.returncode == 0)
        log_output_list.append(f"{ui_log_prefix} Script finished with return code {process.returncode}.\\n"); yield "".join(log_output_list)
    except FileNotFoundError: log_output_list.append(f"{ui_log_prefix} Error: Script not found at {script_path}.\\n")
    except Exception as e: log_output_list.append(f"{ui_log_prefix} An unexpected error occurred: {type(e).__name__}: {e}\\nTraceback: {traceback.format_exc()}\\n")
    finally:
        if log_file and not log_file.closed: log_file.close()
        if process and process.poll() is None:
            log_output_list.append(f"{ui_log_prefix} Terminating script {script_path}.\\n"); yield "".join(log_output_list); process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill(); log_output_list.append(f"{ui_log_prefix} Script force-killed.\\n"); yield "".join(log_output_list)
    yield "SCRIPT_EXECUTION_SUCCESS" if script_success else "SCRIPT_EXECUTION_FAILURE"

def download_selected_asset(asset_name, asset_type, sd_version, webui_choice, log_output_list, hf_token_val, civitai_token_val):
    global current_model_data, current_vae_data, current_controlnet_data, current_lora_data

    if isinstance(manager_utils, _DummyManagerModule) or isinstance(webui_utils, _DummyWebUIUtilsModule):
        log_output_list.append(f"Warning: Manager or WebUIUtils module not fully loaded (dummy). Cannot download {asset_type} '{asset_name}'.\\n"); return False

    data_source_map = {"model": current_model_data, "vae": current_vae_data, "controlnet": current_controlnet_data, "lora": current_lora_data}
    data_source = data_source_map.get(asset_type)
    
    if not data_source or asset_name not in data_source:
        log_output_list.append(f"Warning: Metadata for {asset_type} '{asset_name}' not found. Cannot download.\\n"); return False

    asset_info_list = data_source[asset_name] 
    if not isinstance(asset_info_list, list): asset_info_list = [asset_info_list]

    overall_success_for_asset_group = True
    for file_info in asset_info_list:
        download_url = file_info.get("url")
        filename_from_data = file_info.get("name")
        if not filename_from_data and download_url:
            try: filename_from_data = Path(urlparse(download_url).path).name
            except: pass
        if not download_url or not filename_from_data:
            log_output_list.append(f"Warning: URL/filename missing for an item in {asset_type} '{asset_name}'. Skipping this file.\\n")
            overall_success_for_asset_group = False; continue
        
        target_filename = filename_from_data
        asset_type_plural_map = {"model": "models", "vae": "vaes", "lora": "loras", "controlnet": "controlnet"}
        path_key_for_webui_utils = asset_type_plural_map.get(asset_type, asset_type)
        target_path_full_str = webui_utils.get_webui_asset_path(webui_choice, path_key_for_webui_utils, target_filename)
        
        if not target_path_full_str:
            log_output_list.append(f"Error: Could not get target path for {asset_type} '{target_filename}'. Download aborted.\\n")
            overall_success_for_asset_group = False; continue
            
        log_output_list.append(f"Downloading {asset_type} '{target_filename}' (for '{asset_name}') to {target_path_full_str}...\\n")
        yield "".join(log_output_list)
        
        download_successful = manager_utils.download_url_to_path(
            url=download_url, 
            target_full_path=target_path_full_str, 
            log=True,
            hf_token=hf_token_val, 
            cai_token=civitai_token_val
        )
        
        if download_successful:
            log_output_list.append(f"Successfully downloaded '{target_filename}'.\\n")
        else:
            log_output_list.append(f"Failed to download '{target_filename}'. Check Manager logs or previous messages.\\n")
            overall_success_for_asset_group = False
        yield "".join(log_output_list)
            
    return overall_success_for_asset_group

def launch_anxlight_main_process(
    webui_choice, sd_version, inpainting_models_filter_val,
    selected_models, selected_vaes, selected_controlnets, selected_loras,
    update_webui_val, update_extensions_val, check_custom_nodes_val, detailed_download_val,
    commit_hash_val, civitai_token_val, huggingface_token_val, zrok_token_val, ngrok_token_val,
    custom_args_val, theme_accent_val
):
    log_output_list = [f"--- {APP_DISPLAY_VERSION} Backend Process Initializing (System: {SYSTEM_DISPLAY_VERSION}) ---\\n"]
    log_output_list.append(f"Pre-Flight Setup Script Version (expected by this app): v{PRE_FLIGHT_SETUP_PY_VERSION}\\n"); yield "".join(log_output_list)

    if json_utils is None: log_output_list.append("FATAL: json_utils module not loaded.\\n"); yield "".join(log_output_list); return
    if isinstance(webui_utils, _DummyWebUIUtilsModule): log_output_list.append("Warning: webui_utils module not fully loaded (dummy).\\n")
    if isinstance(manager_utils, _DummyManagerModule): log_output_list.append("Warning: Manager module not fully loaded (dummy). Asset downloads may fail or use dummy.\\n")
    
    load_data_for_sd_version(sd_version) 

    local_project_root = PROJECT_ROOT; log_output_list.append(f"Project Root: {local_project_root}\\n")
    log_session_dir = None
    if detailed_download_val:
        try:
            log_dir_base = os.path.join(local_project_root, 'logs'); log_session_dir = os.path.join(log_dir_base, f'session_{time.strftime("%Y%m%d-%H%M%S")}')
            os.makedirs(log_session_dir, exist_ok=True); log_output_list.append(f"Detailed logging enabled. Session logs: {log_session_dir}\\n")
        except Exception as e: log_output_list.append(f"Warning: Could not create log dir {log_session_dir}: {e}\\n"); log_session_dir = None
    else: log_output_list.append("Detailed file logging disabled.\\n")
    yield "".join(log_output_list)

    log_output_list.append(f"\\n--- Step 1: Verifying WebUI '{webui_choice}' Installation ---\\n")
    log_output_list.append(f"NOTE: WebUI installation is handled by 'scripts/pre_flight_setup.py'. Assuming '{webui_choice}' is installed.\\n")
    if not isinstance(webui_utils, _DummyWebUIUtilsModule): 
        webui_root_path_str = webui_utils.get_webui_installation_root(webui_choice)
        if not webui_root_path_str or not Path(webui_root_path_str).exists():
            log_output_list.append(f"CRITICAL WARNING: Installation directory for '{webui_choice}' not found at '{webui_root_path_str}'. Pre-flight setup may be needed or path is incorrect.\\n")
        else: log_output_list.append(f"Verified installation directory for '{webui_choice}' at '{webui_root_path_str}'.\\n")
    yield "".join(log_output_list)

    log_output_list.append(f"\\n--- Step 2: Downloading Selected Session Assets ---\\n"); yield "".join(log_output_list)
    assets_to_process = [("model", selected_models), ("vae", selected_vaes), ("controlnet", selected_controlnets), ("lora", selected_loras)]
    overall_asset_download_success = True
    for asset_type, asset_names_list in assets_to_process:
        if asset_names_list:
            for asset_name in asset_names_list:
                if not download_selected_asset(asset_name, asset_type, sd_version, webui_choice, log_output_list, huggingface_token_val, civitai_token_val):
                    overall_asset_download_success = False 
                yield "".join(log_output_list) 
        else: log_output_list.append(f"No {asset_type}s selected for download.\\n"); yield "".join(log_output_list)
    if not overall_asset_download_success: log_output_list.append("Warning: One or more assets may have failed to download. Check logs above.\\n")
    yield "".join(log_output_list)

    log_output_list.append(f"\\n--- Step 3: Generating Configuration File ---\\n"); widgets_data = {}
    try:
        widgets_data.update({
            'XL_models': (sd_version == "SDXL"), 'model': selected_models[0] if selected_models else "none",
            'model_num': ",".join(selected_models) if selected_models else "",
            'inpainting_model': (inpainting_models_filter_val == "Inpainting Models Only"), 
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
                            'venv_path': os.environ.get('venv_path', str(Path(PROJECT_ROOT) / "anxlight_venv")), 
                            'fork': "drf0rk/AnxLight", 'branch': subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=PROJECT_ROOT).strip().decode('utf-8'),
                            'start_timer': int(time.time() - 5), 'public_ip': ""}
        anxlight_config = {"WIDGETS": widgets_data, "ENVIRONMENT": environment_data, "UI_SELECTION": {"webui_choice": webui_choice}}
        log_output_list.append("Configuration dictionary constructed.\\n")
    except Exception as e: log_output_list.append(f"Error constructing config: {e}\\nTraceback: {traceback.format_exc()}\\n"); yield "".join(log_output_list); return
    config_file_path = Path(environment_data['settings_path'])
    try:
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, 'w') as f: json.dump(anxlight_config, f, indent=4)
        log_output_list.append(f"Config saved to: {config_file_path}\\n")
    except Exception as e: log_output_list.append(f"Error saving config to {config_file_path}: {e}\\nTraceback: {traceback.format_exc()}\\n"); yield "".join(log_output_list); return
    yield "".join(log_output_list)

    log_output_list.append(f"\\n--- Step 4: Updating WebUI Paths in Config ---\\n")
    try:
        if not isinstance(webui_utils, _DummyWebUIUtilsModule): webui_utils.update_current_webui(webui_choice); log_output_list.append(f"Called webui_utils.update_current_webui for '{webui_choice}'.\\n")
        else: log_output_list.append(f"Warning: webui_utils dummy/not loaded. update_current_webui for '{webui_choice}' skipped/dummy.\\n");_ = webui_utils.update_current_webui(webui_choice) if webui_utils else None
    except Exception as e: log_output_list.append(f"Error calling webui_utils.update_current_webui: {e}\\nTraceback: {traceback.format_exc()}\\n")
    yield "".join(log_output_list)
        
    log_output_list.append(f"\\n--- Step 5: Initiating Launch Script ---\\n")
    launch_script_path = os.path.join(environment_data['scr_path'], 'scripts', 'launch.py')
    log_output_list.append(f"Attempting to run launch script (v{LAUNCH_PY_VERSION}): {launch_script_path}\\n"); yield "".join(log_output_list)
    launch_success = False
    for exec_status in _execute_backend_script(launch_script_path, LAUNCH_PY_VERSION, "launch.log", "[Launcher]", detailed_download_val, log_session_dir, log_output_list):
        if exec_status == "SCRIPT_EXECUTION_SUCCESS": launch_success = True
        elif exec_status == "SCRIPT_EXECUTION_FAILURE": launch_success = False
        else: yield exec_status 
    log_output_list.append(f"--- Launch script {'finished successfully' if launch_success else 'failed or status unclear'}. WebUI may be starting. ---\\n")
    yield "".join(log_output_list)

with gr.Blocks(css=".gradio-container {max-width: 90% !important; margin: auto !important;}") as demo:
    gr.Markdown(f"# AnxLight Launcher ({APP_DISPLAY_VERSION})")
    # Load initial data with a default value before the UI components are fully defined
    load_data_for_sd_version(SD_VERSION_CHOICES[0]) 
    _initial_models, _initial_vaes, _initial_controlnets, _initial_loras = get_asset_choices(SD_VERSION_CHOICES[0], INPAINTING_FILTER_CHOICES[0])
    _initial_webui = WEBUI_CHOICES[0]; _initial_is_comfy = (_initial_webui == 'ComfyUI')
    with gr.Tabs():
        with gr.TabItem("Session Configuration"): 
            gr.Markdown("## Main Configuration")
            with gr.Row(): 
                webui_choice_dd = gr.Dropdown(label="Select WebUI", choices=WEBUI_CHOICES, value=_initial_webui, interactive=True)
                sd_version_rb = gr.Radio(label="Model Version", choices=SD_VERSION_CHOICES, value=SD_VERSION_CHOICES[0], interactive=True)
            inpainting_filter_rg = gr.Radio(label="Model Type Filter", info="Filters the 'Select Models' list below.", choices=INPAINTING_FILTER_CHOICES, value=INPAINTING_FILTER_CHOICES[0], interactive=True)
            with gr.Row(equal_height=False): 
                update_webui_chk = gr.Checkbox(label="Update WebUI Components (Daily)", value=False, info="If pre-flight setup allows for daily/minor updates of WebUI components.")
                update_extensions_chk = gr.Checkbox(label="Update Extensions (Daily)", value=False, info="If pre-flight setup allows for daily/minor updates of extensions.", visible=not _initial_is_comfy)
                check_custom_nodes_deps_chk = gr.Checkbox(label="Check ComfyUI Nodes Deps (on Launch)", value=True, visible=_initial_is_comfy, info="For ComfyUI, check custom node dependencies during launch process.")
                detailed_download_chk = gr.Checkbox(label="Detailed Session Log", value=True, info="Enable detailed UI and file logging for this session's processes.")
            gr.Markdown("### Assets Selection (for this session)")
            with gr.Row(): 
                models_cbg = gr.CheckboxGroup(label="Select Models", choices=_initial_models, value=[], interactive=bool(_initial_models))
                vaes_cbg = gr.CheckboxGroup(label="Select VAEs", choices=_initial_vaes, value=[], interactive=bool(_initial_vaes))
            with gr.Row(): 
                controlnets_cbg = gr.CheckboxGroup(label="Select ControlNets", choices=_initial_controlnets, value=[], interactive=bool(_initial_controlnets))
                loras_cbg = gr.CheckboxGroup(label="Select LoRAs", choices=_initial_loras, value=[], interactive=bool(_initial_loras))
            gr.Markdown("### Advanced Options"); commit_hash_tb = gr.Textbox(label="WebUI Commit Hash (For Pre-Flight Setup)", info="If pre-flight needs to install a specific WebUI version. Run Cell 1 after setting.", placeholder="e.g., a1b2c3d...")
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
    print(f"Launching Gradio App for AnxLight ({APP_DISPLAY_VERSION})...")
    if DATA_MODULE_PATH not in sys.path: sys.path.insert(0, DATA_MODULE_PATH)
    demo.queue().launch(debug=True, share=os.environ.get("GRADIO_SHARE", "true").lower() == "true", prevent_thread_lock=True, show_error=True)