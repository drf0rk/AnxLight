# ~ ComfyUI.py | by ANXETY ~
# Refactored by SuperAssistant for standard Python execution

import sys
from pathlib import Path
import subprocess
import asyncio
import os

project_root = Path(__file__).parent.parent.parent
scripts_dir = project_root / "scripts"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from modules.Manager import m_download
import modules.json_utils as js

osENV = os.environ
CD = os.chdir

# Constants
UI = 'ComfyUI'

PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME = PATHS.get('home_path', Path.cwd())
VENV = PATHS.get('venv_path', Path.cwd() / 'anxlight_venv')
SETTINGS_PATH = PATHS.get('settings_path', Path.cwd() / 'config/settings.json')

WEBUI = HOME / UI
CUSTOM_NODES_PATH = WEBUI / 'custom_nodes'
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name') if SETTINGS_PATH.exists() else 'Colab'
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork') if SETTINGS_PATH.exists() else 'anxety-solo/sd-webui'
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch') if SETTINGS_PATH.exists() else 'main'
REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"

if HOME.exists():
    CD(HOME)

# ==================== WEBUI OPERATIONS ====================

async def _download_file(url, directory, filename):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / filename
    if file_path.exists():
        file_path.unlink()
    process = await asyncio.create_subprocess_shell(
        f"curl -sLo \"{file_path}\" \"{url}\"",
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        print(f"Error downloading {url}. curl stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)

async def download_files(file_list):
    tasks = []
    for file_info in file_list:
        parts = file_info.split(',')
        url = parts[0].strip()
        directory = Path(parts[1].strip()) if len(parts) > 1 else WEBUI
        filename = parts[2].strip() if len(parts) > 2 else Path(url).name
        tasks.append(_download_file(url, directory, filename))
    await asyncio.gather(*tasks)

async def download_configuration():
    print(f"--- [{UI}.py] Downloading configuration files and custom nodes ---")
    ## FILES
    url_cfg = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    files_to_download = [
        f"{url_cfg}/{UI}/install-deps.py,{WEBUI}",
        f"{url_cfg}/{UI}/comfy.settings.json,{WEBUI}/user/default",
        f"{url_cfg}/{UI}/Comfy-Manager/config.ini,{WEBUI}/user/default/ComfyUI-Manager",
        f"{url_cfg}/{UI}/workflows/anxety-workflow.json,{WEBUI}/user/default/workflows",
        f"{url_cfg}/gradio-tunneling.py,{VENV}/lib/python3.10/site-packages/gradio_tunneling,main.py"
    ]
    await download_files(files_to_download)

    ## REPOS (Custom Nodes for ComfyUI)
    extensions_list = [
        'https://github.com/Fannovel16/comfyui_controlnet_aux',
        'https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet',
        'https://github.com/hayden-fr/ComfyUI-Model-Manager',
        'https://github.com/jags111/efficiency-nodes-comfyui',
        'https://github.com/ltdrdata/ComfyUI-Impact-Pack',
        'https://github.com/ltdrdata/ComfyUI-Impact-Subpack',
        'https://github.com/ltdrdata/ComfyUI-Manager',
        'https://github.com/pythongosssss/ComfyUI-Custom-Scripts',
        'https://github.com/pythongosssss/ComfyUI-WD14-Tagger',
        'https://github.com/ssitu/ComfyUI_UltimateSDUpscale',
        'https://github.com/WASasquatch/was-node-suite-comfyui'
    ]
    if ENV_NAME == 'Kaggle':
        extensions_list.append('https://github.com/gutris1/sd-encrypt-image Encrypt-Image')

    CUSTOM_NODES_PATH.mkdir(parents=True, exist_ok=True)
    original_cwd = Path.cwd()
    try:
        CD(CUSTOM_NODES_PATH)
        print(f"--- [{UI}.py] Cloning custom nodes into {CUSTOM_NODES_PATH} ---")
        
        procs = []
        for command in extensions_list:
            repo_name = command.split('/')[-1].split()[0].replace('.git', '')
            if len(command.split()) > 1:
                repo_name = command.split()[-1]
            
            if (CUSTOM_NODES_PATH / repo_name).exists():
                print(f"Custom node '{repo_name}' already exists. Skipping clone.")
                continue

            # Correctly await the creation of the process
            process = await asyncio.create_subprocess_shell(
                f"git clone --depth 1 {command}",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            procs.append(process)

        # Now procs contains Process objects, so we can gather their results
        results = await asyncio.gather(*[p.communicate() for p in procs])

        # Check results after they are all gathered
        for i, (stdout, stderr) in enumerate(results):
            if procs[i].returncode != 0:
                print(f"Error cloning custom node. Git stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)

    finally:
        CD(original_cwd)

def unpack_webui():
    zip_path = HOME / f"{UI}.zip"
    print(f"--- [{UI}.py] Step 1: Downloading WebUI from {REPO_URL} ---")
    m_download(f"{REPO_URL} {str(HOME)} {UI}.zip", log=True)
    
    print(f"--- [{UI}.py] Step 2: Unzipping {zip_path} to {WEBUI} ---")
    WEBUI.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["unzip", "-q", "-o", str(zip_path), "-d", str(WEBUI)], check=True)
    except Exception as e:
        print(f"--- [{UI}.py] ERROR during unzip: {e} ---", file=sys.stderr)
        sys.exit(1)

    print(f"--- [{UI}.py] Step 3: Removing {zip_path} ---")
    try:
        subprocess.run(["rm", "-rf", str(zip_path)], check=True)
    except Exception as e:
        print(f"--- [{UI}.py] WARNING during zip removal: {e} ---", file=sys.stderr)

    install_deps_script = WEBUI / "install-deps.py"
    if install_deps_script.exists():
        print(f"--- [{UI}.py] Step 4: Running {install_deps_script} ---")
        python_executable = VENV / "bin" / "python"
        if not python_executable.exists():
             python_executable = sys.executable

        original_cwd = Path.cwd()
        try:
            CD(WEBUI)
            process = subprocess.run([str(python_executable), str(install_deps_script)], capture_output=True, text=True, check=False)
            if process.returncode == 0:
                print(f"--- [{UI}.py] {install_deps_script} executed successfully ---")
                if process.stdout: print(f"Output:\n{process.stdout}")
            else:
                print(f"--- [{UI}.py] ERROR running {install_deps_script} ---", file=sys.stderr)
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
    print(f"--- AnxLight {UI} UI Installer Script ---")
    unpack_webui()
    print(f"--- [{UI}.py] Unpack finished, proceeding to download configuration & custom nodes ---")
    asyncio.run(download_configuration())
    print(f"--- [{UI}.py] Script finished ---")