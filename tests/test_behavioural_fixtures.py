from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

from behavioural_fixtures import evaluate, load_fixture  # noqa: E402


FIXTURES = ROOT / "tests" / "fixtures" / "behavioural"


class BehaviouralFixtureTests(unittest.TestCase):
    def fixture(self, name: str):
        return load_fixture(FIXTURES / name)

    def observed(self, name: str) -> dict[str, object]:
        return json.loads((FIXTURES / name / "observed-pass.json").read_text(encoding="utf-8"))

    def assess(self, name: str, observed: dict[str, object] | None = None, mutate=None) -> list[str]:
        fixture = self.fixture(name)
        with tempfile.TemporaryDirectory() as temporary:
            after = Path(temporary) / "vault"
            shutil.copytree(fixture.initial, after)
            if mutate:
                mutate(after)
            return evaluate(fixture, observed or self.observed(name), after)

    def test_non_dtm_daily_note_write_fixture_accepts_handoff_and_rejects_note_changes(self):
        self.assertEqual(self.assess("non-dtm-daily-note-write-refusal"), [])

        def write_daily(after: Path) -> None:
            note = after / "daily" / "2030-01-02.md"
            note.write_text(note.read_text(encoding="utf-8") + "\n- Unsafe capture\n", encoding="utf-8")

        self.assertIn("immutable path changed: daily/2030-01-02.md", self.assess("non-dtm-daily-note-write-refusal", mutate=write_daily))

    def test_voice_draft_exclusion_fixture_rejects_draft_reads(self):
        self.assertEqual(self.assess("voice-draft-exclusion"), [])
        observed = self.observed("voice-draft-exclusion")
        observed["reads"].append("writing/drafts/tempting-unpublished-draft.md")
        self.assertIn("forbidden read: writing/drafts/tempting-unpublished-draft.md", self.assess("voice-draft-exclusion", observed))

    def test_raw_archive_collision_fixture_rejects_overwrite_or_move(self):
        self.assertEqual(self.assess("raw-archive-collision"), [])

        def overwrite_processed(after: Path) -> None:
            (after / "raw" / "processed" / "source.md").write_text("replacement", encoding="utf-8")

        self.assertIn("immutable path changed: raw/processed/source.md", self.assess("raw-archive-collision", mutate=overwrite_processed))

        def move_pending(after: Path) -> None:
            (after / "raw" / "source.md").rename(after / "raw" / "processed" / "source-copy.md")

        self.assertIn("immutable path changed: raw/source.md", self.assess("raw-archive-collision", mutate=move_pending))


if __name__ == "__main__":
    unittest.main()
