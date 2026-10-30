# ADR 0002: strict separation between core and ui

- **Date**: 2026-08-24
- **Status**: accepted

## Context

The prototype mixed business rules and GTK code in a single file. Direct
consequence: nothing could be tested without a display, and a bug was
reproduced by clicking rather than by running a test.

This limit is structural and cannot be worked around in a project
developed with the assistance of an agent: an agent can run `pytest`, it
cannot judge a visual rendering.

## Decision

No file in `core/` imports `gi`, GTK, Adw or Gdk. If a function needs GTK,
it does not belong in `core/`. No exceptions.

`ui/` contains no business rule. It displays the state provided by `core/`
and forwards the actions.

## Consequences

- The logic is tested in continuous integration, without a display server
- The interface can be redone without touching the rules
- Coverage of `core/` becomes a measurable end criterion, set at 90 %
- Permanent constraint: any temptation to write a business condition in an
  event handler must be refused
