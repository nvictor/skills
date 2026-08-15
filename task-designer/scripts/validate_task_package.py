#!/usr/bin/env python3
"""Validate a portable task package without third-party dependencies."""

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
RESOURCE_KINDS = {"file", "directory", "service", "tool", "credential", "other"}
RESOURCE_ACCESS = {"read", "write", "read-write", "invoke"}
EFFECT_KINDS = {
    "filesystem-write",
    "external-write",
    "message-send",
    "command-execution",
}
STATE_HEADINGS = (
    "## Last attempted run",
    "## Last successful run",
    "## Current checkpoint",
    "## Recent outcomes",
    "## Pending work",
    "## Known failures",
    "## Open interaction",
)
TASK_HEADINGS = (
    "# Purpose",
    "## Inputs and prerequisites",
    "## Procedure",
    "## Definition of done",
    "## Idempotency and no-op behavior",
    "## Failure and retry behavior",
    "## Outputs",
    "## State updates",
    "## Constraints",
)
PORTABILITY_MARKERS = {
    "/users/": "Keep machine-specific paths outside task.md.",
    "<scheduled-task": "Keep scheduler wrappers outside task.md.",
    "rrule": "Keep native scheduler expressions outside task.md.",
    "cron": "Keep native scheduler syntax outside task.md.",
    "gpt-": "Keep model names outside task.md.",
    "codex": "Keep provider names outside task.md.",
    "claude": "Keep provider names outside task.md.",
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


def require(
    mapping: dict[str, Any],
    key: str,
    expected: type,
    errors: list[str],
    prefix: str = "",
) -> Any:
    value = mapping.get(key)
    label = f"{prefix}{key}"
    if not isinstance(value, expected) or (expected is int and isinstance(value, bool)):
        errors.append(f"{label} must be {expected.__name__}.")
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
    if not path.is_file():
        errors.append(f"{label} does not exist: {value}")
        return None
    return path


def validate_schedule(
    schedule: dict[str, Any],
    errors: list[str],
    *,
    allow_manual: bool,
) -> None:
    enabled = require(schedule, "enabled", bool, errors, "schedule.")
    frequency = schedule.get("frequency")
    frequencies = {"daily", "weekly", "monthly", "manual"} if allow_manual else {
        "daily",
        "weekly",
        "monthly",
    }
    if frequency not in frequencies:
        allowed = "daily, weekly, monthly, or manual" if allow_manual else "daily, weekly, or monthly"
        errors.append(f"schedule.frequency must be {allowed}.")
    interval = require(schedule, "interval", int, errors, "schedule.")
    if interval is not None and interval < 1:
        errors.append("schedule.interval must be at least 1.")

    start_date = schedule.get("start_date")
    if start_date is not None and (
        not isinstance(start_date, str) or not DATE_PATTERN.fullmatch(start_date)
    ):
        errors.append("schedule.start_date must be null or YYYY-MM-DD.")
    if interval is not None and interval > 1 and start_date is None:
        errors.append("schedule.start_date is required when schedule.interval is greater than 1.")
    if enabled and frequency == "monthly" and start_date is None:
        errors.append("An enabled monthly schedule requires schedule.start_date as its anchor.")

    days = require(schedule, "days", list, errors, "schedule.")
    if days is not None:
        invalid_days = [day for day in days if day not in WEEKDAYS]
        if invalid_days:
            errors.append(f"schedule.days contains invalid values: {invalid_days}")
        if len(set(days)) != len(days):
            errors.append("schedule.days must not contain duplicates.")
        if enabled and frequency == "weekly" and not days:
            errors.append("An enabled weekly schedule requires at least one weekday.")

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
        if local_time is not None and (
            not isinstance(local_time, str) or not TIME_PATTERN.fullmatch(local_time)
        ):
            errors.append("schedule.local_time must be null or HH:MM.")
        if timezone is not None and not isinstance(timezone, str):
            errors.append("schedule.timezone must be null or a string.")


def validate_resources(
    resources: Any,
    effects: Any,
    errors: list[str],
) -> None:
    if not isinstance(resources, list):
        errors.append("resources must be a list.")
        return

    resource_map: dict[str, dict[str, Any]] = {}
    for index, resource in enumerate(resources):
        label = f"resources[{index}]"
        if not isinstance(resource, dict):
            errors.append(f"{label} must be an object.")
            continue
        resource_id = require(resource, "id", str, errors, f"{label}.")
        if resource_id is not None:
            if not ID_PATTERN.fullmatch(resource_id):
                errors.append(f"{label}.id must be lowercase and hyphenated.")
            elif resource_id in resource_map:
                errors.append(f"Duplicate resource id: {resource_id}")
            else:
                resource_map[resource_id] = resource
        if resource.get("kind") not in RESOURCE_KINDS:
            errors.append(f"{label}.kind is invalid.")
        if resource.get("access") not in RESOURCE_ACCESS:
            errors.append(f"{label}.access is invalid.")
        require(resource, "required", bool, errors, f"{label}.")
        description = require(resource, "description", str, errors, f"{label}.")
        if description is not None and not description.strip():
            errors.append(f"{label}.description must not be empty.")

    if not isinstance(effects, dict):
        errors.append("effects must be an object.")
        return
    if effects.get("policy") != "deny-by-default":
        errors.append("effects.policy must be deny-by-default.")
    allowed = effects.get("allowed")
    if not isinstance(allowed, list):
        errors.append("effects.allowed must be a list.")
        return

    for index, effect in enumerate(allowed):
        label = f"effects.allowed[{index}]"
        if not isinstance(effect, dict):
            errors.append(f"{label} must be an object.")
            continue
        kind = effect.get("kind")
        if kind not in EFFECT_KINDS:
            errors.append(f"{label}.kind is invalid.")
        resource_id = require(effect, "resource", str, errors, f"{label}.")
        purpose = require(effect, "purpose", str, errors, f"{label}.")
        if purpose is not None and not purpose.strip():
            errors.append(f"{label}.purpose must not be empty.")
        resource = resource_map.get(resource_id) if resource_id is not None else None
        if resource_id is not None and resource is None:
            errors.append(f"{label}.resource references an undeclared resource: {resource_id}")
            continue
        if resource is None:
            continue
        access = resource.get("access")
        resource_kind = resource.get("kind")
        if kind == "filesystem-write" and (
            resource_kind not in {"file", "directory"}
            or access not in {"write", "read-write"}
        ):
            errors.append(f"{label} requires a writable file or directory resource.")
        if kind in {"external-write", "message-send"} and access not in {
            "write",
            "read-write",
            "invoke",
        }:
            errors.append(f"{label} requires write, read-write, or invoke access.")
        if kind == "command-execution" and (
            resource_kind != "tool" or access != "invoke"
        ):
            errors.append(f"{label} requires an invokable tool resource.")


def validate_manifest(
    package: Path,
    data: dict[str, Any],
    warnings: list[str],
    errors: list[str],
) -> tuple[Path | None, Path | None, Path | None]:
    schema_version = data.get("schema_version")
    if schema_version == 1:
        warnings.append(
            "schema_version 1 is deprecated; migrate the package to schema version 2 when refining it."
        )
    elif schema_version != 2:
        errors.append("schema_version must be 1 or 2.")

    task_id = require(data, "id", str, errors)
    if task_id is not None:
        if not ID_PATTERN.fullmatch(task_id):
            errors.append("id must contain lowercase letters, digits, and single hyphens.")
        if package.name != task_id:
            errors.append(f"Package directory '{package.name}' must match id '{task_id}'.")

    name = require(data, "name", str, errors)
    if name is not None and not name.strip():
        errors.append("name must not be empty.")
    if data.get("status") not in {"draft", "active", "paused", "archived"}:
        errors.append("status must be draft, active, paused, or archived.")
    version = require(data, "version", int, errors)
    if version is not None and version < 1:
        errors.append("version must be at least 1.")

    runner_path = safe_relative_file(package, data.get("runner_file"), "runner_file", errors)
    task_path = safe_relative_file(package, data.get("task_file"), "task_file", errors)
    state_path = safe_relative_file(package, data.get("state_file"), "state_file", errors)

    if schema_version == 1:
        schedule = require(data, "schedule", dict, errors)
        if schedule is not None:
            validate_schedule(schedule, errors, allow_manual=True)
    elif schema_version == 2 and "schedule" in data:
        schedule = require(data, "schedule", dict, errors)
        if schedule is not None:
            validate_schedule(schedule, errors, allow_manual=False)

    execution = require(data, "execution", dict, errors)
    if execution is not None:
        unknown_bounds_allowed = (package / "migration.json").exists() and data.get("status") == "draft"
        minimum = execution.get("minimum_minutes")
        maximum = execution.get("maximum_minutes")
        for key, value in (("minimum_minutes", minimum), ("maximum_minutes", maximum)):
            if value is None and unknown_bounds_allowed:
                continue
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f"execution.{key} must be int.")
        if (minimum is None or maximum is None) and not unknown_bounds_allowed:
            errors.append("Null execution bounds are allowed only for draft migrations.")
        if isinstance(minimum, int) and not isinstance(minimum, bool) and minimum < 1:
            errors.append("execution.minimum_minutes must be positive.")
        if isinstance(maximum, int) and not isinstance(maximum, bool) and maximum < 1:
            errors.append("execution.maximum_minutes must be positive.")
        if (
            isinstance(minimum, int)
            and not isinstance(minimum, bool)
            and isinstance(maximum, int)
            and not isinstance(maximum, bool)
            and minimum > maximum
        ):
            errors.append("execution.minimum_minutes cannot exceed maximum_minutes.")
        if execution.get("interaction") not in {"unattended", "interactive", "mixed"}:
            errors.append("execution.interaction must be unattended, interactive, or mixed.")

    validate_resources(data.get("resources"), data.get("effects"), errors)

    continuity = require(data, "continuity", dict, errors)
    if continuity is not None:
        if continuity.get("state_authority") != "package":
            errors.append("continuity.state_authority must be package.")
        require(continuity, "read_before_run", bool, errors, "continuity.")
        require(continuity, "update_after_run", bool, errors, "continuity.")
        require(continuity, "handoff_when_read_only", bool, errors, "continuity.")

    if data.get("privacy") not in {"private", "internal", "public"}:
        errors.append("privacy must be private, internal, or public.")

    return runner_path, task_path, state_path


