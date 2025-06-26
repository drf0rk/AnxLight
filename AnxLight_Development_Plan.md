# AnxLight Development Plan

**Date of Last Update:** 2025-06-19 (Corresponds to current AI session state)

## 0. Guiding Principles

1.  **Multi-Platform First:** AnxLight is envisioned as a tool for various platforms (Google Colab, Kaggle, Vast.ai, Lightning AI, local setups). Path management, environment detection, and configuration must be designed with this flexibility in mind, avoiding hardcoding specific to one platform.
2.  **Emulate Original Configuration Flow (Loosely):** AnxLight's Gradio UI (`main_gradio_app.py`) will generate a JSON configuration file (e.g., `anxlight_config.json`). The AnxLight Colab/platform launcher will set environment variables (e.g., `settings_path`, `home_path`, `scr_path`) so inherited backend scripts can read this configuration.
3.  **Minimize Modifications to Inherited Backend:** Treat inherited scripts from `anxety-solo/sdAIgen` as semi-black boxes. Prefer wrappers or environment management over direct, extensive modifications.
4.  **Modularity for Future Enhancements:** New, significant features (e.g., advanced model downloaders, new application UIs like Fooocus) will be developed as modular components, primarily within AnxLight-specific files, to be integrated last, after core functionality is stable.
5.  **Comprehensive Logging:** Implement robust logging. The "Enable Detailed Download Log" Gradio checkbox will control verbosity for both UI display and detailed file logs (e.g., in `./logs/session_<timestamp>/<script_name>.log`).
6.  **Branching Strategy:** Development occurs on feature branches (e.g., `feature/backend-integration`) based off `main`.

---

## Phase 1: Core Backend Integration - Making "Install, Download & Launch" Functional

**Goal:** Get the Gradio UI to pass configurations to inherited backend scripts and launch a selected WebUI.

*   **Step 1.1: Platform-Agnostic Environment Variable & Path Strategy**
    *   **Action:**
        *   In `AnxLight_Launcher.ipynb` (and conceptually for other platform launchers):
            *   Define `PROJECT_ROOT` (location of the cloned AnxLight repo).
            *   Set `os.environ['home_path'] = PROJECT_ROOT` (or a dedicated `./runtime_home/` within `PROJECT_ROOT` to mirror original `HOME / 'ANXETY'`).
            *   Set `os.environ['scr_path'] = PROJECT_ROOT` (so scripts are found at `./scripts/` etc.).
            *   Set `os.environ['settings_path'] = os.path.join(os.environ['home_path'], 'anxlight_config.json')`.
            *   Set `os.environ['venv_path'] = os.path.join(PROJECT_ROOT, 'venv')` (or platform-appropriate shared venv path).
        *   Consider a helper function in AnxLight (e.g., in `main_gradio_app.py` or a new `utils.py`) to initialize these paths and environment variables consistently, potentially detecting the platform.
    *   **Rationale:** Ensures backend scripts find configurations and operate in a predictable directory structure across platforms. The key is that `home_path` for the backend scripts should point to where `settings_path` will reside.

*   **Step 1.2: Implement Configuration File Generation in `main_gradio_app.py`**
    *   **Location:** Within `launch_anxlight_main_process` function.
    *   **Action:**
        1.  Collect all Gradio input values.
        2.  Construct `widgets_data` dictionary using `SETTINGS_KEYS`. Handle data types. For assets, use singular keys for initial compatibility, plus `_list` keys for future use.
        3.  Construct `environment_data` dictionary (replicating essential info `setup.py` originally saved, like `env_name`, `lang`, paths if backend scripts read them from the "ENVIRONMENT" section of settings).
        4.  Create `anxlight_config = {\"WIDGETS\": widgets_data, \"ENVIRONMENT\": environment_data}`.
        5.  Save `anxlight_config` to the path from `os.environ['settings_path']`.
    *   **Rationale:** Replicates original settings file structure needed by backend.

*   **Step 1.3: Implement `webui_utils.update_current_webui` Call**
    *   **Location:** In `launch_anxlight_main_process` after saving config.
    *   **Action:** Call `modules.webui_utils.update_current_webui(selected_webui_name)`.
    *   **Rationale:** Maintains compatibility.

