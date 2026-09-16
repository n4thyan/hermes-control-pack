# Third-party material

Hermes Control Pack's own code and authored runtime instructions are MIT licensed.

## Primary bootstrap corpus

HCP can ingest external corpora, including:

- `asgeirtj/system_prompts_leaks` — https://github.com/asgeirtj/system_prompts_leaks

At HCP bootstrap time that repository declared CC0-1.0. A repository-level license or waiver from a collector does not necessarily establish ownership of every third-party text contained in a research corpus.

For that reason HCP does **not** vendor the raw source corpus by default. Users supply a local ZIP or checkout, and generated reports contain paths, hashes, counts, and aggregate signals rather than reproducing source passages.

## Runtime target

HCP is designed for:

- `NousResearch/hermes-agent` — https://github.com/NousResearch/hermes-agent

Hermes Agent is not bundled with this repository and remains under its own license and terms.

This file is informational, not legal advice.
