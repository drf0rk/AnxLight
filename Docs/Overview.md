# AnxLight Project Documentation

## 1. Project Overview (As of YYYY-MM-DD_v3_ARCHITECTURE)

**Project: AnxLight**
*   **Base Repository:** Fork of `anxety-solo/sdAIgen`.
*   **Core Goal:** 
    *   To integrate a modern Gradio-based user interface with the robust backend setup and launch mechanisms of the `anxety-solo/sdAIgen` project.
    *   To provide a user-friendly way to configure, download assets for, and launch various Stable Diffusion WebUIs and related tools.
    *   **Multi-Platform Support:** A key objective is to ensure AnxLight is adaptable for use across diverse environments, including Google Colab, Kaggle, cloud platforms, and local setups.
*   **Development Plan:** The primary, most current*   **Base Repository:** Fork of `anxety-solo/sdAIgen`.
*   **Core Goal:** 
    *   To integrate a modern Gradio-based user interface with the robust backend setup and launch mechanisms of the `anxety-solo/sdAIgen` project.
    *   To provide a user-friendly way to configure, download assets for, and launch various Stable Diffusion WebUIs and related tools.
    *   **Multi-Platform Support:** A key objective is to ensure AnxLight is adaptable for use across diverse environments, including Google Colab, Kaggle, cloud platforms, and local setups.
