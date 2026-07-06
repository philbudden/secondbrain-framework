#!/usr/bin/env python3
"""Structural diagnostics for the collaborative writing workflow."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WRITING = ROOT / "writing"
DOCUMENT_FINAL = ROOT / "documents" / "final"
STAGES = {
    "drafts": "draft",
    "ready": "ready",
    "published": "published",
}
REQUIRED = {
    "title",
    "type",
    "status",
    "created",
    "updated",
    "audience",
    "publication_target",
    "canonical_url",
    "published_at",
    "human_author",
    "ai_assistance",
    "voice_pack",
    "tags",
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
VOICE_REQUIRED = {
    "title",
    "type",
    "status",
    "created",
    "updated",
    "ready_sources",
    "published_sources",
    "document_sources",
    "tags",
}
VOICE_HEADINGS = {
    "How to use this pack",
    "Confidence and coverage",
    "Declared preferences",
    "Observed voice",
    "Avoid",
    "Context variations",
    "Drafting checklist",
    "Evidence ledger",
    "Change notes",
}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def pieces() -> list[tuple[Path, str]]:
    result: list[tuple[Path, str]] = []
    for folder, status in STAGES.items():
        result.extend((path, status) for path in sorted((WRITING / folder).glob("*.md")))
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
    warnings: list[str] = []
    all_pieces = pieces()
    names = Counter(path.name for path, _ in all_pieces)
    index_text = (WRITING / "index.md").read_text(encoding="utf-8")
    index_links = [target.removesuffix(".md") for target in LINK_RE.findall(index_text)]

    voice_path = WRITING / "voice" / "voice-pack.md"
    if not voice_path.exists():
        errors.append("writing/voice/voice-pack.md: missing voice pack")
    else:
        voice_text = voice_path.read_text(encoding="utf-8")
        voice_meta = frontmatter(voice_text)
        if voice_meta is None:
            errors.append("writing/voice/voice-pack.md: missing or malformed frontmatter")
        else:
            missing = VOICE_REQUIRED - voice_meta.keys()
            if missing:
                errors.append(
                    "writing/voice/voice-pack.md: missing fields "
                    + ", ".join(sorted(missing))
                )
            if voice_meta.get("type") != "voice-pack":
                errors.append("writing/voice/voice-pack.md: type must be 'voice-pack'")
            if voice_meta.get("status") not in {"provisional", "current"}:
                errors.append(
                    "writing/voice/voice-pack.md: status must be provisional or current"
                )
            for field in ("created", "updated"):
                if not DATE_RE.fullmatch(value(voice_meta, field)):
                    errors.append(f"writing/voice/voice-pack.md: {field} must be YYYY-MM-DD")
            actual_counts = {
                "ready_sources": sum(1 for _, status in all_pieces if status == "ready"),
                "published_sources": sum(
                    1 for _, status in all_pieces if status == "published"
                ),
                "document_sources": len(sorted(DOCUMENT_FINAL.glob("*.md"))),
            }
            for field, actual in actual_counts.items():
                recorded = value(voice_meta, field)
                if not recorded.isdigit():
                    errors.append(f"writing/voice/voice-pack.md: {field} must be an integer")
                elif int(recorded) != actual:
                    warnings.append(
                        f"writing/voice/voice-pack.md: {field}={recorded}, "
                        f"eligible corpus now has {actual}; run $voice"
                    )
        for heading in VOICE_HEADINGS:
            if not re.search(rf"^## {re.escape(heading)}\s*$", voice_text, re.M):
                errors.append(f"writing/voice/voice-pack.md: missing section {heading!r}")
        if "[[writing/drafts/" in voice_text:
            errors.append("writing/voice/voice-pack.md: evidence must never link to drafts")

    for name, count in names.items():
        if count > 1:
            errors.append(f"duplicate writing filename across stages: {name}")

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
        if meta.get("type") != "writing":
            errors.append(f"{label}: type must be 'writing'")
        if meta.get("status") != expected_status:
            errors.append(
                f"{label}: folder requires status {expected_status!r}, "
                f"found {meta.get('status')!r}"
            )
        for field in ("created", "updated"):
            if not DATE_RE.fullmatch(value(meta, field)):
                errors.append(f"{label}: {field} must be YYYY-MM-DD")
        if not value(meta, "title"):
            errors.append(f"{label}: title must not be empty")
        if expected_status in {"ready", "published"}:
            if not value(meta, "publication_target"):
                errors.append(f"{label}: {expected_status} piece needs publication_target")
            if not value(meta, "audience"):
                warnings.append(f"{label}: {expected_status} piece has no audience")
        if expected_status == "published":
            if not value(meta, "canonical_url"):
                errors.append(f"{label}: published piece needs canonical_url")
            if not value(meta, "published_at"):
                errors.append(f"{label}: published piece needs published_at")

        start_count = text.count("<!-- publish:start -->")
        end_count = text.count("<!-- publish:end -->")
        if start_count != 1 or end_count != 1:
            errors.append(f"{label}: needs exactly one publish:start and publish:end marker")
        elif text.index("<!-- publish:start -->") >= text.index("<!-- publish:end -->"):
            errors.append(f"{label}: publish markers are out of order")

        target = label.removesuffix(".md")
        count = index_links.count(target)
        if count == 0:
            errors.append(f"{label}: missing from writing/index.md")
        elif count > 1:
            errors.append(f"{label}: listed {count} times in writing/index.md")

    for item in sorted(set(errors)):
        print(f"ERROR   {item}")
    for item in sorted(set(warnings)):
        print(f"WARNING {item}")
    print(
        f"Checked {len(all_pieces)} writing piece(s): "
        f"{len(set(errors))} error(s), {len(set(warnings))} warning(s)."
    )
    return 1 if errors else 0


def status() -> int:
    counts = Counter(status for _, status in pieces())
    print(f"Drafts: {counts['draft']}")
    print(f"Ready for publishing: {counts['ready']}")
    print(f"Published: {counts['published']}")
    voice_path = WRITING / "voice" / "voice-pack.md"
    if voice_path.exists():
        meta = frontmatter(voice_path.read_text(encoding="utf-8")) or {}
        print(f"Voice pack: {meta.get('status', 'invalid')} (updated {meta.get('updated', 'unknown')})")
    else:
        print("Voice pack: missing")
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
