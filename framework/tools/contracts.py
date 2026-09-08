#!/usr/bin/env python3
"""Validate machine-readable SecondBrain behavioural contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "contracts"
INVENTORY = CONTRACTS / "behaviour-inventory.json"

REQUIRED_TOP_LEVEL = {"version", "updated", "description", "behaviours"}
REQUIRED_BEHAVIOUR_FIELDS = {
    "id",
    "title",
    "owner",
    "workspaces",
    "summary",
    "current_specification",
    "current_enforcement",
    "severity",
    "portability_class",
    "prompt_debt_signals",
    "candidate_tests",
}
REQUIRED_TEST_FIELDS = {
    "id",
    "title",
    "type",
    "priority",
    "description",
    "deterministic_checks",
    "semantic_checks",
}
OWNERS = {
    "knowledge-agent",
    "dtm",
    "shared",
    "publication",
}
SEVERITIES = {"low", "medium", "high", "critical"}
PORTABILITY_CLASSES = {
    "portable-domain",
    "model-sensitive",
    "harness-sensitive",
    "harness-specific",
    "tool-api-specific",
    "mixed",
}
TEST_PRIORITIES = {"near-term", "medium-term", "future"}
TEST_TYPES = {
    "behavioural-fixture",
    "contract-lint",
    "deterministic-integration",
    "deterministic-lint",
    "deterministic-unit",
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_inventory(path: Path = INVENTORY) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{relative(path)}: {exc}") from exc


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def require_fields(value: dict[str, object], required: set[str], label: str, errors: list[str]) -> None:
    missing = required - value.keys()
    if missing:
        errors.append(f"{label}: missing fields {', '.join(sorted(missing))}")


def require_string(value: object, label: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: must be a non-empty string")
        return ""
    return value


def require_string_list(value: object, label: str, errors: list[str], *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label}: must be a list")
        return []
    if not value and not allow_empty:
        errors.append(f"{label}: must not be empty")
        return []
    result: list[str] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{label}[{index}]: must be a non-empty string")
        else:
            result.append(item)
    return result


def validate_candidate_test(value: object, behaviour_id: str, errors: list[str]) -> str:
    label = f"{behaviour_id}.candidate_tests"
    if not isinstance(value, dict):
        errors.append(f"{label}: entries must be objects")
        return ""
    require_fields(value, REQUIRED_TEST_FIELDS, label, errors)
    test_id = require_string(value.get("id"), f"{label}.id", errors)
    if test_id and not SLUG_RE.fullmatch(test_id):
        errors.append(f"{label}.{test_id}: id must use lowercase kebab-case")
    test_type = require_string(value.get("type"), f"{label}.{test_id}.type", errors)
    if test_type and test_type not in TEST_TYPES:
        errors.append(f"{label}.{test_id}: unsupported type {test_type!r}")
    priority = require_string(value.get("priority"), f"{label}.{test_id}.priority", errors)
    if priority and priority not in TEST_PRIORITIES:
        errors.append(f"{label}.{test_id}: unsupported priority {priority!r}")
    for field in ("title", "description"):
        require_string(value.get(field), f"{label}.{test_id}.{field}", errors)
    require_string_list(value.get("deterministic_checks"), f"{label}.{test_id}.deterministic_checks", errors, allow_empty=True)
    require_string_list(value.get("semantic_checks"), f"{label}.{test_id}.semantic_checks", errors, allow_empty=True)
    return test_id


def validate_inventory(data: dict[str, object]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    require_fields(data, REQUIRED_TOP_LEVEL, "behaviour-inventory.json", errors)
    if data.get("version") != 1:
        errors.append("behaviour-inventory.json: version must be 1")
    updated = require_string(data.get("updated"), "behaviour-inventory.json.updated", errors)
    if updated and not DATE_RE.fullmatch(updated):
        errors.append("behaviour-inventory.json.updated: must be YYYY-MM-DD")
    require_string(data.get("description"), "behaviour-inventory.json.description", errors)

    behaviours = data.get("behaviours")
    if not isinstance(behaviours, list) or not behaviours:
        errors.append("behaviour-inventory.json.behaviours: must be a non-empty list")
        return errors, warnings

    behaviour_ids: list[str] = []
    test_ids: list[str] = []
    for position, behaviour in enumerate(behaviours, start=1):
        label = f"behaviour {position}"
        if not isinstance(behaviour, dict):
            errors.append(f"{label}: must be an object")
            continue
        require_fields(behaviour, REQUIRED_BEHAVIOUR_FIELDS, label, errors)
        behaviour_id = require_string(behaviour.get("id"), f"{label}.id", errors)
        if behaviour_id:
            if not SLUG_RE.fullmatch(behaviour_id):
                errors.append(f"{label}: id must use lowercase kebab-case")
            behaviour_ids.append(behaviour_id)
            label = behaviour_id
        for field in ("title", "summary"):
            require_string(behaviour.get(field), f"{label}.{field}", errors)
        owner = require_string(behaviour.get("owner"), f"{label}.owner", errors)
        if owner and owner not in OWNERS:
            errors.append(f"{label}: unsupported owner {owner!r}")
        severity = require_string(behaviour.get("severity"), f"{label}.severity", errors)
        if severity and severity not in SEVERITIES:
            errors.append(f"{label}: unsupported severity {severity!r}")
        portability = require_string(behaviour.get("portability_class"), f"{label}.portability_class", errors)
        if portability and portability not in PORTABILITY_CLASSES:
            errors.append(f"{label}: unsupported portability_class {portability!r}")
        for field in ("workspaces", "current_specification", "current_enforcement", "prompt_debt_signals"):
            require_string_list(behaviour.get(field), f"{label}.{field}", errors)

        candidate_tests = behaviour.get("candidate_tests")
        if not isinstance(candidate_tests, list) or not candidate_tests:
            errors.append(f"{label}.candidate_tests: must be a non-empty list")
            continue
        for candidate in candidate_tests:
            test_id = validate_candidate_test(candidate, label, errors)
            if test_id:
                test_ids.append(test_id)

    for item, count in Counter(behaviour_ids).items():
        if count > 1:
            errors.append(f"duplicate behaviour id: {item}")
    for item, count in Counter(test_ids).items():
        if count > 1:
            errors.append(f"duplicate candidate test id: {item}")

    return sorted(set(errors)), sorted(set(warnings))


def lint() -> int:
    try:
        inventory = load_inventory()
    except ValueError as exc:
        print(f"ERROR   {exc}")
        return 1
    errors, warnings = validate_inventory(inventory)
    for item in errors:
        print(f"ERROR   {item}")
    for item in warnings:
        print(f"WARNING {item}")
    behaviours = inventory.get("behaviours", [])
    count = len(behaviours) if isinstance(behaviours, list) else 0
    print(f"Checked {count} behaviour contract(s): {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


def status() -> int:
    try:
        inventory = load_inventory()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    behaviours = inventory.get("behaviours", [])
    if not isinstance(behaviours, list):
        print("No valid behaviour inventory.")
        return 1
    by_severity = Counter(str(item.get("severity")) for item in behaviours if isinstance(item, dict))
    by_portability = Counter(str(item.get("portability_class")) for item in behaviours if isinstance(item, dict))
    print(f"Behaviour contracts: {len(behaviours)}")
    print("By severity: " + ", ".join(f"{key}={by_severity[key]}" for key in sorted(by_severity)))
    print("By portability: " + ", ".join(f"{key}={by_portability[key]}" for key in sorted(by_portability)))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("lint")
    sub.add_parser("status")
    args = parser.parse_args()
    if args.command == "lint":
        return lint()
    return status()


if __name__ == "__main__":
    sys.exit(main())
