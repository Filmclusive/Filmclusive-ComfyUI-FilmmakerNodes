import folder_paths


def _lora_choices():
    loras = []
    try:
        loras = folder_paths.get_filename_list("loras") or []
    except Exception:
        loras = []
    seen = set()
    out = ["None"]
    for name in loras:
        if not name or name in seen or name == "None":
            continue
        seen.add(name)
        out.append(name)
    return out


def _apply_lora(model, clip, *, lora_name: str, strength: float, slot_label: str):
    if not lora_name or lora_name == "None" or float(strength) == 0.0:
        return model, clip

    lora_path = folder_paths.get_full_path("loras", lora_name)
    if not lora_path:
        raise ValueError(f"LoRA not found in models/loras: {lora_name}")

    import comfy.sd
    import comfy.utils

    lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
    model, clip = comfy.sd.load_lora_for_models(model, clip, lora, float(strength), float(strength))
    print(f"[Filmclusive] Applied LoRA ({slot_label}): {lora_name} @ {float(strength):.3f}")
    return model, clip


class FilmclusiveMultiLoRAFilmmaker:
    """
    Filmmaker-friendly LoRA stacker.

    Goal: expose common creative roles (character / prop / lighting / camera / set design)
    as clearly-labeled slots, while still behaving like the standard Model+CLIP LoRA loader.
    """

    @classmethod
    def INPUT_TYPES(cls):
        loras = _lora_choices()
        strength_spec = {
            "default": 1.0,
            "min": -2.0,
            "max": 2.0,
            "step": 0.05,
            "tooltip": "How strongly this LoRA influences the shot (applies to both the model and text encoder). Set 0 to disable the slot.",
        }
        label_spec = {
            "default": "",
            "tooltip": "Optional: a display label for this slot (e.g. the character name).",
        }
        lora_spec = {
            "default": "None",
            "tooltip": "Pick a LoRA from `ComfyUI/models/loras`. Leave as None to disable the slot.",
        }

        return {
            "required": {
                "model": (
                    "MODEL",
                    {
                        "tooltip": "Connect this to the `model` output of a Checkpoint/Model Loader.",
                    },
                ),
                "clip": (
                    "CLIP",
                    {
                        "tooltip": "Connect this to the `clip` output of a Checkpoint/Model Loader.",
                    },
                ),
                "style_label": ("STRING", {**label_spec, "default": "Style / Look"}),
                "style_lora": (loras, {**lora_spec, "tooltip": "Overall look/style LoRA (grade, lens feel, film stock, art direction)."}),
                "style_strength": ("FLOAT", {**strength_spec, "default": 0.8}),
                "character_1_label": ("STRING", {**label_spec, "default": "Character 1"}),
                "character_1_lora": (loras, {**lora_spec, "tooltip": "Primary character LoRA for consistent identity."}),
                "character_1_strength": ("FLOAT", {**strength_spec, "default": 1.0}),
                "character_2_label": ("STRING", {**label_spec, "default": "Character 2"}),
                "character_2_lora": (loras, {**lora_spec, "tooltip": "Secondary character LoRA (co-star / antagonist)."}),
                "character_2_strength": ("FLOAT", {**strength_spec, "default": 1.0}),
                "character_3_label": ("STRING", {**label_spec, "default": "Character 3"}),
                "character_3_lora": (loras, {**lora_spec, "tooltip": "Third character LoRA (supporting / background)."}),
                "character_3_strength": ("FLOAT", {**strength_spec, "default": 1.0}),
                "prop_label": ("STRING", {**label_spec, "default": "Hero Prop"}),
                "prop_lora": (loras, {**lora_spec, "tooltip": "Hero prop / costume / key object LoRA."}),
                "prop_strength": ("FLOAT", {**strength_spec, "default": 0.9}),
                "lighting_label": ("STRING", {**label_spec, "default": "Lighting"}),
                "lighting_lora": (loras, {**lora_spec, "tooltip": "Lighting direction LoRA (softbox, neon, moonlight, practicals)."}),
                "lighting_strength": ("FLOAT", {**strength_spec, "default": 0.7}),
                "camera_label": ("STRING", {**label_spec, "default": "Camera"}),
                "camera_lora": (loras, {**lora_spec, "tooltip": "Camera/lens/movement LoRA (dolly, handheld, crane, anamorphic)."}),
                "camera_strength": ("FLOAT", {**strength_spec, "default": 1.0}),
                "set_design_label": ("STRING", {**label_spec, "default": "Set Design"}),
                "set_design_lora": (loras, {**lora_spec, "tooltip": "Set design / location / production design LoRA."}),
                "set_design_strength": ("FLOAT", {**strength_spec, "default": 0.8}),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP")
    RETURN_NAMES = ("model", "clip")
    FUNCTION = "apply"
    CATEGORY = "Filmclusive/Filmmaker"

    def apply(
        self,
        model,
        clip,
        style_label,
        style_lora,
        style_strength,
        character_1_label,
        character_1_lora,
        character_1_strength,
        character_2_label,
        character_2_lora,
        character_2_strength,
        character_3_label,
        character_3_lora,
        character_3_strength,
        prop_label,
        prop_lora,
        prop_strength,
        lighting_label,
        lighting_lora,
        lighting_strength,
        camera_label,
        camera_lora,
        camera_strength,
        set_design_label,
        set_design_lora,
        set_design_strength,
    ):
        model, clip = _apply_lora(model, clip, lora_name=style_lora, strength=style_strength, slot_label=style_label)
        model, clip = _apply_lora(
            model, clip, lora_name=character_1_lora, strength=character_1_strength, slot_label=character_1_label
        )
        model, clip = _apply_lora(
            model, clip, lora_name=character_2_lora, strength=character_2_strength, slot_label=character_2_label
        )
        model, clip = _apply_lora(
            model, clip, lora_name=character_3_lora, strength=character_3_strength, slot_label=character_3_label
        )
        model, clip = _apply_lora(model, clip, lora_name=prop_lora, strength=prop_strength, slot_label=prop_label)
        model, clip = _apply_lora(
            model, clip, lora_name=lighting_lora, strength=lighting_strength, slot_label=lighting_label
        )
        model, clip = _apply_lora(model, clip, lora_name=camera_lora, strength=camera_strength, slot_label=camera_label)
        model, clip = _apply_lora(
            model, clip, lora_name=set_design_lora, strength=set_design_strength, slot_label=set_design_label
        )
        return (model, clip)


NODE_CLASS_MAPPINGS = {
    "FilmclusiveMultiLoRAFilmmaker": FilmclusiveMultiLoRAFilmmaker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FilmclusiveMultiLoRAFilmmaker": "Filmclusive Multi-LoRA (Filmmaker)",
}

