""" Manager Module | by ANXETY """

from CivitaiAPI import CivitAiAPI    # CivitAI API
import json_utils as js              # JSON

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
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

CAI_TOKEN = js.read(SETTINGS_PATH, 'WIDGETS.civitai_token') or '65b66176dcf284b266579de57fbdc024'
HF_TOKEN = js.read(SETTINGS_PATH, 'WIDGETS.huggingface_token') or ''


# ===================== Helper Function ====================

# Logging function
def log_message(message, log=False):
    if log:
        print(f"{message}")

# Error handling decorator
def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_message(f"> \033[31m[Error]:\033[0m {e}", kwargs.get('log', False))
            return None
    return wrapper

def _handle_path_and_filename(parts, url, is_git=False):
    """Extract path and filename from parts."""
    path, filename = None, None

    if len(parts) >= 3:
        path = Path(parts[1]).expanduser()
        filename = parts[2]
    elif len(parts) == 2:
        arg = parts[1]
        if '/' in arg or arg.startswith('~'):
            path = Path(arg).expanduser()
        else:
            filename = arg

    if not is_git and 'drive.google.com' not in url:
        if filename and not Path(filename).suffix:
            url_ext = Path(urlparse(url).path).suffix
            if url_ext:
                filename += url_ext
            else:
                filename = None

    return path, filename

def is_github_url(url):
    """Check if the URL is a valid GitHub URL"""
    parsed = urlparse(url)
    return parsed.netloc in ('github.com', 'www.github.com')


# ======================== Download ========================

# Download function
@handle_errors
def m_download(line, log=False, unzip=False):
    """Download files from a comma-separated list of URLs or file paths."""
    links = [link.strip() for link in line.split(',') if link.strip()]

    if not links:
        log_message('> Missing URL, downloading nothing', log)
        return

    for link in links:
        url = link[0]
        if url.endswith('.txt') and Path(url).expanduser().is_file():
            with open(Path(url).expanduser(), 'r') as file:
                for line in file:
                    process_download(line, log, unzip)
        else:
            process_download(link, log, unzip)

@handle_errors
def process_download(line, log, unzip):
    """Process an individual download line."""
    parts = line.split()
    url = parts[0].replace('\\', '')
    url = clean_url(url)

    if not url:
        return

    path, filename = _handle_path_and_filename(parts, url)
    current_dir = Path.cwd()

    try:
        if path:
            path.mkdir(parents=True, exist_ok=True)
            CD(path)

        download_file(url, filename, log)
        if unzip and filename and filename.endswith('.zip'):
            unzip_file(filename, log)
    finally:
        CD(current_dir)

@handle_errors
def download_file(url, filename, log):
    """Download a file from various sources."""
    is_special_domain = any(domain in url for domain in ['civitai.com', 'huggingface.co', 'github.com'])

    if is_special_domain:
        download_with_aria2(url, filename, log)
    elif 'drive.google.com' in url:
        download_google_drive(url, filename, log)
    else:
        """Download using curl."""
        command = f"curl -#JL '{url}'"
        if filename:
            command += f" -o '{filename}'"
        execute_shell_command(command, log)

def download_with_aria2(url, filename, log):
    """Download using aria2c."""
    aria2_args = ('aria2c --header="User-Agent: Mozilla/5.0" --allow-overwrite=true --console-log-level=error --stderr=true -c -x16 -s16 -k1M -j5')

    if HF_TOKEN and 'huggingface.co' in url:
        aria2_args += f' --header="Authorization: Bearer {HF_TOKEN}"'

    command = f"{aria2_args} '{url}'"

    if not filename:
        filename = get_file_name(url)
    if filename:
        command += f" -o '{filename}'"

    monitor_aria2_download(command, log)

def download_google_drive(url, filename, log):
    """Download from Google Drive using gdown."""
    cmd = 'gdown --fuzzy ' + url
    if filename:
        cmd += ' -O ' + filename
    if 'drive.google.com/drive/folders' in url:
        cmd += ' --folder'

    execute_shell_command(cmd, log)

def get_file_name(url):
    """Get the file name based on the URL."""
    if any(domain in url for domain in ['civitai.com', 'drive.google.com']):
        return None
    else:
        return Path(urlparse(url).path).name

@handle_errors
def unzip_file(zip_filepath, log):
    """Extract the ZIP file."""
    with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
        zip_ref.extractall(Path(zip_filepath).parent)
    log_message(f">> Successfully unpacked: {zip_filepath}", log)

