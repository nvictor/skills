#!/usr/bin/env python3
"""Install, verify, or uninstall embedded workflow façade skills."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ADAPTER_NAMES = (
    "workflow-list",
    "workflow-status",
    "workflow-next",
    "workflow-checkpoint",
    "workflow-run",
    "workflow-summary",
    "workflow-complete",
)
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
ADAPTER_ROOT = PACKAGE_ROOT / "adapters" / "skills"
HOST_SKILLS_DIRS = {
    "claude": Path.home() / ".claude" / "skills",
    "codex": Path.home() / ".codex" / "skills",
}


def adapter_pairs(skills_dir: Path) -> list[tuple[Path, Path]]:
    return [
        (ADAPTER_ROOT / name, skills_dir / name)
        for name in ADAPTER_NAMES
    ]


def points_to(target: Path, source: Path) -> bool:
    return target.is_symlink() and target.resolve(strict=False) == source.resolve(
        strict=False
    )


def validate_sources() -> list[str]:
    return [
        f"missing embedded façade: {source}"
        for source in (ADAPTER_ROOT / name for name in ADAPTER_NAMES)
        if not (source / "SKILL.md").is_file()
    ]


def install(skills_dir: Path) -> int:
    errors = validate_sources()
    pairs = adapter_pairs(skills_dir)
    for source, target in pairs:
        if target.is_symlink():
            if not points_to(target, source):
                errors.append(f"conflicting symlink: {target}")
        elif target.exists():
            errors.append(f"conflicting path: {target}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("No adapter links were changed.", file=sys.stderr)
        return 1

    skills_dir.mkdir(parents=True, exist_ok=True)
    for source, target in pairs:
        if points_to(target, source):
            print(f"unchanged {target}")
            continue
        target.symlink_to(source, target_is_directory=True)
        print(f"installed {target} -> {source}")
    return 0


def verify(skills_dir: Path) -> int:
    errors = validate_sources()
    for source, target in adapter_pairs(skills_dir):
        if not points_to(target, source):
            errors.append(f"missing or incorrect adapter link: {target}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"verified {len(ADAPTER_NAMES)} adapter links in {skills_dir}")
    return 0


def uninstall(skills_dir: Path) -> int:
    conflicts = []
    removable = []
    for source, target in adapter_pairs(skills_dir):
        if points_to(target, source):
            removable.append(target)
        elif target.is_symlink() or target.exists():
            conflicts.append(f"refusing to remove unrelated path: {target}")

    if conflicts:
        for conflict in conflicts:
            print(conflict, file=sys.stderr)
        print("No adapter links were changed.", file=sys.stderr)
        return 1

    for target in removable:
        target.unlink()
        print(f"removed {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage workflow-designer façade skill links."
    )
    parser.add_argument("action", choices=("install", "verify", "uninstall"))
    parser.add_argument("--host", choices=tuple(HOST_SKILLS_DIRS), required=True)
    parser.add_argument(
        "--skills-dir",
        type=Path,
        help="Override the host's default personal skills directory.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    skills_dir = (args.skills_dir or HOST_SKILLS_DIRS[args.host]).expanduser()
    return {
        "install": install,
        "verify": verify,
        "uninstall": uninstall,
    }[args.action](skills_dir)


if __name__ == "__main__":
    raise SystemExit(main())
