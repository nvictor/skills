#!/usr/bin/env python3
"""Validate the portable conversation file contract using the standard library."""

import argparse
import json
from pathlib import Path, PureWindowsPath
import re


FILES = ("conversation_file", "state_file", "memory_file", "runner_file")
KEYS = {"schema_version", "id", "name", *FILES}
HEADINGS = {
    "conversation_file": ("## Subject and intent", "## Conversational style",
                          "## Boundaries", "## Starting behavior"),
    "state_file": ("# Conversation state", "## Current question", "## Unresolved threads",
                   "## Pending exchange", "## Resume point"),
    "memory_file": ("# Conversation memory", "## Hypotheses and explanations",
                    "## Distinctions and examples", "## Objections and revisions",
                    "## Qualified conclusions"),
}


def validate(package: Path) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    try:
        data = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        return [f"Cannot read manifest.json: {exc}"], warnings
    if not isinstance(data, dict):
        return ["manifest.json must contain an object."], warnings
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        errors.append("schema_version must be integer 1.")
    identifier = data.get("id")
    if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier):
        errors.append("id must use lowercase letters, digits, and single hyphens.")
    elif identifier != package.name:
        errors.append("id must match the package directory name.")
    name = data.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"Conversation: \S(?:[^\r\n]*\S)?", name):
        errors.append("name must use 'Conversation: <subject>' with a trimmed, nonempty subject.")
    for key in ("prompt_file", "workflow_file", "task_file"):
        if key in data:
            errors.append(f"Conflicting package discriminator: {key}")
    for key in sorted(data.keys() - KEYS - {"prompt_file", "workflow_file", "task_file"}):
        warnings.append(f"Noncanonical manifest extension: {key}")
    if re.search(r"\{\{.*?\}\}", json.dumps(data)):
        errors.append("manifest.json contains an unresolved template marker.")
    paths = set()
    for key in FILES:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a nonempty relative path.")
            continue
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts or PureWindowsPath(value).drive or "\\" in value:
            errors.append(f"{key} must use a safe relative path inside the package.")
            continue
        try:
            path = (package / relative).resolve()
            path.relative_to(package.resolve())
            if path == (package / "manifest.json").resolve() or path in paths:
                errors.append(f"{key} must reference a distinct file.")
                continue
            paths.add(path)
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
            errors.append(f"Cannot read safe {key}: {exc}")
            continue
        if not content.strip():
            errors.append(f"{key} must not be empty.")
        if re.search(r"\{\{.*?\}\}", content, re.DOTALL):
            errors.append(f"{key} contains an unresolved template marker.")
        lines = content.splitlines()
        for heading in HEADINGS.get(key, ()):
            if heading not in lines:
                errors.append(f"{key} is missing heading: {heading}")
        if key == "conversation_file" and (not lines or lines[0] != f"# {name}"):
            errors.append("conversation_file title must match manifest name.")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    errors, warnings = validate(args.package.resolve())
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if not errors:
        print("Valid conversation package.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
