# Contributing

Contributions are welcome when they improve Hermes behavior in a **transferable, testable** way.

## Setup

```bash
git clone https://github.com/n4thyan/hermes-control-pack.git
cd hermes-control-pack
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Runtime-rule contributions

When proposing a new kernel rule, skill, or bundle:

1. describe the concrete failure mode it addresses;
2. explain why the mechanism transfers to Hermes rather than depending on another product's private tool/UI behavior;
3. keep source facts distinct from your interpretation;
4. provide an observable verification criterion;
5. avoid copying long source passages into HCP.

If you add/change a top-level `skills/` or `bundles/` asset, mirror the same file under `src/hermes_control_pack/runtime/`. `tests/test_compiler.py` enforces parity so wheel installs cannot silently lose runtime assets.

## Corpus handling

Do not commit:

- raw prompt corpus ZIPs/checkouts;
- credentials or private user data;
- generated `build/` output;
- third-party text merely because it was present in a research corpus.

Aggregate reports, paths, hashes, counts, and original HCP syntheses are preferred.

## Required checks

```bash
python -m compileall -q src/hermes_control_pack
python -m unittest discover -s tests -v
hcp --version
```

For compiler/installer changes, also build against a small fixture or your local corpus and inspect the emitted manifest/report.
