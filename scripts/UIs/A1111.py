# ~ A1111.py | by ANXETY ~
# Refactored by SuperAssistant

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

from modules.Manager import download_url_to_path
import modules.json_utils as js

osENV = os.environ
CD = os.chdir

# Constants
UI = 'A1111'

PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME = PATHS.get('home_path', Path.cwd())
VENV = PATHS.get('venv_path', Path.cwd() / 'anxlight_venv')
SETTINGS_PATH = PATHS.get('settings_path', Path.cwd() / 'config/settings.json')

WEBUI = HOME / UI
EXTS = WEBUI / 'extensions'
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
    ## FILES
    url_cfg = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    configs = [
        f"{url_cfg}/styles.csv,{WEBUI}",
        f"{url_cfg}/user.css,{WEBUI}",
        f"{url_cfg}/card-no-preview.png,{WEBUI}/html",
        f"{url_cfg}/notification.mp3,{WEBUI}",
        f"{url_cfg}/gradio-tunneling.py,{VENV}/lib/python3.10/site-packages/gradio_tunneling,main.py"
    ]
    await download_files(configs)

    ## REPOS
    extensions_list = [
        'https://github.com/anxety-solo/webui_timer timer',
        'https://github.com/anxety-solo/anxety-theme',
        'https://github.com/anxety-solo/sd-civitai-browser-plus Civitai-Browser-Plus',
        'https://github.com/gutris1/sd-image-viewer Image-Viewer',
        'https://github.com/gutris1/sd-image-info Image-Info',
        'https://github.com/gutris1/sd-hub SD-Hub',
        'https://github.com/Bing-su/adetailer',
        'https://github.com/Haoming02/sd-forge-couple SD-Couple',
        'https://github.com/hako-mikan/sd-webui-regional-prompter Regional-Prompter',
    ]
    if ENV_NAME == 'Kaggle':
        extensions_list.append('https://github.com/anxety-solo/sd-encrypt-image Encrypt-Image')

    EXTS.mkdir(parents=True, exist_ok=True)
    original_cwd = Path.cwd()
    print(f"--- [{UI}.py] Cloning extensions into {EXTS} ---")
    try:
        CD(EXTS)
        for command_str in extensions_list:
            parts = command_str.split()
            repo_url = parts[0]
            repo_name_git = repo_url.split('/')[-1]
            if repo_name_git.endswith('.git'):
                repo_name_git = repo_name_git[:-4]
            repo_name = parts[1] if len(parts) > 1 else repo_name_git
            
            if (EXTS / repo_name).exists():
                print(f"Extension '{repo_name}' already exists. Skipping clone.")
                continue

            print(f"--- [{UI}.py] Cloning '{repo_name}' from {repo_url} ---")
            process = await asyncio.create_subprocess_shell(
                f"git clone --depth 1 {repo_url} {repo_name}",
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout_bytes, stderr_bytes = await process.communicate()
            
            if process.returncode != 0:
                stderr_str = stderr_bytes.decode().strip() if stderr_bytes else 'No stderr'
                print(f"Error cloning extension '{repo_name}'. Exit code: {process.returncode}. Git stderr: {stderr_str}", file=sys.stderr)
                if stdout_bytes and stdout_bytes.decode().strip():
                     print(f"   Git stdout: {stdout_bytes.decode().strip()}", file=sys.stderr)
            else:
                print(f"--- [{UI}.py] Successfully cloned '{repo_name}' ---")
    except Exception as e:
        print(f"An unexpected error occurred during extension cloning: {e}", file=sys.stderr)
    finally:
        CD(original_cwd)

def unpack_webui():
    zip_path = HOME / f"{UI}.zip"
    print(f"--- [A1111.py] Step 1: Downloading WebUI from {REPO_URL} ---")
    download_successful = download_url_to_path(url=REPO_URL, target_full_path=str(zip_path), log=True)
    
    if not download_successful:
        print(f"--- [A1111.py] ERROR: Download failed for {REPO_URL}. Cannot proceed with A1111 setup. ---", file=sys.stderr)
        sys.exit(1) 

    print(f"--- [A1111.py] Step 2: Unzipping {zip_path} to {WEBUI} ---")
    try:
        subprocess.run(["unzip", "-q", "-o", str(zip_path), "-d", str(WEBUI)], check=True)
    except Exception as e:
        print(f"--- [A1111.py] ERROR during unzip: {e} ---", file=sys.stderr)
        sys.exit(1)

    print(f"--- [A1111.py] Step 3: Removing {zip_path} ---")
    try:
        subprocess.run(["rm", "-rf", str(zip_path)], check=True)
    except Exception as e:
        print(f"--- [A1111.py] WARNING during zip removal: {e} ---", file=sys.stderr)

# ======================== MAIN CODE =======================
if __name__ == '__main__':
    print(f"--- AnxLight {UI} UI Installer Script ---")
    unpack_webui()
    print("--- [A1111.py] Unpack finished, proceeding to download configuration ---")
    asyncio.run(download_configuration())
    print("--- [A1111.py] Script finished ---")