def has_template_marker(text: str) -> bool:
    return "{{" in text or "}}" in text


def validate_text_files(
    package: Path,
    runner_path: Path | None,
    task_path: Path | None,
    state_path: Path | None,
    warnings: list[str],
    errors: list[str],
) -> None:
    is_migration = (package / "migration.json").exists()

    if runner_path is not None:
        runner = runner_path.read_text(encoding="utf-8")
        if not runner.strip():
            errors.append("runner.md must not be empty.")
        if has_template_marker(runner):
            errors.append("runner.md contains an unresolved template marker.")
        for required in (
            "manifest.json",
            "task_file",
            "state_file",
            "allowed effects",
            "State handoff",
        ):
            if required not in runner:
                errors.append(f"runner.md must reference {required}.")

    if task_path is not None:
        task = task_path.read_text(encoding="utf-8")
        if not task.strip():
            errors.append("task.md must not be empty.")
        if has_template_marker(task):
            errors.append("task.md contains an unresolved template marker.")
        missing = [heading for heading in TASK_HEADINGS if heading not in task]
        if missing:
            message = "task.md does not use the standard task structure."
            if is_migration:
                warnings.append(f"{message} Preserve it during migration and refine separately.")
            else:
                errors.append(message)
        lowered = task.lower()
        for marker, message in PORTABILITY_MARKERS.items():
            if marker in lowered:
                warnings.append(f"task.md: {message}")

    if state_path is not None:
        state = state_path.read_text(encoding="utf-8")
        if has_template_marker(state):
            errors.append("state.md contains an unresolved template marker.")
        missing = [heading for heading in STATE_HEADINGS if heading not in state]
        if missing:
            warnings.append("state.md uses a legacy structure; preserve it during migration and normalize separately.")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_migration(
    package: Path,
    task_path: Path | None,
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
    selected_task_sources: list[dict[str, Any]] = []
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
            for key in ("selected_task", "selected_state"):
                if not isinstance(source.get(key), bool):
                    errors.append(f"migration.json sources[{index}].{key} must be boolean.")
            if source.get("selected_task") is True:
                selected_task_sources.append(source)
            if source.get("selected_state") is True:
                selected_state_sources.append(source)
            task_hash = source.get("task_sha256")
            if not isinstance(task_hash, str) or not SHA256_PATTERN.fullmatch(task_hash):
                errors.append(f"migration.json sources[{index}].task_sha256 must be a SHA-256 digest.")
            packaged_task_hash = source.get("packaged_task_sha256")
            if not isinstance(packaged_task_hash, str) or not SHA256_PATTERN.fullmatch(packaged_task_hash):
                errors.append(
                    f"migration.json sources[{index}].packaged_task_sha256 must be a SHA-256 digest."
                )
            normalizations = source.get("normalizations")
            if not isinstance(normalizations, list) or any(
                not isinstance(item, str) or not item for item in normalizations
            ):
                errors.append(
                    f"migration.json sources[{index}].normalizations must be a list of non-empty strings."
                )
            if (
                isinstance(task_hash, str)
                and isinstance(packaged_task_hash, str)
                and task_hash != packaged_task_hash
                and not normalizations
                and data.get("behavior_changed") is False
            ):
                errors.append(
                    f"migration.json sources[{index}] must explain differing source and packaged checksums."
                )
            state_hash = source.get("state_sha256")
            if state_hash is not None and (
                not isinstance(state_hash, str) or not SHA256_PATTERN.fullmatch(state_hash)
            ):
                errors.append(f"migration.json sources[{index}].state_sha256 must be null or a SHA-256 digest.")

        if len(selected_task_sources) != 1:
            errors.append("migration.json must select exactly one task source.")
        if len(selected_state_sources) > 1:
            errors.append("migration.json may select at most one state source.")

    for key in ("behavior_changed", "state_changed", "deployment_changed"):
        if not isinstance(data.get(key), bool):
            errors.append(f"migration.json {key} must be boolean.")
    migration_warnings = data.get("warnings")
    if not isinstance(migration_warnings, list) or any(
        not isinstance(item, str) for item in migration_warnings
    ):
        errors.append("migration.json warnings must be a list of strings.")

    if task_path is not None and len(selected_task_sources) == 1:
        if sha256(task_path) != selected_task_sources[0].get("packaged_task_sha256"):
            errors.append("task.md checksum does not match the recorded packaged task checksum.")
    if state_path is not None and data.get("state_changed") is False and len(selected_state_sources) == 1:
        if sha256(state_path) != selected_state_sources[0].get("state_sha256"):
            warnings.append("state.md has changed since the imported migration baseline, as expected after task runs.")


def validate_adapters(package: Path, errors: list[str]) -> None:
    deployments = package / "deployments"
    if not deployments.exists():
        return
    if not deployments.is_dir():
        errors.append("deployments must be a directory.")
        return
    for path in sorted(deployments.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"Cannot read deployment adapter {path.name}: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"Deployment adapter {path.name} must contain a JSON object.")


def validate(package: Path) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    if not package.is_dir():
        print(f"ERROR: package directory does not exist: {package}")
        return 1

    manifest = read_json(package / "manifest.json", errors)
    runner_path: Path | None = None
    task_path: Path | None = None
    state_path: Path | None = None
    if manifest is not None:
        runner_path, task_path, state_path = validate_manifest(
            package, manifest, warnings, errors
        )
    validate_text_files(package, runner_path, task_path, state_path, warnings, errors)
    validate_migration(package, task_path, state_path, warnings, errors)
    validate_adapters(package, errors)

    for warning in dict.fromkeys(warnings):
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    warning_count = len(dict.fromkeys(warnings))
    if errors:
        print(f"FAILED: {len(errors)} error(s), {warning_count} warning(s)")
        return 1
    print(f"VALID: {package} ({warning_count} warning(s))")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="Path to one task package directory")
    args = parser.parse_args()
    return validate(args.package.resolve())


if __name__ == "__main__":
    sys.exit(main())
