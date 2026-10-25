# Component ownership and integration map

This Stage 1 map describes the **intended owner** of currently distributed resources, without changing the current all-in-one installation. `framework/contracts/resource-ownership.json` is the machine-checkable inventory: each `publication/manifest.json` source has a rule, and more specific overrides classify mixed directories. The allowlist supplies the exact source-to-public-path mapping. A directory rule applies to every contained file, including new files, until an explicit override changes it. `python3 tools/contracts.py lint` expands the rules and verifies coverage of all allowlisted files.

## Boundaries

| Owner | Distributed sources and installed destinations | Lifecycle and dependency notes |
|---|---|---|
| Core | `AGENTS.md`, `DTM.md`, `contracts/`, `tools/{wiki,dtm,workspaces,contracts,components,task_envelopes}.py`, DTM defaults, generic templates, base skills, and the three allowlisted `.obsidian` defaults. The public exporter maps these under `framework/`; the current installer maps them to vault-root equivalents. | Code, contracts and instructions are framework-managed. `.obsidian` settings and recurring task configuration are seed-once/user-editable. Knowledge, Daily Notes, `projects/` and `work/` are user-owned data, even though Core owns their generic tools and workflows. |
| Writing | `tools/writing.py`, writing and voice templates, writing publisher and weekly diary automation definitions, and Writing empty-vault seeds. | Editorial lifecycle and voice belong here. `writing/index.md` is curated after seeding; articles and voice evidence are user-owned. Does not depend on Documents in the target. |
| Documents | `documents/README.md`, `tools/{documents,document_deliverables,decks}.py`, `tools/marp-chrome`, document/deck templates and theme, document-related skills, and Documents empty-vault seeds. | Canonical Markdown, document index and deliverables belong here. `documents/index.md` is curated after seeding; canonical content remains user-owned. PDF/DOCX/Marp/browser prerequisites are Documents-specific rather than Core imports. |
| Distribution/development | `publication/repository/` outside the empty-vault seeds, `tests/`, `publication/manifest.json`, exporter/publisher and behavioural-fixture tool, and framework publication automation definition. | These are public repository or publication infrastructure. Several are copied into installed vaults by the current broad installer; that is a later-stage placement issue, not a reason to call them Core runtime. Public export remains independently allowlisted. |
| Unresolved transitional owner | `skills/voice/` (skill and harness registration). | It currently spans Writing and Documents. Stage 3 must split capability-specific evidence and instructions or extract a genuinely neutral helper; it must not make one capability depend on the other. |

The inventory classifies every distributed file by its parent rule or a specific override. `publication/repository/examples/empty-vault/` is seed-once Core scaffolding with Writing and Documents subtree overrides. `tests/` and other repository-only files are inventoried as development resources, not installed capabilities. No private extension source is present in the public allowlist; a private component uses the same contract but requires separately controlled source and publication authority.

## Existing dependencies to remove in Stage 3

- `AGENTS.md` and `DTM.md` are Core-owned entry instructions but currently contain substantial Writing and Documents workflow sections. They cannot yet be used as Core-only instructions without optional references.
- `tools/writing.py` counts `documents/final/*.md` in voice-pack validation. `skills/voice/` reads both approved corpora. Documents guidance references `writing/voice/` assets. These are current cross-capability dependencies, not target dependencies.
- `templates/voice-pack.md` currently refers to Writing's anti-AI rules. Its exact split is part of Stage 3, alongside the shared voice skill.
- The distributed `framework/defaults/documents/README.md` comes from the live `documents/README.md` and contains Writing voice references. Do not copy those references into a Documents-only installation in later stages.

## Shared integration points and authority

| Point | Current evidence | Contract owner and later-stage rule |
|---|---|---|
| `start-here.md` | The live page contains authored navigation and links to both optional workspaces; it has no generated-region markers. The empty-vault example does not supply it. | Core owns one proposed `<!-- secondbrain:capabilities:start -->` / `end` region. Components may contribute validated entries only. Stage 6 must reconcile the personalised page before inserting markers; user text stays outside the region. |
| Workspace indexes | `work/index.md` and `projects/index.md` are curated by Core's `workspaces.py`; `writing/index.md` and `documents/index.md` are curated by their domain tools. | Seed-once/user-owned indexes. Component install must not regenerate or overwrite their edited contents. |
| Instruction/skill discovery | Current `AGENTS.md`, `DTM.md`, skills and harness YAML are copied together by the installer. | Core owns discovery/composition; each optional component owns its instruction and skill entries. The manifest declares paths; a later harness adapter applies only installed entries. |
| Configuration and automation | `.obsidian` defaults are public allowlisted, while only selected files are exported. Automation definitions are templates, separate from scheduler activation. | Core owns shared configuration boundaries; components declare configuration and optional automation resources. Merely installing a definition never activates an automation. |
| Validation | Existing `tools/contracts.py` lints behavioural contracts; workspace/domain tools lint their own content. | Core owns contract validation and dispatch. Each component declares structured validator references; Stage 5+ scopes execution to the installed set. |

The Stage 2 fixtures model these interfaces only. Their prospective Writing/Documents instruction paths are synthetic and do not assert that Stage 3 extraction has happened.
