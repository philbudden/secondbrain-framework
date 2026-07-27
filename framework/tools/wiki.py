#!/usr/bin/env python3
"""Dependency-free structural diagnostics for the LLM Wiki."""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"
SYSTEM_LOG = ROOT / "log.md"
SPECIAL = {WIKI / "index.md"}
REQUIRED = {"title", "type", "status", "created", "updated", "tags"}
VALID_TYPES = {"overview", "source", "entity", "concept", "topic", "analysis"}
VALID_STATUSES = {"current", "seed", "needs-review", "disputed", "superseded"}
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
LOG_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] ([a-z-]+) \| (.+)$", re.M)
QUESTION_STATUSES = (
    "needs-triage",
    "answer-myself",
    "research-with-dtm",
    "ready-to-integrate",
)
QUESTION_HEADINGS = {
    "open questions",
    "questions raised",
}
QUEUE_PATH = ROOT / "work" / "wiki-open-questions.md"
QUESTION_THREAD_RE = re.compile(r"<!--\s*wiki-question-thread:([a-z0-9-]+)\s*-->")
RAW_PENDING_IGNORED_NAMES = {".DS_Store", ".gitkeep", "README.md"}


def pages() -> list[Path]:
    return sorted(
        path for path in WIKI.rglob("*.md") if "_templates" not in path.parts
    )


def content_pages() -> list[Path]:
    return [path for path in pages() if path not in SPECIAL]


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def parse_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value[1:-1]
        return parsed if isinstance(parsed, str) else value[1:-1]
    return value


def read_system_log() -> str | None:
    if not SYSTEM_LOG.exists():
        return None
    return SYSTEM_LOG.read_text(encoding="utf-8")


def parse_iso_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def pending_raw_sources() -> list[Path]:
    return sorted(
        path for path in RAW.iterdir()
        if path.is_file() and path.name not in RAW_PENDING_IGNORED_NAMES
    )


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
            value = parse_scalar(re.sub(r"^\s+-\s+", "", line))
            assert isinstance(result[active_list], list)
            result[active_list].append(value)
            continue
        match = re.match(r"^([A-Za-z_][\w-]*):(?:\s*(.*))?$", line)
        if not match:
            active_list = None
            continue
        key, value = match.groups()
        if value:
            result[key] = parse_scalar(value)
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


def page_title(path: Path, text: str) -> str:
    meta = frontmatter(text) or {}
    title = meta.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    heading = re.search(r"^#\s+(.+)$", text, re.M)
    return heading.group(1).strip() if heading else path.stem.replace("-", " ").title()


def question_id(path: Path, question: str) -> str:
    key = f"{relative(path)}::{question.strip()}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]


