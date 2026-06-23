# SecondBrain agent operating contract

This vault has two distinct agent roles. Follow this contract for every task in
this directory and keep their responsibilities visibly separate.

## Role routing

### LLM Knowledge Agent

Use the Knowledge Agent role for source ingestion, wiki synthesis, provenance,
index maintenance, and wiki health. It owns the long-term knowledge workflow
defined below and may inspect `raw/` when doing that work.

### Digital TeamMate (DTM)

Use the DTM role for daily collaboration: Daily Notes, tasks, projects,
decisions, follow-ups, working documents, assigned research, and operational
continuity. Before acting as the DTM, read and follow `DTM.md`.

The user can select either role explicitly. Otherwise route source-ingestion
and wiki-maintenance requests to the Knowledge Agent, and day-to-day operational
requests to the DTM. If a request genuinely spans both roles, say so and execute
each phase under its respective rules.

The DTM must never scan or automatically process `raw/`. It may read only a
specific raw file explicitly named by the user, and only for that assigned task.
The Knowledge Agent must never add, edit, reorder, or remove content in a Daily
Note's `Notes & Activity` section.

## Knowledge Agent mission

Compile curated source material into a durable, navigable wiki. Integrate new
evidence into existing understanding instead of creating isolated summaries.
Preserve provenance, surface contradictions, and make useful discoveries
compound across sessions.

## Layers and ownership

### `scratch.md` — human-only, excluded

- Ignore `scratch.md` completely in every role and workflow unless the user
  explicitly names that file and directs the agent to use it for the current
  task.
- Do not read, search, index, summarize, cite, link, edit, move, delete, lint,
  monitor, or infer context from it during ordinary vault operations.
- Exclude it from broad file discovery and content searches. Its mere presence
  is not pending work and must never trigger ingestion or DTM capture.
- Explicit access applies only to the task in which the user grants it; return
  to ignoring the file afterwards.

### `raw/` — human-owned inbox and immutable archive

- Read any source necessary for the task.
- Treat top-level source documents in `raw/` as the pending ingestion queue.
- After—and only after—a completely successful Knowledge Agent ingest, move the
  source unchanged into `raw/processed/` and update all provenance links to its
  archived path. This one-time archival move is the only permitted agent move
  within `raw/`.
- Never overwrite an existing processed file. If the destination filename is
  occupied, stop and ask the user how to resolve it.
- Never archive a source when ingestion, integration, index maintenance, log
  maintenance, or linting remains incomplete.
- Never edit, rename, normalize, delete, or subsequently move a file in
  `raw/processed/`.
- Never silently replace a source with a downloaded or reformatted copy.
- Assets referenced by a source belong in `raw/assets/` and are equally
  immutable once placed there.
- If a source is unreadable, incomplete, duplicated, or needs correction, tell
  the user. Record the limitation in its source page.

### `wiki/` — agent-owned, maintained

- Create and revise pages freely when supported by the sources or by clearly
  labelled analysis.
- Prefer updating an existing canonical page over creating a near-duplicate.
- Keep links, index entries, summaries, dates, and citations consistent in the
  same change.
- Never present inference as sourced fact.

### `AGENTS.md` — shared schema

Change this contract only when the user asks, or when a task exposes a durable
workflow improvement. Explain material schema changes before applying them.

### Publication boundary

- The live iCloud vault is production and must never become a Git repository.
  Never run `git init`, `git status`, `git add`, `git commit`, branch, merge,
  worktree, or other repository operations against this directory, and never
  create `.git` metadata anywhere inside it.
- `publication/` contains sanitized public-repository documents and an explicit
  export manifest. `automation-definitions/` contains parameterized, reusable
  descriptions of system automations. Both are framework-owned and must contain
  no personal data.
- Public extraction is allowlist-only through `tools/publish_framework.py`.
  Never publish by copying the vault, using a broad recursive sync, or deriving
  an export from everything not ignored.
- All Git operations for publication must use the separate external framework
  checkout and an explicit target path. The publication tool rejects targets
  inside iCloud or inside the live vault.
- Never publish `scratch.md`, Daily Notes, wiki content, sources, personal
  projects, working documents, activity logs, Obsidian workspaces, or any file
  not explicitly approved by `publication/manifest.json`.
- When system architecture, templates, tools, Obsidian configuration, or
  automations change, update their sanitized framework representation in the
  same task where practical.

## Wiki structure

- `wiki/overview.md` — current high-level synthesis and navigation.
- `wiki/index.md` — complete content catalogue with one-line descriptions.
- `wiki/log.md` — append-only chronological activity record.
- `wiki/sources/` — one provenance and summary page per ingested source.
- `wiki/entities/` — people, organisations, products, places, works, and other
  named things.
- `wiki/concepts/` — reusable ideas, terms, methods, and mechanisms.
- `wiki/topics/` — broader subject hubs that connect entities and concepts.
- `wiki/analyses/` — comparisons, answers, hypotheses, timelines, and other
  synthesized outputs worth retaining.
- `templates/` — Obsidian templates for wiki and DTM documents; never list
  these as content in the wiki index.

Use lowercase kebab-case filenames. Choose the shortest unambiguous canonical
name. Page titles use normal title case. When names collide, qualify the
filename, for example `mercury-planet.md` and `mercury-element.md`.

## Required frontmatter

Every content page except `index.md` and `log.md` has:

```yaml
---
title: Human-readable title
type: overview | source | entity | concept | topic | analysis
status: current | seed | needs-review | disputed | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - wiki
---
```

Additional fields by type:

- Source: `source_path`, `source_kind`, and `ingested`.
- Analysis: `question` when it answers a specific query.
- Any page may use `aliases` as a YAML list.

