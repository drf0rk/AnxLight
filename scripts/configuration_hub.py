#!/usr/bin/env python3
"""
Project Trinity - Configuration Hub v1.0.0
Interactive Gradio interface for WebUI and model configuration
"""

import os
import sys
import json
import time
import gradio as gr
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import project modules
from modules import json_utils as js
from modules.webui_utils import update_current_webui

# Add scripts/data to path
scripts_data_path = PROJECT_ROOT / 'scripts' / 'data'
if str(scripts_data_path) not in sys.path:
    sys.path.insert(0, str(scripts_data_path))

# Import data modules
try:
    from sd15_data import sd15_model_data, sd15_vae_data, sd15_controlnet_data, sd15_lora_data
    from sdxl_data import sdxl_model_data, sdxl_vae_data, sdxl_controlnet_data, sdxl_lora_data
except ImportError as e:
    print(f"Warning: Could not import data modules: {e}")
    # Fallback empty dicts
    sd15_model_data = sd15_vae_data = sd15_controlnet_data = sd15_lora_data = {}
    sdxl_model_data = sdxl_vae_data = sdxl_controlnet_data = sdxl_lora_data = {}

# Trinity Configuration
TRINITY_VERSION = "1.0.0"
CONFIG_PATH = PROJECT_ROOT / "trinity_config.json"
LOG_FILE = PROJECT_ROOT / "trinity_unified.log"

# WebUI options
WEBUI_CHOICES = ["A1111", "ComfyUI", "Forge", "Classic", "ReForge", "SD-UX"]
SD_VERSION_CHOICES = ["SD1.5", "SDXL"]
THEME_CHOICES = ["Default", "gradio/soft", "gradio/base", "gradio/glass", "gradio/monochrome"]

# Default arguments for WebUIs
WEBUI_DEFAULT_ARGS = {
    "A1111": "--xformers --no-half-vae --medvram --theme dark",
    "ComfyUI": "--auto-launch --gpu-only",
    "Forge": "--xformers --no-half-vae --medvram --theme dark",
    "Classic": "--xformers --no-half-vae --medvram --theme dark",
    "ReForge": "--xformers --no-half-vae --medvram --theme dark",
    "SD-UX": "--xformers --no-half-vae --medvram --theme dark"
}

def log_to_unified(message: str, level: str = "INFO"):
    """Unified logging with Trinity integration"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [v{TRINITY_VERSION}] [{level}] [CONFIG-HUB] {message}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    # Print based on level
    if level in ["ERROR", "SUCCESS", "WARNING"]:
        print(f"[{level}] {message}")
    else:
        print(f"[INFO] {message}")

def load_config() -> Dict[str, Any]:
    """Load Trinity configuration"""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            log_to_unified(f"Error loading config: {e}", "ERROR")
    
    # Default config
    return {
        "trinity_version": TRINITY_VERSION,
        "session_id": f"TR_{int(time.time())}",
        "webui_choice": "A1111",
        "sd_version": "SD1.5",
        "selected_models": [],
        "selected_vaes": [],
        "selected_controlnets": [],
        "selected_loras": [],
        "custom_args": "",
        "theme": "Default",
        "update_webui": False,
        "update_extensions": False,
        "check_custom_nodes_deps": True,
        "civitai_token": "",
        "huggingface_token": "",
        "ngrok_token": "",
        "zrok_token": ""
    }

def save_config(config: Dict[str, Any]) -> bool:
    """Save Trinity configuration"""
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        log_to_unified(f"Error saving config: {e}", "ERROR")
        return False

def get_asset_choices(sd_version: str) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Get asset choices based on SD version"""
    if sd_version == "SD1.5":
        models = list(sd15_model_data.keys()) if sd15_model_data else ["No SD1.5 models available"]
        vaes = list(sd15_vae_data.keys()) if sd15_vae_data else ["No SD1.5 VAEs available"]
        controlnets = list(sd15_controlnet_data.keys()) if sd15_controlnet_data else ["No SD1.5 ControlNets available"]
        loras = list(sd15_lora_data.keys()) if sd15_lora_data else ["No SD1.5 LoRAs available"]
    else:  # SDXL
        models = list(sdxl_model_data.keys()) if sdxl_model_data else ["No SDXL models available"]
        vaes = list(sdxl_vae_data.keys()) if sdxl_vae_data else ["No SDXL VAEs available"]
        controlnets = list(sdxl_controlnet_data.keys()) if sdxl_controlnet_data else ["No SDXL ControlNets available"]
        loras = list(sdxl_lora_data.keys()) if sdxl_lora_data else ["No SDXL LoRAs available"]
    
    return models, vaes, controlnets, loras

def update_ui_elements(sd_version: str, webui_choice: str) -> Tuple[List[str], List[str], List[str], List[str], str, bool, bool]:
    """Update UI elements based on selections"""
    models, vaes, controlnets, loras = get_asset_choices(sd_version)
    default_args = WEBUI_DEFAULT_ARGS.get(webui_choice, "")
    
    # ComfyUI specific settings
    is_comfy = (webui_choice == 'ComfyUI')
    check_nodes_visible = is_comfy
    update_ext_visible = not is_comfy
    
    return models, vaes, controlnets, loras, default_args, check_nodes_visible, update_ext_visible

