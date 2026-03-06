import os

import folder_paths
import numpy as np
from PIL import Image


class FilmclusiveCinemaTakeSaver:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "project": ("STRING", {"default": "project"}),
                "scene": ("INT", {"default": 1}),
                "shot": ("STRING", {"default": "A"}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save"
    OUTPUT_NODE = True
    CATEGORY = "Filmclusive"

    def _get_next_take(self, folder: str, shot_name: str) -> int:
        if not os.path.exists(folder):
            return 1

        takes = []
        for filename in os.listdir(folder):
            if shot_name in filename and "_take" in filename:
                try:
                    number = int(filename.split("_take", 1)[1].split(".", 1)[0])
                except Exception:
                    continue
                takes.append(number)

        return (max(takes) + 1) if takes else 1

    def save(self, images, project, scene, shot):
        output_dir = folder_paths.get_output_directory()

        scene_name = f"scene{scene}"
        shot_name = f"{scene_name}{shot}"
        folder = os.path.join(output_dir, project, scene_name, shot_name)
        os.makedirs(folder, exist_ok=True)

        take = self._get_next_take(folder, shot_name)
        filename = f"{shot_name}_take{take}.png"
        path = os.path.join(folder, filename)

        preview_list = []
        for image in images:
            img = image.cpu().numpy()
            img = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8))
            img.save(path)
            preview_list.append(
                {
                    "filename": filename,
                    "subfolder": os.path.join(project, scene_name, shot_name),
                    "type": "output",
                }
            )

        print(f"[Filmclusive] Saved: {path}")
        return {"ui": {"images": preview_list}}


NODE_CLASS_MAPPINGS = {
    "FilmclusiveCinemaTakeSaver": FilmclusiveCinemaTakeSaver,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FilmclusiveCinemaTakeSaver": "Filmclusive Cinema Take Saver",
}

