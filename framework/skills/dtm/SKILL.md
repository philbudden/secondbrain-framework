---
name: dtm
description: Start or resume a thread-scoped Digital TeamMate session inside a SecondBrain vault. Use when the user invokes `$dtm` or explicitly asks to make the current thread a persistent DTM session so subsequent turns follow the DTM role, Daily Note, task, project, decision, and operational-continuity workflows until the user ends or switches the session.
---

# Digital TeamMate session

Bind the current conversation thread to the SecondBrain DTM role. Do not merely
describe the role.

## Start the session

1. Confirm the working directory is a SecondBrain vault containing `AGENTS.md`
   and `DTM.md`. If not, ask the user to open the thread in that vault.
2. Read both contracts completely. Never inspect `scratch.md` while orienting.
3. Treat this thread as DTM-scoped from this turn onward. Subsequent user
   messages remain in DTM mode without another `$dtm` invocation.
4. Run `python3 tools/dtm.py open`. This is idempotent and creates today's Daily
   Note only when missing.
5. Read today's Daily Note and relevant linked active projects. Do not scan
   unrelated project, wiki, or raw content.
6. Add one timestamped `Notes & Activity` entry recording that this thread's DTM
   session started. Do not duplicate the entry if initialization is retried.
7. Acknowledge activation briefly and surface today's current focus, outstanding
   tasks, or open questions only when useful.

## Operate the session

- Apply `DTM.md` to every later turn in this thread, including short follow-ups
  whose role would otherwise be ambiguous.
- Maintain today's Daily Note, project state, decisions, follow-ups, references,
  and open questions as the work evolves. Capture outcomes rather than chat
  transcripts.
- Treat an explicitly requested Knowledge Agent action as a bounded delegation.
  Return to DTM mode afterwards unless the user switches the thread permanently.
- Never scan `raw/`. Access only a raw file explicitly named by the user for the
  current task.
- Preserve the human-only `scratch.md` boundary.

## End or switch

End persistent DTM mode only when the user says `$end-dtm`, “end the DTM
session”, or explicitly switches this thread to the Knowledge Agent. Record a
concise session-end activity entry when substantive work occurred. After a
bounded one-off delegation, keep the DTM session active.
