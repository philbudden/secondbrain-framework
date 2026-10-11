from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("task_envelopes", ROOT / "tools" / "task_envelopes.py")
assert SPEC and SPEC.loader
task_envelopes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(task_envelopes)


class TaskEnvelopeContractTests(unittest.TestCase):
    def test_contracts_are_valid(self):
        self.assertEqual(task_envelopes.lint_contracts(), [])

    def test_task_packet_enforces_profile_and_daily_authority(self):
        packet = {
            "version": 1,
            "task_id": "work-index-check",
            "objective": "Check the work index.",
            "task_class": "workspace-maintenance",
            "capability_profile": "routine",
            "context_volume": "small",
            "risk": "low",
            "allowed_paths": ["work/**"],
            "write_authority": "declared-paths",
            "required_tools": ["tools/workspaces.py"],
            "validation": ["tools/workspaces.py lint"],
            "acceptance_criteria": ["The work index lint passes."],
            "escalate_when": ["The index has an unresolved structural error."],
            "return_schema": "completion-packet-v1"
        }
        self.assertEqual(task_envelopes.validate_task(packet), [])
        packet["allowed_paths"] = ["daily/**"]
        self.assertIn("task packet: daily/** requires dtm-session-only authority", task_envelopes.validate_task(packet))

    def test_completion_packet_projects_the_dtm_handoff_fields(self):
        packet = {
            "version": 1,
            "task_id": "work-index-check",
            "status": "completed",
            "outcomes": ["Work index checked."],
            "artifacts": ["work/index.md"],
            "verification": ["tools/workspaces.py lint passed."],
            "uncertainty": [],
            "blockers": [],
            "follow_up": [],
            "daily_note_implications": ["A DTM may record the completed maintenance task."]
        }
        self.assertEqual(task_envelopes.validate_completion(packet), [])


if __name__ == "__main__":
    unittest.main()
