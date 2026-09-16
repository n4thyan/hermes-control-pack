# Example project-specific additions

Hermes Control Pack provides general execution discipline. Add facts unique to your project below HCP's generated kernel or keep them in your own project context.

## Architecture
- Frontend: describe framework and entry path
- Backend: describe service/API entry path
- Database: describe datastore/migration workflow

## Required local behavior
- State canonical local ports/URLs.
- State the correct working directory if confusing backups/copies exist.
- State commands for focused tests and full verification.

## Do not regress
- List known working flows that must remain intact.
- List files/generated assets that must not be overwritten.

## Acceptance evidence
- Define what actually proves a change works in this project.
