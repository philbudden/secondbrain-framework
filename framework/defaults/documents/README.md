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

`voice/document-voice-pack.md` is the canonical private guide to the user's
internal document style. It is generated from approved reader-facing prose in
`final/`. `../writing/voice/blog-voice-pack.md` is generated separately from
public writing, and `../writing/voice/anti-ai-style-rules.md` supplies the
protected anti-AI avoidance layer shared by both writing modes.

Invoke `$voice` to refresh the blog and document voice packs. The skill never
reads `drafts/` or `../writing/drafts/`, and it must not learn from chats,
Daily Notes, wiki pages, raw sources, projects, or scratch material.

## Lifecycle

## Index

`index.md` is the curated catalogue for this workspace. Keep every draft, final
document, and managed deliverable listed exactly once under its current stage
with a one-line description and concise status context such as updated date or
linked source document. Agents should consult it before loading multiple files
just to understand what work already exists.

Create `documents/index.md` before adding the first managed draft, final
document, or deliverable if it does not already exist in your vault.

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
voice_pack: documents/voice/document-voice-pack.md
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

Use `tools/document_deliverables.py` when a managed Markdown document needs a shareable deliverable under `documents/deliverables/<document-slug>/`.

Word copy:

```sh
python3 tools/document_deliverables.py docx documents/drafts/example.md
```

PDF copy, including Mermaid diagrams when present:

```sh
python3 tools/document_deliverables.py pdf documents/drafts/example.md
```

To omit an author-facing section from the reader copy, add `--exclude-heading`, for example:

```sh
python3 tools/document_deliverables.py pdf documents/drafts/example.md --exclude-heading Notes
```

The PDF path depends on `pandoc`, `typst`, and `mermaid-cli`. Mermaid rendering launches a headless browser, so agents running inside a sandbox may need unsandboxed execution approval when a source contains Mermaid diagrams.

The current supported path is:

- Markdown document to Word `.docx`

## Marp slide decks

Use Marp Markdown as the canonical source for slide decks that should remain easy to edit in Obsidian and revise with Codex. This remains true throughout the whole lifecycle: draft, final, published, and later revised deck sources are Markdown-first. Exported `.pptx`, PDF, HTML, image, and speaker-note files are generated deliverables only; promoting a deck to a final version does not make an exported file the primary copy.

The preferred Obsidian plugin is `Marp Slides Presenter` (`marp-slides-presenter`), configured to use the local Marp CLI, Chrome launch wrapper, and `templates/marp-themes` as the custom theme folder.

Keep active draft deck sources under:

```text
documents/drafts/<deck-slug>/<deck-slug>.marp.md
```

When a deck is approved as final, move the Markdown source folder to:

```text
documents/final/<deck-slug>/<deck-slug>.marp.md
```

Create exported files only when the Markdown source has been reviewed and the user asks for a deliverable pass. Generated PDFs, PPTX files, speaker-note exports, and deck-local export artefacts belong under:

```text
documents/deliverables/<deck-slug>/exports/
```

Keep deck-local images, diagrams, and style overrides beside the Markdown source while the deck is still being edited:

```text
documents/drafts/<deck-slug>/assets/
documents/final/<deck-slug>/assets/
```

Start new decks from `templates/marp-deck.md`. Use `templates/marp-themes/secondbrain.css` as the default theme unless a branded or event-specific deck needs a different visual treatment.

Speaker notes belong in HTML comments on the slide they support:

```markdown
<!--
Speaker note:
Say the spoken argument here rather than crowding the slide.
-->
```

Prefer standard Markdown image links over Obsidian embeds inside decks, for example:

```markdown
![Delegation modes](assets/diagrams/delegation-modes.svg)
```

Use SVG or PNG assets for important visuals. Mermaid is acceptable for rough drafting, but important conference visuals should be exported to SVG or PNG before final delivery so Obsidian preview, PDF export, and PowerPoint export all use the same asset. Keep `MarkdownIt Plugins` disabled in the presenter plugin unless there is a deliberate need for Kroki-backed diagram rendering.

Deck export:

```sh
python3 tools/decks.py check
python3 tools/decks.py export documents/drafts/example-deck/example-deck.marp.md
```

The helper exports PDF, image-based PPTX, and speaker notes by default. Editable PPTX remains a special-case path because Marp's editable export has lower fidelity and does not preserve presenter notes reliably.

After generating a deliverable, render it through the bundled document-skill renderer and visually inspect the PNG output before treating it as ready to share. The current operating note for this workflow lives in `../work/document-deliverables-workflow.md`.
