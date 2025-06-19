# scripts/pre_flight_setup.py
import os
import subprocess
import sys
import importlib.util # For importing anxlight_version

# --- Configuration ---
ANXLIGHT_REPO_URL = "https://github.com/drf0rk/AnxLight.git"
PROJECT_ROOT_DIR = "AnxLight" # The directory name after cloning

# List of WebUIs to install - paths to their setup scripts within AnxLight repo
# Example: SUPPORTED_WEBUIS = {
#    "A1111": "scripts/UIs/A1111_setup.py", # Assuming setup scripts are named like this
#    "ComfyUI": "scripts/UIs/ComfyUI_setup.py",
#    "Forge": "scripts/UIs/Forge_setup.py",
# }
# This will need to be populated based on actual available UI setup scripts.
# For now, let's assume a placeholder or that main_gradio_app.py might eventually provide this list.
SUPPORTED_WEBUIS = {
    "A1111": "scripts/UIs/A1111.py", # Using existing names for now, may need dedicated setup wrappers
    # Add ComfyUI, Forge etc. when their setup scripts are ready
}

CORE_DEPENDENCIES = ["gradio", "pyngrok", "huggingface-hub"] # Add other core deps here

# Tunneling clients - commands to check if installed and install commands
# This is a simplified example; actual installation might be more complex (e.g., downloading binaries)
TUNNELING_CLIENTS = {
    "cloudflared": {
        "check_command": "cloudflared --version",
        "install_command": "echo 'Please install cloudflared manually: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/'" # Placeholder
    },
    "ngrok": { # pyngrok handles ngrok binary, but good to ensure system ngrok isn't conflicting if used directly
        "check_command": "ngrok version",
        "install_command": "echo 'pyngrok will manage ngrok binary. If system ngrok is needed, install manually.'"
    },
    # Add Zrok, Serveo etc.
}

VENV_NAME = "anxlight_venv"
PYTHON_EXECUTABLE = "python3" # Or "python" depending on the system

