# Filmclusive Node Pack

This directory packages the Filmclusive production helpers listed below so they can be distributed as a single ComfyUI Manager node pack.

## Nodes

- **Filmclusive Save Text** – writes a simple note per project/scene/shot/take and prints the full path after saving.
- **Filmclusive Save Image** – saves the rendered outputs with auto-incremented takes, emits PNG metadata, and stores prompt/workflow sidecars for quick recall.
- **Filmclusive Cinema Take Saver** – mirrors the previous scene/shot saving heuristic for archival screenshots and keeps a preview-ready payload for the UI.

Each node registers under the `Filmclusive` category via `NODE_CLASS_MAPPINGS` so they all appear as siblings in ComfyUI.

## Installation via ComfyUI Manager

1. Push this folder as the root of your Git repository and open a pull request against `ComfyUI-Manager`, adding `Filmclusive` to `custom-node-list.json` so Manager can discover it.
2. When a user installs Filmclusive, Manager clones the repo, installs `requirements.txt` (if you add one later), and runs `install.py` from this directory before activating the nodes.
3. Provide optional `disable.py`/`enable.py` scripts when you need to clean up or re-enable resources—the Manager guide states it runs these hooks whenever a node is toggled.

Plan future updates by keeping this README in sync with new Filmclusive nodes (image/video/metadata) and documenting any extra dependencies.
