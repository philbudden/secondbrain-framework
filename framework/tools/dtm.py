#!/usr/bin/env python3
"""Daily Note lifecycle and structural checks for the Digital TeamMate."""

from __future__ import annotations

import argparse
import calendar
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAILY = ROOT / "daily"
RECURRENCE = ROOT / "dtm" / "recurring-tasks.json"

SECTIONS = [
    "Previous Day",
    "Focus",
    "Personal To-Do",
    "Professional To-Do",
    "Schedule & Recurring",
    "Notes & Activity",
    "Decisions",
    "References",
    "Open Questions",
]
AREA_SECTION = {
    "personal": "Personal To-Do",
    "professional": "Professional To-Do",
    "schedule": "Schedule & Recurring",
}
TASK_RE = re.compile(r"^- \[ \] .+$", re.M)
QUESTION_RE = re.compile(r"^- (?!\[[ xX]\] )(?!<!--)(.+)$", re.M)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid ISO date: {value}") from exc


def note_path(day: date) -> Path:
    return DAILY / f"{day.isoformat()}.md"


def read_note(day: date) -> str | None:
    path = note_path(day)
    return path.read_text(encoding="utf-8") if path.exists() else None


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)",
        text,
        flags=re.M | re.S,
    )
    return match.group(1).strip() if match else ""


def incomplete_tasks(text: str, heading: str) -> list[str]:
    return TASK_RE.findall(section(text, heading))


def open_questions(text: str) -> list[str]:
    return [f"- {item.strip()}" for item in QUESTION_RE.findall(section(text, "Open Questions"))]


def load_recurrence() -> dict[str, object]:
    return json.loads(RECURRENCE.read_text(encoding="utf-8"))


def applies(rule: dict[str, object], day: date) -> bool:
    if not rule.get("enabled", False):
        return False
    schedule = rule.get("schedule", {})
    if not isinstance(schedule, dict):
        return False
    frequency = schedule.get("frequency")
    if frequency == "daily":
        return True
    if frequency == "weekly":
        weekdays = schedule.get("weekdays", [])
        return isinstance(weekdays, list) and day.strftime("%A") in weekdays
    if frequency == "monthly":
        configured = schedule.get("day")
        if configured == "last":
            return day.day == calendar.monthrange(day.year, day.month)[1]
        return isinstance(configured, int) and day.day == configured
    return False


def recurrence_instances(day: date) -> dict[str, list[str]]:
    result = {heading: [] for heading in AREA_SECTION.values()}
    for rule in load_recurrence().get("tasks", []):
        if not isinstance(rule, dict) or not applies(rule, day):
            continue
        area = rule.get("area")
        if area not in AREA_SECTION:
            continue
        result[AREA_SECTION[str(area)]].append(
            f'- [ ] {rule["task"]} <!-- recurring:{rule["id"]} -->'
        )
    return result


