# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Search the archives (SPECIFICATION.md §3.13): a search entry in the
  Archives window sidebar filters the date list as you type, keeping only
  the days that hold a task whose text matches. Matching is case- and
  accent-insensitive. The deletions journal is never searched. No count,
  no preview, no match highlighting; a blank query restores the full
  list, and "No matching days." shows when nothing matches.
- Copy a day as plain text (SPECIFICATION.md §3.12): a Copy as text button
  in the Day view and the Archives window header puts the shown day on the
  clipboard — the long-form date, then one `[x]`/`[ ]` line per task in the
  on-screen order. Deleted tasks never appear. No file, no dialog, no
  confirmation.
- Keyboard shortcuts and a help window (SPECIFICATION.md §3.11):
  Ctrl+1/2/3 switch to the Day, Reserve and Recurring views, Ctrl+Z undoes
  the last deletion, and Ctrl+? or F1 open an `AdwShortcutsDialog` listing
  every shortcut, also reachable from the new Keyboard Shortcuts menu
  item.
- Add a task already struck (SPECIFICATION.md §3.2): Shift+Enter in the
  Day view entry logs the task straight into the struck block in one
  gesture instead of add-then-strike, for retroactive logging. Same
  numbering as a normal add, the list scrolls up to the new task, and it
  is refused while the list is frozen like any add.
- Undo the last deletion (SPECIFICATION.md §3.2): a header button in the
  Day view restores the most recently deleted task of the current day at
  its original position and number, struck if it was struck, then drops
  its journal entry so the deletion count stays exact. Insensitive when
  nothing has been deleted today, active even while the list is frozen,
  and it shows no message. A task drawn from the reserve and restored
  this way returns to the reserve at the next day rollover if left
  unstruck.

### Fixed

- A data file (or an archived day) whose top-level JSON is not an object,
  such as a bare list or string, now lands on the corrupted-file recovery
  path instead of crashing: `migrate` rejected it with an `AttributeError`
  that neither startup nor the Archives window caught.

## [0.9.0] - 2026-09-02

### Added

- The main window adapts to narrow widths (SPECIFICATION.md §3.7): an
  `AdwBreakpoint` collapses the `AdwNavigationSplitView` under 500 units
  wide, turning the sidebar into its own page with a back button. The
  Day view's entry bar and a task's full, unwrapped-into-ellipsis text
  stay reachable in that layout, already true by construction. The
  Reserve-to-Day sidebar drag is unavailable while collapsed, since the
  sidebar entry it targets is off screen; the Reserve view's send
  button already covers that case. Completes chantier 3.

### Fixed

- The sidebar list now always navigates to the selected page on click,
  including re-selecting the row already active after using the back
  button: `AdwNavigationSplitView.show-content` needs setting on every
  activation, since `GtkListBox` does not re-emit `row-selected` for a
  click that does not change the selection.

## [0.8.0] - 2026-09-02

### Added

- The Archives window (SPECIFICATION.md §3.5): a read-only secondary
  window opened from the main menu, listing every archived date most
  recent first in a sidebar and showing the matching day's content on
  the right, struck above active with the same numbers as the Day view.
  `App.archived_session` wraps a loaded archived day in a `Session` so
  the struck/active split is never recomputed in the interface. A row
  carries no button, menu, or drag-and-drop, per spec. An archive that
  fails to load (corrupted, or written by a future version) shows a
  neutral message and never blocks the other dates.

## [0.7.0] - 2026-08-31

### Added

- The Recurring view: an `AdwActionRow` per template, text as title and
  the weekdays as subtitle, Monday first. A header `+` button opens a
  form; the row menu offers Edit (the same form, prefilled) and Delete.
  The form is an `AdwDialog` with a text field and seven weekday toggles;
  Save stays insensitive until there is text and at least one day
  (SPECIFICATION.md §2.7.2), and only closes on a successful write so a
  disk failure never discards the typed text. It keeps the template id,
  not the object, so a rollover between opening and Save cannot misdirect
  the write. Weekday names, in the subtitle and on the toggles, are
  derived from the locale with `strftime`, not catalogue strings.
  Completes chantier 3.
- Drag a reserve row onto the Day entry in the sidebar to draw it into
  the day. The drop goes through the same `RatureWindow.send_to_day` as
  the row's send button, never a second path. The action is `COPY`: the
  row leaves the reserve as a consequence of `draw_from_reserve`, not a
  drag-and-drop move. A frozen day list refuses the drop in the `accept`
  callback, so the entry never highlights while the list is frozen
  (SPECIFICATION.md §3.3). Unavailable in the collapsed narrow layout
  where the entry is off screen; the send button covers that case
  (SPECIFICATION.md §3.7).

### Fixed

- The launcher now adopts the environment's locale, so the Day view's
  date title shows day and month names in the user's language instead of
  always in English.

## [0.6.0] - 2026-08-31

### Added

