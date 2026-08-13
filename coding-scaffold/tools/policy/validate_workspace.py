#!/usr/bin/env python3
"""Validate a workspace against a HaxiTAG workspace-policy YAML."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from policy.common import has_yaml, iter_files, load_policy, match_any, rel

TEXT_SAMPLE_BYTES = 64 * 1024


def validate(root: Path, policy: dict) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    include = policy.get("include") or ["**/*"]
    exclude = policy.get("exclude") or []
    deny_names = policy.get("denyNames") or []

    secret_raw = list(policy.get("secretPatterns") or [])
    privacy = policy.get("privacy") if isinstance(policy.get("privacy"), dict) else {}
    if privacy.get("secretPatterns"):
        secret_raw = list(privacy["secretPatterns"])
    secret_patterns = []
    for p in secret_raw:
        try:
            secret_patterns.append(re.compile(p))
        except re.error as exc:
            warnings.append(f"BAD_SECRET_REGEX {p}: {exc}")

    max_file = int(policy.get("maxFileBytes") or 0)

    for path in iter_files(root):
        r = rel(root, path)
        if not match_any(r, include):
            continue
        if match_any(r, exclude):
            continue

        if match_any(path.name, deny_names) or match_any(r, deny_names):
            errors.append(f"DENY_NAME {r}")
            continue

        try:
            size = path.stat().st_size
        except OSError as exc:
            warnings.append(f"STAT_FAIL {r}: {exc}")
            continue

        if max_file and size > max_file:
            warnings.append(f"OVERSIZE {r} ({size} > {max_file})")

        if size == 0:
            continue
        try:
            sample = path.read_bytes()[:TEXT_SAMPLE_BYTES]
        except OSError as exc:
            warnings.append(f"READ_FAIL {r}: {exc}")
            continue
        if b"\x00" in sample:
            continue
        text = sample.decode("utf-8", errors="ignore")
        for cre in secret_patterns:
            if cre.search(text):
                errors.append(f"SECRET_PATTERN {r} :: {cre.pattern}")
                break

    return errors, warnings


def main() -> int:
    here = Path(__file__).resolve()
    default_policy = here.parents[2] / "enterprise" / "profiles" / "local-dev.example.yaml"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Workspace / private repo root")
    parser.add_argument("--policy", default=str(default_policy), help="Policy YAML path")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    policy_path = Path(args.policy).resolve()
    if not root.is_dir():
        print(f"ERROR: root is not a directory: {root}", file=sys.stderr)
        return 2
    if not policy_path.is_file():
        print(f"ERROR: policy not found: {policy_path}", file=sys.stderr)
        return 2

    if not has_yaml():
        print(
            "NOTE: PyYAML not installed; nested `privacy:` block may be ignored. "
            "pip install PyYAML",
            file=sys.stderr,
        )

    policy = load_policy(policy_path)
    errors, warnings = validate(root, policy)

    print(f"root={root}")
    print(f"policy={policy_path}")
    print(f"errors={len(errors)} warnings={len(warnings)}")
    for e in errors:
        print(f"ERROR\t{e}")
    for w in warnings:
        print(f"WARN\t{w}")

    if errors or (args.strict and warnings):
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
