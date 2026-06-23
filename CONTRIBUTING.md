# Contributing

Thank you for improving SecondBrain Framework.

## Before opening a pull request

1. Keep framework behaviour separate from personal vault content.
2. Never include real Daily Notes, wiki pages, sources, activity logs, project
   details, credentials, usernames, home-directory paths, or private links.
3. Use synthetic examples with unmistakably fictional data.
4. Update documentation and automation definitions alongside behavioural
   changes.
5. Run the validation commands below.

```sh
python3 -m py_compile framework/tools/*.py install.py
python3 -m unittest discover -s tests
tmpdir="$(mktemp -d)"
python3 install.py --vault "$tmpdir"
python3 "$tmpdir/tools/wiki.py" lint
python3 "$tmpdir/tools/dtm.py" lint
```

Pull requests should explain the motivation, user impact, privacy implications,
and validation performed. Prefer focused changes that can be rolled back
independently.
