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
            shutil.copytree(fixture.reference_after, after)
            if mutate:
                mutate(after)
            return evaluate(fixture, observed or self.observed(name), after)

    def test_migration_fixture_references_all_pass(self):
        fixture_names = sorted(path.name for path in FIXTURES.iterdir() if path.is_dir())
        self.assertGreaterEqual(len(fixture_names), 10)
        for name in fixture_names:
            with self.subTest(fixture=name):
                self.assertEqual(self.assess(name), [])

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

    def test_required_change_and_validation_are_enforced(self):
        observed = self.observed("complete-wiki-ingest")
        observed["validations"] = []
        self.assertIn(
            "required validation did not pass: tools/wiki.py lint",
            self.assess("complete-wiki-ingest", observed),
        )

        def restore_concept(after: Path) -> None:
            after.joinpath("wiki/concepts/evidence.md").write_text("# Evidence\n\nExisting concept.\n", encoding="utf-8")

        self.assertIn(
            "required path did not change: wiki/concepts/evidence.md",
            self.assess("complete-wiki-ingest", mutate=restore_concept),
        )


if __name__ == "__main__":
    unittest.main()
