# Security policy

## Supported version

Security fixes target the current `main` branch and latest release line.

## Reporting

For ordinary non-sensitive defects, open a GitHub issue.

Do **not** paste API keys, tokens, private corpora, credentials, or user data into public issues. If a vulnerability requires sensitive reproduction material, use GitHub's private vulnerability reporting feature when enabled for the repository, or contact the repository owner privately through an appropriate GitHub-supported channel.

## Threat model

HCP processes untrusted research corpora as **data**. The compiler does not execute corpus files. It reads bytes, attempts UTF-8 decoding for known text extensions, hashes files, and performs deterministic phrase counting.

HCP intentionally does not:

- execute scripts from the supplied corpus;
- import Python/JavaScript from the corpus;
- copy raw corpus text into runtime instructions;
- read secrets from project environment files as part of corpus compilation.

The installer writes project context and Hermes skill/bundle files. Differing existing files are protected unless `--force` is supplied, in which case HCP creates backups first.
