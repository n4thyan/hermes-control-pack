# Hermes compatibility

HCP targets the current Hermes Agent architecture documented by Nous Research.

## Surfaces HCP intentionally uses

- **Project context:** `.hermes.md` / `HERMES.md` is Hermes' highest-priority project context type.
- **Global personality:** HCP does **not** replace `SOUL.md`; personality remains user-controlled.
- **Skills:** installed under `~/.hermes/skills/` (or the active `HERMES_HOME`).
- **Skill bundles:** installed under `~/.hermes/skill-bundles/`.
- **Delegation:** HCP's orchestration rules assume Hermes can delegate/subagent independent work when the active runtime/toolset exposes that capability.
- **Built-in planning:** Hermes has a built-in `/plan`, so HCP does not ship a duplicate planning skill.

## Compatibility philosophy

HCP avoids patching Hermes internals. It uses public extension surfaces — project context, skills, bundles, and ordinary CLI/file installation — so Hermes can continue to update independently.

If Hermes changes a public path/schema, update HCP's installer/assets and tests rather than pinning to private internals.

## Reference

Official documentation: https://hermes-agent.nousresearch.com/docs/
