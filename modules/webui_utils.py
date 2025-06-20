\"\"\" WebUI Utilities Module | by ANXETY \"\"\"

import json_utils as js

from pathlib import Path
import json
import os


osENV = os.environ


# ======================== CONSTANTS =======================

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS.get('home_path', Path(osENV.get('HOME', '/content'))) # Add fallback for HOME if home_path not in env
VENV = PATHS.get('venv_path')
SCR_PATH = PATHS.get('scr_path')
SETTINGS_PATH = PATHS.get('settings_path', HOME / 'anxlight_config.json') # Add fallback for SETTINGS_PATH

DEFAULT_UI = 'A1111'

WEBUI_PATHS = {
    'A1111': (
        'Stable-diffusion', 'VAE', 'Lora',
        'embeddings', 'extensions', 'ESRGAN', 'outputs'
    ),
    'ComfyUI': (
        'checkpoints', 'vae', 'loras',
        'embeddings', 'custom_nodes', 'upscale_models', 'output'
    ),
    'Classic': ( # Assuming Classic is similar to A1111 for these specific paths
        'Stable-diffusion', 'VAE', 'Lora',
        'embeddings', 'extensions', 'ESRGAN', 'output'
    ),
    'Forge': ( # Assuming Forge is similar to A1111 for these specific paths
        'Stable-diffusion', 'VAE', 'Lora',
        'embeddings', 'extensions', 'ESRGAN', 'outputs'
    )
}

# Mapping from generic asset types used in main_gradio_app.py 
# to the specific directory keys used in _set_webui_paths / anxlight_config.json
ASSET_TYPE_TO_CONFIG_KEY_MAP = {
    "models": "model_dir",      # For checkpoints/Stable Diffusion models
    "vaes": "vae_dir",
    "loras": "lora_dir",
    "controlnet": "control_dir", # Note: 'controlnet' not 'controlnets'
    "embeddings": "embed_dir",
    "upscalers": "upscale_dir", # Maps to 'upscale_models' in WEBUI_PATHS for Comfy, 'ESRGAN' for A1111/Classic/Forge
    # For specific model types if needed by Manager.py or specific WebUIs:
    "adetailer": "adetailer_dir",
    "clip": "clip_dir",
    "unet": "unet_dir",
    "clip_vision": "vision_dir", # 'vision_dir' key from _set_webui_paths
    "text_encoders": "encoder_dir", # 'encoder_dir' key from _set_webui_paths
    "diffusion_models": "diffusion_dir" # 'diffusion_dir' key from _set_webui_paths
}

# ===================== WEBUI HANDLERS =====================

def update_current_webui(current_value: str) -> None:
    \"\"\"Update the current WebUI value and save settings.\"\"\"
    if not SETTINGS_PATH:
        print("[webui_utils] ERROR: SETTINGS_PATH is not defined. Cannot update WebUI settings.")
        return
    current_stored = js.read(SETTINGS_PATH, 'WEBUI.current')
    latest_value = js.read(SETTINGS_PATH, 'WEBUI.latest', None)

    if latest_value is None or current_stored != current_value:
        js.save(SETTINGS_PATH, 'WEBUI.latest', current_stored)
        js.save(SETTINGS_PATH, 'WEBUI.current', current_value)

    js.save(SETTINGS_PATH, 'WEBUI.webui_path', str(HOME / current_value))
    _set_webui_paths(current_value)


def _set_webui_paths(ui: str) -> None:
    \"\"\"Configure paths for specified UI, fallback to A1111 for unknown UIs.\"\"\"
    if not SETTINGS_PATH:
        print("[webui_utils] ERROR: SETTINGS_PATH is not defined. Cannot set WebUI paths.")
        return
        
    selected_ui_name = ui if ui in WEBUI_PATHS else DEFAULT_UI
    if ui not in WEBUI_PATHS:
        print(f"[webui_utils] Warning: UI '{ui}' not in WEBUI_PATHS. Falling back to '{DEFAULT_UI}' for path structure.")

    webui_root = HOME / ui # Actual selected UI for root path
    models_root = webui_root / 'models'

    # Get path components for the selected_ui_name (which might be DEFAULT_UI if original ui was unknown)
    path_components = WEBUI_PATHS[selected_ui_name]
    checkpoint, vae, lora, embed, extension_or_custom_nodes, upscale_or_esrgan, output_folder = path_components

    # Configure special paths based on actual selected 'ui'
    is_comfy = ui == 'ComfyUI'
    is_classic_or_forge = ui == 'Classic' or ui == 'Forge' # Grouping similar structures
    
    control_dir_name = 'controlnet' if is_comfy else 'ControlNet'
    embed_root_actual = models_root if (is_comfy or is_classic_or_forge) else webui_root
    # Config dir for Comfy might be just webui_root if 'user/default' is not standard or always present
    config_root_actual = webui_root / 'user/default' if is_comfy else webui_root 
    
    adetailer_dir_name = 'ultralytics' if is_comfy else 'adetailer' # ADetailer models often go here
    clip_dir_name = 'clip' if is_comfy else 'text_encoder' # Placeholder, actual name might vary
    unet_dir_name = 'unet' if is_comfy else 'text_encoder' # Placeholder
    text_encoders_dir_name = 'text_encoders' if is_comfy else 'text_encoder'


    path_config = {
        'model_dir': str(models_root / checkpoint),
        'vae_dir': str(models_root / vae),
        'lora_dir': str(models_root / lora),
        'embed_dir': str(embed_root_actual / embed),
        'extension_dir': str(webui_root / extension_or_custom_nodes), # Covers Comfy's custom_nodes and A1111's extensions
        'control_dir': str(models_root / control_dir_name),
        'upscale_dir': str(models_root / upscale_or_esrgan), # Covers Comfy's upscale_models and A1111's ESRGAN
        'output_dir': str(webui_root / output_folder),
        'config_dir': str(config_root_actual),
        'adetailer_dir': str(models_root / adetailer_dir_name),
        'clip_dir': str(models_root / clip_dir_name), # Often for SD1.5 CLIP
        'unet_dir': str(models_root / unet_dir_name), # Often for SD1.5 UNET
        'vision_dir': str(models_root / 'clip_vision'), # Common for SDXL CLIP Vision
        'encoder_dir': str(models_root / text_encoders_dir_name), # Common for SDXL Text Encoders
        'diffusion_dir': str(models_root / 'diffusion_models') # Generic diffusion models
    }
    js.update(SETTINGS_PATH, 'WEBUI', path_config)


