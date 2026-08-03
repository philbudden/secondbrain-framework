---
name: voice
description: Analyse the user's approved writing and finished internal documents and create or update private SecondBrain voice packs. Use only when the user invokes `$voice` or explicitly asks to learn, refresh, or inspect their writing style from `writing/ready/`, `writing/published/`, and `documents/final/`; never learn from drafts, chats, notes, wiki pages, sources, or other vault content.
---

# Voice analysis

Build evidence-based style models without reading `writing/drafts/` or
`documents/drafts/`.

Generated outputs:

- `writing/voice/blog-voice-pack.md` — public/blog writing voice learned from
  `writing/ready/` and `writing/published/`.
- `documents/voice/document-voice-pack.md` — internal document voice learned
  from `documents/final/`.
- `writing/voice/voice-pack.md` — compatibility mirror of the blog voice pack
  for older templates and artefacts that still point at this path.

Protected input:

- `writing/voice/anti-ai-style-rules.md` — shared anti-AI avoidance rules that
  apply to both generated packs and must not be rewritten by `$voice` unless
  the user explicitly asks to change that file.

## Analyse the corpus

1. Confirm the working directory contains `AGENTS.md`, `writing/README.md`,
   `documents/README.md`, and the writing/document workspaces. Read those
   contracts first. Never inspect `scratch.md`.
2. Read `writing/voice/anti-ai-style-rules.md` when present. Treat it as a
   protected rule input, not as style evidence. Its avoidance rules have higher
   authority than learned patterns from AI-assisted approved prose.
3. Read the existing generated voice packs when present. Preserve useful
   historical nuance and any **Declared preferences** section verbatim unless
   the user explicitly asks to change it.
4. Enumerate Markdown files only under `writing/ready/`,
   `writing/published/`, and `documents/final/`. Do not list, search, count, or
   read files under `writing/drafts/` or `documents/drafts/`.
5. Analyse only reader-facing prose. For writing pieces, use only content
   between `<!-- publish:start -->` and `<!-- publish:end -->`. For internal
   documents in `documents/final/`, analyse the reader-facing body while
   ignoring private notes, metadata, and drafting residue.
6. Analyse blog and document corpora separately. Weight published blog work
   more strongly than ready blog work. Use final internal documents only for
   the document pack. Separate stable habits seen across pieces from topic,
   format, or genre-specific choices. Do not infer a confident rule from a
   single example.
7. Extract actionable positive style patterns for each pack: tone, stance,
   syntax and rhythm, diction, structure, transitions, openings, closings,
   rhetorical habits, formatting, and context variations. Use short examples
   only when they add precision; link them to eligible writing or final
   document files.
8. Incorporate the shared anti-AI rules into both generated packs. If corpus
   evidence appears to conflict with those rules, report the tension and keep
   the learned pattern only when it is clearly purposeful, specific, and
   consistent with the user's authored judgement.

## Update the voice packs

- Create missing packs from `templates/voice-pack.md` as a structural starting
  point; otherwise update them in place without erasing useful historical
  nuance.
- Before writing a newly generated pack over an existing pack, save the current
  file as the corresponding single rollback copy:
  `writing/voice/blog-voice-pack.backup.md`,
  `documents/voice/document-voice-pack.backup.md`, or
  `writing/voice/voice-pack.backup.md` for the compatibility mirror. Keep only
  one rollback copy per generated output. If the backup already exists, replace
  it; do not keep a chain of historical backups. Treat each new `$voice` run as
  confirmation that the current pack is satisfactory enough to become the new
  rollback point.
- Regenerate `writing/voice/voice-pack.md` as a compatibility mirror of
  `writing/voice/blog-voice-pack.md` until all writing templates and artefacts
  have moved to the canonical blog pack path.
- Keep observations concrete enough to guide drafting. Prefer “Use X under Y
  conditions” over vague labels such as “engaging” or “authentic.”
- Record coverage, confidence, eligible source counts, an evidence ledger, and
  what changed in this analysis pass for each generated pack.
- Mark a pack `provisional` when evidence is sparse or narrow. Never invent a
  style to fill gaps; state what cannot yet be learned.
- Append a `voice` entry to `writing/log.md`. If the current thread is an active
  DTM session, also add the updated packs to today's Daily Note References and
  record the action once.
- Run `python3 tools/writing.py lint` and `python3 tools/documents.py lint`
  before reporting completion.

If there is no eligible corpus, create or retain a provisional empty pack,
report that no style was inferred, and suggest moving representative human-
approved work to `writing/ready/`, `writing/published/`, or `documents/final/`
before invoking `$voice` again.
