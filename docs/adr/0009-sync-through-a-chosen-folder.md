# ADR 0009: synchronisation through a chosen folder

- **Date**: 2026-10-31
- **Status**: accepted

## Context

Chantier 10 makes the same data usable from several devices: two desktop
machines first, the phone of chantier 11 as the reference case. Decisions
already taken on 30 October 2026 (`docs/internal/ROADMAP.md`, chantier
10):

- no merge engine and no exclusive lock: a phone stays open all the time,
  a lock would never be released
- before every write, read the file again; if it changed, reload and
  replay the gesture on the fresh data
- the phone is the reference case, not a late addition

The scoping session held with VertOurs on 31 October 2026 settled the
rest, recorded in French in the same document ("Cadrage du 31 octobre
2026"). This ADR restates it and adds the result of the portal spike.

The data stays what ADR 0003 describes: one `data.json`, one file per
archived day in `archive/`, atomic writes. What changes is where that
folder lives and who else writes into it.

## Decision

### The tool

Rature is designed for any tool that synchronises whole files, and is
tested and documented with **Syncthing** only. Only Syncthing's conflict
files are recognised. Its Android client is checked at chantier 11, not
assumed from memory.

### The folder: chosen through the portal

The user chooses the data folder with `Gtk.FileDialog.select_folder`. The
Flatpak manifest does not change: no `--filesystem` in `finish-args`. The
path returned by the portal is stored in GSettings, outside the data
folder, so that the choice never travels to another machine.

Rature only changes the permissions of its own files (`0o600`) and of its
own `archive/` folder (`0o700`), never those of the chosen folder:
`restrict_data_dir_permissions` keeps applying to the default data
folder, not to a chosen one.

### Conflicts

Files matching `*.sync-conflict-*` next to `data.json` or in `archive/`
raise a banner for as long as one exists, with an "Open Folder" action
(`Gtk.FileLauncher`). No merge, no resolution inside the application, and
Rature never deletes them.

Only names of the exact shape `YYYY-MM-DD.json` are read as archived
days, which `list_archives` already enforces: a conflict copy in
`archive/` is never read as a day.

### Day rollover is never written on its own

The rollover is applied in memory at load time and written with the first
real gesture, which reads the file again first. Otherwise a laptop waking
from sleep rolls the day over before Syncthing has delivered the
morning's file, and the morning's tasks end up in conflict at every wake.

**Known limit**: a gesture in the minute after waking, before Syncthing
has delivered, produces two genuinely different edits. The conflict is
reported, nothing more.

**Known limit**: a delivery that lands between the check before writing
and the `os.replace` is overwritten without any conflict file, since
Syncthing takes Rature's write for the next version of the one it has
just delivered. A window of a few milliseconds, accepted.

### Archives

Synchronised: the synchronised folder is the whole data folder. Nothing
specific to one machine lives there (window state and folder choice in
GSettings, logs on stderr). The temporary files of the atomic write stay
as they are; at startup Rature removes its own ones left behind by a
crash, matching the exact pattern `.<name>.<pid>.tmp` and ignoring
symbolic links. The user documentation gives a `.stignore` pattern for
those files, so that a crash on one machine does not spread its
leftovers to the others.

### Unreadable or missing file

Never an empty day written by default, never a `.bad-*` rename: renaming
a file that is arriving is already writing. A blocking message offers
"Try Again" and an explicit way out: set the file aside if it exists,
then start from an empty day, after confirmation. The confirmation says
that the empty day will also reach the other devices. The user decides to
write. `data.json` is only created when joining a folder, never
implicitly at startup.

A first launch is told apart from a vanished file by the data folder
itself: first launch if the folder does not exist, vanished file if it
exists without `data.json`. Not by a GSettings flag, which does not
follow the data when the folder changes, and would block every test
launch on a fresh throwaway `XDG_DATA_HOME`, which shares the host's
dconf.

A chosen folder whose portal grant has gone (permissions reset, folder
moved or deleted) falls into the same blocking message, with nothing
written.

### Joining a folder

If the chosen folder already holds a `data.json`, that file is taken and
the local file is set aside as a backup, without merging. The dialog says
plainly where the local file goes. If the folder is empty, the local data
is copied into it.

- **Empty** ignores Syncthing's own entries (`.stfolder`, `.stignore`,
  `.stversions`). Otherwise no Syncthing folder would ever be empty
