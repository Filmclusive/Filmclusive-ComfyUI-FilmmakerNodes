import csv
import json
import os
from datetime import datetime

def _sanitize_segment(value: str, fallback: str) -> str:
    value = (value or "").strip()
    if not value:
        return fallback
    value = value.replace(os.sep, "_")
    if os.altsep:
        value = value.replace(os.altsep, "_")
    return value or fallback


def _first_row(path: str):
    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            return next(reader, None)
    except Exception:
        return None


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_generation_params(prompt_obj):
    result = {
        "model": "",
        "seed": "",
        "steps": "",
        "sampler": "",
        "scheduler": "",
        "cfg": "",
        "denoise": "",
        "loras": [],
        "prompt": "",
        "negative_prompt": "",
    }

    if not isinstance(prompt_obj, dict):
        return result

    clip_texts = []
    for node_id, node in prompt_obj.items():
        if not isinstance(node, dict):
            continue
        class_type = str(node.get("class_type") or "")
        inputs = node.get("inputs") if isinstance(node.get("inputs"), dict) else {}

        if not result["model"] and ("CheckpointLoader" in class_type or class_type in {"CheckpointLoaderSimple"}):
            ckpt = inputs.get("ckpt_name") or inputs.get("checkpoint") or ""
            if isinstance(ckpt, str):
                result["model"] = ckpt

        if "LoraLoader" in class_type or class_type in {"LoraLoader", "LoraLoaderModelOnly"}:
            name = inputs.get("lora_name") or inputs.get("lora") or ""
            strength_model = inputs.get("strength_model")
            strength_clip = inputs.get("strength_clip")
            if isinstance(name, str) and name.strip():
                result["loras"].append(
                    {
                        "name": name,
                        "strength_model": strength_model,
                        "strength_clip": strength_clip,
                    }
                )

        if (result["seed"] == "" and result["steps"] == "" and result["sampler"] == "" and result["scheduler"] == "") and (
            "KSampler" in class_type
        ):
            if "seed" in inputs:
                result["seed"] = inputs.get("seed")
            if "steps" in inputs:
                result["steps"] = inputs.get("steps")
            if "sampler_name" in inputs:
                result["sampler"] = inputs.get("sampler_name")
            if "scheduler" in inputs:
                result["scheduler"] = inputs.get("scheduler")
            if "cfg" in inputs:
                result["cfg"] = inputs.get("cfg")
            if "denoise" in inputs:
                result["denoise"] = inputs.get("denoise")

        if "CLIPTextEncode" in class_type and "text" in inputs and isinstance(inputs.get("text"), str):
            text = inputs.get("text") or ""
            if text.strip():
                clip_texts.append(text)

    if clip_texts and not result["prompt"]:
        # Best-effort: first text node as "prompt", second (if present) as "negative".
        result["prompt"] = clip_texts[0]
        if len(clip_texts) > 1:
            result["negative_prompt"] = clip_texts[1]

    return result


def _format_loras(loras):
    parts = []
    for item in loras or []:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        if not name:
            continue
        sm = item.get("strength_model")
        sc = item.get("strength_clip")
        suffix = ""
        if sm is not None or sc is not None:
            suffix = f"@{sm},{sc}"
        parts.append(f"{name}{suffix}")
    return "; ".join(parts)


