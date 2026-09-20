# Behavioural fixtures

Each fixture is a synthetic vault plus an expected safe outcome. An adapter runs
the prompt against the `initial/` tree, records observable reads, writes, and
structured events, then calls `evaluate()` from `tests/behavioural_fixtures.py`
against the resulting tree. The evaluator checks safety boundaries, not prose.

`observed-pass.json` is a reference safe trace used by the framework regression
tests. It is not a model answer or a golden-text response.
