# AnxLight Project Context (Brain Dump)

**Date of Last Update:** 2025-06-21 (Reflecting UI Script Refactors)

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
*   **Functionality (v3):** Defines Python constants for versions.
*   **Status:** Created and updated for v3 (SHA `96023add48...`).

### 2.3. Pre-Flight Setup Script (`scripts/pre_flight_setup.py`)
*   **Purpose:** Handles all heavy, one-time setup tasks, executed by Cell 1 of the launcher notebook.
*   **Functionality (v3 - v0.1.0, updated):**
    1.  Displays component versions.
    2.  Sets up Python Virtual Environment (VENV).
    3.  Installs core Python dependencies into VENV.
    4.  Checks for tunneling clients.
    5.  **Installs all supported WebUIs by iterating through and calling the refactored installer scripts in `scripts/UIs/`.**
*   **Status:** Updated to orchestrate all refactored UI installers (SHA `51e89acfb6...`).

### 2.4. Main Gradio Application (`scripts/main_gradio_app.py`)
*   **Purpose (v3 - v1.0.0):** Defines and runs the Gradio UI, manages session configuration, handles session-specific asset downloads, generates `anxlight_config.json`, and orchestrates `scripts/launch.py`.
*   **Status:** Refactored for v3 data handling and orchestration (SHA `6a6d6ef4...`).

### 2.5. Data Modules (`scripts/data/sd15_data.py`, `scripts/data/sdxl_data.py`)
*   **Purpose:** Consolidated data sources for SD1.5 and SDXL assets respectively.
*   **Status:** Updated to include LoRA data. `scripts/data/lora_data.py` is deprecated.

### 2.6. Inherited Backend (from `anxety-solo/sdAIgen`)
*   **`scripts/launch.py`:** Inherited. Responsible for reading `anxlight_config.json`, starting the WebUI process, and initiating tunnels via `modules/TunnelHub.py`.
*   **`modules/Manager.py`, `modules/webui_utils.py`, `modules/json_utils.py`, `modules/TunnelHub.py`:** Inherited core utilities, with some adaptations made for v3.
*   **`scripts/UIs/*.py`:** Inherited WebUI-specific installer scripts. **Initial refactoring pass is complete.** All scripts (`A1111.py`, `Classic.py`, `ComfyUI.py`, `Forge.py`, `ReForge.py`, `SD-UX.py`) have been modified to remove IPython dependencies and use standard `subprocess` calls, making them callable by `scripts/pre_flight_setup.py`.

## 3. Key UI/UX Decisions & Features Implemented/Planned (v3)
*   **Two-Cell Notebook Workflow:** Separates heavy setup (Cell 1) from interactive session launch (Cell 2).
*   **Centralized Versioning:** Via `scripts/anxlight_version.py`.
*   **Consolidated Data Modules:** Per SD version in `scripts/data/`.
*   **Session-Specific Asset Downloads:** `main_gradio_app.py` only downloads what's needed for the current run.
*   **Logging Strategy (v3 Plan):** Gradio UI to feature a \"Download Session Logs\" button.

## 4. Crucial Data Points & Information for Development
(Sections on WebUI args, Themes, Config Parameters, file.txt system remain relevant)

## 5. Known Issues / Current Workarounds
*   **`modules/Manager.py` `download_url_to_path`:** Needs thorough testing with all URL types and token scenarios. Its progress reporting for Gradio is a future enhancement.
*   **Data Module Content:** Accuracy of URLs and filenames in `sd15_data.py` and `sdxl_data.py` is crucial.
*   **UI-specific Configurations:** The `download_configuration()` functions within each `scripts/UIs/*.py` script use a generic list of extensions. These lists need to be reviewed and tailored for each specific WebUI for optimal compatibility (e.g., Forge has its own ADetailer, ReForge is deprecated, SD-UX plugin system is different).
*   **`SD-UX.py` Installation Method**: The true nature and correct installation process for "SD-UX" needs verification. The current zip-based install is a placeholder and may be incorrect if it refers to `Stability-AI/StableStudio`.

## 6. Immediate Next Steps
**Note:** The primary refactoring of `scripts/UIs/*.py` is complete. The focus now shifts to testing and integration.

1.  **Test `scripts/pre_flight_setup.py`:**
    *   Execute via Cell 1 of `notebook/AnxLight_Launcher_v0.0.5.ipynb`.
    *   Verify VENV creation, dependency installation, and successful execution of all `scripts/UIs/*.py` installers without errors. This is the top priority.
2.  **Full End-to-End Test of `AnxLight_Launcher_v0.0.5.ipynb`:**
    *   Run Cell 1 (Pre-Flight Setup).
    *   Run Cell 2 (Launch Gradio App).
    *   In Gradio UI: Select a variety of WebUIs (especially the newly refactored ones like Forge, ComfyUI) and assets.
    *   Click \"Download Assets & Launch WebUI\".
    *   Verify: Correct assets are downloaded, `anxlight_config.json` is generated correctly, and the selected WebUI starts successfully with its tunnel.
3.  **Data Module Accuracy:** Continuously verify and update URLs, filenames, and metadata in `scripts/data/sd15_data.py` and `scripts/data/sdxl_data.py`.
4.  **Implement \"Download Session Logs\" Feature:** Add the button to `main_gradio_app.py` and the backend logic to zip and serve logs.

## 7. Discussed Future Enhancements
(Content as in existing BrainDump.md - still relevant for post-v3 stability)

## 8. Project Documentation
(Content as in existing BrainDump.md - needs to emphasize v3 as current and ensure all local/repo docs are synced)