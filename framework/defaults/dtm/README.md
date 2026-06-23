# DTM configuration

The Digital TeamMate's behaviour is defined in [[DTM|DTM.md]]. This folder
contains machine-readable operational configuration.

## Recurring tasks

Edit `recurring-tasks.json` to manage routines. The included examples are
disabled so the DTM does not silently create commitments you have not chosen.
Set `enabled` to `true` when a rule is wanted.

Supported schedule examples:

```json
{"frequency": "daily"}
{"frequency": "weekly", "weekdays": ["Monday", "Friday"]}
{"frequency": "monthly", "day": 1}
{"frequency": "monthly", "day": "last"}
```

Areas determine the destination section: `personal`, `professional`, or
`schedule`. Rule IDs must remain stable and unique.
