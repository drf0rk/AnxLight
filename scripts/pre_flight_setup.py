# scripts/pre_flight_setup.py
import os
import subprocess
import sys
import importlib.util # For importing anxlight_version

# --- Configuration ---
PROJECT_ROOT_DIR = "." 

SUPPORTED_WEBUIS = {
    "A1111": "scripts/UIs/A1111.py",
    "Classic": "scripts/UIs/Classic.py",
    "ComfyUI": "scripts/UIs/ComfyUI.py",
    "Forge": "scripts/UIs/Forge.py",
    "ReForge": "scripts/UIs/ReForge.py",
    "SD-UX": "scripts/UIs/SD-UX.py",
}

CORE_DEPENDENCIES = ["gradio", "pyngrok", "huggingface-hub"]

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
PYTHON_EXECUTABLE = sys.executable

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
    print("--- AnxLight Pre-Flight Setup ---")
    if versions:
        print(f"AnxLight System Version: {getattr(versions, 'ANXLIGHT_OVERALL_SYSTEM_VERSION', 'N/A')}")
    else:
        print("Version information could not be loaded.")
    print("---------------------------------")

def step_0_ensure_venv_package():
    """Ensures the python3-venv package is installed on Debian-based systems."""
    print("\n--- Pre-Step: Ensuring 'python3-venv' is installed (for compatibility) ---")
    if "linux" in sys.platform:
        try:
            subprocess.run(["dpkg", "-s", "python3-venv"], capture_output=True, check=True, text=True)
            print("'python3-venv' package is already installed.")
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("'python3-venv' not found or check failed. Attempting to install...")
            run_command("sudo apt-get update -y", shell=True)
            if not run_command("sudo apt-get install -y python3-venv", shell=True):
                 print("WARNING: Failed to install 'python3-venv'. Venv creation might fail.", file=sys.stderr)
            else:
                 print("'python3-venv' installed successfully.")
    else:
        print("Skipping venv package check on non-Linux system.")

def step_1_update_repo():
    print("\n--- Step 1: Updating AnxLight Repository ---")
    if not run_command(["git", "pull"], cwd=PROJECT_ROOT_DIR):
        print("Warning: 'git pull' failed. Continuing with the current version.", file=sys.stderr)

def step_2_setup_virtual_environment():
    print("\n--- Step 2: Setting up Virtual Environment ---")
    venv_path = os.path.join(PROJECT_ROOT_DIR, VENV_NAME)
    
    if sys.platform == "win32":
        python_in_venv = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_in_venv = os.path.join(venv_path, "bin", "python")

    if not os.path.exists(python_in_venv):
        print(f"Creating virtual environment at: {venv_path} (without pip, will install manually).")
        # Use --without-pip to avoid ensurepip errors in problematic environments.
        if not run_command([PYTHON_EXECUTABLE, "-m", "venv", "--without-pip", venv_path], cwd=PROJECT_ROOT_DIR):
             print("FATAL: Failed to create virtual environment structure. Exiting.", file=sys.stderr)
             sys.exit(1)
    else:
        print(f"Virtual environment already exists at: {venv_path}")
    
    print(f"VENV Python executable path: {python_in_venv}")
    return python_in_venv

def step_2b_install_pip_in_venv(python_in_venv):
    """Ensures pip is installed in the new VENV, fixing 'No module named pip' errors."""
    print("\n--- Step 2b: Verifying/Installing pip in Virtual Environment ---")
    pip_check_command = [python_in_venv, "-m", "pip", "--version"]
    pip_installed = run_command(pip_check_command, check=False)
    
    if pip_installed:
        print("pip is already installed in the VENV.")
    else:
        print("pip not found in VENV. Installing it manually with get-pip.py...")
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_script = "get-pip.py"
        
        if not run_command(["curl", "-sS", get_pip_url, "-o", get_pip_script]):
            print(f"FATAL: Failed to download {get_pip_script}. Cannot install pip.", file=sys.stderr)
            sys.exit(1)
            
        if not run_command([python_in_venv, get_pip_script]):
            print(f"FATAL: Failed to execute {get_pip_script} in the VENV. Cannot install pip.", file=sys.stderr)
            sys.exit(1)
            
        print("pip successfully installed in the VENV.")
        os.remove(get_pip_script)

def step_3_install_dependencies_in_venv(python_in_venv):
    print(f"\n--- Step 3: Installing Core Dependencies into VENV ({VENV_NAME}) ---")
    for dep in CORE_DEPENDENCIES:
        run_command([python_in_venv, "-m", "pip", "install", "--upgrade", dep])

def step_4_install_tunneling_clients():
    print("\n--- Step 4: Checking for Tunneling Clients ---")
    for client_name, info in TUNNELING_CLIENTS.items():
        print(f"Checking for {client_name}...")
        try:
            result = subprocess.run(info["check_command"], capture_output=True, text=True, shell=False)
            if result.returncode == 0:
                print(f"{client_name} is already installed.")
            else:
                raise FileNotFoundError
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(f"-> {client_name} not found or accessible in PATH. Instructions:")
            run_command(info["install_command"], shell=True)

def step_5_install_webuis(python_in_venv):
    print("\n--- Step 5: Installing All Supported WebUIs ---")
    for ui_name, setup_script_path in SUPPORTED_WEBUIS.items():
        print(f"\n-- Installing {ui_name} --")
        if not os.path.exists(setup_script_path):
            print(f"Warning: Setup script for {ui_name} not found at '{setup_script_path}'. Skipping.", file=sys.stderr)
            continue
        print(f"Running setup for {ui_name} using {python_in_venv}...")
        if not run_command([python_in_venv, setup_script_path], cwd=PROJECT_ROOT_DIR):
            print(f"Warning: Installation of {ui_name} may have encountered errors.", file=sys.stderr)
        else:
            print(f"-- Finished installation attempt for {ui_name} --")
    print("\nAll WebUI installation scripts have been executed.")

if __name__ == "__main__":
    versions = import_versions()
    step_0_display_welcome_and_versions(versions)
    
    step_0_ensure_venv_package()
    
    step_1_update_repo()
    
    python_in_venv = step_2_setup_virtual_environment()
    
    step_2b_install_pip_in_venv(python_in_venv)
    
    step_3_install_dependencies_in_venv(python_in_venv)
    
    step_4_install_tunneling_clients()
    
    step_5_install_webuis(python_in_venv)
    
    print("\n--- Pre-Flight Setup Complete ---")
    print("You should now be able to run Cell 2 of the AnxLight notebook to launch the Gradio UI.")