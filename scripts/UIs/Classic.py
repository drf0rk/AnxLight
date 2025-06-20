# ~ Classic.py | by ANXETY ~
# Refactored by SuperAssistant for standard Python execution

from Manager import m_download   # Every Download
import json_utils as js          # JSON

from pathlib import Path
import subprocess
import asyncio
import os
import sys # Ensure sys is imported for sys.exit and sys.stderr

# try:
#     # Assumes anxlight_version.py is in the parent 'scripts' directory
#     sys.path.append(str(Path(__file__).parent.parent))
#     from anxlight_version import CLASSIC_UI_VERSION # Placeholder, versioning might be different
# except ImportError:
#     CLASSIC_UI_VERSION = "0.0.1" # Fallback
# Commenting out versioning for now as it's not present in original and might need specific var name.

osENV = os.environ
CD = os.chdir

# Constants
UI = 'Classic'

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
EXTS = Path(js.read(SETTINGS_PATH, 'WEBUI.extension_dir'))

CD(HOME)


# ==================== WEBUI OPERATIONS ====================

async def _download_file(url, directory, filename):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / filename

    if file_path.exists():
        # Consider if unlinking is always desired or if we should skip download
        # Forcing fresh download by unlinking:
        try:
            file_path.unlink()
        except OSError as e:
            print(f"Warning: Could not delete existing file {file_path}. Error: {e}", file=sys.stderr)


    # Using shell=True for curl here, ensure URL and file_path are safe.
    # For greater security, consider using a library like 'requests' or 'httpx' for downloads.
    process = await asyncio.create_subprocess_shell(
        f"curl -sLo \"{file_path}\" \"{url}\"", # Added quotes for safety
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE # Capture stderr for curl
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        print(f"Error downloading {url} to {file_path}. curl stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)


async def download_files(file_list):
    tasks = []
    for file_info in file_list:
        parts = file_info.split(',')
        url = parts[0].strip()
        # Default Save Path might need adjustment if WEBUI is not guaranteed to exist when _download_file is called
        # For now, assuming WEBUI path is valid or _download_file handles its creation via directory.mkdir
        directory_str = parts[1].strip() if len(parts) > 1 else str(WEBUI)
        filename = parts[2].strip() if len(parts) > 2 else Path(url).name
        tasks.append(_download_file(url, Path(directory_str), filename))
    await asyncio.gather(*tasks)

async def download_configuration():
    ## FILES
    url_cfg = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    configs = [
        # settings
        f"{url_cfg}/{UI}/config.json",
        f"{url_cfg}/{UI}/ui-config.json",
        f"{url_cfg}/styles.csv",
        f"{url_cfg}/user.css",
        # other | UI
        f"{url_cfg}/notification.mp3",
        # other | tunneling
        # Ensure VENV path is correct and site-packages exist. Python version hardcoded to 3.11 here.
        f"{url_cfg}/gradio-tunneling.py, {VENV}/lib/python3.11/site-packages/gradio_tunneling, main.py"
    ]
    await download_files(configs)

    ## REPOS
    extensions_list = [
        ## ANXETY Edits
        'https://github.com/anxety-solo/webui_timer timer',
        'https://github.com/anxety-solo/anxety-theme',
        'https://github.com/anxety-solo/sd-civitai-browser-plus Civitai-Browser-Plus',

        ## Gutris1
        # 'https://github.com/gutris1/sd-image-viewer Image-Viewer',    # Not Working
        'https://github.com/gutris1/sd-image-info Image-Info',
        'https://github.com/gutris1/sd-hub SD-Hub',

        ## OTHER | ON
        'https://github.com/Bing-su/adetailer',
        'https://github.com/Haoming02/sd-forge-couple SD-Couple',
        'https://github.com/hako-mikan/sd-webui-regional-prompter Regional-Prompter',

        ## OTHER | OFF | Archived
        # 'https://github.com/thomasasfk/sd-webui-aspect-ratio-helper Aspect-Ratio-Helper',
        # 'https://github.com/zanllp/sd-webui-infinite-image-browsing Infinite-Image-Browsing',
        # 'https://github.com/ilian6806/stable-diffusion-webui-state State',
        # 'https://github.com/DominikDoom/a1111-sd-webui-tagcomplete TagComplete',
        # 'https://github.com/Tsukreya/Umi-AI-Wildcards'
    ]
    if ENV_NAME == 'Kaggle':
        extensions_list.append('https://github.com/anxety-solo/sd-encrypt-image Encrypt-Image')

    EXTS.mkdir(parents=True, exist_ok=True)
    
    # Store current CWD and change to EXTS, then change back
    original_cwd = Path.cwd()
    try:
        CD(EXTS)
        tasks = []
        for command_str in extensions_list:
            # Splitting command string for git clone properly if it has a target directory
            parts = command_str.split()
            git_command = ["git", "clone", "--depth", "1"] + parts
            
            # Using shell=False is generally safer if command components are well-defined.
            # However, create_subprocess_shell was used before. For consistency, let's keep it,
            # but ideally, for git commands, splitting and using exec would be better.
            # Reverting to shell=True to match original structure and avoid deeper refactor for now.
            process = await asyncio.create_subprocess_shell(
                f"git clone --depth 1 {command_str}",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE # Capture stderr for git clone
            )
            tasks.append(process) # append the process to await its completion later

        # Wait for all git clone processes to complete and check for errors
        for i, process in enumerate(tasks):
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                print(f"Error cloning extension: {extensions_list[i]}. Git stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)

    finally:
        CD(original_cwd) # Ensure we change back to original CWD

def unpack_webui():
    zip_path = HOME / f"{UI}.zip"
    print(f"--- [{UI}.py] Step 1: Downloading WebUI from {REPO_URL} ---")
    m_download(f"{REPO_URL} {HOME} {UI}.zip") # Assuming m_download is robust
    
    print(f"--- [{UI}.py] Step 2: Unzipping {zip_path} to {WEBUI} ---")
    try:
        # Using list of arguments for better security and handling of paths with spaces
        subprocess.run(["unzip", "-q", "-o", str(zip_path), "-d", str(WEBUI)], check=True, capture_output=True, text=True)
        print(f"--- [{UI}.py] Unzip successful ---")
    except subprocess.CalledProcessError as e:
        print(f"--- [{UI}.py] ERROR during unzip ---", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        print(f"STDOUT: {e.stdout}", file=sys.stderr) # stdout might be empty due to -q
        print(f"STDERR: {e.stderr}", file=sys.stderr)
        sys.exit(f"Critical error during unzip of {UI}.zip. Exiting.") # Exit on critical failure
    except FileNotFoundError:
        print(f"--- [{UI}.py] ERROR: unzip command not found. Please ensure unzip is installed and in PATH.", file=sys.stderr)
        sys.exit(f"Critical error: unzip command not found for {UI}.zip. Exiting.")

    print(f"--- [{UI}.py] Step 3: Removing {zip_path} ---")
    try:
        # Using list of arguments
        subprocess.run(["rm", "-rf", str(zip_path)], check=True)
        print(f"--- [{UI}.py] Zip removal successful ---")
    except subprocess.CalledProcessError as e:
        print(f"--- [{UI}.py] WARNING during zip removal of {UI}.zip ---", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        # No stdout/stderr for rm -rf usually unless error, check=True handles error exit.
        print(f"STDERR: {e.stderr if e.stderr else 'No specific stderr from rm.'}", file=sys.stderr)
    except FileNotFoundError:
        print(f"--- [{UI}.py] WARNING: rm command not found. Could not remove {zip_path}.", file=sys.stderr)


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

        with cmd_args_path.open('a', encoding='utf-8') as f: # Open in append mode
            f.write(f"\n\n{marker}\n")
            f.write('parser.add_argument(\"--hypernetwork-dir\", type=normalized_filepath, '\
                   'default=os.path.join(models_path, \\\'hypernetworks\\\'), help=\"hypernetwork directory\")\n')
        print(f"--- [{UI}.py] Applied fixes to {cmd_args_path} ---")
    except Exception as e:
        print(f"--- [{UI}.py] ERROR applying fixes to {cmd_args_path}: {e} ---", file=sys.stderr)


# ======================== MAIN CODE =======================
if __name__ == '__main__':
    # CLASSIC_UI_VERSION is not defined here if import fails, using UI constant for print
    print(f"--- AnxLight {UI} UI Script ---") # Removed version for now
    
    # Removed 'with capture.capture_output():' as it's IPython specific
    # Output will now go to stdout/stderr as per subprocess calls and print statements
    
    unpack_webui()
    print(f"--- [{UI}.py] Unpack finished, proceeding to download configuration ---")
    asyncio.run(download_configuration())
    print(f"--- [{UI}.py] Download configuration finished, proceeding to apply module fixes ---")
    fixes_modules()
    print(f"--- [{UI}.py] Script finished ---")