"""Light prompt enhancement — build high-quality prompt shell around context."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence


DEFAULT_SYSTEM = (
    "你是企业私有仓上的编码助手。以下 context 已经过 HaxiTAG coding-scaffold "
    "输入法整合（隐私清洗 / llint / 命名对齐等），私有仓源文件未被改写。"
    "请仅基于提供的 context 作答；不要索要 .env 或密钥；改动保持最小必要。"
)


def build_prompt(
    *,
    task: Optional[str],
    blocks: Sequence[dict],
    security: Optional[Dict[str, Any]] = None,
    extra_rules: Optional[Sequence[str]] = None,
) -> str:
    ok_paths = [b["path"] for b in blocks if b.get("status") == "ok"]
    lines: List[str] = [DEFAULT_SYSTEM, ""]
    if task and task.strip():
        lines.append("## Task")
        lines.append(task.strip())
        lines.append("")
    lines.append("## Context files (linear)")
    if ok_paths:
        for i, p in enumerate(ok_paths, start=1):
            lines.append(f"{i}. `{p}`")
    else:
        lines.append("(none injectable)")
    lines.append("")
    if extra_rules:
        lines.append("## Rules")
        for r in extra_rules:
            lines.append(f"- {r}")
        lines.append("")
    if security and security.get("findings"):
        lines.append("## Security notes (Sentinel / local)")
        lines.append(security.get("summary") or "See findings below.")
        for f in security.get("findings", [])[:12]:
            sev = f.get("severity", "info")
            title = f.get("title") or f.get("risk_type") or "finding"
            lines.append(f"- [{sev}] {title}")
        lines.append("")
        if security.get("handoffHint"):
            lines.append(f"Handoff: {security['handoffHint']}")
            lines.append("")
    lines.append(
        "请在回复中：说明将改哪些文件、为何改；不要输出被脱敏的明文密钥。"
    )
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["DEFAULT_SYSTEM", "build_prompt"]
