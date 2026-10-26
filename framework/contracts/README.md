# Component contracts, version 1

These contracts establish the Stage 2 data model. They do not select components, write installed state, render navigation, run validators, or change installation or publication behaviour yet. `tools/components.py` supplies deterministic semantic checks, called by `tools/contracts.py lint`; the three JSON Schema files describe the portable object shape. No third-party schema package is required by the live validator.

`component-manifest.schema.json` defines a component identity, dependencies, explicit source-to-installed-path mappings and ownership, workspace directories and seed files, navigation contributions, instruction/skill references, structured validator commands, configuration, optional automation templates, and prerequisites. `core` has no dependencies. Writing and Documents each require only Core. A private extension uses the same manifest shape as a public component. Sources and targets are relative POSIX paths. A component may reference only its own mapped instruction, skill, configuration, automation and validator targets; shared navigation is a contribution, not a right to edit the shared page. Arbitrary hooks and executable lifecycle scripts are not manifest fields.

`installed-state.schema.json` defines exact source revisions, installed component identities and recorded resources. Every `managed` or `seed-user` record must include the exact source path declared by its owning manifest for that installed destination. Generated resources and user data have no source mapping. `managed` and generated resources carry the last managed SHA-256; `seed-user` records the initial SHA-256 but remains user-editable; `user-data` carries no managed hash. A generated region records a core owner, region ID and renderer version. The future update planner must compare these values with local content and refuse unknown or modified destinations before changing them. This state schema grants no update or removal authority by itself.

`harness-inventory.schema.json` defines a derived adapter payload: installed component IDs, component-scoped instruction paths, component-scoped skill IDs and paths, and permission claims. `tools/components.py` derives it only from validated installed state and manifests; its comparison validator rejects added or altered entries. Permission claims name a component-owned file or workspace directory and request `read` or `write` access. They are descriptive metadata, not grants. The current harness has no mechanism to enforce these scopes or register only selected skills automatically; existing role and file-authority rules remain authoritative. Enforcement and registration must be verified when selective installation arrives.

The `start-here.md` region markers are exact standalone lines:

```markdown
<!-- secondbrain:capabilities:start -->
<!-- secondbrain:capabilities:end -->
```

There must be exactly one start and one end, in that order. Missing, duplicate, inline, reversed or nested markers fail validation. The current live `start-here.md` has no markers; this contract does not insert them. The future renderer must preserve all text outside the region byte for byte.

Public export entitlement remains external to manifests: `publication/manifest.json` is the current authoritative allowlist. The validator accepts a separate explicit public-component set and rejects public-to-private dependencies or source paths under private/secrets roots. A manifest cannot declare itself public. Stage 8 will integrate component-aware publication without weakening this independent allowlist.

`resource-ownership.json` records the Stage 1 classification against each allowlisted source. It distinguishes component owner from lifecycle ownership and flags the shared voice skill as unresolved until Stage 3. The exact publication destination remains in `publication/manifest.json`; the inventory avoids duplicating that authority. The inventory coverage check runs only in the live source tree, where the source paths exist. `component-examples.json` and `tests/fixtures/components/negative-cases.json` are synthetic examples, including the five requested profiles and failure cases. They are not active installed manifests.
