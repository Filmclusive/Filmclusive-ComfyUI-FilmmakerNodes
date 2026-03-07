# Filmclusive Node Pack

This directory packages the Filmclusive production helpers listed below so they can be distributed as a single ComfyUI Manager node pack.

## Nodes

- **Filmclusive Save Text** – writes a simple note per project/scene/shot/take and prints the full path after saving.
- **Filmclusive Save Image** – saves the rendered outputs with auto-incremented takes, emits PNG metadata, and stores prompt/workflow sidecars for quick recall.
- **Filmclusive Save Video (MP4/WebM/GIF)** – encodes the incoming image batch as a video take, writes the same metadata/prompt/workflow sidecars, and emits a thumbnail preview for the UI (requires `ffmpeg`).
- **Filmclusive Cinema Take Saver** – mirrors the previous scene/shot saving heuristic for archival screenshots and keeps a preview-ready payload for the UI.
- **Filmclusive Multi-LoRA (Filmmaker)** – stacks multiple LoRAs in clearly-labeled creative slots (style, characters, props, lighting, camera, set design) and patches both model + CLIP.
- **Filmclusive KSampler (Filmmaker)** – wrapper around `KSampler` with filmmaker labels (e.g. “Prompt Strength (CFG)”) while keeping the same underlying behavior.
- **Filmclusive WanVideo (Filmmaker wrappers)** – wrappers around common `WanVideo*` nodes (model loader, text encode, multi-LoRA, sampler, decode) with clearer labels and tooltips.

Each node registers under the `Filmclusive` category via `NODE_CLASS_MAPPINGS` so they all appear as siblings in ComfyUI.

## Installation via ComfyUI Manager

## Workflow migration helper

To replace node types inside an existing workflow JSON (so it uses Filmclusive filmmaker nodes), run:

`python3 /Users/masmoriya/Documents/ComfyUI/custom_nodes/filmclusive_nodes/tools/migrate_workflow_nodes.py /path/to/input.json /path/to/output.migrated.json`

1. Push this folder as the root of your Git repository and open a pull request against `ComfyUI-Manager`, adding `Filmclusive` to `custom-node-list.json` so Manager can discover it.
2. When a user installs Filmclusive, Manager clones the repo, installs `requirements.txt` (if you add one later), and runs `install.py` from this directory before activating the nodes.
3. Provide optional `disable.py`/`enable.py` scripts when you need to clean up or re-enable resources—the Manager guide states it runs these hooks whenever a node is toggled.

Plan future updates by keeping this README in sync with new Filmclusive nodes (image/video/metadata) and documenting any extra dependencies.
