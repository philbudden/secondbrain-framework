# Operations

## Knowledge ingestion

Place new sources directly under `raw/`. The Knowledge Agent processes each
source, integrates its evidence across the wiki, updates the index and log,
validates the result, then moves the unchanged source to `raw/processed/`.
Incomplete work remains visible in the inbox.

## Daily collaboration

The DTM opens and closes Daily Notes, carries only incomplete tasks and active
questions forward, instantiates enabled recurrence, captures decisions, and
maintains project continuity. Durable knowledge can graduate to the wiki while
remaining clearly distinguished from externally sourced evidence.

## Maintenance

Run both structural linters after framework changes. Periodically perform a
semantic wiki review for contradictions, stale claims, unsupported assertions,
orphans, and evidence gaps.

## Automation

Definitions under `framework/automation-definitions/` are parameterized
documentation, not credentials or host configuration. Recreate them in the
automation system used on the always-on host and keep machine-specific values
out of this repository.
