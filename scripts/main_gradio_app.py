import gradio as gr
import os
import sys
import threading 
import subprocess # Ensure subprocess is imported
import time
import json
from pathlib import Path
import traceback # For detailed error logging

# AnxLight Main App v0.0.7 - 2025-06-19
APP_VERSION = "AnxLight Gradio App v0.0.7"

# --- Define Dummy classes in global scope ---
# These are placeholders in case the real modules fail to import.
class _DummyDataModule: # Renamed to avoid conflict if real 'data' module is a package
    sd15_model_data = {"ERROR: Module Load Failed": {}}
    sd15_vae_data = {}
    sd15_controlnet_data = {}
    sdxl_model_data = {"ERROR: Module Load Failed": {}}
    sdxl_vae_data = {}
    sdxl_controlnet_data = {}

class _DummyLoraDataModule: # Renamed
    lora_data = {"sd15_loras": {}, "sdxl_loras": {}}

class _DummyWebUIUtilsModule: # Renamed
    def update_current_webui(self, webui_name):
        print(f"[_DummyWebUIUtilsModule] update_current_webui called for {webui_name} - REAL MODULE NOT LOADED")
        pass

# Initialize placeholders for modules that will be imported
# These will be overwritten by real imports if successful
sd15_data = _DummyDataModule()
sdxl_data = _DummyDataModule() # Can use the same dummy for simplicity if structure is similar
lora_data = _DummyLoraDataModule()
json_utils = None # Critical, no simple dummy
webui_utils = _DummyWebUIUtilsModule()


# --- Robust Path Setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
MODULES_PATH = os.path.join(PROJECT_ROOT, 'modules')

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(1, PROJECT_ROOT)
if MODULES_PATH not in sys.path:
    sys.path.insert(0, MODULES_PATH)

print(f"--- {APP_VERSION} ---")
print(f"[DEBUG main_gradio_app] SCRIPT_DIR: {SCRIPT_DIR}")
print(f"[DEBUG main_gradio_app] PROJECT_ROOT: {PROJECT_ROOT}")
print(f"[DEBUG main_gradio_app] MODULES_PATH: {MODULES_PATH}")
print(f"[DEBUG main_gradio_app] sys.path just before backend module import attempt: {sys.path}")

try:
    from data import sd15_data as real_sd15_data, sdxl_data as real_sdxl_data, lora_data as real_lora_data
    sd15_data, sdxl_data, lora_data = real_sd15_data, real_sdxl_data, real_lora_data # Overwrite dummies with real modules
    print("Successfully imported real data modules.")
    
    from modules import json_utils as real_json_utils, webui_utils as real_webui_utils
    json_utils, webui_utils = real_json_utils, real_webui_utils # Overwrite dummies
    print("Successfully imported real backend utility modules (json_utils, webui_utils).")

except ImportError as e:
    print(f"FATAL: Error importing data or backend modules: {e}")
    print("One or more essential modules could not be loaded. Using dummy placeholders where possible.")
    print(f"Current sys.path: {sys.path}")
    # Dummies are already initialized, so no need to re-assign here unless to signal failure more explicitly.
    # The fact that `json_utils` might remain `None` is a critical failure point.

# --- UI Lists & Data ---
WEBUI_CHOICES = ["A1111", "Classic", "ComfyUI", "Forge", "ReForge", "SD-UX"]
SD_VERSION_CHOICES = ["SD1.5", "SDXL"]
THEME_CHOICES = ["Default", "anxety", "blue", "green", "peach", "pink", "red", "yellow"]
INPAINTING_FILTER_CHOICES = ["Show All Models", "Inpainting Models Only", "No Inpainting Models"]

WEBUI_DEFAULT_ARGS = {
    'A1111':   "--xformers --no-half-vae",
    'ComfyUI': "--use-sage-attention --dont-print-server",
    'Forge':   "--xformers --cuda-stream --pin-shared-memory",
    'Classic': "--persistent-patches --cuda-stream --pin-shared-memory",
    'ReForge': "--xformers --cuda-stream --pin-shared-memory",
    'SD-UX':   "--xformers --no-half-vae"
}

