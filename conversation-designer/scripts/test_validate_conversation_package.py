"""Structural contract tests. Behavioral scenarios live in the quality rubric."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from validate_conversation_package import validate


class ConversationPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.package = Path(self.temp.name) / "verse-and-chorus"
        template = Path(__file__).resolve().parents[1] / "assets/conversation-package"
        shutil.copytree(template, self.package)
        replacements = {
            "{{conversation-id}}": "verse-and-chorus",
            "{{Subject}}": "Verse and Chorus",
            "{{Describe the inquiry and why it matters.}}": "Explore how musical sections function.",
            "{{Describe material scope and constraints.}}": "Synthetic scenario; no original transcript is available.",
            "{{Describe a focused opening if no prior exchange exists.}}": "Explore what makes a chorus feel like a chorus.",
            "{{Initial question or supported current focus.}}": "Can chorus function explain descending melodies?",
        }
        for path in self.package.iterdir():
            content = path.read_text()
            for old, new in replacements.items():
                content = content.replace(old, new)
            path.write_text(content)
        self.manifest = json.loads((self.package / "manifest.json").read_text())

    def save(self):
        (self.package / "manifest.json").write_text(json.dumps(self.manifest))

    def test_valid_package_and_read_only_validation(self):
        before = {p.name: p.read_bytes() for p in self.package.iterdir()}
        self.assertEqual(([], []), validate(self.package))
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.package.iterdir()})

    def test_invalid_names(self):
        for name in (None, 3, "Verse and Chorus", "Conversation: ", "Conversation:  Test",
                     "Conversation: Test ", "Conversation: Test\nOther"):
            with self.subTest(name=name):
                self.manifest["name"] = name
                self.save()
                self.assertTrue(validate(self.package)[0])

    def test_id_and_schema(self):
        for key, value in (("id", "other"), ("id", "Bad--ID"), ("schema_version", True),
                           ("schema_version", 2)):
            with self.subTest(key=key, value=value):
                original = self.manifest[key]
                self.manifest[key] = value
                self.save()
                self.assertTrue(validate(self.package)[0])
                self.manifest[key] = original

    def test_conflicting_discriminators(self):
        for key in ("prompt_file", "workflow_file", "task_file"):
            self.manifest[key] = "other.md"
            self.save()
            self.assertTrue(any("discriminator" in e for e in validate(self.package)[0]))
            del self.manifest[key]

    def test_unsafe_missing_and_aliased_paths(self):
        for value in ("../outside.md", "/tmp/outside.md", "C:\\outside.md", "missing.md",
                      "memory.md", "manifest.json", "", None):
            with self.subTest(value=value):
                self.manifest["state_file"] = value
                self.save()
                self.assertTrue(validate(self.package)[0])

    def test_symlink_escape(self):
        external = Path(self.temp.name) / "external.md"
        external.write_text((self.package / "state.md").read_text())
        (self.package / "state.md").unlink()
        (self.package / "state.md").symlink_to(external)
        self.assertTrue(validate(self.package)[0])

    def test_missing_empty_and_template_files(self):
        path = self.package / "state.md"
        for content in ("", "{{pending}}"):
            path.write_text(content)
            self.assertTrue(validate(self.package)[0])
        path.unlink()
        self.assertTrue(validate(self.package)[0])

    def test_unknown_extension_warns_without_rewriting(self):
        self.manifest["custom"] = {"keep": True}
        self.save()
        errors, warnings = validate(self.package)
        self.assertFalse(errors)
        self.assertTrue(warnings)
        self.assertEqual(self.manifest, json.loads((self.package / "manifest.json").read_text()))

    def test_invalid_manifest(self):
        for content in ("{", "[]", "null"):
            (self.package / "manifest.json").write_text(content)
            self.assertTrue(validate(self.package)[0])


if __name__ == "__main__":
    unittest.main()
