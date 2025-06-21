# ~ Classic.py | by ANXETY ~
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
UI = 'Classic'

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
        f"{url_cfg}/{UI}/config.json",
        f"{url_cfg}/{UI}/ui-config.json",
        f"{url_cfg}/styles.csv",
        f"{url_cfg}/user.css",
        f"{url_cfg}/notification.mp3",
        f"{url_cfg}/gradio-tunneling.py,{VENV}/lib/python3.11/site-packages/gradio_tunneling,main.py"
    ]
    await download_files(configs)

    ## REPOS
    extensions_list = [
        'https://github.com/anxety-solo/webui_timer timer',
        'https://github.com/anxety-solo/anxety-theme',
        'https://github.com/anxety-solo/sd-civitai-browser-plus Civitai-Browser-Plus',
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
    try:
        CD(EXTS)
        tasks = []
        for command in extensions_list:
            repo_name = command.split('/')[-1].split()[0].replace('.git', '')
            if len(command.split()) > 1:
                repo_name = command.split()[-1]
            
            if (EXTS / repo_name).exists():
                print(f"Extension '{repo_name}' already exists. Skipping clone.")
                continue
            
            # Correctly await the creation of the process
            process = await asyncio.create_subprocess_shell(
                f"git clone --depth 1 {command}",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            tasks.append(process)

        # Now tasks contains Process objects, so we can gather their results
        results = await asyncio.gather(*[p.communicate() for p in tasks])

        # Check results after they are all gathered
        for i, (stdout, stderr) in enumerate(results):
            if tasks[i].returncode != 0:
                # Find the original command string for the failed process
                # This is a bit tricky as we skipped some. A safer way is to build a parallel list of commands.
                # For now, this will do, but it's not perfectly robust if some are skipped.
                print(f"Error cloning extension. Git stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)

    finally:
        CD(original_cwd)

def unpack_webui():
    zip_path = HOME / f"{UI}.zip"
    print(f"--- [{UI}.py] Step 1: Downloading WebUI from {REPO_URL} ---")
    # Correctly format the line for m_download
    m_download(f"{REPO_URL} {str(HOME)} {UI}.zip", log=True)
    
    print(f"--- [{UI}.py] Step 2: Unzipping {zip_path} to {WEBUI} ---")
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

def fixes_modules():
    cmd_args_path = WEBUI / "modules/cmd_args.py"
    if not cmd_args_path.exists():
        print(f"--- [{UI}.py] {cmd_args_path} not found, skipping fixes_modules. ---")
        return

    marker = '# Arguments added by ANXETY'
    try:
        content = cmd_args_path.read_text(encoding='utf-8')
        if marker in content:
            print(f"--- [{UI}.py] Marker already in {cmd_args_path}, skipping fixes_modules. ---")
            return

        with cmd_args_path.open('a', encoding='utf-8') as f:
            f.write(f"\n\n{marker}\n")
            f.write('parser.add_argument(\"--hypernetwork-dir\", type=normalized_filepath, '\
                   'default=os.path.join(models_path, \\\'hypernetworks\\\'), help=\"hypernetwork directory\")\n')
        print(f"--- [{UI}.py] Applied fixes to {cmd_args_path} ---")
    except Exception as e:
        print(f"--- [{UI}.py] ERROR applying fixes to {cmd_args_path}: {e} ---", file=sys.stderr)

# ======================== MAIN CODE =======================
if __name__ == '__main__':
    print(f"--- AnxLight {UI} UI Installer Script ---")
    
    unpack_webui()
    print(f"--- [{UI}.py] Unpack finished, proceeding to download configuration ---")
    asyncio.run(download_configuration())
    print(f"--- [{UI}.py] Download configuration finished, proceeding to apply module fixes ---")
    fixes_modules()
    print(f"--- [{UI}.py] Script finished ---")