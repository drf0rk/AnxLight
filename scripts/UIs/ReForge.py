# ~ ReForge.py | by ANXETY ~
# Refactored by SuperAssistant for standard Python execution
# Note: Panchovix/stable-diffusion-webui-reForge development has reportedly stopped.

import sys
from pathlib import Path
import subprocess
import asyncio
import os

# This block ensures that modules from the 'scripts' and 'modules' directories can be imported
try:
    project_root = Path(__file__).parent.parent.parent
    scripts_dir = project_root / "scripts"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    
    from modules.Manager import m_download   # Every Download
    import modules.json_utils as js          # JSON
except ImportError as e:
    print(f"Error importing required modules: {e}", file=sys.stderr)
    # Define dummy functions if imports fail to prevent NameError
    def m_download(*args, **kwargs):
        print("Error: m_download from Manager not available.", file=sys.stderr)
    class DummyJson:
        def read(self, *args):
            print(f"Warning: json_utils.read not available. Returning default for {args[1]}", file=sys.stderr)
            if args[1] == 'ENVIRONMENT.env_name': return 'Colab'
            if args[1] == 'ENVIRONMENT.fork': return 'anxety-solo/sd-webui'
            if args[1] == 'ENVIRONMENT.branch': return 'main'
            return None
    js = DummyJson()


osENV = os.environ
CD = os.chdir

# Constants
UI = 'ReForge'

# (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME = PATHS.get('home_path', Path.cwd())
VENV = PATHS.get('venv_path', Path.cwd() / 'anxlight_venv')
SETTINGS_PATH = PATHS.get('settings_path', Path.cwd() / 'config/settings.json')

WEBUI = HOME / UI
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')

REFORGE_GIT_REPO_URL = "https://github.com/Panchovix/stable-diffusion-webui-reForge.git"
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')
REFORGE_EXTENSIONS_PATH = WEBUI / 'extensions'

if HOME.exists():
    CD(HOME)


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
        f"curl -sLo \"{file_path}\" \"{url}\"",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        print(f"Error downloading {url} to {file_path}. curl stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)

async def download_files(file_list):
    tasks = []
    for file_info in file_list:
        parts = file_info.split(',')
        url = parts[0].strip()
        directory_str = parts[1].strip() if len(parts) > 1 else str(WEBUI)
        filename = parts[2].strip() if len(parts) > 2 else Path(url).name
        tasks.append(_download_file(url, Path(directory_str), filename))
    await asyncio.gather(*tasks)

async def download_configuration():
    print(f"--- [{UI}.py] Downloading configuration files and extensions (review for ReForge compatibility) ---")
    ## FILES
    url_cfg = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    configs_to_download = [
        f"{url_cfg}/styles.csv,{WEBUI}",
        f"{url_cfg}/user.css,{WEBUI}",
        f"{url_cfg}/card-no-preview.png,{WEBUI}/html",
        f"{url_cfg}/notification.mp3,{WEBUI}",
        f"{url_cfg}/gradio-tunneling.py,{VENV}/lib/python3.10/site-packages/gradio_tunneling,main.py"
    ]
    await download_files(configs_to_download)

    ## REPOS (Extensions)
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
        tasks = []
        for command_str in extensions_list:
            process = await asyncio.create_subprocess_shell(
                f"git clone --depth 1 {command_str}",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            tasks.append(process)

        for i, process in enumerate(tasks):
            _, stderr = await process.communicate()
            if process.returncode != 0:
                print(f"Error cloning extension: {extensions_list[i]}. Git stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)
            else:
                print(f"Successfully cloned: {extensions_list[i]}")
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
    print(f"--- AnxLight {UI} UI Script (Note: {UI} development by Panchovix reportedly stopped) ---")
    
    unpack_webui()
    print(f"--- [{UI}.py] ReForge repository clone process finished. ---")
    asyncio.run(download_configuration())
    print(f"--- [{UI}.py] Script finished ---")