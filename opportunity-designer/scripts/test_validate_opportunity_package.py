"""Exercise opportunity package validation against usable and unsafe packages."""
import json
from pathlib import Path
import re
import tempfile
import unittest

from validate_opportunity_package import validate


class PackageValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'sample'
        self.root.mkdir()
        template = Path(__file__).resolve().parents[1] / 'assets/opportunity-package'
        for source in template.iterdir():
            text = source.read_text()
            text = re.sub(r'\{\{(.*?)\}\}', lambda m: {'id': 'sample', 'subject': 'Sample'}.get(m[1], 'Unknown, pending evaluation.'), text)
            (self.root / source.name).write_text(text)

    def manifest(self, **changes):
        path = self.root / 'manifest.json'
        data = json.loads(path.read_text())
        data.update(changes)
        path.write_text(json.dumps(data))

    def test_all_states_and_no_memory_requirement(self):
        state = self.root / 'state.md'
        original = state.read_text()
        for status in ('captured', 'evaluating', 'deferred', 'pursued', 'declined'):
            state.write_text(original.replace('Status: captured', f'Status: {status}'))
            self.assertEqual(validate(self.root), ([], []))

    def test_rejects_conflicts_and_wrong_version(self):
        self.manifest(workflow_file='opportunity.md', schema_version=2)
        errors, _ = validate(self.root)
        self.assertTrue(any('Conflicting' in e for e in errors))
        self.assertTrue(any('schema_version' in e for e in errors))

    def test_rejects_escaping_and_duplicate_references(self):
        self.manifest(state_file='../outside.md')
        self.assertTrue(validate(self.root)[0])
        self.manifest(state_file='opportunity.md')
        self.assertTrue(validate(self.root)[0])
        outside = Path(self.temp.name) / 'outside.md'
        outside.write_text('Outside')
        (self.root / 'escape.md').symlink_to(outside)
        self.manifest(state_file='escape.md')
        self.assertTrue(validate(self.root)[0])

    def test_rejects_ambiguous_lifecycle_and_unfilled_template(self):
        state = self.root / 'state.md'
        state.write_text(state.read_text().replace('Status: captured', 'Status: captured\nStatus: declined'))
        self.assertTrue(validate(self.root)[0])
        self.manifest(name='Opportunity: {{subject}}')
        self.assertTrue(any('template' in e for e in validate(self.root)[0]))


if __name__ == '__main__':
    unittest.main()
