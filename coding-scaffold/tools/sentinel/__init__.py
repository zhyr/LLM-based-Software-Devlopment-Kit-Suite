"""
Sentinel bridge — call external Sentinel or run a thin local precheck.

Does not embed Sentinel. Output findings are Forge-compatible enough to attach
as pack.security notes (see forge sentinel_report.schema.json spirit).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _finding(
    *,
    risk_type: str,
    severity: str,
    title: str,
    description: str,
    recommendation: str,
    cve_id: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "risk_type": risk_type,
        "severity": severity,
        "title": title,
        "description": description,
        "recommendation": recommendation,
        "cve_id": cve_id,
    }


def local_precheck(root: Path, rel_paths: Sequence[str]) -> Dict[str, Any]:
    """Thin supply-chain / secret surface check for compose-input (no Sentinel binary)."""
    findings: List[Dict[str, Any]] = []
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        deps = {}
        for key in ("dependencies", "devDependencies", "optionalDependencies"):
            block = data.get(key) or {}
            if isinstance(block, dict):
                deps.update(block)
        # heuristic: very loose version / git deps
        for name, ver in deps.items():
            ver_s = str(ver)
            if ver_s.startswith("git+") or "github:" in ver_s:
                findings.append(
                    _finding(
                        risk_type="supply_chain",
                        severity="medium",
                        title=f"Git-sourced dependency: {name}",
                        description=f"{name}@{ver_s}",
                        recommendation="Pin to registry version or lock commit SHA; scan with Sentinel.",
                    )
                )
            if ver_s in {"*", "latest", "x"} or ver_s.startswith(">"):
                findings.append(
                    _finding(
                        risk_type="supply_chain",
                        severity="low",
                        title=f"Loose version range: {name}",
                        description=f"{name}@{ver_s}",
                        recommendation="Prefer exact or caret-pinned ranges; run Sentinel supply-chain scan.",
                    )
                )
        if not (root / "package-lock.json").is_file() and not (
            root / "pnpm-lock.yaml"
        ).is_file() and not (root / "yarn.lock").is_file():
            if deps:
                findings.append(
                    _finding(
                        risk_type="supply_chain",
                        severity="medium",
                        title="No lockfile detected",
                        description="package.json present without lockfile",
                        recommendation="Commit a lockfile; Sentinel can verify SBOM drift.",
                    )
                )

    secret_re = re.compile(
        r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    )
    for rel in rel_paths:
        p = root / rel
        if not p.is_file():
            continue
        try:
            sample = p.read_text(encoding="utf-8", errors="ignore")[:64_000]
        except OSError:
            continue
        if secret_re.search(sample):
            findings.append(
                _finding(
                    risk_type="secret_exposure",
                    severity="high",
                    title=f"Possible hardcoded secret in {rel}",
                    description="Heuristic matched key/password/token assignment",
                    recommendation="Remove secret; use env / secret manager; full scan via Sentinel.",
                )
            )

    critical = sum(1 for f in findings if f["severity"] == "critical")
    high = sum(1 for f in findings if f["severity"] == "high")
    medium = sum(1 for f in findings if f["severity"] == "medium")
    low = sum(1 for f in findings if f["severity"] == "low")
    summary = (
        f"local precheck: {len(findings)} finding(s) "
        f"(critical={critical} high={high} medium={medium} low={low})"
    )
    return {
        "schema_version": "1",
        "source": "coding-scaffold-local",
        "imported_at": _now(),
        "trace_id": f"compose-{root.name}",
        "summary": summary,
        "findings": findings,
        "status": "ok",
        "handoffHint": (
            "For full repo/deploy/supply-chain audit, open Sentinel and import this handoff; "
            "Forge skill: sentinel-security."
        ),
        "risk_summary": {
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "unknown": 0,
        },
    }


def _run_command(cmd: str, root: Path, timeout: int = 120) -> Dict[str, Any]:
    proc = subprocess.run(
        cmd,
        shell=True,
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "HAXITAG_SCAFFOLD_ROOT": str(root)},
    )
    out = (proc.stdout or "").strip()
    if not out:
        return {
            "source": "sentinel-cli",
            "status": "error",
            "summary": f"sentinel command exit={proc.returncode}: {(proc.stderr or '')[:400]}",
            "findings": [],
            "handoffHint": "Configure sentinel.command to print Forge-compatible JSON on stdout.",
        }
    try:
        data = json.loads(out)
        if isinstance(data, dict):
            data.setdefault("source", "sentinel")
            data.setdefault("status", "ok" if proc.returncode == 0 else "error")
            data.setdefault("imported_at", _now())
            return data
    except json.JSONDecodeError:
        pass
    return {
        "source": "sentinel-cli",
        "status": "ok" if proc.returncode == 0 else "error",
        "summary": out[:800],
        "findings": [],
        "raw_text": out[:4000],
    }


def _post_url(url: str, payload: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict):
                data.setdefault("source", "sentinel-http")
                data.setdefault("status", "ok")
                data.setdefault("imported_at", _now())
                return data
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "source": "sentinel-http",
            "status": "error",
            "summary": f"HTTP sentinel failed: {exc}",
            "findings": [],
        }
    return {
        "source": "sentinel-http",
        "status": "error",
        "summary": "unexpected response",
        "findings": [],
    }


def run_sentinel(
    root: Path,
    *,
    rel_paths: Sequence[str],
    policy: Optional[dict] = None,
    enabled: bool = True,
) -> Optional[Dict[str, Any]]:
    if not enabled:
        return None
    block = (policy or {}).get("sentinel") or {}
    if not isinstance(block, dict):
        block = {}
    if block.get("enabled") is False:
        return None

    cmd = block.get("command") or os.environ.get("SENTINEL_CMD") or ""
    url = block.get("url") or os.environ.get("SENTINEL_URL") or ""

    if cmd:
        try:
            return _run_command(str(cmd), root)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {
                "source": "sentinel-cli",
                "status": "error",
                "summary": str(exc),
                "findings": [],
            }
    if url:
        return _post_url(
            str(url),
            {"root": str(root), "files": list(rel_paths), "mode": "compose-precheck"},
        )
    # default: local thin precheck + handoff hint for real Sentinel
    return local_precheck(root, rel_paths)


__all__ = ["local_precheck", "run_sentinel"]
