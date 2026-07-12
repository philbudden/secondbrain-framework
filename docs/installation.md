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

## Install the SecondBrain skills

The vault installer keeps canonical skills under `skills/`. To make `$dtm` and
`$voice` discoverable by Codex, copy them into the user's Codex skills
directory:

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/dtm "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/voice "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/markdown-to-pdf "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Start a thread in the installed vault and invoke `$dtm`. That thread remains in
DTM mode until `$end-dtm` or an explicit permanent switch to the Knowledge
Agent.

Invoke `$voice` after representative writing has reached `ready/` or
`published/`, or after representative internal documents have reached
`documents/final/`. It updates the private voice pack without analysing drafts.

Invoke `$markdown-to-pdf` when you want a shareable PDF from a Markdown note or
managed document, including Mermaid diagrams when present.

## Optional PDF deliverable toolchain

If you want managed Markdown-to-PDF generation with Mermaid support, install:

```sh
brew install pandoc typst mermaid-cli
npx puppeteer browsers install chrome-headless-shell
```

The PDF command is:

```sh
python3 tools/document_deliverables.py pdf documents/drafts/example.md
```

Mermaid rendering launches a headless browser. Inside sandboxed agent
environments, that step may require unsandboxed execution approval even after
the dependencies are installed.

## Validate

```sh
python3 tools/wiki.py lint
python3 tools/dtm.py lint
python3 tools/documents.py lint
python3 tools/writing.py lint
```
