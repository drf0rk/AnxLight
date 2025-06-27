# scripts/main_gradio_app.py
# v1.2.3: Critical Fix: Restore the missing __main__ block with app.launch() call.
# v1.2.2: Add diagnostic prints to startup to locate import hang.

import gradio as gr
import os
import sys
import subprocess
import time
import json
from pathlib import Path
import traceback

# --- Path and Module Setup ---
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.resolve()
MODULES_PATH = PROJECT_ROOT / 'modules'
SCRIPTS_PATH = PROJECT_ROOT / 'scripts'
DATA_PATH = SCRIPTS_PATH / 'data'
sys.path.insert(0, str(DATA_PATH))
sys.path.insert(0, str(SCRIPTS_PATH))
if str(SCRIPT_DIR) not in sys.path: sys.path.insert(0, str(SCRIPT_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(1, str(PROJECT_ROOT))
if str(MODULES_PATH) not in sys.path: sys.path.insert(0, str(MODULES_PATH))

# --- Versioning & Module Imports ---
try:
    from anxlight_version import ANXLIGHT_OVERALL_SYSTEM_VERSION
    from sd15_data import sd15_model_data, sd15_vae_data, sd15_controlnet_data, sd15_lora_data
    from sdxl_data import sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data, sdxl_lora_data
    import json_utils
    import Manager as manager_utils
    NEW_MAIN_GRADIO_APP_VERSION = "1.2.3"
    APP_DISPLAY_VERSION = f"AnxLight Gradio App v{NEW_MAIN_GRADIO_APP_VERSION}"
    SYSTEM_DISPLAY_VERSION = f"AnxLight System v{ANXLIGHT_OVERALL_SYSTEM_VERSION}"
except ImportError as e:
    print(f"FATAL: A critical module failed to import: {e}. Please check environment.")
    sys.exit(1)

# --- Constants & UI Logic ---
WEBUI_CHOICES = ["A1111", "ComfyUI", "Forge"]
SD_VERSION_CHOICES = ["SD1.5", "SDXL"]
WEBUI_DEFAULT_ARGS = {'A1111': "--xformers --no-half-vae", 'ComfyUI': "--preview-method auto", 'Forge': "--xformers --cuda-stream"}

def get_asset_choices(sd_version):
    if sd_version == "SD1.5":
        return list(sd15_model_data.keys()), list(sd15_vae_data.keys()), list(sd15_controlnet_data.keys()), list(sd15_lora_data.keys())
    else:
        return list(sdxl_model_data.keys()), list(sdxl_vae_data.keys()), list(sdxl_controlnet_data.keys()), list(sdxl_lora_data.keys())

def update_all_ui_elements(sd_version, webui_choice):
    models, vaes, cnets, loras = get_asset_choices(sd_version)
    return gr.update(choices=models), gr.update(choices=vaes), gr.update(choices=cnets), gr.update(choices=loras), gr.update(value=WEBUI_DEFAULT_ARGS.get(webui_choice, ""))

# --- Core Application Logic ---
def launch_anxlight_main_process(webui_choice, sd_version, models, vaes, cnets, loras, custom_args):
    try:
        yield "--- Starting AnxLight Process ---\n"
        config_data = {
            'webui_choice': webui_choice, 'sd_version': sd_version,
            'selected_assets': {'models': models, 'vaes': vaes, 'controlnets': cnets, 'loras': loras},
            'launch_args': custom_args
        }
        yield "Configuration prepared.\n"
        config_path = PROJECT_ROOT / 'anxlight_config.json'
        json_utils.save(config_path, config_data)
        yield f"Config saved to {config_path}\n"

        if any(config_data['selected_assets'].values()):
            yield "\n--- Starting Asset Downloads ---\n"
            for line in manager_utils.download_selected_assets(config_data):
                yield line
            yield "--- Asset Downloads Finished ---\n"
        
        yield f"\n--- Launching {webui_choice} ---\n"
        launch_script_path = SCRIPTS_PATH / 'launch.py'
        venv_python = PROJECT_ROOT / 'anxlight_venv' / 'bin' / 'python'
        
        process = subprocess.Popen([str(venv_python), str(launch_script_path)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=PROJECT_ROOT)
        for line in iter(process.stdout.readline, ''):
            yield line
        process.wait()
        yield f"\n--- Launch Process Terminated (Code: {process.returncode}) ---\n"
            
    except Exception as e:
        yield f"\n--- FATAL ERROR IN LAUNCH PROCESS ---\n"
        yield f"Error: {str(e)}\n"
        yield f"Traceback:\n{traceback.format_exc()}\n"

# --- Gradio UI Construction ---
def setup_gradio_interface():
    _initial_models, _initial_vaes, _initial_cn, _initial_loras = get_asset_choices(SD_VERSION_CHOICES[0])
    with gr.Blocks() as demo:
        gr.Markdown(f"# {APP_DISPLAY_VERSION}")
        with gr.Row():
            webui_choice_dd = gr.Dropdown(label="Select WebUI", choices=WEBUI_CHOICES, value=WEBUI_CHOICES[0])
            sd_version_rb = gr.Radio(label="Model Version", choices=SD_VERSION_CHOICES, value=SD_VERSION_CHOICES[0])
        models_cbg = gr.CheckboxGroup(label="Select Models", choices=_initial_models)
        vaes_cbg = gr.CheckboxGroup(label="Select VAEs", choices=_initial_vaes)
        controlnets_cbg = gr.CheckboxGroup(label="Select ControlNets", choices=_initial_cn)
        loras_cbg = gr.CheckboxGroup(label="Select LoRAs", choices=_initial_loras)
        custom_args_tb = gr.Textbox(label="Custom Launch Arguments", value=WEBUI_DEFAULT_ARGS.get(WEBUI_CHOICES[0], ""))
        
        launch_button = gr.Button("Download Assets & Launch WebUI", variant="primary")
        live_log_ta = gr.Textbox(label="Live Log", lines=20, interactive=False, autoscroll=True)

        sd_version_rb.change(fn=update_all_ui_elements, inputs=[sd_version_rb, webui_choice_dd], outputs=[models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, custom_args_tb])
        webui_choice_dd.change(fn=update_all_ui_elements, inputs=[sd_version_rb, webui_choice_dd], outputs=[models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, custom_args_tb])
        
        launch_button.click(
            fn=launch_anxlight_main_process,
            inputs=[webui_choice_dd, sd_version_rb, models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, custom_args_tb],
            outputs=live_log_ta
        )
    return demo

# --- Application Entry Point (CRITICAL FIX) ---
if __name__ == "__main__":
    print("Setting up Gradio interface...")
    app_instance = setup_gradio_interface()
    
    print("Launching Gradio interface...")
    app_instance.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        debug=False  # Important: debug=False prevents Gradio issue #4152
    )
    
    # Keep the main thread alive so the script doesn't exit
    print("Gradio launch called. Entering keep-alive loop.")
    while True:
        time.sleep(1)