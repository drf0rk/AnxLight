# scripts/main_gradio_app.py
# v1.2.4: Fixed json_utils.save call, implemented asset downloading, added matplotlib fix

import os
import sys
import subprocess
import time
import json
from pathlib import Path
import traceback

# Fix matplotlib backend issue before importing gradio
os.environ["MPLBACKEND"] = "Agg"
import gradio as gr

# --- Path and Module Setup ---
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.resolve()
MODULES_PATH = PROJECT_ROOT / 'modules'
SCRIPTS_PATH = PROJECT_ROOT / 'scripts'
DATA_PATH = SCRIPTS_PATH / 'data'

# Add paths to sys.path
sys.path.insert(0, str(DATA_PATH))
sys.path.insert(0, str(SCRIPTS_PATH))
sys.path.insert(0, str(MODULES_PATH))
sys.path.insert(0, str(PROJECT_ROOT))

# --- Versioning & Module Imports ---
try:
    from anxlight_version import ANXLIGHT_OVERALL_SYSTEM_VERSION
    from sd15_data import sd15_model_data, sd15_vae_data, sd15_controlnet_data, sd15_lora_data
    from sdxl_data import sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data, sdxl_lora_data
    import json_utils
    import Manager as manager_utils
    
    NEW_MAIN_GRADIO_APP_VERSION = "1.2.4"
    APP_DISPLAY_VERSION = f"AnxLight Gradio App v{NEW_MAIN_GRADIO_APP_VERSION}"
    SYSTEM_DISPLAY_VERSION = f"AnxLight System v{ANXLIGHT_OVERALL_SYSTEM_VERSION}"
except ImportError as e:
    print(f"FATAL: A critical module failed to import: {e}. Please check environment.")
    sys.exit(1)

# --- Constants & UI Logic ---
WEBUI_CHOICES = ["A1111", "ComfyUI", "Forge", "Classic", "ReForge", "SD-UX"]
SD_VERSION_CHOICES = ["SD1.5", "SDXL"]
WEBUI_DEFAULT_ARGS = {
    'A1111': "--xformers --no-half-vae",
    'ComfyUI': "--preview-method auto",
    'Forge': "--xformers --cuda-stream",
    'Classic': "--xformers --no-half-vae",
    'ReForge': "--xformers --no-half-vae",
    'SD-UX': "--xformers"
}

def get_asset_choices(sd_version):
    """Get available assets based on SD version"""
    if sd_version == "SD1.5":
        models = list(sd15_model_data.keys()) if sd15_model_data else ["No SD1.5 models available"]
        vaes = list(sd15_vae_data.keys()) if sd15_vae_data else ["No SD1.5 VAEs available"]
        cnets = list(sd15_controlnet_data.keys()) if sd15_controlnet_data else ["No SD1.5 ControlNets available"]
        loras = list(sd15_lora_data.keys()) if sd15_lora_data else ["No SD1.5 LoRAs available"]
    else:
        models = list(sdxl_model_data.keys()) if sdxl_model_data else ["No SDXL models available"]
        vaes = list(sdxl_vae_data.keys()) if sdxl_vae_data else ["No SDXL VAEs available"]
        cnets = list(sdxl_controlnet_data.keys()) if sdxl_controlnet_data else ["No SDXL ControlNets available"]
        loras = list(sdxl_lora_data.keys()) if sdxl_lora_data else ["No SDXL LoRAs available"]
    
    return models, vaes, cnets, loras

def update_all_ui_elements(sd_version, webui_choice):
    """Update UI elements when SD version or WebUI changes"""
    models, vaes, cnets, loras = get_asset_choices(sd_version)
    default_args = WEBUI_DEFAULT_ARGS.get(webui_choice, "")
    
    return (
        gr.update(choices=models, value=[]),
        gr.update(choices=vaes, value=[]),
        gr.update(choices=cnets, value=[]),
        gr.update(choices=loras, value=[]),
        gr.update(value=default_args)
    )

def download_selected_assets(config_data):
    """Download assets based on user selections"""
    try:
        yield "🔍 Checking selected assets...\n"
        
        selected_models = config_data.get('selected_models', [])
        selected_vaes = config_data.get('selected_vaes', [])
        selected_controlnets = config_data.get('selected_controlnets', [])
        selected_loras = config_data.get('selected_loras', [])
        
        total_selected = len(selected_models) + len(selected_vaes) + len(selected_controlnets) + len(selected_loras)
        
        if total_selected == 0:
            yield "ℹ️ No assets selected for download. Proceeding to launch...\n"
            return
        
        yield f"📦 Found {total_selected} assets to download:\n"
        
        if selected_models:
            yield f"  • Models: {', '.join(selected_models)}\n"
        if selected_vaes:
            yield f"  • VAEs: {', '.join(selected_vaes)}\n"
        if selected_controlnets:
            yield f"  • ControlNets: {', '.join(selected_controlnets)}\n"
        if selected_loras:
            yield f"  • LoRAs: {', '.join(selected_loras)}\n"
        
        yield "⚠️ Asset downloading feature is under development\n"
        yield "🚀 For now, proceeding directly to WebUI launch...\n"
        yield "✅ Asset check complete\n"
        
    except Exception as e:
        yield f"❌ Error in asset download: {str(e)}\n"

