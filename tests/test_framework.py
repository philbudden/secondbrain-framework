from __future__ import annotations

import importlib.util
import json
import re
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


def load_contracts_module():
    path = ROOT / "framework" / "tools" / "contracts.py"
    spec = importlib.util.spec_from_file_location("secondbrain_contracts", path)
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


class ChangelogTests(unittest.TestCase):
    def test_keep_a_changelog_sections_are_nested_under_dates(self):
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        current_section = None
        dated_section = re.compile(r"^## \[\d{4}-\d{2}-\d{2}\]$")
        keep_a_changelog_heading = re.compile(
            r"^### (Added|Changed|Deprecated|Removed|Fixed|Security)$"
        )

        for line_number, line in enumerate(changelog.splitlines(), start=1):
            if line.startswith("## "):
                current_section = line
            if keep_a_changelog_heading.match(line):
                self.assertIsNotNone(current_section, f"{line} at line {line_number} has no parent section")
                self.assertRegex(
                    current_section,
                    dated_section,
                    f"{line} at line {line_number} must be nested under ## [YYYY-MM-DD], not {current_section}",
                )


class BehaviourContractTests(unittest.TestCase):
    def test_behaviour_inventory_is_valid_and_covers_core_boundaries(self):
        contracts = load_contracts_module()
        inventory = json.loads(
            (ROOT / "framework" / "contracts" / "behaviour-inventory.json").read_text(encoding="utf-8")
        )
        errors, warnings = contracts.validate_inventory(inventory)
        behaviours = {item["id"]: item for item in inventory["behaviours"]}

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertIn("role-routing", behaviours)
        self.assertIn("raw-source-lifecycle", behaviours)
        self.assertIn("publication-privacy-boundary", behaviours)
        self.assertIn("harness-adapters", behaviours)
        self.assertEqual(behaviours["publication-privacy-boundary"]["severity"], "critical")


class SkillPackagingTests(unittest.TestCase):
    def test_dtm_skill_is_explicit_and_thread_scoped(self):
        skill = ROOT / "framework" / "skills" / "dtm"
        instructions = (skill / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("name: dtm", instructions)
        self.assertIn("thread-scoped", instructions)
        self.assertIn("DTM YYYY-MM-DD", instructions)
        self.assertIn("Daily Note write authority", instructions)
        self.assertIn("$end-dtm", instructions)
        self.assertIn("allow_implicit_invocation: false", metadata)

    def test_dtm_handoff_skill_targets_active_dtm_thread(self):
        skill = ROOT / "framework" / "skills" / "dtm-handoff"
        instructions = (skill / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("name: dtm-handoff", instructions)
        self.assertIn("DTM YYYY-MM-DD", instructions)
        self.assertIn("Do not create, edit, append to, reorder, or otherwise modify `daily/`", instructions)
        self.assertIn("send_message_to_thread", instructions)
        self.assertIn("Incremental checkpoint", instructions)
        self.assertIn("DTM Hand-Off", metadata)

    def test_voice_skill_excludes_drafts_and_is_explicit(self):
        skill = ROOT / "framework" / "skills" / "voice"
        instructions = (skill / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
        normalized = " ".join(instructions.split())

        self.assertIn("writing/ready/", instructions)
        self.assertIn("writing/published/", instructions)
        self.assertIn(
            "Do not list, search, count, or read files under `writing/drafts/` or `documents/drafts/`.",
            normalized,
        )
        self.assertIn("writing/drafts/", instructions)
        self.assertIn("allow_implicit_invocation: false", metadata)

    def test_markdown_to_pdf_skill_points_to_managed_command(self):
        skill = ROOT / "framework" / "skills" / "markdown-to-pdf"
        instructions = (skill / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("name: markdown-to-pdf", instructions)
        self.assertIn("tools/document_deliverables.py pdf", instructions)
        self.assertIn("Mermaid", instructions)
        self.assertIn("allow_implicit_invocation: false", metadata)

    def test_resolve_document_items_skill_is_non_adversarial_and_explicit(self):
        skill = ROOT / "framework" / "skills" / "resolve-document-items"
        instructions = (skill / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("name: resolve-document-items", instructions)
        self.assertIn("Ask exactly one primary question at a time.", instructions)
        self.assertIn("not idea exploration, red-team review, or Socratic challenge", instructions)
        self.assertIn("Update the source document", instructions)
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

    def test_rollover_does_not_carry_incomplete_recurring_schedule_items_to_non_applicable_days(self):
        dtm = load_dtm_module()
        saturday = date(2030, 1, 5)
        friday = saturday - timedelta(days=1)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            daily = root / "daily"
            daily.mkdir()
            previous = daily / f"{friday.isoformat()}.md"
            previous.write_text(
                "\n".join(
                    [
                        "---",
                        f"title: Daily Note — {friday.isoformat()}",
                        "type: daily-note",
                        f"date: {friday.isoformat()}",
                        "status: open",
                        "---",
                        "",
                        "## Previous Day",
                        "",
                        "Previous note: [[daily/2029-01-03|2029-01-03]]",
                        "",
                        "## Focus",
                        "",
                        "1. Finish Friday work.",
                        "",
                        "## Blockers",
                        "",
                        "<!-- none -->",
                        "",
                        "## Personal To-Do",
                        "",
                        "<!-- none -->",
                        "",
                        "## Professional To-Do",
                        "",
                        "<!-- none -->",
                        "",
                        "## Schedule & Recurring",
                        "",
                        "- [ ] Weekday recurring item <!-- recurring:weekday-rule -->",
                        "- [ ] One-off carryable schedule item",
                        "",
                        "## Notes & Activity",
                        "",
                        "- 17:00 — DTM — Wrapped up Friday.",
                        "",
                        "## Decisions",
                        "",
                        "<!-- none -->",
                        "",
                        "## References",
                        "",
                        "<!-- none -->",
                        "",
                        "## Open Questions",
                        "",
                        "<!-- none -->",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            recurrence = root / "recurring-tasks.json"
            recurrence.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "tasks": [
                            {
                                "id": "weekday-rule",
                                "task": "Weekday recurring item",
                                "area": "schedule",
                                "enabled": True,
                                "schedule": {
                                    "frequency": "weekly",
                                    "weekdays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            dtm.DAILY = daily
            dtm.RECURRENCE = recurrence

            dtm.rollover(saturday)

            created = (daily / f"{saturday.isoformat()}.md").read_text(encoding="utf-8")
            self.assertIn("- [ ] One-off carryable schedule item", created)
            self.assertNotIn("weekday-rule", created)
            self.assertIn(
                "## Schedule & Recurring\n\n- [ ] One-off carryable schedule item",
                created,
            )


if __name__ == "__main__":
    unittest.main()
