# Usage

## Install from GitHub

```bash
git clone https://github.com/n4thyan/hermes-control-pack.git
cd hermes-control-pack
python -m pip install .
```

Python 3.11+ is required.

## Build from the upstream corpus

Use either a ZIP or a checked-out directory:

```bash
hcp build ~/Downloads/system_prompts_leaks-main.zip --out build/hcp
```

or:

```bash
hcp build ~/src/system_prompts_leaks --out build/hcp
```

A build contains the corpus metadata index, coverage reports, execution kernel, skills, bundles, and a deterministic artifact manifest.

## Install into a project

```bash
hcp install --build build/hcp --project ~/src/my-project
```

This installs:

- `~/src/my-project/.hermes.md`
- HCP skills under `${HERMES_HOME:-~/.hermes}/skills/`
- HCP bundles under `${HERMES_HOME:-~/.hermes}/skill-bundles/`

Existing differing files are protected. Use `--force` to create timestamped backups and replace them.

### Keep an existing `.hermes.md`

```bash
hcp install --build build/hcp --project ~/src/my-project --no-context
```

You can then manually incorporate the parts of HCP's generated `.hermes.md` that fit your project.

### Install only context

```bash
hcp install --build build/hcp --project ~/src/my-project --no-skills --no-bundles
```

## Validate a build

```bash
hcp doctor --build build/hcp --project ~/src/my-project
```

`doctor` checks Python compatibility, build structure, Hermes CLI visibility, and target paths. Hermes itself is optional for compiling/scanning, but required to use the installed pack.

## Analyze without installing

```bash
hcp scan corpus.zip --out corpus-index.json
hcp analyze corpus.zip --out RESEARCH_SIGNALS.md
```

`scan` writes detailed metadata for every corpus file. `analyze` writes aggregate cross-source signal coverage without reproducing source passages.

## Use the bundles in Hermes

After installation, start Hermes inside the project and invoke a bundle:

```text
/hcp-coding implement the requested feature and verify it end to end
/hcp-debug find the root cause of this failing login flow
/hcp-ui match this screen to the provided reference and test the interactions
/hcp-afk finish the remaining in-scope work while I am away
/hcp-research investigate the current API behavior and cite primary sources
```

You can also load individual HCP skills directly with their slash-command names.

## Updating HCP

Pull the repository, reinstall the Python package, rebuild against the latest local corpus, then reinstall with `--force` if HCP-managed runtime files changed:

```bash
git pull
python -m pip install . --upgrade
hcp build /path/to/latest-corpus.zip --out build/hcp
hcp install --build build/hcp --project /path/to/project --force
```

Backups are created before differing installed HCP files are replaced.
