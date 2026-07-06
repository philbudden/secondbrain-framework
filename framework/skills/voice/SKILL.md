---
name: voice
description: Analyse the user's approved writing and finished internal documents and create or update the private SecondBrain writing voice pack. Use only when the user invokes `$voice` or explicitly asks to learn, refresh, or inspect their writing style from `writing/ready/`, `writing/published/`, and `documents/final/`; never learn from drafts, chats, notes, wiki pages, sources, or other vault content.
---

# Writing voice analysis

Build an evidence-based style model at `writing/voice/voice-pack.md` without
reading `writing/drafts/` or `documents/drafts/`.

## Analyse the corpus

1. Confirm the working directory contains `AGENTS.md`, `writing/README.md`, and
   the writing workspace. Read those contracts first. Never inspect
   `scratch.md`.
2. Read the existing voice pack when present. Preserve its **Declared
   preferences** section verbatim unless the user explicitly asks to change it.
3. Enumerate Markdown files only under `writing/ready/`,
   `writing/published/`, and `documents/final/`. Do not list, search, count, or
   read files under `writing/drafts/` or `documents/drafts/`.
4. Analyse only reader-facing prose. For writing pieces, use only content
   between `<!-- publish:start -->` and `<!-- publish:end -->`. For internal
   documents in `documents/final/`, analyse the reader-facing body while
   ignoring private notes, metadata, and drafting residue.
5. Weight published work more strongly than ready work, and weight approved
   final internal documents between those two levels unless the user asks
   otherwise. Separate stable habits seen across pieces from topic, format, or
   genre-specific choices. Do not infer a confident rule from a single example.
6. Extract actionable patterns for tone, stance, syntax and rhythm, diction,
   structure, transitions, openings, closings, rhetorical habits, formatting,
   and characteristic things to avoid. Use short examples only when they add
   precision; link them to the eligible writing file.

## Update the voice pack

- Create the pack from `templates/voice-pack.md` if absent; otherwise update it
  in place without erasing declared preferences or useful historical nuance.
- Keep observations concrete enough to guide drafting. Prefer “Use X under Y
  conditions” over vague labels such as “engaging” or “authentic.”
- Record coverage, confidence, eligible source counts, an evidence ledger, and
  what changed in this analysis pass.
- Mark the pack `provisional` when evidence is sparse or narrow. Never invent a
  style to fill gaps; state what cannot yet be learned.
- Append a `voice` entry to `writing/log.md`. If the current thread is an active
  DTM session, also add the updated pack to today's Daily Note References and
  record the action once.
- Run `python3 tools/writing.py lint` before reporting completion.

If there is no eligible corpus, create or retain a provisional empty pack,
report that no style was inferred, and suggest moving representative human-
approved work to `writing/ready/`, `writing/published/`, or `documents/final/`
before invoking `$voice` again.
