"""Document noise cleaning — ported from Kit-Suite clean-data.py (in-memory).

Removes crawler/export footers (page counts, URL stamps) from text before
LLM inject. Never writes source files.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Mapping, Optional, Sequence, Tuple

# Strategies aligned with repo-root clean-data.py CLEANING_STRATEGIES (+ a few commons)
DEFAULT_DOC_NOISE_STRATEGIES: List[Mapping[str, str]] = [
    {
        "name": "page_word_count_zh",
        "pattern": r"\(共\d+页,?\s*全文\d+字\)",
        "replacement": "",
    },
    {
        "name": "word_count_url_zh",
        "pattern": r"\(本页字数:\s*\d+,\s*URL:\s*[^\)]+\)",
        "replacement": "",
    },
    {
        "name": "page_word_count_en",
        "pattern": r"\(\s*\d+\s+pages?,\s*(?:full\s*text\s*)?\d+\s+words?\s*\)",
        "replacement": "",
    },
    {
        "name": "url_stamp",
        "pattern": r"\(\s*URL:\s*https?://[^\)]+\)",
        "replacement": "",
    },
    {
        "name": "crawl_timestamp_prefix",
        "pattern": r"(?m)^\[?\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}\]?\s*Crawled from:\s*.+\n?",
        "replacement": "",
    },
]


def _compile_strategies(
    strategies: Optional[Sequence[Mapping[str, str]]],
) -> List[Tuple[str, re.Pattern[str], str]]:
    compiled: List[Tuple[str, re.Pattern[str], str]] = []
    for s in strategies or DEFAULT_DOC_NOISE_STRATEGIES:
        name = str(s.get("name") or "doc_noise")
        pattern = str(s.get("pattern") or "")
        if not pattern:
            continue
        try:
            cre = re.compile(pattern)
        except re.error:
            continue
        replacement = str(s.get("replacement") if s.get("replacement") is not None else "")
        compiled.append((name, cre, replacement))
    return compiled


def apply_doc_noise(
    text: str,
    *,
    strategies: Optional[Sequence[Mapping[str, str]]] = None,
) -> Tuple[str, List[str]]:
    """Apply document-noise regex strategies; return text + applied rule tags."""
    applied: List[str] = []
    out = text
    for name, cre, replacement in _compile_strategies(strategies):
        new_out, n = cre.subn(replacement, out)
        if n:
            applied.append(f"doc_noise:{name}x{n}")
            out = new_out
    # collapse leftover blank runs after removals
    if applied:
        collapsed = re.sub(r"\n{3,}", "\n\n", out).strip() + ("\n" if text.endswith("\n") else "")
        if collapsed != out:
            applied.append("doc_noise:blank_runs")
            out = collapsed
    return out, applied


def strategies_from_policy(policy: dict) -> Optional[List[Mapping[str, str]]]:
    """Optional ime.docNoiseStrategies override; None → defaults."""
    ime = policy.get("ime") if isinstance(policy.get("ime"), dict) else {}
    raw = ime.get("docNoiseStrategies") if isinstance(ime, dict) else None
    if not isinstance(raw, list) or not raw:
        return None
    out: List[Mapping[str, str]] = []
    for item in raw:
        if isinstance(item, dict) and item.get("pattern"):
            out.append(
                {
                    "name": str(item.get("name") or "custom"),
                    "pattern": str(item["pattern"]),
                    "replacement": str(item.get("replacement") or ""),
                }
            )
    return out or None


__all__ = [
    "DEFAULT_DOC_NOISE_STRATEGIES",
    "apply_doc_noise",
    "strategies_from_policy",
]
