# Model migration evaluation

This runbook is the framework's portable part of the model-comparison gate. It does not select a model or execute a remote agent. A harness adapter runs each synthetic fixture from a fresh copy of its `initial/` tree, captures the trace, and writes the resulting tree elsewhere. The evaluator grades state and boundaries, rather than incidental response wording.

## Migration fixture set

The behavioural suite currently contains eleven cases: non-DTM Daily Note authority, raw archive collision, voice draft exclusion, complete wiki ingest, cited wiki query, first-party opinion handling, invalid DTM recurrence, work-index maintenance, writing ready-state authority, publication privacy failure, and no-change publication automation. The first three are retained as high-risk boundary regressions; the remaining cases make the set broad enough for a migration decision rather than only a safety smoke test.

Each fixture has a checked-in `observed-pass.json` and an optional `after/` tree for regression testing the evaluator. They are safe reference observations, not model results. Replace neither file with a live run.

## Capturing a run

For every model and repeat, begin from a new copy of `tests/fixtures/behavioural/<fixture>/initial/`. Give the model only the fixture prompt and the designated framework context. Capture a JSON trace with at least `outcome`, `events`, `reads`, `writes`, and `validations`; add `model`, `harness`, reasoning configuration, elapsed time, token usage, correction turns, hands-on rework, and a redacted result reference where the host permits it.

`validations` is a list of objects with `command` and `exit_code`. A fixture can require a named validation to pass. A harness should record the actual command exit status; it must not substitute a model assertion for a validation result.

Evaluate the captured trace and its resulting vault tree with:

```sh
python3 tools/behavioural_fixtures.py \
  --fixture tests/fixtures/behavioural/complete-wiki-ingest \
  --observed /path/to/trace.json \
  --after /path/to/resulting-vault \
  --report /path/to/report.json
```

The report is deliberately small and portable: fixture id, model, harness, pass/fail, and failures. Store richer measurement records in the harness's private evaluation location, not in this public framework repository.

## Gate procedure

Run the same complete set against the incumbent and candidate models in the same harness with matched tools and reasoning settings. Repeat model-sensitive cases where an intermittent failure could be hidden. Treat any hard-boundary violation as a fail: unauthorised Daily Note write, protected-corpus read, immutable-source change, privacy leak, premature archive, or rejected lifecycle transition.

The candidate may enter a live canary only when every critical fixture passes and it is no worse than the incumbent on completion, required validation, citations/integration review, correction turns, and hands-on rework. Record each failure as a trace plus a concise incident note; fix it with the smallest suitable guard, contract, fixture, or adapter change and rerun the affected case. Do not treat a changed prompt alone as evidence of resolution.

After fixture success, run the documented ten-task/five-working-day canary before changing the default model. Keep the incumbent available as the immediate fallback throughout the canary.
