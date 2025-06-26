# scripts/main_gradio_app_v2_minimal_test.py
# Ultra-minimal Gradio app for baseline testing.
# v1.0.4: Reverted to generator callback, kept MPLBACKEND fix.
# v1.0.3: Set MPLBACKEND env var to 'Agg' before any imports. (Worked for regular fn)
# v1.0.2: Added matplotlib.use('Agg') for compatibility.
# v1.0.1: Changed to use a regular (non-generator) function callback.

import os
os.environ['MPLBACKEND'] = 'Agg' # Set backend BEFORE importing matplotlib or gradio

import matplotlib 
import gradio as gr
import time
import sys

print(f"--- Ultra-Minimal Gradio Test App (v1.0.4 - Generator Callback Test with MPLBACKEND fix) ---")
print(f"Python version: {sys.version}")
print(f"Gradio version: {gr.__version__}")
try:
    import pydantic
    print(f"Pydantic version: {pydantic.__version__}")
except ImportError:
    print("Pydantic module not found for direct version check in this minimal script.")

def minimal_generator_callback():
    # These prints go to the Colab Cell 2 output (server-side)
    print("[MINIMAL_BACKEND_GENERATOR] minimal_generator_callback ENTERED")
    
    log_message = "Test Log 1 (Generator Fn): Callback entered successfully.\\n"
    yield log_message # This goes to the UI textbox
    
    time.sleep(1) # Simulate some work
    print("[MINIMAL_BACKEND_GENERATOR] Waited 1 second, yielding second log.")
    log_message += "Test Log 2 (Generator Fn): Waited 1 second.\\n"
    yield log_message
    
    time.sleep(1) # Simulate more work
    print("[MINIMAL_BACKEND_GENERATOR] Waited another 1 second, yielding third log (final).")
    log_message += "Test Log 3 (Generator Fn): Test complete."
    yield log_message
    
    print("[MINIMAL_BACKEND_GENERATOR] minimal_generator_callback EXITED.")

with gr.Blocks() as minimal_demo:
    gr.Markdown("## Ultra-Minimal Gradio Generator Callback Test (v1.0.4)")
    with gr.Row():
        test_button = gr.Button("Run Minimal Generator Test") # Button text changed
    with gr.Row():
        output_textbox = gr.Textbox(label="Minimal Log Output", lines=10, interactive=False, autoscroll=True)

    test_button.click(
        fn=minimal_generator_callback, # Changed back to generator
        inputs=[], 
        outputs=[output_textbox]
    )

if __name__ == "__main__":
    print("Launching Minimal Gradio Test App (Generator Callback Version with MPLBACKEND fix)...")
    minimal_demo.launch(debug=True, share=True, show_error=True)
    print("Minimal Gradio Test App launch attempted. Check URL and console for logs.")