- For an empty folder, the dialog asks to wait until Syncthing has
  finished its first synchronisation before joining it. Joining too early
  would copy the local data over a folder that is about to receive the
  other device's
- If the folder holds other visible files, the dialog says so
- Local archives stay in the previous folder, and the dialog says so

### Two versions of Rature on the same folder

A `FutureVersionError` on reading again forbids any write and asks for an
update. Without this check, an older version would overwrite the newer
format.

### Stale display

`data.json` is read again when the window regains focus, with no file
watching. The fingerprint is the SHA-256 of the content, not the
modification time, which Syncthing copies from the device the change came
from. The fingerprint held in memory is updated after each of Rature's own
writes, so that a focus return with no outside change reloads nothing.
Rows are rebuilt only if the file's fingerprint changed, and
never while a "⋯" menu or a rename is open: the reload waits until it
closes. This is the lesson of ADR 0007's withdrawal, where a rebuild on
focus return destroyed a row under its open menu.

### A replayed gesture that no longer applies

A gesture is replayed on the fresh data once. If the replay is refused
(its target no longer exists, or the business rules refuse it on the
fresh data), the gesture is dropped: nothing is written, the fresh data
is shown, and a toast says the task changed on another device. This is
neither a conflict nor an error: no banner, and one log line without
task text.

