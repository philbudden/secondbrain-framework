# Internal documents workspace

This is the DTM-managed workspace for authored internal documents such as
strategies, architecture notes, governance papers, operating models, and other
substantive work products that are not part of the public writing pipeline.

## Relationship to `raw/`

Use `raw/` only when a document is being treated as source material for wiki
ingestion. Keep that raw-source copy unchanged for provenance. If the same work
also belongs in your authored document system, keep a separate managed copy
here under `documents/`.

## Voice pack

`../writing/voice/voice-pack.md` is the private style guide shared across
writing and internal documents. Invoke `$voice` to learn from approved prose in
`../writing/ready/`, `../writing/published/`, and `final/`. The skill never
reads `drafts/`.

## Lifecycle

## Index

`index.md` is the curated catalogue for this workspace. Keep every draft, final
document, and managed deliverable listed exactly once under its current stage
with a one-line description and concise status context such as updated date or
linked source document. Agents should consult it before loading multiple files
just to understand what work already exists.

### `drafts/`

Active private drafting. Agents may create and revise drafts when assigned. Use
`templates/document-piece.md`, retain a stable kebab-case filename, and keep
frontmatter current.

### `final/`

The canonical internal record of finished documents. Move a draft here only
when the user approves that named document as the finished internal version.
These files are eligible as voice evidence and should remain stable except for
deliberate later revisions.

### `deliverables/`

Shareable artefacts generated from or associated with a document, such as
PowerPoint slide decks, Word versions, spreadsheets, and similar distribution
formats. Keep them under a folder matching the document slug where practical:

```text
documents/deliverables/data-strategy-for-social-impact/
```

Use kebab-case filenames for managed copies, for example
`data-strategy-for-social-impact.pptx` or
`data-strategy-for-social-impact.docx`.

Record only materially significant lifecycle changes for this workspace in the
root `log.md`; `documents/` no longer maintains a separate append-only log.

## Required frontmatter

```yaml
---
title: Document title
type: document
status: draft
created: YYYY-MM-DD
updated: YYYY-MM-DD
audience:
human_author:
ai_assistance: true
voice_pack: writing/voice/voice-pack.md
origin_path:
tags:
  - document
---
```

`origin_path` is optional and is useful when a document copy was seeded from
`raw/` or another location.

## Commands

```sh
python3 tools/documents.py status
python3 tools/documents.py lint
python3 tools/document_deliverables.py docx documents/drafts/example.md
```

## Deliverable generation

Use `tools/document_deliverables.py` when a managed Markdown document needs a shareable `.docx` copy under `documents/deliverables/<document-slug>/`.

The current supported path is:

- Markdown document to Word `.docx`

After generating a deliverable, render it through the bundled document-skill renderer and visually inspect the PNG output before treating it as ready to share. The current operating note for this workflow lives in `../work/document-deliverables-workflow.md`.
