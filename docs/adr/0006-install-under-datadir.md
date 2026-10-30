# ADR 0006: install the package under datadir

- **Date**: 2026-08-29
- **Status**: accepted

## Context

Session B had to make the Meson installation runnable whatever the
prefix, including a throwaway prefix used to check the window locally.

Two interpreters coexist on the development machine: the project venv in
Python 3.13 without PyGObject, used for `ruff` and `pytest`, and the
system `python3` in 3.14 with PyGObject, used to run the application
outside Flatpak.

Installing the package into the interpreter's `site-packages` ties the
application to that interpreter and to a system prefix. An arbitrary
`--prefix` then does not put the package on the import path.

## Decision

The package is installed under `<datadir>/rature/rature`. The launcher
`src/rature.in`, configured by Meson, puts this directory first in
`sys.path`. The `.gresource` and the generated `config.py` live in the
same place.

A Meson option `python`, defaulting to `python3`, picks the interpreter
named in the launcher's shebang. Locally:
`meson setup build -Dpython=/usr/bin/python3`. Under Flatpak and in CI,
the default is fine, as `python3` there has PyGObject.

Installing as a regular Python package, through a build backend and
`pip install .`, was rejected. The build goes through Meson, not through
a Python backend, and that path would bring back the coupling to the
prefix and to `site-packages`.

## Consequences

- Installation works under any prefix, checked with a throwaway
  `--prefix`
- The application runs under the GNOME 50 runtime's `python3` in
  Flatpak, and under the machine's `python3` with PyGObject locally
- `meson test` resolves `pytest` from the `PATH`, hence the activated
  venv, and keeps `required: false` for development. CI installs
  `pytest` explicitly in its own job
- The list of `__pycache__` directories passed to `exclude_directories`
  in `src/meson.build` is maintained by hand. Moving the source tree
  means reviewing it
