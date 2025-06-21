# ~ SD-UX.py | by ANXETY ~
# Refactored by SuperAssistant for standard Python execution
# Note: The exact nature and preferred installation method of "SD-UX" should be verified.
# This script currently assumes installation from the ANXETY HF REPO_URL (zip file).
# If SD-UX refers to Stability-AI/StableStudio, a different (Node.js based) installation is required.

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
UI = 'SD-UX'

# (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME = PATHS.get('home_path', Path.cwd())
VENV = PATHS.get('venv_path', Path.cwd() / 'anxlight_venv')
SETTINGS_PATH = PATHS.get('settings_path', Path.cwd() / 'config/settings.json')

WEBUI = HOME / UI
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')

REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')
EXTS_PATH = WEBUI / 'extensions'

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
    print(f"--- [{UI}.py] Downloading generic configuration files (review for SD-UX compatibility) ---")
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
    print(f"--- [{UI}.py] Generic extension download step skipped/placeholder for SD-UX. Needs verification. ---")


def unpack_webui():
    zip_path = HOME / f"{UI}.zip"
    print(f"--- [{UI}.py] Step 1: Downloading WebUI from {REPO_URL} (assuming zip archive) ---")
    m_download(f"\"{REPO_URL}\"", str(HOME), f"{UI}.zip")
    
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
    
    print(f"--- [{UI}.py] Basic unzip complete. If this is Stability-AI/StableStudio, further Node.js/Yarn setup is needed. ---")


# ======================== MAIN CODE =======================
if __name__ == '__main__':
    print(f"--- AnxLight {UI} UI Script ---")
    print(f"--- Note: Installation method and nature of '{UI}' needs verification. ---")
    
    unpack_webui()
    print(f"--- [{UI}.py] Unpack process finished. ---")
    asyncio.run(download_configuration())
    print(f"--- [{UI}.py] Script finished ---")