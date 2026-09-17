# Usage

## Recommended setup

Install once from anywhere:

```bash
cd hermes-control-pack
python -m pip install .
hcp setup --project /path/to/project
hcp doctor --project /path/to/project
```

After running `hcp setup`, HCP runtime assets live in your Hermes installation (`~/.hermes/`), global state lives under `~/.hermes/hcp/global/`, and you can **launch Hermes from any directory**:

```bash
cd C:\Users\pc
hermes
```

```bash
cd C:\Users\pc\Desktop\another-project
hermes
```

`hcp setup` does not require the research corpus. It installs the packaged runtime assets, enables `hcp-runtime` when the Hermes CLI is available, merges the balanced SOUL overlay, initializes `.hcp/state`, and installs/selects `hcp-continuity`.

Useful variants:

```bash
# Keep Hermes' normal compressor
hcp setup --project . --no-context-engine

# Use coder SOUL overlay
hcp setup --project . --soul coder

# Keep existing SOUL completely untouched
hcp setup --project . --no-soul

# Also install the generic project .hermes.md fallback
hcp setup --project . --project-context
```

For a non-default Hermes profile/home:

```bash
hcp setup --project . --hermes-home /path/to/hermes/home
```

HCP passes the same `HERMES_HOME` to Hermes CLI enable/config commands, so setup does not accidentally configure a different profile.

## Verifying after installation

After setup, verify HCP is active and cwd-independent:

```bash
hcp doctor --hermes-home ~/.hermes
```

Check that HCP runtime assets are under `~/.hermes/` and global state lives under `~/.hermes/hcp/global/` — **not** inside the HCP clone.

## Advanced/manual install

`hcp install` exposes individual layers. When `--build` is omitted it uses runtime assets packaged with HCP:

```bash
hcp install --project . --soul balanced --context-engine --select-context-engine --enable-plugin
```

Install from a reproducible corpus build instead:

```bash
hcp build /path/to/corpus.zip --out build/hcp
hcp install --build build/hcp --project . --soul balanced
```

Project `.hermes.md`, skills, bundles, and plugins are protected from unrequested replacement. Use `--force` to back up and replace differing HCP-managed files. SOUL is handled differently: HCP owns only a marked managed block and preserves user-authored text around it.

## State commands

```bash
hcp state show --project .
hcp state show --project . --scope task
hcp state show --project . --scope evidence
hcp trace --project . --limit 50
```

Manually patch task/project state when useful:

```bash
hcp state set --project . --scope task --json '{"objective":"Finish renderer","phase":"VERIFY"}'
```

## Research commands

```bash
hcp scan corpus.zip
hcp analyze corpus.zip
hcp mechanisms corpus.zip
hcp build corpus.zip --out build/hcp
```

These commands are for corpus research/recompilation and are not required for runtime setup.

## Reverting the context engine

```bash
hermes config set context.engine compressor
```

The installed HCP engine/plugin files can remain present while inactive.
