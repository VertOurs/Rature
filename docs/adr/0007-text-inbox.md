# ADR 0007: text inbox

- **Date**: 2026-09-22
- **Status**: abandoned on 2026-09-28, see "Withdrawal" at the end of the
  document

## Context

Capture from the phone existed in the POC, which was abandoned (ADR 0004).
The need is still real: being able to add tasks to the reserve from a
phone, without a dedicated application to maintain (rejected, see
`ROADMAP.md`, "Repoussé volontairement"), without a network and without a
third-party account (cloud synchronisation and Todoist postponed to v3,
same document).

The current Flatpak manifest grants no filesystem permission
(`build-aux/flatpak/io.github.vertours.Rature.yml`, only `wayland`,
`fallback-x11`, `dri` and `ipc` are present). Adding a broad
`--filesystem` permission would break the sandboxing and the project's
discipline on this point; any read of a folder chosen by the user must
therefore go through the file chooser portal (`xdg-desktop-portal`),
which does not appear in `finish-args` and needs no new static
permission.

The typical user drops a text file into a synchronised folder (Syncthing,
Nextcloud or equivalent) from any notes application on their phone.
Rature must find that file at the next launch or return to the
foreground, import it into the reserve, and never lose it on error.

## Decision

An inbox based on a text folder, with no continuous watching.

- **Choice of folder**: selected once by the user through the file
  chooser portal (`Gtk.FileDialog.select_folder`), which grants
  persistent access without a `--filesystem` permission in the manifest.
  The identifier returned by the portal is stored in GSettings.
- **When to read, and no `inotify`**: at application startup, then each
  time the window regains focus. The folder chosen through the file
  chooser portal is seen by the application through the document
  portal's FUSE mount, not through the real path on disk. On that mount,
  `inotify` does not reliably detect files dropped by a process outside
  the sandbox, a synchronisation client first of all: continuous
  watching would be a mechanism that seems to work in a local test and
  then goes silent in real use. Reading at the two moments above is
  therefore the robust choice, not merely the simplest. Accepted
  trade-off: a drop made while the window stays in the foreground
  without losing and regaining focus is only seen at the next launch.
- **File format**: plain text, one task per line, empty lines ignored, no
  syntax to interpret. The simplest possible format on the phone side,
  where any notes application will do.
- **One file per source**: each device or application that drops writes
  its own file, named `inbox-<machine>-<timestamp>.txt`. This removes any
  risk of two concurrent writers on the same file, with no locking to
  implement.
