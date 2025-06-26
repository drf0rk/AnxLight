# ~ ReForge.py | by ANXETY ~
# Refactored by SuperAssistant for standard Python execution
# Note: Panchovix/stable-diffusion-webui-reForge development has reportedly stopped.

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
UI = 'ReForge'

PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME = PATHS.get('home_path', Path.cwd())
VENV = PATHS.get('venv_path', Path.cwd() / 'anxlight_venv')
SETTINGS_PATH = PATHS.get('settings_path', Path.cwd() / 'config/settings.json')

WEBUI = HOME / UI
REFORGE_EXTENSIONS_PATH = WEBUI / 'extensions'
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name') if SETTINGS_PATH.exists() else 'Colab'
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork') if SETTINGS_PATH.exists() else 'anxety-solo/sd-webui'
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch') if SETTINGS_PATH.exists() else 'main'
REFORGE_GIT_REPO_URL = "https://github.com/Panchovix/stable-diffusion-webui-reForge.git"

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
    print(f"--- [{UI}.py] Downloading configuration files and extensions (review for ReForge compatibility) ---")
    url_cfg = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    configs_to_download = [
        f"{url_cfg}/styles.csv,{WEBUI}",
        f"{url_cfg}/user.css,{WEBUI}",
        f"{url_cfg}/card-no-preview.png,{WEBUI}/html",
        f"{url_cfg}/notification.mp3,{WEBUI}",
        f"{url_cfg}/gradio-tunneling.py,{VENV}/lib/python3.10/site-packages/gradio_tunneling,main.py"
    ]
    await download_files(configs_to_download)

    extensions_list = [
        'https://github.com/anxety-solo/webui_timer timer',
        'https://github.com/anxety-solo/anxety-theme',
        'https://github.com/anxety-solo/sd-civitai-browser-plus Civitai-Browser-Plus',
        'https://github.com/gutris1/sd-image-viewer Image-Viewer',
        'https://github.com/gutris1/sd-image-info Image-Info',
        'https://github.com/gutris1/sd-hub SD-Hub',
        'https://github.com/hako-mikan/sd-webui-regional-prompter Regional-Prompter',
    ]
    if ENV_NAME == 'Kaggle':
        extensions_list.append('https://github.com/anxety-solo/sd-encrypt-image Encrypt-Image')

    REFORGE_EXTENSIONS_PATH.mkdir(parents=True, exist_ok=True)
    original_cwd = Path.cwd()
    try:
        CD(REFORGE_EXTENSIONS_PATH)
        print(f"--- [{UI}.py] Cloning extensions into {REFORGE_EXTENSIONS_PATH} (review for ReForge compatibility) ---")
        procs = []
        for command in extensions_list:
            repo_name = command.split('/')[-1].split()[0].replace('.git', '')
            if len(command.split()) > 1:
                repo_name = command.split()[-1]
            
            if (REFORGE_EXTENSIONS_PATH / repo_name).exists():
                print(f"Extension '{repo_name}' already exists. Skipping clone.")
                continue

            process = await asyncio.create_subprocess_shell(
                f"git clone --depth 1 {command}",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            procs.append(process)

        results = await asyncio.gather(*[p.communicate() for p in procs])

        for i, (stdout, stderr) in enumerate(results):
            if procs[i].returncode != 0:
                print(f"Error cloning extension. Git stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)
    finally:
        CD(original_cwd)

def unpack_webui():
    print(f"--- [{UI}.py] Step 1: Cloning WebUI from {REFORGE_GIT_REPO_URL} into {WEBUI} ---")
    if WEBUI.exists():
        print(f"--- [{UI}.py] Directory {WEBUI} already exists. Assuming ReForge is already cloned. ---")
    else:
        try:
            subprocess.run(["git", "clone", REFORGE_GIT_REPO_URL, str(WEBUI)], check=True)
            print(f"--- [{UI}.py] ReForge cloned successfully. Checking out main branch... ---")
            subprocess.run(["git", "checkout", "main"], cwd=str(WEBUI), check=True)
        except Exception as e:
            print(f"--- [{UI}.py] ERROR during git operation for ReForge: {e} ---", file=sys.stderr)
            sys.exit(1)
    
    print(f"--- [{UI}.py] ReForge repository cloned. Further setup handled by its first launch. ---")

# ======================== MAIN CODE =======================
if __name__ == '__main__':
    print(f"--- AnxLight {UI} UI Installer Script (Note: {UI} development by Panchovix reportedly stopped) ---")
    
    unpack_webui()
    print(f"--- [{UI}.py] ReForge repository clone process finished. ---")
    asyncio.run(download_configuration())
    print(f"--- [{UI}.py] Script finished ---")