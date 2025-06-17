# AnxLight Project Context (Brain Dump)

**Date of Last Update:** 2025-06-19 (Corresponds to current AI session state)

## 1. Project Overview

*   **Project Name:** AnxLight
*   **Core Goal:** 
    *   To create a user-friendly and robust system for launching various Stable Diffusion WebUIs on Google Colab and other platforms. This involves integrating a modern Gradio-based user interface with the well-tested backend setup and launch mechanisms of the `anxety-solo/sdAIgen` project.
    *   **Multi-Platform Ambition:** The tool is intended to be adaptable for use across various environments, including Google Colab, Kaggle, cloud IDEs (e.g., Vast.ai, Lightning AI), and local setups, requiring flexible path and environment management.
*   **Base Repository (Forked From):** `anxety-solo/sdAIgen` (GitHub: `https://github.com/anxety-solo/sdAIgen`)
*   **Current Development Repository:** `drf0rk/AnxLight` (GitHub: `https://github.com/drf0rk/AnxLight`)
*   **Primary User Interface:** Gradio

### 1.1. Development Roadmap
*   A detailed, multi-phase development strategy, including long-term goals and specific implementation steps, is maintained in the `AnxLight_Development_Plan.md` file located in the root of the `drf0rk/AnxLight` repository. This plan should be consulted for an overview of the project's direction.

## 2. Current Architecture & Key Files

### 2.1. Colab Launcher (`AnxLight_Launcher.ipynb` - Conceptual Name)
*   **Purpose:** Single-cell Colab notebook to set up the environment and launch the Gradio application. Adaptable for other platform launchers.
*   **Functionality:**
    1.  Clones the `drf0rk/AnxLight` repository (targeting the `feature/backend-integration` branch for current development) or pulls the latest changes.
    2.  Installs necessary Python dependencies (primarily `gradio`).
    3.  Changes the working directory into the cloned repository (`PROJECT_ROOT`).
    4.  **Sets crucial environment variables** (`home_path`, `scr_path`, `settings_path`, `venv_path`) relative to `PROJECT_ROOT` to ensure inherited backend scripts can locate configurations and operate correctly across different platforms.
    5.  Uses `runpy.run_path('scripts/main_gradio_app.py', run_name=\"__main__\")` to execute the main Gradio application script.
*   **Note:** The notebook cell code is designed to be the primary entry point, preparing the environment for `main_gradio_app.py`.

### 2.2. Main Gradio Application (`scripts/main_gradio_app.py`)
*   **Purpose:** Defines and runs the entire Gradio user interface, collects user configurations, and orchestrates the backend processes, including preparing log directories and handling detailed logging.
*   **Current UI Elements & Functionality (Setup & Asset Selection Tab):**
    *   (UI elements as previously listed)
    *   `Detailed Download Log Checkbox`: This checkbox will control the verbosity of logging both to the UI's live log and to persistent log files.
*   (Event Handlers, Key Data Used, Recent Fix as previously listed)

### 2.3. Data Modules (`scripts/data/`)
(As previously listed)

### 2.4. Inherited Backend (from `anxety-solo/sdAIgen`)
(As previously listed, emphasizing reliance on env vars like `settings_path`)

## 3. Key UI/UX Decisions & Features Implemented
(As previously listed)
*   **Logging Strategy (Planned):**
    *   The \"Enable Detailed Download Log\" checkbox will gate verbose output.
    *   If checked, `main_gradio_app.py` will create a session-specific log directory (e.g., `PROJECT_ROOT/logs/session_<timestamp>/`).
    *   Backend script outputs (`downloading-en.py`, `launch.py`) will be streamed to the UI and also saved to separate files within this session log directory (e.g., `downloading.log`, `launch.log`).
    *   If unchecked, only summary status/errors will go to UI, but errors will still be logged to files.

## 4. Crucial Data Points & Information for Development

### 4.1. WebUI Default Arguments
(As previously listed)

### 4.2. Theme Choices
(As previously listed)

