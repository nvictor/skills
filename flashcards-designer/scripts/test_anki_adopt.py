#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import anki_adopt as a
import anki_sync as s
import fcd


def note(kind="cloze", nid=1, **fields):
    base = {"Text": "The {{c1::x}}.", "Back Extra": "", "ID": ""} if kind == "cloze" else {"Front": "Q?", "Back": "A.", "Speak": "", "ID": ""}
    return a.Note(nid, kind, {**base, **fields}, [{"cardId": 9, "deck": "anki::core::sre"}])


class TestAdoptable(unittest.TestCase):
    def test_cloze_ok(self):
        md, why = a.adoptable(note())
        self.assertEqual(md, {"C": "The {{c1::x}}."})

    def test_br_becomes_newline_and_round_trips(self):
        md, _ = a.adoptable(note(Text="3 ways:<br>{{c1::a}}<br>{{c2::b}}"))
        self.assertEqual(md["C"], "3 ways:\n{{c1::a}}\n{{c2::b}}")

    def test_basic_ok(self):
        md, _ = a.adoptable(note("basic"))
        self.assertEqual(md, {"Q": "Q?", "A": "A."})

    def test_skips_existing_id(self):
        self.assertIn("ID", a.adoptable(note(ID="x-001"))[1])

    def test_back_extra_becomes_x(self):
        md, _ = a.adoptable(note(**{"Back Extra": "why<br>because"}))
        self.assertEqual(md, {"C": "The {{c1::x}}.", "X": "why\nbecause"})

    def test_skips_html_that_would_change(self):
        md, why = a.adoptable(note(Text='<img src="a.png"> {{c1::x}}'))
        self.assertIsNone(md)
        self.assertIn("would change", why)

    def test_skips_empty_field(self):
        self.assertIsNone(a.adoptable(note(Text=" "))[0])


class TestDraft(unittest.TestCase):
    def test_draft_parses_and_titles_carry_note_id(self):
        body, ids, skipped = a.build_draft([note(nid=7), note(nid=8, ID="x-001")])
        self.assertEqual(ids, [7])
        self.assertEqual([n for n, _ in skipped], [8])
        self.assertIn("## anki-note-7", body)
        self.assertIn("ID: pending", body)

    def test_field_like_lines_are_escaped_and_survive(self):
        text = "Security scope (CAVE)\nC: {{c1::Credentials}}\nA: {{c2::Access}}\n## not a card"
        body, ids, skipped = a.build_draft([note(Text=text.replace("\n", "<br>").replace("&", "&amp;"))])
        self.assertEqual((ids, skipped), ([1], []))
        self.assertIn("\\C: {{c1::Credentials}}", body)
        self.assertIn("\\## not a card", body)

    def test_promoted_maps_note_to_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "core" / "sre").mkdir(parents=True)
            (root / "other").mkdir()
            (root / "core" / "sre" / "sre.md").write_text(
                "## anki-note-7\n\nID: sre-001\nC: The {{c1::x}}.\nSource: pasted: imported from Anki\n\n"
                "## hand written\n\nID: sre-002\nC: The {{c1::y}}.\nSource: pasted: z\n"
            )
            (root / "other" / "o.md").write_text("## anki-note-9\n\nID: o-001\nC: {{c1::z}}\nSource: pasted: z\n")
            self.assertEqual(a.promoted(root, "core/sre"), {7: "sre-001"})
            self.assertEqual(a.promoted(root, "core::sre"), {7: "sre-001"})


class TestLink(unittest.TestCase):
    def test_target_deck(self):
        self.assertEqual(a.target_deck("anki::repo", "core/sre"), "anki::repo::core::sre")
        self.assertEqual(a.target_deck("anki::repo", "core::sre/"), "anki::repo::core::sre")

    def test_plan_link_flags_problems(self):
        notes = [note(nid=1), note(nid=2, ID="other-001"), note(nid=3, ID="sre-003")]
        todo, problems = a.plan_link(notes, {1: "sre-001", 2: "sre-002", 3: "sre-003", 4: "sre-004"}, "d")
        self.assertEqual([(n.id, c) for n, c in todo], [(1, "sre-001"), (3, "sre-003")])
        self.assertEqual(len(problems), 2)

    def test_link_refuses_non_anki_parent(self):
        with self.assertRaises(s.SyncError):
            s.require_root_deck("elsewhere")


if __name__ == "__main__":
    unittest.main()
