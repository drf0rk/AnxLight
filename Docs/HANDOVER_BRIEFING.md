# AnxLight Project - Session Handover Briefing

**Date of Last Update:** 2025-06-21

**1. Purpose of this Document:**
To provide a new AI assistant session with a concise overview of the AnxLight project's current state, key architectural decisions (v3 plan), immediate tasks, and guidance on how to quickly get up to speed.

**2. Core Project Goal:**
To create a user-friendly, robust, and multi-platform (Colab, Kaggle, cloud, local) launcher for Stable Diffusion WebUIs, by integrating a Gradio UI with the backend of `anxety-solo/sdAIgen`.

**3. Current Architecture: v3 Plan (Primary Guide)**
*   **Workflow:** A two-cell notebook (`AnxLight_Launcher_v0.0.5.ipynb`) is the entry point.
    *   **Cell 1** runs `scripts/pre_flight_setup.py` to handle all heavy, one-time installations (VENV, system packages like `aria2`, core Python dependencies, and all supported WebUIs via the refactored `scripts/UIs/*.py` installers).
    *   **Cell 2** runs `scripts/main_gradio_app.py` to launch the user-facing Gradio application for session configuration and launch.
*   **Key Modules:** `modules/Manager.py` and `modules/webui_utils.py` provide core backend logic for downloads and pathing.

**4. Current Project State & Where We Left Off:**
*   **Last Major Task Completed:** A full debugging and refactoring cycle has been completed.
    *   **`pre_flight_setup.py`** was made more robust by adding installation for system dependencies (`python3-venv`, `aria2`, `unzip`) and a manual `pip` installation step for the VENV.
    *   **All `scripts/UIs/*.py` scripts** have been refactored to remove IPython dependencies and use standard `subprocess` calls. Critical `sys.path` and logic errors (`TypeError`, incorrect `m_download` calls) have been fixed.
    *   **`modules/Manager.py`** and **`modules/webui_utils.py`** were fixed to resolve critical `SyntaxError` issues.
    *   **`scripts/main_gradio_app.py`** was fixed to resolve a `NameError` by defining necessary UI constants.
*   **The project is now at a major milestone**: The entire pre-flight and application launch sequence has been coded and debugged.

**5. Immediate Next Task:**
*   **Primary Next Task:** **End-to-End Testing.** The entire notebook (Cell 1, then Cell 2) must be run to verify that all fixes work together and the Gradio application launches successfully without errors.

**6. Latest SHAs of Key Modified Files (as of 2025-06-21):**
*   `scripts/pre_flight_setup.py`: `2599d0183783ea2c03df6c0fd788907aca373256`
*   `scripts/UIs/A1111.py`: `c98890175590d4ef566c5f5ab8db0cb4631e2f85`
*   `scripts/UIs/Classic.py`: `8e80513c0d7c83bc0f249f720da4a13684c8c312`
*   `scripts/UIs/ComfyUI.py`: `1525eab72e87ab7a63e3684d8763f3abdc062b3b`
*   `scripts/UIs/Forge.py`: `f0928ca97c1f748c8ef81ab51bf1211a008998d0`
*   `scripts/UIs/ReForge.py`: `750c246e63b9cca4ad7003cea965090e4461bb50`
*   `scripts/UIs/SD-UX.py`: `9292a2af6bf1ea4d90e86f10ac2e84ae0bcde2d0`
*   `modules/Manager.py`: `ab6fa53cbb8315520d60c7932f3fe7d874704bb9`
*   `modules/webui_utils.py`: `401072969d8c61937784e02bc48a90ffa73aae65`
*   `scripts/main_gradio_app.py`: `8fb4af1a91a5d056950e87b9a3b59fdc7f95ae32`

**7. SCIE Routine Status:**
*   The last completed SCIE was #11. The next routine will be triggered on SCIE #12 (Routine B, Sanity Check).