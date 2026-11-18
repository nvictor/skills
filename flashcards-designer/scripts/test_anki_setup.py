#!/usr/bin/env python3
import unittest
from unittest import mock

import anki_setup as s

SPEC = {
    "kind": "normal",
    "fields": ["Front", "Back", "ID"],
    "templates": {"Card 1": {"front": "{{Front}}", "back": "{{Back}}"}},
    "css": ".card{}",
}
CUR = {"kind": "normal", "fields": ["Front", "Back"], "templates": {"Card 1": {"front": "{{Front}}", "back": "{{Back}}"}}, "css": ".card{}"}
OPTS = {"deck": "anki::repo", "preset_name": "Default", "shared_with_other_decks": 3,
        "config": {"new_per_day": 5, "reviews_per_day": 50, "desired_retention": 0.8,
                   "maximum_review_interval": 36500, "learn_steps": [1.0, 10.0], "relearn_steps": [10.0]}}


def fake_anki(decks, notetypes=("Basic",), cfg_new=5, cfg_id=1):
    def run(*args):
        if args[0] == "notetypes":
            return {"items": [{"name": n} for n in notetypes]}
        if args[0] == "decks":
            return {"items": decks}
        if args[0] == "deck:config":
            c = dict(OPTS["config"], new_per_day=cfg_new)
            return {"config_id": cfg_id, "config_name": "Default", "config": c}
        raise AssertionError(args)
    return run


class TestSteps(unittest.TestCase):
    def test_create_with_extra_template_and_cloze_kind(self):
        spec = dict(SPEC, templates={"A": {"front": "f", "back": "b"}, "B": {"front": "f2", "back": "b2"}})
        steps = s._steps_create("X", spec)
        self.assertEqual([st.action for st in steps], ["CREATE", "TEMPLATE+"])
        self.assertIn("--kind", steps[0].args[0])

    def test_update_detects_missing_field_template_css(self):
        spec = dict(SPEC, css=".card{x}", templates={"Card 1": {"front": "F", "back": "{{Back}}"}, "Card 2": {"front": "a", "back": "b"}})
        steps, warns = s._steps_update("Basic", spec, CUR)
        self.assertEqual([st.action for st in steps], ["FIELD+", "TEMPLATE~", "TEMPLATE+", "CSS~"])
        self.assertEqual(warns, [])

    def test_update_clean_is_empty(self):
        steps, warns = s._steps_update("Basic", dict(SPEC, fields=["Front", "Back"]), CUR)
        self.assertEqual((steps, warns), ([], []))

    def test_kind_mismatch_blocks(self):
        steps, _ = s._steps_update("Basic", dict(SPEC, kind="cloze"), CUR)
        self.assertTrue(steps[0].blocked)

    def test_field_order_warning(self):
        _, warns = s._steps_update("Basic", dict(SPEC, fields=["Back", "Front", "ID"]), CUR)
        self.assertEqual(len(warns), 1)


class TestOptions(unittest.TestCase):
    def decks(self, repo_cfg=1, others=2):
        d = [{"name": "anki::repo", "config_id": repo_cfg}] + [{"name": f"o{i}", "config_id": 1} for i in range(others)]
        return d

    def test_shared_preset_is_blocked_unless_allowed(self):
        with mock.patch.object(s, "anki", fake_anki(self.decks(), cfg_new=99)):
            blocked = s._steps_options(OPTS, allow_shared=False)
            allowed = s._steps_options(OPTS, allow_shared=True)
        self.assertTrue(blocked[0].blocked)
        self.assertFalse(allowed[0].blocked)
        self.assertEqual(allowed[0].args[0], ["deck:config:set", "--deck", "anki::repo", "--new-per-day", "5"])

    def test_own_preset_is_not_blocked(self):
        with mock.patch.object(s, "anki", fake_anki([{"name": "anki::repo", "config_id": 7}, {"name": "o", "config_id": 1}], cfg_new=99, cfg_id=7)):
            steps = s._steps_options(OPTS, allow_shared=False)
        self.assertFalse(steps[0].blocked)

    def test_no_diff_no_step(self):
        with mock.patch.object(s, "anki", fake_anki(self.decks(), cfg_new=5)):
            self.assertEqual(s._steps_options(OPTS, allow_shared=False), [])

    def test_missing_deck_is_created(self):
        with mock.patch.object(s, "anki", fake_anki([{"name": "Default", "config_id": 1}])):
            steps = s._steps_options(OPTS, allow_shared=False)
        self.assertEqual(steps[0].action, "DECK+")
        self.assertTrue(steps[1].blocked)


class TestDoctor(unittest.TestCase):
    def test_missing_cli_stops_early(self):
        with mock.patch.object(s.shutil, "which", return_value=None):
            checks = s.run_doctor(s.DEFAULT_SNAPSHOT, None, "anki::repo")
        self.assertEqual([c.level for c in checks if c.level == "FAIL"], ["FAIL"])
        self.assertIn("uv tool install anki-cli", [c.fix for c in checks][-1])

    def test_rejects_parent_outside_anki(self):
        with mock.patch.object(s.shutil, "which", return_value=None):
            checks = s.run_doctor(s.DEFAULT_SNAPSHOT, None, "repo")
        self.assertTrue(any(c.name == "parent deck" and c.level == "FAIL" for c in checks))

    def test_format_reports_problem_count(self):
        out = s.format_doctor([s.Check("FAIL", "x", "m", "do y"), s.Check("OK", "z", "fine")])
        self.assertIn("fix: do y", out)
        self.assertTrue(out.endswith("1 problem(s) to fix"))


class TestRootDeck(unittest.TestCase):
    def test_guard(self):
        from anki_sync import require_root_deck, SyncError
        require_root_deck("anki")
        require_root_deck("anki::repo")
        for bad in ("repo", "ankiX", "other::anki"):
            with self.assertRaises(SyncError):
                require_root_deck(bad)


if __name__ == "__main__":
    unittest.main()
