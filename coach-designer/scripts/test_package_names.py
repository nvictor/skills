"""Validate canonical display names through the package manifest interface."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from validate_coach_package import validate_manifest


class PackageNameTests(unittest.TestCase):
    def errors_for(self, name, missing=False):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "example"
            template = Path(__file__).resolve().parents[1] / "assets/coach-package"
            shutil.copytree(template, package)
            manifest = json.loads((package / "manifest.json").read_text())
            manifest["id"] = "example"
            if missing:
                manifest.pop("name")
            else:
                manifest["name"] = name
            errors = []
            validate_manifest(package, manifest, errors)
            return errors

    def test_accepts_canonical_names(self):
        for name in ("Coach: Example", "Coach: SRE", "Coach: X"):
            with self.subTest(name=name):
                self.assertEqual([], self.errors_for(name))

    def test_rejects_invalid_names(self):
        for name in ("Example", "Other: Example", "coach: Example", "Coach:",
                     "Coach: ", "Coach:   ", "Coach:  Example", "Coach: Example ",
                     " Coach: Example", "Coach: Example\nSecond line", "", None, 42):
            with self.subTest(name=name):
                errors = self.errors_for(name)
                self.assertTrue(errors)
                self.assertTrue(all(error.startswith("name ") for error in errors), errors)

    def test_requires_name(self):
        self.assertEqual(["name must be str."], self.errors_for(None, missing=True))


if __name__ == "__main__":
    unittest.main()