def get_webui_asset_path(webui_name: str, asset_type_plural: str, asset_filename: str) -> str:
    \"\"\"
    Gets the absolute path for a given asset type and filename for the specified WebUI.
    It reads the pre-configured directory paths from anxlight_config.json.
    Assumes update_current_webui() has already been called for the session to populate these paths.
    \"\"\"
    if not SETTINGS_PATH:
        print("[webui_utils] ERROR: SETTINGS_PATH is not defined. Cannot get asset path.")
        return ""
    if not asset_filename:
        print(f"[webui_utils] Warning: asset_filename is empty for asset type '{asset_type_plural}'. Cannot determine path.")
        return ""

    config_key = ASSET_TYPE_TO_CONFIG_KEY_MAP.get(asset_type_plural.lower())
    if not config_key:
        print(f"[webui_utils] Warning: Unknown asset_type_plural '{asset_type_plural}' for path mapping. Cannot determine path for '{asset_filename}'.")
        return ""

    try:
        asset_dir = js.read(SETTINGS_PATH, f'WEBUI.{config_key}')
        if asset_dir and isinstance(asset_dir, str) and Path(asset_dir).is_absolute():
            return str(Path(asset_dir) / asset_filename)
        elif asset_dir and isinstance(asset_dir, str): # If relative, assume relative to HOME
            print(f"[webui_utils] Warning: Path for '{config_key}' is relative: '{asset_dir}'. Resolving against HOME: {HOME}")
            return str(HOME / asset_dir / asset_filename)
        else:
            print(f"[webui_utils] Warning: Directory path for '{config_key}' (asset type '{asset_type_plural}') not found or invalid in config for WebUI '{webui_name}'. Path read: {asset_dir}")
            return "" # Indicate failure to find pre-configured path
            
    except Exception as e:
        print(f"[webui_utils] Error reading/determining path for {asset_type_plural} '{asset_filename}' for WebUI '{webui_name}': {e}")
        return ""

def get_webui_installation_root(webui_name: str) -> str:
    \"\"\"
    Returns the absolute root path of the specified WebUI installation.
    This is typically HOME / webui_name.
    \"\"\"
    if webui_name and isinstance(webui_name, str):
        return str(HOME / webui_name)
    print(f"[webui_utils] Warning: Could not determine installation root for webui_name: {webui_name}")
    return ""


def handle_setup_timer(webui_path: str, timer_webui: float) -> float:
    \"\"\"Manage timer persistence for WebUI instances.\"\"\"
    timer_file = Path(webui_path) / 'static' / 'timer.txt' # 'static' might not exist for all UIs
    
    # Ensure parent directory of timer.txt exists
    # More robustly, place timer.txt in a known location like webui_path itself or webui_path / '.anxlight_meta'
    # For now, let's try to create 'static' if it doesn't exist, but this is a guess.
    # A better approach would be to store this in anxlight_config.json or a dedicated AnxLight metadata dir.
    
    # Let's assume timer.txt is at the root of webui_path for more reliability
    timer_file = Path(webui_path) / '.anxlight_timer.txt'

    try:
        timer_file.parent.mkdir(parents=True, exist_ok=True) # Ensures webui_path exists
        with timer_file.open('r') as f:
            timer_webui = float(f.read())
    except FileNotFoundError:
        pass # File not found, will use provided timer_webui or default
    except ValueError:
        print(f"[webui_utils] Warning: Could not parse float from timer file: {timer_file}. Using provided value.")
    except Exception as e:
        print(f"[webui_utils] Error reading timer file {timer_file}: {e}")


    try:
        with timer_file.open('w') as f:
            f.write(str(timer_webui))
    except Exception as e:
        print(f"[webui_utils] Error writing to timer file {timer_file}: {e}")

    return timer_webui