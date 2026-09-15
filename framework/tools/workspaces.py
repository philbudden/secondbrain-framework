#!/usr/bin/env python3
"""Lifecycle indexes and structural diagnostics for DTM project and work areas."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "projects"
WORK = ROOT / "work"

PROJECT_STATUS_ORDER = ["active", "on-hold", "completed"]
WORK_STATUS_ORDER = ["current", "parked", "reference"]
PROJECT_STATUS_LABELS = {
    "active": "Active",
    "on-hold": "On Hold",
    "completed": "Completed",
}
WORK_STATUS_LABELS = {
    "current": "Current",
    "parked": "Parked",
    "reference": "Reference",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
INDEX_ENTRY_RE = re.compile(r"^\s*-\s+\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", re.M)
NEW_REFERENCE_CHECK_FROM = "2026-07-22"


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


def value(meta: dict[str, object], field: str) -> str:
    candidate = meta.get(field, "")
    return candidate if isinstance(candidate, str) else ""


def managed_markdown_files(folder: Path) -> list[Path]:
    return sorted(
        path
        for path in folder.glob("*.md")
        if path.name.lower() not in {"readme.md", "index.md"} and path.is_file()
    )


def first_paragraph(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            text = text[end + 5 :]
    lines = text.splitlines()
    collecting: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if started:
                break
            continue
        if stripped.startswith("#") or stripped.startswith("|") or stripped.startswith("- ") or stripped.startswith(">"):
            if started:
                break
            continue
        started = True
        collecting.append(stripped)
    return " ".join(collecting).strip()


def concise_summary(text: str, limit: int = 180) -> str:
    paragraph = first_paragraph(text)
    if not paragraph:
        return "No summary yet."
    if len(paragraph) <= limit:
        return paragraph
    cut = paragraph[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:")
    return (cut or paragraph[: limit - 1]).rstrip() + "…"


def load_items(folder: Path) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for path in managed_markdown_files(folder):
        text = path.read_text(encoding="utf-8")
        meta = frontmatter(text) or {}
        items.append(
            {
                "path": path,
                "text": text,
                "meta": meta,
                "title": value(meta, "title") or path.stem.replace("-", " ").title(),
                "status": value(meta, "status"),
                "updated": value(meta, "updated"),
                "summary": concise_summary(text),
            }
        )
    return items


def render_index(title: str, intro: str, labels: dict[str, str], order: list[str], items: list[dict[str, object]]) -> str:
    grouped: dict[str, list[dict[str, object]]] = {status: [] for status in order}
    for item in items:
        status = str(item["status"])
        if status in grouped:
            grouped[status].append(item)

    lines = [f"# {title}", "", intro, ""]
    for status in order:
        section_items = sorted(grouped[status], key=lambda item: str(item["title"]).casefold())
        lines.append(f"## {labels[status]}")
        lines.append("")
        if section_items:
            for item in section_items:
                path = relative(item["path"])
                lines.append(
                    f"- [[{path.removesuffix('.md')}|{item['title']}]] — {item['summary']} `{status}` · updated {item['updated']}"
                )
        else:
            lines.append(f"<!-- No {labels[status].lower()} items. -->")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def project_index_text(items: list[dict[str, object]]) -> str:
    return render_index(
        "Projects Index",
        "Curated catalogue of DTM-managed project pages. Each project appears exactly once under its current lifecycle state so active delivery stays visible while completed or paused work remains easy to recover without dominating day-to-day navigation.",
        PROJECT_STATUS_LABELS,
        PROJECT_STATUS_ORDER,
        items,
    )


def work_index_text(items: list[dict[str, object]]) -> str:
    return render_index(
        "Work Index",
        "Curated catalogue of DTM-managed working notes. Each managed note appears exactly once under its current lifecycle state so active operational material stays easy to find while parked or retained reference notes remain available without crowding current work.",
        WORK_STATUS_LABELS,
        WORK_STATUS_ORDER,
        items,
    )


def write_indexes() -> int:
    project_items = load_items(PROJECTS)
    work_items = load_items(WORK)
    (PROJECTS / "index.md").write_text(project_index_text(project_items), encoding="utf-8")
    (WORK / "index.md").write_text(work_index_text(work_items), encoding="utf-8")
    print("Updated projects/index.md")
    print("Updated work/index.md")
    return 0


def lint() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    project_items = load_items(PROJECTS)
    work_items = load_items(WORK)

    project_names = Counter(item["path"].name for item in project_items)
    work_names = Counter(item["path"].name for item in work_items)
    for name, count in project_names.items():
        if count > 1:
            errors.append(f"duplicate project filename: {name}")
    for name, count in work_names.items():
        if count > 1:
            errors.append(f"duplicate work-note filename: {name}")

    project_index_path = PROJECTS / "index.md"
    work_index_path = WORK / "index.md"
    project_index_links: list[str] = []
    work_index_links: list[str] = []

    if project_index_path.exists():
        project_index_links = [
            target.removesuffix(".md")
            for target in INDEX_ENTRY_RE.findall(project_index_path.read_text(encoding="utf-8"))
        ]
    elif project_items:
        errors.append("projects/index.md: missing curated index")

    if work_index_path.exists():
        work_index_links = [
            target.removesuffix(".md")
            for target in INDEX_ENTRY_RE.findall(work_index_path.read_text(encoding="utf-8"))
        ]
    elif work_items:
        errors.append("work/index.md: missing curated index")

    project_targets = {
        relative(item["path"]).removesuffix(".md") for item in project_items
    }
    work_targets = {
        relative(item["path"]).removesuffix(".md") for item in work_items
    }
    for target in sorted(set(project_index_links) - project_targets):
        errors.append(f"projects/index.md: stale entry {target}")
    for target in sorted(set(work_index_links) - work_targets):
        errors.append(f"work/index.md: stale entry {target}")

    for item in project_items:
        path = item["path"]
        label = relative(path)
        meta = item["meta"]
        if not SLUG_RE.fullmatch(path.name):
            errors.append(f"{label}: filename must use lowercase kebab-case")
        if not meta:
            errors.append(f"{label}: missing or malformed frontmatter")
            continue
        missing = {"title", "type", "status", "created", "updated", "tags"} - meta.keys()
        if missing:
            errors.append(f"{label}: missing fields {', '.join(sorted(missing))}")
        if meta.get("type") != "project":
            errors.append(f"{label}: type must be 'project'")
        if item["status"] not in PROJECT_STATUS_ORDER:
            errors.append(
                f"{label}: status must be one of {', '.join(PROJECT_STATUS_ORDER)}"
            )
        for field in ("created", "updated"):
            if not DATE_RE.fullmatch(value(meta, field)):
                errors.append(f"{label}: {field} must be YYYY-MM-DD")
        target = relative(path).removesuffix(".md")
        count = project_index_links.count(target)
        if count == 0:
            errors.append(f"{label}: missing from projects/index.md")
        elif count > 1:
            errors.append(f"{label}: listed {count} times in projects/index.md")
        if item["status"] == "completed" and "## Outcome" not in item["text"]:
            warnings.append(f"{label}: completed project should keep a clear Outcome section")

    for item in work_items:
        path = item["path"]
        label = relative(path)
        meta = item["meta"]
        if not SLUG_RE.fullmatch(path.name):
            errors.append(f"{label}: filename must use lowercase kebab-case")
        if not meta:
            errors.append(f"{label}: missing or malformed frontmatter")
            continue
        missing = {"title", "type", "status", "created", "updated", "tags"} - meta.keys()
        if missing:
            errors.append(f"{label}: missing fields {', '.join(sorted(missing))}")
        if meta.get("type") != "working-note":
            errors.append(f"{label}: type must be 'working-note'")
        if item["status"] not in WORK_STATUS_ORDER:
            errors.append(f"{label}: status must be one of {', '.join(WORK_STATUS_ORDER)}")
        for field in ("created", "updated"):
            if not DATE_RE.fullmatch(value(meta, field)):
                errors.append(f"{label}: {field} must be YYYY-MM-DD")
        if (
            item["status"] == "reference"
            and value(meta, "created") == value(meta, "updated")
            and value(meta, "created") >= NEW_REFERENCE_CHECK_FROM
            and "## Retention reason" not in item["text"]
        ):
            errors.append(
                f"{label}: newly created reference work note needs a Retention reason section; use status current if it has an expected next use"
            )
        target = relative(path).removesuffix(".md")
        count = work_index_links.count(target)
        if count == 0:
            errors.append(f"{label}: missing from work/index.md")
        elif count > 1:
            errors.append(f"{label}: listed {count} times in work/index.md")

    for item in sorted(set(errors)):
        print(f"ERROR   {item}")
    for item in sorted(set(warnings)):
        print(f"WARNING {item}")
    print(
        f"Checked {len(project_items)} project note(s) and {len(work_items)} work note(s): "
        f"{len(set(errors))} error(s), {len(set(warnings))} warning(s)."
    )
    return 1 if errors else 0


def status() -> int:
    project_counts = Counter(str(item["status"]) for item in load_items(PROJECTS))
    work_counts = Counter(str(item["status"]) for item in load_items(WORK))
    for state in PROJECT_STATUS_ORDER:
        print(f"Projects {state}: {project_counts[state]}")
    for state in WORK_STATUS_ORDER:
        print(f"Work {state}: {work_counts[state]}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("lint")
    sub.add_parser("status")
    sub.add_parser("write")
    args = parser.parse_args()
    if args.command == "lint":
        return lint()
    if args.command == "status":
        return status()
    return write_indexes()


if __name__ == "__main__":
    sys.exit(main())
