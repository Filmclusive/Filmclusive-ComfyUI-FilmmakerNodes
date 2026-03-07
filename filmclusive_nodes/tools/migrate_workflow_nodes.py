#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


TYPE_REPLACEMENTS = {
    # Core SD sampler
    "KSampler": "FilmclusiveKSamplerFilmmaker",
    # Wan 2.1 pipeline (as seen in Filmclusive-Video2Video_PhotoRef-wan_2_1_14B_MoCha.json)
    "WanVideoModelLoader": "FilmclusiveWanVideoModelLoaderFilmmaker",
    "WanVideoVAELoader": "FilmclusiveWanVideoVAELoaderFilmmaker",
    "WanVideoTextEncodeCached": "FilmclusiveWanVideoTextEncodeCachedFilmmaker",
    "WanVideoLoraSelectMulti": "FilmclusiveWanVideoLoraSelectMultiFilmmaker",
    "WanVideoSampler": "FilmclusiveWanVideoSamplerFilmmaker",
    "WanVideoDecode": "FilmclusiveWanVideoDecodeFilmmaker",
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _dump_json(path: Path, data) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _migrate_graph_format(data: dict) -> tuple[dict, dict[str, int]]:
    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("Unsupported JSON format: expected a top-level `nodes` list (ComfyUI graph JSON).")

    changed: dict[str, int] = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        old_type = node.get("type")
        if old_type not in TYPE_REPLACEMENTS:
            continue
        new_type = TYPE_REPLACEMENTS[old_type]
        node["type"] = new_type
        props = node.get("properties")
        if isinstance(props, dict) and props.get("Node name for S&R") == old_type:
            props["Node name for S&R"] = new_type
        changed[old_type] = changed.get(old_type, 0) + 1
    return data, changed


def main() -> int:
    p = argparse.ArgumentParser(description="Replace node types in a ComfyUI workflow JSON with Filmclusive filmmaker nodes.")
    p.add_argument("input", type=Path, help="Path to the input workflow JSON.")
    p.add_argument("output", type=Path, help="Path to write the migrated workflow JSON.")
    args = p.parse_args()

    data = _load_json(args.input)
    if not isinstance(data, dict):
        raise SystemExit("Unsupported JSON: expected an object at the top level.")

    migrated, changed = _migrate_graph_format(data)
    _dump_json(args.output, migrated)

    total = sum(changed.values())
    print(f"[Filmclusive] Migrated workflow written to: {args.output}")
    print(f"[Filmclusive] Replaced {total} node(s).")
    for k in sorted(changed, key=lambda x: (-changed[x], x)):
        print(f"  - {k} -> {TYPE_REPLACEMENTS[k]}  (x{changed[k]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

