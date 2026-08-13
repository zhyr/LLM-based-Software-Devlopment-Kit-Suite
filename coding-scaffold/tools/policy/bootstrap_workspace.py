#!/usr/bin/env python3
"""Bootstrap a private repo with HaxiTAG workspace policy + Cursor rules."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve()
    project = here.parents[2]
    enterprise = project / "enterprise"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Target private repository root")
    parser.add_argument(
        "--profile",
        default="local-dev",
        help="Profile name under enterprise/profiles (without .example.yaml)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR: root is not a directory: {root}", file=sys.stderr)
        return 2

    profile_src = enterprise / "profiles" / f"{args.profile}.example.yaml"
    if not profile_src.is_file():
        # allow non-example name
        alt = enterprise / "profiles" / f"{args.profile}.yaml"
        profile_src = alt if alt.is_file() else profile_src
    if not profile_src.is_file():
        print(f"ERROR: profile not found: {profile_src}", file=sys.stderr)
        return 2

    dest_policy_dir = root / ".haxitag"
    dest_policy = dest_policy_dir / "workspace-policy.yaml"
    dest_rules_dir = root / ".cursor" / "rules"
    dest_agents = root / "AGENTS.md"

    dest_policy_dir.mkdir(parents=True, exist_ok=True)
    dest_rules_dir.mkdir(parents=True, exist_ok=True)

    def copy_file(src: Path, dst: Path) -> None:
        if dst.exists() and not args.force:
            print(f"SKIP exists {dst}")
            return
        shutil.copy2(src, dst)
        print(f"WRITE {dst}")

    copy_file(profile_src, dest_policy)

    rules_src = enterprise / "templates" / "cursor-rules"
    for src in sorted(rules_src.glob("*.mdc")):
        copy_file(src, dest_rules_dir / src.name)

    agents_src = enterprise / "templates" / "AGENTS.md"
    if agents_src.is_file():
        copy_file(agents_src, dest_agents)

    naming_src = enterprise / "templates" / "naming-align.example.yaml"
    naming_dst = dest_policy_dir / "naming-align.yaml"
    if naming_src.is_file():
        copy_file(naming_src, naming_dst)

    print("DONE. Next:")
    print(f"  1) Open {root} in VS Code / Cursor / CodeBuddy")
    print(
        f"  2) python3 tools/inject/compose_input.py --root {root} "
        f"--policy {dest_policy} --files <paths> --task '...' --sentinel"
    )
    validate = here.parent / "validate_workspace.py"
    print(f"  3) python3 {validate} --root {root} --policy {dest_policy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
