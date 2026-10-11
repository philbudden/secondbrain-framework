#!/usr/bin/env python3
"""Validate SecondBrain's provider-neutral task-profile and envelope contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "contracts"
PROFILES = CONTRACTS / "task-profiles.json"
ENVELOPES = CONTRACTS / "task-envelope-contract.json"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PATH_RE = re.compile(r"^(?:[A-Za-z0-9._-]+|\*\*)(?:/(?:[A-Za-z0-9._-]+|\*\*))*$")


def load_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)}: top-level value must be an object")
    return value


def string_list(value: object, label: str, errors: list[str], *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        errors.append(f"{label}: must be a {'possibly empty ' if allow_empty else 'non-empty '}list")
        return []
    if not all(isinstance(item, str) and item.strip() for item in value):
        errors.append(f"{label}: entries must be non-empty strings")
        return []
    return list(value)


def lint_contracts() -> list[str]:
    errors: list[str] = []
    try:
        profiles, envelopes = load_json(PROFILES), load_json(ENVELOPES)
    except ValueError as exc:
        return [str(exc)]
    if profiles.get("version") != 1:
        errors.append("task-profiles.json: version must be 1")
    profile_rows = profiles.get("profiles")
    if not isinstance(profile_rows, list) or not profile_rows:
        errors.append("task-profiles.json: profiles must be a non-empty list")
        profile_rows = []
    profile_ids: set[str] = set()
    expected_profiles = {"no-llm", "routine", "balanced", "strong"}
    for row in profile_rows:
        if not isinstance(row, dict):
            errors.append("task-profiles.json: profile entries must be objects")
            continue
        profile_id = row.get("id")
        if not isinstance(profile_id, str) or not SLUG_RE.fullmatch(profile_id):
            errors.append("task-profiles.json: profile id must be lowercase kebab-case")
            continue
        if profile_id in profile_ids:
            errors.append(f"task-profiles.json: duplicate profile id {profile_id}")
        profile_ids.add(profile_id)
        for field in ("title", "description", "semantic_judgement", "context_volume", "risk_ceiling"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"task-profiles.json: {profile_id}.{field} must be a non-empty string")
        string_list(row.get("escalate_when"), f"task-profiles.json: {profile_id}.escalate_when", errors)
    if profile_ids != expected_profiles:
        errors.append("task-profiles.json: profiles must be exactly no-llm, routine, balanced, strong")

    if envelopes.get("version") != 1:
        errors.append("task-envelope-contract.json: version must be 1")
    for packet_name in ("task_packet", "completion_packet"):
        packet = envelopes.get(packet_name)
        if not isinstance(packet, dict):
            errors.append(f"task-envelope-contract.json: {packet_name} must be an object")
            continue
        string_list(packet.get("required_fields"), f"task-envelope-contract.json: {packet_name}.required_fields", errors)
    task_packet = envelopes.get("task_packet")
    if isinstance(task_packet, dict):
        for field, values in {
            "context_volume_values": {"none", "small", "bounded", "large"},
            "risk_values": {"low", "moderate", "high", "consequential"},
            "write_authority_values": {"none", "declared-paths", "dtm-session-only"},
            "return_schema_values": {"completion-packet-v1"},
        }.items():
            if set(string_list(task_packet.get(field), f"task-envelope-contract.json: task_packet.{field}", errors)) != values:
                errors.append(f"task-envelope-contract.json: task_packet.{field} must contain the declared vocabulary")
    completion_packet = envelopes.get("completion_packet")
    if isinstance(completion_packet, dict):
        if set(string_list(completion_packet.get("status_values"), "task-envelope-contract.json: completion_packet.status_values", errors)) != {"completed", "partial", "blocked", "failed"}:
            errors.append("task-envelope-contract.json: completion_packet.status_values must contain the declared vocabulary")
    return sorted(set(errors))


def validate_task(packet: dict[str, object]) -> list[str]:
    errors = lint_contracts()
    if errors:
        return errors
    profiles, envelopes = load_json(PROFILES), load_json(ENVELOPES)
    contract = envelopes["task_packet"]
    assert isinstance(contract, dict)
    for field in contract["required_fields"]:
        if field not in packet:
            errors.append(f"task packet: missing required field {field}")
    if packet.get("version") != 1:
        errors.append("task packet: version must be 1")
    task_id = packet.get("task_id")
    if not isinstance(task_id, str) or not SLUG_RE.fullmatch(task_id):
        errors.append("task packet: task_id must be lowercase kebab-case")
    profile_ids = {row["id"] for row in profiles["profiles"] if isinstance(row, dict) and isinstance(row.get("id"), str)}
    if packet.get("capability_profile") not in profile_ids:
        errors.append("task packet: capability_profile must be a declared profile")
    for field, vocabulary in (("context_volume", contract["context_volume_values"]), ("risk", contract["risk_values"]), ("write_authority", contract["write_authority_values"]), ("return_schema", contract["return_schema_values"])):
        if packet.get(field) not in vocabulary:
            errors.append(f"task packet: {field} must use the contract vocabulary")
    paths = string_list(packet.get("allowed_paths"), "task packet: allowed_paths", errors, allow_empty=True)
    for path in paths:
        if not PATH_RE.fullmatch(path) or ".." in Path(path).parts:
            errors.append(f"task packet: invalid vault-relative path {path!r}")
        if path == "daily/**" and packet.get("write_authority") != "dtm-session-only":
            errors.append("task packet: daily/** requires dtm-session-only authority")
    if packet.get("write_authority") == "none" and paths:
        errors.append("task packet: write_authority none cannot declare allowed_paths")
    for field in ("required_tools", "validation", "acceptance_criteria", "escalate_when"):
        string_list(packet.get(field), f"task packet: {field}", errors, allow_empty=True)
    return sorted(set(errors))


def validate_completion(packet: dict[str, object]) -> list[str]:
    errors = lint_contracts()
    if errors:
        return errors
    envelopes = load_json(ENVELOPES)
    contract = envelopes["completion_packet"]
    assert isinstance(contract, dict)
    for field in contract["required_fields"]:
        if field not in packet:
            errors.append(f"completion packet: missing required field {field}")
    if packet.get("version") != 1:
        errors.append("completion packet: version must be 1")
    if not isinstance(packet.get("task_id"), str) or not SLUG_RE.fullmatch(packet["task_id"]):
        errors.append("completion packet: task_id must be lowercase kebab-case")
    if packet.get("status") not in contract["status_values"]:
        errors.append("completion packet: status must use the contract vocabulary")
    for field in ("outcomes", "artifacts", "verification", "uncertainty", "blockers", "follow_up", "daily_note_implications"):
        string_list(packet.get(field), f"completion packet: {field}", errors, allow_empty=True)
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("lint")
    for name in ("validate-task", "validate-completion"):
        command = subcommands.add_parser(name)
        command.add_argument("--packet", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "lint":
        errors = lint_contracts()
    else:
        try:
            packet = load_json(args.packet)
        except ValueError as exc:
            print(f"ERROR   {exc}")
            return 1
        errors = validate_task(packet) if args.command == "validate-task" else validate_completion(packet)
    for error in errors:
        print(f"ERROR   {error}")
    print(f"Task-envelope contract: {len(errors)} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
