**AnxLight Project - Session Handover Briefing**

**Date of Last Update:** 2025-06-20 (Please update with current date)

**1. Purpose of this Document:**
   To provide a new AI assistant session with a concise overview of the AnxLight project's current state, key architectural decisions (especially the v3 plan), immediate tasks, and guidance on how to quickly get up to speed. This document aims to allow bypassing the lengthy initial startup analysis of older documentation if desired.

**2. Core Project Goal:**
   To create a user-friendly, robust, and multi-platform (Colab, Kaggle, cloud, local) launcher for Stable Diffusion WebUIs, by integrating a Gradio UI with the backend of `anxety-solo/sdAIgen`.

**3. Current Architecture: v3 Plan (Primary Guide)**
   *   **Why the v3 Change?** The v3 architecture was introduced to improve modularity, stability, and user experience over previous iterations. Key goals were to separate heavy, one-time setup tasks from interactive session launches, centralize versioning, and streamline the download process.
   *   **Key v3 Components & Flow:**
        *   **Launcher Notebook (`notebook/AnxLight_Launcher_v0.0.5.ipynb`):** Two-cell structure.
            *   Cell 1: Clones/updates AnxLight repo, executes `scripts/pre_flight_setup.py`.
            *   Cell 2: Sets ENV vars, executes `scripts/main_gradio_app.py` using VENV Python.
        *   **Versioning (`scripts/anxlight_version.py`):** Central source of truth for component versions.
        *   **Pre-Flight Setup (`scripts/pre_flight_setup.py`):** Handles all initial heavy installations (VENV, core dependencies, tunneling clients, ALL supported WebUIs via `scripts/UIs/*`).
        *   **Main Gradio App (`scripts/main_gradio_app.py`):** Provides Gradio UI, handles session-specific asset downloads (models, LoRAs, etc. via `modules/Manager.py`), generates `anxlight_config.json`, calls `scripts/launch.py`.
        *   **Data Modules (`scripts/data/sd15_data.py`, `scripts/data/sdxl_data.py`):** Consolidated asset definitions (models, VAEs, ControlNets, LoRAs).
        *   **Core Modules (`modules/Manager.py`, `modules/webui_utils.py`, `modules/TunnelHub.py`, `modules/json_utils.py`):** Inherited and adapted backend logic.
        *   **UI Installers (`scripts/UIs/*.py`):** Inherited, need refactoring for `pre_flight_setup.py`.
   *   **Primary v3 Plan Document:** The detailed "Proposed Architecture: Two-Cell Notebook for AnxLight (v3)" (text should be in Mem0/LightDoc) and the root `AnxLight_Development_Plan.md`.

**4. Recommended Reading Order for New Session (if full context desired beyond this brief):**
   1.  This `HANDOVER_BRIEFING.md`.
   2.  The user-provided "Proposed Architecture: Two-Cell Notebook for AnxLight (v3)" plan (check Mem0 or `LightDoc.md` for its text).
   3.  `AnxLight_Development_Plan.md` (root of repo).
   4.  `scripts/anxlight_version.py` (for current versions).
   5.  `LightDoc.md` (local: `C:\Users\Greepo\Documents\Cline\Workflows\LightDoc.md`) - especially latest Diary & Changelog.
   6.  Optionally, `Docs/Plan.md`, `Docs/Overview.md`, `Docs/BrainDump.md` (in repo) for historical context, understanding they are now aligned with v3 at a high level but v3 plan details take precedence.

**5. MCP Tool Usage Notes:**
   *   **Memory Tool:**
        *   Add Memory: `mem0-mcp.add_memory`
        *   Search Memory: `mem0-mcp.search_memory`
        *   *Timeout Workaround*: `mem0-mcp.add_memory` may report a timeout. If so, simulate a 60-second pause and assume server-side success.
   *   **GitHub Tools:** `github.get_file_contents`, `github.create_or_update_file`, etc., for `drf0rk/AnxLight@main`.
   *   **Filesystem Tools:** `filesystem.read_file`, `filesystem.write_file` for local docs (e.g., `LightDoc.md`, local copies of repo docs).

**6. Current Project State & Where We Left Off:**
   *   **Last Major Code Update:** `scripts/main_gradio_app.py` refactored to use updated `modules/Manager.py` (`download_url_to_path`) and consolidated data structures from `scripts/data/sd*_data.py`. (SCIE #12)
   *   **SHA Index of Key v3 Files (as of 2025-06-20):**
        *   `notebook/AnxLight_Launcher_v0.0.5.ipynb`: `ef26a601bf511f90304b783c08b72e7f7d80d446`
        *   `scripts/anxlight_version.py`: `96023add4875b8810b34793d29df87f2c0600571`
        *   `scripts/pre_flight_setup.py`: `dd199d2457fbb6a51f8a99bd67124fdfb2917b16`
        *   `scripts/main_gradio_app.py`: `e5145a96dd8d257cc195d7d2e42e4efc9c725e1a`
        *   `modules/Manager.py`: `42186db2658ff04df464b734bb8b6d46e0d175d3`
        *   `modules/webui_utils.py`: `64030407304fc817c45f26beb5385753aab36d2b`
        *   `scripts/data/sd15_data.py`: `4145395e59e33c381d38c363143f2b13055db532`
        *   `scripts/data/sdxl_data.py`: `035041c9508c2e3f78209be86a8340d3e4f6aa2a`
        *   `Docs/Plan.md`: `51b4f0ea68981bc63745824cde8737a027ab308d`
        *   `Docs/BrainDump.md`: `ff6bdf49a2a6ea63539c6470b6712cf37dfcacd3`
        *   `Docs/Overview.md`: `92ba2cb43af4acc2024af244e7818e78616c0145`
   *   **Documentation Status:** Repo docs (`Plan.md`, `BrainDump.md`, `Overview.md`) and local `LightDoc.md` updated to reflect v3 architecture.

**7. Immediate Next Task & Parts Not Fully Implemented:**
   *   **Primary Next Task:** Refactor `scripts/UIs/A1111.py` to remove IPython dependencies, making it executable by `scripts/pre_flight_setup.py`.
   *   **Key Parts of v3 Not Yet Fully Implemented/Tested:**
        *   **`modules/Manager.py` - `download_url_to_path` robustness:** Needs thorough testing (diverse URLs, tokens, errors). Filename derivation for URLs without explicit names.
        *   **`scripts/UIs/*.py` Refactors:** `A1111.py` is next; others will follow.
        *   **End-to-End Testing:** Full `AnxLight_Launcher_v0.0.5.ipynb` flow.
        *   **Data Accuracy in `sd15_data.py`/`sdxl_data.py`:** Ongoing verification needed.
        *   **"Download Session Logs" feature in `main_gradio_app.py`**.

**8. SCIE Routine Status:**
    *   SCIE counter was reset after SCIE #12. Routines trigger based on *new* code-related SCIEs.
    *   Per user instruction, only Routine B (Sanity Check against `anxety-solo/sdAIgen` for existing functions) should be actively performed when triggered by default.