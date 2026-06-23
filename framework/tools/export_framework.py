#!/usr/bin/env python3
"""Build a fail-closed, sanitized SecondBrain framework export."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

LIVE_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = LIVE_ROOT / "publication" / "manifest.json"


class ExportError(RuntimeError):
    pass


def inside(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def safe_relative(value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ExportError(f"Unsafe {label}: {value}")
    return path


def load_manifest() -> dict[str, object]:
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExportError(f"Cannot read publication manifest: {exc}") from exc
    if manifest.get("version") != 1 or not isinstance(manifest.get("entries"), list):
        raise ExportError("Publication manifest must have version 1 and an entries list")
    return manifest


def assert_live_boundary() -> None:
    if (LIVE_ROOT / ".git").exists():
        raise ExportError("Refusing export: live vault contains forbidden .git metadata")
    if LIVE_ROOT.is_symlink():
        raise ExportError("Refusing export from a symlinked live root")


def denied_source(source: Path, prefixes: list[str]) -> bool:
    relative = source.relative_to(LIVE_ROOT).as_posix()
    return any(relative == prefix or relative.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def copy_entry(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise ExportError(f"Symlinks are not publishable: {source.relative_to(LIVE_ROOT)}")
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return
    if not source.is_dir():
        raise ExportError(f"Manifest source does not exist: {source.relative_to(LIVE_ROOT)}")
    for item in sorted(source.rglob("*")):
        if item.is_symlink():
            raise ExportError(f"Symlinks are not publishable: {item.relative_to(LIVE_ROOT)}")
        if item.is_file():
            target = destination / item.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def staged_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def privacy_scan(root: Path, manifest: dict[str, object]) -> None:
    failures: list[str] = []
    path_patterns = [
        re.compile(pattern) for pattern in manifest.get("forbidden_export_path_patterns", [])
    ]
    home = Path.home().resolve()
    personal_literals = {
        str(LIVE_ROOT),
        str(home),
        home.name,
    }
    email_pattern = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)

    for path in staged_files(root):
        relative = path.relative_to(root).as_posix()
        if any(pattern.search(relative) for pattern in path_patterns):
            failures.append(f"forbidden export path: {relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            failures.append(f"unexpected binary file: {relative}")
            continue
        folded = text.casefold()
        for literal in personal_literals:
            if len(literal) >= 4 and literal.casefold() in folded:
                failures.append(f"personal identifier in {relative}: {literal!r}")
        if email_pattern.search(text):
            failures.append(f"email address in {relative}")

    if failures:
        details = "\n".join(f"- {failure}" for failure in sorted(set(failures)))
        raise ExportError(f"Privacy scan failed:\n{details}")


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in staged_files(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def clear_output(output: Path) -> None:
    if output.exists():
        for child in output.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        output.mkdir(parents=True)


def export_framework(output: Path) -> str:
    assert_live_boundary()
    output = output.expanduser().resolve()
    if output in {Path("/"), Path.home().resolve()} or inside(output, LIVE_ROOT) or inside(LIVE_ROOT, output):
        raise ExportError(f"Unsafe export destination: {output}")
    if (output / ".git").exists():
        raise ExportError("Export destination is a Git checkout; stage elsewhere and publish explicitly")
    manifest = load_manifest()
    prefixes = list(manifest.get("forbidden_live_prefixes", []))
    clear_output(output)

    destinations: set[str] = set()
    for entry in manifest["entries"]:
        if not isinstance(entry, dict) or set(entry) != {"source", "destination"}:
            raise ExportError(f"Malformed manifest entry: {entry!r}")
        source_relative = safe_relative(str(entry["source"]), "source")
        destination_relative = safe_relative(str(entry["destination"]), "destination")
        source = (LIVE_ROOT / source_relative).resolve()
        if not inside(source, LIVE_ROOT):
            raise ExportError(f"Source escapes live root: {source_relative}")
        if denied_source(source, prefixes):
            raise ExportError(f"Manifest attempts to publish denied source: {source_relative}")
        destination_key = destination_relative.as_posix()
        if destination_key in destinations:
            raise ExportError(f"Duplicate manifest destination: {destination_relative}")
        destinations.add(destination_key)
        copy_entry(source, output / destination_relative)

    privacy_scan(output, manifest)
    return tree_digest(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        fingerprint = export_framework(args.output)
    except ExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Exported sanitized framework: {fingerprint[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