SETTINGS_KEYS = [
    'XL_models', 'model', 'model_num', 'inpainting_model', 'vae', 'vae_num',
    'latest_webui', 'latest_extensions', 'check_custom_nodes_deps', 'change_webui', 'detailed_download',
    'controlnet', 'controlnet_num', 'commit_hash',
    'civitai_token', 'huggingface_token', 'zrok_token', 'ngrok_token', 'commandline_arguments', 'theme_accent',
    'empowerment', 'empowerment_output',
    'Model_url', 'Vae_url', 'LoRA_url', 'Embedding_url', 'Extensions_url', 'ADetailer_url',
    'custom_file_urls'
]

def get_asset_choices(sd_version, inpainting_filter_mode="Show All Models"):
    # Use the globally defined sd15_data, sdxl_data, lora_data which are either real or dummy
    models_data_source = sd15_data.sd15_model_data if sd_version == "SD1.5" else sdxl_data.sdxl_model_data
    filtered_models_keys = [name for name in models_data_source.keys() if (inpainting_filter_mode == "Show All Models") or \
                                                                       (inpainting_filter_mode == "Inpainting Models Only" and "inpaint" in name.lower()) or \
                                                                       (inpainting_filter_mode == "No Inpainting Models" and "inpaint" not in name.lower())]
    models = filtered_models_keys
    if sd_version == "SD1.5":
        vaes = list(sd15_data.sd15_vae_data.keys())
        controlnets = list(sd15_data.sd15_controlnet_data.keys())
        loras = list(lora_data.lora_data.get("sd15_loras", {}).keys())
    elif sd_version == "SDXL":
        vaes = list(sdxl_data.sdxl_vae_data.keys())
        controlnets = list(sdxl_data.sdxl_controlnet_data.keys())
        loras = list(lora_data.lora_data.get("sdxl_loras", {}).keys())
    else:
        vaes, controlnets, loras = [], [], []
    return models, vaes, controlnets, loras

def update_all_ui_elements(sd_version_selected, inpainting_filter_selected, webui_selected):
    models, vaes, controlnets, loras = get_asset_choices(sd_version_selected, inpainting_filter_selected)
    default_args = WEBUI_DEFAULT_ARGS.get(webui_selected, "")
    is_comfy = (webui_selected == 'ComfyUI')
    update_ext_visible = not is_comfy
    check_nodes_visible = is_comfy
    theme_accent_visible = not is_comfy
    current_theme_value = THEME_CHOICES[1]
    theme_dd_widget = globals().get('theme_accent_dd')
    if theme_accent_visible and theme_dd_widget is not None and hasattr(theme_dd_widget, 'value'):
         current_theme_value = theme_dd_widget.value 
    return (gr.update(choices=models, value=[]), gr.update(choices=vaes, value=[]), gr.update(choices=controlnets, value=[]),
            gr.update(choices=loras, value=[]), gr.update(value=default_args), gr.update(visible=update_ext_visible),
            gr.update(visible=check_nodes_visible), gr.update(visible=theme_accent_visible, value=current_theme_value))

def save_keys_to_file_fn(civitai, hf, ngrok, zrok):
    keys_data = {"civitai_token": civitai, "huggingface_token": hf, "ngrok_token": ngrok, "zrok_token": zrok}
    temp_file_path = "anxlight_keys.json"
    try:
        with open(temp_file_path, 'w') as f: json.dump(keys_data, f, indent=2)
        gr.Info("Keys saved! Your browser should prompt a download.")
        return gr.update(value=temp_file_path, visible=True)
    except Exception as e:
        gr.Error(f"Failed to save keys: {e}")
        return gr.update(value=None, visible=False)

def load_keys_from_file_fn(file_obj):
    if file_obj is None: return gr.update(), gr.update(), gr.update(), gr.update()
    try:
        with open(file_obj.name, 'r') as f: keys_data = json.load(f)
        gr.Info("Keys loaded successfully!")
        return (gr.update(value=keys_data.get("civitai_token", "")), gr.update(value=keys_data.get("huggingface_token", "")),
                gr.update(value=keys_data.get("ngrok_token", "")), gr.update(value=keys_data.get("zrok_token", "")))
    except Exception as e:
        gr.Error(f"Error loading keys: {e}. Make sure it's a valid JSON file.")
        return gr.update(), gr.update(), gr.update(), gr.update()

