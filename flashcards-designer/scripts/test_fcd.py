#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import fcd


class DeckCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        (self.root / "docs").mkdir()
        (self.root / "cards" / "ds").mkdir(parents=True)
        (self.root / ".flashcards" / "drafts").mkdir(parents=True)
        self.doc = self.root / "docs" / "rep.md"
        self.doc.write_text("# Rep\n\n## Quorum\n\nR + W > N.\n\n## Other\n\nunrelated\n")

    def tearDown(self):
        self._tmp.cleanup()

    def draft(self, name="d.md", n=2):
        src = fcd.source_value(self.root / "cards" / "ds" / "rep.md", self.doc, "Quorum")
        body = "# Draft\n\n"
        for i in range(n):
            body += f"## Card {i}\n\nID: pending\nQ: Why overlap {i}?\nA: Because R+W>N {i}.\nSource: {src}\n\n"
        p = self.root / ".flashcards" / "drafts" / name
        p.write_text(body)
        return p

    def promote(self, name="d.md", n=2):
        return fcd.promote(self.root, self.draft(name, n), self.root / "cards" / "ds" / "rep.md", None)


class TestHash(DeckCase):
    def test_section_hash_ignores_other_sections(self):
        _, h1 = fcd.section_hash(self.doc, "Quorum")
        self.doc.write_text(self.doc.read_text().replace("unrelated", "changed"))
        _, h2 = fcd.section_hash(self.doc, "Quorum")
        self.assertEqual(h1, h2)

    def test_section_hash_detects_change(self):
        _, h1 = fcd.section_hash(self.doc, "Quorum")
        self.doc.write_text(self.doc.read_text().replace("R + W > N.", "R + W > N and more."))
        _, h2 = fcd.section_hash(self.doc, "Quorum")
        self.assertNotEqual(h1, h2)

    def test_missing_cases(self):
        self.assertEqual(fcd.section_hash(self.root / "nope.md", None)[0], "missing-file")
        self.assertEqual(fcd.section_hash(self.doc, "Nope")[0], "missing-section")

    def test_line_range(self):
        self.assertEqual(fcd.section_hash(self.doc, "L3-5")[0], "ok")
        self.assertEqual(fcd.section_hash(self.doc, "L90-99")[0], "missing-section")


class TestAllocate(DeckCase):
    def test_monotonic_and_never_reused(self):
        self.assertEqual(fcd.allocate(self.root, "rep", 2), ["rep-001", "rep-002"])
        self.assertEqual(fcd.allocate(self.root, "rep", 1), ["rep-003"])

    def test_respects_deck_max_when_registry_lost(self):
        self.promote()
        fcd.registry_path(self.root).unlink()
        self.assertEqual(fcd.allocate(self.root, "rep", 1), ["rep-003"])

    def test_rejects_bad_prefix(self):
        with self.assertRaises(fcd.FcdError):
            fcd.allocate(self.root, "Bad Prefix", 1)


class TestPromote(DeckCase):
    def test_promote_assigns_ids_and_moves_draft(self):
        got = self.promote()
        self.assertEqual([i for _, i in got], ["rep-001", "rep-002"])
        self.assertTrue((self.root / ".flashcards" / "drafts" / "_promoted" / "d.md").exists())
        cards = fcd.parse_cards(self.root / "cards" / "ds" / "rep.md")
        self.assertEqual([c.id for c in cards], ["rep-001", "rep-002"])

    def test_second_promote_appends(self):
        self.promote("a.md", 1)
        self.promote("b.md", 1)
        cards = fcd.parse_cards(self.root / "cards" / "ds" / "rep.md")
        self.assertEqual([c.id for c in cards], ["rep-001", "rep-002"])

    def test_rejects_draft_with_existing_id(self):
        p = self.draft()
        p.write_text(p.read_text().replace("ID: pending", "ID: rep-009", 1))
        with self.assertRaises(fcd.FcdError):
            fcd.promote(self.root, p, self.root / "cards" / "ds" / "rep.md", None)

    def test_rejects_target_outside_cards(self):
        with self.assertRaises(fcd.FcdError):
            fcd.promote(self.root, self.draft(), self.root / "elsewhere.md", None)


class TestCheck(DeckCase):
    def codes(self):
        return {f["code"] for f in fcd.check_deck(self.root)}

    def test_clean_deck(self):
        self.promote()
        self.assertEqual({f["severity"] for f in fcd.check_deck(self.root)} - {"info"}, set())

    def test_stale_and_missing_source(self):
        self.promote()
        self.doc.write_text(self.doc.read_text().replace("R + W > N.", "changed"))
        self.assertIn("SOURCE_STALE", self.codes())
        self.doc.unlink()
        self.assertIn("SOURCE_MISSING", self.codes())

    def test_pasted_source_is_unverifiable(self):
        f = self.root / "cards" / "ds" / "x.md"
        f.write_text("## T\n\nID: x-001\nQ: Why X?\nA: Y.\nSource: pasted: meeting notes\n")
        fcd.save_registry(self.root, {"version": 1, "counters": {"x": 1}})
        self.assertIn("SOURCE_UNVERIFIABLE", self.codes())

    def test_duplicate_id_and_registry_behind(self):
        self.promote()
        f = self.root / "cards" / "ds" / "rep.md"
        f.write_text(f.read_text() + f.read_text().split("## Card 0")[1].join(["\n## Dup", ""]).replace("rep-002", "rep-001", 1))
        self.assertIn("ID_DUPLICATE", self.codes())
        fcd.save_registry(self.root, {"version": 1, "counters": {}})
        self.assertIn("REGISTRY_BEHIND", self.codes())

    def test_quality_heuristics(self):
        f = self.root / "cards" / "ds" / "q.md"
        f.write_text(
            "## A\n\nID: q-001\nQ: Is it fast?\nA: " + "word " * 70 + "\nSource: pasted: x\n\n"
            "## B\n\nID: q-002\nQ: Is it fast?\nA: Yes.\nSource: pasted: x\n"
        )
        fcd.save_registry(self.root, {"version": 1, "counters": {"q": 2}})
        c = self.codes()
        self.assertTrue({"POSSIBLE_YES_NO", "ANSWER_OVERLOADED", "QUESTION_DUPLICATE"} <= c)

    def test_code_fence_does_not_split_cards(self):
        f = self.root / "cards" / "ds" / "f.md"
        f.write_text("## T\n\nID: f-001\nQ: Show it.\nA:\n```\n## not a card\nQ: nor a field\n```\nSource: pasted: x\n")
        cards = fcd.parse_cards(f)
        self.assertEqual(len(cards), 1)
        self.assertIn("## not a card", cards[0].fields["A"])


class TestMutation(DeckCase):
    def test_refresh_clears_stale(self):
        self.promote()
        self.doc.write_text(self.doc.read_text().replace("R + W > N.", "changed"))
        fcd.refresh_source(self.root, "rep-001")
        fcd.refresh_source(self.root, "rep-002")
        self.assertNotIn("SOURCE_STALE", {f["code"] for f in fcd.check_deck(self.root)})

    def test_retire_keeps_id_and_skips_checks(self):
        self.promote()
        fcd.retire(self.root, "rep-001", ["rep-002"], "2026-11-18")
        c = fcd.find_card(self.root, "rep-001")
        self.assertTrue(c.retired)
        self.assertIn("replaced-by: rep-002", c.fields["Retired"])
        self.assertEqual(fcd.allocate(self.root, "rep", 1), ["rep-003"])
        with self.assertRaises(fcd.FcdError):
            fcd.retire(self.root, "rep-001", [], "2026-11-18")


if __name__ == "__main__":
    unittest.main()
