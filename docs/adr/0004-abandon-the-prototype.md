# ADR 0004: abandon the prototype

- **Date**: 2026-08-24
- **Status**: accepted

## Context

A working prototype existed: a single file, French in the code and the
interface, no tests, no separation of concerns, packaged as a Flatpak on
a runtime already at end of life. It answered the question "does the
method translate into an application", and the answer was yes.

Building on it meant dragging its choices along: language, structure,
lack of tests, a data format without identifiers.

## Decision

The prototype is abandoned. It is not used, migrated, consulted or
copied, not even in part. Construction starts again from the
specification written in `docs/internal/SPECIFICATION.md`.

The author keeps working through daily conversations until the application
is ready.

## Consequences

- No real data to preserve, so no migration to write
- The data format is born in version 1, complete, with reserve and
  recurring items
- The specification becomes the single source of truth, which forced it
  to be actually written rather than inferred from the existing code
- Accepted cost: several milestones with nothing usable, a period when a
  personal project is easily abandoned
