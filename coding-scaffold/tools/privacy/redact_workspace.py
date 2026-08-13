#!/usr/bin/env python3
"""
Privacy SCAN only — never modifies private-repo source files.

Reports deny / noise / secret-pattern hits for CI or preflight.
For AI coding context, use tools/inject/resolve_context.py (dynamic in-memory
clean → denoise → redact → inject). Do NOT rewrite the private tree.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from policy.common import iter_files, load_policy, match_any, rel
from privacy.denoise import is_noise_path
from privacy.pipeline import privacy_config_from_policy
import re

TEXT_SAMPLE = 64 * 1024


def main() -> int:
    here = Path(__file__).resolve()
    default_policy = (
        here.parents[2] / "enterprise" / "profiles" / "local-dev.example.yaml"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Private repo root (READ-ONLY)")
    parser.add_argument("--policy", default=str(default_policy))
    parser.add_argument("--report", default="", help="Optional JSON report path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    policy_path = Path(args.policy).resolve()
    if not root.is_dir() or not policy_path.is_file():
        print("ERROR: invalid root/policy", file=sys.stderr)
        return 2

    policy = load_policy(policy_path)
    cfg = privacy_config_from_policy(policy)
    include = policy.get("include") or ["**/*"]
    exclude = policy.get("exclude") or []
    deny_names = policy.get("denyNames") or []
    secret_raw = list(policy.get("secretPatterns") or [])
    secret_res = []
    for p in secret_raw:
        try:
            secret_res.append(re.compile(p))
        except re.error:
            continue

    findings: List[dict] = []
    deny_n = noise_n = secret_n = 0

    for path in iter_files(root):
        r = rel(root, path)
        if not match_any(r, include) or match_any(r, exclude):
            continue
        if match_any(path.name, deny_names) or match_any(r, deny_names):
            deny_n += 1
            findings.append({"path": r, "issue": "denyNames"})
            continue
        if is_noise_path(r, cfg.get("noiseGlobs") or []):
            noise_n += 1
            findings.append({"path": r, "issue": "noise"})
            continue
        try:
            sample = path.read_bytes()[:TEXT_SAMPLE]
        except OSError:
            continue
        if b"\x00" in sample:
            continue
        text = sample.decode("utf-8", errors="ignore")
        for cre in secret_res:
            if cre.search(text):
                secret_n += 1
                findings.append({"path": r, "issue": "secretPattern", "pattern": cre.pattern})
                break

    summary = {
        "root": str(root),
        "policy": str(policy_path),
        "sourceUnchanged": True,
        "mode": "scan-only",
        "deny": deny_n,
        "noise": noise_n,
        "secretHits": secret_n,
        "findings": findings,
        "hint": "Use tools/inject/resolve_context.py for dynamic AI context injection (no source writes).",
    }
    print(
        f"scan deny={deny_n} noise={noise_n} secretHits={secret_n} sourceUnchanged=true"
    )
    if args.report:
        Path(args.report).write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"report={args.report}")
    return 1 if (deny_n or secret_n) else 0


if __name__ == "__main__":
    raise SystemExit(main())
