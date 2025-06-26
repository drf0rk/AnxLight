# scripts/diagnose_ui_build.py
# Purpose: To isolate which Gradio UI component is hanging during instantiation.

import os
import sys
import traceback
import time

print("--- [DIAGNOSE UI BUILD] Script started. ---", flush=True)

try:
    # --- Step 1: Perform all imports from main_gradio_app.py ---
    print("--- [DIAGNOSE UI BUILD] Performing all imports...", flush=True)
    
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(SCRIPT_DIR, 'data'))
    sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'modules'))

    import gradio as gr
    from anxlight_version import MAIN_GRADIO_APP_VERSION
    from sd15_data import sd15_model_data
    from sdxl_data import sdxl_model_data
    
    print("--- [DIAGNOSE UI BUILD] All imports successful. ---", flush=True)

    # --- Step 2: Replicate the global variables and functions needed ---
    SD_VERSION_CHOICES = ["SD1.5", "SDXL"]
    INPAINTING_FILTER_CHOICES = ["Show All Models"]
    WEBUI_CHOICES = ["A1111", "ComfyUI"]

    def get_asset_choices(sd_version, inpainting_filter_mode="Show All Models"):
        # Dummy function, we just need it to return something.
        print(f"--- [DIAGNOSE UI BUILD] get_asset_choices called for {sd_version}... OK", flush=True)
        return ["Model1", "Model2"], ["VAE1"], ["CN1"], ["LoRA1"]

    print("--- [DIAGNOSE UI BUILD] Helper functions and vars defined. ---", flush=True)
    
    # --- Step 3: Execute the initial data loading call ---
    print("\\n--- [DIAGNOSE UI BUILD] Attempting initial get_asset_choices() call... ---", flush=True)
    _initial_models, _initial_vaes, _initial_controlnets, _initial_loras = get_asset_choices(SD_VERSION_CHOICES[0], INPAINTING_FILTER_CHOICES[0])
    print("--- [DIAGNOSE UI BUILD] Initial data load successful. ---", flush=True)

    # --- Step 4: Build the UI, one component at a time ---
    print("\\n--- [DIAGNOSE UI BUILD] Starting UI component instantiation... ---", flush=True)

    with gr.Blocks() as demo:
        print("--- [DIAGNOSE UI BUILD] gr.Blocks(): OK ---", flush=True)
        
        gr.Markdown("# Test")
        print("--- [DIAGNOSE UI BUILD] gr.Markdown: OK ---", flush=True)

        with gr.Tabs():
            print("--- [DIAGNOSE UI BUILD] gr.Tabs(): OK ---", flush=True)
            with gr.TabItem("Session Configuration"):
                print("--- [DIAGNOSE UI BUILD] gr.TabItem: OK ---", flush=True)
                with gr.Row():
                    print("--- [DIAGNOSE UI BUILD] gr.Row (1): OK ---", flush=True)
                    webui_choice_dd = gr.Dropdown(label="Select WebUI", choices=WEBUI_CHOICES)
                    print("--- [DIAGNOSE UI BUILD] gr.Dropdown (webui_choice): OK ---", flush=True)
                    sd_version_rb = gr.Radio(label="Model Version", choices=SD_VERSION_CHOICES)
                    print("--- [DIAGNOSE UI BUILD] gr.Radio (sd_version): OK ---", flush=True)
                
                models_cbg = gr.CheckboxGroup(label="Select Models", choices=_initial_models)
                print("--- [DIAGNOSE UI BUILD] gr.CheckboxGroup (models): OK ---", flush=True)

    print("\\n--- [DIAGNOSE UI BUILD] UI build appears successful. ---", flush=True)
    print("--- [DIAGNOSE UI BUILD] If you see this, the hang is not in the UI build process. ---", flush=True)


except Exception as e:
    print(f"\\n--- [DIAGNOSE UI BUILD] CRITICAL ERROR: {e} ---", flush=True)
    print(f"--- [DIAGNOSE UI BUILD] Traceback: {traceback.format_exc()} ---", flush=True)

print("\\n--- [DIAGNOSE UI BUILD] Script finished. ---", flush=True)