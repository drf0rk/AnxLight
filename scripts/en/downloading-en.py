# AnxLight Backend Script (downloading-en.py)
# Original: # ~ download.py | by ANXETY ~

import os
import sys
import json
import time
import re
import shlex
import shutil
import zipfile
import subprocess 
from pathlib import Path
from urllib.parse import urlparse
from datetime import timedelta
import importlib

# --- Versioning ---
try:
    from anxlight_version import DOWNLOADER_VERSION, A1111_UI_VERSION
except ImportError:
    DOWNLOADER_VERSION = "1.0.0"
    A1111_UI_VERSION = "unknown" # Default, will be replaced if UI script has versioning

print(f"--- AnxLight Downloader v{DOWNLOADER_VERSION} ---")

# --- AnxLight: Helper functions to replace IPython specifics ---
def run_shell_command(command_str, suppress_output=False, check_rc=False, cwd=None):
    print(f"[ShellCmd] Executing: {command_str}")
    try:
        result = subprocess.run(command_str, shell=True, check=check_rc, 
                                capture_output=True, text=True, cwd=cwd, env=os.environ.copy())
        if not suppress_output:
            if result.stdout and result.stdout.strip(): print(f"[ShellCmd STDOUT]: {result.stdout.strip()}")
        if result.stderr and result.stderr.strip() and (not suppress_output or (check_rc and result.returncode != 0)):
             print(f"[ShellCmd STDERR]: {result.stderr.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"[ShellCmd Error] Command '{command_str}' failed with rc {e.returncode}")
        if e.stdout and e.stdout.strip(): print(f"[ShellCmd STDOUT on Error]: {e.stdout.strip()}")
        if e.stderr and e.stderr.strip(): print(f"[ShellCmd STDERR on Error]: {e.stderr.strip()}")
        if check_rc: raise
        return e 
    except Exception as e_gen:
        print(f"[ShellCmd Exception] Running '{command_str}': {e_gen}")
        return None

def run_python_script(script_path_str, script_cwd=None):
    # This function will now also try to get the version from the script
    script_version = "unknown"
    try:
        # A bit of a hack to get the version without full import issues
        with open(script_path_str, 'r') as f:
            for line in f:
                if "A1111_SCRIPT_VERSION" in line: # Adapt for other scripts if needed
                    script_version = line.split('=')[-1].strip().replace('"', '')
                    break
    except:
        pass # Ignore if we can't get the version

    print(f"[PyScript] Executing: {sys.executable} {script_path_str} (Target Version: {script_version})")
    script_cwd = script_cwd or os.getcwd()
    try:
        result = subprocess.run([sys.executable, script_path_str], check=True, 
                                capture_output=True, text=True, env=os.environ.copy(), cwd=script_cwd)
        if result.stdout.strip(): print(f"[PyScript STDOUT - {os.path.basename(script_path_str)}]:\\n{result.stdout.strip()}")
        if result.stderr.strip(): print(f"[PyScript STDERR - {os.path.basename(script_path_str)}]:\\n{result.stderr.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"[PyScript Error] Script '{script_path_str}' failed with rc {e.returncode}")
        if e.stdout and e.stdout.strip(): print(f"[PyScript STDOUT on Error]:\\n{e.stdout.strip()}")
        if e.stderr and e.stderr.strip(): print(f"[PyScript STDERR on Error]:\\n{e.stderr.strip()}")
        raise 
    except Exception as e_gen:
        print(f"[PyScript Exception] Running '{script_path_str}': {e_gen}")
        raise 

def clear_output_placeholder():
    print("\\n--- [Output Cleared (Placeholder)] ---\\n")
# --- End AnxLight Helpers ---

try:
    from webui_utils import handle_setup_timer
    from Manager import m_download, m_clone
    from CivitaiAPI import CivitAiAPI
    import json_utils as js
    print("[downloading-en.py] Successfully imported utility modules.")
except ImportError as e:
    print(f"[downloading-en.py] CRITICAL Error importing utility modules: {e}")
    print(f"[downloading-en.py] Check PYTHONPATH for subprocess. Current sys.path: {sys.path}")
    print(f"[downloading-en.py] Current PYTHONPATH env var: {os.environ.get('PYTHONPATH')}")
    if 'js' not in globals():
        class DummyJsonUtils: # Define a more complete dummy for js
            def read(self, path, key=None, default=None): 
                print(f"DummyJsonUtils.read called: path={path}, key={key}, default={default}"); 
                if key: return default if default is not None else {} # Simulate finding nothing or default for a key
                return {} # Simulate empty JSON if no key
            def update(self, path, key, value): print(f"DummyJsonUtils.update called: path={path}, key={key}, value={value}")
            def key_exists(self, path, key, value=None): print(f"DummyJsonUtils.key_exists called: path={path}, key={key}, value={value}"); return False
            def save(self, path, key, value): print(f"DummyJsonUtils.save called: path={path}, key={key}, value={value}")

        js = DummyJsonUtils()
        print("[downloading-en.py] Using DUMMY json_utils.")
    # Define other dummies if necessary for script to not crash immediately
    if 'handle_setup_timer' not in globals():
        def handle_setup_timer(*args): print(f"Dummy handle_setup_timer called with {args}"); return None
    if 'm_download' not in globals():
        def m_download(*args): print(f"Dummy m_download called with {args}")
    if 'm_clone' not in globals():
        def m_clone(*args): print(f"Dummy m_clone called with {args}")
    if 'CivitAiAPI' not in globals():
        class CivitAiAPI:
            def __init__(self, token): print(f"Dummy CivitAiAPI initialized with token: {token}")
            def validate_download(self, *args): print(f"Dummy CivitAiAPI.validate_download called with {args}"); return None


osENV = os.environ
CD = os.chdir

PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME = PATHS.get('home_path')
VENV = PATHS.get('venv_path')
SCR_PATH = PATHS.get('scr_path')
SETTINGS_PATH = PATHS.get('settings_path')

if not all([HOME, VENV, SCR_PATH, SETTINGS_PATH]):
    print("[downloading-en.py] CRITICAL ERROR: Essential path variables not found in environment.")
    sys.exit(1)

SCRIPTS = SCR_PATH / 'scripts'
LANG, ENV_NAME, UI, WEBUI_PATH_STR = "en", "Unknown", "A1111", ""
WEBUI_DIR = None
try:
    LANG = js.read(SETTINGS_PATH, 'ENVIRONMENT.lang') or LANG
    ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name') or ENV_NAME
    UI = js.read(SETTINGS_PATH, 'WEBUI.current') or UI # This key might be 'change_webui' from WIDGETS
    # Let's check WIDGETS.change_webui if WEBUI.current isn't found
    if not UI or UI == "A1111": # If UI is default or not found in WEBUI key
        UI = js.read(SETTINGS_PATH, 'WIDGETS.change_webui') or "A1111"

    WEBUI_PATH_STR = js.read(SETTINGS_PATH, 'WEBUI.webui_path') # This might not exist
    WEBUI_DIR = Path(WEBUI_PATH_STR) if WEBUI_PATH_STR else (SCR_PATH / UI)
    print(f"[downloading-en.py] Settings loaded: LANG={LANG}, ENV_NAME={ENV_NAME}, UI={UI}, WEBUI_DIR={WEBUI_DIR}")
except Exception as e_settings:
    print(f"[downloading-en.py] Error loading initial settings from {SETTINGS_PATH}: {e_settings}")
    WEBUI_DIR = SCR_PATH / UI

class COLORS:
    R = "\\033[31m"; G = "\\033[32m"; Y = "\\033[33m"; B = "\\033[34m"; lB = "\\033[36;1m"; X = "\\033[0m"
COL = COLORS

def install_dependencies_os(commands): # Renamed to avoid conflict
    for cmd in commands:
        run_shell_command(cmd, suppress_output=True)

def setup_venv(url):
    CD(str(HOME)) 
    fn = Path(url).name
    if 'm_download' in globals(): m_download(f"{url} {str(HOME)} {fn}")

    install_commands = []
    if ENV_NAME == 'Kaggle':
        install_commands.extend([
            f"{sys.executable} -m pip install ipywidgets jupyterlab_widgets --upgrade",
            'rm -f /usr/lib/python3.10/sitecustomize.py' 
        ])
    # The sudo command will likely fail in restricted environments. Consider making it optional or conditional.
    install_commands.append('apt-get -y install lz4 pv || echo "apt-get failed, proceeding..."') 
    install_dependencies_os(install_commands)

    run_shell_command(f"pv {fn} | lz4 -d | tar xf -", cwd=str(HOME))
    if (HOME / fn).exists(): (HOME / fn).unlink()

    BIN = str(VENV / 'bin')
    site_packages_glob = list((VENV / 'lib').glob('python3.*/site-packages'))
    PKG = str(site_packages_glob[0]) if site_packages_glob else str(VENV / 'lib/python3.10/site-packages')

    os.environ['PYTHONWARNINGS'] = 'ignore'
    if PKG not in sys.path: sys.path.insert(0, PKG)
    
    current_path_env = os.environ.get('PATH', '')
    if BIN not in current_path_env:
        os.environ['PATH'] = f"{BIN}{os.pathsep}{current_path_env}"
    
    current_pythonpath_env = os.environ.get('PYTHONPATH', '')
    if PKG not in current_pythonpath_env:
         os.environ['PYTHONPATH'] = f"{PKG}{os.pathsep}{current_pythonpath_env}" if current_pythonpath_env else PKG

def install_packages_pip(install_lib): # Renamed
    for index, (package, install_cmd) in enumerate(install_lib.items(), start=1):
        print(f"\\r[{index}/{len(install_lib)}] {COL.G}>>{COL.X} Installing {COL.Y}{package}{COL.X}..." + ' ' * 35, end='')
        run_shell_command(install_cmd, suppress_output=True)

if not js.key_exists(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True):
    install_lib = {
        'aria2': f"{sys.executable} -m pip install aria2",
        'gdown': f"{sys.executable} -m pip install gdown",
    }
    print('💿 Installing core libraries (aria2, gdown)...')
    install_packages_pip(install_lib)
    clear_output_placeholder()
    js.update(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)

current_ui_settings = js.read(SETTINGS_PATH, 'WIDGETS.change_webui') or UI # Read from WIDGETS
latest_ui_settings = js.read(SETTINGS_PATH, 'WEBUI.latest') or current_ui_settings 

venv_needs_reinstall = (not VENV.exists()) or \
                       (latest_ui_settings == 'Classic') != (current_ui_settings == 'Classic')

if venv_needs_reinstall:
    if VENV.exists():
        print("🗑️ Removing old venv...")
        shutil.rmtree(VENV)
        clear_output_placeholder()
    py_version_str = '(unknown)'
    if current_ui_settings == 'Classic':
        venv_url = "https://huggingface.co/NagisaNao/ANXETY/resolve/main/python31112-venv-torch251-cu121-C-Classic.tar.lz4"
        py_version_str = '(3.11.12)'
    else:
        venv_url = "https://huggingface.co/NagisaNao/ANXETY/resolve/main/python31015-venv-torch251-cu121-C-fca.tar.lz4"
        py_version_str = '(3.10.15)'
    print(f"♻️ Installing VENV {py_version_str}, this will take some time...")
    setup_venv(venv_url)
    clear_output_placeholder()
    js.update(SETTINGS_PATH, 'WEBUI.latest', current_ui_settings)

# Renamed function to match original call sites (load_settings)
def load_settings(path):
    """Load settings from a JSON file."""
    print(f"[downloading-en.py] Attempting to load settings from: {path}")
    try:
        environment_settings = js.read(path, 'ENVIRONMENT') or {}
        widgets_settings = js.read(path, 'WIDGETS') or {}
        webui_settings = js.read(path, 'WEBUI') or {} # This might be sparsely populated by AnxLight initially
        
        all_settings = {}
        all_settings.update(environment_settings)
        all_settings.update(widgets_settings) 
        # WEBUI specific settings from the original file structure, might not be fully present
        # in AnxLight's initial config.json, but WIDGETS.change_webui is the primary driver.
        all_settings['UI'] = widgets_settings.get('change_webui', UI) # Use WIDGETS.change_webui for current UI
        all_settings['WEBUI_PATH_STR'] = webui_settings.get('webui_path', str(SCR_PATH / all_settings['UI'])) # Default path
        all_settings['WEBUI_DIR'] = Path(all_settings['WEBUI_PATH_STR'])
        
        print(f"[downloading-en.py] Loaded settings: {list(all_settings.keys())}")
        return all_settings
    except Exception as e:
        print(f"[downloading-en.py] Error in load_settings: {e}")
        print(f"[downloading-en.py] Traceback: {traceback.format_exc()}")
        return {}

settings = load_settings(SETTINGS_PATH)
locals().update(settings) # This makes keys from 'settings' dict local variables

# Re-evaluate WEBUI_DIR based on loaded settings, particularly UI from WIDGETS
UI = settings.get('UI', UI) # Ensure UI is from the loaded settings
WEBUI_DIR = Path(settings.get('WEBUI_PATH_STR', str(SCR_PATH / UI)))
print(f"[downloading-en.py] Effective UI: {UI}, WEBUI_DIR: {WEBUI_DIR}")


if UI in ['A1111', 'SD-UX'] and ENV_NAME == 'Google Colab' and not Path('/root/.cache/huggingface/hub/models--Bingsu--adetailer').exists():
    print('🚚 Unpacking ADetailer model cache for Colab...')
    name_zip = 'hf_cache_adetailer'
    chache_url = 'https://huggingface.co/NagisaNao/ANXETY/resolve/main/hf_chache_adetailer.zip'
    zip_path = HOME / f"{name_zip}.zip"
    if 'm_download' in globals(): m_download(f"{chache_url} {HOME} {name_zip}")
    run_shell_command(f"unzip -q -o {zip_path} -d /") 
    run_shell_command(f"rm -rf {zip_path}")
    clear_output_placeholder()

start_timer_val = js.read(SETTINGS_PATH, 'ENVIRONMENT.start_timer')

if not WEBUI_DIR.exists():
    start_install_time = time.time() # Renamed variable
    print(f"⌚ Unpacking Stable Diffusion... | WEBUI: {COL.B}{UI}{COL.X}", end='')
    ui_script = SCRIPTS / 'UIs' / f"{UI}.py"
    run_python_script(str(ui_script), script_cwd=str(SCR_PATH))
    if 'handle_setup_timer' in globals(): handle_setup_timer(str(WEBUI_DIR), start_timer_val)
    install_time_val = time.time() - start_install_time # Renamed variable
    minutes, seconds = divmod(int(install_time_val), 60)
    print(f"\\r🚀 Unpacking {COL.B}{UI}{COL.X} is complete! {minutes:02}:{seconds:02} ⚡" + ' '*25)
else:
    print(f"🔧 Current WebUI: {COL.B}{UI}{COL.X}")
    print('🚀 Unpacking is complete. Pass. ⚡')
    if 'handle_setup_timer' in globals():
      timer_env_val = handle_setup_timer(str(WEBUI_DIR), start_timer_val) # Renamed variable
      elapsed_time = str(timedelta(seconds=time.time() - (timer_env_val or start_timer_val) )).split('.')[0]
      print(f"⌚️ Session duration: {COL.Y}{elapsed_time}{COL.X}")

# Using .get() for settings dictionary access for safety
if settings.get('latest_webui') or settings.get('latest_extensions'):
    action = 'WebUI and Extensions' if settings.get('latest_webui') and settings.get('latest_extensions') else \
             ('WebUI' if settings.get('latest_webui') else 'Extensions')
    print(f"⌚️ Update {action}...")
    run_shell_command('git config --global user.email "you@example.com"', suppress_output=True)
    run_shell_command('git config --global user.name "Your Name"', suppress_output=True)

    if settings.get('latest_webui'):
        CD(str(WEBUI_DIR))
        run_shell_command('git stash push --include-untracked', suppress_output=True)
        run_shell_command('git pull --rebase', suppress_output=True)
        run_shell_command('git stash pop', suppress_output=True, check_rc=False)

    if settings.get('latest_extensions'):
        ext_dir_path = WEBUI_DIR / 'extensions'
        if ext_dir_path.is_dir():
            for entry in os.listdir(ext_dir_path):
                dir_p = ext_dir_path / entry
                if dir_p.is_dir() and (dir_p / '.git').is_dir():
                    print(f"Updating extension: {entry}")
                    # Using subprocess.run directly for more control if needed
                    subprocess.run(['git', 'reset', '--hard'], cwd=str(dir_p), capture_output=True)
                    subprocess.run(['git', 'pull'], cwd=str(dir_p), capture_output=True)
    print(f"\\r✨ Update {action} Completed!")

if UI == "A1111":
    umi_script_path = WEBUI_DIR / 'extensions/Umi-AI-Wildcards/scripts/wildcard_recursive.py'
    if umi_script_path.exists():
        run_shell_command(f"sed -i 's/open=True/open=False/g; s/open= False/open=False/g' {str(umi_script_path)}", suppress_output=True)

commit_hash_val = settings.get('commit_hash')
if commit_hash_val:
    print('🔄 Switching to the specified version...', end='')
    CD(str(WEBUI_DIR))
    run_shell_command('git config --global user.email "you@example.com"', suppress_output=True)
    run_shell_command('git config --global user.name "Your Name"', suppress_output=True)
    run_shell_command(f'git reset --hard {commit_hash_val}', suppress_output=True)
    # `git pull origin <hash>` is not standard; usually pull a branch or tag.
    # If it's just to ensure the commit is present, reset --hard should suffice.
    # run_shell_command(f'git pull origin {commit_hash_val}', suppress_output=True, check_rc=False)
    print(f"\\r🔄 Switch complete! Current commit: {COL.B}{commit_hash_val}{COL.X}")

if ENV_NAME == 'Google Colab':
    try:
        from google.colab import drive
        mountGDrive_flag = js.read(SETTINGS_PATH, 'mountGDrive')
        print(f"[downloading-en.py] Google Drive mount flag: {mountGDrive_flag}. Original symlink logic is complex and currently omitted for this refactor.")
        # Original handle_gdrive logic would be here if fully ported.
    except ImportError:
        print("[downloading-en.py] google.colab module not found. Skipping Drive operations.")
    except Exception as e_drive:
        print(f"[downloading-en.py] Error during Google Drive processing: {e_drive}")

print('📦 Downloading models and stuff (using placeholders for original complex logic)...')
# The full original download logic (handle_submodels, process_file_downloads, download, manual_download etc.)
# is very extensive. This refactor focuses on making the script runnable.
# The actual download calls would need to use the settings variables populated by locals().update(settings).
# For example: model = settings.get('model'), model_num = settings.get('model_num'), etc.
# And then the original logic using these variables would follow.

# Example placeholder:
if settings.get('detailed_download') == 'on':
    print(f"\\n\\n{COL.Y}# ====== Detailed Download (Placeholder) ====== #\\n{COL.X}")
    # download(line_variable_constructed_from_settings) # 'line' would be built up here
    print(f"Placeholder: Would call download function with constructed line of URLs.")
    print(f"\\n{COL.Y}# ============================================== #\\n{COL.X}")
else:
    print("Placeholder: Simulating non-detailed download (original used capture_output).")

print('\\r🏁 Download models processing in downloading-en.py finished (or placeholder executed)!')

extension_repo_list = settings.get('extension_repo', []) # Ensure key exists
extension_dir_name = 'custom_nodes' if UI == 'ComfyUI' else 'extensions'
extension_full_path = WEBUI_DIR / extension_dir_name

if extension_repo_list: # This would be populated from settings
    print(f"✨ Installing custom {extension_dir_name}...")
    # for repo_url, repo_name in extension_repo_list:
    #     if 'm_clone' in globals(): m_clone(f"{repo_url} {str(extension_full_path)} {repo_name}")
    print(f"\\r📦 Placeholder for custom {extension_dir_name} installation.")

if UI == 'ComfyUI':
    adetailer_dir_path = WEBUI_DIR / 'models' / 'adetailer' 
    # ... (simplified ComfyUI ADetailer sorting logic) ...
    print(f"Placeholder for ComfyUI ADetailer model sorting if {str(adetailer_dir_path)} exists.")

# download_result_script_path = SCRIPTS / 'download-result.py'
# if download_result_script_path.exists():
#     print(f"Running {download_result_script_path}...")
#     run_python_script(str(download_result_script_path), script_cwd=str(SCRIPTS))
# else:
#     print(f"Warning: {download_result_script_path} not found.")

print(f"\\n--- {os.path.basename(__file__)} finished its tasks ---")