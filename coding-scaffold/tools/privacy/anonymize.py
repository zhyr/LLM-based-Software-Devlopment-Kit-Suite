"""Content anonymization inspired by KnowledgeBase preprocess.ts anonymizeData."""

from __future__ import annotations

import json
import re
from typing import Any, Iterable, List, Optional, Sequence, Tuple

from .defaults import (
    CARD_MASK,
    DEFAULT_CARD_PATTERN,
    DEFAULT_PII_PATTERNS,
    DEFAULT_SECRET_PATTERNS,
    PII_FIELD_KEYS,
    PII_MASK,
)
from .sanitize import is_sensitive_key, sanitize


def _compile_patterns(patterns: Sequence[str]) -> List[re.Pattern[str]]:
    out: List[re.Pattern[str]] = []
    for p in patterns:
        try:
            out.append(re.compile(p))
        except re.error:
            continue
    return out


def _replace_secret(match: re.Match[str]) -> str:
    if match.lastindex and match.lastindex >= 3:
        return f"{match.group(1)}{match.group(2)}{PII_MASK}{match.group(2)}"
    return PII_MASK


def anonymize_text(
    text: str,
    *,
    pii_patterns: Optional[Sequence[str]] = None,
    secret_patterns: Optional[Sequence[str]] = None,
) -> Tuple[str, List[str]]:
    applied: List[str] = []
    result = text

    card_re = re.compile(DEFAULT_CARD_PATTERN)
    if card_re.search(result):
        result = card_re.sub(CARD_MASK, result)
        applied.append("card_mask")

    for i, cre in enumerate(_compile_patterns(pii_patterns or DEFAULT_PII_PATTERNS)):
        if cre.pattern in (card_re.pattern, r"\b\d{4}[\d-]{0,8}\d{4}\b"):
            continue
        if cre.search(result):
            result = cre.sub(PII_MASK, result)
            applied.append(f"pii_pattern[{i}]")

    for i, cre in enumerate(_compile_patterns(secret_patterns or DEFAULT_SECRET_PATTERNS)):
        if cre.search(result):
            result = cre.sub(_replace_secret, result)
            applied.append(f"secret_pattern[{i}]")

    return result, applied


def anonymize_value(
    item: Any,
    *,
    pii_field_keys: Optional[Iterable[str]] = None,
    sensitive_keys: Optional[Iterable[str]] = None,
    pii_patterns: Optional[Sequence[str]] = None,
    secret_patterns: Optional[Sequence[str]] = None,
) -> Any:
    fields = {k.lower() for k in (pii_field_keys or PII_FIELD_KEYS)}

    if isinstance(item, str):
        redacted, _ = anonymize_text(
            item, pii_patterns=pii_patterns, secret_patterns=secret_patterns
        )
        return redacted

    if isinstance(item, list):
        return [
            anonymize_value(
                x,
                pii_field_keys=fields,
                sensitive_keys=sensitive_keys,
                pii_patterns=pii_patterns,
                secret_patterns=secret_patterns,
            )
            for x in item
        ]

    if isinstance(item, dict):
        out = {}
        for key, value in item.items():
            kl = str(key).lower()
            if kl in fields or is_sensitive_key(str(key), sensitive_keys):
                out[key] = PII_MASK if kl in fields else "***REDACTED***"
            else:
                out[key] = anonymize_value(
                    value,
                    pii_field_keys=fields,
                    sensitive_keys=sensitive_keys,
                    pii_patterns=pii_patterns,
                    secret_patterns=secret_patterns,
                )
        return out

    return item


def try_parse_structured(text: str) -> Optional[Any]:
    stripped = text.strip()
    if not stripped:
        return None
    if stripped[0] in "{[":
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return None
    return None


def redact_file_text(
    text: str,
    *,
    pii_field_keys: Optional[Iterable[str]] = None,
    sensitive_keys: Optional[Iterable[str]] = None,
    pii_patterns: Optional[Sequence[str]] = None,
    secret_patterns: Optional[Sequence[str]] = None,
) -> Tuple[str, List[str]]:
    applied: List[str] = []
    structured = try_parse_structured(text)
    if structured is not None:
        sanitized = sanitize(structured, sensitive_keys=sensitive_keys)
        applied.append("sanitize_sensitive_keys")
        anonymized = anonymize_value(
            sanitized,
            pii_field_keys=pii_field_keys,
            sensitive_keys=sensitive_keys,
            pii_patterns=pii_patterns,
            secret_patterns=secret_patterns,
        )
        applied.append("anonymize_structured")
        return json.dumps(anonymized, ensure_ascii=False, indent=2) + "\n", applied

    redacted, rules = anonymize_text(
        text, pii_patterns=pii_patterns, secret_patterns=secret_patterns
    )
    if rules:
        applied.extend(rules)
    return redacted, applied