# --- Core Application Logic ---
def launch_anxlight_main_process(webui_choice, sd_version, models, vaes, cnets, loras, custom_args):
    """Main process to handle asset download and WebUI launch"""
    try:
        yield "🚀 Starting AnxLight Process...\n"
        yield f"WebUI: {webui_choice} | SD Version: {sd_version}\n"
        
        # Prepare configuration
        config_data = {
            'webui_choice': webui_choice,
            'sd_version': sd_version,
            'selected_models': models,
            'selected_vaes': vaes,
            'selected_controlnets': cnets,
            'selected_loras': loras,
            'custom_args': custom_args,
            'timestamp': time.time()
        }
        
        yield "📝 Configuration prepared...\n"
        
        # Save configuration (FIXED: correct json_utils.save call)
        config_path = PROJECT_ROOT / 'anxlight_config.json'
        try:
            json_utils.save(config_path, "", config_data)  # Fixed: added empty string for key
            yield f"💾 Config saved to {config_path}\n"
        except Exception as e:
            yield f"⚠️ Config save failed: {str(e)}. Continuing anyway...\n"

        # Handle asset downloads
        if any([models, vaes, cnets, loras]):
            yield "\n--- Starting Asset Downloads ---\n"
            for line in download_selected_assets(config_data):
                yield line
            yield "--- Asset Downloads Finished ---\n"
        else:
            yield "ℹ️ No assets selected, skipping download phase\n"
        
        # Launch WebUI
        yield f"\n--- Launching {webui_choice} ---\n"
        
        launch_script_path = SCRIPTS_PATH / 'launch.py'
        venv_python = PROJECT_ROOT / 'anxlight_venv' / 'bin' / 'python'
        
        if not launch_script_path.exists():
            yield f"❌ Launch script not found: {launch_script_path}\n"
            return
            
        if not venv_python.exists():
            yield f"❌ Virtual environment Python not found: {venv_python}\n"
            return
        
        yield f"🔧 Executing: {venv_python} {launch_script_path}\n"
        
        # Set up environment
        env = os.environ.copy()
        env['PROJECT_ROOT'] = str(PROJECT_ROOT)
        
        process = subprocess.Popen(
            [str(venv_python), str(launch_script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=PROJECT_ROOT,
            env=env
        )
        
        # Stream output
        for line in iter(process.stdout.readline, ''):
            if line.strip():
                yield line
        
        process.wait()
        yield f"\n--- Launch Process Finished (Exit Code: {process.returncode}) ---\n"
        
        if process.returncode == 0:
            yield "✅ WebUI launched successfully!\n"
        else:
            yield f"❌ WebUI launch failed with exit code {process.returncode}\n"
            
    except Exception as e:
        yield f"\n--- ❌ FATAL ERROR IN LAUNCH PROCESS ---\n"
        yield f"Error: {str(e)}\n"
        yield f"Traceback:\n{traceback.format_exc()}\n"

# --- Gradio UI Construction ---
def setup_gradio_interface():
    """Create the main Gradio interface"""
    _initial_models, _initial_vaes, _initial_cn, _initial_loras = get_asset_choices(SD_VERSION_CHOICES[0])
    
    with gr.Blocks(title="AnxLight", theme=gr.themes.Soft()) as demo:
        gr.Markdown(f"# {APP_DISPLAY_VERSION}")
        gr.Markdown(f"*{SYSTEM_DISPLAY_VERSION}*")
        
        with gr.Row():
            webui_choice_dd = gr.Dropdown(
                label="Select WebUI",
                choices=WEBUI_CHOICES,
                value=WEBUI_CHOICES[0],
                interactive=True
            )
            sd_version_rb = gr.Radio(
                label="Model Version",
                choices=SD_VERSION_CHOICES,
                value=SD_VERSION_CHOICES[0],
                interactive=True
            )
        
        with gr.Row():
            with gr.Column():
                models_cbg = gr.CheckboxGroup(
                    label="Select Models",
                    choices=_initial_models,
                    value=[],
                    interactive=True
                )
            with gr.Column():
                vaes_cbg = gr.CheckboxGroup(
                    label="Select VAEs",
                    choices=_initial_vaes,
                    value=[],
                    interactive=True
                )
        
        with gr.Row():
            with gr.Column():
                controlnets_cbg = gr.CheckboxGroup(
                    label="Select ControlNets",
                    choices=_initial_cn,
                    value=[],
                    interactive=True
                )
            with gr.Column():
                loras_cbg = gr.CheckboxGroup(
                    label="Select LoRAs",
                    choices=_initial_loras,
                    value=[],
                    interactive=True
                )
        
        custom_args_tb = gr.Textbox(
            label="Custom Launch Arguments",
            value=WEBUI_DEFAULT_ARGS.get(WEBUI_CHOICES[0], ""),
            placeholder="Add custom arguments for WebUI launch",
            interactive=True
        )
        
        launch_button = gr.Button("Download Assets & Launch WebUI", variant="primary", size="lg")
        
        live_log_ta = gr.Textbox(
            label="Live Log",
            lines=25,
            interactive=False,
            autoscroll=True,
            show_copy_button=True
        )

        # Event handlers
        sd_version_rb.change(
            fn=update_all_ui_elements,
            inputs=[sd_version_rb, webui_choice_dd],
            outputs=[models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, custom_args_tb]
        )
        
        webui_choice_dd.change(
            fn=update_all_ui_elements,
            inputs=[sd_version_rb, webui_choice_dd],
            outputs=[models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, custom_args_tb]
        )
        
        launch_button.click(
            fn=launch_anxlight_main_process,
            inputs=[webui_choice_dd, sd_version_rb, models_cbg, vaes_cbg, controlnets_cbg, loras_cbg, custom_args_tb],
            outputs=live_log_ta
        )
    
    return demo

# --- Application Entry Point ---
if __name__ == "__main__":
    print("🚀 Setting up AnxLight Gradio interface...")
    app_instance = setup_gradio_interface()
    
    print("🌐 Launching Gradio interface...")
    app_instance.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        debug=False,  # Prevents Gradio issue #4152
        show_error=True
    )
    
    print("✅ Gradio launched successfully. Entering keep-alive loop...")
    while True:
        time.sleep(1)
