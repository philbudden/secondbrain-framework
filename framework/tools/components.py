#!/usr/bin/env python3
"""Validate proposed component and installed-state contracts without installing anything."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
REVISION = re.compile(r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")
HASH = re.compile(r"^[a-f0-9]{64}$")
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
START = "<!-- secondbrain:capabilities:start -->"
END = "<!-- secondbrain:capabilities:end -->"
RESERVED = {".git", "scratch.md"}
MANIFEST_KEYS = {"schema_version", "id", "requires", "files", "workspace", "contributions", "prerequisites"}
CONTRIBUTION_KEYS = {"navigation", "instructions", "skills", "validators", "configuration", "automations", "permission_claims"}


def object_fields(value: object, required: set[str], label: str, errors: list[str]) -> dict:
    if not isinstance(value, dict):
        errors.append(f"{label}: expected object")
        return {}
    missing = required - value.keys()
    extra = value.keys() - required
    if missing:
        errors.append(f"{label}: missing {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"{label}: unknown {', '.join(sorted(extra))}")
    return value


def array(value: object, label: str, errors: list[str]) -> list:
    if not isinstance(value, list):
        errors.append(f"{label}: expected array")
        return []
    return value


def identifier(value: object, label: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        errors.append(f"{label}: invalid component/contribution identifier")
        return ""
    return value


def path(value: object, label: str, errors: list[str], *, source_root: Path | None = None) -> str:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or any(ord(character) < 32 for character in value):
        errors.append(f"{label}: invalid relative POSIX path")
        return ""
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts) or any(part.casefold() in RESERVED for part in parts) or value.startswith("/"):
        errors.append(f"{label}: unsafe or reserved path")
        return ""
    if source_root is not None:
        current = source_root
        for part in parts:
            current = current / part
            if current.is_symlink():
                errors.append(f"{label}: symlink in source path")
                return ""
    return value


def duplicates(values: list[str], label: str, errors: list[str]) -> None:
    for value, count in Counter(item.casefold() for item in values if item).items():
        if count > 1:
            errors.append(f"{label}: duplicate or case-insensitive collision: {value}")


def validate_manifest(data: object, *, source_root: Path | None = None, target_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    item = object_fields(data, MANIFEST_KEYS, "manifest", errors)
    if item.get("schema_version") != 1:
        errors.append("manifest: schema_version must be 1")
    component = identifier(item.get("id"), "manifest.id", errors)
    requires = [identifier(x, "requires", errors) for x in array(item.get("requires"), "requires", errors)]
    duplicates(requires, "requires", errors)
    if component == "core" and requires:
        errors.append("core must not require another component")
    if component and component != "core" and "core" not in requires:
        errors.append(f"{component}: core dependency is required")
    if component in {"writing", "documents"} and requires != ["core"]:
        errors.append(f"{component}: optional public capability may require only core")
    if component and component in requires:
        errors.append(f"{component}: self dependency")

    targets: list[str] = []
    own_targets: set[str] = set()
    for group, entries in (("files", item.get("files")), ("workspace.seeds", (item.get("workspace") or {}).get("seeds") if isinstance(item.get("workspace"), dict) else None)):
        for i, raw in enumerate(array(entries, group, errors)):
            label = f"{group}[{i}]"
            mapping = object_fields(raw, {"source", "target", "ownership"}, label, errors)
            source = path(mapping.get("source"), f"{label}.source", errors, source_root=source_root)
            target = path(mapping.get("target"), f"{label}.target", errors, source_root=target_root)
            allowed = {"seed-user"} if group == "workspace.seeds" else {"managed", "seed-user"}
            if mapping.get("ownership") not in allowed:
                errors.append(f"{label}: invalid ownership")
            if target and target.split("/", 1)[0] in {"raw", "daily"}:
                errors.append(f"{label}: installer may not own raw or Daily Note content")
            if target:
                targets.append(target)
                own_targets.add(target)
            if source and source.split("/", 1)[0] == "private" and component in {"core", "writing", "documents"}:
                errors.append(f"{label}: public component references private source")
    workspace = object_fields(item.get("workspace"), {"directories", "seeds"}, "workspace", errors)
    directories = [path(x, "workspace.directories", errors, source_root=target_root) for x in array(workspace.get("directories"), "workspace.directories", errors)]
    duplicates(directories, "workspace.directories", errors)
    duplicates(targets, "destinations", errors)
    for directory in directories:
        if directory and any(directory.casefold() == target.casefold() for target in targets):
            errors.append(f"workspace directory conflicts with file: {directory}")
    for target in targets:
        if any(target.casefold().startswith(other.casefold() + "/") for other in targets if other != target):
            errors.append(f"file destination is nested beneath another file: {target}")

    contributions = object_fields(item.get("contributions"), CONTRIBUTION_KEYS, "contributions", errors)
    navigation_ids: list[str] = []
    for i, raw in enumerate(array(contributions.get("navigation"), "navigation", errors)):
        label = f"navigation[{i}]"
        entry = object_fields(raw, {"id", "label", "target"}, label, errors)
        navigation_ids.append(identifier(entry.get("id"), f"{label}.id", errors))
        if not isinstance(entry.get("label"), str) or not entry["label"].strip() or "\n" in entry["label"] or "[[" in entry["label"] or "<!--" in entry["label"]:
            errors.append(f"{label}: invalid label")
        target = path(entry.get("target"), f"{label}.target", errors)
        if target and target not in own_targets and not any(target.startswith(d + "/") for d in directories if d):
            errors.append(f"{label}: target is not an owned file or workspace path")
    duplicates(navigation_ids, "navigation ids", errors)
    for group in ("instructions", "configuration"):
        values = [path(x, group, errors) for x in array(contributions.get(group), group, errors)]
        duplicates(values, group, errors)
        for value in values:
            if value and value not in own_targets:
                errors.append(f"{group}: undeclared owned target {value}")
    skill_ids: list[str] = []
    for i, raw in enumerate(array(contributions.get("skills"), "skills", errors)):
        entry = object_fields(raw, {"id", "path"}, f"skills[{i}]", errors)
        skill_ids.append(identifier(entry.get("id"), "skills.id", errors))
        target = path(entry.get("path"), "skills.path", errors)
        if target and target not in own_targets:
            errors.append(f"skills: undeclared owned target {target}")
    duplicates(skill_ids, "skill ids", errors)
    for i, raw in enumerate(array(contributions.get("validators"), "validators", errors)):
        entry = object_fields(raw, {"tool", "args"}, f"validators[{i}]", errors)
        target = path(entry.get("tool"), "validators.tool", errors)
        if target and target not in own_targets:
            errors.append(f"validators: undeclared owned target {target}")
        for arg in array(entry.get("args"), "validators.args", errors):
            if not isinstance(arg, str) or not arg or "\x00" in arg or "\n" in arg:
                errors.append("validators.args: invalid argument")
    for i, raw in enumerate(array(contributions.get("automations"), "automations", errors)):
        entry = object_fields(raw, {"path", "activation"}, f"automations[{i}]", errors)
        target = path(entry.get("path"), "automations.path", errors)
        if target and target not in own_targets:
            errors.append(f"automations: undeclared owned target {target}")
        if entry.get("activation") != "manual":
            errors.append("automations: activation must be manual")
    claims: list[str] = []
    for i, raw in enumerate(array(contributions.get("permission_claims"), "permission_claims", errors)):
        label = f"permission_claims[{i}]"
        entry = object_fields(raw, {"path", "access"}, label, errors)
        scope = path(entry.get("path"), f"{label}.path", errors)
        if entry.get("access") not in {"read", "write"}:
            errors.append(f"{label}: invalid access")
        if scope and scope not in own_targets and scope not in directories:
            errors.append(f"{label}: scope is not an owned file or workspace directory")
        if scope and isinstance(entry.get("access"), str):
            claims.append(scope + "#" + entry["access"])
    duplicates(claims, "permission claims", errors)
    for i, raw in enumerate(array(item.get("prerequisites"), "prerequisites", errors)):
        entry = object_fields(raw, {"kind", "name"}, f"prerequisites[{i}]", errors)
        if entry.get("kind") not in {"executable", "python-module"} or not isinstance(entry.get("name"), str) or not NAME.fullmatch(entry["name"]):
            errors.append(f"prerequisites[{i}]: invalid prerequisite")
    return sorted(set(errors))


def validate_bundle(manifests: list[object], public_components: set[str]) -> list[str]:
    errors: list[str] = []
    by_id: dict[str, dict] = {}
    targets: dict[str, str] = {}
    navigation: dict[str, str] = {}
    directories: dict[str, str] = {}
    for manifest in manifests:
        errors.extend(validate_manifest(manifest))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("id"), str):
            continue
        cid = manifest["id"]
        if cid in by_id:
            errors.append(f"duplicate component id: {cid}")
        by_id[cid] = manifest
        mappings = manifest.get("files", []) + manifest.get("workspace", {}).get("seeds", []) if isinstance(manifest.get("files"), list) and isinstance(manifest.get("workspace"), dict) and isinstance(manifest.get("workspace", {}).get("seeds"), list) else []
        for mapping in mappings:
            if not isinstance(mapping, dict) or not isinstance(mapping.get("target"), str):
                continue
            target = mapping["target"].casefold()
            if target in targets:
                errors.append(f"duplicate destination ownership: {mapping['target']} ({targets[target]}, {cid})")
            targets[target] = cid
            source = mapping.get("source")
            if cid in public_components and isinstance(source, str) and source.split("/", 1)[0].casefold() in {"private", "secrets"}:
                errors.append(f"{cid}: public component references private source {source}")
        for directory in manifest.get("workspace", {}).get("directories", []) if isinstance(manifest.get("workspace"), dict) else []:
            if isinstance(directory, str):
                key = directory.casefold()
                if key in directories:
                    errors.append(f"duplicate workspace directory ownership: {directory}")
                directories[key] = cid
        for entry in manifest.get("contributions", {}).get("navigation", []) if isinstance(manifest.get("contributions"), dict) else []:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                key = entry["id"].casefold()
                if key in navigation:
                    errors.append(f"duplicate navigation id: {entry['id']}")
                navigation[key] = cid
    if "core" not in by_id:
        errors.append("bundle: core component missing")
    if "core" not in public_components or not public_components <= by_id.keys():
        errors.append("public allowlist: must contain core and only declared components")
    for cid, manifest in by_id.items():
        for requirement in manifest.get("requires", []) if isinstance(manifest.get("requires"), list) else []:
            if requirement not in by_id:
                errors.append(f"{cid}: missing dependency {requirement}")
            if cid in public_components and requirement not in public_components:
                errors.append(f"{cid}: public component depends on non-public {requirement}")
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(cid: str) -> None:
        if cid in visiting:
            errors.append(f"dependency cycle involving {cid}")
            return
        if cid in visited or cid not in by_id:
            return
        visiting.add(cid)
        for requirement in by_id[cid].get("requires", []):
            if isinstance(requirement, str):
                visit(requirement)
        visiting.remove(cid)
        visited.add(cid)
    for cid in by_id:
        visit(cid)
    return sorted(set(errors))


def validate_navigation_region(text: str) -> list[str]:
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if START in line]
    ends = [i for i, line in enumerate(lines) if END in line]
    errors = []
    if len(starts) != 1 or len(ends) != 1:
        errors.append("navigation region requires exactly one start and end marker")
    if starts and ends and starts[0] >= ends[0]:
        errors.append("navigation markers are reversed or nested")
    for i in starts + ends:
        if lines[i] not in {START, END}:
            errors.append("navigation markers must occupy whole lines")
    return sorted(set(errors))


def validate_state(data: object, manifests: list[object]) -> list[str]:
    errors: list[str] = []
    state = object_fields(data, {"schema_version", "installed_components", "resources"}, "installed-state", errors)
    if state.get("schema_version") != 1:
        errors.append("installed-state: schema_version must be 1")
    known = {m.get("id"): m for m in manifests if isinstance(m, dict)}
    installed: dict[str, str] = {}
    for i, raw in enumerate(array(state.get("installed_components"), "installed_components", errors)):
        entry = object_fields(raw, {"id", "source_revision"}, f"installed_components[{i}]", errors)
        cid = identifier(entry.get("id"), "installed_components.id", errors)
        revision = entry.get("source_revision")
        if not isinstance(revision, str) or not REVISION.fullmatch(revision):
            errors.append(f"installed_components[{i}]: source_revision must be an exact hash")
        if cid in installed:
            errors.append(f"installed_components: duplicate {cid}")
        if cid:
            installed[cid] = revision if isinstance(revision, str) else ""
        if cid not in known:
            errors.append(f"installed_components: unknown component {cid}")
    if "core" not in installed:
        errors.append("installed_components: core required")
    for cid in installed:
        for requirement in known.get(cid, {}).get("requires", []):
            if requirement not in installed:
                errors.append(f"installed_components: missing dependency {requirement} for {cid}")
    keys: list[str] = []
    for i, raw in enumerate(array(state.get("resources"), "resources", errors)):
        label = f"resources[{i}]"
        if not isinstance(raw, dict):
            errors.append(f"{label}: expected object")
            continue
        allowed = {"path", "component", "ownership", "source_revision", "source", "initial_sha256", "last_managed_sha256", "region_id", "renderer_version"}
        if raw.keys() - allowed:
            errors.append(f"{label}: unknown fields")
        target = path(raw.get("path"), f"{label}.path", errors)
        cid = identifier(raw.get("component"), f"{label}.component", errors)
        ownership = raw.get("ownership")
        if ownership not in {"managed", "seed-user", "generated-file", "generated-region", "user-data"}:
            errors.append(f"{label}: invalid ownership")
        if cid not in installed:
            errors.append(f"{label}: component is not installed")
        if raw.get("source_revision") != installed.get(cid):
            errors.append(f"{label}: source_revision differs from installed component")
        if ownership in {"managed", "seed-user"} and isinstance(known.get(cid), dict):
            manifest = known[cid]
            declared = [*manifest.get("files", []), *manifest.get("workspace", {}).get("seeds", [])]
            source = path(raw.get("source"), f"{label}.source", errors)
            if not any(isinstance(mapping, dict) and mapping.get("source") == source and mapping.get("target") == target and mapping.get("ownership") == ownership for mapping in declared):
                errors.append(f"{label}: source mapping is not declared by its component manifest")
        elif "source" in raw:
            errors.append(f"{label}: source is only valid for managed or seed-user resources")
        if ownership in {"managed", "generated-file", "generated-region"}:
            if not isinstance(raw.get("last_managed_sha256"), str) or not HASH.fullmatch(raw["last_managed_sha256"]):
                errors.append(f"{label}: last_managed_sha256 required")
        if ownership == "seed-user":
            if not isinstance(raw.get("initial_sha256"), str) or not HASH.fullmatch(raw["initial_sha256"]):
                errors.append(f"{label}: initial_sha256 required for seed-user")
        if ownership == "user-data" and ("initial_sha256" in raw or "last_managed_sha256" in raw):
            errors.append(f"{label}: user-data must not carry managed hashes")
        region = raw.get("region_id")
        if ownership == "generated-region":
            if cid != "core" or not isinstance(region, str) or not ID.fullmatch(region) or not isinstance(raw.get("renderer_version"), int) or raw["renderer_version"] < 1:
                errors.append(f"{label}: generated region needs core owner, id and renderer version")
        elif "region_id" in raw or "renderer_version" in raw:
            errors.append(f"{label}: region fields only valid for generated-region")
        if target:
            keys.append((target + "#" + region if ownership == "generated-region" and isinstance(region, str) else target).casefold())
    duplicates(keys, "state resource paths", errors)
    return sorted(set(errors))


def harness_inventory(state: dict, manifests: list[dict]) -> dict:
    """Produce declarative metadata for a harness from the installed set only.

    This does not register skills or grant any claimed permission.
    """
    by_id = {manifest["id"]: manifest for manifest in manifests}
    installed = sorted(entry["id"] for entry in state["installed_components"])
    instructions: list[dict] = []
    skills: list[dict] = []
    claims: list[dict] = []
    for cid in installed:
        contributions = by_id[cid]["contributions"]
        instructions.extend({"component": cid, "path": item} for item in contributions["instructions"])
        skills.extend({"component": cid, **item} for item in contributions["skills"])
        claims.extend({"component": cid, **item} for item in contributions["permission_claims"])
    return {"schema_version": 1, "installed_components": installed, "instructions": instructions, "skills": skills, "permission_claims": claims}


def validate_harness_inventory(data: object, state: dict, manifests: list[dict]) -> list[str]:
    """Reject metadata that differs from the validated installed component set."""
    if not isinstance(data, dict) or data != harness_inventory(state, manifests):
        return ["harness inventory differs from installed component declarations"]
    return []


def validate_ownership_inventory() -> tuple[list[str], int]:
    """Check that the Stage 1 rules classify every allowlisted publication file."""
    errors: list[str] = []
    manifest = json.loads((ROOT / "publication" / "manifest.json").read_text(encoding="utf-8"))
    inventory = json.loads((ROOT / "contracts" / "resource-ownership.json").read_text(encoding="utf-8"))
    entries = manifest["entries"]
    rules = inventory["rules"]
    overrides = inventory["overrides"]
    sources = [entry["source"] for entry in entries]
    if inventory.get("version") != 1:
        errors.append("resource ownership inventory version must be 1")
    if Counter(rule.get("source") for rule in rules) != Counter(sources):
        errors.append("resource ownership rules must match publication manifest sources exactly")
    for item in [*rules, *overrides]:
        if item.get("owner") not in {"core", "writing", "documents", "distribution", "unresolved"}:
            errors.append(f"resource ownership: invalid owner for {item.get('source')}")
        if item.get("lifecycle") not in {"managed", "seed-user", "development"}:
            errors.append(f"resource ownership: invalid lifecycle for {item.get('source')}")
        source = item.get("source")
        if not isinstance(source, str) or not (ROOT / source).exists():
            errors.append(f"resource ownership: missing source {source}")
        if item in overrides and not any(source == base or source.startswith(base + "/") for base in sources):
            errors.append(f"resource ownership: override outside allowlist {source}")
    rule_by_source = {item["source"]: item for item in rules if isinstance(item.get("source"), str)}
    files = 0
    for entry in entries:
        source = ROOT / entry["source"]
        paths = [source] if source.is_file() else [item for item in source.rglob("*") if item.is_file() and item.name != ".DS_Store" and "__pycache__" not in item.parts]
        for actual in paths:
            files += 1
            relative = actual.relative_to(ROOT).as_posix()
            candidates = [item for item in overrides if isinstance(item.get("source"), str) and (relative == item["source"] or relative.startswith(item["source"] + "/"))]
            owner = max(candidates, key=lambda item: len(item["source"])) if candidates else rule_by_source.get(entry["source"])
            if owner is None:
                errors.append(f"resource ownership: unclassified {relative}")
    return sorted(set(errors)), files


def lint() -> int:
    fixture = ROOT / "contracts" / "component-examples.json"
    try:
        data = json.loads(fixture.read_text(encoding="utf-8"))
        for name in ("component-manifest.schema.json", "installed-state.schema.json", "harness-inventory.schema.json"):
            json.loads((ROOT / "contracts" / name).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERROR   component contracts: {exc}")
        return 1
    errors = validate_bundle(data["manifests"], set(data["public_components"]))
    errors.extend(validate_state(data["state"], data["manifests"]))
    errors.extend(validate_harness_inventory(harness_inventory(data["state"], data["manifests"]), data["state"], data["manifests"]))
    errors.extend(validate_navigation_region(data["navigation_region"]))
    file_count = 0
    if (ROOT / "publication" / "manifest.json").exists():
        inventory_errors, file_count = validate_ownership_inventory()
        errors.extend(inventory_errors)
    for error in sorted(set(errors)):
        print(f"ERROR   {error}")
    inventory_result = f", {file_count} inventoried export file(s)" if file_count else ""
    print(f"Component contracts: {len(data['manifests'])} manifest(s){inventory_result}, {len(errors)} error(s).")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["lint"])
    args = parser.parse_args()
    return lint() if args.command == "lint" else 2


if __name__ == "__main__":
    sys.exit(main())
