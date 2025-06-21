# scripts/pre_flight_setup.py
import os
import subprocess
import sys
import importlib.util # For importing anxlight_version

# --- Configuration ---
# This script should be run from the root of the AnxLight repository.
PROJECT_ROOT_DIR = "." 

# List of WebUIs to install. The keys are the UI names, and the values are the paths
# to their setup scripts within the AnxLight repository.
# The order of installation here does not currently matter, but could if there were dependencies.
SUPPORTED_WEBUIS = {
    "A1111": "scripts/UIs/A1111.py",
    "Classic": "scripts/UIs/Classic.py",
    "ComfyUI": "scripts/UIs/ComfyUI.py",
    "Forge": "scripts/UIs/Forge.py",
    "ReForge": "scripts/UIs/ReForge.py",
    "SD-UX": "scripts/UIs/SD-UX.py",
}

# Core Python dependencies required for main_gradio_app.py to function.
# These will be installed into the virtual environment.
CORE_DEPENDENCIES = ["gradio", "pyngrok", "huggingface-hub"]

# Tunneling clients - commands to check if installed and provide install instructions
TUNNELING_CLIENTS = {
    "cloudflared": {
        "check_command": ["cloudflared", "--version"],
        "install_command": "echo 'Please install cloudflared manually: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/'"
    },
    "ngrok": {
        "check_command": ["ngrok", "version"],
        "install_command": "echo 'pyngrok handles its own ngrok binary. If a system-wide ngrok is needed, install it manually.'"
    },
}

VENV_NAME = "anxlight_venv"
PYTHON_EXECUTABLE = sys.executable # Use the python that is running this script to create the venv

# --- Helper Functions ---
def run_command(command, cwd=None, env=None, check=True, shell=False):
    """Runs a command and streams its output."""
    cmd_str = ' '.join(command) if isinstance(command, list) and not shell else command
    print(f"Executing: {cmd_str} in {cwd or '.'}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            env=env,
            shell=shell,
            bufsize=1,
            universal_newlines=True
        )
        for line in process.stdout:
            print(line, end='')
        process.wait()
        if check and process.returncode != 0:
            print(f"Error: Command '{cmd_str}' failed with exit code {process.returncode}", file=sys.stderr)
            return False
        return process.returncode == 0
    except Exception as e:
        print(f"Exception running command '{cmd_str}': {e}", file=sys.stderr)
        return False

def import_versions():
    """Imports version variables from scripts/anxlight_version.py"""
    try:
        version_file_path = os.path.join(os.path.dirname(__file__), "anxlight_version.py")
        spec = importlib.util.spec_from_file_location("anxlight_version", version_file_path)
        anxlight_version = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(anxlight_version)
        return anxlight_version
    except Exception as e:
        print(f"Warning: Could not import scripts/anxlight_version.py. {e}", file=sys.stderr)
        return None

# --- Main Setup Steps ---

def step_0_display_welcome_and_versions(versions):
    """Displays welcome message and component versions."""
    print("--- AnxLight Pre-Flight Setup ---")
    if versions:
        print(f"AnxLight System Version: {getattr(versions, 'ANXLIGHT_OVERALL_SYSTEM_VERSION', 'N/A')}")
        print(f"  Launcher Notebook Target: v{getattr(versions, 'ANXLIGHT_LAUNCHER_NOTEBOOK_VERSION', 'N/A')}")
        print(f"  Main Gradio App Target: v{getattr(versions, 'MAIN_GRADIO_APP_VERSION', 'N/A')}")
        print(f"  Pre-Flight Setup Script: v{getattr(versions, 'PRE_FLIGHT_SETUP_PY_VERSION', 'N/A')}")
    else:
        print("Version information could not be loaded.")
    print("---------------------------------")

