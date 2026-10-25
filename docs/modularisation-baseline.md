# Modularisation baseline: Stages 0–2

Recorded 2026-10-19 before the Stage 1–2 implementation. This is an implementation baseline, not a release or a claim that the target architecture is installed.

## Source and publication authority

The live Git-free vault is the canonical source for `AGENTS.md`, `DTM.md`, `contracts/`, `tools/`, `templates/`, distributed skills and automation definitions. `publication/manifest.json` is the explicit source-to-public-export allowlist. `tools/export_framework.py` stages and privacy-checks it; the scheduled `tools/publish_framework.py` workflow alone operates the separate Git checkout. `publication/repository/` provides static public repository files and the empty-vault example. The public `install.py` currently copies the whole `framework/` subtree and example into a destination vault, preserving existing files unless `--force` is used. There is no installed-component state or selective installation.

## Revisions and divergence

- The separate local public checkout was clean on `automation/framework-sync-2026-w43-2e9e5d20` at `619f17dee80c937bd30291293c74865f7303b91c`. Its cached `origin/main` was `b0d856cabe92cc182134e6fa2d7c8fd4d57e1c2e`; the GitHub API reported current public `main` as `28fe38d4bfbc520886d1d7b720aa1eff8b79db1d`. The local checkout/ref was therefore not a reliable mirror of current public `main`.
- Publication PR #19 had merged at 2026-10-19 09:53 UTC. The open-PR listing was empty at baseline. The local checkout branch and current public `main` diverged by one commit each; comparison listed `CHANGELOG.md`, `framework/DTM.md`, the PDF-to-Markdown skill pair, and `tests/test_task_envelopes.py`. No reconciliation was attempted.
- A pre-increment sanitized export staged successfully with digest prefix `2b518e835a3b`. Relative to the local checkout, only `CHANGELOG.md` and `framework/tools/documents.py` differed, reflecting the prior reference-document task. Because the local checkout was not current `main` and these differences already existed, publication no-op equivalence was not established. The dated changelog history was retained.

## Pre-change checks

| Check | Baseline result |
|---|---|
| Live behavioural inventory and task-envelope lint | 17 behaviours, 0 errors/warnings; envelope contract 0 errors |
| Live unit tests | 8 passed |
| Live wiki, DTM, and project/work lint | 390 wiki pages, 118 Daily Notes, 4 projects and 102 work notes; 0 errors/warnings |
| Live Writing and Documents lint | Writing: 33 pieces, 0 errors, 1 existing warning (`voice-pack.md` ready-source count 1 versus eligible corpus 2); Documents: 9 documents and 2 deck sources, 0 errors/warnings |
| Staged public suite and clean installation | 20 tests passed; clean-vault install plus contract, wiki and DTM lint passed |
| Recovery baseline | The user authoritatively confirms that the vault is suitably backed up. They created `SecondBrainV2.zip` before this increment and copied it from iCloud Drive to the iPad's local, non-iCloud storage while the NAS is unavailable. This satisfies the independent recovery-copy requirement; no further backup verification or restore-procedure documentation is required for this increment. |

The recovery baseline is satisfied by the user's confirmation. Public-main divergence matters before later publication changes. This increment only adds contracts, fixtures, validation and documentation; it does not alter the installer, publisher, live navigation or user content.
