""" Manager Module | by ANXETY """

from modules.CivitaiAPI import CivitAiAPI    # CivitAI API
import modules.json_utils as js              # JSON

from urllib.parse import urlparse, parse_qs
from pathlib import Path
import subprocess
import requests
import zipfile
import shlex
import sys
import os
import re


osENV = os.environ
CD = os.chdir

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}

HOME = PATHS.get('home_path', Path(osENV.get('HOME', '/content')))
SCR_PATH = PATHS.get('scr_path', HOME) # Fallback scr_path to HOME if not set
SETTINGS_PATH = PATHS.get('settings_path', HOME / 'anxlight_config.json')

# These will be default tokens if not overridden or found in config by specific functions
CAI_TOKEN_DEFAULT = ''
HF_TOKEN_DEFAULT = ''
try:
    if SETTINGS_PATH and SETTINGS_PATH.exists():
        CAI_TOKEN_DEFAULT = js.read(SETTINGS_PATH, 'WIDGETS.civitai_token') or ''
        HF_TOKEN_DEFAULT = js.read(SETTINGS_PATH, 'WIDGETS.huggingface_token') or ''
except Exception: # Handle cases where SETTINGS_PATH might not be fully formed yet or js.read fails
    print("[Manager.py] Warning: Could not read tokens from SETTINGS_PATH at module load.")
    pass


# ===================== Helper Function ====================

def log_message(message, log=False):
    if log:
        print(f"{message}")

def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_message(f"> \033[31m[Error] in {func.__name__}:\033[0m {e}", kwargs.get('log', True)) # Default log to True for errors
            return False
    return wrapper

def _handle_path_and_filename(parts, url, is_git=False): # Primarily for old m_download
    path, filename = None, None
    if len(parts) >= 3:
        path = Path(parts[1]).expanduser(); filename = parts[2]
    elif len(parts) == 2:
        arg = parts[1]
        if '/' in arg or arg.startswith('~'): path = Path(arg).expanduser()
        else: filename = arg
    if not is_git and 'drive.google.com' not in url:
        if filename and not Path(filename).suffix:
            url_ext = Path(urlparse(url).path).suffix
            if url_ext: filename += url_ext
            else: filename = None # Invalid if no extension derivable
    return path, filename

def is_github_url(url):
    parsed = urlparse(url); return parsed.netloc in ('github.com', 'www.github.com')

@handle_errors
def clean_url(url: str, cai_token_override: str = None) -> str | None:
    """Clean and format URLs. Returns cleaned URL or None on failure."""
    log_message(f"> Cleaning URL: {url}", True) # Log attempt
    token_to_use_cai = cai_token_override if cai_token_override is not None else CAI_TOKEN_DEFAULT

    if 'civitai.com/models/' in url:
        api = CivitAiAPI(str(token_to_use_cai) if token_to_use_cai else None)
        data = api.validate_download(url)
        if not data or not data.download_url:
            log_message(f"> Civitai URL validation/resolution failed for: {url}", True)
            return None
        url = data.download_url
        log_message(f"> Cleaned Civitai URL: {url}", True)
    elif 'huggingface.co' in url:
        if '/blob/' in url: url = url.replace('/blob/', '/resolve/')
        if '?' in url: url = url.split('?')[0]
        log_message(f"> Cleaned HuggingFace URL: {url}", True)
    elif 'github.com' in url:
        if '/blob/' in url: url = url.replace('/blob/', '/raw/')
        log_message(f"> Cleaned GitHub URL: {url}", True)
    return url

def get_file_name(url: str) -> str | None:
    """Get the file name based on the URL. Returns None if not determinable."""
    if any(domain in url for domain in ['civitai.com', 'drive.google.com']): return None
    try:
        name = Path(urlparse(url).path).name
        return name if name else None
    except Exception:
        return None

