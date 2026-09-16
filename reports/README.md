# Bootstrap reports

These reports were generated from the bootstrap `system_prompts_leaks` archive identified by `sources/bootstrap-source-lock.json`.

They contain aggregate counts and hashes only — no raw captured prompt passages.

- `bootstrap-corpus-coverage.md` — file/source-family and behavior-signal totals.
- `bootstrap-research-signals.md` — cross-source breadth for each behavior family.

Regenerate from your own corpus snapshot with:

```bash
hcp build /path/to/corpus.zip --out build/hcp
```