def unique(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        key = re.sub(r"\s*<!-- recurring:[^>]+ -->\s*$", "", line).casefold()
        if key not in seen:
            seen.add(key)
            result.append(line)
    return result


def block(lines: list[str], empty_hint: str | None = None) -> str:
    if lines:
        return "\n".join(lines)
    return f"<!-- {empty_hint} -->" if empty_hint else ""


def render_note(day: date, previous_text: str | None) -> str:
    previous_day = day - timedelta(days=1)
    recurrence = recurrence_instances(day)
    personal: list[str] = []
    professional: list[str] = []
    schedule: list[str] = []
    questions: list[str] = []

    if previous_text:
        personal = incomplete_tasks(previous_text, "Personal To-Do")
        professional = incomplete_tasks(previous_text, "Professional To-Do")
        schedule = incomplete_tasks(previous_text, "Schedule & Recurring")
        questions = open_questions(previous_text)

    personal = unique(personal + recurrence["Personal To-Do"])
    professional = unique(professional + recurrence["Professional To-Do"])
    schedule = unique(schedule + recurrence["Schedule & Recurring"])
    previous_link = (
        f"[[daily/{previous_day.isoformat()}|{previous_day.isoformat()}]]"
        if previous_text
        else "No Daily Note exists for the previous calendar day."
    )
    focus = (
        "1. Review and prioritise carried work, active projects, and open questions.\n"
        "<!-- DTM: replace this with a concise, evidence-based focus recommendation. -->"
        if previous_text
        else "1. Establish today's priorities and active workstreams."
    )
    previous_summary = (
        f"Previous note: {previous_link}\n\n"
        "<!-- DTM: replace this comment with a concise synthesis of the previous day. -->"
        if previous_text
        else previous_link
    )
    now = datetime.now().strftime("%H:%M")

    return f"""---
title: Daily Note — {day.isoformat()}
type: daily-note
date: {day.isoformat()}
status: open
previous: {f'"{previous_link}"' if previous_text else ''}
next:
tags:
  - daily-note
  - dtm
---

# {day.strftime('%A, %d %B %Y').replace(' 0', ' ')}

## Previous Day

{previous_summary}

## Focus

{focus}

## Personal To-Do

{block(personal, 'No carried personal tasks.')}

## Professional To-Do

{block(professional, 'No carried professional tasks.')}

## Schedule & Recurring

{block(schedule, 'No scheduled or recurring tasks apply today.')}

## Notes & Activity

- {now} — DTM — Opened the day and carried forward active work.

## Decisions

<!-- Meaningful decisions use DEC-YYYY-MM-DD-NN records. -->

## References

<!-- List only documents created or updated by the DTM today. -->

## Open Questions

{block(questions, 'No active open questions.')}
"""


def replace_frontmatter_value(text: str, field: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(field)}:.*$", re.M)
    replacement = f"{field}: {value}"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    end = text.find("\n---\n", 4)
    if end < 0:
        return text
    return text[:end] + f"\n{replacement}" + text[end:]


def close_day(day: date, next_day: date | None = None) -> bool:
    path = note_path(day)
    if not path.exists():
        print(f"No Daily Note to close: {path.relative_to(ROOT)}")
        return False
    text = path.read_text(encoding="utf-8")
    changed = replace_frontmatter_value(text, "status", "closed")
    if next_day:
        changed = replace_frontmatter_value(
            changed, "next", f'"[[daily/{next_day.isoformat()}|{next_day.isoformat()}]]"'
        )
    if changed != text:
        path.write_text(changed, encoding="utf-8")
        print(f"Closed {path.relative_to(ROOT)}")
    else:
        print(f"Already closed {path.relative_to(ROOT)}")
    return True


def open_day(day: date) -> bool:
    path = note_path(day)
    if path.exists():
        print(f"Already open/present: {path.relative_to(ROOT)}")
        return False
    previous_text = read_note(day - timedelta(days=1))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_note(day, previous_text), encoding="utf-8")
    print(f"Created {path.relative_to(ROOT)}")
    return True


def rollover(day: date) -> int:
    previous_day = day - timedelta(days=1)
    close_day(previous_day, day)
    open_day(day)
    return 0


