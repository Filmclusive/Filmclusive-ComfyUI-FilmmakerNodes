# Filmclusive Node Pack for ComfyUI
### Organize your generations like a real film production.

<img width="289" height="227" alt="image" src="https://github.com/user-attachments/assets/0cbc73c5-421a-4bb2-a934-05776864b953" />


> **Note:** These nodes are currently in **Beta**. They are designed to make it easier to select and update your file and folder names on the fly, keeping your production organized.

## The Problem: The "Output Folder" Mess
If you've used ComfyUI for a while, you know the struggle. Every generation, every test, and every experimental render ends up in a giant pile in your `output` folder. Maybe it goes into a `video` subfolder if you're lucky, but that’s not how professional filmmakers or video editors work. 

When you're producing a film, you don't just have "files." You have **Scenes**, **Shots**, and **Takes**.

## The Solution: Think Like a Filmmaker
Coming from a background of 15 years in filmmaking, I built these nodes because I needed ComfyUI to act like a digital **Assistant Editor**. In a real edit suite, everything must be in the right folder, labeled properly by scene and take number, before the work even begins.

**Filmclusive Nodes** replace your standard save nodes with a filmmaker-friendly workflow. Instead of hacking together folder paths with backslashes and manually renaming files, these nodes let you manage your production directly from the UI. Every time you hit "Queue Prompt," you aren't just saving a file—you're recording a new **Take**.

### Why use this instead of standard nodes?
*   **Automatic Folder Organization:** Your files are automatically sorted into `Project/Scene/Shot/Take` structures.
*   **Assistant Editor Logic:** Everything is labeled properly from the start, making your renders ready for professional NLEs (Non-Linear Editors) like Premiere, DaVinci Resolve, or Avid.
*   **Production Speed:** You can update scene and take numbers directly in the node. No more digging through file strings to change a folder name.
*   **Sanity for Professionals:** This isn't a "flashy" node that changes your pixels; it's the essential utility that keeps your project from becoming a disorganized mess.

---

## Included Nodes

### 🎬 The "Vault" (Saving & Logging)
*   **Filmclusive Save Image:** A smart replacement for the standard Save Image node. It handles auto-incrementing takes, embeds PNG metadata, and saves your prompt/workflow as a sidecar file for instant recall.
*   **Filmclusive Save Video (MP4/WebM/GIF):** Encodes image batches into professional video takes (requires `ffmpeg`) and generates UI thumbnails so you can see what you've rendered without leaving ComfyUI.
*   **Filmclusive Save Text:** Logs project notes, scene descriptions, or shot details directly into your project folders.
*   **Filmclusive Shot Logger:** Keeps a running log of your production's progress and metadata.
*   **Filmclusive Cinema Take Saver:** Specialized for archival screenshots and high-quality production "stills" from your workflow.

### 🎥 The "Set" (Filmmaker Wrappers)
We've wrapped standard ComfyUI logic in labels that make sense to a Director or DP:
*   **Filmmaker Multi-LoRA:** Stack your LoRAs into clearly labeled creative "slots" (Style, Character, Props, Lighting, Camera, Set Design) instead of a confusing list.
*   **Filmmaker KSampler:** A wrapper that uses cinematic terminology like "Prompt Strength" (CFG) while maintaining the underlying power of ComfyUI.
*   **WanVideo (Filmmaker Wrappers):** Dedicated wrappers for WanVideo models and samplers with clearer labels and helpful tooltips for professional use.

---

## Installation

### Via ComfyUI Manager
1. Search for `Filmclusive` in the ComfyUI Manager.
2. Click **Install**.
3. Restart ComfyUI.

### Manual Installation
1. Navigate to your `ComfyUI/custom_nodes` directory.
2. Clone this repository:
   ```bash
   git clone https://github.com/filmclusive/Filmclusive-ComfyUI-FilmmakerNodes.git
   ```
3. Restart ComfyUI.

---

## Workflow Migration Helper
If you have an existing workflow and want to swap your standard nodes for Filmclusive filmmaker nodes, you can use our migration script:

```bash
python3 filmclusive_nodes/tools/migrate_workflow_nodes.py /path/to/input.json /path/to/output.migrated.json
```

---
*Created by a filmmaker, for filmmakers. Stay organized, stay creative.*