### 4.3. Backend Configuration Parameters (Guidance for Interfacing)
*   The original `anxety-solo/sdAIgen` project utilized a JSON configuration file to store user selections made via its IPython widget interface (`scripts/en/widgets-en.py`).
*   The path to this JSON configuration file was determined by an environment variable, `settings_path`, typically defined during the execution of `scripts/setup.py` in the main Colab notebook. Other related environment variables like `home_path` (e.g., `/root/ANXETY`) and `scr_path` (e.g., path to the cloned repository scripts) were also set up similarly. These paths are crucial for multi-platform adaptability.
*   The `scripts/en/widgets-en.py` script would then use `modules/json_utils.py` to read from and save to the file at `settings_path`, storing configurations typically under a top-level `\"WIDGETS\"` key and an `\"ENVIRONMENT\"` key.
*   The backend scripts (`scripts/en/downloading-en.py`, `scripts/launch.py`) would subsequently read this same configuration file to perform their operations.
*   The `SETTINGS_KEYS` list, identified from `scripts/en/widgets-en.py`, represents the keys used within the `\"WIDGETS\"` section of this JSON configuration structure:
    ```python
    SETTINGS_KEYS = [
        'XL_models', 'model', 'model_num', 'inpainting_model', 'vae', 'vae_num',
        'latest_webui', 'latest_extensions', 'check_custom_nodes_deps', 'change_webui', 'detailed_download', # 'detailed_download' here refers to original's log level, AnxLight reuses the flag for its own comprehensive logging.
        'controlnet', 'controlnet_num', 'commit_hash',
        'civitai_token', 'huggingface_token', 'zrok_token', 'ngrok_token', 'commandline_arguments', 'theme_accent',
        'empowerment', 'empowerment_output',
        'Model_url', 'Vae_url', 'LoRA_url', 'Embedding_url', 'Extensions_url', 'ADetailer_url',
        'custom_file_urls'
    ]
    ```
*   **AnxLight's Interfacing Strategy:** AnxLight will adopt a similar approach. Its `scripts/main_gradio_app.py` will collect user configurations from the Gradio UI and generate a JSON file (e.g., `anxlight_config.json` at the path defined by `os.environ['settings_path']`). This file will be structured to be compatible with the expectations of the inherited backend scripts, using `SETTINGS_KEYS` for the `\"WIDGETS\"` section and also creating an `\"ENVIRONMENT\"` section. The AnxLight platform launcher (e.g., `AnxLight_Launcher.ipynb`) is responsible for setting up the `settings_path`, `home_path`, and `scr_path` environment variables appropriately for the target platform before `main_gradio_app.py` is run.

### 4.4. `file.txt` Download System (from Original Repo)
(As previously listed)

## 5. Known Issues / Current Workarounds
(As previously listed, with successful SHA mismatch test noted)

## 6. Immediate Next Steps (Detailed Development Plan)

**Note:** The following steps are part of Phase 1 of the strategy outlined in `AnxLight_Development_Plan.md`. The multi-platform goal and detailed logging strategy should be incorporated from the outset.

The primary focus is to make the \"Install, Download & Launch\" button functional by implementing configuration passing to the backend scripts (via AnxLight-generated `anxlight_config.json`) and backend script execution within `launch_anxlight_main_process` in `scripts/main_gradio_app.py`.

### 6.1. Implement AnxLight Configuration Handling & Logging Setup

**Context:** The original `anxety-solo/sdAIgen` project used a JSON file (path from `settings_path` env var) for configuration. AnxLight emulates this. The \"Enable Detailed Download Log\" checkbox will control UI and file logging verbosity.

1.  **Platform-Agnostic Environment Variable Strategy (Launcher Responsibility):**
    *   The platform launcher (e.g., `AnxLight_Launcher.ipynb`) must define `PROJECT_ROOT`.
    *   It must set `os.environ['home_path'] = PROJECT_ROOT` (or a dedicated `./runtime_env/` within `PROJECT_ROOT`).
    *   It must set `os.environ['scr_path'] = PROJECT_ROOT`.
    *   It must set `os.environ['settings_path'] = os.path.join(os.environ['home_path'], 'anxlight_config.json')`.
    *   It must set `os.environ['venv_path'] = os.path.join(PROJECT_ROOT, 'venv')` (or platform-appropriate path).
    *   This setup is crucial for backend scripts to find configurations and operate correctly across different platforms.

