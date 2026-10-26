# Operations

## Knowledge ingestion

Place new sources directly under `raw/`. The Knowledge Agent processes each
source, integrates its evidence across the wiki, updates the index and log,
validates the result, then moves the unchanged source to `raw/processed/`.
Incomplete work remains visible in the inbox.

## Daily collaboration

An explicitly activated DTM thread opens and closes Daily Notes, carries only
incomplete tasks and active questions forward, preserves the nesting of
unfinished parent and child tasks, instantiates enabled recurrence, captures
decisions, and maintains project continuity. Completed tasks stay in the
historical note. Durable knowledge can graduate to the wiki while remaining
clearly distinguished from externally sourced evidence.

Completing work includes its normal delivery: sharing, sending, handing over,
or publishing an output does not need a separate follow-up task unless the user
asks for one. When a hand-off confirms delivery is complete, do not create or
carry a delivery task; correct any stale Daily Note entry.

Create a follow-up task only when the user explicitly asks to track it, an
existing user-assigned outcome remains incomplete, or the step is required to
complete the outcome the user assigned. A work report, technical finding,
authorised hand-off, or the agent's view of a sensible next step does not by
itself authorise a new task. Keep optional investigations, checks, improvements,
and recommendations as context unless the user adopts them.

An open point listed in a hand-off is not automatically an outstanding user
commitment. Do not label it pending, carry it forward, or repeatedly surface it
unless it is part of an existing user-assigned outcome or the user adopts it.
Record it as a limitation only when it materially affects the completed outcome.

When every child task under a parent is checked off, check off the parent task
as well.

Specialised work can run in separate non-DTM threads. Those threads must not
edit Daily Notes directly. Only the human decides whether to hand their
outcomes to the DTM and explicitly invokes the `dtm-handoff` skill. Agents must
not initiate or send a hand-off on their own; the receiving DTM processes only
a hand-off that states the user explicitly invoked the skill.

## Internal documents

Use `documents/drafts/` for collaborative internal drafting and
`documents/final/` for the approved internal record of strategies,
architectural notes, and similar work products. Use
`documents/deliverables/<document-slug>/` for shareable `.pptx`, `.docx`,
`.xlsx`, and similar artefacts linked to those documents. If a document also
serves as a wiki source, keep the raw-source copy under `raw/` or
`raw/processed/` as immutable provenance and manage the authored copy
separately under `documents/`.

## Maintenance

Run the structural linters after framework changes, including
`python3 tools/contracts.py lint` when behaviour contracts change. Periodically
perform a semantic wiki review for contradictions, stale claims, unsupported
assertions, orphans, and evidence gaps.

## Collaborative writing

Writing moves from agent-assisted `drafts/` to the human-approved `ready/`
queue and then to `published/` only after confirmed publication. Publishing
integrations consume only content between explicit publish markers; private
briefs, source checks, and revision notes remain in the vault. The framework
includes a parameterized publisher definition but enables no destination by
default.

The explicit `$voice` skill learns only from reader-facing prose in
`writing/ready/`, `writing/published/`, and `documents/final/`, maintains a
private voice pack, and excludes drafts to avoid training the style guide on
unfinished or agent-generated work. Drafting agents read the pack when present,
while the current brief always takes precedence.

## Automation

Definitions under `framework/automation-definitions/` are parameterized
documentation, not credentials or host configuration. Recreate them in the
automation system used on the always-on host and keep machine-specific values
out of this repository.
