# scripts/pre_flight_setup.py
# v0.1.14: Fix SyntaxError on multiline string declaration.
# v0.1.13: Explicitly pin Pydantic, FastAPI, and Starlette versions for compatibility. Add verification step.

import os
import sys
import subprocess
from pathlib import Path

print("--- AnxLight Pre-Flight Setup Script v0.1.14 ---")

# --- Environment Setup ---
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
    if not capture_output:
        process = subprocess.Popen(command, shell=shell, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
        process.wait()
        if check and process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
        return process
    else:
        return subprocess.run(command, shell=shell, check=check, cwd=cwd, capture_output=True, text=True, env=env)

# --- Step 0: Install essential system packages (like aria2) ---
print("\n--- Ensuring essential system packages are installed (e.g., aria2) ---")
try:
    if os.geteuid() == 0:
        run_command("apt-get update -y")
        run_command("apt-get install -y aria2 curl unzip")
        print("System packages installed/updated.")
    else:
        print("WARNING: Not running as root. Skipping apt-get for system packages. aria2 might be missing.")
except Exception as e:
    print(f"WARNING: Error during system package installation: {e}. Continuing, but some features might fail.")

# --- Step 1: Create Virtual Environment ---
if not VENV_PATH.exists():
    print(f"Creating virtual environment at {VENV_PATH} (without pip initially)...")
    run_command(f'"{sys.executable}" -m venv --without-pip "{VENV_PATH}"')
    print(f"Installing pip into {VENV_PATH}...")
    run_command(f"curl -sS https://bootstrap.pypa.io/get-pip.py -o \"{PROJECT_ROOT / 'get-pip.py'}\"")
    run_command(f'"{VENV_PYTHON}" "{PROJECT_ROOT / "get-pip.py"}"')
    os.remove(PROJECT_ROOT / 'get-pip.py')
    print("Pip installed successfully in VENV.")
else:
    print("Virtual environment already exists.")
    print(f"Upgrading pip in existing VENV at {VENV_PATH}...")
    run_command(f'"{VENV_PYTHON}" -m pip install --upgrade pip')

# --- Step 2: Install Core Dependencies into VENV ---
print("\n--- Installing/Updating core dependencies with compatibility pins ---")
core_deps = [
    "gradio==4.44.1",
    "pydantic>=2.9.0,<3.0.0",
    "fastapi>=0.104.0",
    "starlette>=0.27.0",
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
    'gradio': '4.44.1',
    'pydantic': '>=2.9.0',
    'fastapi': '>=0.104.0',
    'starlette': '>=0.27.0'
}
mismatches = 0
print('--- Checking package versions ---')
for package, version_req in required_versions.items():
    try:
        installed_version = pkg_resources.get_distribution(package).version
        req = pkg_resources.Requirement.parse(f'{package}{version_req}')
        if installed_version not in req:
            print(f'[MISMATCH] {package}: Found {installed_version}, requires {version_req}')
            mismatches += 1
        else:
            print(f'[OK] {package}: Found {installed_version}, meets {version_req}')
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