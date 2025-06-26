# scripts/main_gradio_app_v2.py
# Version 2.0.2 - Fleshed out UI and backend logic more comprehensively.

import os
os.environ['MPLBACKEND'] = 'Agg' # Set backend BEFORE any other imports

import gradio as gr
import sys
import subprocess
import time
import json
from pathlib import Path
import traceback
import pprint

# --- Robust Path Setup ---
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
MODULES_PATH = PROJECT_ROOT / 'modules'
SCRIPTS_DATA_PATH = SCRIPT_DIR / 'data' 

for p_item in [SCRIPT_DIR, PROJECT_ROOT, MODULES_PATH, SCRIPTS_DATA_PATH]:
    if str(p_item) not in sys.path:
        sys.path.insert(0, str(p_item))

# --- Versioning ---
APP_SCRIPT_VERSION = "2.0.2"
LAUNCH_PY_VERSION = ANXLIGHT_OVERALL_SYSTEM_VERSION = PRE_FLIGHT_SETUP_PY_VERSION = "unknown" # Defaults
try:
    from anxlight_version import (
        LAUNCH_PY_VERSION as LPV,
        ANXLIGHT_OVERALL_SYSTEM_VERSION as AOSV,
        PRE_FLIGHT_SETUP_PY_VERSION as PFSPV
    )
    LAUNCH_PY_VERSION, ANXLIGHT_OVERALL_SYSTEM_VERSION, PRE_FLIGHT_SETUP_PY_VERSION = LPV, AOSV, PFSPV
    APP_DISPLAY_VERSION = f"AnxLight Gradio App v{APP_SCRIPT_VERSION}"
    SYSTEM_DISPLAY_VERSION = f"AnxLight System v{ANXLIGHT_OVERALL_SYSTEM_VERSION}"
    print(f"--- {APP_DISPLAY_VERSION} (System: {SYSTEM_DISPLAY_VERSION}, Pre-Flight: v{PRE_FLIGHT_SETUP_PY_VERSION}, Launch.py: v{LAUNCH_PY_VERSION}) ---")
except ImportError as e_ver:
    print(f"[CRITICAL] Failed to import versions from anxlight_version.py: {e_ver}. Using placeholders.")
    APP_DISPLAY_VERSION = f"AnxLight Gradio App v{APP_SCRIPT_VERSION} (Version File Error)"

# --- Module Imports ---
# Data modules
sd15_model_data, sd15_vae_data, sd15_controlnet_data, sd15_lora_data = {}, {}, {}, {}
sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data, sdxl_lora_data = {}, {}, {}, {}
try:
    from sd15_data import sd15_model_data as s15md, sd15_vae_data as s15vd, sd15_controlnet_data as s15cd, sd15_lora_data as s15ld
    sd15_model_data, sd15_vae_data, sd15_controlnet_data, sd15_lora_data = s15md, s15vd, s15cd, s15ld
    from sdxl_data import sdxl_model_data as sxlmd, sdxl_vae_data as sxlvd, sdxl_controlnet_data as sxlcd, sdxl_lora_data as sxlld
    sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data, sdxl_lora_data = sxlmd, sxlvd, sxlcd, sxlld
    print("Successfully imported data modules from scripts/data.")
except ImportError as e: print(f"Warning: Error importing data modules: {e}. UI choices will be limited.")

# Utility modules
manager_m_download_func = None
json_utils_save_func = None
json_utils_load_func = None
webui_utils_update_current_webui_func = None
webui_utils_get_webui_asset_path_func = None

try:
    from Manager import m_download # Assuming m_download is a function in Manager.py
    manager_m_download_func = m_download
    print("Successfully imported m_download from Manager module.")
except ImportError as e: print(f"Warning: Error importing m_download from Manager: {e}. Downloads will fail.")

try:
    from json_utils import save, load # Assuming save and load are functions
    json_utils_save_func = save
    json_utils_load_func = load
    print("Successfully imported save and load from json_utils module.")
except ImportError as e: print(f"Warning: Error importing from json_utils: {e}. Config operations may fail.")

try:
    from webui_utils import update_current_webui, get_webui_asset_path 
    webui_utils_update_current_webui_func = update_current_webui
    webui_utils_get_webui_asset_path_func = get_webui_asset_path
    print("Successfully imported webui_utils module.")
except ImportError as e: print(f"Warning: Error importing webui_utils: {e}. Path functions will fail.")


