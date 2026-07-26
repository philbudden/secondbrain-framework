---
name: resolve-document-items
description: Work through unresolved items in a specified document through a structured, non-adversarial question-and-answer workflow. Use when the user invokes `$resolve-document-items` or explicitly asks to close open questions, unowned tasks, incomplete actions, assumptions, or pending decisions in a document one item at a time, updating the source document only when the user's answer resolves, assigns, confirms, changes, or explicitly records deferral for an item.
---

# Resolve Document Items

Use this skill to help close open loops in an existing document calmly and efficiently. The goal is document completion, not idea exploration, red-team review, or Socratic challenge.

## Core Behavior

- Read the specified source document before asking questions.
- Identify unresolved open questions, unowned tasks, incomplete actions, assumptions needing confirmation, stale placeholders, and decisions still required.
- Work through items one at a time.
- Ask exactly one primary question at a time.
- Wait for the user's answer before moving to the next item.
- Ask a brief follow-up only when the answer is ambiguous, incomplete, internally inconsistent, or not enough to update the document accurately.
- Avoid challenging the user's reasoning unless the document cannot be updated safely without clarifying a real contradiction.
- Update the source document as soon as an answer resolves an item, assigns ownership, confirms a decision, changes action status, or records a user-requested deferral.
- Leave the source document unchanged when the user explicitly defers an item without asking for the deferral to be recorded.
- Continue until every identified item is resolved, updated, assigned, or explicitly deferred.

## Distinction From Interview Skills

This skill is not a thought-development interview. Do not use it to test the user's assumptions, deepen their argument, generate new ideas, or pressure-test strategy. Use the minimum question needed to make the document more complete and actionable.

If a user appears to want exploration rather than close-out, ask whether they want this skill or a separate thinking/interview workflow. If they ask to resolve document items, stay practical.

## Workflow

1. Confirm the document path or identify the named document from the current workspace.
2. Read the document and any directly necessary local context, such as a linked index entry or project page that defines statuses or ownership conventions. Do not broaden into unrelated research.
3. Build a short internal queue of outstanding items. Prefer items already visible in headings, tables, checklists, `TBC`, `TODO`, `Open questions`, `Next actions`, `Assumptions`, `Risks`, `Decisions`, and owner/status columns.
4. Start with the item that is most blocking, easiest to resolve, or nearest to the document's current operating purpose. If no order is obvious, use document order.
5. Ask one focused question that makes clear:
   - which item is being resolved;
   - what answer format would let the document be updated;
   - whether the likely update is a decision, owner, action, status, assumption confirmation, or deferral.
6. After the user answers, decide whether the answer is document-ready.
7. If document-ready, update the source document immediately and tell the user briefly what changed.
8. If not document-ready, ask one brief follow-up that names the missing piece.
9. If deferred, leave the source document unchanged unless the user asks to record the deferral.
10. Move to the next item and repeat until the queue is closed or the user stops.

## Question Style

Ask narrow, answerable questions. Prefer:

- "For this open query, should the owner be Philip, Ben, another named person, or left unassigned for now?"
- "Can I mark this as resolved with the decision that the Kanban board remains the live delivery view and the project note is only a periodic snapshot?"
- "Should this action stay open, move to blocked, or be removed because it is no longer required?"
- "Is this assumption now confirmed, or should I leave it as an explicit assumption?"

Avoid:

- "Are you sure?"
- "What are the second-order consequences?"
- "Defend this decision."
- "Let's explore your underlying mental model."
- Multi-part questions that require the user to resolve several items at once.

## Updating The Document

When updating, preserve the document's existing style, structure, and status vocabulary. Make the smallest change that accurately captures the answer.

Common update patterns:

- Replace `TBC` with the confirmed value.
- Add or update an owner in a table.
- Move an action from open to blocked, completed, or deferred if the document has those statuses.
- Remove an open question only when the answer has been integrated into the relevant section.
- Add a concise decision bullet when the document has a decision section.
- Add a short note to an item when the user asks for a deferral or uncertainty to be recorded.

Do not silently rewrite large sections while resolving one item. If an answer implies a broader restructure, say so and ask whether to make that broader edit after the current item is handled.

## Progress Reporting

Keep progress visible but lightweight. After each update, use a short confirmation such as:

`Updated: assigned the workbook review-rhythm action to Philip and left Ben as consulted. Next item: the unresolved safeguarding mapping ownership.`

When the queue is complete, give a concise summary of:

- items resolved;
- items assigned;
- decisions confirmed;
- items explicitly deferred;
- any remaining blockers the document still shows.

## DTM Compatibility

If this skill is invoked inside an active `$dtm` thread, remain within the DTM workflow. Capture substantive document changes in today's Daily Note before closing out. For project, work, writing, or document workspace changes, run the relevant local lint command when one exists.