Dates use the user's local date. `created` never changes; update `updated` when
the body materially changes. `seed` means useful but thin. `needs-review` marks
uncertainty or incomplete processing. `disputed` means credible sources
conflict. `superseded` pages must link prominently to their replacement.

## Writing and linking

- Start each content page with a concise synthesis, not a table of metadata.
- Use Obsidian links rooted at the vault, with useful display text:
  `[[wiki/concepts/example|Example]]`.
- Link the first meaningful mention of another wiki page. Avoid link spam.
- Link back from a newly created page to at least one hub or related page.
- Use headings that describe the domain. Do not force every page into an
  identical outline.
- Distinguish facts, source claims, and analysis with prose. Use explicit labels
  such as **Inference**, **Open question**, and **Conflict** where ambiguity is
  possible.
- Do not copy long source passages. Summarize; quote only short language whose
  exact wording matters.

## Citations and provenance

Claims that are specific, contestable, quantitative, or not common knowledge
need a citation to a wiki source page. Cite at sentence or paragraph level:

```markdown
Claim being supported. [[wiki/sources/source-name#Relevant heading|Source Name]]
```

The linked source page must identify the immutable raw file via `source_path`
and a body link such as `[[raw/article.md|Open raw source]]`. Use a meaningful
heading, page, timestamp, section, row, or figure as a locator whenever the raw
format permits it. If several sources support a synthesis, cite each relevant
source. If sources disagree, preserve both claims and explain the conflict.

Never cite an analysis page as though it were primary evidence. It may be linked
for context, but its underlying source citations remain authoritative.

## Ingest workflow

When asked to ingest one or more sources:

1. Read `wiki/index.md`, `wiki/overview.md`, recent entries in `wiki/log.md`, and
   the source. Search the wiki for related names and concepts before creating
   pages.
2. For image-bearing material, read the text first, then inspect locally
   available images that could change the interpretation. Note uninspected or
   unavailable material.
3. Detect exact or likely duplicate ingestion. Do not create a second source
   page for the same raw file.
4. Extract the source's central claims, evidence, entities, concepts,
   limitations, dates, and relationships. Identify what is genuinely new to
   the existing wiki.
5. If emphasis or interpretation is consequential and genuinely ambiguous,
   discuss it with the user. Otherwise proceed and mark uncertainty explicitly.
6. Create or update the source page. Then integrate the evidence into every
   materially affected entity, concept, topic, analysis, and overview page.
   Do not stop at a standalone summary.
7. Reconcile contradictions: record both positions, date them where relevant,
   assess source quality without inventing certainty, and use `disputed` or
   `superseded` when appropriate.
8. Update `wiki/index.md` for every created, renamed, or materially re-scoped
   page. Keep entries in their category and sorted by title.
9. Append one log entry describing the source and all important pages created
   or revised.
10. Run `python3 tools/wiki.py lint`. Fix safe structural issues; report
    substantive unresolved issues to the user.
11. Only when all preceding steps succeed, move a top-level source into
    `raw/processed/`. Update its source page's `source_path` and body link to the
    processed location, rerun lint, and confirm that the top-level inbox is
    clear of that document. Sources already under `raw/processed/` are not moved.

## Query workflow

When asked a question:

1. Read `wiki/index.md`, then search and read the relevant wiki pages.
2. Follow citations to source pages and raw material when the claim is
   high-stakes, disputed, unclear, or requires precise wording.
3. Answer from the available evidence with inline wiki citations. State gaps
   and confidence plainly; do not fill gaps from memory without saying so.
4. Use web research only when the user asks or when current external facts are
   necessary. Save any source the user chooses to curate under `raw/` before
   treating it as durable wiki evidence.
5. Offer to file a substantial reusable answer. If the user already asked to
   file it, create or update an analysis/topic page, update the index and
   related pages, and append a `query` log entry.

Short answers and one-off operational chat do not need to become pages.

## Lint workflow

For a health check, run the local lint first, then do a semantic review that
automation cannot perform:

- claims contradicted by newer or stronger sources;
- stale time-sensitive claims and superseded conclusions;
- near-duplicate pages or inconsistent names;
- important unlinked concepts that deserve pages;
- missing reciprocal/contextual links and weak hub pages;
- source pages whose evidence was never integrated elsewhere;
- unsupported assertions, vague citations, and unclear inference;
- unanswered questions and evidence gaps worth investigating.

Fix mechanical issues directly. For substantive reinterpretations, preserve the
old view in the log and explain the change. Append a `lint` log entry listing
checks performed, fixes made, and unresolved recommendations.

## Index contract

`wiki/index.md` is curated navigation, not a raw file dump. Every non-template
content page appears exactly once with a link, one-line description, status,
and updated date. Organize it under Overview, Topics, Concepts, Entities,
Analyses, and Sources. Omit empty categories only if the structure remains
obvious. Keep descriptions concrete enough to route future queries.

## Log contract

`wiki/log.md` is append-only. Never rewrite or reorder prior entries except to
repair a broken link or obvious typo. Put newest entries at the bottom, using:

```markdown
## [YYYY-MM-DD] ingest | Source title

Summary of what changed, with links to affected pages.
```

Allowed operation labels are `setup`, `ingest`, `query`, `lint`, `schema`, and
`dtm`. DTM log entries are reserved for significant operational changes such as
project milestones, durable decisions, or created/updated wiki artefacts; routine
daily rollover does not need a wiki log entry.
Mention unresolved conflicts, gaps, or follow-ups in the same entry.

## Completion standard

A wiki task is complete only when the content, backlinks, index, dates, and log
agree; citations resolve to source pages; any newly ingested source is archived
unchanged under `raw/processed/`; and the local lint passes or its remaining
warnings are explained.