# --- Helper Functions ---
def run_command(command, cwd=None, env=None, check=True, shell=False):
    """Runs a shell command and prints its output."""
    print(f"Executing: {' '.join(command) if isinstance(command, list) else command}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Redirect stderr to stdout
            text=True,
            cwd=cwd,
            env=env,
            shell=shell,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        for line in process.stdout:
            print(line, end='')
        process.wait()
        if check and process.returncode != 0:
            print(f"Error: Command '{' '.join(command) if isinstance(command, list) else command}' failed with exit code {process.returncode}")
            # sys.exit(process.returncode) # Option to exit on error
            return False
        return True
    except Exception as e:
        print(f"Exception running command {' '.join(command) if isinstance(command, list) else command}: {e}")
        return False

def import_versions():
    """Imports version variables from scripts/anxlight_version.py"""
    try:
        version_file_path = os.path.join(os.path.dirname(__file__), "anxlight_version.py")
        spec = importlib.util.spec_from_file_location("anxlight_version", version_file_path)
        anxlight_version = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(anxlight_version)
        return anxlight_version
    except ImportError:
        print("Error: Could not import scripts/anxlight_version.py. Ensure it exists.")
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
        # Add more versions as they are defined in anxlight_version.py
    else:
        print("Version information could not be loaded.")
    print("---------------------------------")

def step_1_clone_or_update_repo():
    """Clones or updates the AnxLight repository."""
    print("\n--- Step 1: Cloning/Updating AnxLight Repository ---")
    if os.path.exists(PROJECT_ROOT_DIR) and os.path.isdir(PROJECT_ROOT_DIR):
        print(f"Directory '{PROJECT_ROOT_DIR}' already exists. Attempting to pull latest changes.")
        if not run_command(["git", "pull"], cwd=PROJECT_ROOT_DIR):
            print(f"Warning: Failed to pull latest changes in {PROJECT_ROOT_DIR}. Continuing with existing version.")
    else:
        print(f"Cloning AnxLight repository into '{PROJECT_ROOT_DIR}'...")
        if not run_command(["git", "clone", ANXLIGHT_REPO_URL, PROJECT_ROOT_DIR]):
            print("Error: Failed to clone repository. Exiting.")
            sys.exit(1)
    # Change current working directory to the project root for subsequent steps
    # This assumes pre_flight_setup.py is run from outside PROJECT_ROOT_DIR initially,
    # or paths are adjusted accordingly if run from within.
    # For simplicity, let's assume it's run from the parent of where PROJECT_ROOT_DIR will be.
    # If this script itself is inside PROJECT_ROOT_DIR/scripts, CWD management is different.
    # For now, let's assume we need to `cd` into it if it was just cloned.
    # This part needs careful consideration based on how the notebook calls this script.
    # For now, let's assume subsequent commands will use PROJECT_ROOT_DIR as cwd.
    print("Repository setup complete.")


def step_2_install_core_dependencies():
    """Installs core Python dependencies."""
    print("\n--- Step 2: Installing Core Dependencies ---")
    # This should ideally use the VENV's pip if VENV is already set up.
    # For now, let's assume direct pip install. VENV setup comes later.
    # Or, VENV should be set up first. Let's re-order.
    for dep in CORE_DEPENDENCIES:
        run_command([sys.executable, "-m", "pip", "install", dep]) # Use sys.executable for pip in current env

def step_3_setup_virtual_environment():
    """Sets up the Python virtual environment."""
    print("\n--- Step 3: Setting up Virtual Environment ---")
    venv_path = os.path.join(PROJECT_ROOT_DIR, VENV_NAME) # Assuming PROJECT_ROOT_DIR is now the CWD or accessible
    
    # Path to python executable within the venv
    if sys.platform == "win32":
        python_in_venv = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_in_venv = os.path.join(venv_path, "bin", "python")

    if not os.path.exists(python_in_venv):
        print(f"Creating virtual environment at: {venv_path}")
        if not run_command([PYTHON_EXECUTABLE, "-m", "venv", venv_path], cwd="."): # Create venv
             print(f"Failed to create virtual environment. Attempting to continue without.")
             return None # Indicate failure or proceed without venv
    else:
        print(f"Virtual environment already exists at: {venv_path}")
    
    print(f"To activate the VENV (manual step if needed):")
    if sys.platform == "win32":
        print(f"  {os.path.join(venv_path, 'Scripts', 'activate')}")
    else:
        print(f"  source {os.path.join(venv_path, 'bin', 'activate')}")
    return python_in_venv # Return path to python in venv for subsequent pip installs

def step_4_install_dependencies_in_venv(python_in_venv):
    """Installs core Python dependencies into the VENV."""
    if not python_in_venv:
        print("Skipping VENV dependency installation as VENV setup failed or was skipped.")
        # Fallback to global install (already done in step_2 conceptually, but this makes it explicit for venv)
        print("Attempting global dependency installation again as fallback.")
        step_2_install_core_dependencies()
        return

    print(f"\n--- Step 4: Installing Core Dependencies into VENV ({VENV_NAME}) ---")
    for dep in CORE_DEPENDENCIES:
        run_command([python_in_venv, "-m", "pip", "install", dep])


def step_5_install_tunneling_clients():
    """Checks and installs tunneling clients."""
    print("\n--- Step 5: Installing Tunneling Clients ---")
    for client_name, info in TUNNELING_CLIENTS.items():
        print(f"Checking for {client_name}...")
        try:
            # Use subprocess.call to suppress output for check, or parse version
            if subprocess.call(info["check_command"].split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                print(f"{client_name} is already installed.")
            else:
                raise FileNotFoundError # Simulate not found if command fails
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(f"{client_name} not found. Attempting to install (or providing instructions)...")
            run_command(info["install_command"], shell=True) # Some installers might need shell

def step_6_install_webuis(python_in_venv_or_global):
    """Installs all supported WebUIs."""
    print("\n--- Step 6: Installing All Supported WebUIs ---")
    # Determine the python executable to use for running WebUI setup scripts
    # If VENV setup was successful, use python from VENV. Otherwise, use global python.
    python_to_use = python_in_venv_or_global if python_in_venv_or_global else sys.executable

    if not os.path.exists(PROJECT_ROOT_DIR) or not os.path.isdir(PROJECT_ROOT_DIR):
        print(f"Error: Project directory '{PROJECT_ROOT_DIR}' not found. Please run Step 1 first.")
        return

    for ui_name, setup_script_path_rel in SUPPORTED_WEBUIS.items():
        print(f"\n-- Installing {ui_name} --")
        # setup_script_full_path = os.path.join(PROJECT_ROOT_DIR, setup_script_path_rel) # If CWD is parent
        setup_script_full_path = setup_script_path_rel # If CWD is PROJECT_ROOT_DIR

        if not os.path.exists(setup_script_full_path):
            print(f"Warning: Setup script for {ui_name} not found at '{setup_script_full_path}'. Skipping.")
            continue
        
        # The WebUI setup scripts (e.g., A1111.py) might need to be run from PROJECT_ROOT_DIR
        # and might also need specific environment variables set.
        # This part requires that those scripts are runnable independently.
        # They might also handle their own VENV or expect to be run in one.
        print(f"Running setup for {ui_name} using {python_to_use}...")
        if not run_command([python_to_use, setup_script_full_path], cwd=PROJECT_ROOT_DIR): # Run from project root
            print(f"Warning: Installation of {ui_name} may have failed.")
    print("All WebUI installations attempted.")


if __name__ == "__main__":
    # This structure assumes the script is run and AnxLight is cloned into a subdir.
    # If AnxLight is already cloned and this script is inside AnxLight/scripts,
    # then PROJECT_ROOT_DIR should be '..' or an absolute path.
    # For now, let's adjust PROJECT_ROOT_DIR if the script is inside the repo.
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # If this script is in "AnxLight/scripts", then project_root is one level up from script_dir's parent
    # However, the v3 plan implies Cell 1 clones the repo, then runs this.
    # So, PROJECT_ROOT_DIR = "AnxLight" (as a subdirectory) is correct if Cell 1 is in a parent dir.
    # If Cell 1 `cd AnxLight` then runs `python scripts/pre_flight_setup.py`, then PROJECT_ROOT_DIR should be "."

    # Let's assume the notebook ensures CWD is AnxLight project root before calling this script.
    # So, PROJECT_ROOT_DIR should refer to the CWD.
    PROJECT_ROOT_DIR = "." # Current working directory is assumed to be AnxLight root.

    versions = import_versions()
    step_0_display_welcome_and_versions(versions)
    
    # Step 1 (Clone/Update) is handled by the notebook's Cell 1 before this script is run.
    # So, we can comment it out here or make it just a 'git pull'.
    # For now, let's assume the notebook handles the clone/update, and CWD is already AnxLight.
    print("\n--- Step 1: Repository Setup (Assumed done by Notebook Cell 1) ---")
    print(f"Current working directory is expected to be: {os.path.abspath(PROJECT_ROOT_DIR)}")
    print("Running 'git pull' to ensure latest version...")
    run_command(["git", "pull"], cwd=PROJECT_ROOT_DIR)


    # Order of VENV setup and dependency install is important.
    # 1. Setup VENV
    # 2. Install deps into VENV
    python_in_venv = step_3_setup_virtual_environment() # Creates VENV inside PROJECT_ROOT_DIR

    # If python_in_venv is None, it means VENV setup failed or was skipped.
    # In this case, dependencies will be installed globally (or into current python env).
    # The step_4 function handles this logic.
    step_4_install_dependencies_in_venv(python_in_venv)
    
    step_5_install_tunneling_clients()

    # Determine which python executable to use for WebUI installations
    # If VENV is active and working, use its python. Otherwise, fallback to global/current.
    python_for_webui_setups = python_in_venv if python_in_venv and os.path.exists(python_in_venv) else sys.executable
    step_6_install_webuis(python_for_webui_setups)
    
    print("\n--- Pre-Flight Setup Complete ---")
    print("You should now be able to run Cell 2 of the AnxLight notebook to launch the Gradio UI.")