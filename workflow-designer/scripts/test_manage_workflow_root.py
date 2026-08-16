#!/usr/bin/env python3
"""Regression tests for workflow-root discovery without activation state."""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("manage_workflow_root.py")
SPEC = importlib.util.spec_from_file_location("manage_workflow_root", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
REGISTRY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REGISTRY)


def create_package(root: Path, workflow_id: str, status: str) -> Path:
    package = root / workflow_id
    package.mkdir(parents=True)
    (package / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": workflow_id,
                "workflow_file": "workflow.md",
                "state_file": "state.md",
                "memory_file": "memory.md",
                "runner_file": "runner.md",
            }
        ),
        encoding="utf-8",
    )
    (package / "workflow.md").write_text("# Goal\n", encoding="utf-8")
    (package / "state.md").write_text(
        f"# Workflow state\n\nStatus: {status}\n", encoding="utf-8"
    )
    (package / "memory.md").write_text("# Workflow memory\n", encoding="utf-8")
    (package / "runner.md").write_text(
        "# Portable workflow runner\n", encoding="utf-8"
    )
    return package


class WorkflowRootTests(unittest.TestCase):
    def test_sole_nonterminal_resolves_without_root_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_package(root, "one", "in_progress")

            record, source = REGISTRY.resolve_workflow(root, None)

            self.assertEqual("one", record["id"])
            self.assertEqual("sole-incomplete", source)

    def test_legacy_root_state_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_package(root, "current", "in_progress")
            (root / "state.json").write_text(
                '{"active": "missing"}\n', encoding="utf-8"
            )

            record, source = REGISTRY.resolve_workflow(root, None)

            self.assertEqual("current", record["id"])
            self.assertEqual("sole-incomplete", source)

    def test_multiple_nonterminal_workflows_require_explicit_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_package(root, "one", "draft")
            create_package(root, "two", "blocked")

            with self.assertRaisesRegex(
                REGISTRY.RegistryError, "supply an explicit target"
            ):
                REGISTRY.resolve_workflow(root, None)

            record, source = REGISTRY.resolve_workflow(root, "two")
            self.assertEqual("two", record["id"])
            self.assertEqual("explicit", source)

    def test_list_has_no_selection_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_package(root, "one", "in_progress")
            output = io.StringIO()

            with redirect_stdout(output):
                REGISTRY.command_list(root)

            payload = json.loads(output.getvalue())
            self.assertNotIn("active", payload)
            self.assertNotIn("selected", payload["workflows"][0])


if __name__ == "__main__":
    unittest.main()
