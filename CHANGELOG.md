# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/VertOurs/Rature/commits/main
