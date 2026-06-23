# Installation

## Requirements

- Python 3.9 or later
- An Obsidian vault
- An LLM coding agent capable of reading a vault-level `AGENTS.md`

## Install

Clone this repository somewhere outside the vault, then run:

```sh
python3 install.py --vault /path/to/vault
```

The installer creates missing operational directories and copies framework
contracts, templates, tools, safe Obsidian settings, recurrence defaults, and
sanitized seed pages. It does not copy `.git` metadata and does not overwrite
existing files by default. Preview with `--dry-run`; deliberately replace
framework files with `--force` after reviewing the changes.

## Configure

1. Review `AGENTS.md` and `DTM.md` for local preferences.
2. Keep `scratch.md` human-only or remove that convention explicitly.
3. Edit `dtm/recurring-tasks.json`; example rules are disabled by default.
4. Configure automation definitions for the local agent host. Replace every
   `{{PLACEHOLDER}}`; never commit the resulting machine-specific values.
5. Open the directory as an Obsidian vault.

## Validate

```sh
python3 tools/wiki.py lint
python3 tools/dtm.py lint
```
