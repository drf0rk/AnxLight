# scripts/main_gradio_app.py
# v1.1.1: Fix: Remove unused 'request' parameter from launch function to prevent Pydantic error.
# v1.1.0: Restore full launch logic with compatibility fixes.

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
sys.path.insert(0, str(SCRIPTS_PATH))
if str(SCRIPT_DIR) not in sys.path: sys.path.insert(0, str(SCRIPT_DIR))
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(1, str(PROJECT_ROOT))
if str(MODULES_PATH) not in sys.path: sys.path.insert(0, str(MODULES_PATH))

# --- Versioning ---
try:
    from anxlight_version import ANXLIGHT_OVERALL_SYSTEM_VERSION, PRE_FLIGHT_SETUP_PY_VERSION
    NEW_MAIN_GRADIO_APP_VERSION = "1.1.1"
    APP_DISPLAY_VERSION = f"AnxLight Gradio App v{NEW_MAIN_GRADIO_APP_VERSION}"
    SYSTEM_DISPLAY_VERSION = f"AnxLight System v{ANXLIGHT_OVERALL_SYSTEM_VERSION}"
    print(f"--- {APP_DISPLAY_VERSION} (System: {SYSTEM_DISPLAY_VERSION}, Pre-Flight: v{PRE_FLIGHT_SETUP_PY_VERSION}) ---")
except ImportError as e_ver:
    print(f"[CRITICAL] Failed to import versions: {e_ver}")
    APP_DISPLAY_VERSION = "AnxLight Gradio App v?.?.? (Version File Error)"

# --- Module Imports ---
try:
    from sd15_data import sd15_model_data, sd15_vae_data, sd15_controlnet_data, sd15_lora_data
    from sdxl_data import sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data, sdxl_lora_data
    import json_utils
    import Manager as manager_utils
    print("Successfully imported real data and utility modules.")
except ImportError as e:
    print(f"FATAL: Error importing backend modules: {e}. Check PYTHONPATH and file integrity.")
    sys.exit(1)

# --- Constants ---
WEBUI_CHOICES = ["A1111", "ComfyUI", "Forge"]
SD_VERSION_CHOICES = ["SD1.5", "SDXL"]
THEME_CHOICES = ["Default", "anxety", "blue", "green", "peach", "pink", "red", "yellow"]
INPAINTING_FILTER_CHOICES = ["Show All Models", "Inpainting Models Only", "No Inpainting Models"]
WEBUI_DEFAULT_ARGS = {
    'A1111': "--xformers --no-half-vae",
    'ComfyUI': "--preview-method auto",
    'Forge': "--xformers --cuda-stream --pin-shared-memory"
}

# --- UI Logic Functions ---
def get_asset_choices(sd_version, inpainting_filter_mode="Show All Models"):
    if sd_version == "SD1.5":
        models_src, vaes_src, cnets_src, loras_src = sd15_model_data, sd15_vae_data, sd15_controlnet_data, sd15_lora_data
    else:
        models_src, vaes_src, cnets_src, loras_src = sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data, sdxl_lora_data
    filtered_models = [name for name, data in models_src.items() if (inpainting_filter_mode == "Show All Models") or (inpainting_filter_mode == "Inpainting Models Only" and data.get("inpainting")) or (inpainting_filter_mode == "No Inpainting Models" and not data.get("inpainting"))]
    return filtered_models, list(vaes_src.keys()), list(cnets_src.keys()), list(loras_src.keys())

def update_all_ui_elements(sd_version_selected, inpainting_filter_selected, webui_selected):
    models, vaes, controlnets, loras = get_asset_choices(sd_version_selected, inpainting_filter_selected)
    default_args = WEBUI_DEFAULT_ARGS.get(webui_selected, "")
    is_comfy = (webui_selected == 'ComfyUI')
    return (gr.update(choices=models, value=[]), gr.update(choices=vaes, value=[]), gr.update(choices=controlnets, value=[]), gr.update(choices=loras, value=[]), gr.update(value=default_args), gr.update(visible=not is_comfy), gr.update(visible=is_comfy), gr.update(visible=not is_comfy, value=THEME_CHOICES[0]))

