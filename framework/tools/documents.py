#!/usr/bin/env python3
"""Structural diagnostics for the collaborative internal-documents workflow."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS = ROOT / "documents"
DELIVERABLES = DOCUMENTS / "deliverables"
REFERENCE = DOCUMENTS / "reference"
STAGES = {
    "drafts": "draft",
    "final": "final",
}
DECK_REQUIRED = {
    "marp",
    "type",
    "status",
    "created",
    "updated",
    "title",
    "author",
    "human_author",
    "ai_assistance",
    "voice_pack",
    "tags",
}
REQUIRED = {
    "title",
    "type",
    "status",
    "created",
    "updated",
    "audience",
    "human_author",
    "ai_assistance",
    "voice_pack",
    "tags",
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
DECK_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.marp\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
INDEX_ENTRY_RE = re.compile(r"^\s*-\s+\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", re.M)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def pieces() -> list[tuple[Path, str]]:
    result: list[tuple[Path, str]] = []
    for folder, status in STAGES.items():
        result.extend((path, status) for path in sorted((DOCUMENTS / folder).glob("*.md")))
    return result


def deck_sources() -> list[tuple[Path, str]]:
    result: list[tuple[Path, str]] = []
    for folder, status in STAGES.items():
        result.extend((path, status) for path in sorted((DOCUMENTS / folder).glob("*/*.marp.md")))
    return result


def frontmatter(text: str) -> dict[str, object] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    result: dict[str, object] = {}
    active_list: str | None = None
    for line in text[4:end].splitlines():
        if re.match(r"^\s+-\s+", line) and active_list:
            value = re.sub(r"^\s+-\s+", "", line).strip().strip('"\'')
            assert isinstance(result[active_list], list)
            result[active_list].append(value)
            continue
        match = re.match(r"^([A-Za-z_][\w-]*):(?:\s*(.*))?$", line)
        if not match:
            active_list = None
            continue
        key, value = match.groups()
        if value:
            result[key] = value.strip().strip('"\'')
            active_list = None
        else:
            result[key] = []
            active_list = key
    return result


def value(meta: dict[str, object], field: str) -> str:
    candidate = meta.get(field, "")
    return candidate if isinstance(candidate, str) else ""


def lint() -> int:
    errors: list[str] = []
    all_pieces = pieces()
    all_decks = deck_sources()
    names = Counter(path.name for path, _ in [*all_pieces, *all_decks])
    deliverable_files = sorted(
        path
        for path in DELIVERABLES.rglob("*")
        if path.is_file() and path.name.lower() != "readme.md" and not path.name.startswith(".")
    )
    reference_files = sorted(
        path
        for path in REFERENCE.rglob("*")
        if path.is_file() and path.name.lower() != "readme.md" and not path.name.startswith(".")
    )
    index_path = DOCUMENTS / "index.md"
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8")
        index_links = [target.removesuffix(".md") for target in INDEX_ENTRY_RE.findall(index_text)]
    else:
        index_text = ""
        index_links = []
        if all_pieces or all_decks or deliverable_files or reference_files:
            errors.append(
                "documents/index.md: missing curated index; create documents/index.md before managing documents, references, or deliverables"
            )

    for name, count in names.items():
        if count > 1:
            errors.append(f"duplicate document filename across stages: {name}")

    for path, expected_status in all_decks:
        label = relative(path)
        text = path.read_text(encoding="utf-8")
        meta = frontmatter(text)
        if not DECK_SLUG_RE.fullmatch(path.name):
            errors.append(f"{label}: deck filename must use lowercase kebab-case ending .marp.md")
        if meta is None:
            errors.append(f"{label}: missing or malformed frontmatter")
            continue
        missing = DECK_REQUIRED - meta.keys()
        if missing:
            errors.append(f"{label}: missing fields {', '.join(sorted(missing))}")
        if str(meta.get("marp", "")).lower() != "true":
            errors.append(f"{label}: marp must be true")
        if meta.get("type") != "deck":
            errors.append(f"{label}: type must be 'deck'")
        if meta.get("status") != expected_status:
            errors.append(
                f"{label}: folder requires status {expected_status!r}, found {meta.get('status')!r}"
            )
        for field in ("created", "updated"):
            if not DATE_RE.fullmatch(value(meta, field)):
                errors.append(f"{label}: {field} must be YYYY-MM-DD")
        if not value(meta, "title"):
            errors.append(f"{label}: title must not be empty")
        if not value(meta, "voice_pack"):
            errors.append(f"{label}: voice_pack must not be empty")
        target = label.removesuffix(".md")
        count = index_links.count(target)
        if count == 0:
            errors.append(f"{label}: missing from documents/index.md")
        elif count > 1:
            errors.append(f"{label}: listed {count} times in documents/index.md")

    for path, expected_status in all_pieces:
        label = relative(path)
        text = path.read_text(encoding="utf-8")
        meta = frontmatter(text)
        if not SLUG_RE.fullmatch(path.name):
            errors.append(f"{label}: filename must use lowercase kebab-case")
        if meta is None:
            errors.append(f"{label}: missing or malformed frontmatter")
            continue
        missing = REQUIRED - meta.keys()
        if missing:
            errors.append(f"{label}: missing fields {', '.join(sorted(missing))}")
        if meta.get("type") != "document":
            errors.append(f"{label}: type must be 'document'")
        if meta.get("status") != expected_status:
            errors.append(
                f"{label}: folder requires status {expected_status!r}, found {meta.get('status')!r}"
            )
        for field in ("created", "updated"):
            if not DATE_RE.fullmatch(value(meta, field)):
                errors.append(f"{label}: {field} must be YYYY-MM-DD")
        if not value(meta, "title"):
            errors.append(f"{label}: title must not be empty")
        if not value(meta, "voice_pack"):
            errors.append(f"{label}: voice_pack must not be empty")
        target = label.removesuffix(".md")
        count = index_links.count(target)
        if count == 0:
            errors.append(f"{label}: missing from documents/index.md")
        elif count > 1:
            errors.append(f"{label}: listed {count} times in documents/index.md")

    if DELIVERABLES.exists():
        for path in deliverable_files:
            if " " in path.name:
                errors.append(
                    f"{relative(path)}: managed deliverable filenames must use kebab-case without spaces"
                )
            count = index_links.count(relative(path))
            if count == 0:
                errors.append(f"{relative(path)}: missing from documents/index.md")
            elif count > 1:
                errors.append(f"{relative(path)}: listed {count} times in documents/index.md")

    if REFERENCE.exists():
        for path in reference_files:
            count = index_links.count(relative(path))
            if count == 0:
                errors.append(f"{relative(path)}: missing from documents/index.md")
            elif count > 1:
                errors.append(f"{relative(path)}: listed {count} times in documents/index.md")

    for item in sorted(set(errors)):
        print(f"ERROR   {item}")
    print(
        f"Checked {len(all_pieces)} document(s) and {len(all_decks)} deck source(s): {len(set(errors))} error(s), 0 warning(s)."
    )
    return 1 if errors else 0


def status() -> int:
    counts = Counter(status for _, status in pieces())
    deck_counts = Counter(status for _, status in deck_sources())
    print(f"Drafts: {counts['draft']}")
    print(f"Final: {counts['final']}")
    print(f"Draft decks: {deck_counts['draft']}")
    print(f"Final decks: {deck_counts['final']}")
    reference_count = sum(
        1
        for path in REFERENCE.rglob("*")
        if path.is_file()
        and path.name.lower() != "readme.md"
        and not path.name.startswith(".")
    )
    print(f"Reference: {reference_count}")
    deliverable_count = sum(
        1
        for path in DELIVERABLES.rglob("*")
        if path.is_file()
        and path.name.lower() != "readme.md"
        and not path.name.startswith(".")
    )
    print(f"Deliverables: {deliverable_count}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("lint")
    sub.add_parser("status")
    args = parser.parse_args()
    return lint() if args.command == "lint" else status()


if __name__ == "__main__":
    sys.exit(main())
