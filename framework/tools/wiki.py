#!/usr/bin/env python3
"""Dependency-free structural diagnostics for the LLM Wiki."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"
SPECIAL = {WIKI / "index.md", WIKI / "log.md"}
REQUIRED = {"title", "type", "status", "created", "updated", "tags"}
VALID_TYPES = {"overview", "source", "entity", "concept", "topic", "analysis"}
VALID_STATUSES = {"current", "seed", "needs-review", "disputed", "superseded"}
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
LOG_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] ([a-z-]+) \| (.+)$", re.M)


def pages() -> list[Path]:
    return sorted(
        path for path in WIKI.rglob("*.md") if "_templates" not in path.parts
    )


def content_pages() -> list[Path]:
    return [path for path in pages() if path not in SPECIAL]


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


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


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip().replace("\\", "/")
    return target[:-3] if target.endswith(".md") else target


def target_exists(target: str, known: set[str]) -> bool:
    normalized = normalize_target(target)
    if normalized in known:
        return True
    path = ROOT / target
    if path.exists() or path.with_suffix(".md").exists():
        return True
    if "/" not in normalized:
        return sum(item.rsplit("/", 1)[-1] == normalized for item in known) == 1
    return False


def collect_links(path: Path) -> list[str]:
    return LINK_RE.findall(path.read_text(encoding="utf-8"))


def lint() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    all_pages = pages()
    contents = content_pages()
    known = {relative(path)[:-3] for path in all_pages}
    known.update(
        relative(path)[:-3] if path.suffix == ".md" else relative(path)
        for path in RAW.rglob("*") if path.is_file()
    )
    titles: list[str] = []
    inbound: Counter[str] = Counter()

    for path in contents:
        text = path.read_text(encoding="utf-8")
        meta = frontmatter(text)
        if meta is None:
            errors.append(f"{relative(path)}: missing or malformed frontmatter")
        else:
            missing = REQUIRED - meta.keys()
            if missing:
                errors.append(
                    f"{relative(path)}: missing fields {', '.join(sorted(missing))}"
                )
            if meta.get("type") not in VALID_TYPES:
                errors.append(f"{relative(path)}: invalid type {meta.get('type')!r}")
            if meta.get("status") not in VALID_STATUSES:
                errors.append(f"{relative(path)}: invalid status {meta.get('status')!r}")
            if meta.get("title"):
                titles.append(str(meta["title"]).casefold())
            if meta.get("type") == "source":
                for field in ("source_path", "source_kind", "ingested"):
                    if not meta.get(field):
                        errors.append(f"{relative(path)}: source missing {field}")
                source_path = meta.get("source_path")
                if isinstance(source_path, str) and not (ROOT / source_path).exists():
                    errors.append(
                        f"{relative(path)}: source_path does not exist: {source_path}"
                    )

        for target in LINK_RE.findall(text):
            normalized = normalize_target(target)
            if not target_exists(target, known):
                errors.append(f"{relative(path)}: broken link [[{target}]]")
            if normalized in known:
                inbound[normalized] += 1

    duplicates = [title for title, count in Counter(titles).items() if count > 1]
    for title in duplicates:
        warnings.append(f"duplicate page title: {title}")

    index_text = (WIKI / "index.md").read_text(encoding="utf-8")
    index_links = [normalize_target(link) for link in LINK_RE.findall(index_text)]
    for path in contents:
        key = relative(path)[:-3]
        count = sum(link == key for link in index_links)
        if count == 0:
            errors.append(f"{relative(path)}: missing from wiki/index.md")
        elif count > 1:
            errors.append(f"{relative(path)}: listed {count} times in wiki/index.md")
        if path != WIKI / "overview.md" and inbound[key] == 0:
            warnings.append(f"{relative(path)}: orphan page (no inbound wiki links)")

    for path in all_pages:
        for target in collect_links(path):
            if not target_exists(target, known):
                errors.append(f"{relative(path)}: broken link [[{target}]]")

    log_text = (WIKI / "log.md").read_text(encoding="utf-8")
    if not LOG_RE.search(log_text):
        errors.append("wiki/log.md: no parseable log entries")

    errors = sorted(set(errors))
    warnings = sorted(set(warnings))
    for item in errors:
        print(f"ERROR   {item}")
    for item in warnings:
        print(f"WARNING {item}")
    print(
        f"Checked {len(contents)} content pages: "
        f"{len(errors)} error(s), {len(warnings)} warning(s)."
    )
    return 1 if errors else 0


def status() -> int:
    counts: Counter[str] = Counter()
    states: Counter[str] = Counter()
    for path in content_pages():
        meta = frontmatter(path.read_text(encoding="utf-8")) or {}
        counts[str(meta.get("type", "unknown"))] += 1
        states[str(meta.get("status", "unknown"))] += 1
    pending = sorted(
        path for path in RAW.iterdir()
        if path.is_file() and path.name not in {".gitkeep", "README.md"}
    )
    processed = sum(
        1 for path in (RAW / "processed").rglob("*")
        if path.is_file() and path.name not in {".gitkeep", "README.md"}
    )
    print(f"Pending raw sources: {len(pending)}")
    print(f"Processed raw sources: {processed}")
    print(f"Wiki pages: {sum(counts.values())}")
    print("By type: " + (", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "none"))
    print("By status: " + (", ".join(f"{k}={v}" for k, v in sorted(states.items())) or "none"))
    return 0


def pending() -> int:
    sources = sorted(
        path for path in RAW.iterdir()
        if path.is_file() and path.name not in {".gitkeep", "README.md"}
    )
    if not sources:
        print("No pending raw sources.")
        return 0
    for path in sources:
        print(relative(path))
    return 0


def recent(limit: int) -> int:
    entries = LOG_RE.findall((WIKI / "log.md").read_text(encoding="utf-8"))
    for date, operation, title in entries[-limit:]:
        print(f"{date}  {operation:<7}  {title}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("lint", help="check structure, metadata, links, index, and log")
    sub.add_parser("status", help="summarize raw files and wiki pages")
    sub.add_parser("pending", help="list top-level raw sources awaiting ingest")
    recent_parser = sub.add_parser("recent", help="show recent log entries")
    recent_parser.add_argument("count", nargs="?", type=int, default=5)
    args = parser.parse_args()
    if args.command == "lint":
        return lint()
    if args.command == "status":
        return status()
    if args.command == "pending":
        return pending()
    return recent(max(0, args.count))


if __name__ == "__main__":
    sys.exit(main())
