# AnxLight Project Context (Brain Dump)

**Date of Last Update:** YYYY-MM-DD (Reflecting v3 Architecture Implementation)

## 1. Project Overview

*   **Project Name:** AnxLight
*   **Core Goal:** 
    *   To create a user-friendly and robust system for launching various Stable Diffusion WebUIs on Google Colab and other platforms. This involves integrating a modern Gradio-based user interface with the well-tested backend setup and launch mechanisms of the `anxety-solo/sdAIgen` project.
    *   The current development is focused on implementing the **v3 Architecture Plan**, which emphasizes a two-cell notebook structure for improved setup and launch reliability.
    *   **Multi-Platform Ambition:** The tool is intended to be adaptable for use across various environments, including Google Colab, Kaggle, cloud IDEs (e.g., Vast.ai, Lightning AI), and local setups, requiring flexible path and environment management.
*   **Base Repository (Forked From):** `anxety-solo/sdAIgen` (GitHub: `https://github.com/anxety-solo/sdAIgen`)
*   **Current Development Repository:** `drf0rk/AnxLight` (GitHub: `https://github.com/drf0rk/AnxLight`)
*   **Primary User Interface:** Gradio
*   **Language Focus**: Development should prioritize English-language versions of components (e.g., `*-en.py` files) or create new language-agnostic components. Russian-specific files (e.g., `widgets-ru.py`, `downloading-ru.py`) from the original `anxety-solo/sdAIgen` repository should be ignored and are not part of AnxLight's scope.

### 1.1. Development Roadmap
*   A detailed, multi-phase development strategy, including long-term goals and specific implementation steps, is maintained in the `AnxLight_Development_Plan.md` file located in the root of the `drf0rk/AnxLight` repository. The user-provided \"v3 Architecture Plan\" currently guides detailed implementation.

## 2. Current Architecture & Key Files (v3 Implementation)

### 2.1. Platform Launcher (`notebook/AnxLight_Launcher_v0.0.5.ipynb`)
*   **Purpose:** User's primary entry point (e.g., on Colab). Implements the v3 two-cell architecture.
*   **Functionality (v3):**
    1.  **Cell 1 (Pre-Flight Setup):** Clones/updates the `drf0rk/AnxLight` repository (main branch), changes CWD to repo root, then executes `scripts/pre_flight_setup.py`.
    2.  **Cell 2 (Gradio UI & Launch):** Sets crucial environment variables (`PROJECT_ROOT`, `home_path`, `scr_path`, `settings_path`, `venv_path`, `PYTHONPATH`) and executes `scripts/main_gradio_app.py` using the Python interpreter from the VENV created by Cell 1.
*   **Status:** Structure updated to v3 plan (SHA `ef26a601bf51...`).

### 2.2. Versioning Script (`scripts/anxlight_version.py`)
*   **Purpose:** Centralized source of truth for component versions within the AnxLight project.
*   **Functionality (v3):** Defines Python constants for versions (e.g., `MAIN_GRADIO_APP_VERSION = \"1.0.0\"`, `PRE_FLIGHT_SETUP_PY_VERSION = \"0.1.0\"`, `ANXLIGHT_OVERALL_SYSTEM_VERSION = \"3.0.0-alpha\"`).
*   **Status:** Created and updated for v3 (SHA `96023add48...`).

### 2.3. Pre-Flight Setup Script (`scripts/pre_flight_setup.py`)
*   **Purpose:** Handles all heavy, one-time setup tasks, executed by Cell 1 of the launcher notebook.
*   **Functionality (v3 - v0.1.0):**
    1.  Displays component versions (from `anxlight_version.py`).
    2.  Creates/activates a Python Virtual Environment (VENV).
    3.  Installs core Python dependencies (Gradio, pyngrok, huggingface-hub, etc.) into the VENV.
    4.  Checks for and attempts to install supported tunneling clients.
    5.  Installs all supported WebUIs by calling their respective setup scripts from `scripts/UIs/` (e.g., `A1111.py` - once refactored).
*   **Status:** Initial version created for v3 (SHA `dd199d24...`).