def _execute_backend_script(script_path, log_file_name_base, ui_log_prefix, detailed_logging_enabled, log_session_dir, current_log_output_list):
    log_output_list = current_log_output_list 
    full_log_file_path = None
    script_success = False

    if detailed_logging_enabled and log_session_dir:
        full_log_file_path = os.path.join(log_session_dir, log_file_name_base)
        log_output_list.append(f"Detailed log for this step will be at: {full_log_file_path}\\n")
        yield "".join(log_output_list) 
    
    log_output_list.append(f"Executing: {sys.executable} {script_path}...\\n")
    yield "".join(log_output_list)
    
    process = None
    log_file = None
    try:
        process_env = os.environ.copy()
        existing_pythonpath = process_env.get('PYTHONPATH', '')
        paths_to_prepend = [MODULES_PATH, PROJECT_ROOT]
        new_pythonpath_parts = paths_to_prepend
        if existing_pythonpath:
            new_pythonpath_parts.extend(existing_pythonpath.split(os.pathsep))
        seen_paths = set()
        unique_pythonpath_parts = []
        for p_item in new_pythonpath_parts:
            if p_item not in seen_paths:
                unique_pythonpath_parts.append(p_item)
                seen_paths.add(p_item)
        process_env['PYTHONPATH'] = os.pathsep.join(unique_pythonpath_parts)
        
        log_output_list.append(f"{ui_log_prefix} Subprocess PYTHONPATH: {process_env['PYTHONPATH']}\\n")
        yield "".join(log_output_list)

        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=process_env,
            cwd=PROJECT_ROOT 
        )

        if full_log_file_path:
            try:
                log_file = open(full_log_file_path, 'a', encoding='utf-8')
            except Exception as e_file:
                log_output_list.append(f"Warning: Could not open log file {full_log_file_path}: {e_file}\\n")
                yield "".join(log_output_list)

        for line in process.stdout: 
            line_stripped = line.strip()
            log_output_list.append(f"{ui_log_prefix} {line_stripped}\\n")
            if log_file:
                try:
                    log_file.write(line)
                except Exception as e_write:
                    print(f"Error writing to log file {full_log_file_path}: {e_write}") 
                    if log_file: log_file.close()
                    log_file = None 
            yield "".join(log_output_list) 
        
        process.wait()

        if process.returncode == 0:
            log_output_list.append(f"{ui_log_prefix} Script finished successfully (return code 0).\\n")
            script_success = True
        else:
            log_output_list.append(f"{ui_log_prefix} Script failed with return code {process.returncode}.\\n")
            script_success = False
        yield "".join(log_output_list)

    except FileNotFoundError:
        log_output_list.append(f"{ui_log_prefix} Error: Script not found at {script_path}. Ensure paths are correct.\\n")
        script_success = False
        yield "".join(log_output_list)
    except Exception as e:
        log_output_list.append(f"{ui_log_prefix} An unexpected error occurred while trying to run {script_path}: {type(e).__name__}: {e}\\n")
        log_output_list.append(f"Traceback: {traceback.format_exc()}\\n")
        script_success = False
        if process and process.stdout: 
            try:
                for line in process.stdout: 
                    log_output_list.append(f"{ui_log_prefix} [err] {line.strip()}\\n")
            except Exception as e_read_err:
                 log_output_list.append(f"{ui_log_prefix} [err] Error reading stdout after process error: {e_read_err}\\n")
        yield "".join(log_output_list)
    finally:
        if log_file:
            log_file.close()
        if process and process.poll() is None: 
            log_output_list.append(f"{ui_log_prefix} Terminating script {script_path} due to an error or timeout in managing function.\\n")
            yield "".join(log_output_list)
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                log_output_list.append(f"{ui_log_prefix} Script {script_path} force-killed.\\n")
                yield "".join(log_output_list)
    
    if script_success:
        yield "SCRIPT_EXECUTION_SUCCESS"
    else:
        yield "SCRIPT_EXECUTION_FAILURE"

