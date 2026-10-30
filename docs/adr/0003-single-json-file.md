# ADR 0003: a JSON file rather than a database

- **Date**: 2026-08-24
- **Status**: accepted

## Context

The application handles a few dozen entries a day, on a single machine,
with no concurrent access and no synchronisation. SQLite was the natural
alternative.

## Decision

One versioned JSON file in `$XDG_DATA_HOME/rature/`, plus one file per
archived day in `archive/`.

Atomic writes are mandatory: temporary file in the same directory,
`flush`, `os.fsync` on the file, close, `os.replace`, then `os.fsync` on
the directory descriptor.

## Consequences

- Data readable and repairable by hand, which matters for an application
  that holds its author's lists
- No additional dependency
- The directory fsync is not optional: without it, the rename can be lost
  on a power cut and the atomicity guarantee would be false
- A `version` field and uuid identifiers are present from version 1, to
  avoid forcing a migration on real data later
- This choice would have to be reopened if synchronisation across machines
  became necessary, which is explicitly out of scope

## Addendum (2026-09-24)

Bug and security review, batch E: `data.json` and the archives were
written as `0o644` (masked by the system umask, from an `open()` with no
explicit mode), and their directory as `0o755`, readable by the whole
system although they contain the text of the user's tasks.
`_atomic_write_json` now forces `0o600` on the temporary file through a
dedicated `opener`, and `save()`/`archive()` create their directory as
`0o700`; neither value has a bit the umask could remove, so both are
reliable whatever the system umask. `App.open` also restricts the
existing data directory to `0o700` at each launch
(`storage.restrict_data_dir_permissions`), not at each write: a `0o700`
directory already blocks access to all of its contents, old `0o644`
archives included, so this single call also covers an installation
predating this fix without touching each existing file one by one. A
failure of this chmod is logged but never blocking: the restriction is a
privacy improvement, not a startup requirement.
