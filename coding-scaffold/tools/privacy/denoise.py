"""Denoise for private-repo context (KB「去噪压缩」面向代码仓的落地)."""

from __future__ import annotations

import fnmatch
import os
import re
from typing import Iterable, List, Sequence, Tuple


def collapse_whitespace(text: str) -> str:
    """Light clean: trim lines, collapse 3+ blank lines → 1 (KB cleanData spirit)."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    out: List[str] = []
    blank_run = 0
    for ln in lines:
        if not ln.strip():
            blank_run += 1
            if blank_run <= 1:
                out.append("")
            continue
        blank_run = 0
        out.append(ln)
    return "\n".join(out).strip() + ("\n" if text.endswith("\n") else "")


def strip_block_comments_light(text: str) -> str:
    """Optional noise reduction for C-like sources; keep strings naive-safe enough for policy previews."""
    # Remove /* ... */ then // line comments — best-effort, not a full parser.
    no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    no_line = re.sub(r"(^|[^:])//.*?$", r"\1", no_block, flags=re.M)
    return no_line


def is_noise_path(rel_path: str, noise_globs: Sequence[str]) -> bool:
    base = os.path.basename(rel_path)
    for g in noise_globs:
        if fnmatch.fnmatch(rel_path, g) or fnmatch.fnmatch(base, g):
            return True
    return False


def denoise_text(text: str, *, strip_comments: bool = False) -> Tuple[str, List[str]]:
    applied: List[str] = []
    result = text
    if strip_comments:
        result = strip_block_comments_light(result)
        applied.append("strip_comments_light")
    cleaned = collapse_whitespace(result)
    if cleaned != text:
        applied.append("collapse_whitespace")
    return cleaned, applied
