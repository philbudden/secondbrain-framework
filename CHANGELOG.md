# Changelog

This project follows Keep a Changelog principles and uses semantic versioning
for tagged releases.

## [Unreleased]

### Added

- Marp slide-deck support, with a canonical Markdown deck template, a SecondBrain theme, deck-aware validation, and managed PDF, PowerPoint, and speaker-note exports.
- Separate voice-pack profiles for public writing and internal documents, with shared protected anti-AI style rules and a rollback copy for each generated profile.

### Changed

- Document and slide-deck workflows now keep Markdown as the canonical source throughout drafting, approval, and delivery; exported files remain generated deliverables.
- DOCX generation now supports standard Markdown image links and preserves a more natural document structure in exported Word files.
- Daily Note rollover now replaces earlier previous-note pointers cleanly, keeping a single current link to the preceding note.

## [2026-07-27]

### Added

- `resolve-document-items` skill for closing open questions, unowned actions, assumptions, and pending decisions in documents through a calm one-question-at-a-time workflow.
- DOCX deliverable generation now renders Markdown pipe tables as Word tables.

### Changed

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
