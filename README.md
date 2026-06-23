# SecondBrain Framework

An Obsidian-native personal knowledge and operational system maintained by two
deliberately separate LLM roles:

- the **LLM Knowledge Agent**, which compiles curated sources into a persistent,
  cited wiki; and
- the **Digital TeamMate (DTM)**, which maintains day-to-day continuity across
  notes, tasks, projects, decisions, and follow-ups.

This repository contains only the reusable framework. It contains no personal
vault data, source material, Daily Notes, project content, or activity history.

## Why this exists

Most document assistants rediscover context at query time. SecondBrain instead
maintains a durable intermediate knowledge layer and a separate operational
memory. The division keeps long-term evidence synthesis disciplined while still
supporting practical daily collaboration.

## Quick start

Requirements: Python 3.9+ and an existing or new Obsidian vault.

```sh
python3 install.py --vault /path/to/your/obsidian-vault
```

The installer copies only framework files and never copies this repository's
`.git` directory. Existing files are preserved unless `--force` is supplied.
After installation:

1. Put a source directly in `raw/` and ask the Knowledge Agent to ingest it.
2. Ask the DTM to open or update today's Daily Note.
3. Review `framework/automation-definitions/` and recreate only the automations
   appropriate for your host.

See [Installation](docs/installation.md), [Architecture](docs/architecture.md),
and [Operations](docs/operations.md) for the full model.

## Privacy model

The public framework is produced through an allowlist-only exporter. Personal
content paths are denied independently of the allowlist, and the export fails
closed when it detects live-vault Git metadata, unsafe destinations, or likely
personal identifiers. See [Publication and versioning](docs/publication.md).

## Status

The framework is evolving and should be reviewed before use with sensitive or
high-stakes information. Contributions are welcome through pull requests.

Licensed under the [MIT License](LICENSE).
