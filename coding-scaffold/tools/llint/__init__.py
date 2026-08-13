"""llint + linear + document noise: injection-oriented cleanup (never writes source)."""

from __future__ import annotations

import re
from typing import List, Mapping, Optional, Sequence, Tuple

from .doc_noise import apply_doc_noise

_BOM = "\ufeff"
_TRAIL_WS = re.compile(r"[ \t]+$", re.MULTILINE)
_MULTI_BLANK = re.compile(r"\n{3,}")
_CRLF = re.compile(r"\r\n?")


def llint_text(
    text: str,
    *,
    doc_noise: bool = True,
    doc_noise_strategies: Optional[Sequence[Mapping[str, str]]] = None,
) -> Tuple[str, List[str]]:
    """
    Lightweight lint for LLM context: BOM, newlines, trailing ws, blank runs,
    plus optional document-noise strip (Kit-Suite clean-data strategies).
    """
    applied: List[str] = []
    out = text
    if out.startswith(_BOM):
        out = out.lstrip(_BOM)
        applied.append("llint:bom")
    if "\r" in out:
        out = _CRLF.sub("\n", out)
        applied.append("llint:newlines")
    cleaned = _TRAIL_WS.sub("", out)
    if cleaned != out:
        applied.append("llint:trailing_ws")
        out = cleaned
    collapsed = _MULTI_BLANK.sub("\n\n", out)
    if collapsed != out:
        applied.append("llint:blank_runs")
        out = collapsed
    if doc_noise:
        out, rules = apply_doc_noise(out, strategies=doc_noise_strategies)
        applied.extend(rules)
    if out.endswith("\n\n") and not text.endswith("\n\n"):
        out = out.rstrip("\n") + "\n"
    elif not out.endswith("\n") and text.endswith("\n"):
        out = out + "\n"
    return out, applied


def linearize_blocks(blocks: List[dict]) -> Tuple[List[dict], List[str]]:
    """
    Present context as a linear sequence for the model.
    Keeps ok blocks first (stable path order), skipped last with short markers.
    """
    ok = [b for b in blocks if b.get("status") == "ok" and b.get("content")]
    other = [b for b in blocks if b not in ok]
    out: List[dict] = []
    for i, b in enumerate(ok, start=1):
        nb = dict(b)
        methods = list(nb.get("methods") or [])
        methods.append(f"linear:{i}/{len(ok)}")
        nb["methods"] = methods
        nb["linearIndex"] = i
        out.append(nb)
    out.extend(other)
    return out, ["linear"] if ok else []


__all__ = ["llint_text", "linearize_blocks", "apply_doc_noise"]
