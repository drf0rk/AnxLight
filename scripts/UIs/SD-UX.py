# ~ SD-UX.py | by ANXETY ~
# Refactored by SuperAssistant for standard Python execution
# Note: The exact nature and preferred installation method of "SD-UX" should be verified.
# This script currently assumes installation from the ANXETY HF REPO_URL (zip file).
# If SD-UX refers to Stability-AI/StableStudio, a different (Node.js based) installation is required.

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
UI = 'SD-UX' # Name of the directory for this UI

# (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME = PATHS['home_path']
VENV = PATHS['venv_path']
SETTINGS_PATH = PATHS['settings_path']

WEBUI = HOME / UI # Installation directory
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')

REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip" # Current source
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')
# Path for extensions; SD-UX might have its own specific structure or not support these generic extensions.
EXTS_PATH = WEBUI / 'extensions' # A guess, needs verification for SD-UX

CD(HOME) # Initial CWD


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
        directory_str = parts[1].strip() if len(parts) > 1 else str(WEBUI)
        filename = parts[2].strip() if len(parts) > 2 else Path(url).name
        tasks.append(_download_file(url, Path(directory_str), filename))
    await asyncio.gather(*tasks)

async def download_configuration():
    print(f"--- [{UI}.py] Downloading generic configuration files and extensions (review for SD-UX compatibility) ---")
    ## FILES
    url_cfg = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    # These configs are generic; SD-UX likely has its own specific config structure or none needed from here.
    configs_to_download = [
        # f"{url_cfg}/{UI}/config.json", # SD-UX specific?
        # f"{url_cfg}/{UI}/ui-config.json", # SD-UX specific?
        f"{url_cfg}/styles.csv,{WEBUI}", # Generic, may or may not apply
        f"{url_cfg}/user.css,{WEBUI}",   # Generic, may or may not apply
        f"{url_cfg}/card-no-preview.png,{WEBUI}/html", # Generic, path likely wrong for SD-UX
        f"{url_cfg}/notification.mp3,{WEBUI}",      # Generic, path likely wrong for SD-UX
        f"{url_cfg}/gradio-tunneling.py,{VENV}/lib/python3.10/site-packages/gradio_tunneling,main.py"
    ]
    await download_files(configs_to_download)

    ## REPOS (Extensions) - This list is generic and needs careful review for SD-UX
    extensions_list = [
        'https://github.com/anxety-solo/webui_timer timer',
        'https://github.com/anxety-solo/anxety-theme',
        # ... other generic extensions which might not apply to SD-UX ...
    ]
    # SD-UX (if StableStudio) has its own plugin system, not traditional A1111 extensions.
    # This section is highly likely to be N/A or require complete rework for SD-UX.
    # For now, leaving a placeholder but commenting out most aggressive cloning.
    
    # EXTS_PATH.mkdir(parents=True, exist_ok=True) # Use SD-UX specific extension path if known
    # original_cwd = Path.cwd()
    # try:
    #     CD(EXTS_PATH)
    #     print(f"--- [{UI}.py] Cloning extensions into {EXTS_PATH} (HIGHLY LIKELY NEEDS REVIEW/REMOVAL FOR SD-UX) ---")
    #     tasks = []
    #     for command_str in extensions_list:
    #         process = await asyncio.create_subprocess_shell(
    #             f"git clone --depth 1 {command_str}",
    #             stdout=subprocess.DEVNULL,
    #             stderr=subprocess.PIPE
    #         )
    #         tasks.append(process)
    #     for i, process in enumerate(tasks):
    #         stdout, stderr = await process.communicate() # Corrected from gather
    #         if process.returncode != 0:
    #             print(f"Error cloning extension: {extensions_list[i]}. Git stderr: {stderr.decode() if stderr else 'No stderr'}", file=sys.stderr)
    #         else:
    #            print(f"Successfully cloned: {extensions_list[i]}")
    # finally:
    #     CD(original_cwd)
    print(f"--- [{UI}.py] Generic extension download step skipped/placeholder for SD-UX. Needs verification. ---")


def unpack_webui():
    zip_path = HOME / f"{UI}.zip"
    print(f"--- [{UI}.py] Step 1: Downloading WebUI from {REPO_URL} (assuming zip archive) ---")
    m_download(f"{REPO_URL} {HOME} {UI}.zip") # Assuming m_download handles download
    
    print(f"--- [{UI}.py] Step 2: Unzipping {zip_path} to {WEBUI} ---")
    WEBUI.mkdir(parents=True, exist_ok=True) # Ensure WEBUI directory exists
    try:
        subprocess.run(["unzip", "-q", "-o", str(zip_path), "-d", str(WEBUI)], check=True, capture_output=True, text=True)
        print(f"--- [{UI}.py] Unzip successful ---")
    except subprocess.CalledProcessError as e:
        print(f"--- [{UI}.py] ERROR during unzip of {UI}.zip ---", file=sys.stderr)
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
    
    # If SD-UX is Stability-AI/StableStudio, it requires Node.js/Yarn setup.
    # This script does not handle that. The following is a placeholder.
    print(f"--- [{UI}.py] Basic unzip complete. If this is Stability-AI/StableStudio, further Node.js/Yarn setup is needed manually or via pre_flight_setup.py enhancements. ---")


# ======================== MAIN CODE =======================
if __name__ == '__main__':
    print(f"--- AnxLight {UI} UI Script ---")
    print(f"--- Note: Installation method and nature of '{UI}' needs verification. ---")
    
    unpack_webui()
    print(f"--- [{UI}.py] Unpack process finished. ---")
    # Configuration and extension downloads are generic and might need specific adjustments or be irrelevant for SD-UX.
    asyncio.run(download_configuration())
    print(f"--- [{UI}.py] Script finished ---")