def extract_questions(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    meta = frontmatter(text) or {}
    if meta.get("type") == "project" and meta.get("status") == "completed":
        return []
    title = page_title(path, text)
    items: list[dict[str, str]] = []
    lines = text.splitlines()
    active_heading: str | None = None
    for line in lines:
        heading_match = re.match(r"^(##)\s+(.+?)\s*$", line)
        if heading_match:
            heading = heading_match.group(2).strip().casefold()
            active_heading = heading if heading in QUESTION_HEADINGS else None
            continue
        if active_heading is None:
            continue
        if re.match(r"^#(?!#)\s+", line) or re.match(r"^###\s+", line):
            active_heading = None
            continue
        bullet = re.match(r"^-\s+(.*\S)\s*$", line)
        if not bullet:
            continue
        raw_question = bullet.group(1).strip()
        thread_match = QUESTION_THREAD_RE.search(raw_question)
        thread_id = thread_match.group(1) if thread_match else question_id(path, raw_question)
        question = QUESTION_THREAD_RE.sub("", raw_question).strip()
        items.append(
            {
                "id": question_id(path, question),
                "thread_id": thread_id,
                "question": question,
                "path": relative(path)[:-3],
                "title": title,
            }
        )
    return items


def load_question_statuses(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    statuses: dict[str, str] = {}
    pattern = re.compile(
        r"^-\s+\[[ xX]\]\s+\[([a-z-]+)\].*?<!--\s*wiki-question-(?:id|thread):([a-z0-9-]+)\s*-->$"
    )
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        status, item_id = match.groups()
        if status in QUESTION_STATUSES:
            statuses[item_id] = status
    return statuses


def format_question_item(item: dict[str, object], status: str) -> str:
    links = " · ".join(
        f"[[{source['path']}|{source['title']}]]"
        for source in item["sources"]
    )
    return (
        f"- [ ] [{status}] {item['question']} "
        f"{links} "
        f"<!-- wiki-question-thread:{item['thread_id']} -->"
    )


def queue_dates(path: Path) -> tuple[str, str]:
    created = date.today().isoformat()
    updated = created
    if path.exists():
        meta = frontmatter(path.read_text(encoding="utf-8")) or {}
        existing_created = meta.get("created")
        if isinstance(existing_created, str) and existing_created.strip():
            created = existing_created.strip()
    return created, updated


def render_question_queue(items: list[dict[str, str]], statuses: dict[str, str]) -> str:
    created, updated = queue_dates(QUEUE_PATH)
    grouped: dict[str, list[dict[str, object]]] = {status: [] for status in QUESTION_STATUSES}
    thread_groups: dict[str, dict[str, object]] = {}
    for item in sorted(items, key=lambda entry: (entry["title"].casefold(), entry["question"].casefold())):
        thread_id = item["thread_id"]
        thread = thread_groups.setdefault(
            thread_id,
            {
                "thread_id": thread_id,
                "question": item["question"],
                "sources": [],
            },
        )
        if len(item["question"]) > len(str(thread["question"])):
            thread["question"] = item["question"]
        thread["sources"].append({"path": item["path"], "title": item["title"]})

    for thread in sorted(
        thread_groups.values(),
        key=lambda entry: (str(entry["question"]).casefold(), str(entry["thread_id"])),
    ):
        status = statuses.get(str(thread["thread_id"]), "needs-triage")
        if status not in grouped:
            status = "needs-triage"
        grouped[status].append(thread)

    def section_lines(status: str, heading: str, description: str) -> list[str]:
        lines = [f"## {heading}", "", description, ""]
        if grouped[status]:
            lines.extend(format_question_item(item, status) for item in grouped[status])
        else:
            lines.append(f"<!-- No `{status}` wiki questions. -->")
        lines.append("")
        return lines

    sections: list[str] = [
        "---",
        "title: Wiki Open Questions",
        "type: working-note",
        "status: current",
        f"created: {created}",
        f"updated: {updated}",
        "tags:",
        "  - work",
        "  - wiki",
        "  - questions",
        "---",
        "",
        "# Wiki Open Questions",
        "",
        "This DTM-managed queue surfaces unresolved questions that are still present in the wiki so they can be worked separately from Daily Note open questions.",
        "",
        "Change an item's bracketed status token when triaging it, then rerun `python3 tools/wiki.py questions --write` after wiki changes so this queue stays aligned with the current wiki state.",
        "",
        "If the same underlying question appears in more than one wiki page, add the same `<!-- wiki-question-thread:your-thread-id -->` marker to each page-level bullet. The queue will then fold them into one entry with multiple source links while still expecting the answer to be integrated back into every relevant page.",
        "",
        "Status tokens:",
        "- `needs-triage` — the question exists in the wiki but has not yet been classified.",
        "- `answer-myself` — best answered directly from Philip's own judgment or point of view.",
        "- `research-with-dtm` — needs additional research or synthesis with the DTM.",
        "- `ready-to-integrate` — an answer exists and now needs to be folded back into the wiki.",
        "",
    ]
    sections.extend(
        section_lines(
            "needs-triage",
            "Needs triage",
            "Newly surfaced or not yet classified.",
        )
    )
    sections.extend(
        section_lines(
            "answer-myself",
            "Answer myself",
            "Questions where the user's own view is a valid primary answer.",
        )
    )
    sections.extend(
        section_lines(
            "research-with-dtm",
            "Research with DTM",
            "Questions that need evidence gathering, synthesis, or structured follow-up.",
        )
    )
    sections.extend(
        section_lines(
            "ready-to-integrate",
            "Ready to integrate",
            "Questions that appear answered and now need the wiki updated to reflect that answer.",
        )
    )
    return "\n".join(sections).rstrip() + "\n"


def questions(write: bool) -> int:
    items: list[dict[str, str]] = []
    for path in content_pages():
        if path == WIKI / "index.md":
            continue
        items.extend(extract_questions(path))
    statuses = load_question_statuses(QUEUE_PATH)
    output = render_question_queue(items, statuses)
    if write:
        QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        QUEUE_PATH.write_text(output, encoding="utf-8")
        print(f"Wrote {relative(QUEUE_PATH)} with {len(items)} active wiki question(s).")
        return 0
    print(output, end="")
    return 0


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
    wiki_updated_dates: set[date] = set()
    source_ingests: list[tuple[str, str, date]] = []

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
            updated_at = parse_iso_date(meta.get("updated"))
            if updated_at is None:
                errors.append(f"{relative(path)}: invalid updated date {meta.get('updated')!r}")
            else:
                wiki_updated_dates.add(updated_at)
            if meta.get("type") == "source":
                for field in ("source_path", "source_kind", "ingested"):
                    if not meta.get(field):
                        errors.append(f"{relative(path)}: source missing {field}")
                source_path = meta.get("source_path")
                if isinstance(source_path, str) and not (ROOT / source_path).exists():
                    errors.append(
                        f"{relative(path)}: source_path does not exist: {source_path}"
                    )
                ingested_at = parse_iso_date(meta.get("ingested"))
                if ingested_at is None:
                    errors.append(f"{relative(path)}: invalid ingested date {meta.get('ingested')!r}")
                elif isinstance(meta.get("title"), str) and meta["title"].strip():
                    source_ingests.append((relative(path), meta["title"].strip(), ingested_at))

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

    log_text = read_system_log()
    if log_text is None:
        errors.append("log.md: missing root system log; create log.md with at least one parseable entry")
    elif not LOG_RE.search(log_text):
        errors.append("log.md: no parseable log entries")
    else:
        log_entries = [
            (date.fromisoformat(entry_date), operation, title.strip())
            for entry_date, operation, title in LOG_RE.findall(log_text)
        ]
        for previous, current in zip(log_entries, log_entries[1:]):
            previous_date, previous_operation, previous_title = previous
            current_date, current_operation, current_title = current
            if current_date < previous_date:
                errors.append(
                    "log.md: entries are out of chronological order; "
                    f"{current_date.isoformat()} {current_operation} | {current_title} "
                    "appears after "
                    f"{previous_date.isoformat()} {previous_operation} | {previous_title}"
                )
        log_entry_blocks: list[tuple[date, str, str, str]] = []
        matches = list(LOG_RE.finditer(log_text))
        for index, match in enumerate(matches):
            body_start = match.end()
            body_end = matches[index + 1].start() if index + 1 < len(matches) else len(log_text)
            entry_date, operation, title = match.groups()
            log_entry_blocks.append(
                (
                    date.fromisoformat(entry_date),
                    operation,
                    title.strip(),
                    log_text[body_start:body_end],
                )
            )
        log_dates = {entry_date for entry_date, _, _ in log_entries}
        logged_source_entries = {
            (entry_date, title.casefold())
            for entry_date, operation, title in log_entries
            if operation in {"ingest", "dtm", "query", "lint"}
        }
        for updated_at in sorted(wiki_updated_dates):
            if updated_at not in log_dates:
                errors.append(
                    "log.md: missing log entry for wiki content updated on "
                    f"{updated_at.isoformat()}"
                )
        for source_path, source_title, ingested_at in source_ingests:
            source_key = source_path[:-3]
            has_matching_entry = (ingested_at, source_title.casefold()) in logged_source_entries
            if not has_matching_entry:
                has_matching_entry = any(
                    entry_date == ingested_at
                    and operation in {"ingest", "dtm", "query", "lint"}
                    and f"[[{source_key}" in body
                    for entry_date, operation, _, body in log_entry_blocks
                )
            if not has_matching_entry:
                errors.append(
                    f"log.md: missing source-specific entry for {source_path} "
                    f"on {ingested_at.isoformat()} titled {source_title!r}"
                )

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
    pending = pending_raw_sources()
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
    sources = pending_raw_sources()
    if not sources:
        print("No pending raw sources.")
        return 0
    for path in sources:
        print(relative(path))
    return 0


def recent(limit: int) -> int:
    log_text = read_system_log()
    if log_text is None:
        print(
            "ERROR: missing root system log at log.md; create the file before using `wiki.py recent`.",
            file=sys.stderr,
        )
        return 1
    entries = LOG_RE.findall(log_text)
    for date, operation, title in entries[-limit:]:
        print(f"{date}  {operation:<7}  {title}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("lint", help="check structure, metadata, links, index, and log")
    sub.add_parser("status", help="summarize raw files and wiki pages")
    sub.add_parser("pending", help="list top-level raw sources awaiting ingest")
    questions_parser = sub.add_parser("questions", help="show or write the wiki open-question queue")
    questions_parser.add_argument("--write", action="store_true", help="write the queue to work/wiki-open-questions.md")
    recent_parser = sub.add_parser("recent", help="show recent log entries")
    recent_parser.add_argument("count", nargs="?", type=int, default=5)
    args = parser.parse_args()
    if args.command == "lint":
        return lint()
    if args.command == "status":
        return status()
    if args.command == "pending":
        return pending()
    if args.command == "questions":
        return questions(args.write)
    return recent(max(0, args.count))


if __name__ == "__main__":
    sys.exit(main())
