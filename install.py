#!/usr/bin/env python3
"""Install SecondBrain framework files into an Obsidian vault without Git."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
FRAMEWORK = REPO / "framework"
EXAMPLE = REPO / "examples" / "empty-vault"


def files_under(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            yield path


def copy_file(source: Path, destination: Path, force: bool, dry_run: bool) -> str:
    if destination.exists() and not force:
        return f"preserve {destination}"
    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return f"{'would write' if dry_run else 'wrote'} {destination}"


def install(vault: Path, force: bool, dry_run: bool) -> int:
    vault = vault.expanduser().resolve()
    if vault == REPO or REPO in vault.parents:
        print("Refusing to install inside the framework repository.", file=sys.stderr)
        return 2
    mappings = [
        (FRAMEWORK / "AGENTS.md", vault / "AGENTS.md"),
        (FRAMEWORK / "DTM.md", vault / "DTM.md"),
    ]
    for folder, target in (
        (FRAMEWORK / "templates", vault / "templates"),
        (FRAMEWORK / "tools", vault / "tools"),
        (FRAMEWORK / "obsidian", vault / ".obsidian"),
        (FRAMEWORK / "defaults" / "dtm", vault / "dtm"),
        (FRAMEWORK / "automation-definitions", vault / "automation-definitions"),
        (FRAMEWORK / "skills", vault / "skills"),
        (EXAMPLE, vault),
    ):
        for source in files_under(folder):
            mappings.append((source, target / source.relative_to(folder)))
    for source, destination in mappings:
        print(copy_file(source, destination, force, dry_run))
    print("Installation preview complete." if dry_run else "Installation complete.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--force", action="store_true", help="replace existing framework files")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return install(args.vault, args.force, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
