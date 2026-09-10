"""Validate canonical display names through the package manifest interface."""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from validate_task_package import validate_manifest, validate_migration


class PackageNameTests(unittest.TestCase):
    def errors_for(self, name, missing=False):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "example"
            template = Path(__file__).resolve().parents[1] / "assets/task-package"
            shutil.copytree(template, package)
            manifest = json.loads((package / "manifest.json").read_text())
            manifest["id"] = "example"
            if missing:
                manifest.pop("name")
            else:
                manifest["name"] = name
            errors = []
            validate_manifest(package, manifest, [], errors)
            return errors

    def test_accepts_canonical_names(self):
        for name in ("Task: Example", "Task: SRE", "Task: X"):
            with self.subTest(name=name):
                self.assertEqual([], self.errors_for(name))

    def test_rejects_invalid_names(self):
        for name in ("Example", "Other: Example", "task: Example", "Task:",
                     "Task: ", "Task:   ", "Task:  Example", "Task: Example ",
                     " Task: Example", "Task: Example\nSecond line", "", None, 42):
            with self.subTest(name=name):
                errors = self.errors_for(name)
                self.assertTrue(errors)
                self.assertTrue(all(error.startswith("name ") for error in errors), errors)

    def test_requires_name(self):
        self.assertEqual(["name must be str."], self.errors_for(None, missing=True))


class MigrationTitleTests(unittest.TestCase):
    def test_preserves_baseline_but_rejects_body_or_unrelated_title_changes(self):
        body = b"# Purpose\n\nPerform the original task.\n"
        digest = hashlib.sha256(body).hexdigest()
        migration = {
            "schema_version": 1,
            "migrated_at": "2026-09-10T00:00:00-04:00",
            "sources": [{
                "kind": "test", "id": "example", "selected_task": True,
                "selected_state": False, "task_sha256": digest,
                "packaged_task_sha256": digest, "normalizations": [],
                "state_sha256": None,
            }],
            "behavior_changed": False, "state_changed": False,
            "deployment_changed": False, "warnings": [],
        }
        for content, valid in (
            (body, True),
            (b"# Task: Example\n\n" + body, True),
            (b"# Task: Example\n\n" + body + b"Extra instruction.\n", False),
            (b"# Task: Other\n\n" + body, False),
        ):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                package = Path(directory)
                (package / "manifest.json").write_text(json.dumps({"name": "Task: Example"}))
                (package / "migration.json").write_text(json.dumps(migration))
                task = package / "task.md"
                task.write_bytes(content)
                errors = []
                validate_migration(package, task, None, [], errors)
                self.assertEqual(not valid, bool(errors), errors)


if __name__ == "__main__":
    unittest.main()
