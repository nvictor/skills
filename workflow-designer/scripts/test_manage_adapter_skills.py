#!/usr/bin/env python3
"""Regression tests for embedded workflow façade skill bindings."""

from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("manage_adapter_skills.py")
SPEC = importlib.util.spec_from_file_location("manage_adapter_skills", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MANAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MANAGER)


class AdapterSkillTests(unittest.TestCase):
    def test_install_verify_and_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skills_dir = Path(directory) / "skills"
            output = io.StringIO()

            with redirect_stdout(output):
                self.assertEqual(0, MANAGER.install(skills_dir))
                self.assertEqual(0, MANAGER.install(skills_dir))
                self.assertEqual(0, MANAGER.verify(skills_dir))

            for name in MANAGER.ADAPTER_NAMES:
                target = skills_dir / name
                source = MANAGER.ADAPTER_ROOT / name
                self.assertTrue(target.is_symlink())
                self.assertEqual(source.resolve(), target.resolve())

            with redirect_stdout(output):
                self.assertEqual(0, MANAGER.uninstall(skills_dir))

            for name in MANAGER.ADAPTER_NAMES:
                self.assertFalse((skills_dir / name).is_symlink())

    def test_install_refuses_all_changes_when_one_target_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skills_dir = Path(directory) / "skills"
            conflict = skills_dir / "workflow-run"
            conflict.mkdir(parents=True)
            errors = io.StringIO()

            with redirect_stderr(errors):
                self.assertEqual(1, MANAGER.install(skills_dir))

            self.assertIn("conflicting path", errors.getvalue())
            for name in MANAGER.ADAPTER_NAMES:
                if name != "workflow-run":
                    self.assertFalse((skills_dir / name).exists())

    def test_uninstall_refuses_unrelated_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills_dir = root / "skills"
            skills_dir.mkdir()
            unrelated = root / "unrelated"
            unrelated.mkdir()
            (skills_dir / "workflow-run").symlink_to(
                unrelated, target_is_directory=True
            )
            errors = io.StringIO()

            with redirect_stderr(errors):
                self.assertEqual(1, MANAGER.uninstall(skills_dir))

            self.assertIn("refusing to remove unrelated path", errors.getvalue())
            self.assertTrue((skills_dir / "workflow-run").is_symlink())


if __name__ == "__main__":
    unittest.main()
