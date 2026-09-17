# Let Hermes install HCP for itself

If Hermes Agent is already running and you do not want to follow the manual setup steps, paste this prompt into Hermes:

```text
Set up Hermes Control Pack for this Hermes installation using the official project repository:
https://github.com/n4thyan/hermes-control-pack

Do the setup yourself end to end. Read the repository README and relevant installation/compatibility documentation first, inspect this Hermes installation and current working environment, then install the latest stable HCP version using the repository's documented method. Use `hcp setup` when the installed version provides it.

Requirements:
- Preserve and back up any existing SOUL.md, .hermes.md, skills, bundles, plugins, config, or other user customizations before replacing or merging anything.
- Do not delete unrelated user data or project files.
- Prefer HCP's supported plugin/integration path over patching Hermes core.
- Install the recommended HCP runtime assets, skills, bundles, managed balanced SOUL overlay, persistent state, and continuity integration where supported.
- A prompt-research corpus is optional for analysis/recompilation and must not block the normal runtime installation.
- Run HCP's doctor/validation checks after installation.
- Verify Hermes can see the installed HCP integration without errors.
- Important: After installation, verify that HCP is ambient and cwd-independent:
  1. Check that HCP runtime assets are installed under HERMES_HOME (e.g., `~/.hermes/plugins/hcp-runtime/`, `~/.hermes/skills/`, `~/.hermes/skill-bundles/`).
  2. Confirm global state lives under `~/.hermes/hcp/global/` (NOT inside the HCP clone).
  3. The HCP Git clone should not be required to be the current working directory for HCP to function.
- If something fails, diagnose and repair it rather than stopping at the first error.
- At the end, give me a concise report of what was installed, what was backed up, what verification passed, and any optional features that remain unconfigured.
```

The prompt intentionally tells Hermes to inspect the current repository documentation rather than relying on a permanently hard-coded command sequence.