# --- UI Constants and Helper Functions ---
WEBUI_CHOICES = ["A1111", "ComfyUI", "Forge", "Classic", "ReForge", "SD-UX"] 
SD_VERSION_CHOICES = ["SD1.5", "SDXL"]
THEME_CHOICES = ["Default", "gradio/soft", "gradio/base", "gradio/glass", "gradio/monochrome"] 
INPAINTING_FILTER_CHOICES = ["Show All Models", "Inpainting Models Only", "No Inpainting Models"]
WEBUI_DEFAULT_ARGS = {
    'A1111': "--xformers --no-half-vae --skip-version-check", 
    'ComfyUI': "--preview-method auto", 
    'Forge': "--xformers --cuda-stream --pin-shared-memory --skip-version-check",
    'Classic': "--xformers --no-half-vae --skip-version-check",
    'ReForge': "--xformers --no-half-vae --skip-version-check",
    'SD-UX': "" 
}

def get_asset_choices_v2(sd_version, inpainting_filter_mode="Show All Models"):
    print(f"[get_asset_choices_v2] Called with sd_version: {sd_version}, filter: {inpainting_filter_mode}")
    if sd_version == "SD1.5":
        models_src, vaes_src, controlnets_src, loras_src = sd15_model_data, sd15_vae_data, sd15_controlnet_data, sd15_lora_data
    else: # SDXL
        models_src, vaes_src, controlnets_src, loras_src = sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data, sdxl_lora_data

    models = [name for name, data in models_src.items() if name != "ERROR: Module Load Failed" and (
                (inpainting_filter_mode == "Show All Models") or
                (inpainting_filter_mode == "Inpainting Models Only" and data.get("inpainting", False)) or
                (inpainting_filter_mode == "No Inpainting Models" and not data.get("inpainting", False)))]
    vaes = list(vaes_src.keys()) if vaes_src else []
    controlnets = list(controlnets_src.keys()) if controlnets_src else []
    loras = list(loras_src.keys()) if loras_src else []
    
    if "ERROR: Module Load Failed" in models: models.remove("ERROR: Module Load Failed")
    # Provide default if list is empty after filtering
    models = models or ["(No models match filter)"]
    vaes = vaes or ["(No VAEs available)"]
    controlnets = controlnets or ["(No ControlNets available)"]
    loras = loras or ["(No LoRAs available)"]
    return models, vaes, controlnets, loras

def update_all_ui_elements_v2(sd_version_selected, inpainting_filter_selected, webui_selected):
    print(f"[update_all_ui_elements_v2] Args: sd_ver='{sd_version_selected}', filter='{inpainting_filter_selected}', webui='{webui_selected}'")
    models, vaes, controlnets, loras = get_asset_choices_v2(sd_version_selected, inpainting_filter_selected)
    default_args = WEBUI_DEFAULT_ARGS.get(webui_selected, "")
    is_comfy = (webui_selected == 'ComfyUI')
    
    check_nodes_visible = is_comfy
    update_ext_visible = not is_comfy 
    theme_accent_visible = not is_comfy

    return (gr.update(choices=models, value=[]), 
            gr.update(choices=vaes, value=[]), 
            gr.update(choices=controlnets, value=[]), 
            gr.update(choices=loras, value=[]),
            gr.update(value=default_args), 
            gr.update(visible=update_ext_visible),
            gr.update(visible=check_nodes_visible),
            gr.update(visible=theme_accent_visible))

def _log_and_yield(log_output_list, message):
    """Helper to append message and yield the whole list."""
    print(f"[Backend Log] {message.strip()}") # Also print to server console for easier debugging
    log_output_list.append(message)
    return "".join(log_output_list)

def _execute_launch_script(log_output_list):
    launch_script_path_rel = 'scripts/launch.py'
    full_script_path = PROJECT_ROOT / launch_script_path_rel
    yield _log_and_yield(log_output_list, f"Executing: {sys.executable} {full_script_path} (v{LAUNCH_PY_VERSION})...\\n")
    
    process = subprocess.Popen([sys.executable, str(full_script_path)], 
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, bufsize=1, universal_newlines=True, 
                               env=os.environ.copy(), cwd=PROJECT_ROOT)
    if process.stdout:
        for line in iter(process.stdout.readline, ''):
            yield _log_and_yield(log_output_list, f"[launch.py] {line.strip()}\\n")
        process.stdout.close()
    process.wait()
    yield _log_and_yield(log_output_list, f"[launch.py] Script finished with return code {process.returncode}.\\n")
    return process.returncode == 0