def step_1_update_repo():
    """Pulls the latest changes from the git repository."""
    print("\n--- Step 1: Updating AnxLight Repository ---")
    print(f"Current working directory is expected to be: {os.path.abspath(PROJECT_ROOT_DIR)}")
    print("Running 'git pull' to ensure latest version...")
    if not run_command(["git", "pull"], cwd=PROJECT_ROOT_DIR):
        print("Warning: 'git pull' failed. Continuing with the current version.", file=sys.stderr)

def step_2_setup_virtual_environment():
    """Sets up the Python virtual environment."""
    print("\n--- Step 2: Setting up Virtual Environment ---")
    venv_path = os.path.join(PROJECT_ROOT_DIR, VENV_NAME)
    
    if sys.platform == "win32":
        python_in_venv = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_in_venv = os.path.join(venv_path, "bin", "python")

    if not os.path.exists(python_in_venv):
        print(f"Creating virtual environment at: {venv_path}")
        if not run_command([PYTHON_EXECUTABLE, "-m", "venv", venv_path], cwd=PROJECT_ROOT_DIR):
             print("FATAL: Failed to create virtual environment. Exiting.", file=sys.stderr)
             sys.exit(1)
    else:
        print(f"Virtual environment already exists at: {venv_path}")
    
    print(f"Using Python from VENV: {python_in_venv}")
    return python_in_venv

def step_3_install_dependencies_in_venv(python_in_venv):
    """Installs core Python dependencies into the VENV."""
    print(f"\n--- Step 3: Installing Core Dependencies into VENV ({VENV_NAME}) ---")
    for dep in CORE_DEPENDENCIES:
        run_command([python_in_venv, "-m", "pip", "install", "--upgrade", dep])

def step_4_install_tunneling_clients():
    """Checks and provides instructions for tunneling clients."""
    print("\n--- Step 4: Checking for Tunneling Clients ---")
    for client_name, info in TUNNELING_CLIENTS.items():
        print(f"Checking for {client_name}...")
        try:
            # Use subprocess.run for a cleaner check
            result = subprocess.run(info["check_command"], capture_output=True, text=True, shell=False)
            if result.returncode == 0:
                print(f"{client_name} is already installed.")
            else:
                raise FileNotFoundError
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(f"-> {client_name} not found or accessible in PATH. Instructions:")
            run_command(info["install_command"], shell=True)

def step_5_install_webuis(python_in_venv):
    """Installs all supported WebUIs by calling their refactored setup scripts."""
    print("\n--- Step 5: Installing All Supported WebUIs ---")
    
    for ui_name, setup_script_path in SUPPORTED_WEBUIS.items():
        print(f"\n-- Installing {ui_name} --")
        
        if not os.path.exists(setup_script_path):
            print(f"Warning: Setup script for {ui_name} not found at '{setup_script_path}'. Skipping.", file=sys.stderr)
            continue
        
        print(f"Running setup for {ui_name} using {python_in_venv}...")
        # Run each UI installer script from the project root directory
        if not run_command([python_in_venv, setup_script_path], cwd=PROJECT_ROOT_DIR):
            print(f"Warning: Installation of {ui_name} may have encountered errors.", file=sys.stderr)
        else:
            print(f"-- Finished installation attempt for {ui_name} --")
            
    print("\nAll WebUI installation scripts have been executed.")

if __name__ == "__main__":
    # This script assumes it is executed from the root of the AnxLight repository.
    # The Colab notebook's Cell 1 should handle cloning and `cd AnxLight` before running this.
    
    versions = import_versions()
    step_0_display_welcome_and_versions(versions)
    
    step_1_update_repo()
    
    python_in_venv = step_2_setup_virtual_environment()
    
    step_3_install_dependencies_in_venv(python_in_venv)
    
    step_4_install_tunneling_clients()
    
    step_5_install_webuis(python_in_venv)
    
    print("\n--- Pre-Flight Setup Complete ---")
    print("You should now be able to run Cell 2 of the AnxLight notebook to launch the Gradio UI.")