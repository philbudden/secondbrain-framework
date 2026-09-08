# Architecture

SecondBrain separates operational collaboration from durable knowledge work.

## Runtime layers

1. **Raw sources** are human-curated evidence. Top-level files await ingestion;
   completed sources move unchanged to `raw/processed/`.
2. **Wiki** pages are agent-maintained syntheses with provenance, citations,
   cross-links, an index, and an append-only operation log.
3. **Daily operations** contain Daily Notes, tasks, decisions, project plans,
   working documents, and recurrence state maintained by the DTM.
4. **Contracts, schema, and tools** define role boundaries, formats, workflows,
   validation, templates, behaviour inventory, and automations.

## Behaviour contracts

`contracts/behaviour-inventory.json` is the maintained inventory of framework
behaviours that should be tracked as explicit contracts, deterministic checks,
fixtures, or harness-specific adapters. It classifies each behaviour by owner,
workspace, current specification, current enforcement, severity, portability
class, prompt-debt signals, and candidate tests.

Run `python3 tools/contracts.py lint` after changing the inventory. The
validator is deliberately dependency-free so it can run in ordinary Python
environments and in framework CI.

## Role boundary

The Knowledge Agent owns systematic source ingestion and wiki maintenance. An
explicitly activated DTM thread owns Daily Notes and operational continuity. The
DTM does not scan the raw inbox, and the Knowledge Agent never writes the Daily
Note activity section.

Non-DTM work threads may perform specialised execution with their own model and
context, but they do not write Daily Notes directly. When their outcomes should
be captured, they use the `dtm-handoff` skill to send a concise incremental
hand-off to the active DTM thread named `DTM YYYY-MM-DD`.

## Production boundary

The live Obsidian vault may be local-only or synchronised by a file service
such as OneDrive, SharePoint, Obsidian Sync, iCloud, or another storage
provider, but it is never a Git checkout. A separate repository contains a
sanitized product representation of the framework. Publication is strictly
one-way:

```text
live vault -- allowlist + privacy checks --> staged framework --> Git checkout
```

No branch, merge, worktree, or repository operation runs against the live
vault. Rollback means restoring a reviewed framework version through the
installer or manually applying a known-good change—not checking out history in
production.