*   **Development Plan:** The primary, continuously updated roadmap is `AnxLight_Development_Plan.md` (in the repository root). The current major effort is the **v3 Architecture refactor**.
*   **Architecture (Current v3 Implementation Phase):**
    *   **Platform Entry Point (`notebook/AnxLight_Launcher_v0.0.5.ipynb`):** A versioned, two-cell Colab notebook.
        *   **Cell 1 (Pre-Flight Setup):** Clones/updates the AnxLight repo, then executes `scripts/pre_flight_setup.py`.
        *   **Cell 2 (Gradio UI & Launch):** Sets environment variables and executes `scripts/main_gradio_app.py` using the VENV Python.
    *   **Versioning Script (`scripts/anxlight_version.py`):** Centralizes version numbers for components (e.g., `MAIN_GRADIO_APP_VERSION = "1.0.0"`, `ANXLIGHT_OVERALL_SYSTEM_VERSION = "3.0 development strategy is the user-provided "v3 Architecture Plan" and the evolving `AnxLight_Development_Plan.md` (located in the root of the `drf0rk/AnxLight` repository).
*   **Architecture (Current v3 Implementation Phase):**
    *   **Platform Entry Point (`notebook/AnxLight_Launcher_v0.0.5.ipynb`):** A versioned, two-cell Colab notebook.
        *   Cell 1: Clones/updates the AnxLight repo and executes `scripts/pre_flight_setup.py` for all heavy initial setup (VENV, dependencies, WebUI installations).
        *   Cell 2: Sets environment variables and executes `scripts/main_gradio_app.py` (using VENV Python) to launch the Gradio UI.
    *   **Versioning Script (`scripts/anxlight_version.py`):** Centralizes version numbers for key components (e.g., `MAIN_GRADIO_APP_VERSION = "1.0.0"`, `ANXLIGHT_OVERALL_SYSTEM_VERSION = "3.0.0-alpha"`).
    *   **Pre-Flight Setup (`scripts/pre_flight_setup.py` - v0.1.0):** Handles one-time environment preparation: VENV, core dependencies, tunneling clients, and installation of all supported WebUIs (by calling `scripts/UIs/*.py`).
    *   **Gradio UI & Orchestration (`scripts/main_gradio_app.py` - v1.0.0):** 
        *   Provides the Gradio user interface.
        *   Imports asset data from consolidated `scripts/data/sd15_data.py` and `scripts/data/sdxl_data.py`.
        *   Handles session-specific asset downloads (models, VAEs, LoRAs, etc.) using `modules/Manager.py`.
.0-alpha"`).
    *   **Pre-Flight Setup Script (`scripts/pre_flight_setup.py` - v0.1.0):** Handles all one-time heavy installations: VENV creation, core dependencies, tunneling clients, and all supported WebUIs (via `scripts/UIs/*.py`).
    *   **Gradio UI & Orchestration (`scripts/main_gradio_app.py` - v1.0.0):** 
        *   Provides the Gradio user interface.
        *   Dynamically loads asset data from `scripts/data/sd15_data.py` or `scripts/data/sdxl_data.py`.
        *   Manages session-specific asset downloads using `modules/Manager.py` (via `download_url_to_path`).
        *   Generates `anxlight_config.json`.
        *   Orchestrates `scripts/launch.py` for WebUI startup and tunneling.
    *   **Data Modules (`scripts/data/sd15_data.py`, `scripts/data/sdxl_data.py`):** Consolidated data sources for SD1.5 and SDXL assets respectively, including models, VAEs, ControlNets, and LoRAs.
    *   **Backend (Adapted from `anxety-solo/sdAIgen`):** 
        *   `scripts/launch.py`: Inherited for WebUI execution and tunneling.
        *   `modules/Manager.py`: Inherited and refactored for v3 (added `download_url_to_path`).
        *   `modules/webui_utils.py`: Inherited and refactored for v3 (added `get_webui_asset_path`, `get_webui_installation_root`).
        *   `modules/TunnelHub.py`, `modules/json_utils.py`, `modules/CivitaiAPI.py`: Inherited and utilized.
        *   `scripts/UIs/A1111.py` (and others): Inherited, but **require refactoring** to remove IPython dependencies for compatibility with `pre_flight        *   Generates `anxlight_config.json`.
        *   Orchestrates `scripts/launch.py` for WebUI startup and tunneling.
    *   **Data Modules (`scripts/data/sd15_data.py`, `scripts/data/sdxl_data.py`):** Consolidated data sources for SD1.5 and SDXL assets respectively, including models, VAEs, ControlNets, and LoRAs.
    *   **Backend (Adapted from `anxety-solo/sdAIgen`):** 
        *   `scripts/launch.py`: Inherited for WebUI execution and tunneling (via `modules/TunnelHub.py`).
        *   `modules/Manager.py`: Inherited and refactored (e.g., `download_url_to_path`) for downloads.
        *   `modules/webui_utils.py`: Inherited and refactored (e.g., `get_webui_asset_path`) for path management.
        *   `scripts/UIs/A1111.py` (and others): Inherited WebUI installers, **requiring refactor** to remove IPython calls for compatibility with `pre_flight_setup.py`.
        *   `scripts/en/downloading-en.py`: Role significantly reduced/deprecated in v3.
*   **Key Features (v3 Plan):** Two-cell notebook, centralized pre-flight setup, robust versioning, Gradio UI, session-specific asset downloads, live log streaming, multi-platform support, planned "Download Session Logs" feature.

---

## 2. File Descriptions (As of YYYY-MM-DD_v3_ARCHITECTURE)

- **`notebook/AnxLight_Launcher_v0.0.5.ipynb` (SHA `ef26a601bf51...` - v3 Launcher):**
    - User's primary entry point, implementing the v3 two-cell architecture.
    - **Cell 1:** Clones/updates repo, executes `scripts/pre_flight_setup.py`.
    - **Cell 2:** Sets environment, executes `scripts/main_gradio_app.py` using VENV Python.
    - **Status:** Updated to v3 structure. `ANXLIGHT_LAUNCHER_setup.py`.
        *   `scripts/en/downloading-en.py`: Role significantly reduced/deprecated in v3.
*   **Key Features (v3 Plan):** Two-cell notebook, centralized pre-flight setup, robust versioning, Gradio UI, session-specific asset downloads, live log streaming, multi-platform support, planned log download feature.

---

## 2. File Descriptions (As of YYYY-MM-DD_V3_UPDATE_DATE)

- **`notebook/AnxLight_Launcher_v0.0.5.ipynb` (SHA `ef26a601bf51...` - v3 Launcher):**
    - User's primary entry point, implementing the v3 two-cell architecture.
    - **Cell 1:** Clones/updates repo, executes `scripts/pre_flight_setup.py`.
    - **Cell 2:** Sets environment and executes `scripts/main_gradio_app.py` using VENV Python.
    - **Status:** Updated for v3. `ANXLIGHT_LAUNCHER_NOTEBOOK_VERSION` in `anxlight_version.py` is "0.0.5".

- **`scripts/anxlight_version.py` (SHA `96023add48...` - v3 Versioning):**
    - Central source for component version strings.
    - **Status:** Contains `MAIN_GRADIO_APP_VERSION = "1.0.0"`, `PRE_FLIGHT_SETUP_PY_VERSION = "0.1.0"`, etc.

- **`scripts/pre_flight_setup.py` (SHA `dd199d24...` - v3 Pre-Flight Setup v0.1.0):**
    - Handles all one-time heavy installations (VENV, dependencies, WebUIs via `scripts/UIs/*`, tunneling clients). Executed by Launcher Cell 1.
    - **Status:** Initial v3 version created.

- **`scripts/main_gradio_app.py` (SHA `6a6d6ef4...` - v3 Gradio App v1.0.0):**
    - Core Gradio application for v3.
    - **Responsibilities:** UI, dynamic data loading from `scripts/data/*_data.py`, session asset downloads (via `modules/Manager.py`), `anxlight_config.json` generation, `scripts/launch.py` orchestration._NOTEBOOK_VERSION = "0.0.5"` in `anxlight_version.py`.

- **`scripts/anxlight_version.py` (SHA `96023add48...` - v3 Versioning):**
    - Central source for component version strings.
    - **Status:** Contains `MAIN_GRADIO_APP_VERSION = "1.0.0"`, `PRE_FLIGHT_SETUP_PY_VERSION = "0.1.0"`, etc.

- **`scripts/pre_flight_setup.py` (SHA `dd199d24...` - v3 Pre-Flight Setup v0.1.0):**
    - Handles all initial heavy setup: VENV, dependencies, tunneling clients, all WebUI installations. Executed by Launcher Cell 1.
    - **Status:** Initial v3 version created.

- **`scripts/main_gradio_app.py` (SHA `6a6d6ef4...` - Gradio App v1.0.0 - v3 Refactor):**
    - Core Gradio application.
    - **Responsibilities (v3):** UI, dynamic data loading from `sd15_data.py`/`sdxl_data.py`, session asset downloads (via `Manager.py`), `anxlight_config.json` generation, `launch.py` orchestration.
    - **Status:** Refactored for v3 data handling and orchestration.

- **`scripts/data/sd15_data.py` (SHA `4145395e...` - SD1.5 Assets):**
    - Consolidated data for SD1.5 models, VAEs, ControlNets, and LoRAs.
    - **Status:** Updated to include LoRA data.

- **`scripts/data/sdxl_data.py` (SHA `035041c9...` - SDXL Assets):**
    - Consolidated data for SDXL models, VAEs, ControlNets, and LoRAs.
    - **Status:** Updated to include LoRA data.

- **`scripts/data/lora_data.py` (Deprecated):**
    - Formerly held LoRA data. Contents merged into `sd15_data.py` and `sdxl_data.py`.
    - **Status:** Deprecated.

- **`scripts/launch.py` (Inherited):**
    - Handles actual WebUI process startup and tunneling via `modules/TunnelHub.py`. Reads `anxlight_config.json`.
    - **Status:** Largely unchanged from `anxety-solo/sdAIgen` but its successful operation depends on correct v3 config and environment.

- **`modules/Manager.py` (
    - **Status:** Refactored for v3 orchestration and data handling.

- **`scripts/data/sd15_data.py` (SHA `4145395e...` - SD1.5 Assets):**
    - Consolidated data for SD1.5 models, VAEs, ControlNets, and LoRAs.
    - **Status:** Updated to include LoRA data.

- **`scripts/data/sdxl_data.py` (SHA `035041c9...` - SDXL Assets):**
    - Consolidated data for SDXL models, VAEs, ControlNets, and LoRAs.
    - **Status:** Updated to include LoRA data.

- **`scripts/data/lora_data.py` (SHA `168aa516...` - Deprecated):**
    - Formerly contained LoRA definitions.
    - **Status:** Deprecated; content merged into `sd15_data.py` and `sdxl_data.py`.

- **`AnxLight_Development_Plan.md` (In Repository Root):** Primary detailed roadmap.

- **`scripts/launch.py` (Inherited):** Handles actual WebUI process startup and tunneling via `modules/TunnelHub.py`. Reads `anxlight_config.json`.

- **`modules/Manager.py` (SHA `42186db2...` - Refactored for v3):**
    - Core download utility. V3 added `download_url_to_path()` for direct path downloads. Retains multi-source download capabilities and token handling.

- **`modules/webui_utils.py` (SHA `64030407...` - Refactored for v3):**
    - Manages WebUI-specific file paths. V3 added `get_webui_asset_path()` and `get_webui_installation_root()`. `_set_webui_paths()` populates config.

- **`scripts/en/downloading-en.py` (Inherited - Role Reduced):**
    - Original script for downloads and setup. Its primary setup role is superseded by `pre_flight_setup.py` and `main_gradio_app.py` in v3.

- **`scripts/UIs/A1111.py` (Inherited - Requires Refactor):**
    - Setup script for A1111 WebUI.
    - **Known Issue:** Contains IPython calls; needs refactor to standard Python for `pre_flight_setup.py`.

(Older file entries can be removed or marked as pre-v3 if they are no longer relevant or have been significantly replaced)

---

## 3. Changelog
(This section contains historical changes and should be preserved. New entries are added to LightDoc.md)

### 2025-06-19 (Manual Update of main_gradio_app.py to v0.0.7 for Robust Path/Dummy Handling)
... (rest of existing changelog) ...

---

## 4. Assistant's Diary
(This section contains historical diary entries and should be preserved. New entries are added to LightDoc.md)

### 2025-06-19 (Correcting Documentation and Planning Next Steps for Notebook/A1111.py)
... (rest of existing diary) ...