*   **Step 1.4: Implement Backend Script Execution (`downloading-en.py`)**
    *   **Location:** In `launch_anxlight_main_process`.
    *   **Action:**
        1.  Path: `os.path.join(os.environ['scr_path'], 'scripts', 'en', 'downloading-en.py')`.
        2.  Use `subprocess.Popen`, passing current `os.environ`.
        3.  Implement logging:
            *   If "Detailed Download Log" is checked: Stream all `stdout`/`stderr` to UI and also append to a timestamped log file (e.g., `logs/session_<ts>/downloading.log`).
            *   If unchecked: Stream a summary or key status updates to UI. Still log errors to file.
        4.  Check `returncode`.
    *   **Rationale:** Executes download/setup with proper environment and logging.

*   **Step 1.5: Implement Backend Script Execution (`launch.py`)**
    *   **Location:** In `launch_anxlight_main_process` after successful download.
    *   **Action:** Similar to 1.4 (path, `subprocess.Popen` with `os.environ`, detailed/summary logging to UI and file `logs/session_<ts>/launch.log`).
    *   **Rationale:** Launches WebUI with proper environment and logging.

*   **Step 1.6: Create Log Directory Structure**
    *   **Action:** Ensure `main_gradio_app.py` creates a `./logs/session_<timestamp>/` directory at the start of `launch_anxlight_main_process` if detailed logging is enabled.
    *   **Rationale:** Organizes logs.

*   **Step 1.7: Testing and Refinement**
    *   **Action:** Test thoroughly on Colab first. Identify any hardcoded paths in backend scripts that might break multi-platform goals and plan for how AnxLight can manage them (e.g., by ensuring its env vars guide them correctly).
    *   **Documentation:** Update `Braindump.md` and `LightDoc.md`.

---

## Phase 2: Enhancements & Stability

*   **Step 2.1: Refine Asset Handling for Multi-Select**
    *   **Action:** If backend scripts only use singular asset keys, investigate minimal-impact ways (wrappers, or small script diffs maintained by AnxLight) for `downloading-en.py` to use the `_list` keys from `anxlight_config.json`.
    *   **Rationale:** Fully utilize Gradio multi-select.

*   **Step 2.2: Implement Dynamic Gradio Theming**
    *   **Action:** Use `theme_accent_dd` value to apply `gr.themes.*` or custom CSS.
    *   **Rationale:** UI polish.

*   **Step 2.3: Robust Platform Detection and Path Abstraction**
    *   **Action:** Enhance platform detection beyond Colab/Kaggle. Abstract path configurations (e.g., default venv locations, typical user data dirs) for Vast.ai, Lightning AI, local. This might involve a config utility in AnxLight that `main_gradio_app.py` calls early.
    *   **Rationale:** Core for multi-platform goal.

---

## Phase 3: New Features (Modular Components - To Be Developed Last)

*   **Step 3.1: Standalone Model Downloader Tab (Civitai, HuggingFace)**
    *   **Action:** New Gradio tab. UI for URLs/IDs. Logic using `CivitaiAPI.py` / `huggingface_hub` to download into correct WebUI model paths. Detailed logging.
    *   **Rationale:** Key feature request.

*   **Step 3.2: Fooocus Integration**
    *   **Action:** Research requirements. Add to UI choices. New script in `AnxLight/scripts/UIs/Fooocus.py` (or similar) for clone, deps, config. Adapt `launch.py` logic if needed.
    *   **Rationale:** Expand application support.

*   **Step 3.3: Roop-Unleashed Integration**
    *   **Action:** Research (standalone vs. extension). Integrate accordingly.
    *   **Rationale:** Expand application support.

---

## Cross-Cutting Concerns (Throughout all Phases)

*   **Error Handling:** Graceful error reporting in UI and logs.
*   **Code Refactoring:** Keep `main_gradio_app.py` manageable.
*   **Path Management:** Consistent use of `os.path.join`, `pathlib.Path`. Ensure platform compatibility (e.g., path separators).
*   **Documentation:** Keep `Braindump.md` (state), `LightDoc.md` (changelog/diary), and `AnxLight_Development_Plan.md` (this file) updated.