def download_asset_wrapper_v2(asset_name, asset_type, sd_version, webui_choice, log_output_list):
    # This wrapper calls the imported manager_m_download_func
    yield _log_and_yield(log_output_list, f"--- Preparing to download {asset_type}: '{asset_name}' ---\\n")
    
    data_source = None
    if asset_type == "model": data_source = sd15_model_data if sd_version == "SD1.5" else sdxl_model_data
    elif asset_type == "vae": data_source = sd15_vae_data if sd_version == "SD1.5" else sdxl_vae_data
    # ... (add elif for lora, controlnet)
    else: data_source = {} # Default empty if type unknown

    if not data_source: yield _log_and_yield(log_output_list, f"ERROR: No data source for '{asset_type}'.\\n"); return False
    asset_info = data_source.get(asset_name)
    if not asset_info: yield _log_and_yield(log_output_list, f"ERROR: No asset_info for '{asset_name}'.\\n"); return False
    
    download_url, filename_in_repo = asset_info.get("url"), asset_info.get("filename")
    if not download_url or not filename_in_repo: yield _log_and_yield(log_output_list, f"ERROR: Missing URL/filename for '{asset_name}'.\\n"); return False
    
    target_dir_type_map = {"model": "models", "vae": "vaes", "lora": "loras", "controlnet": "controlnet"}
    target_dir_type = target_dir_type_map.get(asset_type)
    if not target_dir_type: yield _log_and_yield(log_output_list, f"ERROR: Unknown target dir for '{asset_type}'.\\n"); return False
    
    if not callable(webui_utils_get_webui_asset_path_func): yield _log_and_yield(log_output_list, "ERROR: webui_utils_get_webui_asset_path_func not available.\\n"); return False
    target_path_full = webui_utils_get_webui_asset_path_func(webui_choice, target_dir_type, filename_in_repo)
    yield _log_and_yield(log_output_list, f"Target path: {target_path_full}\\n")
    
    if not callable(manager_m_download_func): yield _log_and_yield(log_output_list, "ERROR: manager_m_download_func not available.\\n"); return False
    try:
        download_instruction = f"{download_url} {Path(target_path_full).parent} {filename_in_repo}"
        yield _log_and_yield(log_output_list, f"Calling Manager with: {download_instruction}\\n")
        # Pass a lambda that appends to log_output_list and yields for real-time logging from Manager
        def manager_log_cb(msg): nonlocal log_output_list; yield _log_and_yield(log_output_list, f"[Manager] {msg.strip()}\\n")
        
        # This part is tricky if m_download itself is not a generator.
        # If m_download is blocking and uses a callback for logs:
        # manager_m_download_func(download_instruction, log_callback=lambda m: log_output_list.append(f"[Manager] {m}\\n"))
        # For now, assume m_download is blocking and we log after.
        manager_m_download_func(download_instruction, log=True) # Assuming log=True makes it print to its own stdout
                                                            # which we are not capturing from there directly.
                                                            # A better Manager would take a log_func.
        yield _log_and_yield(log_output_list, f"SUCCESS: Download call for {asset_type} '{asset_name}' completed.\\n")
        return True
    except Exception as e_dl:
        yield _log_and_yield(log_output_list, f"EXCEPTION downloading '{asset_name}': {str(e_dl)}\\nTraceback:\\n{traceback.format_exc()}\\n")
        return False