### 2.4. Main Gradio Application (`scripts/main_gradio_app.py`)
*   **Purpose (v3 - v1.0.0):** Defines and runs the Gradio UI, manages session configuration, handles session-specific asset downloads, generates `anxlight_config.json`, and orchestrates `scripts/launch.py`.
*   **Functionality (v3):**
    1.  Imports versions from `anxlight_version.py`.
    2.  Dynamically loads asset data (models, VAEs, ControlNets, LoRAs) from `scripts/data/sd15_data.py` or `scripts/data/sdxl_data.py` based on selected SD version.
    3.  `get_asset_choices`: Populates UI selectors.
    4.  `download_selected_asset`: Downloads user-selected assets for the current session using `modules/Manager.py` (via `download_url_to_path`) and `modules/webui_utils.py` (for paths).
    5.  Generates `anxlight_config.json`.
    6.  Calls `scripts/launch.py` for WebUI and tunnel startup.
    7.  Streams logs to UI.
*   **Status:** Refactored for v3 data handling and orchestration (SHA `6a6d6ef4...`). Relies on functional `Manager.py` and `webui_utils.py` for downloads.

### 2.5. Data Modules (`scripts/data/sd15_data.py`, `scripts/data/sdxl_data.py`)
*   **Purpose:** Consolidated data sources for SD1.5 and SDXL assets respectively.
*   **Functionality (v3):** Each file exports Python dictionaries (e.g., `sd15_model_data`, `sd15_vae_data`, `sd15_controlnet_data`, `sd15_lora_data`) containing asset metadata (display names, URLs, target filenames, inpainting flags).
*   **Status:** Updated to include LoRA data. `scripts/data/lora_data.py` is now deprecated.
    *   `sd15_data.py` SHA: `4145395e...`
    *   `sdxl_data.py` SHA: `035041c9...`

### 2.6. Inherited Backend (from `anxety-solo/sdAIgen`)
*   **`scripts/launch.py`:** Inherited. Responsible for reading `anxlight_config.json`, starting the WebUI process, and initiating tunnels via `modules/TunnelHub.py`.
*   **`modules/Manager.py` (SHA `42186db2...`):** Inherited, then refactored for v3.
    *   Core download utility. V3 added `download_url_to_path(url, target_full_path, ...)` which accepts absolute paths, handles directory creation, and aims for clear boolean success/failure.
    *   Retains `clean_url` (for HF, Civitai, GitHub URL processing) and multi-tool download logic (`aria2c`, `gdown`, `curl`). Handles `HF_TOKEN`, `CAI_TOKEN`.
*   **`modules/webui_utils.py` (SHA `64030407...`):** Inherited, then refactored for v3.
    *   Manages WebUI-specific paths. `_set_webui_paths` populates `anxlight_config.json` with directory structures.
    *   V3 added `get_webui_asset_path(...)` (reads from config to provide full asset save paths) and `get_webui_installation_root(...)`.
*   **`modules/json_utils.py`:** Inherited utility for JSON read/write operations, used for `anxlight_config.json`.
*   **`modules/TunnelHub.py`:** Inherited. Manages various tunneling services.
*   **`scripts/UIs/*.py` (e.g., `A1111.py`):** Inherited WebUI-specific installer scripts. **Crucially, these need refactoring to remove IPython dependencies to be callable by `scripts/pre_flight_setup.py`.**

## 3. Key UI/UX Decisions & Features Implemented/Planned (v3)
*   **Two-Cell Notebook Workflow:** Separates heavy setup (Cell 1) from interactive session launch (Cell 2).
*   **Centralized Versioning:** Via `scripts/anxlight_version.py`.
*   **Consolidated Data Modules:** Per SD version in `scripts/data/`.
*   **Session-Specific Asset Downloads:** `main_gradio_app.py` only downloads what's needed for the current run.
*   **Logging Strategy (v3 Plan):** Gradio UI to feature a \"Download Session Logs\" button. Detailed logs from `main_gradio_app.py` and backend scripts (like `launch.py`) are saved to a session-specific directory if \"Detailed Session Log\" is enabled.

## 4. Crucial Data Points & Information for Development

### 4.1. WebUI Default Arguments
(Content as in existing BrainDump.md - still relevant)

### 4.2. Theme Choices
(Content as in existing BrainDump.md - still relevant)

