"""Recursive sanitize inspired by HaxiTAG-AI-CMS/src/utils/logger.ts."""

from __future__ import annotations

import re
from typing import Any, Iterable, Optional, Set

from .defaults import REDACTED, SANITIZE_MAX_DEPTH, SENSITIVE_KEYS

_URI_PASS = re.compile(r"(:\/\/[^:]+):([^@]+)@")


def is_sensitive_key(key: str, sensitive_keys: Optional[Iterable[str]] = None) -> bool:
    keys = list(sensitive_keys) if sensitive_keys is not None else SENSITIVE_KEYS
    kl = key.lower()
    return any(sk in kl for sk in keys)


def sanitize(
    data: Any,
    *,
    sensitive_keys: Optional[Iterable[str]] = None,
    depth: int = 0,
    seen: Optional[Set[int]] = None,
) -> Any:
    if data is None:
        return data
    if depth > SANITIZE_MAX_DEPTH:
        return "[Max depth]"

    if isinstance(data, Exception):
        return {"name": type(data).__name__, "message": str(data)}

    if isinstance(data, str):
        if "://" in data and ("@" in data or "password" in data.lower()):
            return _URI_PASS.sub(r"\1:****@", data)
        return data

    if isinstance(data, list):
        return [
            sanitize(item, sensitive_keys=sensitive_keys, depth=depth + 1, seen=seen)
            for item in data
        ]

    if isinstance(data, dict):
        set_ids = seen if seen is not None else set()
        obj_id = id(data)
        if obj_id in set_ids:
            return "[Circular]"
        set_ids.add(obj_id)
        out: dict = {}
        for key, val in data.items():
            if is_sensitive_key(str(key), sensitive_keys):
                out[key] = REDACTED
            else:
                out[key] = sanitize(
                    val, sensitive_keys=sensitive_keys, depth=depth + 1, seen=set_ids
                )
        return out

    return data