def execute_shell_command_with_bool_return(command_str: str, log: bool = False, cwd: str = None) -> bool:
    log_message(f"Executing shell command: {command_str} (CWD: {cwd or Path.cwd()})", log)
    try:
        process = subprocess.run(shlex.split(command_str), capture_output=True, text=True, check=False, cwd=cwd)
        if log and process.stdout.strip(): log_message(f"Stdout: {process.stdout.strip()}", log)
        if log and process.stderr.strip(): log_message(f"Stderr: {process.stderr.strip()}", log)
        if process.returncode == 0:
            log_message(">> Command executed successfully.", log); return True
        else:
            log_message(f">> Command failed with exit code {process.returncode}.", log); return False
    except Exception as e:
        log_message(f">> Exception during shell command: {e}", log); return False

# ======================== Download ========================

@handle_errors
def download_url_to_path(url: str, target_full_path: str, log: bool = False, hf_token: str = None, cai_token: str = None) -> bool:
    log_message(f"> Downloading: {url} \n  To: {target_full_path}", log)
    if not url or not target_full_path: log_message("> Error: URL or target_full_path is empty.", log); return False

    cleaned_url = clean_url(url, cai_token_override=cai_token)
    if not cleaned_url: log_message(f"> Error: URL cleaning failed for {url}.", log); return False
    url = cleaned_url

    target_path_obj = Path(target_full_path)
    target_dir = target_path_obj.parent
    target_filename = target_path_obj.name

    if not target_filename:
        inferred_name = get_file_name(url)
        if inferred_name:
            target_filename = inferred_name
            target_path_obj = target_dir / target_filename
            log_message(f">> Inferred filename: {target_filename}. Full path: {target_path_obj}", log)
        else:
            log_message(f"> Error: Target filename is empty and could not be inferred from URL: {url}", log); return False
            
    try: target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e: log_message(f"> Error creating directory {target_dir}: {e}", log); return False

    log_message(f">> Target directory: {target_dir}\n>> Target filename: {target_filename}", log)

    token_to_use_hf = hf_token if hf_token is not None else HF_TOKEN_DEFAULT

    if any(domain in url for domain in ['huggingface.co', 'github.com', 'civitai.com']):
        aria2_args_list = ['aria2c', '--header="User-Agent: Mozilla/5.0"', '--allow-overwrite=true', 
                           '--console-log-level=warn', '--summary-interval=0',
                           '--stderr=true', '-c', '-x16', '-s16', '-k1M', '-j5',
                           f'--dir="{str(target_dir)}"', f'--out="{target_filename}"']
        if token_to_use_hf and 'huggingface.co' in url:
            aria2_args_list.append(f'--header="Authorization: Bearer {token_to_use_hf}"')
        aria2_args_list.append(f'"{url}"')
        command = " ".join(aria2_args_list)
        log_message(f">> Attempting Aria2c: {command}", log)
        process = subprocess.run(shlex.split(command), capture_output=True, text=True)
        if process.returncode == 0 and target_path_obj.exists():
             log_message(f">> Aria2c download successful for {target_filename}", log); return True
        else:
            log_message(f">> Aria2c download FAILED for {target_filename}. Code: {process.returncode}", log)
            if process.stderr: log_message(f"   Aria2c stderr: {process.stderr.strip()}", log)
            return False
    elif 'drive.google.com' in url:
        cmd_list = ['gdown', '--fuzzy']
        if 'drive.google.com/drive/folders' in url: cmd_list.extend(['--folder', '-O', str(target_dir)])
        else: cmd_list.extend(['-O', str(target_path_obj)])
        cmd_list.append(url)
        command = " ".join(cmd_list)
        log_message(f">> Attempting GDown: {command}", log)
        return execute_shell_command_with_bool_return(command, log)
    else:
        command_list = ['curl', '-#', '-L', '-f', '-o', str(target_path_obj), url]
        command = " ".join(command_list)
        log_message(f">> Attempting Curl: {command}", log)
        return execute_shell_command_with_bool_return(command, log)


@handle_errors
def download_file(url, filename, log):
    log_message(f"[Manager old `download_file`] Called for URL: {url}, Filename: {filename}, CWD: {Path.cwd()}", log)
    if not filename:
        filename = get_file_name(url)
        if not filename:
            log_message(f"> Old download_file: Could not determine filename for {url}", log)
            return False
            
    full_target_path = str(Path.cwd() / filename)
    return download_url_to_path(url, full_target_path, log)