class FilmclusiveShotLogger:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "project_name": ("STRING", {"default": "FilmclusiveProject"}),
                "scene": ("STRING", {"default": "01"}),
                "shot": ("STRING", {"default": "A"}),
                "fps": ("INT", {"default": 24, "min": 1, "max": 240}),
                "output_dir_hint": ("STRING", {"default": "ComfyUI/output"}),
                "file_path": ("STRING", {"default": ""}),
                "take": ("INT", {"default": 1, "min": 1, "max": 999999}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "log_shot"
    OUTPUT_NODE = True
    CATEGORY = "Filmclusive"

    def log_shot(self, project_name, scene, shot, fps, output_dir_hint, file_path, take):
        import folder_paths

        output_dir = folder_paths.get_output_directory()

        safe_project = _sanitize_segment(project_name, "project")
        project_folder = os.path.join(output_dir, safe_project)
        os.makedirs(project_folder, exist_ok=True)

        log_path = os.path.join(project_folder, "shot_log.csv")

        timestamp = datetime.now().isoformat(timespec="seconds")

        file_value = (file_path or "").strip()
        meta_file_value = ""
        meta_path = ""
        meta_json = {}
        extracted = {}

        if file_value:
            try:
                abs_path = os.path.abspath(file_value)
                if abs_path.startswith(os.path.abspath(project_folder) + os.sep):
                    file_value = os.path.relpath(abs_path, project_folder)
                elif abs_path.startswith(os.path.abspath(output_dir) + os.sep):
                    file_value = os.path.relpath(abs_path, output_dir)
                else:
                    file_value = abs_path

                meta_path = os.path.splitext(abs_path)[0] + ".meta.json"
                if os.path.isfile(meta_path):
                    meta_json = _load_json(meta_path) or {}
                    extracted = _extract_generation_params(meta_json.get("prompt"))

                    try:
                        if meta_path.startswith(os.path.abspath(project_folder) + os.sep):
                            meta_file_value = os.path.relpath(meta_path, project_folder)
                        elif meta_path.startswith(os.path.abspath(output_dir) + os.sep):
                            meta_file_value = os.path.relpath(meta_path, output_dir)
                        else:
                            meta_file_value = meta_path
                    except Exception:
                        meta_file_value = meta_path
            except Exception:
                pass

        columns = [
            "scene",
            "shot",
            "take",
            "fps",
            "timestamp",
            "file",
            "model",
            "seed",
            "steps",
            "sampler",
            "scheduler",
            "cfg",
            "denoise",
            "loras",
            "prompt",
            "negative_prompt",
            "meta_file",
            "meta_json",
        ]

        write_header = not os.path.exists(log_path)
        if not write_header:
            existing_header = _first_row(log_path)
            if existing_header and list(existing_header) != columns:
                rotated = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_path = os.path.join(project_folder, f"shot_log_{rotated}.csv")
                write_header = True

        model = extracted.get("model", "") if isinstance(extracted, dict) else ""
        seed = extracted.get("seed", "") if isinstance(extracted, dict) else ""
        steps = extracted.get("steps", "") if isinstance(extracted, dict) else ""
        sampler = extracted.get("sampler", "") if isinstance(extracted, dict) else ""
        scheduler = extracted.get("scheduler", "") if isinstance(extracted, dict) else ""
        cfg = extracted.get("cfg", "") if isinstance(extracted, dict) else ""
        denoise = extracted.get("denoise", "") if isinstance(extracted, dict) else ""
        loras = _format_loras(extracted.get("loras")) if isinstance(extracted, dict) else ""
        prompt_text = extracted.get("prompt", "") if isinstance(extracted, dict) else ""
        neg_prompt_text = extracted.get("negative_prompt", "") if isinstance(extracted, dict) else ""

        with open(log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(columns)
            writer.writerow(
                [
                    scene,
                    shot,
                    int(take),
                    int(fps),
                    timestamp,
                    file_value,
                    model,
                    seed,
                    steps,
                    sampler,
                    scheduler,
                    cfg,
                    denoise,
                    loras,
                    prompt_text,
                    neg_prompt_text,
                    meta_file_value,
                    json.dumps(extracted or {}, ensure_ascii=False),
                ]
            )

        print(f"[Filmclusive] Logged shot: {scene} {shot} take {int(take)} -> {file_value}")
        return ()


NODE_CLASS_MAPPINGS = {
    "FilmclusiveShotLogger": FilmclusiveShotLogger,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FilmclusiveShotLogger": "Filmclusive Shot Logger",
}
