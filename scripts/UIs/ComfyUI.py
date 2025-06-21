# ~ ComfyUI.py | by ANXETY ~
# Refactored by SuperAssistant for standard Python execution

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
UI = 'ComfyUI'

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
CUSTOM_NODES_PATH = WEBUI / 'custom_nodes'

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
        tasks = []
        for repo_url_with_optional_name in extensions_list:
            git_command_str = f"git clone --depth 1 {repo_url_with_optional_name}"
            process = await asyncio.create_subprocess_shell(
                git_command_str,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            tasks.append(process)

        for i, process in enumerate(tasks):
            _, stderr = await process.communicate()
            if process.returncode != 0:
                print(f"Error cloning custom node: {extensions_list[i]}. Git stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)
            else:
                print(f"Successfully cloned: {extensions_list[i]}")
    finally:
        CD(original_cwd)

def unpack_webui():
    zip_path = HOME / f"{UI}.zip"
    print(f"--- [{UI}.py] Step 1: Downloading WebUI from {REPO_URL} ---")
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
    print(f"--- AnxLight {UI} UI Script ---")
    
    unpack_webui()
    print(f"--- [{UI}.py] Unpack finished, proceeding to download configuration & custom nodes ---")
    asyncio.run(download_configuration())
    print(f"--- [{UI}.py] Script finished ---")