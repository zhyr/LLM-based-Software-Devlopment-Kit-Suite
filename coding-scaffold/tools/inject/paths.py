"""Shared inject helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List


def read_path_list(
    files: list | None = None,
    paths_file: str = "",
    *,
    read_stdin: bool = True,
) -> List[str]:
    paths: List[str] = []
    if files:
        paths.extend(files)
    if paths_file:
        paths.extend(
            ln.strip()
            for ln in Path(paths_file).read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        )
    if read_stdin and not sys.stdin.isatty():
        paths.extend(
            ln.strip()
            for ln in sys.stdin.read().splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        )
    seen = set()
    out: List[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out
