# scripts/main_gradio_app.py
# v1.0.10: Test: Remove .queue() from launch, set debug=True. No-args callback remains.
# v1.0.9: No-Args Callback Test for launch_anxlight_main_process.
# v1.0.8: Simplified initial logging in launch_anxlight_main_process for pinpointing hangs.

import gradio as gr
import os
import sys
import threading
import subprocess
import time
import json
from pathlib import Path
import traceback
import pprint 

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
MODULES_PATH = os.path.join(PROJECT_ROOT, 'modules')
SCRIPTS_PATH = os.path.join(PROJECT_ROOT, 'scripts')
sys.path.insert(0, SCRIPTS_PATH)
if SCRIPT_DIR not in sys.path: sys.path.insert(0, SCRIPT_DIR)
if PROJECT_ROOT not in sys.path: sys.path.insert(1, PROJECT_ROOT)
if MODULES_PATH not in sys.path: sys.path.insert(0, MODULES_PATH)

try:
    from anxlight_version import (
        MAIN_GRADIO_APP_VERSION, 
        LAUNCH_PY_VERSION,
        ANXLIGHT_OVERALL_SYSTEM_VERSION,
        PRE_FLIGHT_SETUP_PY_VERSION
    )
    NEW_MAIN_GRADIO_APP_VERSION = "1.0.10" # Script version
    APP_DISPLAY_VERSION = f"AnxLight Gradio App v{NEW_MAIN_GRADIO_APP_VERSION}"
    SYSTEM_DISPLAY_VERSION = f"AnxLight System v{ANXLIGHT_OVERALL_SYSTEM_VERSION}"
    print(f"--- {APP_DISPLAY_VERSION} (System: {SYSTEM_DISPLAY_VERSION}, Pre-Flight: v{PRE_FLIGHT_SETUP_PY_VERSION}) ---")
except ImportError as e_ver:
    print(f"[CRITICAL] Failed to import versions from anxlight_version.py: {e_ver}")
    APP_DISPLAY_VERSION = "AnxLight Gradio App v?.?.? (Version File Error)"
    LAUNCH_PY_VERSION = "unknown"; PRE_FLIGHT_SETUP_PY_VERSION = "unknown"; NEW_MAIN_GRADIO_APP_VERSION = "error_import"

class _DummyDataModule:
    sd15_model_data = {"ERROR: Module Load Failed": {}}; sd15_vae_data, sd15_controlnet_data, sd15_lora_data = {}, {}, {}
    sdxl_model_data = {"ERROR: Module Load Failed": {}}; sdxl_vae_data, sdxl_controlnet_data, sdxl_lora_data = {}, {}, {}
class _DummyWebUIUtilsModule:
    def update_current_webui(self, webui_name): print(f"[_DummyWebUIUtilsModule] update_current_webui for {webui_name}")
    def get_webui_asset_path(self, webui_name, asset_type, asset_filename=""): return os.path.join(PROJECT_ROOT, "models", asset_type, asset_filename)
sd15_data, sdxl_data = _DummyDataModule(), _DummyDataModule(); webui_utils = _DummyWebUIUtilsModule(); json_utils, manager_utils = None, None
try:
    DATA_MODULE_PATH = os.path.join(SCRIPTS_PATH, 'data')
    if DATA_MODULE_PATH not in sys.path: sys.path.insert(0, DATA_MODULE_PATH)
    from sd15_data import sd15_model_data, sd15_vae_data, sd15_controlnet_data, sd15_lora_data
    sd15_data.sd15_model_data, sd15_data.sd15_vae_data, sd15_data.sd15_controlnet_data, sd15_data.sd15_lora_data = sd15_model_data, sd15_vae_data, sd15_controlnet_data, sd15_lora_data
    from sdxl_data import sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data, sdxl_lora_data
    sdxl_data.sdxl_model_data, sdxl_data.sdxl_vae_data, sdxl_data.sdxl_controlnet_data, sdxl_data.sdxl_lora_data = sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data, sdxl_lora_data
    print("Successfully imported real data modules.")
