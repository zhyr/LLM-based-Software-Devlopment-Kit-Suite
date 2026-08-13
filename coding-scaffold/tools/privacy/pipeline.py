"""Privacy pipeline: ordered methods like KnowledgeBase preprocessMethods."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .anonymize import redact_file_text
from .defaults import (
    DEFAULT_NOISE_GLOBS,
    DEFAULT_PII_PATTERNS,
    DEFAULT_SECRET_PATTERNS,
    METHOD_ALIASES,
    PII_FIELD_KEYS,
    PRIVACY_METHODS,
    SENSITIVE_KEYS,
)
from .denoise import collapse_whitespace, denoise_text, is_noise_path


def normalize_methods(methods: Optional[Iterable[str]]) -> List[str]:
    if not methods:
        return list(PRIVACY_METHODS)
    out: List[str] = []
    for m in methods:
        key = METHOD_ALIASES.get(m.strip(), m.strip().lower())
        if key in PRIVACY_METHODS and key not in out:
            out.append(key)
    return out or list(PRIVACY_METHODS)


def privacy_config_from_policy(policy: dict) -> Dict[str, Any]:
    block = policy.get("privacy") or {}
    if not isinstance(block, dict):
        block = {}
    return {
        "methods": normalize_methods(block.get("methods") or policy.get("privacyMethods")),
        "sensitiveKeys": block.get("sensitiveKeys") or SENSITIVE_KEYS,
        "piiFieldKeys": block.get("piiFieldKeys") or PII_FIELD_KEYS,
        "piiPatterns": block.get("piiPatterns") or DEFAULT_PII_PATTERNS,
        "secretPatterns": block.get("secretPatterns") or DEFAULT_SECRET_PATTERNS,
        "noiseGlobs": block.get("noiseGlobs") or DEFAULT_NOISE_GLOBS,
        "stripComments": bool(block.get("stripComments", False)),
        "mode": block.get("mode") or "inject",  # inject | report
    }


def apply_pipeline(
    text: str,
    *,
    methods: Sequence[str],
    cfg: Dict[str, Any],
) -> Tuple[str, List[str]]:
    """Apply clean → denoise → redact in given order (KB switch loop)."""
    applied: List[str] = []
    result = text
    for method in methods:
        if method == "clean":
            cleaned = collapse_whitespace(result)
            if cleaned != result:
                applied.append("清洗")
            result = cleaned
        elif method == "denoise":
            result, rules = denoise_text(
                result, strip_comments=bool(cfg.get("stripComments"))
            )
            if rules:
                applied.append("去噪")
                applied.extend(rules)
        elif method == "redact":
            result, rules = redact_file_text(
                result,
                pii_field_keys=cfg.get("piiFieldKeys"),
                sensitive_keys=cfg.get("sensitiveKeys"),
                pii_patterns=cfg.get("piiPatterns"),
                secret_patterns=cfg.get("secretPatterns"),
            )
            if rules:
                applied.append("脱敏")
                applied.extend(rules)
    return result, applied


__all__ = [
    "apply_pipeline",
    "is_noise_path",
    "normalize_methods",
    "privacy_config_from_policy",
]
