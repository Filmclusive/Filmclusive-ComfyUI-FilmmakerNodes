from __future__ import annotations


def _get_node_class(node_type: str):
    import nodes

    cls = nodes.NODE_CLASS_MAPPINGS.get(node_type)
    if cls is None:
        raise RuntimeError(
            f"Underlying node type not found: {node_type}. Make sure the extension providing it is installed/enabled."
        )
    return cls


def _call_underlying(node_type: str, **kwargs):
    cls = _get_node_class(node_type)
    instance = cls()
    fn_name = getattr(cls, "FUNCTION", None)
    if not fn_name or not hasattr(instance, fn_name):
        raise RuntimeError(f"Underlying node {node_type} has no callable FUNCTION.")
    return getattr(instance, fn_name)(**kwargs)


class _FilmclusiveWrappedNodeBase:
    TARGET_NODE_TYPE = ""
    CATEGORY = "Filmclusive/Filmmaker"

    @classmethod
    def INPUT_TYPES(cls):
        target = _get_node_class(cls.TARGET_NODE_TYPE)
        spec = target.INPUT_TYPES()

        # Ensure tooltips exist for core patch points we care about.
        required = spec.get("required", {})
        optional = spec.get("optional", {})
        hidden = spec.get("hidden", {})

        def add_tip(group, key: str, tip: str):
            entry = group.get(key)
            if not isinstance(entry, (tuple, list)) or len(entry) < 2 or not isinstance(entry[1], dict):
                return
            entry[1].setdefault("tooltip", tip)

        add_tip(required, "model", "Connect this to the `model` output of the upstream model loader.")
        add_tip(required, "clip", "Connect this to the `clip` output of the upstream model loader.")
        add_tip(required, "positive", "Connect this to a positive prompt encoder.")
        add_tip(required, "negative", "Connect this to a negative prompt encoder.")
        add_tip(required, "latent_image", "Connect this to a latent source (Empty Latent, VAE Encode, etc.).")
        add_tip(required, "cfg", "Prompt strength (CFG): how strongly the model follows your prompt. Higher = more literal, lower = looser.")
        add_tip(required, "steps", "How many sampling steps to run. More steps can improve detail but takes longer.")
        add_tip(required, "seed", "Random seed. Same seed + same settings = repeatable result.")
        add_tip(required, "denoise", "Denoise strength: 1.0 = full generation; lower values preserve more of the input latent.")

        return {"required": required, "optional": optional, "hidden": hidden}

    def _delegate(self, **kwargs):
        return _call_underlying(self.TARGET_NODE_TYPE, **kwargs)


class FilmclusiveKSamplerFilmmaker(_FilmclusiveWrappedNodeBase):
    TARGET_NODE_TYPE = "KSampler"

    # Keep identical IO so workflow links stay compatible after migration.
    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("samples",)
    FUNCTION = "sample"
    CATEGORY = "Filmclusive/Filmmaker/Sampling"

    def sample(self, **kwargs):
        return self._delegate(**kwargs)


class FilmclusiveWanVideoModelLoaderFilmmaker(_FilmclusiveWrappedNodeBase):
    TARGET_NODE_TYPE = "WanVideoModelLoader"

    FUNCTION = "load"
    CATEGORY = "Filmclusive/Filmmaker/Wan 2.1"

    def load(self, **kwargs):
        return self._delegate(**kwargs)


class FilmclusiveWanVideoVAELoaderFilmmaker(_FilmclusiveWrappedNodeBase):
    TARGET_NODE_TYPE = "WanVideoVAELoader"

    FUNCTION = "load"
    CATEGORY = "Filmclusive/Filmmaker/Wan 2.1"

    def load(self, **kwargs):
        return self._delegate(**kwargs)


class FilmclusiveWanVideoTextEncodeCachedFilmmaker(_FilmclusiveWrappedNodeBase):
    TARGET_NODE_TYPE = "WanVideoTextEncodeCached"

    FUNCTION = "encode"
    CATEGORY = "Filmclusive/Filmmaker/Wan 2.1"

    def encode(self, **kwargs):
        return self._delegate(**kwargs)


class FilmclusiveWanVideoLoraSelectMultiFilmmaker(_FilmclusiveWrappedNodeBase):
    TARGET_NODE_TYPE = "WanVideoLoraSelectMulti"

    FUNCTION = "select"
    CATEGORY = "Filmclusive/Filmmaker/Wan 2.1"

    def select(self, **kwargs):
        return self._delegate(**kwargs)


class FilmclusiveWanVideoSamplerFilmmaker(_FilmclusiveWrappedNodeBase):
    TARGET_NODE_TYPE = "WanVideoSampler"

    FUNCTION = "sample"
    CATEGORY = "Filmclusive/Filmmaker/Wan 2.1"

    def sample(self, **kwargs):
        return self._delegate(**kwargs)


class FilmclusiveWanVideoDecodeFilmmaker(_FilmclusiveWrappedNodeBase):
    TARGET_NODE_TYPE = "WanVideoDecode"

    FUNCTION = "decode"
    CATEGORY = "Filmclusive/Filmmaker/Wan 2.1"

    def decode(self, **kwargs):
        return self._delegate(**kwargs)


NODE_CLASS_MAPPINGS = {
    "FilmclusiveKSamplerFilmmaker": FilmclusiveKSamplerFilmmaker,
    "FilmclusiveWanVideoModelLoaderFilmmaker": FilmclusiveWanVideoModelLoaderFilmmaker,
    "FilmclusiveWanVideoVAELoaderFilmmaker": FilmclusiveWanVideoVAELoaderFilmmaker,
    "FilmclusiveWanVideoTextEncodeCachedFilmmaker": FilmclusiveWanVideoTextEncodeCachedFilmmaker,
    "FilmclusiveWanVideoLoraSelectMultiFilmmaker": FilmclusiveWanVideoLoraSelectMultiFilmmaker,
    "FilmclusiveWanVideoSamplerFilmmaker": FilmclusiveWanVideoSamplerFilmmaker,
    "FilmclusiveWanVideoDecodeFilmmaker": FilmclusiveWanVideoDecodeFilmmaker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FilmclusiveKSamplerFilmmaker": "Filmclusive KSampler (Filmmaker)",
    "FilmclusiveWanVideoModelLoaderFilmmaker": "Filmclusive WanVideo Model Loader (Filmmaker)",
    "FilmclusiveWanVideoVAELoaderFilmmaker": "Filmclusive WanVideo VAE Loader (Filmmaker)",
    "FilmclusiveWanVideoTextEncodeCachedFilmmaker": "Filmclusive WanVideo Text Encode (Cached) (Filmmaker)",
    "FilmclusiveWanVideoLoraSelectMultiFilmmaker": "Filmclusive WanVideo Multi-LoRA (Filmmaker)",
    "FilmclusiveWanVideoSamplerFilmmaker": "Filmclusive WanVideo Sampler (Filmmaker)",
    "FilmclusiveWanVideoDecodeFilmmaker": "Filmclusive WanVideo Decode (Filmmaker)",
}
