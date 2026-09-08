# Changelog

This project follows Keep a Changelog principles and uses semantic versioning
for tagged releases.

## [Unreleased]

No unreleased changes.

## [2026-09-08]

### Added

- A versioned behaviour-contract inventory and dependency-free validator covering role boundaries, source and content lifecycles, privacy, automation, storage, and harness assumptions.

### Changed

- Framework installation, export validation, CI, and regression tests now include the behaviour-contract inventory so contract drift is detected before release.
- DTM coordination now uses a discoverable `DTM YYYY-MM-DD` session title and explicitly reserves Daily Note writes for activated DTM threads; non-DTM work is handed back for DTM interpretation and capture.
- Installation, architecture, and operations guidance now document the contract checks, DTM hand-off path, and support for non-iCloud vault storage providers.

## [2026-08-31]

### Added

- `dtm-handoff` skill for sending incremental work-thread outcomes to the active DTM thread without granting Daily Note write authority.

### Changed

- Daily Note writes are now reserved for explicitly DTM-activated threads, with scheduled rollover as the only direct-write exception.

## [2026-08-24]

### Changed

- Writing archive rules now support unpublished superseded drafts retained as source material, while still preserving former publication metadata for archived published pieces.

## [2026-08-17]

### Added

- Core guidance now recognises a practical review tools index for reusable tests, heuristics, taxonomies, checklists, and decision lenses created in the wiki.

### Changed

- Writing and newsletter templates now include an italic generative-AI-use preface at the end of new publishable bodies.
- Voice analysis now weights more recent approved writing more strongly, so older accepted prose does not permanently anchor the user's developing style.

## [2026-08-03]

### Changed

- Daily Note rollover now replaces earlier previous-note pointers cleanly, keeping a single current link to the preceding note.

## [2026-07-30]

### Added

- Separate voice-pack profiles for public writing and internal documents, with shared protected anti-AI style rules and a rollback copy for each generated profile.

## [2026-07-28]

### Added

- Marp slide-deck support, with a canonical Markdown deck template, a SecondBrain theme, deck-aware validation, and managed PDF, PowerPoint, and speaker-note exports.

### Changed

- Document and slide-deck workflows now keep Markdown as the canonical source throughout drafting, approval, and delivery; exported files remain generated deliverables.

## [2026-07-27]

### Added

- `resolve-document-items` skill for closing open questions, unowned actions, assumptions, and pending decisions in documents through a calm one-question-at-a-time workflow.
- DOCX deliverable generation now renders Markdown pipe tables as Word tables.

### Changed

- DOCX generation now supports standard Markdown image links and preserves a more natural document structure in exported Word files.
- Daily Notes are retained together in the main workspace, and DTM validation checks that referenced projects, working notes, documents, and writing items have a same-day activity-log record.
- Framework validation now detects out-of-order system-log entries.

## [2026-07-19]

### Added

- `thinking-interview` skill for working through a question with structured prompts before committing to a conclusion.
- Lifecycle validation for archived writing, including the former publication URL, publication date, archive date, and archive reason.

### Changed

- Daily Note and working-note workflows were refined around stable focus commitments, durable working-note status, and clearer operational continuity.

## [2026-07-12]

### Added

- Markdown-to-PDF skill and managed Markdown-to-DOCX deliverable generation.
- Working-note template and workspace conventions for retained operational research, plans, and decision support.

### Changed

- Daily Note rollover and framework export checks were strengthened to preserve continuity and public-safe framework output.

## [2026-07-06]

### Added

- Managed `writing/` and `documents/` workspaces, including draft, ready, final, published, and deliverable lifecycle rules.
- DTM and voice skills, writing and document lint tools, reusable writing/document templates, and scheduled drafting and publishing automation definitions.
- Thread-scoped DTM sessions and a durable queue for wiki open questions.

### Changed

- The publication boundary now excludes personal writing and documents as well as Daily Notes, wiki content, and other live-vault material.

## [2026-06-23]

### Added

- Initial Knowledge Agent and Digital TeamMate framework.
- Allowlist-only publication boundary, repeatable installer, sanitized automation definitions, and empty-vault example.
