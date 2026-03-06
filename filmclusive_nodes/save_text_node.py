import os
import re

import folder_paths


def _sanitize_segment(value: str, fallback: str) -> str:
    value = (value or "").strip()
    if not value:
        return fallback
    value = value.replace(os.sep, "_")
    if os.altsep:
        value = value.replace(os.altsep, "_")
    value = re.sub(r"[^a-zA-Z0-9._-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._-")
    return value or fallback


class FilmclusiveSaveTextNode:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "forceInput": True}),
                "project_name": ("STRING", {"default": "project", "forceInput": True}),
                "scene": ("STRING", {"default": "scene_1", "forceInput": True}),
                "shot": ("STRING", {"default": "shot_A", "forceInput": True}),
                "take": ("INT", {"default": 1, "min": 1, "max": 999}),
                "description": ("STRING", {"default": "notes", "forceInput": True}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_text"
    OUTPUT_NODE = True
    CATEGORY = "Filmclusive"

    def save_text(self, text, project_name, scene, shot, take, description):
        safe_project = _sanitize_segment(project_name, "project")
        safe_scene = _sanitize_segment(scene, "scene_1")
        safe_shot = _sanitize_segment(shot, "shot_A")
        safe_description = _sanitize_segment(description, "notes")

        project_folder = os.path.join(self.output_dir, safe_project)
        scene_folder = os.path.join(project_folder, safe_scene)
        os.makedirs(scene_folder, exist_ok=True)

        filename = f"{safe_scene}_{safe_shot}_take_{take:02}_{safe_description}.txt"
        full_path = os.path.join(scene_folder, filename)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"[Filmclusive] Saved text to {full_path}")
        return ()


NODE_CLASS_MAPPINGS = {
    "FilmclusiveSaveTextNode": FilmclusiveSaveTextNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FilmclusiveSaveTextNode": "Filmclusive Save Text",
}

