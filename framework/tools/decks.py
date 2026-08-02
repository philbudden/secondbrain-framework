#!/usr/bin/env python3
"""Export and check Marp slide decks managed inside the vault."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_THEME = ROOT / "templates" / "marp-themes" / "secondbrain.css"
DEFAULT_CHROME_CANDIDATES = [
    ROOT / "tools" / "marp-chrome",
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/opt/homebrew/bin/chromium"),
    Path("/usr/local/bin/chromium"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
]


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def command_path(name: str) -> str | None:
    return shutil.which(name)


def default_chrome_path() -> str | None:
    configured = os.environ.get("CHROME_PATH")
    if configured and Path(configured).exists():
        return configured
    for candidate in DEFAULT_CHROME_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return None


def default_export_dir(source: Path) -> Path:
    resolved = source.resolve()
    try:
        rel = resolved.relative_to(ROOT / "documents" / "deliverables")
    except ValueError:
        rel = None

    if rel and len(rel.parts) >= 2:
        return ROOT / "documents" / "deliverables" / rel.parts[0] / "exports"

    slug = source.stem.removesuffix(".marp")
    return ROOT / "documents" / "deliverables" / slug / "exports"


def marp_command(source: Path, output: Path, theme: Path, extra: list[str] | None = None) -> list[str]:
    chrome_path = default_chrome_path()
    command = [
        "marp",
        str(source),
        "--allow-local-files",
        "--theme-set",
        str(theme),
        "-o",
        str(output),
    ]
    if chrome_path:
        command[1:1] = ["--browser", "chrome", "--browser-path", chrome_path]
    if extra:
        command[1:1] = extra
    return command


def run(command: list[str]) -> None:
    print("$ " + " ".join(command))
    env = os.environ.copy()
    chrome_path = default_chrome_path()
    if chrome_path and "CHROME_PATH" not in env:
        env["CHROME_PATH"] = chrome_path
    subprocess.run(command, cwd=ROOT, check=True, env=env)


def check(_args: argparse.Namespace) -> int:
    checks = {
        "node": command_path("node"),
        "npm": command_path("npm"),
        "marp": command_path("marp"),
        "chromium": command_path("chromium"),
        "google-chrome-cli": command_path("google-chrome"),
        "google-chrome-app": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome").exists()
        else None,
        "soffice": command_path("soffice"),
        "libreoffice": command_path("libreoffice"),
    }
    for name, path in checks.items():
        print(f"{name}: {path or 'missing'}")
    print(f"CHROME_PATH: {default_chrome_path() or 'missing'}")
    if not checks["marp"]:
        print("ERROR   marp CLI is missing; install @marp-team/marp-cli before exporting decks.")
        return 1
    return 0


def export(args: argparse.Namespace) -> int:
    source = (ROOT / args.source).resolve() if not Path(args.source).is_absolute() else Path(args.source).resolve()
    if not source.exists():
        print(f"ERROR   source not found: {relative(source)}")
        return 1
    if command_path("marp") is None:
        print("ERROR   marp CLI is missing; install @marp-team/marp-cli before exporting decks.")
        return 1

    theme = (ROOT / args.theme).resolve() if args.theme else DEFAULT_THEME
    if not theme.exists():
        print(f"ERROR   theme not found: {relative(theme)}")
        return 1

    output_dir = (ROOT / args.output_dir).resolve() if args.output_dir else default_export_dir(source)
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = source.stem.removesuffix(".marp")

    formats = args.formats or ["pdf", "pptx", "notes"]
    if "pdf" in formats:
        run(marp_command(source, output_dir / f"{slug}.pdf", theme))
    if "pptx" in formats:
        run(marp_command(source, output_dir / f"{slug}.pptx", theme))
    if "notes" in formats:
        run(marp_command(source, output_dir / f"{slug}-speaker-notes.txt", theme, ["--notes"]))

    print(f"Exported to {relative(output_dir)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    check_parser = sub.add_parser("check", help="check host dependencies for Marp deck export")
    check_parser.set_defaults(func=check)

    export_parser = sub.add_parser("export", help="export a Marp deck to managed deliverables")
    export_parser.add_argument("source", help="path to a .marp.md or Marp-enabled Markdown source")
    export_parser.add_argument("--output-dir", help="override export output directory")
    export_parser.add_argument("--theme", help="override Marp theme CSS path")
    export_parser.add_argument(
        "--formats",
        nargs="+",
        choices=["pdf", "pptx", "notes"],
        help="formats to export; default: pdf pptx notes",
    )
    export_parser.set_defaults(func=export)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