def launch_anxlight_main_process_v2(
    webui_choice, sd_version, models_selected, vaes_selected, 
    controlnets_selected, loras_selected, update_webui, 
    update_extensions, check_custom_nodes_deps, detailed_download,
    commit_hash, civitai_token, huggingface_token, zrok_token,
    ngrok_token, custom_args, theme_accent, 
    request: gr.Request 
):
    log_output_list = []
    yield _log_and_yield(log_output_list, f"--- AnxLight Backend Process v{APP_SCRIPT_VERSION} Starting ---\\nTimestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
    start_time_proc = time.time()
    try:
        args_for_log = {k:v for k,v in locals().items() if k not in ['civitai_token', 'huggingface_token', 'zrok_token', 'ngrok_token', 'request', 'log_output_list', 'start_time_proc']}
        yield _log_and_yield(log_output_list, f"Received parameters (tokens masked):\\n{pprint.pformat(args_for_log)}\\n")

        yield _log_and_yield(log_output_list, "Step 1: Preparing configuration...\\n")
        config_data = {
            'webui_choice': webui_choice, 'sd_version': sd_version,
            'selected_assets': {'models': models_selected or [], 'vaes': vaes_selected or [], 
                                'controlnets': controlnets_selected or [], 'loras': loras_selected or []},
            'tokens': {'civitai': civitai_token, 'huggingface': huggingface_token, 'zrok': zrok_token, 'ngrok': ngrok_token},
            'launch_args': custom_args, 'commit_hash': commit_hash,
            'options': {'update_webui': update_webui, 'update_extensions': update_extensions, 
                        'check_deps': check_custom_nodes_deps, 'detailed_log': detailed_download, 'theme': theme_accent}
        }
        yield _log_and_yield(log_output_list, "Config data prepared.\\n")
        
        yield _log_and_yield(log_output_list, "Step 2: Saving configuration...\\n")
        config_path = PROJECT_ROOT / 'anxlight_config.json'
        try:
            if callable(json_utils_save_func):
                json_utils_save_func(str(config_path), "WIDGETS", config_data) 
                yield _log_and_yield(log_output_list, f"Config saved to {config_path}\\n")
            else: yield _log_and_yield(log_output_list, "ERROR: json_utils_save_func not available. Config not saved.\\n")
        except Exception as e_cfg_save: yield _log_and_yield(log_output_list, f"ERROR saving config: {str(e_cfg_save)}\\n{traceback.format_exc()}\\n")
        
        yield _log_and_yield(log_output_list, f"Step 3: Updating WebUI paths for '{webui_choice}'...\\n")
        try:
            if callable(webui_utils_update_current_webui_func): webui_utils_update_current_webui_func(webui_choice)
            yield _log_and_yield(log_output_list, "WebUI paths updated.\\n")
        except Exception as e_webui_paths: yield _log_and_yield(log_output_list, f"ERROR updating WebUI paths: {str(e_webui_paths)}\\n{traceback.format_exc()}\\n")

        yield _log_and_yield(log_output_list, "Step 4: Asset Downloads...\\n")
        overall_assets_success = True
        for asset_type, asset_names_list in config_data['selected_assets'].items():
            if asset_names_list:
                for asset_name in asset_names_list:
                    # download_asset_wrapper_v2 is a generator, iterate through its yields
                    dl_success_flag_for_asset = False
                    for status_yield in download_asset_wrapper_v2(asset_name, asset_type, sd_version, webui_choice, log_output_list):
                        if isinstance(status_yield, bool): dl_success_flag_for_asset = status_yield
                        else: yield status_yield # Pass through log yields
                    if not dl_success_flag_for_asset: overall_assets_success = False
        if not overall_assets_success: yield _log_and_yield(log_output_list, "WARNING: One or more assets failed to download properly.\\n")
        
        yield _log_and_yield(log_output_list, f"Step 5: Launching {webui_choice} via scripts/launch.py...\\n")
        launch_successful = False
        try:
            for _ in _execute_launch_script(log_output_list): yield _
            if f"[launch.py] Script finished with return code 0" in "".join(log_output_list[-2:]): launch_successful = True
        except Exception as e_launch: yield _log_and_yield(log_output_list, f"EXCEPTION during launch.py execution: {str(e_launch)}\\n{traceback.format_exc()}\\n")
        
        if launch_successful: yield _log_and_yield(log_output_list, f"--- {webui_choice} launch process initiated successfully by launch.py. ---\\n")
        else: yield _log_and_yield(log_output_list, f"--- ERROR: {webui_choice} launch process via launch.py failed. ---\\n")
    except Exception as e_main:
        yield _log_and_yield(log_output_list, f"---!!! TOP LEVEL EXCEPTION !!!---\\nError: {str(e_main)}\\nTraceback:\\n{traceback.format_exc()}\\n")
    finally:
        yield _log_and_yield(log_output_list, f"--- Backend Process Finished. Total time: {time.time() - start_time_proc:.2f}s ---\\n")

# --- Gradio UI Definition ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"# {APP_DISPLAY_VERSION}")
    gr.Markdown(f"System: {SYSTEM_DISPLAY_VERSION} | Pre-Flight: v{PRE_FLIGHT_SETUP_PY_VERSION} | Launch.py: v{LAUNCH_PY_VERSION}")

    _initial_models, _initial_vaes, _initial_cn, _initial_loras = get_asset_choices_v2(SD_VERSION_CHOICES[0], INPAINTING_FILTER_CHOICES[0])

    with gr.Tabs():
        with gr.TabItem("Session Configuration"):
            gr.Markdown("### Configure your WebUI session")
            with gr.Row():
                webui_choice_dd = gr.Dropdown(label="Select WebUI", choices=WEBUI_CHOICES, value=WEBUI_CHOICES[0], interactive=True)
                sd_version_rb = gr.Radio(label="Model Version", choices=SD_VERSION_CHOICES, value=SD_VERSION_CHOICES[0], type="value", interactive=True)
            inpainting_filter_rg = gr.Radio(label="Model Type Filter", info="Filters the 'Select Models' list below.", choices=INPAINTING_FILTER_CHOICES, value=INPAINTING_FILTER_CHOICES[0], type="value", interactive=True)
            with gr.Row(equal_height=False):
                update_webui_chk = gr.Checkbox(label="Update WebUI Components (Daily)", value=False, interactive=True)
                update_extensions_chk = gr.Checkbox(label="Update Extensions (Daily)", value=False, interactive=True)
                check_custom_nodes_deps_chk = gr.Checkbox(label="Check ComfyUI Nodes Deps (on Launch)", value=True, visible=(WEBUI_CHOICES[0] == 'ComfyUI'), interactive=True)
                detailed_download_chk = gr.Checkbox(label="Detailed Session Log (in Colab)", value=True, interactive=True)
            
            models_cbg = gr.CheckboxGroup(label="Select Models", choices=_initial_models, value=[], interactive=True)
            vaes_cbg = gr.CheckboxGroup(label="Select VAEs", choices=_initial_vaes, value=[], interactive=True)
            controlnets_cbg = gr.CheckboxGroup(label="Select ControlNets", choices=_initial_cn, value=[], interactive=True)
            loras_cbg = gr.CheckboxGroup(label="Select LoRAs", choices=_initial_loras, value=[], interactive=True)
            
            with gr.Accordion("Advanced & Tokens", open=False):
                commit_hash_tb = gr.Textbox(label="WebUI Commit Hash (Optional)", placeholder="Leave blank for default/latest", interactive=True)
                custom_args_tb = gr.Textbox(label="Custom Launch Arguments (Optional)", placeholder="e.g., --medvram --another-arg", interactive=True)
                theme_accent_dd = gr.Dropdown(label="Launcher UI Theme Accent (Optional)", choices=THEME_CHOICES, value=THEME_CHOICES[0], interactive=True) # Made always visible for now
                civitai_token_tb = gr.Textbox(label="CivitAI API Key (Optional)", type="password", interactive=True)
                huggingface_token_tb = gr.Textbox(label="HuggingFace Token (Optional)", type="password", interactive=True)
                zrok_token_tb = gr.Textbox(label="Zrok Token (Optional, for zrok tunneling)", type="password", interactive=True)
                ngrok_token_tb = gr.Textbox(label="NGROK Token (Optional, for ngrok tunneling)", type="password", interactive=True)

        with gr.TabItem("Launch & Live Log"):
            launch_button = gr.Button("Download Assets & Launch WebUI", variant="primary", scale=2) # Made button larger
            live_log_ta = gr.Textbox(label="Live Log", lines=30, interactive=False, autoscroll=True) # Increased lines
    
    all_launch_inputs = [
        webui_choice_dd, sd_version_rb, models_cbg, vaes_cbg, controlnets_cbg,
        loras_cbg, update_webui_chk, update_extensions_chk, check_custom_nodes_deps_chk,
        detailed_download_chk, commit_hash_tb, civitai_token_tb, huggingface_token_tb,
        zrok_token_tb, ngrok_token_tb, custom_args_tb, theme_accent_dd
    ] 
    change_event_inputs = [sd_version_rb, inpainting_filter_rg, webui_choice_dd]
    dynamic_ui_outputs = [models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, 
                          custom_args_tb, update_extensions_chk, 
                          check_custom_nodes_deps_chk, theme_accent_dd]
    
    sd_version_rb.change(fn=update_all_ui_elements_v2, inputs=change_event_inputs, outputs=dynamic_ui_outputs)
    inpainting_filter_rg.change(fn=update_all_ui_elements_v2, inputs=change_event_inputs, outputs=dynamic_ui_outputs)
    webui_choice_dd.change(fn=update_all_ui_elements_v2, inputs=change_event_inputs, outputs=dynamic_ui_outputs)
    
    launch_button.click(fn=launch_anxlight_main_process_v2, inputs=all_launch_inputs, outputs=[live_log_ta])

if __name__ == "__main__":
    print(f"Launching {APP_DISPLAY_VERSION}...")
    demo.launch(debug=True, share=True, show_error=True) 
    print(f"{APP_DISPLAY_VERSION} server launched. Keeping script alive...")
    while True: 
        time.sleep(1)