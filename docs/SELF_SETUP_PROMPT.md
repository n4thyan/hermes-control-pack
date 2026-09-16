# Let Hermes install HCP for itself

If you already have Hermes Agent running and do not want to follow the manual install steps, paste the prompt below into Hermes.

```text
Set up Hermes Control Pack for this Hermes installation using the official project repository:
https://github.com/n4thyan/hermes-control-pack

Do the setup yourself end to end. Read the repository README and relevant installation/compatibility documentation first, inspect this Hermes installation and current working environment, then install the latest stable HCP version using the repository's documented method.

Requirements:
- Preserve and back up any existing SOUL.md, .hermes.md, skills, bundles, plugins, config, or other user customizations before replacing or merging anything.
- Do not delete unrelated user data or project files.
- Prefer HCP's supported plugin/integration path over patching Hermes core.
- Install the recommended HCP runtime assets, skills, bundles, and default balanced SOUL/profile where applicable.
- If HCP needs a research corpus for optional analysis/build features, do not block the basic runtime installation when the corpus is not present.
- Run HCP's validation/doctor checks after installation.
- Verify Hermes can see the installed HCP skills/bundles and that the integration loads without errors.
- If something fails, diagnose and repair it rather than stopping at the first error.
- At the end, give me a concise report of what was installed, what was backed up, what verification passed, and any optional features that remain unconfigured.
```

This prompt intentionally tells Hermes to inspect the current repository documentation instead of relying on a hard-coded command sequence, so it remains useful as HCP installation evolves.