- The Reserve view: a single list plus an entry bar, the same shape as the
  Day view. Add (Enter, keeps focus, scrolls to the new row, never
  de-duplicated per SPECIFICATION.md §2.7.4), rename in place, delete (row
  menu only), and a per-row send button that draws the item into the day
  through `RatureWindow.send_to_day`, the one method the sidebar drop
  target will share in step 7. The send button is insensitive while the day
  list is frozen. The `created` date is never shown. Empty-reserve status
  page. Completes chantier 3 step 6.

## [0.5.0] - 2026-08-31

### Added

- Drag-and-drop reordering in the Day view: a row is dragged within its own
  block and dropped before or after another row, calling `App.move_before`.
  A drop onto the other block is refused with no "drop here" cue, since
  `Session.view()` always lifts struck tasks above active ones and the move
  would not show. Reordering stays available while the list is frozen
  (SPECIFICATION.md §2.1 point 3). Completes chantier 3 step 5.

## [0.4.0] - 2026-08-31

### Added

- The Day view, read-only: struck tasks in a block on top, active tasks
  below, in `Session.view()` order, numbers never recalculated. Empty-day
  status page. A single `AdwBanner` covers three cases with a strict
  priority (write failure, then quarantine, then new day), each closable
  and never returning once closed; a 60-second timer calls `App.ensure_day`
  through the one OSError-catching wrapper every future action will reuse.
- Editing in the Day view: strike/unstrike, rename in place (Enter or
  losing focus commits, Escape discards), delete (row menu only, never a
  line button, no confirmation), an entry to add a task (Enter, keeps
  focus, scrolls to it), and freezing the list. Business errors the
  interface should have made impossible (a locked list, an unknown task)
  are logged to stderr and never shown. Drag-and-drop reordering is
  chantier 3 step 5, still to come.

## [0.3.0] - 2026-08-31

### Added

- `core/storage.py`: `list_archives`, listing archived days most recent
  first without opening any file's content, and `load_archive`, reading
  one back. `App.archives`/`App.read_archive` are the matching pass-throughs;
  `App.ensure_day` now returns the day it archived, or `None`.
- The main window: sidebar navigation (Day, Reserve, Recurring, with
  placeholder content until each view's own PR), window size and
  maximized state persisted through GSettings, an About Rature dialog.
  `RatureApplication` now owns the single `App` instance for the
  process, built once, and shows an unrecoverable-error dialog if the
  data file was written by a newer version of Rature. First visible
  feature: this is the version this bump belongs to.

## [0.2.0] - 2026-08-31

### Added

- Python package skeleton with the `core` and `ui` split, plus ruff and
  pytest configuration.
- Meson build: configured launcher, gresource bundle, translated desktop and
  metainfo files, icon install, and a `meson test` target.
- gettext plumbing with a French catalogue.
- An empty main window built from a `.ui` template.
- Flatpak manifest building against the GNOME 50 runtime.
- Continuous integration on every pull request: four jobs covering ruff,
  pytest, metadata validation with meson, and a Flatpak build.
- A PEP 735 development dependency group in `pyproject.toml`.
- Repository conventions, including a code-style rule.
- Business logic in `core/`: the day list with its operations, the reserve
  and recurring models, atomic JSON storage with day archiving, and the
  migration base. No GUI. CI gates `core/` coverage at 90%.
- Reserve and recurring logic in `core/`: reserve editing and the draw into
  the day, recurring templates and which apply on a weekday, and the day
  rollover with the 04:00 reference date, the reserve return, text
  de-duplication, and the multi-day catch-up. Still no GUI.
- `Session.move_before`, an explicit "place this task before that one, or at
  the end" reorder, built on the existing `reorder` permutation check.
- The deletion journal (`Deletion`) now carries everything needed to
  restore a deleted task exactly: its position in the day, whether it was
  struck and when, and where it came from.
- `App`, in `core/app.py`: the application coordination layer, behind a
  single injectable clock. `App.open` loads the data file or creates one on
  first launch, quarantines it and starts fresh if it is unreadable, and
  rejects a future data version outright. It always returns an App whose
  day already matches today, running the rollover/archive/save sequence
  itself. A mutation wrapper for every `Session` operation supplies the
  clock and saves after. A GUI can now be written calling only `App`. Still
  no GUI.

### Changed

- `Task` refuses a reserve-origin task built without both `source_id` and
  `source_created`, closing a crash path that used to only surface at
  serialisation.
- `Session.add_to_reserve`, `strike` and `delete` now require the caller to
  supply the reference date or timestamp explicitly. `core/` never reads
  the system clock.

[Unreleased]: https://github.com/VertOurs/Rature/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/VertOurs/Rature/releases/tag/v0.9.0
[0.8.0]: https://github.com/VertOurs/Rature/releases/tag/v0.8.0
[0.7.0]: https://github.com/VertOurs/Rature/releases/tag/v0.7.0
[0.6.0]: https://github.com/VertOurs/Rature/releases/tag/v0.6.0
[0.5.0]: https://github.com/VertOurs/Rature/releases/tag/v0.5.0
[0.4.0]: https://github.com/VertOurs/Rature/releases/tag/v0.4.0
[0.3.0]: https://github.com/VertOurs/Rature/releases/tag/v0.3.0
[0.2.0]: https://github.com/VertOurs/Rature/releases/tag/v0.2.0