def launch_anxlight_main_process(
    webui_choice, sd_version, inpainting_models_filter_val, # Renamed webui to webui_choice for clarity
    selected_models, selected_vaes, selected_controlnets, selected_loras,
    update_webui_val, update_extensions_val, check_custom_nodes_val, detailed_download_val,
    commit_hash_val, civitai_token_val, huggingface_token_val, zrok_token_val, ngrok_token_val,
    custom_args_val, theme_accent_val
):
    log_output_list = [f"--- {APP_VERSION} Backend Process Initializing ---\\n"] 
    yield "".join(log_output_list)

    if json_utils is None:
        log_output_list.append("FATAL: json_utils module not loaded. Cannot proceed with config generation.\\n")
        yield "".join(log_output_list)
        return
    if webui_utils is None: # Check if the real webui_utils loaded
        log_output_list.append("Warning: webui_utils module not loaded. update_current_webui will be skipped.\\n")
        # Allow to proceed but functionality will be limited
    
    local_project_root = PROJECT_ROOT
    log_output_list.append(f"Project Root: {local_project_root}\\n")
    yield "".join(log_output_list)
    
    log_session_dir = None
    if detailed_download_val:
        try:
            log_dir_base = os.path.join(local_project_root, 'logs')
            log_session_dir = os.path.join(log_dir_base, f'session_{time.strftime("%Y%m%d-%H%M%S")}')
            os.makedirs(log_session_dir, exist_ok=True)
            log_output_list.append(f"Detailed logging enabled. Session logs will be in: {log_session_dir}\\n")
        except Exception as e:
            log_output_list.append(f"Warning: Could not create log directory {log_session_dir}: {e}\\n")
            log_session_dir = None 
    else:
        log_output_list.append("Detailed file logging is disabled. Summary will be shown.\\n")
    yield "".join(log_output_list)

    widgets_data = {}
    try:
        widgets_data['XL_models'] = (sd_version == "SDXL")
        widgets_data['model'] = selected_models[0] if selected_models and len(selected_models) >= 1 else "none"
        widgets_data['model_num'] = ",".join(selected_models) if selected_models else ""
        widgets_data['inpainting_model'] = (inpainting_models_filter_val == "Inpainting Models Only")
        widgets_data['vae'] = selected_vaes[0] if selected_vaes and len(selected_vaes) >= 1 else "none"
        widgets_data['vae_num'] = ",".join(selected_vaes) if selected_vaes else ""
        widgets_data['latest_webui'] = update_webui_val
        widgets_data['latest_extensions'] = update_extensions_val
        widgets_data['check_custom_nodes_deps'] = check_custom_nodes_val
        widgets_data['change_webui'] = webui_choice 
        widgets_data['detailed_download'] = "on" if detailed_download_val else "off"
        widgets_data['controlnet'] = selected_controlnets[0] if selected_controlnets and len(selected_controlnets) >=1 else "none"
        widgets_data['controlnet_num'] = ",".join(selected_controlnets) if selected_controlnets else ""
        widgets_data['commit_hash'] = commit_hash_val or ""
        widgets_data['civitai_token'] = civitai_token_val or ""
        widgets_data['huggingface_token'] = huggingface_token_val or ""
        widgets_data['zrok_token'] = zrok_token_val or ""
        widgets_data['ngrok_token'] = ngrok_token_val or ""
        widgets_data['commandline_arguments'] = custom_args_val or ""
        widgets_data['theme_accent'] = theme_accent_val
        widgets_data['anxlight_selected_models_list'] = selected_models or []
        widgets_data['anxlight_selected_vaes_list'] = selected_vaes or []
        widgets_data['anxlight_selected_controlnets_list'] = selected_controlnets or []
        widgets_data['anxlight_selected_loras_list'] = selected_loras or []

        for key_to_check in SETTINGS_KEYS:
            if key_to_check not in widgets_data:
                if key_to_check == 'empowerment': widgets_data[key_to_check] = False
                elif key_to_check == 'empowerment_output': widgets_data[key_to_check] = ""
                elif '_url' in key_to_check.lower() or 'custom_file_urls' in key_to_check.lower(): widgets_data[key_to_check] = ""
        
        log_output_list.append("Successfully collected UI data for WIDGETS section.\\n")
        yield "".join(log_output_list)

        environment_data = {}
        is_colab_env = os.environ.get('IS_COLAB', 'false').lower() == 'true' or 'COLAB_GPU' in os.environ
        environment_data['env_name'] = "Google Colab" if is_colab_env else "AnxLight_Generic_Platform"
        environment_data['lang'] = "en"
        default_home_path = local_project_root 
        default_scr_path = local_project_root
        default_settings_path = os.path.join(default_home_path, 'anxlight_config.json')
        default_venv_path = os.path.join(local_project_root, 'venv')

        environment_data['home_path'] = os.environ.get('home_path', default_home_path)
        environment_data['scr_path'] = os.environ.get('scr_path', default_scr_path)
        environment_data['settings_path'] = os.environ.get('settings_path', default_settings_path)
        environment_data['venv_path'] = os.environ.get('venv_path', default_venv_path)
        environment_data['fork'] = "drf0rk/AnxLight" 
        environment_data['branch'] = "feature/backend-integration" 
        environment_data['start_timer'] = int(time.time() - 5) 
        environment_data['public_ip'] = "" 
        log_output_list.append("Successfully prepared ENVIRONMENT data.\\n")
        yield "".join(log_output_list)
        
        anxlight_config = {"WIDGETS": widgets_data, "ENVIRONMENT": environment_data, "UI_SELECTION": {"webui_choice": webui_choice}}
        log_output_list.append("Configuration dictionary constructed.\\n")

    except Exception as e:
        log_output_list.append(f"Error constructing configuration data: {type(e).__name__}: {e}\\n")
        log_output_list.append(f"Traceback: {traceback.format_exc()}\\n")
        yield "".join(log_output_list)
        return 

    config_file_path_str = environment_data['settings_path'] 
    config_file_path = Path(config_file_path_str)
    try:
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, 'w') as f:
            json.dump(anxlight_config, f, indent=4)
        log_output_list.append(f"Configuration successfully saved to: {config_file_path}\\n")
        yield "".join(log_output_list)
    except Exception as e:
        log_output_list.append(f"Error saving configuration file to {config_file_path}: {type(e).__name__}: {e}\\n")
        log_output_list.append(f"Traceback: {traceback.format_exc()}\\n")
        yield "".join(log_output_list)
        return

    try:
        # Check if webui_utils is the real module, not the dummy one
        if webui_utils and not isinstance(webui_utils, _DummyWebUIUtilsModule):
             webui_utils.update_current_webui(webui_choice) 
             log_output_list.append(f"Called webui_utils.update_current_webui for '{webui_choice}'. This function should update the config file.\\n")
        elif webui_utils is None: # Real module failed to import, and no dummy was assigned (should not happen with current setup)
            log_output_list.append(f"Critical Error: webui_utils is None. update_current_webui cannot be called.\\n")
        else: # It's the dummy module
            log_output_list.append(f"Warning: Using _DummyWebUIUtilsModule. update_current_webui for '{webui_choice}' was a dummy call.\\n")
            webui_utils.update_current_webui(webui_choice) # Call the dummy method for consistent logging
        yield "".join(log_output_list)
    except Exception as e:
        log_output_list.append(f"Error calling webui_utils.update_current_webui: {type(e).__name__}: {e}\\n")
        log_output_list.append("Ensure 'modules' directory is in sys.path and webui_utils.py is correct.\\n")
        log_output_list.append(f"Traceback: {traceback.format_exc()}\\n")
        yield "".join(log_output_list)
        
    log_output_list.append("\\n--- Initiating Backend Script Execution ---\\n")
    yield "".join(log_output_list)

    scr_path_env = environment_data['scr_path'] 
    downloading_script_path = os.path.join(scr_path_env, 'scripts', 'en', 'downloading-en.py')
    launch_script_path = os.path.join(scr_path_env, 'scripts', 'launch.py')

    log_output_list.append(f"Attempting to run downloading script: {downloading_script_path}\\n")
    yield "".join(log_output_list)
    
    download_success = False
    for exec_status_or_log_chunk in _execute_backend_script(downloading_script_path, "downloading.log", "[Downloader]", detailed_download_val, log_session_dir, log_output_list):
        if exec_status_or_log_chunk == "SCRIPT_EXECUTION_SUCCESS":
            download_success = True
        elif exec_status_or_log_chunk == "SCRIPT_EXECUTION_FAILURE":
            download_success = False
        else: 
            yield exec_status_or_log_chunk 
    
    if download_success:
        log_output_list.append(f"\\nDownload script finished. Attempting to run launch script: {launch_script_path}\\n")
        yield "".join(log_output_list) 
        
        launch_success = False
        for exec_status_or_log_chunk_launch in _execute_backend_script(launch_script_path, "launch.log", "[Launcher]", detailed_download_val, log_session_dir, log_output_list):
            if exec_status_or_log_chunk_launch == "SCRIPT_EXECUTION_SUCCESS":
                launch_success = True
            elif exec_status_or_log_chunk_launch == "SCRIPT_EXECUTION_FAILURE":
                launch_success = False
            else:
                yield exec_status_or_log_chunk_launch
        
        if launch_success:
            log_output_list.append("--- Launch script execution successful ---\\n")
        else:
            log_output_list.append("--- Launch script execution failed or status unclear from logs. Check detailed logs if enabled. ---\\n")
    else:
        log_output_list.append("--- Download script failed or status unclear. Skipping launch script. Check detailed logs if enabled. ---\\n")
        
    yield "".join(log_output_list)

