from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dtm_module():
    path = ROOT / "framework" / "tools" / "dtm.py"
    spec = importlib.util.spec_from_file_location("secondbrain_dtm", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ObsidianConfigurationTests(unittest.TestCase):
    def test_templates_and_daily_notes_match_installed_layout(self):
        obsidian = ROOT / "framework" / "obsidian"
        templates = json.loads((obsidian / "templates.json").read_text())
        daily = json.loads((obsidian / "daily-notes.json").read_text())

        self.assertEqual(templates["folder"], "templates")
        self.assertEqual(daily["folder"], "daily")
        self.assertEqual(daily["format"], "YYYY-MM-DD")
        self.assertEqual(daily["template"], "templates/daily-note")


class SkillPackagingTests(unittest.TestCase):
    def test_dtm_skill_is_explicit_and_thread_scoped(self):
        skill = ROOT / "framework" / "skills" / "dtm"
        instructions = (skill / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("name: dtm", instructions)
        self.assertIn("thread-scoped", instructions)
        self.assertIn("$end-dtm", instructions)
        self.assertIn("allow_implicit_invocation: false", metadata)


class RecurrenceSafetyTests(unittest.TestCase):
    def test_invalid_rule_fails_before_rollover_mutates_notes(self):
        dtm = load_dtm_module()
        today = date(2030, 1, 2)
        yesterday = today - timedelta(days=1)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            daily = root / "daily"
            daily.mkdir()
            previous = daily / f"{yesterday.isoformat()}.md"
            previous.write_text("---\nstatus: open\n---\n", encoding="utf-8")
            recurrence = root / "recurring-tasks.json"
            recurrence.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "tasks": [
                            {
                                "id": "missing-task",
                                "area": "personal",
                                "enabled": True,
                                "schedule": {"frequency": "daily"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            dtm.DAILY = daily
            dtm.RECURRENCE = recurrence

            with self.assertRaises(dtm.DTMError):
                dtm.rollover(today)

            self.assertIn("status: open", previous.read_text(encoding="utf-8"))
            self.assertFalse((daily / f"{today.isoformat()}.md").exists())


if __name__ == "__main__":
    unittest.main()