### 4.3. Backend Configuration Parameters (`anxlight_config.json`)
*   Still generated by `scripts/main_gradio_app.py` (path from `settings_path` env var).
*   `SETTINGS_KEYS` list (from original `widgets-en.py`) remains a useful reference for keys expected by `scripts/launch.py` and other backend components. `main_gradio_app.py` populates these.
*   The `ENVIRONMENT` section (with `home_path`, `scr_path`, etc.) is set up by the launcher notebook and used by scripts.
*   The `UI_SELECTION` key (with `webui_choice`) is used by `main_gradio_app.py` and `webui_utils.py`.
*   The `WEBUI` key is populated by `webui_utils._set_webui_paths()` with specific directory paths for the chosen WebUI, which `webui_utils.get_webui_asset_path()` then reads.

### 4.4. `file.txt` Download System (from Original Repo)
*   `modules/Manager.py` (`m_download` function) retains the ability to read a `.txt` file containing multiple URLs for batch downloading. This is less central to the Gradio UI flow but remains an underlying capability of `Manager.py`.

## 5. Known Issues / Current Workarounds (Post v3 Initial Implementation)
*   **`scripts/UIs/A1111.py` (and other UI installers):** Requires refactoring to remove IPython-specific calls to be compatible with `scripts/pre_flight_setup.py`. This is a critical pending task.
*   **`modules/Manager.py` `download_url_to_path`:** Needs thorough testing with all URL types and token scenarios. Its progress reporting for Gradio is a future enhancement.
*   **Data Module Content:** Accuracy of URLs and filenames in `sd15_data.py` and `sdxl_data.py` is crucial. Consistent use of `inpainting: True` flag for models needed for UI filter. Handling of ControlNet model+YAML pairs in `download_selected_asset` needs to ensure both are fetched if listed.

## 6. Immediate Next Steps (Post Initial v3 File Setup)
**Note:** This section is revised for the current v3 context, superseding older \"Next Steps\" detailed in previous versions of this document. The primary focus is achieving full functionality of the v3 architecture. Refer to `AnxLight_Development_Plan.md` (root) for the broader roadmap.

1.  **Refactor `scripts/UIs/A1111.py`:**
    *   Remove IPython dependencies (`get_ipython().system`, `!`).
    *   Replace with standard `subprocess.run()` calls.
    *   Ensure it can be executed as a standalone Python script by `scripts/pre_flight_setup.py` to install A1111 WebUI correctly into the VENV.
2.  **Test `scripts/pre_flight_setup.py`:**
    *   Execute via Cell 1 of `notebook/AnxLight_Launcher_v0.0.5.ipynb`.
    *   Verify VENV creation, dependency installation, and successful installation of at least one WebUI (e.g., A1111 after its refactor).
3.  **Thoroughly Test `modules/Manager.py`'s `download_url_to_path`:**
    *   Create test cases or use `main_gradio_app.py` to test downloads of various asset types from different sources (HTTP, HF, Civitai), ensuring token usage and filename handling (especially for ControlNet YAMLs if `main_gradio_app.py` lists them) work correctly.
    *   Confirm clear True/False return values.
4.  **Full End-to-End Test of `AnxLight_Launcher_v0.0.5.ipynb`:**
    *   Run Cell 1 (Pre-Flight Setup).
    *   Run Cell 2 (Launch Gradio App).
    *   In Gradio UI: Select WebUI, SD Version, and various assets (models, VAEs, LoRAs, ControlNets).
    *   Click \"Download Assets & Launch WebUI\".
    *   Verify:
        *   Correct assets are downloaded by `main_gradio_app.py` (via `Manager.py`) to the correct locations (determined by `webui_utils.py`).
        *   `anxlight_config.json` is generated correctly.
        *   `scripts/launch.py` starts the WebUI and tunnel successfully.
5.  **Implement \"Download Session Logs\" Feature:** Add the button to `main_gradio_app.py` and the backend logic to zip and serve logs from the `log_session_dir`.
6.  **Data Module Accuracy:** Continuously verify and update URLs, filenames, and metadata in `scripts/data/sd15_data.py` and `scripts/data/sdxl_data.py`.

## 7. Discussed Future Enhancements
(Content as in existing BrainDump.md - still relevant for post-v3 stability)

## 8. Project Documentation
(Content as in existing BrainDump.md - needs to emphasize v3 as current and ensure all local/repo docs are synced)