# --- Core Application Logic (FIX APPLIED) ---
def launch_anxlight_main_process(webui_choice, sd_version, models_selected, vaes_selected,
                                controlnets_selected, loras_selected, update_webui,
                                update_extensions, check_custom_nodes_deps, detailed_download,
                                commit_hash, civitai_token, huggingface_token, zrok_token,
                                ngrok_token, custom_args, theme_accent, inpainting_filter):
    # The 'request' parameter has been removed from this function definition
    try:
        yield "--- Starting AnxLight Process ---\n"
        config_data = {'webui_choice': webui_choice, 'sd_version': sd_version, 'selected_assets': {'models': models_selected, 'vaes': vaes_selected, 'controlnets': controlnets_selected, 'loras': loras_selected}, 'tokens': {'civitai': civitai_token, 'huggingface': huggingface_token, 'zrok': zrok_token, 'ngrok': ngrok_token}, 'launch_args': custom_args, 'options': {'update_webui': update_webui, 'update_extensions': update_extensions, 'check_deps': check_custom_nodes_deps, 'detailed_log': detailed_download}}
        yield "Configuration prepared.\n"
        config_path = PROJECT_ROOT / 'anxlight_config.json'
        json_utils.save(config_path, config_data)
        yield f"Config saved to {config_path}\n"
        if any(config_data['selected_assets'].values()):
            yield "\n--- Starting Asset Downloads ---\n"
            for line in manager_utils.download_selected_assets(config_data):
                yield line
            yield "--- Asset Downloads Finished ---\n"
        else:
            yield "No assets selected for download. Skipping.\n"
        yield f"\n--- Launching {webui_choice} ---\n"
        launch_script_path = SCRIPTS_PATH / 'launch.py'
        if not launch_script_path.exists():
            yield f"CRITICAL ERROR: Launch script not found at {launch_script_path}\n"
            return
        venv_python = PROJECT_ROOT / 'anxlight_venv' / 'bin' / 'python'
        launch_process = subprocess.Popen([str(venv_python), str(launch_script_path)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=PROJECT_ROOT)
        for line in iter(launch_process.stdout.readline, ''):
            if line.strip():
                yield line
        launch_process.wait()
        yield f"\n--- Launch Process Terminated (Code: {launch_process.returncode}) ---\n"
    except Exception as e:
        yield f"\n--- FATAL ERROR IN LAUNCH PROCESS ---\n"
        yield f"Error: {str(e)}\n"
        yield f"Traceback:\n{traceback.format_exc()}\n"

# --- Gradio UI Construction ---
def setup_gradio_interface():
    _initial_models, _initial_vaes, _initial_cn, _initial_loras = get_asset_choices(SD_VERSION_CHOICES[0])
    with gr.Blocks() as demo:
        gr.Markdown(f"# {APP_DISPLAY_VERSION}")
        with gr.Tabs():
            with gr.TabItem("Session Configuration"):
                with gr.Row():
                    webui_choice_dd = gr.Dropdown(label="Select WebUI", choices=WEBUI_CHOICES, value=WEBUI_CHOICES[0], interactive=True)
                    sd_version_rb = gr.Radio(label="Model Version", choices=SD_VERSION_CHOICES, value=SD_VERSION_CHOICES[0], interactive=True)
                inpainting_filter_rg = gr.Radio(label="Model Type Filter", choices=INPAINTING_FILTER_CHOICES, value=INPAINTING_FILTER_CHOICES[0], interactive=True)
                with gr.Row(equal_height=False):
                    update_webui_chk = gr.Checkbox(label="Update WebUI (Daily)", value=False)
                    update_extensions_chk = gr.Checkbox(label="Update Extensions (Daily)", value=False)
                    check_custom_nodes_deps_chk = gr.Checkbox(label="Check ComfyUI Deps", value=True, visible=False)
                    detailed_download_chk = gr.Checkbox(label="Detailed Session Log", value=True)
                models_cbg = gr.CheckboxGroup(label="Select Models", choices=_initial_models, value=[])
                vaes_cbg = gr.CheckboxGroup(label="Select VAEs", choices=_initial_vaes, value=[])
                controlnets_cbg = gr.CheckboxGroup(label="Select ControlNets", choices=_initial_cn, value=[])
                loras_cbg = gr.CheckboxGroup(label="Select LoRAs", choices=_initial_loras, value=[])
                with gr.Accordion("Advanced & Tokens", open=False):
                    custom_args_tb = gr.Textbox(label="Custom Launch Arguments", value=WEBUI_DEFAULT_ARGS.get(WEBUI_CHOICES[0], ""))
                    commit_hash_tb = gr.Textbox(label="WebUI Commit Hash (Optional)")
                    with gr.Row():
                        civitai_token_tb = gr.Textbox(label="CivitAI API Key", type="password")
                        huggingface_token_tb = gr.Textbox(label="HuggingFace Token", type="password")
                    with gr.Row():
                        zrok_token_tb = gr.Textbox(label="Zrok Token", type="password")
                        ngrok_token_tb = gr.Textbox(label="NGROK Token", type="password")
                theme_accent_dd = gr.Dropdown(label="UI Theme", choices=THEME_CHOICES, value=THEME_CHOICES[0], visible=False)
            with gr.TabItem("Launch & Live Log"):
                launch_button = gr.Button("Download Assets & Launch WebUI", variant="primary")
                live_log_ta = gr.Textbox(label="Live Log", lines=20, interactive=False, autoscroll=True)
        inputs = [sd_version_rb, inpainting_filter_rg, webui_choice_dd]
        outputs = [models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, custom_args_tb, update_extensions_chk, check_custom_nodes_deps_chk, theme_accent_dd]
        sd_version_rb.change(fn=update_all_ui_elements, inputs=inputs, outputs=outputs)
        inpainting_filter_rg.change(fn=update_all_ui_elements, inputs=inputs, outputs=outputs)
        webui_choice_dd.change(fn=update_all_ui_elements, inputs=inputs, outputs=outputs)
        launch_button.click(fn=launch_anxlight_main_process, inputs=[webui_choice_dd, sd_version_rb, models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, update_webui_chk, update_extensions_chk, check_custom_nodes_deps_chk, detailed_download_chk, commit_hash_tb, civitai_token_tb, huggingface_token_tb, zrok_token_tb, ngrok_token_tb, custom_args_tb, theme_accent_dd, inpainting_filter_rg], outputs=live_log_ta)
    return demo

# --- Application Entry Point ---
if __name__ == "__main__":
    print("Setting up Gradio interface...")
    app_instance = setup_gradio_interface()
    print("Launching Gradio App...")
    try:
        app_instance.launch(debug=False, share=True, show_error=True)
        print("Gradio server launched. Keeping script alive...")
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"FATAL LAUNCH ERROR: {e}")
        print("Could not launch the Gradio server. Please check logs.")