@handle_errors
def monitor_aria2_download(command, log):
    """Monitor aria2c download progress."""
    try:
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        error_codes, error_messages = [], []
        result = ''
        br = False

        while True:
            lines = process.stderr.readline()
            if lines == '' and process.poll() is not None:
                break

            if lines:
                result += lines
                for output_line in lines.splitlines():
                    handle_error_output(lines, error_codes, error_messages)

                    if re.match(r'\[#\w{6}\s.*\]', output_line):
                        formatted_line = format_output_line(output_line)
                        if log:
                            print(f"\r{' ' * 180}\r{formatted_line}", end='')
                            sys.stdout.flush()
                        br = True
                        break

        if log:
            for error in error_codes + error_messages:
                print(f"{error}")

            if br:
                print()

            stripe = result.find('======+====+===========')
            if stripe != -1:
                for line in result[stripe:].splitlines():
                    if '|' in line and 'OK' in line:
                        formatted_line = re.sub(r'(\|\s*)(OK)(\s*\|)', r'\1\033[32m\2\033[0m\3', line)
                        print(f"{formatted_line}")

        process.wait()
    except KeyboardInterrupt:
        log_message('\n> Download interrupted', log)

def format_output_line(line):
    """Format a line of output with ANSI color codes."""
    line = re.sub(r'\[', '\033[35m【\033[0m', line)
    line = re.sub(r'\]', '\033[35m】\033[0m', line)
    line = re.sub(r'(#)(\w+)', r'\1\033[32m\2\033[0m', line)
    line = re.sub(r'(\(\d+%\))', r'\033[36m\1\033[0m', line)
    line = re.sub(r'(CN:)(\d+)', r'\1\033[34m\2\033[0m', line)
    line = re.sub(r'(DL:)(\d+\w+)', r'\1\033[32m\2\033[0m', line)
    line = re.sub(r'(ETA:)(\d+\w+)', r'\1\033[33m\2\033[0m', line)
    return line

def handle_error_output(line, error_codes, error_messages):
    """Check and collect error messages from the output."""
    if 'errorCode' in line or 'Exception' in line:
        error_codes.append(line)
    if '|' in line and 'ERR' in line:
        formatted_line = re.sub(r'(\|\s*)(ERR)(\s*\|)', r'\1\033[31m\2\033[0m\3', line)
        error_messages.append(formatted_line)

@handle_errors
def execute_shell_command(command, log):
    """Execute a shell command and handle logging."""
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if log:
        for line in process.stderr:
            print(line, end='')
    process.wait()

@handle_errors
def clean_url(url):
    """Clean and format URLs to ensure correct access."""
    if 'civitai.com/models/' in url:
        api = CivitAiAPI(CAI_TOKEN)
        if not (data := api.validate_download(url)):
            return

        url = data.download_url

    elif 'huggingface.co' in url:
        if '/blob/' in url:
            url = url.replace('/blob/', '/resolve/')
        if '?' in url:
            url = url.split('?')[0]

    elif 'github.com' in url:
        if '/blob/' in url:
            url = url.replace('/blob/', '/raw/')

    return url


# ========================== Clone =========================

def m_clone(input_source, recursive=True, depth=1, log=False):
    """Main function to clone repositories"""
    sources = [link.strip() for link in input_source.split(',') if link.strip()]

    if not sources:
        log_message('>> No valid repositories to clone', log)
        return

    for source in sources:
        if source.endswith('.txt') and Path(source).expanduser().is_file():
            with open(Path(source).expanduser(), 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        process_clone(line.strip(), recursive, depth, log)
        else:
            process_clone(source, recursive, depth, log)

def process_clone(input_source, recursive, depth, log=False):
    parts = shlex.split(input_source)
    if not parts:
        log_message(">> \033[31m[Error]: Empty command\033[0m", log)
        return

    url = parts[0].replace('\\', '')
    if not url:
        log_message(f">> \033[31m[Error]:\033[0m Empty URL in command: {input_source}", log)
        return

    # Check if URL is a GitHub URL
    if not is_github_url(url):
        log_message(f">>  \033[33m[Warning]:\033[0m Not a GitHub URL - {url}", log)
        return

    path, repo_name = _handle_path_and_filename(parts, url, is_git=True)

    current_dir = Path.cwd()
    try:
        if path:
            path.mkdir(parents=True, exist_ok=True)
            CD(path)

        # Build a clone command
        command = build_git_command(url, repo_name, recursive, depth)
        execute_git_command(command, log)
    finally:
        CD(current_dir)

def build_git_command(url, repo_name, recursive, depth):
    """Build git clone command"""
    cmd = ['git', 'clone']

    if depth > 0:
        cmd.extend(['--depth', str(depth)])
    if recursive:
        cmd.append('--recursive')

    cmd.append(url)
    if repo_name:
        cmd.append(repo_name)

    return ' '.join(cmd)

@handle_errors
def execute_git_command(command, log=False):
    repo_url = re.search(r'https?://\S+', command).group()
    process = subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    repo_name = False
    while True:
        output = process.stdout.readline()
        if not output and process.poll() is not None:
            break

        output = output.strip()
        if not output:
            continue

        # Parse cloning progress
        if 'Cloning into' in output:
            repo_path = re.search(r"'(.+?)'", output).group(1)
            repo_name = '/'.join(repo_path.split('/')[-3:])
            log_message(f">> Cloning: \033[32m{repo_name}\033[0m -> {repo_url}", log)

        # Handle error messages
        if 'fatal' in output.lower():
            log_message(f">> \033[31m[Error]:\033[0m {output}", log)