@handle_errors
def process_download(line, log, unzip):
    parts = line.split(); url = parts[0].replace('\\\\', '')
    cleaned_url = clean_url(url)
    if not cleaned_url: return False
    url = cleaned_url

    path, filename = _handle_path_and_filename(parts, url)
    current_dir = Path.cwd()
    download_successful = False
    try:
        target_dir_for_this_item = path if path else current_dir
        if path:
            target_dir_for_this_item.mkdir(parents=True, exist_ok=True)
        
        final_filename = filename if filename else get_file_name(url)
        if not final_filename:
            log_message(f"> process_download: Could not determine filename for {url}", log)
            return False

        full_target_path = str(target_dir_for_this_item / final_filename)
        download_successful = download_url_to_path(url, full_target_path, log)

        if download_successful and unzip and final_filename.endswith('.zip'):
            unzip_file(full_target_path, log)
    finally:
        pass
    return download_successful


@handle_errors
def m_download(line, log=False, unzip=False):
    links = [link.strip() for link in line.split(',') if link.strip()]
    if not links: log_message('> Missing URL, downloading nothing', log); return
    for link_item in links:
        potential_txt_path = Path(link_item).expanduser()
        if link_item.endswith('.txt') and potential_txt_path.is_file():
            log_message(f"> Reading URLs from file: {potential_txt_path}", log)
            with open(potential_txt_path, 'r') as file:
                for file_line in file:
                    if file_line.strip(): process_download(file_line.strip(), log, unzip)
        else:
            process_download(link_item, log, unzip)


@handle_errors
def unzip_file(zip_filepath_str, log):
    zip_filepath = Path(zip_filepath_str)
    extract_path = zip_filepath.parent
    log_message(f">> Unzipping: {zip_filepath} to {extract_path}", log)
    with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    log_message(f">> Successfully unpacked: {zip_filepath}", log)
    return True

@handle_errors
def execute_git_command(command, log=False):
    repo_url_match = re.search(r'https?://\S+', command)
    repo_url = repo_url_match.group() if repo_url_match else "Unknown_Repo"
    log_message(f">> Executing Git: {command}", log)
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    ret_code = process.wait()
    if ret_code == 0:
        log_message(f">> Git command successful for {repo_url}", log)
        return True
    else:
        log_message(f">> Git command FAILED for {repo_url} with code {ret_code}", log)
        return False

def build_git_command(url, repo_name, recursive, depth):
    cmd = ['git', 'clone']
    if depth > 0: cmd.extend(['--depth', str(depth)])
    if recursive: cmd.append('--recursive')
    cmd.append(url)
    if repo_name: cmd.append(repo_name)
    return ' '.join(cmd)

@handle_errors
def process_clone(input_source, recursive, depth, log=False):
    parts = shlex.split(input_source)
    if not parts: log_message('>> \033[31m[Error]: Empty clone command\033[0m', log); return False
    url = parts[0].replace('\\\\', '')
    if not url: log_message(f'>> \033[31m[Error]:\033[0m Empty URL in clone: {input_source}', log); return False
    if not is_github_url(url): log_message(f'>>  \033[33m[Warning]:\033[0m Not a GitHub URL - {url}', log); return False
    
    path, repo_name = _handle_path_and_filename(parts, url, is_git=True)
    current_dir = Path.cwd()
    clone_success = False
    try:
        target_clone_dir = path if path else current_dir
        if path: target_clone_dir.mkdir(parents=True, exist_ok=True)
        
        command = build_git_command(url, repo_name, recursive, depth)
        
        execution_cwd = str(path) if path else None
        clone_success = execute_git_command(command, log)
    finally:
        pass
    return clone_success

def m_clone(input_source, recursive=True, depth=1, log=False):
    sources = [link.strip() for link in input_source.split(',') if link.strip()]
    if not sources: log_message('>> No valid repositories to clone', log); return
    for source_item in sources:
        if source_item.endswith('.txt') and Path(source_item).expanduser().is_file():
            log_message(f"> Reading clone sources from file: {source_item}", log)
            with open(Path(source_item).expanduser(), 'r') as f:
                for line in f:
                    line = line.strip()
                    if line: process_clone(line, recursive, depth, log)
        else:
            process_clone(source_item, recursive, depth, log)