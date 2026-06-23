# Architecture

SecondBrain separates operational collaboration from durable knowledge work.

## Runtime layers

1. **Raw sources** are human-curated evidence. Top-level files await ingestion;
   completed sources move unchanged to `raw/processed/`.
2. **Wiki** pages are agent-maintained syntheses with provenance, citations,
   cross-links, an index, and an append-only operation log.
3. **Daily operations** contain Daily Notes, tasks, decisions, project plans,
   working documents, and recurrence state maintained by the DTM.
4. **Schema and tools** define role boundaries, formats, workflows, validation,
   templates, and automations.

## Role boundary

The Knowledge Agent owns systematic source ingestion and wiki maintenance. The
DTM owns Daily Notes and operational continuity. The DTM does not scan the raw
inbox, and the Knowledge Agent never writes the Daily Note activity section.

## Production boundary

The live Obsidian vault may be synchronized by a file service such as iCloud,
but it is never a Git checkout. A separate repository contains a sanitized
product representation of the framework. Publication is strictly one-way:

```text
live vault -- allowlist + privacy checks --> staged framework --> Git checkout
```

No branch, merge, worktree, or repository operation runs against the live
vault. Rollback means restoring a reviewed framework version through the
installer or manually applying a known-good change—not checking out history in
production.