except ImportError as e: print(f"Warning: Error importing data modules: {e}. Using dummy data.")
try:
    from modules import json_utils as real_json_utils, webui_utils as real_webui_utils, Manager as real_manager_utils
    json_utils, webui_utils, manager_utils = real_json_utils, real_webui_utils, real_manager_utils
    print("Successfully imported real backend utility modules.")
except ImportError as e: print(f"FATAL: Error importing backend utility modules: {e}.")

WEBUI_CHOICES = ["A1111", "ComfyUI", "Forge"]; SD_VERSION_CHOICES = ["SD1.5", "SDXL"]
THEME_CHOICES = ["Default", "anxety", "blue", "green", "peach", "pink", "red", "yellow"]
INPAINTING_FILTER_CHOICES = ["Show All Models", "Inpainting Models Only", "No Inpainting Models"]
WEBUI_DEFAULT_ARGS = {'A1111': "--xformers --no-half-vae", 'ComfyUI': "--preview-method auto", 'Forge': "--xformers --cuda-stream --pin-shared-memory"}

def get_asset_choices(sd_version, inpainting_filter_mode="Show All Models"):
    models_data_source = sd15_data.sd15_model_data if sd_version == "SD1.5" else sdxl_data.sdxl_model_data
    filtered_models_keys = [name for name, data in models_data_source.items() if name != "ERROR: Module Load Failed" and (
                            (inpainting_filter_mode == "Show All Models") or
                            (inpainting_filter_mode == "Inpainting Models Only" and data.get("inpainting", False)) or
                            (inpainting_filter_mode == "No Inpainting Models" and not data.get("inpainting", False)))]
    models = filtered_models_keys
    if sd_version == "SD1.5": vaes, controlnets, loras = list(sd15_data.sd15_vae_data.keys()), list(sd15_data.sd15_controlnet_data.keys()), list(sd15_data.sd15_lora_data.keys())
    elif sd_version == "SDXL": vaes, controlnets, loras = list(sdxl_data.sdxl_vae_data.keys()), list(sdxl_data.sdxl_controlnet_data.keys()), list(sdxl_data.sdxl_lora_data.keys())
    else: vaes, controlnets, loras = [], [], []
    return models, vaes, controlnets, loras

def update_all_ui_elements(sd_version_selected, inpainting_filter_selected, webui_selected):
    models, vaes, controlnets, loras = get_asset_choices(sd_version_selected, inpainting_filter_selected)
    default_args = WEBUI_DEFAULT_ARGS.get(webui_selected, ""); is_comfy = (webui_selected == 'ComfyUI')
    return (gr.update(choices=models, value=[]), gr.update(choices=vaes, value=[]), gr.update(choices=controlnets, value=[]),
            gr.update(choices=loras, value=[]), gr.update(value=default_args), gr.update(visible=not is_comfy),
            gr.update(visible=is_comfy), gr.update(visible=not is_comfy, value=THEME_CHOICES[0]))

# ***** RETAINING NO-ARGS TEST VERSION OF THIS FUNCTION *****
def launch_anxlight_main_process(): # NO ARGUMENTS
    current_app_version = NEW_MAIN_GRADIO_APP_VERSION if 'NEW_MAIN_GRADIO_APP_VERSION' in globals() else 'unknown_debug_no_args'
    log_output_list = [f"--- launch_anxlight_main_process v{current_app_version} (NO_ARGS_TEST) ENTERED ---\\n"]
    yield "".join(log_output_list)
    
    log_output_list.append("NO_ARGS_TEST: If you see this, the basic callback and yield are working.\\n")
    yield "".join(log_output_list)
    
    time.sleep(2) # Simulate some work
    
    log_output_list.append("NO_ARGS_TEST: Test completed successfully.\\n")
    yield "".join(log_output_list)

