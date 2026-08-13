"""Shared policy helpers for validate / privacy CLIs."""

from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path
from typing import Iterable

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None


def load_policy(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ValueError(f"Policy must be a mapping: {path}")
        return data
    return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> dict:
    """Fallback for flat lists; nested `privacy:` needs PyYAML."""
    data: dict = {
        "include": [],
        "exclude": [],
        "denyNames": [],
        "secretPatterns": [],
    }
    current_list: str | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if re.match(r"^[A-Za-z_][\w]*:\s*$", line):
            key = line.split(":", 1)[0].strip()
            current_list = key if key in data and isinstance(data[key], list) else None
            continue
        if re.match(r"^[A-Za-z_][\w]*:\s+\S", line):
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key in ("name", "description", "notes"):
                data[key] = val
            elif key in ("version", "maxFileBytes", "maxTotalBytes"):
                data[key] = int(val)
            elif key == "allowBinary":
                data[key] = val.lower() in ("true", "yes", "1")
            current_list = None
            continue
        if current_list and line.strip().startswith("- "):
            data.setdefault(current_list, []).append(
                line.strip()[2:].strip().strip('"').strip("'")
            )
    if not data.get("include"):
        data["include"] = ["**/*"]
    return data


def match_any(path: str, patterns: Iterable[str]) -> bool:
    return any(
        fnmatch.fnmatch(path, p) or fnmatch.fnmatch(os.path.basename(path), p)
        for p in patterns
    )


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d
            not in {
                ".git",
                "node_modules",
                ".next",
                "dist",
                "build",
                ".venv",
                "venv",
                "__pycache__",
            }
        ]
        for name in filenames:
            yield Path(dirpath) / name


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def has_yaml() -> bool:
    return yaml is not None
