---
name: markdown-to-pdf
description: Generate a shareable PDF from a SecondBrain Markdown note or managed document, including Mermaid diagrams when present. Use when the user asks for a PDF deliverable, a shareable PDF copy, or a Markdown-to-PDF export inside the vault.
---

# Markdown to PDF

Create a PDF artefact from a Markdown source using the managed SecondBrain deliverables tool.

## Use the managed command

1. Confirm the working directory is a SecondBrain vault containing `AGENTS.md` and `tools/document_deliverables.py`.
2. If the source is a managed document under `documents/drafts/` or `documents/final/`, prefer the default output location under `documents/deliverables/<slug>/`.
3. Run:

```sh
python3 tools/document_deliverables.py pdf <source.md>
```

4. For a non-document Markdown note, provide an explicit output path:

```sh
python3 tools/document_deliverables.py pdf <source.md> --output /path/to/output.pdf
```

5. If the note contains author-facing sections that should not be included in the reader copy, omit them with one or more `--exclude-heading` arguments:

```sh
python3 tools/document_deliverables.py pdf <source.md> --exclude-heading Notes
```

## Mermaid and sandboxing

- The PDF workflow supports Mermaid diagrams automatically.
- Mermaid rendering depends on `pandoc`, `typst`, `mermaid-cli`, and a working headless browser runtime.
- If the source contains Mermaid and browser launch fails inside a sandboxed agent environment, rerun the same command with unsandboxed execution approval rather than replacing the diagram workflow by hand.

## Validation

- Confirm the command prints the output path.
- Inspect the PDF visually before treating it as ready to share.
- For managed document deliverables created under DTM authority, update the Daily Note and relevant document index or log entries when the artefact materially changes the workspace state.
