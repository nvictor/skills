#!/usr/bin/env python3
"""Discover, inspect, resolve, and bind a portable workflow root."""

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
BINDING_FILENAME = ".workflow-root.json"
BINDING_FIELD = "workflow_root"
ENVIRONMENT_BINDING = "WORKFLOW_ROOT"


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


def workspace_path(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if path.is_file():
        return path.parent
    return path


def binding_path(workspace: Path) -> Path:
    return workspace / BINDING_FILENAME


def validate_workflow_root(root: Path) -> Path:
    if not root.is_dir():
        raise RegistryError(f"Workflow root does not exist: {root}")
    return root


def resolve_binding_value(value: Any, base: Path, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise RegistryError(f"{label} must be a non-empty path string.")
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = base / candidate
    return validate_workflow_root(candidate.resolve())


def locate_workflow_root(start: Path) -> tuple[Path, str, Path | None]:
    environment_value = os.environ.get(ENVIRONMENT_BINDING)
    if environment_value:
        root = resolve_binding_value(
            environment_value, Path.cwd(), f"{ENVIRONMENT_BINDING}"
        )
        return root, "environment", None

    current = workspace_path(str(start))
    for directory in (current, *current.parents):
        candidate = binding_path(directory)
        if not candidate.exists():
            continue
        binding = read_json(candidate, BINDING_FILENAME)
        root = resolve_binding_value(
            binding.get(BINDING_FIELD), directory, f"{candidate} {BINDING_FIELD}"
        )
        return root, "workspace", candidate

    raise RegistryError(
        f"No workflow-root binding was found from {current}. "
        f"Set {ENVIRONMENT_BINDING} or create {BINDING_FILENAME} in the workspace."
    )


def portable_binding_value(workspace: Path, root: Path) -> str:
    try:
        relative = root.relative_to(workspace)
    except ValueError:
        return str(root)
    return relative.as_posix()


def ensure_inside(root: Path, path: Path, label: str) -> Path:
    root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RegistryError(f"{label} resolves outside the workflow root.") from exc
    return resolved


def write_binding(workspace: Path, binding: dict[str, Any]) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    destination = binding_path(workspace)
    mode = destination.stat().st_mode & 0o777 if destination.exists() else 0o644
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=workspace,
            prefix=".workflow-root-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            json.dump(binding, temporary, indent=2, sort_keys=True)
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
    root = root.resolve()
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
    root = root.resolve()
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


def resolve_target(root: Path, target: str) -> dict[str, str]:
    root = root.resolve()
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

    incomplete = [
        record
        for record in discover(root)
        if record["status"] not in TERMINAL_STATUSES | {"invalid"}
    ]
    if len(incomplete) == 1:
        return incomplete[0], "sole-incomplete"
    if not incomplete:
        raise RegistryError(
            "No nonterminal workflow was found. "
            "Supply an explicit target to inspect a terminal workflow."
        )
    candidates = ", ".join(record["path"] for record in incomplete)
    raise RegistryError(
        "Multiple nonterminal workflows were found; "
        f"supply an explicit target: {candidates}"
    )


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def command_list(root: Path) -> None:
    validate_workflow_root(root)
    print_json({"root": str(root), "workflows": discover(root)})


def command_resolve(root: Path, target: str | None) -> None:
    record, source = resolve_workflow(root, target)
    print_json({"root": str(root), "source": source, "workflow": record})


def command_validate(root: Path) -> None:
    validate_workflow_root(root)
    records = discover(root)
    invalid = [record for record in records if record["status"] == "invalid"]
    if invalid:
        details = "; ".join(
            f"{record['path']}: {record['error']}" for record in invalid
        )
        raise RegistryError(f"Invalid workflow packages: {details}")
    print_json({"root": str(root), "valid": True, "workflow_count": len(records)})


def command_bind(workspace: Path, root: Path) -> None:
    if not workspace.is_dir():
        raise RegistryError(f"Workspace does not exist: {workspace}")
    validate_workflow_root(root)
    path = binding_path(workspace)
    binding = read_json(path, BINDING_FILENAME) if path.exists() else {}
    binding[BINDING_FIELD] = portable_binding_value(workspace, root)
    write_binding(workspace, binding)
    written = read_json(path, BINDING_FILENAME)
    located_root = resolve_binding_value(
        written.get(BINDING_FIELD), workspace, f"{path} {BINDING_FIELD}"
    )
    if located_root != root:
        raise RegistryError(f"Workflow-root binding verification failed: {path}")
    print_json(
        {
            "workspace": str(workspace),
            "binding_file": str(path),
            "workflow_root": str(root),
            "stored_value": binding[BINDING_FIELD],
        }
    )


def command_locate(start: Path) -> None:
    root, source, path = locate_workflow_root(start)
    print_json(
        {
            "start": str(workspace_path(str(start))),
            "source": source,
            "binding_file": str(path) if path is not None else None,
            "workflow_root": str(root),
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("list", "validate"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("root", help="User-selected workflow root")

    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("root", help="User-selected workflow root")
    resolve.add_argument("target", nargs="?", help="Workflow id, relative path, or path")

    bind = subparsers.add_parser("bind")
    bind.add_argument("workspace", help="Workspace directory that should own the binding")
    bind.add_argument("root", help="User-selected workflow root")

    locate = subparsers.add_parser("locate")
    locate.add_argument(
        "start",
        nargs="?",
        default=".",
        help="Directory from which to resolve the nearest workspace binding",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "list":
            command_list(workflow_root(args.root))
        elif args.command == "resolve":
            command_resolve(workflow_root(args.root), args.target)
        elif args.command == "validate":
            command_validate(workflow_root(args.root))
        elif args.command == "bind":
            command_bind(workspace_path(args.workspace), workflow_root(args.root))
        elif args.command == "locate":
            command_locate(workspace_path(args.start))
        else:
            raise RegistryError(f"Unsupported command: {args.command}")
    except RegistryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
