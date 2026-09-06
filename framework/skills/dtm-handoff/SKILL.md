---
name: dtm-handoff
description: Hand completed work from a non-DTM SecondBrain thread to the active DTM thread for Daily Note capture without modifying the Daily Note directly.
---

# DTM Hand-Off

Use this skill when the current thread is not an explicitly DTM-activated
thread and the user wants completed work, progress, decisions, blockers, or
follow-up items passed back to the active Daily Note manager.

## Hard boundaries

- Do not create, edit, append to, reorder, or otherwise modify `daily/` files.
- Do not run `python3 tools/dtm.py open`, `python3 tools/dtm.py activity`, or
  any direct Daily Note write command.
- Do not activate DTM in the current thread. This skill is a hand-off mechanism,
  not a DTM session.
- Do not create a DTM thread automatically. If the active DTM thread cannot be
  found, stop and tell the user.

## Find the active DTM thread

1. Use the available Codex thread-management tools. If they are not already
   loaded, first search for the thread tools, especially `list_threads` and
   `send_message_to_thread`.
2. Search recent threads for the exact current-day title `DTM YYYY-MM-DD`, using
   the user's local date for `YYYY-MM-DD`.
3. Choose only a live, accessible Codex thread whose title exactly matches that
   current-day DTM title. If there is no exact match, or there are multiple
   plausible matches that cannot be disambiguated safely, stop and explain the
   problem to the user.

## Build the hand-off

Summarise outcomes rather than the chat transcript. Include only information
that the DTM thread may need to update the Daily Note accurately:

- tasks completed;
- progress against existing tasks;
- new tasks identified;
- blockers or dependencies discovered;
- decisions made;
- significant findings or conclusions;
- important context worth retaining;
- follow-up work required;
- artefacts created or changed, with paths or links where relevant;
- suggested Daily Note capture points, clearly labelled as suggestions.

Keep the hand-off concise but operationally complete. Mention verification
performed and any verification that could not be run.

## Incremental checkpoint

On the first successful invocation in a work thread, hand off all relevant work
completed in that thread so far.

On later invocations in the same thread, hand off only new or materially changed
information since the previous successful hand-off. Use the last successful
hand-off message in this thread as the checkpoint. After `send_message_to_thread`
succeeds, preserve a compact checkpoint in the originating thread's response or
thread summary context containing:

- the DTM thread title and thread id used;
- the successful hand-off time;
- the exact scope covered by the hand-off;
- any material items intentionally not handed off.

If locating the DTM thread fails, sending the message fails, or the hand-off is
ambiguous enough that you stop for user input, do not advance the checkpoint.

## Send the hand-off

Send a single follow-up prompt to the DTM thread. Use this shape:

```markdown
DTM hand-off from a non-DTM work thread.

Originating thread: <brief title or task description>
Coverage: <all work so far | changes since previous successful hand-off at HH:MM>

Outcomes:
- ...

Daily Note implications for you to assess:
- ...

Verification:
- ...

Open points:
- ...
```

End the current thread's response by stating whether the hand-off was sent. Do
not claim the Daily Note was updated; the receiving DTM thread owns that step.