The refusal takes its own path. The generic handling of `LockedError`,
`KeyError` and `ValueError` in the window treats them as bugs, logged
with a full trace and never shown (`SPECIFICATION.md` §3.6, "Refus
métier"). A refused replay is expected: `App` raises a dedicated
exception, caught before that generic case.

This is not a rare case. The day rollover gives new identifiers to some
of the items it creates: the recurring tasks of the new day, and the
unstruck day tasks that return to the reserve as new items. The same task
then has a different identifier on each device that rolled the day over.
A gesture made just before the other device's file arrives targets an
identifier that no longer exists. Tasks prepared in Tomorrow keep their
identifier when they enter the day, and reserve items drawn into the day
get their own back when they return.

Gestures name their target by identifier, never by position: a position
replayed on different data would silently hit another task.

### Undo targets a local deletion

Undo only covers deletions (ADR 0005). Today it restores the last entry
of the deletion journal, with no identifier. Replayed on fresh data, it
would undo the last deletion in the file, which may have been made on
the other device.

Undo therefore targets a deletion by identifier. Rature keeps in memory
a stack of the identifiers of the deletions made on this device since
launch. The header button and `Ctrl+Z` undo the most recent one, so that
several deletions in a row can still be undone one after the other.

An undo is a gesture like any other: the file is read again before
writing, the undo is replayed on the fresh data, and it is refused with
the toast of a refused replay if its entry is no longer in the journal
(for instance, the other device has rolled the day over). On each reload
with a changed fingerprint, the identifiers missing from the fresh
journal leave the stack, so that the button and `Ctrl+Z` reflect what can
still be undone.

The stack is not cleared on a reload: clearing it on every change from
elsewhere would disable undo as soon as the phone adds a task.

The journal on disk is never cleared: it carries the counts of §2.6
(ADR 0005).

Undo is no longer offered after a restart: the stack lives in memory
only. Today, the journal allows undoing the day's last deletion even
after a relaunch. Accepted: keeping it would need a "device" field in the
format, hence a migration.

An undo never undoes the day rollover, even when the deletion it restores
was the first gesture of the day, written together with the rollover.

### Strict type validation on load

Field by field. Done first, independently of the rest
(#213): `"done": "yes"` or `"text": 42` no longer pass `Task.from_dict`.

### No synchronised mode

The day rollover written with the first gesture, the blocking message for
an unreadable file and the reload on focus return carry no risk locally.
They apply always: no setting, no second code path, no risk of forgetting
to enable a mode.

Visible cost locally: the previous day only shows in Archives, Statistics
and the export after the first gesture of the day. Accepted.

## The portal spike

Run on 31 October 2026, outside the repository, inside the installed
Rature Flatpak, on a throwaway folder chosen through the portal, before
and after a reboot.

| Check | Result |
|---|---|
| `os.replace`, new file and replacement | OK |
| `fsync` of the file and of the folder | OK |
| `0o600` on Rature's file, `0o700` on its `archive/` folder | OK |
| Atomic write and `fsync` inside `archive/` | OK |
| `stat` and content fingerprint | OK |
| A file written from the host, seen on reading again | OK |
| `Gtk.FileLauncher` on the folder | OK, the file manager opens |
| Access after a reboot, same path, no dialog | OK |
| File notifications for writes from the host | **none**, as expected |

The missing notifications change nothing: the design reads again on
focus return and before every write, and never relies on watching.

Not covered by the spike, to check at implementation:

- `os.link`, used by the backup before migration (§2.7.10), on the
  portal mount. If it fails, an `os.open` with `O_CREAT | O_EXCL` keeps
  the same guarantee: an existing backup is never overwritten
- a real Syncthing delivery into the folder: covered by the end
  criterion of chantier 10, two machines for a week of real use

## Open risk

The spike covers the desktop only. On Android, reaching a folder written
by another application goes through the Storage Access Framework, with no
known atomic replacement, or through access to all files. To validate at
chantier 11, before any commitment on the phone. A half-written file is
already covered: it is unreadable, and falls into the blocking message.

## Alternatives rejected

- **Plan B: Syncthing on the host syncs the application's own data
  folder** (`~/.var/app/io.github.vertours.Rature/data/rature` under
  Flatpak). No portal, no FUSE, no permission. Written before the spike as
  the fallback if the portal failed, not as a degraded solution. Not
  chosen, since the portal spike passed: it loses the join dialog, joining
  becomes a written instruction to follow in Syncthing (empty folder on
  the second machine), and the folder stays hidden in `~/.var`.
- **A `--filesystem` permission** in the manifest. Rejected: it breaks
  the sandbox, for a need the portal meets.
- **A merge engine.** Rejected on 30 October 2026: the replay of the
  gesture on fresh data covers the normal case, and a real conflict is
  shown to the user, never resolved behind their back.
- **A deterministic day rollover** (identifiers derived from the date and
  the source, no run timestamp, stable serialisation). With the deferred
  write it would only protect `archive/<D>.json`, and only when
  `data.json` is already in conflict. Postponed, see
  `docs/internal/ROADMAP.md`, "Repoussé volontairement".

## Consequences

- `docs/internal/SPECIFICATION.md` is updated before any code: §3.6
  (unreadable file: blocking message instead of the automatic set-aside),
  §2.5 (rollover written with the first gesture), the folder choice, the
  join dialog with the additions above, the conflict banner, the refused
  replay and its toast, and undo by identifier instead of "the last
  entry", with the local stack in memory
- A GSettings key holds the chosen folder; without it, the default data
  folder is used, unchanged
- `App` reads `data.json` again before each write and on focus return,
  and replays the gesture if the fingerprint changed
- The implementation is split according to this ADR in
  `docs/internal/ROADMAP.md`

## Addendum (2026-11-01)

Joining an empty folder now copies `archive/` along with `data.json`,
VertOurs's decision while writing `docs/internal/SPECIFICATION.md` §3.17.
The decision above left local archives in the previous folder in every
case. Since no button leads back to the default folder (`SPECIFICATION.md`
§3.6), archives
left behind would become invisible in Archives and Statistics. The folder
is empty, so nothing is overwritten. When the chosen folder already holds
data, nothing changes: local archives stay in the previous folder, and the
dialog says so.
