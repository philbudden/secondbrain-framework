#!/usr/bin/env python3
"""Publish a sanitized framework branch and assigned draft pull request."""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from export_framework import ExportError, export_framework, staged_files, tree_digest

LIVE_ROOT = Path(__file__).resolve().parent.parent


class PublishError(RuntimeError):
    pass


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True)
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise PublishError(f"Command failed ({' '.join(command[:3])}): {detail}")
    return result


def git(target: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", "-C", str(target), *arguments], check=check)


def assert_target(target: Path) -> None:
    target_text = str(target)
    if target == LIVE_ROOT or LIVE_ROOT in target.parents or target in LIVE_ROOT.parents:
        raise PublishError("Public checkout must be separate from the live vault")
    if "Mobile Documents" in target.parts or "iCloud~md~obsidian" in target_text:
        raise PublishError("Public checkout must not be inside an iCloud-synchronized path")
    if (LIVE_ROOT / ".git").exists():
        raise PublishError("Live vault contains forbidden .git metadata")
    if not (target / ".git").exists():
        raise PublishError(f"Target is not a Git checkout: {target}")
    top = Path(git(target, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if top != target:
        raise PublishError(f"Target is not the repository root: {target}")


def repository_digest(target: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="secondbrain-current-") as temporary:
        snapshot = Path(temporary)
        for source in staged_files(target):
            relative = source.relative_to(target)
            if ".git" in relative.parts or source.name in {".DS_Store"} or "__pycache__" in relative.parts:
                continue
            destination = snapshot / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        return tree_digest(snapshot)


def replace_worktree(target: Path, staging: Path) -> None:
    for child in target.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    for source in staged_files(staging):
        destination = target / source.relative_to(staging)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def validate_export(target: Path) -> None:
    python_files = [str(target / "install.py")]
    python_files.extend(str(path) for path in sorted((target / "framework" / "tools").glob("*.py")))
    run([sys.executable, "-m", "py_compile", *python_files])
    with tempfile.TemporaryDirectory(prefix="secondbrain-install-") as temporary:
        vault = Path(temporary) / "vault"
        run([sys.executable, str(target / "install.py"), "--vault", str(vault)])
        run([sys.executable, str(vault / "tools" / "wiki.py"), "lint"])
        run([sys.executable, str(vault / "tools" / "dtm.py"), "lint"])


def existing_pr(repo: str, branch: str) -> str:
    result = run(
        ["gh", "pr", "list", "--repo", repo, "--head", branch, "--state", "open", "--json", "url", "--jq", ".[0].url"],
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def create_pr(repo: str, branch: str, base: str, assignee: str, week: str) -> str:
    body = (
        "## What changed\n\n"
        "Automated allowlist-only synchronization of the reusable SecondBrain framework.\n\n"
        "## Privacy boundary\n\n"
        "The exporter denied personal vault paths and scanned staged text for host paths, "
        "identifiers, and email addresses before publication.\n\n"
        "## Validation\n\n"
        "- Python tools compiled\n"
        "- Clean-vault installation completed\n"
        "- Wiki and DTM structural lint passed\n"
    )
    result = run(
        [
            "gh", "pr", "create", "--repo", repo, "--draft", "--base", base,
            "--head", branch, "--assignee", assignee,
            "--title", f"[automation] Sync SecondBrain framework ({week})",
            "--body", body,
        ]
    )
    return result.stdout.strip()


def publish(target: Path, repo: str, assignee: str, base: str) -> int:
    target = target.expanduser().resolve()
    assert_target(target)
    if git(target, "status", "--porcelain").stdout.strip():
        raise PublishError("Public checkout has uncommitted changes; refusing automated publication")

    git(target, "fetch", "origin", "--prune")
    git(target, "switch", base)
    git(target, "pull", "--ff-only", "origin", base)

    with tempfile.TemporaryDirectory(prefix="secondbrain-export-") as temporary:
        staging = Path(temporary)
        fingerprint = export_framework(staging)
        if fingerprint == repository_digest(target):
            print("No meaningful framework changes; no branch, commit, or PR created.")
            return 0

        today = dt.date.today()
        week = f"{today.isocalendar().year}-W{today.isocalendar().week:02d}"
        branch = f"automation/framework-sync-{week.lower()}-{fingerprint[:8]}"
        remote = git(
            target, "ls-remote", "--exit-code", "--heads", "origin", f"refs/heads/{branch}", check=False
        )
        if remote.returncode == 0:
            url = existing_pr(repo, branch)
            if url:
                print(f"Publication already exists: {url}")
                return 0
            url = create_pr(repo, branch, base, assignee, week)
            print(f"Created missing draft PR for existing branch: {url}")
            return 0

        git(target, "switch", "-c", branch)
        replace_worktree(target, staging)
        validate_export(target)
        git(target, "add", "-A")
        if git(target, "diff", "--cached", "--quiet", check=False).returncode == 0:
            print("No meaningful staged changes; no commit or PR created.")
            return 0
        git(target, "commit", "-m", f"Sync SecondBrain framework ({week})")
        git(target, "push", "-u", "origin", branch)
        url = create_pr(repo, branch, base, assignee, week)
        print(f"Published draft PR: {url}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--repo", required=True, help="GitHub owner/repository")
    parser.add_argument("--assignee", required=True)
    parser.add_argument("--base", default="main")
    args = parser.parse_args()
    try:
        return publish(args.target, args.repo, args.assignee, args.base)
    except (ExportError, PublishError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