# --- Gradio Interface Definition ---
with gr.Blocks(css=".gradio-container {max-width: 90% !important; margin: auto !important;}") as demo:
    gr.Markdown(f"# AnxLight Launcher ({APP_VERSION})") 
    
    _initial_models, _initial_vaes, _initial_controlnets, _initial_loras = get_asset_choices(SD_VERSION_CHOICES[0], INPAINTING_FILTER_CHOICES[0])
    _initial_webui = WEBUI_CHOICES[0]
    _initial_is_comfy = (_initial_webui == 'ComfyUI')

    with gr.Tabs():
        with gr.TabItem("Setup & Asset Selection"):
            gr.Markdown("## Main Configuration")
            with gr.Row():
                webui_choice_dd = gr.Dropdown(label="Select WebUI", choices=WEBUI_CHOICES, value=_initial_webui, interactive=True)
                sd_version_rb = gr.Radio(label="Model Version", choices=SD_VERSION_CHOICES, value=SD_VERSION_CHOICES[0], interactive=True)
            
            inpainting_filter_rg = gr.Radio(label="Model Type Filter", info="Filters the 'Select Models' list below.", choices=INPAINTING_FILTER_CHOICES, value=INPAINTING_FILTER_CHOICES[0], interactive=True)
            
            with gr.Row(equal_height=False): 
                update_webui_chk = gr.Checkbox(label="Update WebUI", value=True, info="To latest commit (if Commit Hash empty).")
                update_extensions_chk = gr.Checkbox(label="Update Extensions", value=True, info="To latest commit.", visible=not _initial_is_comfy)
                check_custom_nodes_deps_chk = gr.Checkbox(label="Check ComfyUI Nodes Deps", value=True, visible=_initial_is_comfy, info="For ComfyUI, check custom node dependencies.")
                detailed_download_chk = gr.Checkbox(label="Detailed Download Log", value=False, info="Enable detailed UI and file logging for backend processes.")

            gr.Markdown("### Assets Selection")
            with gr.Row():
                models_cbg = gr.CheckboxGroup(label="Select Models", choices=_initial_models, value=[])
                vaes_cbg = gr.CheckboxGroup(label="Select VAEs", choices=_initial_vaes, value=[])
            with gr.Row():
                controlnets_cbg = gr.CheckboxGroup(label="Select ControlNets", choices=_initial_controlnets, value=[])
                loras_cbg = gr.CheckboxGroup(label="Select LoRAs", choices=_initial_loras, value=[])

            gr.Markdown("### Advanced Options")
            commit_hash_tb = gr.Textbox(label="WebUI Commit Hash", info="Optional. Overrides 'Update WebUI'. For specific WebUI version.", placeholder="e.g., a1b2c3d...")
            
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
            custom_args_tb = gr.Textbox(label="Custom Launch Arguments for WebUI", value=WEBUI_DEFAULT_ARGS[_initial_webui], placeholder="e.g., --xformers --no-half-vae")
            theme_accent_dd = gr.Dropdown(label="Launcher UI Theme Accent", choices=THEME_CHOICES, value=THEME_CHOICES[1], info="Select a visual theme (effects Gradio's default themes).", visible=not _initial_is_comfy)

        with gr.TabItem("Launch & Live Log"):
            gr.Markdown("## Launch Controls")
            launch_button = gr.Button("Install, Download & Launch", variant="primary")
            live_log_ta = gr.Textbox(label="Live Log Output", lines=20, interactive=False, max_lines=50, show_copy_button=True)
            
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
    print(f"Launching Gradio App for AnxLight ({APP_VERSION})...") 
    demo.queue().launch(debug=True, share=True, prevent_thread_lock=True, show_error=True)