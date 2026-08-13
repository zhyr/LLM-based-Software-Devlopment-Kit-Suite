"""Parameter / variable naming alignment for inject packs (in-memory only)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None


def load_align_map(path: Path | None) -> Dict[str, str]:
    if path is None or not path.is_file():
        return {}
    raw = path.read_text(encoding="utf-8")
    data: Any
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML required for naming align maps")
        data = yaml.safe_load(raw) or {}
    else:
        import json

        data = json.loads(raw)
    if isinstance(data, dict) and "map" in data and isinstance(data["map"], dict):
        data = data["map"]
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items() if k and v and str(k) != str(v)}


def align_text(text: str, naming_map: Mapping[str, str]) -> Tuple[str, List[str]]:
    """Replace whole-word identifiers per map (longest keys first)."""
    if not naming_map:
        return text, []
    applied: List[str] = []
    out = text
    for src in sorted(naming_map.keys(), key=len, reverse=True):
        dst = naming_map[src]
        pattern = re.compile(rf"\b{re.escape(src)}\b")
        new_out, n = pattern.subn(dst, out)
        if n:
            applied.append(f"align:{src}->{dst}x{n}")
            out = new_out
    return out, applied


def align_config_from_policy(policy: dict, root: Path) -> Dict[str, Any]:
    block = policy.get("align") or {}
    if not isinstance(block, dict):
        block = {}
    map_path = block.get("mapFile") or ".haxitag/naming-align.yaml"
    p = root / map_path if not Path(map_path).is_absolute() else Path(map_path)
    inline = block.get("map") if isinstance(block.get("map"), dict) else {}
    file_map = load_align_map(p) if p.is_file() else {}
    merged = {**file_map, **{str(k): str(v) for k, v in inline.items()}}
    return {
        "enabled": bool(block.get("enabled", True)) and bool(merged),
        "map": merged,
        "mapFile": str(p) if p.is_file() else None,
    }


__all__ = ["align_config_from_policy", "align_text", "load_align_map"]
