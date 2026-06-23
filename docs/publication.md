# Publication and versioning

## Safety properties

- The live vault is never a Git repository.
- Export starts from an explicit manifest, not an ignore file.
- Personal content paths are denied even if accidentally allowlisted.
- Staged text is scanned for home paths, email addresses, and live-vault
  identifiers before touching the public checkout.
- The target must be a separate Git checkout outside iCloud.
- A no-change export creates no branch, commit, or pull request.

## Weekly flow

The publisher fetches and fast-forwards the public repository's default branch,
builds a sanitized staging tree, and compares its content fingerprint. When a
meaningful diff exists it creates a fingerprinted weekly branch, validates the
export, commits, pushes, and opens an assigned draft pull request. Re-running
the same export reuses the branch or existing pull request. If an earlier
framework publication PR is still open, the run defers rather than creating a
stack of noisy or competing reviews.

## Review and promotion

Review the generated PR with special attention to the privacy boundary,
contracts, automation behaviour, and install output. Merge only intentional
changes. Release tags should use semantic versioning and summarize migration
requirements in the changelog.

## Rollback

Do not use Git directly in a live synchronized vault. Instead:

1. identify the last known-good tag or commit in the public repository;
2. check it out in the separate repository clone;
3. preview restoration with `python3 install.py --vault /path --dry-run`;
4. restore only reviewed framework files, using `--force` deliberately;
5. validate the live system and record the rollback in its system log.

Personal knowledge remains outside this version history and is unaffected.
