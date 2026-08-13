#!/usr/bin/env python3
"""
Dynamic context resolve for AI coding — READ-ONLY on the private repo.

Never writes into --root. Applies KnowledgeBase-aligned clean/denoise/redact
in memory, then emits an injection pack (JSON / markdown) for the Agent.

Usage:
  python3 tools/inject/resolve_context.py \\
    --root /path/to/private-repo \\
    --policy /path/to/private-repo/.haxitag/workspace-policy.yaml \\
    --files src/a.ts src/b.ts \\
    --format markdown

  # Or pipe relative paths (one per line):
  printf 'src/a.ts\\n' | python3 tools/inject/resolve_context.py --root ... --policy ... --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from policy.common import load_policy, match_any
from privacy.denoise import is_noise_path
from privacy.pipeline import (
    apply_pipeline,
    normalize_methods,
    privacy_config_from_policy,
)
from inject.paths import read_path_list


def _read_path_list(args: argparse.Namespace) -> List[str]:
    return read_path_list(
        args.files,
        args.paths_file,
        read_stdin=True,
    )

def resolve_one(
    root: Path,
    rel_path: str,
    *,
    policy: dict,
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    include = policy.get("include") or ["**/*"]
    exclude = policy.get("exclude") or []
    deny_names = policy.get("denyNames") or []

    # normalize
    rel_path = rel_path.lstrip("./")
    abs_path = (root / rel_path).resolve()
    try:
        abs_path.relative_to(root.resolve())
    except ValueError:
        return {
            "path": rel_path,
            "status": "denied",
            "reason": "path_escape",
            "content": None,
            "methods": [],
        }

    if not match_any(rel_path, include) or match_any(rel_path, exclude):
        return {
            "path": rel_path,
            "status": "excluded",
            "reason": "include/exclude",
            "content": None,
            "methods": [],
        }
    if match_any(Path(rel_path).name, deny_names) or match_any(rel_path, deny_names):
        return {
            "path": rel_path,
            "status": "denied",
            "reason": "denyNames",
            "content": None,
            "methods": ["deny"],
        }
    if is_noise_path(rel_path, cfg.get("noiseGlobs") or []):
        return {
            "path": rel_path,
            "status": "noise",
            "reason": "noiseGlobs",
            "content": None,
            "methods": ["denoise"],
        }
    if not abs_path.is_file():
        return {
            "path": rel_path,
            "status": "missing",
            "reason": "not_a_file",
            "content": None,
            "methods": [],
        }

    max_file = int(policy.get("maxFileBytes") or 0)
    size = abs_path.stat().st_size
    if max_file and size > max_file:
        return {
            "path": rel_path,
            "status": "oversized",
            "reason": f"maxFileBytes={max_file}",
            "content": None,
            "methods": [],
        }

    try:
        raw = abs_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {
            "path": rel_path,
            "status": "unreadable",
            "reason": str(exc),
            "content": None,
            "methods": [],
        }

    cleaned, applied = apply_pipeline(raw, methods=cfg["methods"], cfg=cfg)
    return {
        "path": rel_path,
        "status": "ok",
        "reason": None,
        "content": cleaned,
        "methods": applied,
        "bytesOriginal": size,
        "bytesInjected": len(cleaned.encode("utf-8")),
        "sourceUnchanged": True,
    }


def to_markdown(pack: Dict[str, Any]) -> str:
    lines: List[str] = [
        "<!-- haxitag-coding-scaffold: dynamic inject; private repo source NOT modified -->",
        f"<!-- methods={pack.get('methods')} blocks={len(pack.get('blocks', []))} -->",
        "",
        pack.get(
            "systemHint",
            "以下内容已经过 coding-scaffold 动态清洗/去噪/脱敏，仅用于 AI 上下文注入；私有仓原始文件未改写。",
        ),
        "",
    ]
    for b in pack.get("blocks", []):
        status = b.get("status")
        path = b.get("path")
        if status != "ok" or not b.get("content"):
            lines.append(f"### `{path}` — skipped ({status}: {b.get('reason')})")
            lines.append("")
            continue
        lines.append(f"### `{path}`")
        if b.get("methods"):
            lines.append(f"<!-- applied: {', '.join(b['methods'])} -->")
        ext = Path(path).suffix.lstrip(".") or "text"
        lines.append(f"```{ext}")
        lines.append(b["content"].rstrip("\n"))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def build_pack(
    root: Path,
    paths: Sequence[str],
    *,
    policy: dict,
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    blocks = [
        resolve_one(root, p, policy=policy, cfg=cfg) for p in paths
    ]
    ok = sum(1 for b in blocks if b["status"] == "ok")
    return {
        "version": 1,
        "mode": "dynamic-inject",
        "sourceUnchanged": True,
        "root": str(root),
        "methods": cfg["methods"],
        "systemHint": (
            "Dynamic privacy pipeline (clean/denoise/redact) applied in-memory. "
            "Private repository source files were NOT modified. "
            "Aligned with HaxiTAG-AI-CMS KnowledgeBase preprocess + logger sanitize."
        ),
        "stats": {
            "requested": len(paths),
            "ok": ok,
            "skipped": len(paths) - ok,
        },
        "blocks": blocks,
    }


def main() -> int:
    here = Path(__file__).resolve()
    default_policy = (
        here.parents[2] / "enterprise" / "profiles" / "local-dev.example.yaml"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Private repo root (READ-ONLY)")
    parser.add_argument("--policy", default=str(default_policy))
    parser.add_argument("--files", nargs="*", default=[], help="Relative paths to inject")
    parser.add_argument("--paths-file", default="", help="File listing relative paths")
    parser.add_argument(
        "--methods",
        nargs="*",
        default=None,
        help="Override privacy methods, e.g. 清洗 去噪 脱敏",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Injection pack format (default markdown for chat paste)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    policy_path = Path(args.policy).resolve()
    if not root.is_dir() or not policy_path.is_file():
        print("ERROR: invalid root/policy", file=sys.stderr)
        return 2

    paths = _read_path_list(args)
    if not paths:
        print(
            "ERROR: no paths; pass --files, --paths-file, or stdin paths",
            file=sys.stderr,
        )
        return 2

    policy = load_policy(policy_path)
    cfg = privacy_config_from_policy(policy)
    if args.methods:
        cfg["methods"] = normalize_methods(args.methods)
    # inject mode never writes
    cfg["mode"] = "inject"

    pack = build_pack(root, paths, policy=policy, cfg=cfg)
    if args.format == "json":
        print(json.dumps(pack, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(pack))

    # stderr audit line
    print(
        f"inject ok={pack['stats']['ok']} skipped={pack['stats']['skipped']} "
        f"sourceUnchanged=true",
        file=sys.stderr,
    )
    return 0 if pack["stats"]["ok"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
