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

[Unreleased]: https://github.com/VertOurs/Rature/commits/main
