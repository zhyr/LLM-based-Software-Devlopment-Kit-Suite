#!/usr/bin/env python3
"""
Compose Input — coding-scaffold「输入法」主入口.

私有仓 READ-ONLY → privacy → llint → align → linear → enhance prompt
→ optional Sentinel bridge → 高质量 prompt + context pack（供 Forge / IDE Agent）.

Usage:
  python3 tools/inject/compose_input.py \\
    --root /path/to/private-repo \\
    --policy .../.haxitag/workspace-policy.yaml \\
    --files src/a.ts \\
    --task "修复登录校验" \\
    --format markdown \\
    --sentinel
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

from align import align_config_from_policy, align_text, load_align_map
from enhance import build_prompt
from inject.paths import read_path_list
from inject.resolve_context import resolve_one
from llint import linearize_blocks, llint_text
from policy.common import load_policy
from privacy.pipeline import normalize_methods, privacy_config_from_policy
from sentinel import run_sentinel


def _flag(cli: Optional[bool], policy_val: bool) -> bool:
    return policy_val if cli is None else cli


def _ime_flags(policy: dict, args: argparse.Namespace) -> Dict[str, bool]:
    ime = policy.get("ime") or {}
    if not isinstance(ime, dict):
        ime = {}
    return {
        "llint": _flag(args.llint, bool(ime.get("llint", True))),
        "linear": _flag(args.linear, bool(ime.get("linear", True))),
        "align": _flag(args.align, bool(ime.get("align", True))),
        "enhance": _flag(args.enhance, bool(ime.get("enhance", True))),
        "sentinel": _flag(args.sentinel, bool(ime.get("sentinel", False))),
    }


def compose(
    root: Path,
    paths: Sequence[str],
    *,
    policy: dict,
    privacy_cfg: Dict[str, Any],
    flags: Dict[str, bool],
    task: Optional[str],
    align_map_override: Optional[Path],
) -> Dict[str, Any]:
    pipeline: List[str] = ["privacy"]
    blocks: List[dict] = [
        resolve_one(root, p, policy=policy, cfg=privacy_cfg) for p in paths
    ]

    align_cfg = align_config_from_policy(policy, root)
    if align_map_override:
        override = load_align_map(align_map_override)
        align_cfg["map"] = {**align_cfg.get("map", {}), **override}
        align_cfg["enabled"] = bool(align_cfg["map"])

    for b in blocks:
        if b.get("status") != "ok" or not b.get("content"):
            continue
        content = b["content"]
        methods = list(b.get("methods") or [])
        if flags["llint"]:
            content, rules = llint_text(content)
            methods.extend(rules)
            if "llint" not in pipeline:
                pipeline.append("llint")
        if flags["align"] and align_cfg.get("enabled"):
            content, rules = align_text(content, align_cfg["map"])
            methods.extend(rules)
            if rules and "align" not in pipeline:
                pipeline.append("align")
        b["content"] = content
        b["methods"] = methods
        b["bytesInjected"] = len(content.encode("utf-8"))
        b["sourceUnchanged"] = True

    if flags["linear"]:
        blocks, _ = linearize_blocks(blocks)
        pipeline.append("linear")

    security = None
    if flags["sentinel"]:
        security = run_sentinel(
            root, rel_paths=paths, policy=policy, enabled=True
        )
        pipeline.append("sentinel")

    if flags["enhance"]:
        rules: List[str] = []
        ime = policy.get("ime") or {}
        if isinstance(ime, dict) and isinstance(ime.get("rules"), list):
            rules = [str(r) for r in ime["rules"]]
        prompt = build_prompt(
            task=task, blocks=blocks, security=security, extra_rules=rules or None
        )
        pipeline.append("enhance")
    else:
        prompt = (
            task.strip()
            if task and task.strip()
            else "（未启用 enhance；请直接使用 context blocks）"
        )

    ok = sum(1 for b in blocks if b.get("status") == "ok")
    return {
        "schema": "haxitag.coding-scaffold.pack",
        "schemaVersion": "1",
        "mode": "compose-input",
        "sourceUnchanged": True,
        "root": str(root),
        "task": task,
        "prompt": prompt,
        "context": {"blocks": blocks},
        "security": security,
        "pipeline": pipeline,
        "stats": {
            "requested": len(paths),
            "ok": ok,
            "skipped": len(paths) - ok,
            "securityFindings": len((security or {}).get("findings") or []),
        },
    }


def to_markdown(pack: Dict[str, Any]) -> str:
    lines: List[str] = [
        "<!-- haxitag-coding-scaffold: compose-input; source NOT modified -->",
        f"<!-- pipeline={pack.get('pipeline')} schemaVersion={pack.get('schemaVersion')} -->",
        "",
        "# Prompt",
        "",
        pack.get("prompt") or "",
        "",
        "# Context",
        "",
    ]
    for b in pack.get("context", {}).get("blocks", []):
        path = b.get("path")
        if b.get("status") != "ok" or not b.get("content"):
            lines.append(
                f"### `{path}` — skipped ({b.get('status')}: {b.get('reason')})"
            )
            lines.append("")
            continue
        idx = b.get("linearIndex")
        title = f"### [{idx}] `{path}`" if idx else f"### `{path}`"
        lines.append(title)
        if b.get("methods"):
            lines.append(f"<!-- applied: {', '.join(b['methods'])} -->")
        ext = Path(str(path)).suffix.lstrip(".") or "text"
        lines.append(f"```{ext}")
        lines.append(b["content"].rstrip("\n"))
        lines.append("```")
        lines.append("")
    sec = pack.get("security")
    if sec:
        lines.append("# Security")
        lines.append("")
        lines.append(sec.get("summary") or "")
        for f in sec.get("findings") or []:
            lines.append(
                f"- **[{f.get('severity')}]** {f.get('title')}: {f.get('recommendation')}"
            )
        if sec.get("handoffHint"):
            lines.append("")
            lines.append(f"> {sec['handoffHint']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    here = Path(__file__).resolve()
    default_policy = (
        here.parents[2] / "enterprise" / "profiles" / "local-dev.example.yaml"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--policy", default=str(default_policy))
    parser.add_argument("--files", nargs="*", default=[])
    parser.add_argument("--paths-file", default="")
    parser.add_argument("--task", default="", help="User task for prompt shell")
    parser.add_argument("--methods", nargs="*", default=None)
    parser.add_argument("--align-map", default="", help="Override naming align map")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.set_defaults(llint=None, linear=None, align=None, enhance=None, sentinel=None)
    parser.add_argument("--llint", action="store_true", dest="llint")
    parser.add_argument("--no-llint", action="store_false", dest="llint")
    parser.add_argument("--linear", action="store_true", dest="linear")
    parser.add_argument("--no-linear", action="store_false", dest="linear")
    parser.add_argument("--align", action="store_true", dest="align")
    parser.add_argument("--no-align", action="store_false", dest="align")
    parser.add_argument("--enhance", action="store_true", dest="enhance")
    parser.add_argument("--no-enhance", action="store_false", dest="enhance")
    parser.add_argument("--sentinel", action="store_true", dest="sentinel")
    parser.add_argument("--no-sentinel", action="store_false", dest="sentinel")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    policy_path = Path(args.policy).resolve()
    if not root.is_dir() or not policy_path.is_file():
        print("ERROR: invalid root/policy", file=sys.stderr)
        return 2

    paths = read_path_list(args.files, args.paths_file, read_stdin=True)
    if not paths:
        print("ERROR: no paths", file=sys.stderr)
        return 2

    policy = load_policy(policy_path)
    privacy_cfg = privacy_config_from_policy(policy)
    if args.methods:
        privacy_cfg["methods"] = normalize_methods(args.methods)
    privacy_cfg["mode"] = "inject"

    flags = _ime_flags(policy, args)
    align_override = Path(args.align_map) if args.align_map else None

    pack = compose(
        root,
        paths,
        policy=policy,
        privacy_cfg=privacy_cfg,
        flags=flags,
        task=args.task or None,
        align_map_override=align_override,
    )

    if args.format == "json":
        print(json.dumps(pack, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(pack))

    print(
        f"compose ok={pack['stats']['ok']} skipped={pack['stats']['skipped']} "
        f"securityFindings={pack['stats']['securityFindings']} "
        f"pipeline={','.join(pack['pipeline'])} sourceUnchanged=true",
        file=sys.stderr,
    )
    return 0 if pack["stats"]["ok"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
