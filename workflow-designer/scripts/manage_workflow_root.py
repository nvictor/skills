#!/usr/bin/env python3
"""Initialize, inspect, resolve, and update a portable workflow root."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


STATUS_PATTERN = re.compile(r"^Status:\s*([a-z_]+)\s*$", re.MULTILINE)
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STATUSES = {"draft", "in_progress", "paused", "blocked", "completed", "abandoned"}
TERMINAL_STATUSES = {"completed", "abandoned"}


class RegistryError(Exception):
    """Report a workflow-root contract violation."""


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryError(f"Missing {label}: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Cannot read {label} at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistryError(f"{label} must contain a JSON object: {path}")
    return value


def workflow_root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def root_state_path(root: Path) -> Path:
    return root / "state.json"


def validate_relative_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise RegistryError(f"{label} must be a non-empty relative path.")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
        raise RegistryError(f"{label} must stay inside the workflow root.")
    return relative


def ensure_inside(root: Path, path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RegistryError(f"{label} resolves outside the workflow root.") from exc
    return resolved


def load_root_state(root: Path) -> dict[str, Any]:
    state = read_json(root_state_path(root), "workflow-root state.json")
    if "active" not in state:
        raise RegistryError("workflow-root state.json must contain an 'active' field.")
    active = state["active"]
    if active is not None:
        validate_relative_path(active, "state.json active")
    return state


def write_root_state(root: Path, state: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    destination = root_state_path(root)
    mode = destination.stat().st_mode & 0o777 if destination.exists() else 0o644
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=root,
            prefix=".workflow-state-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            json.dump(state, temporary, indent=2, sort_keys=True)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, destination)
    finally:
        if temporary_name is not None:
            temporary_path = Path(temporary_name)
            if temporary_path.exists():
                temporary_path.unlink()


def safe_package_file(package: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise RegistryError(f"{label} must be a non-empty relative path.")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise RegistryError(f"{label} must stay inside its workflow package.")
    path = (package / relative).resolve()
    try:
        path.relative_to(package.resolve())
    except ValueError as exc:
        raise RegistryError(f"{label} resolves outside its workflow package.") from exc
    if not path.is_file():
        raise RegistryError(f"{label} does not exist: {path}")
    return path


def read_package(root: Path, package: Path) -> dict[str, str]:
    package = ensure_inside(root, package, "Workflow package")
    if package == root:
        raise RegistryError("A workflow package must be below the workflow root.")
    manifest = read_json(package / "manifest.json", "workflow manifest")
    if "workflow_file" not in manifest:
        raise RegistryError(f"Package is not a workflow package: {package}")
    if "task_file" in manifest or "prompt_file" in manifest:
        raise RegistryError(f"Package has conflicting type discriminators: {package}")

    workflow_id = manifest.get("id")
    if not isinstance(workflow_id, str) or not ID_PATTERN.fullmatch(workflow_id):
        raise RegistryError(f"Workflow manifest id is missing or invalid: {package}")
    if package.name != workflow_id:
        raise RegistryError(
            f"Workflow directory '{package.name}' does not match id '{workflow_id}'."
        )
    for field in ("workflow_file", "memory_file", "runner_file"):
        safe_package_file(package, manifest.get(field), field)
    state_path = safe_package_file(package, manifest.get("state_file"), "state_file")

    try:
        state_text = state_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RegistryError(f"Cannot read package state at {state_path}: {exc}") from exc
    match = STATUS_PATTERN.search(state_text)
    if match is None or match.group(1) not in STATUSES:
        raise RegistryError(f"Package has an invalid lifecycle status: {package}")

    return {
        "id": workflow_id,
        "path": package.relative_to(root).as_posix(),
        "status": match.group(1),
    }


def discover(root: Path) -> list[dict[str, str]]:
    if not root.is_dir():
        raise RegistryError(f"Workflow root does not exist: {root}")
    records: list[dict[str, str]] = []
    for manifest_path in root.rglob("manifest.json"):
        try:
            manifest = read_json(manifest_path, "manifest")
        except RegistryError:
            continue
        if "workflow_file" not in manifest:
            continue
        try:
            records.append(read_package(root, manifest_path.parent))
        except RegistryError as exc:
            relative = manifest_path.parent.relative_to(root).as_posix()
            records.append(
                {
                    "id": str(manifest.get("id", relative)),
                    "path": relative,
                    "status": "invalid",
                    "error": str(exc),
                }
            )
    return sorted(records, key=lambda record: record["path"])


def package_from_relative(root: Path, relative_value: str) -> dict[str, str]:
    relative = validate_relative_path(relative_value, "Workflow package")
    package = ensure_inside(root, root / relative, "Workflow package")
    return read_package(root, package)


def resolve_target(root: Path, target: str) -> dict[str, str]:
    candidate = Path(target).expanduser()
    if candidate.is_absolute():
        package = ensure_inside(root, candidate, "Explicit workflow package")
        return read_package(root, package)

    direct = root / candidate
    if (direct / "manifest.json").is_file():
        return read_package(root, direct)

    matches = [record for record in discover(root) if record["id"] == target]
    if not matches:
        raise RegistryError(f"No workflow matches target '{target}'.")
    if len(matches) > 1:
        paths = ", ".join(record["path"] for record in matches)
        raise RegistryError(f"Workflow id '{target}' is ambiguous: {paths}")
    match = matches[0]
    if match["status"] == "invalid":
        raise RegistryError(match["error"])
    return match


def resolve_workflow(root: Path, target: str | None) -> tuple[dict[str, str], str]:
    if target is not None:
        return resolve_target(root, target), "explicit"

    state = load_root_state(root)
    active = state["active"]
    if active is not None:
        record = package_from_relative(root, active)
        if record["status"] in TERMINAL_STATUSES:
            raise RegistryError(
                f"Active pointer references a terminal workflow: {record['path']}"
            )
        return record, "active"

    incomplete = [
        record
        for record in discover(root)
        if record["status"] not in TERMINAL_STATUSES | {"invalid"}
    ]
    if len(incomplete) == 1:
        return incomplete[0], "sole-incomplete"
    if not incomplete:
        raise RegistryError("No active or incomplete workflow was found.")
    candidates = ", ".join(record["path"] for record in incomplete)
    raise RegistryError(f"No workflow is active. Incomplete workflows: {candidates}")


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def command_init(root: Path) -> None:
    path = root_state_path(root)
    if path.exists():
        state = load_root_state(root)
        print_json({"root": str(root), "state": state, "created": False})
        return
    state = {"active": None}
    write_root_state(root, state)
    print_json({"root": str(root), "state": state, "created": True})


def command_list(root: Path) -> None:
    state = load_root_state(root)
    if state["active"] is not None:
        active_record = package_from_relative(root, state["active"])
        if active_record["status"] in TERMINAL_STATUSES:
            raise RegistryError(
                f"Active pointer references a terminal workflow: {active_record['path']}"
            )
    records = discover(root)
    for record in records:
        record["selected"] = record["path"] == state["active"]
    print_json({"root": str(root), "active": state["active"], "workflows": records})


def command_resolve(root: Path, target: str | None) -> None:
    record, source = resolve_workflow(root, target)
    print_json({"root": str(root), "source": source, "workflow": record})


def command_activate(root: Path, target: str) -> None:
    record = resolve_target(root, target)
    if record["status"] in TERMINAL_STATUSES:
        raise RegistryError(
            f"Cannot activate a workflow with status {record['status']}: {record['path']}"
        )
    state = load_root_state(root)
    state["active"] = record["path"]
    write_root_state(root, state)
    print_json({"root": str(root), "active": record["path"], "workflow": record})


def command_clear(root: Path, target: str | None) -> None:
    record = resolve_target(root, target) if target is not None else None
    state = load_root_state(root)
    previous = state["active"]
    if target is not None:
        assert record is not None
        if previous != record["path"]:
            print_json(
                {
                    "root": str(root),
                    "active": previous,
                    "cleared": False,
                    "reason": "target-is-not-active",
                }
            )
            return
    state["active"] = None
    write_root_state(root, state)
    print_json({"root": str(root), "active": None, "cleared": previous is not None})


def command_validate(root: Path) -> None:
    state = load_root_state(root)
    active = state["active"]
    record = None
    if active is not None:
        record = package_from_relative(root, active)
        if record["status"] in TERMINAL_STATUSES:
            raise RegistryError(
                f"Active pointer references a terminal workflow: {record['path']}"
            )
    print_json({"root": str(root), "valid": True, "active": active, "workflow": record})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("init", "list", "validate"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("root", help="User-selected workflow root")

    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("root", help="User-selected workflow root")
    resolve.add_argument("target", nargs="?", help="Workflow id, relative path, or path")

    activate = subparsers.add_parser("activate")
    activate.add_argument("root", help="User-selected workflow root")
    activate.add_argument("target", help="Workflow id, relative path, or path")

    clear = subparsers.add_parser("clear")
    clear.add_argument("root", help="User-selected workflow root")
    clear.add_argument(
        "--if-active",
        dest="target",
        help="Clear only when this workflow id or path is active",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = workflow_root(args.root)
    try:
        if args.command == "init":
            command_init(root)
        elif args.command == "list":
            command_list(root)
        elif args.command == "resolve":
            command_resolve(root, args.target)
        elif args.command == "activate":
            command_activate(root, args.target)
        elif args.command == "clear":
            command_clear(root, args.target)
        elif args.command == "validate":
            command_validate(root)
        else:
            raise RegistryError(f"Unsupported command: {args.command}")
    except RegistryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
