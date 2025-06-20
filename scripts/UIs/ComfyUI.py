# ~ ComfyUI.py | by ANXETY ~
# Refactored by SuperAssistant for standard Python execution

from Manager import m_download   # Every Download
import json_utils as js          # JSON

from pathlib import Path
import subprocess
import asyncio
import os
import sys # Ensure sys is imported

osENV = os.environ
CD = os.chdir

# Constants
UI = 'ComfyUI'

# (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
VENV = PATHS['venv_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

WEBUI = HOME / UI
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')

REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')
# EXTS for ComfyUI usually refers to its 'custom_nodes' directory.
# The original script used SETTINGS_PATH, 'WEBUI.extension_dir' which might be generic.
# For ComfyUI, custom nodes are typically cloned into WEBUI / 'custom_nodes'.
# This will be handled by changing CWD to WEBUI / 'custom_nodes' before cloning.
CUSTOM_NODES_PATH = WEBUI / 'custom_nodes'


CD(HOME) # Initial CWD set to HOME


# ==================== WEBUI OPERATIONS ====================

async def _download_file(url, directory, filename):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / filename

    if file_path.exists():
        try:
            file_path.unlink()
        except OSError as e:
            print(f"Warning: Could not delete existing file {file_path}. Error: {e}", file=sys.stderr)

    process = await asyncio.create_subprocess_shell(
        f"curl -sLo \"{file_path}\" \"{url}\"", # Added quotes
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        print(f"Error downloading {url} to {file_path}. curl stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)

async def download_files(file_list):
    tasks = []
    for file_info in file_list:
        parts = file_info.split(',')
        url = parts[0].strip()
        directory_str = parts[1].strip() if len(parts) > 1 else str(WEBUI) # Default to WEBUI for general files
        filename = parts[2].strip() if len(parts) > 2 else Path(url).name
        
        # Specific handling for ComfyUI settings to ensure they go to user/default
        if "comfy.settings.json" in filename or "Comfy-Manager/config.ini" in filename or "anxety-workflow.json" in filename:
             # The paths in `files` list already specify subdirectories like WEBUI/user/default
             # So, directory_str from parts[1] should be used directly if provided.
             pass # directory_str is already set correctly from file_info

        tasks.append(_download_file(url, Path(directory_str), filename))
    await asyncio.gather(*tasks)

async def download_configuration():
    print(f"--- [{UI}.py] Downloading configuration files and custom nodes ---")
    ## FILES
    url_cfg = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    files_to_download = [ # Renamed 'files' to 'files_to_download' to avoid conflict
        # settings
        f"{url_cfg}/{UI}/install-deps.py,{WEBUI}", # Download install-deps.py to WEBUI root
        f"{url_cfg}/{UI}/comfy.settings.json,{WEBUI}/user/default",
        f"{url_cfg}/{UI}/Comfy-Manager/config.ini,{WEBUI}/user/default/ComfyUI-Manager",
        # workflows
        f"{url_cfg}/{UI}/workflows/anxety-workflow.json,{WEBUI}/user/default/workflows",
        # other | tunneling
        # Ensure VENV path and python version for site-packages is correct
        f"{url_cfg}/gradio-tunneling.py,{VENV}/lib/python3.10/site-packages/gradio_tunneling,main.py"
    ]
    await download_files(files_to_download)

    ## REPOS (Custom Nodes for ComfyUI)
    extensions_list = [
        'https://github.com/Fannovel16/comfyui_controlnet_aux',
        'https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet',
        'https://github.com/hayden-fr/ComfyUI-Model-Manager', # This is a standalone tool, not a typical custom node, but often used alongside.
                                                             # If it's a custom node, it belongs in custom_nodes. If a tool, installation might differ.
                                                             # Assuming it's a custom node for now based on context.
        'https://github.com/jags111/efficiency-nodes-comfyui',
        'https://github.com/ltdrdata/ComfyUI-Impact-Pack',
        'https://github.com/ltdrdata/ComfyUI-Impact-Subpack', # This might need Impact-Pack first. Order matters.
        'https://github.com/ltdrdata/ComfyUI-Manager',
        'https://github.com/pythongosssss/ComfyUI-Custom-Scripts',
        'https://github.com/pythongosssss/ComfyUI-WD14-Tagger',
        'https://github.com/ssitu/ComfyUI_UltimateSDUpscale',
        'https://github.com/WASasquatch/was-node-suite-comfyui'
    ]
    if ENV_NAME == 'Kaggle': # This extension might not be a custom node. Clarify its nature.
        extensions_list.append('https://github.com/gutris1/sd-encrypt-image Encrypt-Image')


    CUSTOM_NODES_PATH.mkdir(parents=True, exist_ok=True)
    original_cwd = Path.cwd()
    try:
        CD(CUSTOM_NODES_PATH) # Change to custom_nodes directory for git clones
        print(f"--- [{UI}.py] Cloning custom nodes into {CUSTOM_NODES_PATH} ---")
        
        tasks = []
        for repo_url_with_optional_name in extensions_list:
            parts = repo_url_with_optional_name.split()
            repo_url = parts[0]
            # Constructing git clone command: git clone --depth 1 <repo_url> [optional_local_name]
            git_command_str = f"git clone --depth 1 {repo_url_with_optional_name}"

            process = await asyncio.create_subprocess_shell(
                git_command_str,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            tasks.append(process)

        for i, process in enumerate(tasks):
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                print(f"Error cloning custom node: {extensions_list[i]}. Git stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)
            else:
                print(f"Successfully cloned: {extensions_list[i]}")

    finally:
        CD(original_cwd) # Restore original CWD

def unpack_webui():
    zip_path = HOME / f"{UI}.zip"
    print(f"--- [{UI}.py] Step 1: Downloading WebUI from {REPO_URL} ---")
    m_download(f"{REPO_URL} {HOME} {UI}.zip")
    
    print(f"--- [{UI}.py] Step 2: Unzipping {zip_path} to {WEBUI} ---")
    WEBUI.mkdir(parents=True, exist_ok=True) # Ensure WEBUI directory exists before unzipping
    try:
        subprocess.run(["unzip", "-q", "-o", str(zip_path), "-d", str(WEBUI)], check=True, capture_output=True, text=True)
        print(f"--- [{UI}.py] Unzip successful ---")
    except subprocess.CalledProcessError as e:
        print(f"--- [{UI}.py] ERROR during unzip ---", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        print(f"STDERR: {e.stderr}", file=sys.stderr)
        sys.exit(f"Critical error during unzip of {UI}.zip. Exiting.")
    except FileNotFoundError:
        print(f"--- [{UI}.py] ERROR: unzip command not found. Please ensure unzip is installed and in PATH.", file=sys.stderr)
        sys.exit(f"Critical error: unzip command not found for {UI}.zip. Exiting.")

    print(f"--- [{UI}.py] Step 3: Removing {zip_path} ---")
    try:
        subprocess.run(["rm", "-rf", str(zip_path)], check=True)
        print(f"--- [{UI}.py] Zip removal successful ---")
    except subprocess.CalledProcessError as e:
        print(f"--- [{UI}.py] WARNING during zip removal of {UI}.zip ---", file=sys.stderr)
        print(f"STDERR: {e.stderr if e.stderr else 'No specific stderr from rm.'}", file=sys.stderr)
    except FileNotFoundError:
        print(f"--- [{UI}.py] WARNING: rm command not found. Could not remove {zip_path}.", file=sys.stderr)

    # After unzipping ComfyUI, run its install-deps.py if it exists
    install_deps_script = WEBUI / "install-deps.py"
    if install_deps_script.exists():
        print(f"--- [{UI}.py] Step 4: Running {install_deps_script} ---")
        python_executable = VENV / "bin" / "python" # Assuming python in VENV bin
        if not python_executable.exists():
             python_executable = sys.executable # Fallback to current interpreter if VENV python not found

        original_cwd = Path.cwd()
        try:
            CD(WEBUI) # Run install-deps.py from within ComfyUI directory
            process = subprocess.run([str(python_executable), str(install_deps_script)], capture_output=True, text=True, check=False) # check=False to inspect output
            if process.returncode == 0:
                print(f"--- [{UI}.py] {install_deps_script} executed successfully ---")
                if process.stdout: print(f"Output:\n{process.stdout}")
            else:
                print(f"--- [{UI}.py] ERROR running {install_deps_script} ---", file=sys.stderr)
                print(f"Return Code: {process.returncode}", file=sys.stderr)
                if process.stdout: print(f"STDOUT:\n{process.stdout}", file=sys.stderr)
                if process.stderr: print(f"STDERR:\n{process.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"--- [{UI}.py] Exception running {install_deps_script}: {e} ---", file=sys.stderr)
        finally:
            CD(original_cwd)
    else:
        print(f"--- [{UI}.py] {install_deps_script} not found, skipping execution. ---")


# ======================== MAIN CODE =======================
if __name__ == '__main__':
    print(f"--- AnxLight {UI} UI Script ---")
    
    unpack_webui()
    print(f"--- [{UI}.py] Unpack finished, proceeding to download configuration & custom nodes ---")
    asyncio.run(download_configuration())
    print(f"--- [{UI}.py] Script finished ---")