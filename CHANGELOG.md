# Changelog

This project follows Keep a Changelog principles and uses semantic versioning
for tagged releases.

## [Unreleased]

### Added

- Initial Knowledge Agent and Digital TeamMate framework.
- Allowlist-only publication boundary and repeatable installer.
- Sanitized automation definitions and empty-vault example.
- `resolve-document-items` skill for closing open questions, unowned actions, assumptions, and pending decisions in documents through a calm one-question-at-a-time workflow.
- DOCX deliverable generation now renders Markdown pipe tables as Word tables.
- Marp slide-deck support, with a canonical Markdown deck template, a SecondBrain theme, deck-aware validation, and managed PDF, PowerPoint, and speaker-note exports.
- Separate voice-pack profiles for public writing and internal documents, with shared protected anti-AI style rules and a rollback copy for each generated profile.

### Changed

- Document and slide-deck workflows now keep Markdown as the canonical source throughout drafting, approval, and delivery; exported files remain generated deliverables.
- DOCX generation now supports standard Markdown image links and preserves a more natural document structure in exported Word files.
- Daily Note rollover now replaces earlier previous-note pointers cleanly, keeping a single current link to the preceding note.
