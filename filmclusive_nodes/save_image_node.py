import json
import os
import re
from datetime import datetime

import folder_paths
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo


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


class FilmclusiveSaveImage:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "project_name": ("STRING", {"default": "project"}),
                "scene": ("STRING", {"default": "scene_1"}),
                "shot": ("STRING", {"default": "shot_A"}),
                "description": ("STRING", {"default": "render"}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save"
    OUTPUT_NODE = True
    CATEGORY = "Filmclusive"

    def _get_next_take(self, folder: str, prefix: str) -> int:
        if not os.path.exists(folder):
            return 1

        takes = []
        for filename in os.listdir(folder):
            if not (filename.startswith(prefix) and filename.lower().endswith(".png")):
                continue
            remainder = filename[len(prefix) :]
            try:
                take_text = remainder.split("_", 1)[0].lstrip("0") or "0"
                takes.append(int(take_text))
            except Exception:
                continue
        return (max(takes) + 1) if takes else 1

    def _write_json(self, path: str, data) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save(self, images, project_name, scene, shot, description, prompt=None, extra_pnginfo=None):
        safe_project = _sanitize_segment(project_name, "project")
        safe_scene = _sanitize_segment(scene, "scene_1")
        safe_shot = _sanitize_segment(shot, "shot_A")
        safe_description = _sanitize_segment(description, "render")

        shot_folder = os.path.join(self.output_dir, safe_project, safe_scene, safe_shot)
        os.makedirs(shot_folder, exist_ok=True)

        base_prefix = f"{safe_scene}_{safe_shot}_take_"
        take = self._get_next_take(shot_folder, base_prefix)

        base_name = f"{safe_scene}_{safe_shot}_take_{take:02}_{safe_description}"
        timestamp = datetime.now().isoformat(timespec="seconds")

        workflow = None
        if isinstance(extra_pnginfo, dict):
            workflow = extra_pnginfo.get("workflow") or extra_pnginfo.get("Workflow")

        meta = {
            "project_name": project_name,
            "scene": scene,
            "shot": shot,
            "take": take,
            "description": description,
            "timestamp": timestamp,
            "prompt": prompt,
            "workflow": workflow,
        }

        self._write_json(os.path.join(shot_folder, f"{base_name}.meta.json"), meta)
        if prompt is not None:
            self._write_json(os.path.join(shot_folder, f"{base_name}.prompt.json"), prompt)
        if workflow is not None:
            self._write_json(os.path.join(shot_folder, f"{base_name}.workflow.json"), workflow)

        pnginfo = PngInfo()
        try:
            if prompt is not None:
                pnginfo.add_text("filmclusive_prompt", json.dumps(prompt, ensure_ascii=False))
            if workflow is not None:
                pnginfo.add_text("filmclusive_workflow", json.dumps(workflow, ensure_ascii=False))
            pnginfo.add_text(
                "filmclusive",
                json.dumps(
                    {
                        "project_name": project_name,
                        "scene": scene,
                        "shot": shot,
                        "take": take,
                        "description": description,
                        "timestamp": timestamp,
                    },
                    ensure_ascii=False,
                ),
            )
        except Exception:
            pnginfo = None

        preview_list = []
        images_list = list(images)
        for index, image in enumerate(images_list):
            suffix = "" if len(images_list) == 1 else f"_img_{index:02}"
            filename = f"{base_name}{suffix}.png"
            full_path = os.path.join(shot_folder, filename)

            img = image.cpu().numpy()
            img = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8))
            if pnginfo is not None:
                img.save(full_path, pnginfo=pnginfo)
            else:
                img.save(full_path)

            preview_list.append(
                {
                    "filename": filename,
                    "subfolder": os.path.join(safe_project, safe_scene, safe_shot),
                    "type": "output",
                }
            )

        print(f"[Filmclusive] Saved take {take:02} to {shot_folder}")
        return {"ui": {"images": preview_list}}


NODE_CLASS_MAPPINGS = {
    "FilmclusiveSaveImage": FilmclusiveSaveImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FilmclusiveSaveImage": "Filmclusive Save Image",
}

