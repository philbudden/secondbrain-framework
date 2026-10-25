# Modularisation baseline: Stages 0–2

Recorded 2026-10-19 before the Stage 1–2 implementation. This is an implementation baseline, not a release or a claim that the target architecture is installed.

## Source and publication authority

The live Git-free vault is the canonical source for `AGENTS.md`, `DTM.md`, `contracts/`, `tools/`, `templates/`, distributed skills and automation definitions. `publication/manifest.json` is the explicit source-to-public-export allowlist. `tools/export_framework.py` stages and privacy-checks it; the scheduled `tools/publish_framework.py` workflow alone operates the separate Git checkout. `publication/repository/` provides static public repository files and the empty-vault example. The public `install.py` currently copies the whole `framework/` subtree and example into a destination vault, preserving existing files unless `--force` is used. There is no installed-component state or selective installation.

## Revisions and divergence

- The separate public checkout was clean but was not a reliable mirror of current public `main`; no reconciliation was attempted at this baseline.
- The prior publication had merged and no publication pull request was open at baseline. Local and public histories had diverged, including framework guidance, a distributed skill, a regression test, and changelog content.
- A pre-increment sanitized export staged successfully. Because the local checkout was not current `main` and existing differences remained, publication no-op equivalence was not established. The dated changelog history was retained.

## Pre-change checks

| Check | Baseline result |
|---|---|
| Live behavioural inventory and task-envelope lint | 17 behaviours, 0 errors/warnings; envelope contract 0 errors |
| Live unit tests | 8 passed |
| Live wiki, DTM, and project/work lint | All relevant checks completed without errors or warnings |
| Live Writing and Documents lint | All checks completed; one pre-existing writing voice-pack coverage warning remained |
| Staged public suite and clean installation | 20 tests passed; clean-vault install plus contract, wiki and DTM lint passed |
| Recovery baseline | An independent recovery copy was confirmed before this increment. This satisfies the recovery-copy requirement; no further backup verification or restore-procedure documentation is required for this increment. |

The recovery baseline is satisfied by the user's confirmation. Public-main divergence matters before later publication changes. This increment only adds contracts, fixtures, validation and documentation; it does not alter the installer, publisher, live navigation or user content.
