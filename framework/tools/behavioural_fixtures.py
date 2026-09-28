"""Evaluate observable outcomes for synthetic SecondBrain behavioural fixtures.

Fixtures assess paths, filesystem state, and structured events rather than the
incidental wording of a model response. A harness adapter translates its trace
into the observation dictionary evaluated here.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Fixture:
    root: Path
    data: dict[str, object]

    @property
    def initial(self) -> Path:
        return self.root / "initial"

    @property
    def reference_after(self) -> Path:
        after = self.root / "after"
        return after if after.is_dir() else self.initial


def load_fixture(root: Path) -> Fixture:
    return Fixture(root, json.loads((root / "fixture.json").read_text(encoding="utf-8")))


def normalise_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Fixture path must be relative and contained: {value}")
    return path.as_posix()


def matches(path: str, pattern: str) -> bool:
    return Path(path).match(pattern) or path == pattern.rstrip("/")


def files(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


def evaluate(fixture: Fixture, observed: dict[str, object], after: Path) -> list[str]:
    expected = fixture.data["expected"]
    assert isinstance(expected, dict)
    failures: list[str] = []
    if observed.get("outcome") != expected["outcome"]:
        failures.append(f"expected outcome {expected['outcome']!r}, got {observed.get('outcome')!r}")

    events = observed.get("events", [])
    if not isinstance(events, list):
        failures.append("events must be a list")
        events = []
    event_types = {event.get("type") for event in events if isinstance(event, dict)}
    for required in expected.get("required_events", []):
        if required not in event_types:
            failures.append(f"missing required event: {required}")

    validations = observed.get("validations", [])
    if not isinstance(validations, list):
        failures.append("validations must be a list")
        validations = []
    results = {item.get("command"): item.get("exit_code") for item in validations if isinstance(item, dict)}
    for required in expected.get("required_validations", []):
        if results.get(required) != 0:
            failures.append(f"required validation did not pass: {required}")

    for field in ("reads", "writes"):
        values = observed.get(field, [])
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            failures.append(f"{field} must be a list of relative paths")
            continue
        for value in values:
            try:
                path = normalise_path(value)
            except ValueError as exc:
                failures.append(str(exc))
                continue
            for pattern in expected.get(f"forbidden_{field}", []):
                if matches(path, pattern):
                    failures.append(f"forbidden {field[:-1]}: {path}")

    before, after_files = files(fixture.initial), files(after)
    for pattern in expected.get("immutable_paths", []):
        for path in sorted({path for path in before | after_files if matches(path, pattern)}):
            if before.get(path) != after_files.get(path):
                failures.append(f"immutable path changed: {path}")
    for required in expected.get("required_existing_paths", []):
        path = normalise_path(required)
        if path not in after_files:
            failures.append(f"required path missing: {path}")
    for required in expected.get("required_changed_paths", []):
        path = normalise_path(required)
        if before.get(path) == after_files.get(path):
            failures.append(f"required path did not change: {path}")
    for required in expected.get("required_absent_paths", []):
        path = normalise_path(required)
        if path in after_files:
            failures.append(f"required absent path exists: {path}")
    for field, required_present in (("required_file_text", True), ("forbidden_file_text", False)):
        for raw_path, snippets in expected.get(field, {}).items():
            path = normalise_path(raw_path)
            content = after_files.get(path)
            if content is None:
                failures.append(f"text-checked path missing: {path}")
                continue
            text = content.decode("utf-8", errors="replace")
            for snippet in snippets:
                if required_present and snippet not in text:
                    failures.append(f"required text missing from {path}: {snippet!r}")
                if not required_present and snippet in text:
                    failures.append(f"forbidden text found in {path}: {snippet!r}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    fixture = load_fixture(args.fixture)
    observed = json.loads(args.observed.read_text(encoding="utf-8"))
    failures = evaluate(fixture, observed, args.after)
    report = {"fixture_id": fixture.data.get("id"), "model": observed.get("model"), "harness": observed.get("harness"), "passed": not failures, "failures": failures}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
