#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import anki_sync as s
import fcd

NAMES = {"basic": "Basic", "cloze": "Cloze"}


def desired(id_="t-001", kind="basic", retired=False, front="Q", back="A<br><small>s</small>"):
    fields = {"Front": front, "Back": back, "ID": id_} if kind == "basic" else {"Text": front, "Back Extra": back, "ID": id_}
    return s.Desired(id_, kind, "repo::t", ["fc", "t"], retired, fields)


def existing(id_="t-001", nt="Basic", front="Q", back="A<br><small>s</small>", queue=0):
    fields = {"Front": front, "Back": back, "Speak": "", "ID": id_} if nt == "Basic" else {"Text": front, "Back Extra": back, "ID": id_}
    return s.Existing(10, nt, [{"cardId": 20, "queue": queue, "reps": 3}], fields)


class TestRender(unittest.TestCase):
    def test_escapes_and_breaks(self):
        self.assertEqual(s.render_html("R + W > N\nnext"), "R + W &gt; N<br>next")

    def test_inline_code(self):
        self.assertEqual(s.render_html("use `a<b`"), "use <code>a&lt;b</code>")

    def test_fenced_code(self):
        out = s.render_html("Show:\n```py\nx < 1\n```\ndone")
        self.assertEqual(out, "Show:<pre><code>x &lt; 1</code></pre>done")

    def test_cloze_markup_survives(self):
        self.assertEqual(s.render_html("It is {{c1::R+W>N}}."), "It is {{c1::R+W&gt;N}}.")

    def test_leading_dashes_guarded(self):
        self.assertTrue(s.render_html("--flag").startswith("<span></span>"))

    def test_source_label(self):
        self.assertEqual(s.source_label("../../docs/a.md#Quorum sha256:abcdef123456"), "a.md#Quorum")
        self.assertEqual(s.source_label("pasted: meeting notes"), "meeting notes")


class TestPlan(unittest.TestCase):
    def test_add_when_absent(self):
        p = s.make_plan([desired()], {}, NAMES)
        self.assertEqual(len(p.adds), 1)
        self.assertFalse(p.empty)

    def test_unchanged_is_empty_plan(self):
        p = s.make_plan([desired()], {"t-001": existing()}, NAMES)
        self.assertTrue(p.empty)
        self.assertEqual(p.unchanged, 1)

    def test_update_on_field_diff_ignores_speak(self):
        p = s.make_plan([desired(back="new")], {"t-001": existing()}, NAMES)
        self.assertEqual(len(p.updates), 1)
        self.assertEqual(list(p.updates[0][2]), ["Back"])

    def test_retired_suspends_once(self):
        d = desired(retired=True)
        self.assertEqual(len(s.make_plan([d], {"t-001": existing()}, NAMES).suspends), 1)
        self.assertTrue(s.make_plan([d], {"t-001": existing(queue=-1)}, NAMES).empty)
        self.assertTrue(s.make_plan([d], {}, NAMES).empty)

    def test_orphan_reported_not_touched(self):
        p = s.make_plan([desired()], {"t-001": existing(), "gone-001": existing("gone-001")}, NAMES)
        self.assertEqual(p.orphans, ["gone-001"])
        self.assertTrue(p.empty)

    def test_kind_change_is_error(self):
        p = s.make_plan([desired(kind="cloze")], {"t-001": existing()}, NAMES)
        self.assertEqual(len(p.errors), 1)


class TestDesired(unittest.TestCase):
    def test_maps_basic_cloze_deck_and_retired(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            root = base / "deck"
            (root / "writing").mkdir(parents=True)
            (base / "docs").mkdir()
            (base / "docs" / "a.md").write_text("# A\n\n## S\n\ntext\n")
            f = root / "writing" / "a.md"
            src = fcd.source_value(f, base / "docs" / "a.md", "S")
            f.write_text(
                f"## One\n\nID: a-001\nQ: Why > x?\nA: Because.\nSource: {src}\n\n"
                f"## Two\n\nID: a-002\nC: The {{{{c1::answer}}}}.\nSource: {src}\n\n"
                f"## Three\n\nID: a-003\nQ: Old?\nA: Yes.\nSource: {src}\nRetired: 2026-11-18\n"
            )
            fcd.save_registry(root, {"version": 1, "counters": {"a": 3}})
            d = {x.id: x for x in s.desired_notes(root, "repo")}
            self.assertEqual(d["a-001"].kind, "basic")
            self.assertEqual(d["a-001"].deck, "repo::writing")
            self.assertEqual(d["a-001"].fields["Front"], "Why &gt; x?")
            self.assertIn("<small>a.md#S</small>", d["a-001"].fields["Back"])
            self.assertEqual(d["a-002"].kind, "cloze")
            self.assertEqual(d["a-002"].fields["Text"], "The {{c1::answer}}.")
            self.assertTrue(d["a-003"].retired)

    def test_nested_folders_map_to_nested_deck_and_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            root = base / "deck"
            (root / "core" / "sre").mkdir(parents=True)
            (base / "docs").mkdir()
            (base / "docs" / "a.md").write_text("# A\n\n## S\n\ntext\n")
            f = root / "core" / "sre" / "x.md"
            src = fcd.source_value(f, base / "docs" / "a.md", "S")
            f.write_text(f"## One\n\nID: a-001\nQ: Q?\nA: A.\nSource: {src}\n")
            fcd.save_registry(root, {"version": 1, "counters": {"a": 1}})
            d = {x.id: x for x in s.desired_notes(root, "anki::repo")}
            self.assertEqual(d["a-001"].deck, "anki::repo::core::sre")
            self.assertEqual(d["a-001"].tags, ["fc", "core::sre"])

    def test_x_goes_before_source_in_back_extra(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "t").mkdir()
            (root / "t" / "x.md").write_text("## A\n\nID: x-001\nC: The {{c1::a}}.\nX: why\nSource: pasted: n\n")
            fcd.save_registry(root, {"version": 1, "counters": {"x": 1}})
            d = s.desired_notes(root, "anki")[0]
            self.assertEqual(d.fields["Back Extra"], "why<br><small>n</small>")

    def test_refuses_deck_with_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "t").mkdir()
            (root / "t" / "x.md").write_text("## Bad\n\nQ: no id\n")
            with self.assertRaises(s.SyncError):
                s.desired_notes(root, "repo")


if __name__ == "__main__":
    unittest.main()
