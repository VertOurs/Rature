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

### Day rollover is never written on its own

The rollover is applied in memory at load time and written with the first
real gesture, which reads the file again first. Otherwise a laptop waking
from sleep rolls the day over before Syncthing has delivered the
morning's file, and the morning's tasks end up in conflict at every wake.

**Known limit**: a gesture in the minute after waking, before Syncthing
has delivered, produces two genuinely different edits. The conflict is
reported, nothing more.

### Archives

Synchronised: the synchronised folder is the whole data folder. Nothing
specific to one machine lives there (window state and folder choice in
GSettings, logs on stderr). The temporary files of the atomic write stay
as they are; at startup Rature removes its own ones left behind by a
crash, matching the exact pattern `.<name>.<pid>.tmp` and ignoring
symbolic links.

### Unreadable or missing file

Never an empty day written by default, never a `.bad-*` rename: renaming
a file that is arriving is already writing. A blocking message offers
"Try Again" and an explicit way out: set the file aside if it exists,
then start from an empty day, after confirmation. The user decides to
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

### Two versions of Rature on the same folder

A `FutureVersionError` on reading again forbids any write and asks for an
update. Otherwise the older version overwrites the newer format.

### Stale display

`data.json` is read again when the window regains focus, with no file
watching. Rows are rebuilt only if the file's fingerprint changed, and
never while a "⋯" menu or a rename is open: the reload waits until it
closes. This is the lesson of ADR 0007's withdrawal, where a rebuild on
focus return destroyed a row under its open menu.

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

## Alternatives rejected

- **Plan B: Syncthing on the host syncs the application's own data
  folder** (`~/.var/app/io.github.vertours.Rature/data/rature` under
  Flatpak). No portal, no FUSE, no permission. Written before the spike as
  the fallback if the portal failed, not as a degraded solution. Not
  retained since the portal passed: it loses the join dialog, joining
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
  join dialog and the conflict banner
- A GSettings key holds the chosen folder; without it, the default data
  folder is used, unchanged
- `App` reads `data.json` again before each write and on focus return,
  and replays the gesture if the fingerprint changed
- The implementation is split according to this ADR in
  `docs/internal/ROADMAP.md`
