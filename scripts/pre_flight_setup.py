# scripts/pre_flight_setup.py
# v0.1.15: Fix shell redirection error by quoting dependency with '<' and '>'.
# v0.1.14: Fix SyntaxError on multiline string declaration.

import os
import sys
import subprocess
from pathlib import Path

print("--- AnxLight Pre-Flight Setup Script v0.1.15 ---")

# --- Environment Setup ---
# Get project root - handle both direct execution and exec()
try:
    # When run as a script
    PROJECT_ROOT = Path(__file__).parent.parent
except NameError:
    # When run via exec()
    PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', '/content/AnxLight'))

VENV_NAME = "anxlight_venv"
VENV_PATH = PROJECT_ROOT / VENV_NAME
VENV_PYTHON = VENV_PATH / "bin" / "python"
VENV_PIP = VENV_PATH / "bin" / "pip"
print(f"Project Root: {PROJECT_ROOT}")
print(f"Virtual Env Path: {VENV_PATH}")

# --- Utility to run commands ---
def run_command(command, cwd=None, check=True, capture_output=False, shell=True, env=None):
    print(f"\n$ {command}")
    # Using list of args for Popen is safer than a single string with shell=True
    # but for simplicity in this script, we'll stick to shell=True and be careful.
    process = subprocess.Popen(command, shell=shell, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
    process.wait()
    if check and process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command)
    return process

def log_to_unified(message: str, level: str = "INFO", test_name: str = None, force_display: bool = False):
    """Unified logging with Trinity integration"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [v{TRINITY_VERSION}] [{level}] [PRE-FLIGHT] {message}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    # Print based on level or force_display
    if force_display or level in ["ERROR", "SUCCESS", "WARNING"]:
        print(f"[{level}] {message}")
    else:
        print(f"[{level}] {message}")
    
    # Update test UI if test name provided
    if test_name:
        update_test_ui(test_name, level.lower(), message)

# --- Step 0: Install essential system packages (like aria2) ---
print("\n--- Ensuring essential system packages are installed (e.g., aria2) ---")
try:
    if os.geteuid() == 0:
        run_command("apt-get update -y")
        run_command("apt-get install -y aria2 curl unzip")
        print("System packages installed/updated.")
    else:
        print("WARNING: Not running as root. Skipping apt-get for system packages.")
except Exception as e:
    print(f"WARNING: Error during system package installation: {e}.")

# --- Step 1: Create Virtual Environment ---
if not VENV_PATH.exists():
    print(f"Creating virtual environment at {VENV_PATH}...")
    run_command(f'"{sys.executable}" -m venv --without-pip "{VENV_PATH}"')
    print(f"Installing pip into {VENV_PATH}...")
    run_command(f"curl -sS https://bootstrap.pypa.io/get-pip.py | \"{VENV_PYTHON}\"")
    print("Pip installed successfully in VENV.")
else:
    print("Virtual environment already exists.")
    print(f"Upgrading pip in existing VENV at {VENV_PATH}...")
    run_command(f'"{VENV_PYTHON}" -m pip install --upgrade pip')

# --- Step 2: Install Core Dependencies into VENV ---
print("\n--- Installing/Updating core dependencies with compatibility pins ---")
# CRITICAL FIX: Quote the packages with special shell characters
core_deps = [
    "gradio==4.44.1",
    "'pydantic>=2.9.0,<3.0.0'", # Quoted to prevent shell redirection
    "'fastapi>=0.104.0'",        # Quoted for consistency
    "'starlette>=0.27.0'",      # Quoted for consistency
    "huggingface-hub",
    "gdown",
    "nest_asyncio"
]
run_command(f'"{VENV_PIP}" install --upgrade {" ".join(core_deps)}')

# --- Step 3: Install WebUIs ---
print("\n--- Running WebUI Installers ---")
ui_scripts_path = PROJECT_ROOT / "scripts" / "UIs"
ui_scripts = [f for f in ui_scripts_path.glob("*.py") if f.is_file() and not f.name.startswith('_')]

for script in ui_scripts:
    print(f"--- Running UI installer: {script.name} ---")
    env_vars = os.environ.copy()
    env_vars["VENV_PYTHON_PATH"] = str(VENV_PYTHON)
    env_vars["VENV_PIP_PATH"] = str(VENV_PIP)
    result = run_command(f'"{VENV_PYTHON}" "{script}"', cwd=PROJECT_ROOT, check=False, env=env_vars)
    if result.returncode != 0:
        print(f"WARNING: Script {script.name} failed with return code {result.returncode}.", file=sys.stderr)

# --- Step 4: Environment Compatibility Check ---
print("\n--- Verifying Environment Compatibility ---")
check_script_content = """
import pkg_resources
import sys

required_versions = {
    'gradio': '==4.44.1',
    'pydantic': '>=2.9.0,<3.0.0',
    'fastapi': '>=0.104.0',
    'starlette': '>=0.27.0'
}
mismatches = 0
print('--- Checking package versions ---')
for package, version_req_str in required_versions.items():
    try:
        installed_version_str = pkg_resources.get_distribution(package).version
        req = pkg_resources.Requirement.parse(f'{package}{version_req_str}')
        if pkg_resources.parse_version(installed_version_str) not in req:
            print(f'[MISMATCH] {package}: Found {installed_version_str}, requires {version_req_str}')
            mismatches += 1
        else:
            print(f'[OK] {package}: Found {installed_version_str}, meets {version_req_str}')
    except pkg_resources.DistributionNotFound:
        print(f'[ERROR] {package}: NOT INSTALLED')
        mismatches += 1

if mismatches > 0:
    print(f'\\nFound {mismatches} package version mismatches. Errors may occur.')
else:
    print('\\nAll checked packages meet version requirements.')

print('\\n--- Running pip check for dependency conflicts ---')
"""
check_script_path = PROJECT_ROOT / "temp_check_script.py"
check_script_path.write_text(check_script_content)
run_command(f'"{VENV_PYTHON}" "{check_script_path}"')
os.remove(check_script_path)

# Final pip check for overall health
run_command(f'"{VENV_PIP}" check', check=False)

print("\n--- Pre-Flight Setup Finished ---")