#!/usr/bin/env python3
"""Tests for workflow package lifecycle status validation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_workflow_package import STATUSES, validate_state, validate_runner


STATE_TEMPLATE = """# Workflow state

Status: {status}

## Current step

## Completed steps

## Blockers

## Pending decisions

## Working artifacts

## Open operation
"""


class ValidateWorkflowStateTests(unittest.TestCase):
    def validate_status(self, status: str) -> list[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            state_path = Path(temporary_directory) / "state.md"
            state_path.write_text(STATE_TEMPLATE.format(status=status), encoding="utf-8")
            errors: list[str] = []
            validate_state(state_path, errors)
            return errors

    def test_accepts_every_exact_lifecycle_status(self) -> None:
        for status in STATUSES:
            with self.subTest(status=status):
                self.assertEqual([], self.validate_status(status))

    def test_rejects_humanized_lifecycle_status(self) -> None:
        self.assertEqual(
            [
                "state_file status must be draft, in_progress, paused, blocked, "
                "completed, or abandoned."
            ],
            self.validate_status("in progress"),
        )


class ValidateWorkflowRunnerTests(unittest.TestCase):
    def test_accepts_current_and_legacy_runner(self) -> None:
        template = (Path(__file__).resolve().parents[1] / "assets/workflow-package/runner.md").read_text()
        for text in (template, template.replace("workflow-", "workflow:")):
            with self.subTest(legacy="workflow:" in text), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "runner.md"
                path.write_text(text)
                errors = []
                validate_runner(path, errors)
                self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
