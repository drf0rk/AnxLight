#!/usr/bin/env python3
"""
Project Trinity - Execution Engine v1.0.0
Asset download and WebUI launch system
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union

# Get project root - handle both direct execution and exec()
try:
    # When run as a script
    PROJECT_ROOT = Path(__file__).parent.parent
except NameError:
    # When run via exec()
    PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', '/content/AnxLight'))

sys.path.insert(0, str(PROJECT_ROOT))

# Import project modules
from modules import json_utils as js
from modules.Manager import download_selected_assets, m_download, m_clone
from modules.webui_utils import update_current_webui, get_webui_asset_path

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
EXECUTION_LOG = PROJECT_ROOT / "trinity_execution.log"

def log_to_unified(message: str, level: str = "INFO", force_display: bool = False):
    """Unified logging with Trinity integration"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [v{TRINITY_VERSION}] [{level}] [EXECUTION] {message}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    # Also log to execution log
    with open(EXECUTION_LOG, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    # Print based on level or force_display
    if force_display or level in ["ERROR", "SUCCESS", "WARNING"]:
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
            return {}
    else:
        log_to_unified("Configuration file not found", "ERROR")
        return {}

def update_config_status(status: str, details: Optional[str] = None):
    """Update configuration status"""
    config = load_config()
    config["execution_status"] = status
    config["execution_details"] = details
    config["execution_time"] = datetime.now().isoformat()
    
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        log_to_unified(f"Error updating config status: {e}", "ERROR")

def download_assets(config: Dict[str, Any]) -> bool:
    """Download selected assets"""
    log_to_unified("Starting asset download...", "INFO")
    
    try:
        # Extract configuration
        webui_choice = config.get("webui_choice", "A1111")
        sd_version = config.get("sd_version", "SD1.5")
        selected_models = config.get("selected_models", [])
        selected_vaes = config.get("selected_vaes", [])
        selected_controlnets = config.get("selected_controlnets", [])
        selected_loras = config.get("selected_loras", [])
        civitai_token = config.get("civitai_token", "")
        huggingface_token = config.get("huggingface_token", "")
        
        # Log selections
        log_to_unified(f"WebUI: {webui_choice}, SD Version: {sd_version}", "INFO")
        log_to_unified(f"Models: {len(selected_models)}, VAEs: {len(selected_vaes)}, ControlNets: {len(selected_controlnets)}, LoRAs: {len(selected_loras)}", "INFO")
        
        # Skip if no assets selected
        if not any([selected_models, selected_vaes, selected_controlnets, selected_loras]):
            log_to_unified("No assets selected for download", "WARNING")
            return True
        
        # Download assets
        download_config = {
            "webui_choice": webui_choice,
            "sd_version": sd_version,
            "selected_models": selected_models,
            "selected_vaes": selected_vaes,
            "selected_controlnets": selected_controlnets,
            "selected_loras": selected_loras,
            "civitai_token": civitai_token,
            "huggingface_token": huggingface_token
        }
        
        # Use download_selected_assets function from Manager.py
        result = download_selected_assets(download_config)
        
        if result:
            log_to_unified("Asset download completed successfully", "SUCCESS")
            return True
        else:
            log_to_unified("Asset download failed", "ERROR")
            return False
            
    except Exception as e:
        log_to_unified(f"Error downloading assets: {e}", "ERROR")
        return False

def launch_webui(config: Dict[str, Any]) -> bool:
    """Launch selected WebUI"""
    log_to_unified("Launching WebUI...", "INFO")
    
    try:
        # Extract configuration
        webui_choice = config.get("webui_choice", "A1111")
        custom_args = config.get("custom_args", "")
        update_webui = config.get("update_webui", False)
        update_extensions = config.get("update_extensions", False)
        check_custom_nodes_deps = config.get("check_custom_nodes_deps", True)
        
        # Update current WebUI in settings
        update_current_webui(webui_choice)
        
        # Prepare launch command
        launch_script = PROJECT_ROOT / "scripts" / "launch.py"
        
        if not launch_script.exists():
            log_to_unified(f"Launch script not found: {launch_script}", "ERROR")
            return False
        
        # Build command
        cmd = [sys.executable, str(launch_script)]
        
        if update_webui:
            cmd.append("--update-webui")
        
        if update_extensions:
            cmd.append("--update-extensions")
        
        if check_custom_nodes_deps and webui_choice == "ComfyUI":
            cmd.append("--check-custom-nodes-deps")
        
        if custom_args:
            cmd.append("--args")
            cmd.append(custom_args)
        
        # Log launch command
        log_to_unified(f"Launch command: {' '.join(cmd)}", "INFO")
        
        # Execute launch script
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output
        log_to_unified(f"WebUI launch process started (PID: {process.pid})", "SUCCESS")
        
        # Monitor for a short time to catch immediate failures
        start_time = time.time()
        while process.poll() is None and time.time() - start_time < 10:
            output = process.stdout.readline()
            if output:
                log_to_unified(output.strip(), "INFO")
        
        # Check if process died immediately
        if process.poll() is not None:
            returncode = process.poll()
            log_to_unified(f"WebUI process exited early with code {returncode}", "ERROR")
            return False
        
        # Process is still running, consider it successful
        log_to_unified(f"WebUI {webui_choice} launched successfully", "SUCCESS")
        return True
        
    except Exception as e:
        log_to_unified(f"Error launching WebUI: {e}", "ERROR")
        return False

def execute_trinity_launch():
    """Main execution function"""
    log_to_unified("=== TRINITY EXECUTION ENGINE STARTED ===", "INFO")
    
    try:
        # Load configuration
        config = load_config()
        
        if not config:
            log_to_unified("No configuration found. Please run Cell 2 first.", "ERROR")
            return False
        
        # Update status
        update_config_status("downloading", "Starting asset download")
        
        # Download assets
        download_success = download_assets(config)
        
        if not download_success:
            update_config_status("failed", "Asset download failed")
            log_to_unified("Execution failed at asset download stage", "ERROR")
            return False
        
        # Update status
        update_config_status("launching", "Starting WebUI launch")
        
        # Launch WebUI
        launch_success = launch_webui(config)
        
        if not launch_success:
            update_config_status("failed", "WebUI launch failed")
            log_to_unified("Execution failed at WebUI launch stage", "ERROR")
            return False
        
        # Update status
        update_config_status("running", "WebUI running")
        log_to_unified("=== TRINITY EXECUTION COMPLETED SUCCESSFULLY ===", "SUCCESS")
        return True
        
    except Exception as e:
        log_to_unified(f"Execution error: {e}", "ERROR")
        update_config_status("error", str(e))
        return False

if __name__ == "__main__":
    # Create log directory if it doesn't exist
    LOG_FILE.parent.mkdir(exist_ok=True)
    
    # Clear execution log
    with open(EXECUTION_LOG, 'w') as f:
        f.write(f"[{datetime.now().isoformat()}] Trinity Execution Log v{TRINITY_VERSION}\n")
    
    # Execute launch
    success = execute_trinity_launch()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)