#!/usr/bin/env python3
"""Validate a portable coach package without third-party dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
WEEKDAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}
STATE_HEADINGS = (
    "## Last completed session",
    "## Demonstrated strengths",
    "## Recurring gaps",
    "## Current difficulty",
    "## Recent modes and scenarios",
    "## Skills due for review",
    "## Next useful target",
    "## Open interaction",
)
PORTABILITY_MARKERS = {
    "automation run": "Use 'session' instead of scheduler-specific language.",
    "rrule": "Keep native scheduler expressions outside prompt.md.",
    "project_id": "Keep project identifiers outside prompt.md.",
    "/users/": "Keep machine-specific paths outside prompt.md.",
    "gpt-": "Keep model names outside prompt.md.",
    "codex": "Keep provider names outside prompt.md.",
    "claude code": "Keep provider names outside prompt.md.",
}


def read_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"Missing required file: {path.name}")
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"Cannot read {path.name}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path.name} must contain a JSON object.")
        return None
    return value


def require(mapping: dict[str, Any], key: str, expected: type, errors: list[str], prefix: str = "") -> Any:
    value = mapping.get(key)
    label = f"{prefix}{key}"
    if not isinstance(value, expected) or isinstance(value, bool) and expected is int:
        errors.append(f"{label} must be {expected.__name__}.")
        return None
    return value


def safe_relative_file(package: Path, value: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{label} must be a non-empty relative path.")
        return None
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        errors.append(f"{label} must stay inside the package directory.")
        return None
    path = package / relative
    if not path.is_file():
        errors.append(f"{label} does not exist: {value}")
        return None
    return path


def validate_manifest(package: Path, data: dict[str, Any], errors: list[str]) -> tuple[Path | None, Path | None, Path | None]:
    if data.get("schema_version") != 2:
        errors.append("schema_version must be 2.")

    coach_id = require(data, "id", str, errors)
    if coach_id is not None:
        if not ID_PATTERN.fullmatch(coach_id):
            errors.append("id must contain lowercase letters, digits, and single hyphens.")
        if package.name != coach_id:
            errors.append(f"Package directory '{package.name}' must match id '{coach_id}'.")

    require(data, "name", str, errors)
    if data.get("status") not in {"draft", "active", "paused", "archived"}:
        errors.append("status must be draft, active, paused, or archived.")
    version = require(data, "version", int, errors)
    if version is not None and version < 1:
        errors.append("version must be at least 1.")

    runner_path = safe_relative_file(package, data.get("runner_file"), "runner_file", errors)
    prompt_path = safe_relative_file(package, data.get("prompt_file"), "prompt_file", errors)
    state_path = safe_relative_file(package, data.get("state_file"), "state_file", errors)

    schedule = require(data, "schedule", dict, errors)
    if schedule is not None:
        enabled = require(schedule, "enabled", bool, errors, "schedule.")
        frequency = schedule.get("frequency")
        if frequency not in {"daily", "weekly", "monthly", "manual"}:
            errors.append("schedule.frequency must be daily, weekly, monthly, or manual.")
        interval = require(schedule, "interval", int, errors, "schedule.")
        if interval is not None and interval < 1:
            errors.append("schedule.interval must be at least 1.")
        start_date = schedule.get("start_date")
        if start_date is not None and (not isinstance(start_date, str) or not DATE_PATTERN.fullmatch(start_date)):
            errors.append("schedule.start_date must be null or YYYY-MM-DD.")
        if interval is not None and interval > 1 and start_date is None:
            errors.append("schedule.start_date is required when schedule.interval is greater than 1.")
        days = require(schedule, "days", list, errors, "schedule.")
        if days is not None:
            invalid_days = [day for day in days if day not in WEEKDAYS]
            if invalid_days:
                errors.append(f"schedule.days contains invalid values: {invalid_days}")
        local_time = schedule.get("local_time")
        timezone = schedule.get("timezone")
        if enabled:
            if frequency == "manual":
                errors.append("An enabled schedule cannot use manual frequency.")
            if not isinstance(local_time, str) or not TIME_PATTERN.fullmatch(local_time):
                errors.append("An enabled schedule requires local_time in HH:MM format.")
            if not isinstance(timezone, str) or not timezone:
                errors.append("An enabled schedule requires an explicit timezone.")
        else:
            if local_time is not None and (not isinstance(local_time, str) or not TIME_PATTERN.fullmatch(local_time)):
                errors.append("schedule.local_time must be null or HH:MM.")
            if timezone is not None and not isinstance(timezone, str):
                errors.append("schedule.timezone must be null or a string.")

    session = require(data, "session", dict, errors)
    if session is not None:
        minimum = require(session, "minimum_minutes", int, errors, "session.")
        maximum = require(session, "maximum_minutes", int, errors, "session.")
        if minimum is not None and minimum < 1:
            errors.append("session.minimum_minutes must be positive.")
        if maximum is not None and maximum < 1:
            errors.append("session.maximum_minutes must be positive.")
        if minimum is not None and maximum is not None and minimum > maximum:
            errors.append("session.minimum_minutes cannot exceed maximum_minutes.")
        if session.get("interaction") not in {"conversational", "self-contained", "mixed"}:
            errors.append("session.interaction must be conversational, self-contained, or mixed.")

    continuity = require(data, "continuity", dict, errors)
    if continuity is not None:
        if continuity.get("state_authority") != "package":
            errors.append("continuity.state_authority must be package.")
        require(continuity, "read_before_session", bool, errors, "continuity.")
        require(continuity, "update_after_turn", bool, errors, "continuity.")
        require(continuity, "handoff_when_read_only", bool, errors, "continuity.")

    if data.get("privacy") not in {"private", "internal", "public"}:
        errors.append("privacy must be private, internal, or public.")

    return runner_path, prompt_path, state_path


def validate_text_files(
    runner_path: Path | None,
    prompt_path: Path | None,
    state_path: Path | None,
    warnings: list[str],
    errors: list[str],
) -> None:
    if runner_path is not None:
        runner = runner_path.read_text(encoding="utf-8")
        if not runner.strip():
            errors.append("runner.md must not be empty.")
        if "{{" in runner or "}}" in runner:
            errors.append("runner.md contains an unresolved template marker.")
        for required in ("manifest.json", "prompt_file", "state_file", "State handoff"):
            if required not in runner:
                errors.append(f"runner.md must reference {required}.")
    if prompt_path is not None:
        prompt = prompt_path.read_text(encoding="utf-8")
        if not prompt.strip():
            errors.append("prompt.md must not be empty.")
        if "{{" in prompt or "}}" in prompt:
            errors.append("prompt.md contains an unresolved template marker.")
        lowered = prompt.lower()
        for marker, message in PORTABILITY_MARKERS.items():
            if marker in lowered:
                warnings.append(f"prompt.md: {message}")

    if state_path is not None:
        state = state_path.read_text(encoding="utf-8")
        if "{{" in state or "}}" in state:
            errors.append("state.md contains an unresolved template marker.")
        missing = [heading for heading in STATE_HEADINGS if heading not in state]
        if missing:
            warnings.append("state.md uses a legacy structure; preserve it during migration and normalize separately.")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_migration(
    package: Path,
    prompt_path: Path | None,
    state_path: Path | None,
    warnings: list[str],
    errors: list[str],
) -> None:
    path = package / "migration.json"
    if not path.exists():
        return
    data = read_json(path, errors)
    if data is None:
        return
    if data.get("schema_version") != 1:
        errors.append("migration.json schema_version must be 1.")
    migrated_at = data.get("migrated_at")
    if not isinstance(migrated_at, str) or not re.search(r"(?:Z|[+-]\d\d:\d\d)$", migrated_at):
        errors.append("migration.json migrated_at must be an ISO 8601 timestamp with a timezone.")
    sources = data.get("sources")
    selected_prompt_sources: list[dict[str, Any]] = []
    selected_state_sources: list[dict[str, Any]] = []
    if not isinstance(sources, list) or not sources:
        errors.append("migration.json sources must be a non-empty list.")
    else:
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                errors.append(f"migration.json sources[{index}] must be an object.")
                continue
            for key in ("kind", "id"):
                if not isinstance(source.get(key), str) or not source[key]:
                    errors.append(f"migration.json sources[{index}].{key} must be a non-empty string.")
            for key in ("selected_prompt", "selected_state"):
                if not isinstance(source.get(key), bool):
                    errors.append(f"migration.json sources[{index}].{key} must be boolean.")
            if source.get("selected_prompt") is True:
                selected_prompt_sources.append(source)
            if source.get("selected_state") is True:
                selected_state_sources.append(source)
            prompt_hash = source.get("prompt_sha256")
            if not isinstance(prompt_hash, str) or not SHA256_PATTERN.fullmatch(prompt_hash):
                errors.append(f"migration.json sources[{index}].prompt_sha256 must be a SHA-256 digest.")
            state_hash = source.get("state_sha256")
            if state_hash is not None and (not isinstance(state_hash, str) or not SHA256_PATTERN.fullmatch(state_hash)):
                errors.append(f"migration.json sources[{index}].state_sha256 must be null or a SHA-256 digest.")
        if len(selected_prompt_sources) != 1:
            errors.append("migration.json must select exactly one prompt source.")
        if len(selected_state_sources) > 1:
            errors.append("migration.json may select at most one state source.")
    for key in ("behavior_changed", "state_changed", "deployment_changed"):
        if not isinstance(data.get(key), bool):
            errors.append(f"migration.json {key} must be boolean.")
    if not isinstance(data.get("warnings"), list):
        errors.append("migration.json warnings must be a list.")

    if prompt_path is not None and data.get("behavior_changed") is False and len(selected_prompt_sources) == 1:
        if sha256(prompt_path) != selected_prompt_sources[0].get("prompt_sha256"):
            errors.append("prompt.md checksum does not match the selected source while behavior_changed is false.")
    if state_path is not None and data.get("state_changed") is False and len(selected_state_sources) == 1:
        if sha256(state_path) != selected_state_sources[0].get("state_sha256"):
            warnings.append("state.md has changed since the imported migration baseline, as expected after live coaching updates.")


def validate(package: Path) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    if not package.is_dir():
        print(f"ERROR: package directory does not exist: {package}")
        return 1

    manifest = read_json(package / "manifest.json", errors)
    runner_path: Path | None = None
    prompt_path: Path | None = None
    state_path: Path | None = None
    if manifest is not None:
        runner_path, prompt_path, state_path = validate_manifest(package, manifest, errors)
    validate_text_files(runner_path, prompt_path, state_path, warnings, errors)
    validate_migration(package, prompt_path, state_path, warnings, errors)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"VALID: {package} ({len(warnings)} warning(s))")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Path to one coach package directory")
    args = parser.parse_args()
    return validate(args.package.resolve())


if __name__ == "__main__":
    sys.exit(main())