def save_and_trigger_launch(
    webui_choice: str,
    sd_version: str,
    selected_models: List[str],
    selected_vaes: List[str],
    selected_controlnets: List[str],
    selected_loras: List[str],
    custom_args: str,
    theme: str,
    update_webui: bool,
    update_extensions: bool,
    check_custom_nodes_deps: bool,
    civitai_token: str,
    huggingface_token: str,
    ngrok_token: str,
    zrok_token: str
) -> str:
    """Save configuration and trigger Cell 3 launch"""
    # Update config
    config = {
        "trinity_version": TRINITY_VERSION,
        "session_id": f"TR_{int(time.time())}",
        "webui_choice": webui_choice,
        "sd_version": sd_version,
        "selected_models": selected_models,
        "selected_vaes": selected_vaes,
        "selected_controlnets": selected_controlnets,
        "selected_loras": selected_loras,
        "custom_args": custom_args,
        "theme": theme,
        "update_webui": update_webui,
        "update_extensions": update_extensions,
        "check_custom_nodes_deps": check_custom_nodes_deps,
        "civitai_token": civitai_token,
        "huggingface_token": huggingface_token,
        "ngrok_token": ngrok_token,
        "zrok_token": zrok_token,
        "launch_triggered": True,
        "launch_time": datetime.now().isoformat()
    }
    
    # Save config
    if not save_config(config):
        return "❌ Error saving configuration. Please check logs."
    
    # Update current WebUI in settings
    update_current_webui(webui_choice)
    
    log_to_unified(f"Configuration saved for {webui_choice} with {len(selected_models)} models", "SUCCESS")
    
    # Trigger Cell 3 execution
    # Note: In Colab, Cell 3 needs to be manually executed after this
    return f"""
    ✅ Configuration saved successfully!
    
    Selected WebUI: {webui_choice}
    SD Version: {sd_version}
    Models: {len(selected_models)} selected
    VAEs: {len(selected_vaes)} selected
    ControlNets: {len(selected_controlnets)} selected
    LoRAs: {len(selected_loras)} selected
    
    🚀 Please run Cell 3 to download assets and launch {webui_choice}.
    """

def create_trinity_configuration_hub():
    """Create Trinity Configuration Hub interface"""
    log_to_unified("Initializing Trinity Configuration Hub...", "INFO")
    
    # Load existing config
    config = load_config()
    
    # Get initial choices
    initial_models, initial_vaes, initial_cnets, initial_loras = get_asset_choices(config.get("sd_version", "SD1.5"))
    
    # Create Gradio interface
    with gr.Blocks(title=f"Project Trinity v{TRINITY_VERSION} - Configuration Hub") as app:
        gr.Markdown(f"# 🔹 Project Trinity v{TRINITY_VERSION} - Configuration Hub 🔹")
        gr.Markdown("Configure your WebUI and model selections for Stable Diffusion")
        
        with gr.Tabs():
            with gr.Tab("WebUI Selection"):
                with gr.Row():
                    with gr.Column(scale=1):
                        webui_choice = gr.Dropdown(
                            label="Select WebUI",
                            choices=WEBUI_CHOICES,
                            value=config.get("webui_choice", "A1111"),
                            interactive=True
                        )
                        
                        sd_version = gr.Radio(
                            label="Model Version",
                            choices=SD_VERSION_CHOICES,
                            value=config.get("sd_version", "SD1.5"),
                            type="value",
                            interactive=True
                        )
                        
                        with gr.Accordion("Advanced Options", open=False):
                            custom_args = gr.Textbox(
                                label="Custom Launch Arguments",
                                placeholder="e.g., --medvram --theme dark",
                                value=config.get("custom_args", ""),
                                interactive=True
                            )
                            
                            theme = gr.Dropdown(
                                label="UI Theme",
                                choices=THEME_CHOICES,
                                value=config.get("theme", "Default"),
                                interactive=True
                            )
                            
                            update_webui = gr.Checkbox(
                                label="Update WebUI on Launch",
                                value=config.get("update_webui", False),
                                visible=True,
                                interactive=True
                            )
                            
                            update_extensions = gr.Checkbox(
                                label="Update Extensions on Launch",
                                value=config.get("update_extensions", False),
                                visible=True,
                                interactive=True
                            )
                            
                            check_custom_nodes_deps = gr.Checkbox(
                                label="Check ComfyUI Custom Nodes Dependencies",
                                value=config.get("check_custom_nodes_deps", True),
                                visible=(config.get("webui_choice", "A1111") == 'ComfyUI'),
                                interactive=True
                            )
                    
                    with gr.Column(scale=2):
                        models_cbg = gr.CheckboxGroup(
                            label="Select Models",
                            choices=initial_models,
                            value=config.get("selected_models", []),
                            interactive=True
                        )
                        
                        vaes_cbg = gr.CheckboxGroup(
                            label="Select VAEs",
                            choices=initial_vaes,
                            value=config.get("selected_vaes", []),
                            interactive=True
                        )
                        
                        controlnets_cbg = gr.CheckboxGroup(
                            label="Select ControlNets",
                            choices=initial_cnets,
                            value=config.get("selected_controlnets", []),
                            interactive=True
                        )
                        
                        loras_cbg = gr.CheckboxGroup(
                            label="Select LoRAs",
                            choices=initial_loras,
                            value=config.get("selected_loras", []),
                            interactive=True
                        )
            
            with gr.Tab("API Tokens"):
                gr.Markdown("### API Tokens for Model Downloads")
                gr.Markdown("These tokens are used for downloading models from various sources.")
                
                civitai_token = gr.Textbox(
                    label="CivitAI API Token",
                    placeholder="Enter your CivitAI API token",
                    value=config.get("civitai_token", ""),
                    type="password",
                    interactive=True
                )