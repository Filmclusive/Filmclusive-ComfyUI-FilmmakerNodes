import json
import os
import re
import shutil
import subprocess
from datetime import datetime

import folder_paths
import numpy as np
from PIL import Image


try:
    _LANCZOS = Image.Resampling.LANCZOS
except Exception:
    _LANCZOS = Image.LANCZOS


def _norm_subfolder(*parts: str) -> str:
    return "/".join([p for p in parts if p])


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


def _write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _resolve_ffmpeg() -> str:
    env_path = os.environ.get("FFMPEG_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    which_path = shutil.which("ffmpeg")
    if which_path:
        return which_path

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return ""


def _resolve_video_source(video=None, video_info=None, video_native=None, video_path: str | None = None) -> str:
    """
    Best-effort extraction of an on-disk video path from common ComfyUI/VHS payloads.
    Returns "" when unknown/unavailable.
    """

    def from_dict(payload: dict) -> str:
        for key in ("fullpath", "path", "file", "video", "filename", "name"):
            value = payload.get(key)
            if not isinstance(value, str) or not value.strip():
                continue
            value = value.strip()
            if os.path.isabs(value) and os.path.isfile(value):
                return value

            subfolder = payload.get("subfolder") or ""
            kind = payload.get("type")
            base = None
            if kind == "input":
                base = folder_paths.get_input_directory()
            elif kind == "output":
                base = folder_paths.get_output_directory()
            elif kind == "temp" and hasattr(folder_paths, "get_temp_directory"):
                base = folder_paths.get_temp_directory()
            if base:
                candidate = os.path.join(base, subfolder, value)
                if os.path.isfile(candidate):
                    return candidate
        return ""

    if isinstance(video_path, str) and video_path.strip():
        candidate = video_path.strip()
        if os.path.isfile(candidate):
            return candidate

    for payload in (video, video_info, video_native):
        if isinstance(payload, str) and payload.strip() and os.path.isfile(payload.strip()):
            return payload.strip()
        if isinstance(payload, dict):
            found = from_dict(payload)
            if found:
                return found
        if isinstance(payload, (list, tuple)) and len(payload) == 1:
            inner = payload[0]
            if isinstance(inner, dict):
                found = from_dict(inner)
                if found:
                    return found
            if isinstance(inner, str) and inner.strip() and os.path.isfile(inner.strip()):
                return inner.strip()

    return ""


def _frame_to_rgb_u8(frame, width: int, height: int) -> np.ndarray:
    arr = frame.cpu().numpy()
    if arr.ndim != 3:
        raise ValueError(f"Expected frame HWC, got shape {arr.shape}")
    if arr.shape[2] < 3:
        raise ValueError(f"Expected 3+ channels, got shape {arr.shape}")

    arr = np.clip(arr[..., :3] * 255.0, 0, 255).astype(np.uint8)
    if arr.shape[1] != width or arr.shape[0] != height:
        img = Image.fromarray(arr, mode="RGB")
        img = img.resize((width, height), resample=_LANCZOS)
        arr = np.asarray(img, dtype=np.uint8)
    if not arr.flags["C_CONTIGUOUS"]:
        arr = np.ascontiguousarray(arr)
    return arr


class _FilmclusiveSaveVideoBase:
    CODEC = ""
    EXT = ""
    DISPLAY = ""

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "fps": ("INT", {"default": 24, "min": 1, "max": 240}),
            "project_name": ("STRING", {"default": "FilmclusiveProject"}),
            "scene": ("STRING", {"default": "01"}),
            "shot": ("STRING", {"default": "A"}),
            "description": ("STRING", {"default": "render"}),
            "save_comparison_video": ("BOOLEAN", {"default": True}),
        }
        required.update(cls._format_inputs())
        return {
            "required": required,
            "optional": {
                "images": ("IMAGE",),
                "comparison_images": ("IMAGE",),
                "video": ("VHS_VIDEO",),
                "video_info": ("VHS_VIDEOINFO",),
                "video_native": ("VIDEO",),
                "video_path": ("STRING", {"default": ""}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    @classmethod
    def _format_inputs(cls):
        return {}

    RETURN_TYPES = ("STRING", "INT", "STRING", "STRING", "STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = ("file_path", "take", "output_dir", "project_name", "scene", "shot", "fps", "comparison_file_path")
    FUNCTION = "save"
    OUTPUT_NODE = True
    CATEGORY = "Filmclusive"

    def _get_next_take(self, folder: str, prefix: str) -> int:
        if not os.path.exists(folder):
            return 1

        takes = []
        for filename in os.listdir(folder):
            if not filename.startswith(prefix):
                continue
            remainder = filename[len(prefix) :]
            try:
                take_text = remainder.split("_", 1)[0].lstrip("0") or "0"
                takes.append(int(take_text))
            except Exception:
                continue
        return (max(takes) + 1) if takes else 1

    def _ffmpeg_args(self, *, ffmpeg: str, fps: int, width: int, height: int, output_path: str, **kwargs):
        raise NotImplementedError

    def _thumbnail_path(self, base_name: str) -> str:
        return f"{base_name}_thumb.png"

    def _encode_video(self, *, ffmpeg: str, frames, fps: int, output_path: str, width: int, height: int, **kwargs) -> None:
        args = self._ffmpeg_args(
            ffmpeg=ffmpeg,
            fps=int(fps),
            width=width,
            height=height,
            output_path=output_path,
            **kwargs,
        )

        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            for frame in frames:
                rgb = _frame_to_rgb_u8(frame, width, height)
                proc.stdin.write(rgb.tobytes())
            proc.stdin.close()
            stderr = proc.stderr.read().decode("utf-8", errors="replace")
            rc = proc.wait()
        finally:
            try:
                if proc.stdin and not proc.stdin.closed:
                    proc.stdin.close()
            except Exception:
                pass

        if rc != 0:
            tail = "\n".join(stderr.strip().splitlines()[-30:])
            raise RuntimeError(f"ffmpeg failed (exit {rc}). Last output:\n{tail}")

    def _save_bundle(
        self,
        *,
        ffmpeg: str,
        frames,
        fps: int,
        project_name: str,
        scene: str,
        shot: str,
        take: int,
        description: str,
        timestamp: str,
        shot_folder: str,
        safe_project: str,
        safe_scene: str,
        safe_shot: str,
        base_name: str,
        prompt,
        workflow,
        meta_extra: dict | None = None,
        settings: dict | None = None,
        **kwargs,
    ):
        if not frames:
            raise ValueError("No frames provided.")

        first = frames[0].cpu().numpy()
        if first.ndim != 3 or first.shape[2] < 3:
            raise ValueError(f"Expected HWC RGB frames, got shape {first.shape}")
        height, width = int(first.shape[0]), int(first.shape[1])

        video_filename = f"{base_name}.{self.EXT}"
        video_path = os.path.join(shot_folder, video_filename)

        meta = {
            "project_name": project_name,
            "scene": scene,
            "shot": shot,
            "take": take,
            "description": description,
            "timestamp": timestamp,
            "fps": int(fps),
            "frames": len(frames),
            "width": width,
            "height": height,
            "format": self.EXT,
            "codec": self.CODEC,
            "prompt": prompt,
            "workflow": workflow,
            "settings": (settings if settings is not None else kwargs),
        }
        if meta_extra:
            meta.update(meta_extra)

        _write_json(os.path.join(shot_folder, f"{base_name}.meta.json"), meta)
        if prompt is not None:
            _write_json(os.path.join(shot_folder, f"{base_name}.prompt.json"), prompt)
        if workflow is not None:
            _write_json(os.path.join(shot_folder, f"{base_name}.workflow.json"), workflow)

        self._encode_video(
            ffmpeg=ffmpeg,
            frames=frames,
            fps=int(fps),
            output_path=video_path,
            width=width,
            height=height,
            **kwargs,
        )

        thumb_filename = self._thumbnail_path(base_name)
        thumb_path = os.path.join(shot_folder, thumb_filename)
        thumb_img = Image.fromarray(np.clip(first[..., :3] * 255.0, 0, 255).astype(np.uint8), mode="RGB")
        thumb_img.save(thumb_path)

        subfolder = _norm_subfolder(safe_project, safe_scene, safe_shot)
        preview_item = {"filename": thumb_filename, "subfolder": subfolder, "type": "output"}
        video_item = {"filename": video_filename, "subfolder": subfolder, "type": "output"}

        return video_path, preview_item, video_item

    def save(
        self,
        fps,
        project_name,
        scene,
        shot,
        description,
        save_comparison_video,
        images=None,
        comparison_images=None,
        video=None,
        video_info=None,
        video_native=None,
        video_path="",
        prompt=None,
        extra_pnginfo=None,
        **kwargs,
    ):
        source_video_path = _resolve_video_source(video=video, video_info=video_info, video_native=video_native, video_path=video_path)
        ffmpeg = _resolve_ffmpeg()

        safe_project = _sanitize_segment(project_name, "project")
        safe_scene = _sanitize_segment(scene, "scene_1")
        safe_shot = _sanitize_segment(shot, "shot_A")
        safe_description = _sanitize_segment(description, "render")

        shot_folder = os.path.join(self.output_dir, safe_project, safe_scene, safe_shot)
        os.makedirs(shot_folder, exist_ok=True)
        subfolder = _norm_subfolder(safe_project, safe_scene, safe_shot)

        base_prefix = f"{safe_scene}_{safe_shot}_take_"
        take = self._get_next_take(shot_folder, base_prefix)

        base_name = f"{safe_scene}_{safe_shot}_take_{take:02}_{safe_description}"
        timestamp = datetime.now().isoformat(timespec="seconds")

        workflow = None
        if isinstance(extra_pnginfo, dict):
            workflow = extra_pnginfo.get("workflow") or extra_pnginfo.get("Workflow")

        format_keys = set(type(self)._format_inputs().keys())
        legacy_map = {
            "quality_crf": "crf",
            "speed_preset": "preset",
        }
        for new_key, old_key in legacy_map.items():
            if new_key in format_keys and new_key not in kwargs and old_key in kwargs:
                kwargs[new_key] = kwargs[old_key]

        encode_kwargs = {k: v for k, v in kwargs.items() if k in format_keys}

        image_preview_list = []
        video_preview_list = []

        if source_video_path:
            src_ext = os.path.splitext(source_video_path)[1].lstrip(".").lower() or self.EXT
            video_filename = f"{base_name}.{src_ext}"
            main_video_path = os.path.join(shot_folder, video_filename)
            shutil.copy2(source_video_path, main_video_path)

            video_preview_list.append({"filename": video_filename, "subfolder": subfolder, "type": "output"})

            # Write metadata bundle even when we "copy" instead of encoding.
            meta = {
                "project_name": project_name,
                "scene": scene,
                "shot": shot,
                "take": take,
                "description": description,
                "timestamp": timestamp,
                "fps": int(fps),
                "frames": None,
                "width": None,
                "height": None,
                "format": src_ext,
                "codec": "copy",
                "prompt": prompt,
                "workflow": workflow,
                "settings": kwargs,
            }
            if isinstance(video_info, dict):
                for k_src, k_dst in (("fps", "fps"), ("frame_count", "frames"), ("frames", "frames"), ("width", "width"), ("height", "height")):
                    if k_src in video_info and meta.get(k_dst) in (None, int(fps)):
                        meta[k_dst] = video_info.get(k_src)
            _write_json(os.path.join(shot_folder, f"{base_name}.meta.json"), meta)
            if prompt is not None:
                _write_json(os.path.join(shot_folder, f"{base_name}.prompt.json"), prompt)
            if workflow is not None:
                _write_json(os.path.join(shot_folder, f"{base_name}.workflow.json"), workflow)

            # Thumbnail: prefer first provided frame; else attempt ffmpeg.
            thumb_filename = self._thumbnail_path(base_name)
            thumb_path = os.path.join(shot_folder, thumb_filename)
            try:
                frames = list(images) if images is not None else []
                if frames:
                    first = frames[0].cpu().numpy()
                    thumb_img = Image.fromarray(np.clip(first[..., :3] * 255.0, 0, 255).astype(np.uint8), mode="RGB")
                    thumb_img.save(thumb_path)
                elif ffmpeg:
                    subprocess.run(
                        [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", main_video_path, "-frames:v", "1", thumb_path],
                        check=True,
                    )
            except Exception as e:
                print(f"[Filmclusive] Thumbnail generation skipped: {e}")

            if os.path.isfile(thumb_path):
                image_preview_list.append({"filename": thumb_filename, "subfolder": subfolder, "type": "output"})

            video_path = main_video_path
        else:
            frames = list(images) if images is not None else []
            if not frames:
                raise ValueError("Provide either `images` frames or a `video` / `video_info` / `video_path` input.")
            if not ffmpeg:
                raise RuntimeError("ffmpeg not found. Install ffmpeg or set FFMPEG_PATH to the ffmpeg binary path.")

            video_path, main_image_preview, main_video_preview = self._save_bundle(
                ffmpeg=ffmpeg,
                frames=frames,
                fps=int(fps),
                project_name=project_name,
                scene=scene,
                shot=shot,
                take=take,
                description=description,
                timestamp=timestamp,
                shot_folder=shot_folder,
                safe_project=safe_project,
                safe_scene=safe_scene,
                safe_shot=safe_shot,
                base_name=base_name,
                prompt=prompt,
                workflow=workflow,
                settings=kwargs,
                **encode_kwargs,
            )

            image_preview_list.append(main_image_preview)
            video_preview_list.append(main_video_preview)

        comparison_video_path = ""
        try:
            if bool(save_comparison_video):
                compare_frames = list(comparison_images) if comparison_images is not None else []
                if compare_frames:
                    compare_base_name = f"{base_name}_compare"
                    if not ffmpeg:
                        raise RuntimeError("ffmpeg not found. Install ffmpeg or set FFMPEG_PATH to the ffmpeg binary path.")
                    comparison_video_path, compare_image_preview, compare_video_preview = self._save_bundle(
                        ffmpeg=ffmpeg,
                        frames=compare_frames,
                        fps=int(fps),
                        project_name=project_name,
                        scene=scene,
                        shot=shot,
                        take=take,
                        description=f"{description} (compare)",
                        timestamp=timestamp,
                        shot_folder=shot_folder,
                        safe_project=safe_project,
                        safe_scene=safe_scene,
                        safe_shot=safe_shot,
                        base_name=compare_base_name,
                        prompt=prompt,
                        workflow=workflow,
                        meta_extra={
                            "comparison": True,
                            "comparison_of": os.path.basename(video_path),
                        },
                        settings=kwargs,
                        **encode_kwargs,
                    )
                    image_preview_list.append(compare_image_preview)
                    video_preview_list.append(compare_video_preview)
        except Exception as e:
            print(f"[Filmclusive] Comparison save skipped: {e}")

        if comparison_video_path:
            print(f"[Filmclusive] Saved video take {take:02} to {video_path} (+ comparison)")
        else:
            print(f"[Filmclusive] Saved video take {take:02} to {video_path}")

        output_dir = self.output_dir.replace("\\", "/")
        pretty_output_dir = "/".join(output_dir.split("/")[-2:]) if "/" in output_dir else output_dir
        return {
            "ui": {"images": (image_preview_list + video_preview_list), "videos": video_preview_list},
            "result": (
                video_path,
                int(take),
                pretty_output_dir,
                str(project_name),
                str(scene),
                str(shot),
                int(fps),
                str(comparison_video_path or ""),
            ),
        }


class FilmclusiveSaveVideoMP4(_FilmclusiveSaveVideoBase):
    CODEC = "libx264"
    EXT = "mp4"
    DISPLAY = "Filmclusive Save Video (MP4)"

    @classmethod
    def _format_inputs(cls):
        return {
            "quality_crf": (
                "INT",
                {
                    "default": 18,
                    "min": 0,
                    "max": 51,
                    "label": "Quality (CRF 0–51)",
                    "tooltip": "Quality (CRF 0–51). Lower = higher quality + larger file. Typical range: 18 (high) to 23 (smaller).",
                },
            ),
            "speed_preset": (
                [
                    "ultrafast",
                    "superfast",
                    "veryfast",
                    "faster",
                    "fast",
                    "medium",
                    "slow",
                    "slower",
                    "veryslow",
                ],
                {
                    "default": "medium",
                    "label": "Speed (preset)",
                    "tooltip": "Encoding speed preset. Faster = quicker renders, bigger files. Slower = smaller files, longer renders.",
                },
            ),
        }

    def _ffmpeg_args(
        self,
        *,
        ffmpeg: str,
        fps: int,
        width: int,
        height: int,
        output_path: str,
        quality_crf: int,
        speed_preset: str,
    ):
        return [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(fps),
            "-i",
            "pipe:0",
            "-an",
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            str(speed_preset),
            "-crf",
            str(int(quality_crf)),
            "-movflags",
            "+faststart",
            output_path,
        ]


class FilmclusiveSaveVideoSimple(FilmclusiveSaveVideoMP4):
    DISPLAY = "Filmclusive Save Video"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "fps": ("INT", {"default": 24, "min": 1, "max": 240}),
                "project_name": ("STRING", {"default": "FilmclusiveProject"}),
                "scene": ("STRING", {"default": "01"}),
                "shot": ("STRING", {"default": "A"}),
                "description": ("STRING", {"default": "render"}),
                "output_dir_hint": ("STRING", {"default": "ComfyUI/output"}),
                "save_comparison_video": ("BOOLEAN", {"default": True}),
                "quality_crf": (
                    "INT",
                    {
                        "default": 18,
                        "min": 0,
                        "max": 51,
                        "label": "Quality (CRF 0–51)",
                        "tooltip": "Quality (CRF 0–51). Lower = higher quality + larger file. Typical range: 18 (high) to 23 (smaller).",
                    },
                ),
                "speed_preset": (
                    [
                        "ultrafast",
                        "superfast",
                        "veryfast",
                        "faster",
                        "fast",
                        "medium",
                        "slow",
                        "slower",
                        "veryslow",
                    ],
                    {
                        "default": "medium",
                        "label": "Speed (preset)",
                        "tooltip": "Encoding speed preset. Faster = quicker renders, bigger files. Slower = smaller files, longer renders.",
                    },
                ),
            },
            "optional": {
                "images": ("IMAGE",),
                "comparison_images": ("IMAGE",),
                "video": ("VHS_VIDEO",),
                "video_info": ("VHS_VIDEOINFO",),
                "video_native": ("VIDEO",),
                "video_path": ("STRING", {"default": ""}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    def save(self, *args, **kwargs):
        kwargs.setdefault("quality_crf", 18)
        kwargs.setdefault("speed_preset", "medium")
        return super().save(*args, **kwargs)


class FilmclusiveSaveVideoWebM(_FilmclusiveSaveVideoBase):
    CODEC = "libvpx-vp9"
    EXT = "webm"
    DISPLAY = "Filmclusive Save Video (WebM)"

    @classmethod
    def _format_inputs(cls):
        return {
            "crf": ("INT", {"default": 32, "min": 0, "max": 63}),
            "cpu_used": ("INT", {"default": 4, "min": 0, "max": 8}),
        }

    def _ffmpeg_args(self, *, ffmpeg: str, fps: int, width: int, height: int, output_path: str, crf: int, cpu_used: int):
        return [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(fps),
            "-i",
            "pipe:0",
            "-an",
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v",
            "libvpx-vp9",
            "-crf",
            str(int(crf)),
            "-b:v",
            "0",
            "-deadline",
            "good",
            "-cpu-used",
            str(int(cpu_used)),
            "-pix_fmt",
            "yuv420p",
            output_path,
        ]


class FilmclusiveSaveVideoGIF(_FilmclusiveSaveVideoBase):
    CODEC = "gif"
    EXT = "gif"
    DISPLAY = "Filmclusive Save Video (GIF)"

    @classmethod
    def _format_inputs(cls):
        return {
            "max_width": ("INT", {"default": 0, "min": 0, "max": 4096}),
            "dither": ("STRING", {"default": "bayer"}),
        }

    def _ffmpeg_args(self, *, ffmpeg: str, fps: int, width: int, height: int, output_path: str, max_width: int, dither: str):
        if int(max_width) > 0:
            scale = f"scale=min({int(max_width)},iw):-1:flags=lanczos"
        else:
            scale = "scale=iw:ih:flags=lanczos"

        filter_complex = (
            f"[0:v]fps={int(fps)},{scale},split[a][b];"
            f"[a]palettegen=max_colors=256[p];"
            f"[b][p]paletteuse=dither={dither}"
        )

        return [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(fps),
            "-i",
            "pipe:0",
            "-filter_complex",
            filter_complex,
            "-loop",
            "0",
            output_path,
        ]


NODE_CLASS_MAPPINGS = {
    "FilmclusiveSaveVideo": FilmclusiveSaveVideoSimple,
    "FilmclusiveSaveVideoMP4": FilmclusiveSaveVideoMP4,
    "FilmclusiveSaveVideoWebM": FilmclusiveSaveVideoWebM,
    "FilmclusiveSaveVideoGIF": FilmclusiveSaveVideoGIF,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FilmclusiveSaveVideo": "Filmclusive Save Video",
    "FilmclusiveSaveVideoMP4": FilmclusiveSaveVideoMP4.DISPLAY,
    "FilmclusiveSaveVideoWebM": FilmclusiveSaveVideoWebM.DISPLAY,
    "FilmclusiveSaveVideoGIF": FilmclusiveSaveVideoGIF.DISPLAY,
}