2.  **Log Directory Setup (in `launch_anxlight_main_process`):**
    *   At the beginning of `launch_anxlight_main_process` in `main_gradio_app.py`:
        *   If `detailed_download_chk.value` is True:
            *   Create a unique session log directory: `log_session_dir = os.path.join(PROJECT_ROOT, 'logs', f'session_{time.strftime(\"%Y%m%d-%H%M%S\")}')`.
            *   `os.makedirs(log_session_dir, exist_ok=True)`.
            *   Store `log_session_dir` for use by subprocess loggers.
        *   Else: Set `log_session_dir = None`.

3.  **Collect UI Data & Construct Configuration Dictionary (in `launch_anxlight_main_process`):**
    *   Retrieve values from all Gradio inputs.
    *   Create `widgets_data = {}` mapping Gradio inputs to `SETTINGS_KEYS`.
    *   Create `environment_data = {}` with `env_name` (e.g., \"AnxLight_Gradio_Colab\"), `lang`, and paths from `os.environ`.
    *   `anxlight_config = {\"WIDGETS\": widgets_data, \"ENVIRONMENT\": environment_data}`.

4.  **Save AnxLight's JSON Configuration File (in `launch_anxlight_main_process`):**
    *   `config_file_path = os.environ['settings_path']`.
    *   `os.makedirs(os.path.dirname(config_file_path), exist_ok=True)`.
    *   Save `anxlight_config` to `config_file_path` using `json.dump()`.
    *   Log action to UI (e.g., \"Configuration saved to anxlight_config.json\").

5.  **Adapt `update_current_webui` Call (in `launch_anxlight_main_process`):**
    *   Call `modules.webui_utils.update_current_webui(webui_choice_dd.value)`. This function is expected to read `settings_path` and update the config file directly.

### 6.2. Implement Backend Script Execution (in `launch_anxlight_main_process`)

1.  **Define Script Paths:** (Using `os.environ['scr_path']`)
    *   `downloading_script = os.path.join(os.environ['scr_path'], 'scripts', 'en', 'downloading-en.py')`
    *   `launch_script = os.path.join(os.environ['scr_path'], 'scripts', 'launch.py')`

2.  **Helper Function for Subprocess Execution & Logging:**
    *   Create a helper function, e.g., `execute_backend_script(script_path, log_file_name, ui_log_prefix, detailed_logging_enabled, log_session_dir)`:
        *   Takes script path, base name for its log file, UI prefix, detailed log flag, and session log directory.
        *   Uses `subprocess.Popen` with `env=os.environ`.
        *   If `detailed_logging_enabled` and `log_session_dir` is not None:
            *   Opens `os.path.join(log_session_dir, log_file_name)` in append mode.
            *   Streams all `stdout`/`stderr` lines to UI (with prefix) AND writes them to the log file.
        *   Else (summary logging):
            *   Streams selected status updates or just final status/errors to UI.
            *   Still logs full `stderr` to a generic error log or the specific file if `log_session_dir` exists.
        *   Waits for process completion and returns `process.returncode`.

3.  **Execute `downloading-en.py`:**
    *   Call the helper function: `ret_code = execute_backend_script(downloading_script, \"downloading.log\", \"[Downloader]\", detailed_download_chk.value, log_session_dir_from_step_6_1_2)`.
    *   If `ret_code != 0`, handle error and yield message to UI, then return.

4.  **Execute `launch.py` (if download successful):**
    *   Call the helper function: `execute_backend_script(launch_script, \"launch.log\", \"[Launcher]\", detailed_download_chk.value, log_session_dir_from_step_6_1_2)`.

This detailed breakdown for Section 6 should provide excellent guidance for the next coding phase, incorporating the multi-platform and detailed logging requirements.

## 7. Discussed Future Enhancements
(Content as before, with understanding that these are post-Phase 1/2 as per `AnxLight_Development_Plan.md`)

## 8. Project Documentation
(Content as before, now also implicitly includes `AnxLight_Development_Plan.md`)

This summary should provide a solid foundation for any future work or for a new assistant instance.