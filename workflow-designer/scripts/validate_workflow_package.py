#!/usr/bin/env python3
"""Validate a portable workflow package without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STATUS_PATTERN = re.compile(r"^Status:\s*([a-z_]+)\s*$", re.MULTILINE)
STATUSES = {"draft", "in_progress", "paused", "blocked", "completed", "abandoned"}
MANIFEST_KEYS = {
    "schema_version",
    "id",
    "workflow_file",
    "state_file",
    "memory_file",
    "runner_file",
}
WORKFLOW_HEADINGS = (
    "# Goal",
    "## Completion criteria",
    "## Constraints",
    "## Steps",
    "## Transitions",
)
STATE_HEADINGS = (
    "# Workflow state",
    "## Current step",
    "## Completed steps",
    "## Blockers",
    "## Pending decisions",
    "## Working artifacts",
    "## Open operation",
)
MEMORY_HEADINGS = (
    "# Workflow memory",
    "## Decisions",
    "## Discoveries",
    "## Rejected approaches",
    "## Durable context",
)
RUNNER_MARKERS = (
    "manifest.json",
    "workflow_file",
    "state_file",
    "memory_file",
    "workflow:status",
    "workflow:next",
    "workflow:checkpoint",
    "workflow:run",
    "workflow:summary",
    "workflow:complete",
    "State handoff",
    "Memory handoff",
)
PORTABILITY_MARKERS = {
    "/users/": "Keep machine-specific paths out of canonical workflow instructions.",
    "c:\\": "Keep machine-specific paths out of canonical workflow instructions.",
    "cron": "Use a task package for repeatable scheduler behavior.",
    "gpt-": "Keep model names out of canonical workflow instructions.",
    "codex": "Keep provider names out of canonical workflow instructions.",
    "claude": "Keep provider names out of canonical workflow instructions.",
}


def read_text(path: Path, label: str, errors: list[str]) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"Missing required file: {label}")
        return None
    except (OSError, UnicodeError) as exc:
        errors.append(f"Cannot read {label}: {exc}")
        return None
    if not text.strip():
        errors.append(f"{label} must not be empty.")
    return text


def read_manifest(path: Path, errors: list[str]) -> dict[str, Any] | None:
    text = read_text(path, "manifest.json", errors)
    if text is None:
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"manifest.json is not valid JSON: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append("manifest.json must contain a JSON object.")
        return None
    return value


def require(
    mapping: dict[str, Any],
    key: str,
    expected: type,
    errors: list[str],
) -> Any:
    value = mapping.get(key)
    if not isinstance(value, expected) or (expected is int and isinstance(value, bool)):
        errors.append(f"{key} must be {expected.__name__}.")
        return None
    return value


def safe_relative_file(
    package: Path,
    value: Any,
    label: str,
    errors: list[str],
) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{label} must be a non-empty relative path.")
        return None

    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        errors.append(f"{label} must stay inside the package directory.")
        return None

    path = package / relative
    try:
        path.resolve().relative_to(package.resolve())
    except ValueError:
        errors.append(f"{label} resolves outside the package directory.")
        return None

    if not path.is_file():
        errors.append(f"{label} does not exist: {value}")
        return None
    return path


def has_template_marker(text: str) -> bool:
    return "{{" in text or "}}" in text


def missing_headings(text: str, headings: tuple[str, ...]) -> list[str]:
    lines = {line.strip() for line in text.splitlines()}
    return [heading for heading in headings if heading not in lines]


def validate_manifest(
    package: Path,
    data: dict[str, Any],
    warnings: list[str],
    errors: list[str],
) -> dict[str, Path | None]:
    schema_version = data.get("schema_version")
    if schema_version != 1 or isinstance(schema_version, bool):
        errors.append("schema_version must be 1.")

    workflow_id = require(data, "id", str, errors)
    if workflow_id is not None:
        if not ID_PATTERN.fullmatch(workflow_id):
            errors.append("id must contain lowercase letters, digits, and single hyphens.")
        if package.name != workflow_id:
            errors.append(
                f"Package directory '{package.name}' must match id '{workflow_id}'."
            )

    for conflicting in ("task_file", "prompt_file"):
        if conflicting in data:
            errors.append(
                f"manifest.json contains conflicting package discriminator: {conflicting}"
            )

    unknown = sorted(set(data) - MANIFEST_KEYS)
    if unknown:
        warnings.append(
            "manifest.json contains noncanonical extension fields: " + ", ".join(unknown)
        )

    paths = {
        key: safe_relative_file(package, data.get(key), key, errors)
        for key in ("workflow_file", "state_file", "memory_file", "runner_file")
    }

    resolved = [path.resolve() for path in paths.values() if path is not None]
    if len(resolved) != len(set(resolved)):
        errors.append("Each manifest file field must reference a different file.")

    return paths


def validate_workflow(
    path: Path | None,
    warnings: list[str],
    errors: list[str],
) -> None:
    if path is None:
        return
    text = read_text(path, "workflow_file", errors)
    if text is None:
        return
    if has_template_marker(text):
        errors.append("workflow_file contains an unresolved template marker.")
    missing = missing_headings(text, WORKFLOW_HEADINGS)
    if missing:
        errors.append("workflow_file is missing headings: " + ", ".join(missing))
    lowered = text.lower()
    for marker, message in PORTABILITY_MARKERS.items():
        if marker in lowered:
            warnings.append(f"workflow_file: {message}")


def validate_state(path: Path | None, errors: list[str]) -> None:
    if path is None:
        return
    text = read_text(path, "state_file", errors)
    if text is None:
        return
    if has_template_marker(text):
        errors.append("state_file contains an unresolved template marker.")
    missing = missing_headings(text, STATE_HEADINGS)
    if missing:
        errors.append("state_file is missing headings: " + ", ".join(missing))
    match = STATUS_PATTERN.search(text)
    if match is None:
        errors.append("state_file must contain a 'Status: <value>' line.")
    elif match.group(1) not in STATUSES:
        errors.append(
            "state_file status must be draft, in_progress, paused, blocked, completed, or abandoned."
        )


def validate_memory(path: Path | None, errors: list[str]) -> None:
    if path is None:
        return
    text = read_text(path, "memory_file", errors)
    if text is None:
        return
    if has_template_marker(text):
        errors.append("memory_file contains an unresolved template marker.")
    missing = missing_headings(text, MEMORY_HEADINGS)
    if missing:
        errors.append("memory_file is missing headings: " + ", ".join(missing))


def validate_runner(path: Path | None, errors: list[str]) -> None:
    if path is None:
        return
    text = read_text(path, "runner_file", errors)
    if text is None:
        return
    if has_template_marker(text):
        errors.append("runner_file contains an unresolved template marker.")
    missing = [marker for marker in RUNNER_MARKERS if marker not in text]
    if missing:
        errors.append("runner_file is missing protocol markers: " + ", ".join(missing))


def validate_package(package: Path) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    if not package.is_dir():
        errors.append(f"Package directory does not exist: {package}")
        return warnings, errors

    data = read_manifest(package / "manifest.json", errors)
    if data is None:
        return warnings, errors

    paths = validate_manifest(package, data, warnings, errors)
    validate_workflow(paths["workflow_file"], warnings, errors)
    validate_state(paths["state_file"], errors)
    validate_memory(paths["memory_file"], errors)
    validate_runner(paths["runner_file"], errors)
    return warnings, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Path to the workflow package")
    args = parser.parse_args()

    package = args.package.expanduser().resolve()
    warnings, errors = validate_package(package)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1

    print(f"PASSED: {package} ({len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