def validate_recurrence() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        config = load_recurrence()
    except (OSError, json.JSONDecodeError) as exc:
        return [f"dtm/recurring-tasks.json: {exc}"], warnings
    if config.get("version") != 1 or not isinstance(config.get("tasks"), list):
        errors.append("dtm/recurring-tasks.json: expected version 1 and a tasks list")
        return errors, warnings
    ids: set[str] = set()
    weekdays = set(calendar.day_name)
    for position, rule in enumerate(config["tasks"], start=1):
        label = f"recurrence rule {position}"
        if not isinstance(rule, dict):
            errors.append(f"{label}: must be an object")
            continue
        for field in ("id", "task", "area", "enabled", "schedule"):
            if field not in rule:
                errors.append(f"{label}: missing {field}")
        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not re.fullmatch(r"[a-z0-9-]+", rule_id):
            errors.append(f"{label}: id must use lowercase kebab-case")
        elif rule_id in ids:
            errors.append(f"{label}: duplicate id {rule_id}")
        else:
            ids.add(rule_id)
        if rule.get("area") not in AREA_SECTION:
            errors.append(f"{label}: invalid area {rule.get('area')!r}")
        if not isinstance(rule.get("enabled"), bool):
            errors.append(f"{label}: enabled must be true or false")
        schedule = rule.get("schedule")
        if not isinstance(schedule, dict):
            errors.append(f"{label}: schedule must be an object")
            continue
        frequency = schedule.get("frequency")
        if frequency not in {"daily", "weekly", "monthly"}:
            errors.append(f"{label}: unsupported frequency {frequency!r}")
        if frequency == "weekly":
            values = schedule.get("weekdays")
            if not isinstance(values, list) or not values or any(v not in weekdays for v in values):
                errors.append(f"{label}: weekly schedule needs valid weekday names")
        if frequency == "monthly":
            value = schedule.get("day")
            if value != "last" and (not isinstance(value, int) or not 1 <= value <= 31):
                errors.append(f"{label}: monthly day must be 1..31 or 'last'")
            elif isinstance(value, int) and value > 28:
                warnings.append(f"{label}: will not occur in months without day {value}")
    return errors, warnings


def lint() -> int:
    errors, warnings = validate_recurrence()
    note_files = sorted(path for path in DAILY.glob("*.md") if path.name != "README.md")
    for path in note_files:
        if not DATE_RE.fullmatch(path.stem):
            warnings.append(f"{path.relative_to(ROOT)}: filename is not an ISO date")
            continue
        text = path.read_text(encoding="utf-8")
        for heading in SECTIONS:
            count = len(re.findall(rf"^## {re.escape(heading)}\s*$", text, re.M))
            if count != 1:
                errors.append(
                    f"{path.relative_to(ROOT)}: section {heading!r} occurs {count} times"
                )
        positions = [text.find(f"## {heading}") for heading in SECTIONS]
        if all(position >= 0 for position in positions) and positions != sorted(positions):
            errors.append(f"{path.relative_to(ROOT)}: required sections are out of order")
        for field in ("type: daily-note", f"date: {path.stem}", "status:"):
            if field not in text[: text.find("\n---\n", 4) + 5]:
                errors.append(f"{path.relative_to(ROOT)}: missing frontmatter value {field}")

    for item in sorted(set(errors)):
        print(f"ERROR   {item}")
    for item in sorted(set(warnings)):
        print(f"WARNING {item}")
    print(
        f"Checked {len(note_files)} Daily Note(s): "
        f"{len(set(errors))} error(s), {len(set(warnings))} warning(s)."
    )
    return 1 if errors else 0


def status() -> int:
    notes = sorted(DAILY.glob("*.md"))
    if not notes:
        print("No Daily Notes.")
        return 0
    latest = notes[-1]
    text = latest.read_text(encoding="utf-8")
    task_count = sum(
        len(incomplete_tasks(text, heading))
        for heading in ("Personal To-Do", "Professional To-Do", "Schedule & Recurring")
    )
    question_count = len(open_questions(text))
    status_match = re.search(r"^status:\s*(\S+)", text, re.M)
    current_status = status_match.group(1) if status_match else "unknown"
    enabled = sum(1 for rule in load_recurrence().get("tasks", []) if rule.get("enabled"))
    print(f"Latest note: {latest.stem} ({current_status})")
    print(f"Outstanding tasks: {task_count}")
    print(f"Open questions: {question_count}")
    print(f"Enabled recurrence rules: {enabled}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("open", "close", "rollover"):
        command_parser = sub.add_parser(command)
        command_parser.add_argument("--date", type=parse_date, default=date.today())
    sub.add_parser("lint")
    sub.add_parser("status")
    args = parser.parse_args()
    if args.command == "open":
        open_day(args.date)
        return 0
    if args.command == "close":
        close_day(args.date)
        return 0
    if args.command == "rollover":
        return rollover(args.date)
    if args.command == "lint":
        return lint()
    return status()


if __name__ == "__main__":
    sys.exit(main())
