# ADR 0005: deletion log

- **Date**: 2026-08-24
- **Status**: accepted

## Context

Two rules of the specification directly contradicted each other.

`docs/internal/SPECIFICATION.md` §2.2 states that deleting a task makes it
disappear without leaving a trace. This is the most critical point of the
product: the distinction between striking, which keeps a trace of what
was done, and deleting, which erases something given up.

`docs/internal/SPECIFICATION.md` §2.6 allows the Statistics window to
count deleted tasks. But what left no trace cannot be counted.

Three outcomes were possible: remove deletions from the statistics scope,
log without the text, or log the complete entry.

## Decision

The archive file keeps a `deletions` log. Each entry holds the
identifier, the number, the text, the origin, the optional `source_id`
and the local timestamp.

The log is never displayed. The Statistics window only derives a number
from it.

The variant without text had been proposed to preserve the wording
"without leaving a trace" literally. It was rejected: it deprived the
undoing of a deletion of a faithful restoration, for a gain nobody was
after. The stated need was not confidentiality, it was the absence of a
trace in the interface.

## Consequences

- Counting deletions becomes possible, per day and per origin
- Undoing a deletion restores the task exactly, with no approximate
  reconstruction
- The wording of `docs/internal/SPECIFICATION.md` §2.2 had to be
  rephrased. The disappearance is functional: the task leaves every view
  and is never shown again. It is not a confidentiality guarantee, as the
  text stays readable to anyone who opens the archive file by hand. The
  document says so explicitly rather than implying the opposite
- Permanent prohibition: the Statistics window must not expose the
  contents of the log in any form, no preview, no search, no export. Any
  future request in that direction runs into this choice, and that is
  intended
- Undoing a deletion must maintain the log, otherwise the count drifts.
  To be covered by a test in milestone 4
- Lifted before milestone 3 (hardening PR for `core/`, see `STATE.md`):
  `Deletion` now carries `id`, `num`, `text`, `origin`, `source_id`,
  `source_created`, `template_id`, `done`, `done_at`, `index` and
  `deleted_at`, everything needed to restore a struck task or a task
  drawn from the reserve exactly, `index` also fixing its original
  position in `day.tasks`. Added now rather than in milestone 4 so that
  the field exists from version 1 of the format and forces no migration
  on real data, none existing yet
- The log belongs to the day, not to the whole data: it leaves with the
  archive at the day rollover, and the new day opens an empty one. Each
  entry keeps the full text and the origin (`day`, `reserve` or
  `recurring`), never displayed