- **Strict filtering when listing**: only files whose name exactly
  matches the `inbox-*.txt` pattern are treated as drops. The temporary
  files that synchronisation clients write during a transfer (`.tmp`,
  `.part`, and each client's own equivalents) do not match the pattern
  and are ignored, even if they appear and then disappear between two
  reads.
- **Order of operations on import**: `data.json` is saved first, and the
  source file is only moved to `processed/` afterwards. A crash between
  the two steps leaves the source file in place: at the next launch it is
  imported again and produces a duplicate in the reserve, repairable by
  hand. The reverse order would lose the dropped tasks without any trace
  on a crash at the same point; between a duplicate and a loss, the
  duplicate is the risk to accept.
- **After import**: the file is moved to a `processed/` subfolder of the
  watched folder, never deleted. An English, ASCII name rather than
  `traité/`: consistent with the language of the code (`CLAUDE.md` §4
  rule 3), and immune to differences in Unicode normalisation (NFC/NFD)
  between synchronisation platforms, which could otherwise produce two
  distinct folders for the same accented name. The user keeps a trace of
  what was imported and can check or recover it by hand.
- **No deduplication on import**: consistent with `SPECIFICATION.md`
  §2.7.4, which keeps deduplication for the day rollover. A file dropped
  twice by mistake creates two entries; a rare case left to the user
  rather than handled in code.
- **Definition of "unreadable file"**: a file whose content is not valid
  UTF-8 is quarantined, under the same conditions as a corrupt
  `data.json`; nothing is imported, the file stays in the watched folder
  (not in `processed/`), and a banner warns the user. This reuses the
  quarantine pattern already in place for `data.json` (`StartupOutcome`,
  see milestone 3) rather than inventing a new one. An empty file is not
  an error: there is no task to import, and it is moved straight to
  `processed/` without triggering a quarantine.
- **Watched folder no longer accessible** (deleted, or the right granted
  by the portal revoked): the application attempts no silent
  reconstruction. It shows a message and offers to choose the folder
  again through the portal, exactly the same path as the first setup.

## Consequences

- No new permission in `finish-args`: reading goes through the file
  chooser portal, whose use the project rules already allow (`CLAUDE.md`
  §4 rule 6, no new runtime dependency).
- The import logic (reading, filtering, saving then moving to
  `processed/`, error detection) lives in `core/`, testable without
  `gi`, in line with `CLAUDE.md` §4 rule 1. Only the choice of folder
  through the portal and the recovery from an inaccessible folder touch
  `ui/`.
- The `processed/` folder grows without limit over time; no purge is
  planned for now. Accepted cost, to revisit only if real use justifies
  it.
- No real-time notification: the user discovers an addition at the next
  launch or focus return, never while the window stays open without
  losing focus.
- Prepares the ground for 7.2 (manual return to the reserve, priority)
  without depending on it: the inbox feeds the existing reserve, it
  introduces no new data structure beyond the field already provided for
  by `SPECIFICATION.md`.

## Addendum (2026-09-24)

Bug and security review focused on the 7.1 code, six batches. What
follows refines the decision above without reopening it.

- **Two-step move**: `move_to_processed` (a single rename) is replaced by
  `claim` (move to `processed/<name>.pending`) then `finalize` (rename to
  `<name>` once the content is imported). Needed so that "unreadable or
  too large file" (below) and "save then move" stay true at the same
  time: without this intermediate step, checking a file before claiming
  it would have left it in the watched folder during the check, whereas
  claiming it first would have taken it out of the watched folder before
  its content was accepted, in direct contradiction with
  `SPECIFICATION.md` §2.8. The chosen order: check (size, decoding) on
  the original file, claim (`claim`), read again from the `.pending` to
  import, then finalize.
- **Collision avoidance**: `claim` and `finalize` both refuse to
  overwrite a file already present under the target name, in the same
  spirit as `storage.quarantine()`: a `-2`, `-3`... suffix is inserted
  before the final extension rather than overwriting an unfinalised
  `.pending` from a previous launch or a file already in `processed/`.
- **Rare case documented**: if reading again from the `.pending` fails
  (the content changed between the check and `claim`, in practice a
  concurrent resynchronisation), the file stays as `.pending`, reported
  by the banner, with no automatic repair attempt.
- **Duplication bounded to one per launch**: if the import is saved but
  `finalize` then fails, the application remembers this `.pending` for
  the duration of the launch and does not import it again at each focus
  return (which would produce one more duplicate each time); only the
  next launch retries. Refines the duplicate-rather-than-loss trade-off
  already recorded above, without changing it.
- **Listening to the watched folder**: a read error when listing the
  watched folder itself (right revoked along the way) is treated as a
  folder that has become inaccessible, not as a write failure: these are
  two different banners of `SPECIFICATION.md` §3.6, and confusing them
  would have pointed the user to the wrong fix.
- **Byte order mark**: a UTF-8 BOM at the start of a file is ignored
  rather than treated as a character of the first task, useful for notes
  applications that write one by default.
- **Maximum size**: 1 MB per file (`SPECIFICATION.md` §2.8), so as never
  to load an abnormally large drop into memory before knowing whether it
  should be imported. A larger file gets the same treatment as an
  unreadable one.
- **Symbolic links excluded**: a symbolic link in the watched folder can
  point anywhere on the disk, outside what the portal actually granted
  when the folder was chosen. Ignoring it, even if its name matches the
  pattern, keeps the access scope to what the user really authorised.

## Withdrawal (2026-09-28)

The inbox, published in `1.2.0`, is withdrawn in the next version on
VertOurs's decision, after a week of real use.

- **Reason**: the gesture itself does not fit the use. Writing a text
  file from the phone, in a synchronised folder, remains heavier than the
  dictation in conversation that the method replaces.
- **Side effect observed**: reading at each focus return rebuilt every
  row of the Day view. Opening a task's "⋯" menu changes the window's
  active state, the row was destroyed while its menu was open, and both
  Rename and Delete had no effect any more. Any future trigger on focus
  return must avoid rebuilding the rows when the data has not changed.
- **What is removed**: `core/inbox.py`, `App.import_inbox`, the menu
  entry, the `capture-folder` GSettings key, the two banners,
  `SPECIFICATION.md` §2.8 and §3.15.
- **What remains**: the fixes from the September 2026 review unrelated
  to the inbox (Pango markup, data permissions, CI hardening), and the
  `po/meson.build` fix.
- **User data**: nothing is touched. Files already moved to `processed/`
  stay where they are, and imported items stay in the reserve.
- **Next steps**: synchronisation with the phone is postponed with no
  date (`ROADMAP.md`, "Repoussé volontairement"). Any resumption would
  start from a new ADR, not from this one.