with gr.Blocks() as demo:
    gr.Markdown(f"# {APP_DISPLAY_VERSION}")
    # UI definition remains the same, but launch_button click is simplified
    _initial_models, _initial_vaes, _initial_controlnets, _initial_loras = get_asset_choices(SD_VERSION_CHOICES[0], INPAINTING_FILTER_CHOICES[0])
    with gr.Tabs():
        with gr.TabItem("Session Configuration"):
            with gr.Row():
                webui_choice_dd = gr.Dropdown(label="Select WebUI", choices=WEBUI_CHOICES, value=WEBUI_CHOICES[0], interactive=True)
                sd_version_rb = gr.Radio(label="Model Version", choices=SD_VERSION_CHOICES, value=SD_VERSION_CHOICES[0], interactive=True)
            # ... (rest of UI components as in v1.0.9) ...
            inpainting_filter_rg = gr.Radio(label="Model Type Filter", info="Filters the 'Select Models' list below.", choices=INPAINTING_FILTER_CHOICES, value=INPAINTING_FILTER_CHOICES[0], interactive=True)
            with gr.Row(equal_height=False):
                update_webui_chk = gr.Checkbox(label="Update WebUI Components (Daily)", value=False)
                update_extensions_chk = gr.Checkbox(label="Update Extensions (Daily)", value=False)
                check_custom_nodes_deps_chk = gr.Checkbox(label="Check ComfyUI Nodes Deps (on Launch)", value=True, visible=False)
                detailed_download_chk = gr.Checkbox(label="Detailed Session Log", value=True)
            models_cbg = gr.CheckboxGroup(label="Select Models", choices=_initial_models, value=[])
            vaes_cbg = gr.CheckboxGroup(label="Select VAEs", choices=_initial_vaes, value=[])
            controlnets_cbg = gr.CheckboxGroup(label="Select ControlNets", choices=_initial_controlnets, value=[])
            loras_cbg = gr.CheckboxGroup(label="Select LoRAs", choices=_initial_loras, value=[])
            commit_hash_tb = gr.Textbox(label="WebUI Commit Hash")
            civitai_token_tb = gr.Textbox(label="CivitAI API Key", type="password")
            huggingface_token_tb = gr.Textbox(label="HuggingFace Token", type="password")
            zrok_token_tb = gr.Textbox(label="Zrok Token", type="password")
            ngrok_token_tb = gr.Textbox(label="NGROK Token", type="password")
            custom_args_tb = gr.Textbox(label="Custom Launch Arguments", value=WEBUI_DEFAULT_ARGS.get(WEBUI_CHOICES[0], ""))
            theme_accent_dd = gr.Dropdown(label="Launcher UI Theme Accent", choices=THEME_CHOICES, value=THEME_CHOICES[0])
        with gr.TabItem("Launch & Live Log"):
            launch_button = gr.Button("Download Assets & Launch WebUI", variant="primary")
            live_log_ta = gr.Textbox(label="Live Log", lines=20, interactive=False, autoscroll=True)
    
    # Event handlers
    sd_version_rb.change(fn=update_all_ui_elements, inputs=[sd_version_rb, inpainting_filter_rg, webui_choice_dd], outputs=[models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, custom_args_tb, update_extensions_chk, check_custom_nodes_deps_chk, theme_accent_dd])
    inpainting_filter_rg.change(fn=update_all_ui_elements, inputs=[sd_version_rb, inpainting_filter_rg, webui_choice_dd], outputs=[models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, custom_args_tb, update_extensions_chk, check_custom_nodes_deps_chk, theme_accent_dd])
    webui_choice_dd.change(fn=update_all_ui_elements, inputs=[sd_version_rb, inpainting_filter_rg, webui_choice_dd], outputs=[models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, custom_args_tb, update_extensions_chk, check_custom_nodes_deps_chk, theme_accent_dd])
    
    # ***** MODIFIED FOR NO-ARGS TEST & NO QUEUE TEST *****
    launch_button.click(fn=launch_anxlight_main_process, inputs=[], outputs=live_log_ta)

if __name__ == "__main__":
    print("Launching Gradio App...")
    # ***** MODIFIED FOR NO QUEUE TEST & DEBUG MODE *****
    demo.launch(debug=True, share=True, show_error=True) 
    print("Gradio server launched. Keeping script alive...")
    while True:
        time.sleep(1)