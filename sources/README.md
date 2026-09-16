# Corpus sources

Raw research corpora are intentionally not tracked in this repository.

Recommended local layout:

```text
sources/
  private/
    system_prompts_leaks-main.zip
```

Then run:

```bash
hcp build sources/private/system_prompts_leaks-main.zip --out build/hcp
```

Primary bootstrap corpus: https://github.com/asgeirtj/system_prompts_leaks

`sources/bootstrap-source-lock.json` records aggregate metadata and the exact SHA-256/fingerprint of the bootstrap archive used for the repository's initial reports. It contains no raw prompt text.
