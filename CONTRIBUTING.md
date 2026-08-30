# Contributing to Rature

This file is the single home of the repository conventions. The agent working
on this repo follows it too; `CLAUDE.md` only points here.

## Scope

Rature reproduces one specific daily-list method. Requests that add planning,
categories, priorities, scoring, reminders, or any commentary on the user's
behaviour are out of scope by design. Open an issue to discuss anything else
before writing code.

## Architecture

- `src/rature/core/` holds the business logic and never imports `gi`, GTK,
  Adwaita or Gdk. It stays testable without a display.
- `src/rature/ui/` holds everything GTK. Interfaces are `.ui` files loaded
  through `Gtk.Template`; widgets are not built in Python.
- Business logic never lives in `ui/`. A condition that decides product
  behaviour belongs in `core/`.

The rule and its rationale: `docs/adr/0002-separation-core-ui.md`.

## Development setup

The venv is only for ruff, pytest and meson; running the app is handled by
`-Dpython` below, not by the venv seeing system packages.

```
python3 -m venv .venv
. .venv/bin/activate
pip install --group dev
meson setup build
meson compile -C build
meson test -C build
```

The installed launcher runs under the interpreter Meson picks at setup time.
On a host where that interpreter has no PyGObject, point it at one that does:

```
meson setup build -Dpython=/usr/bin/python3
```

## Checks before a pull request

```
ruff check .
ruff format --check .
pytest
```

CI runs these plus a metadata-validation job and a Flatpak build.

## Code style

- No comment that paraphrases the code. If a comment states what a line
  does, fix the name or the structure instead.
- A comment is expected when it carries something the code cannot: the
  reason for a counter-intuitive choice (a local import, a system call, a
  library workaround), a reference to the spec as `SPECIFICATION.md §2.7.1`,
  or the temporary nature of an element and the milestone that replaces it.
- One-line docstrings for modules, classes and functions. Longer only when
  the why fits nowhere else.
- Every user-visible string goes through `_()` and is marked translatable in
  `.ui` files.
- English everywhere in the repository: names, comments, commit messages. The
  documents under `docs/internal/` are in French, deliberately.

## Commits

[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

```
<type>(<optional scope>): <imperative description>

<optional body: the why, not the what>

<optional footer: BREAKING CHANGE, Closes #12>
```

| Type | Use for |
|---|---|
| `feat` | a user-visible feature |
| `fix` | a bug fix |
| `refactor` | a behaviour-preserving rewrite |
| `test` | adding or fixing tests |
| `docs` | documentation only |
| `build` | Meson, Flatpak, packaging, dependencies |
| `ci` | continuous integration |
| `i18n` | translatable strings and catalogues |
| `chore` | misc work with no effect on shipped code |

- Imperative present, English, no leading capital, no trailing period, at
  most 72 characters in the description.
- One intent per commit. If the description needs an "and", it is probably
  two commits.
- The body explains why; the diff already shows what.
- `BREAKING CHANGE:` in the footer for any data-format or behaviour break.
- Scopes follow the tree: `core`, `ui`, `storage`, `i18n`, `flatpak`,
  `meson`.

```
feat(core): add reserve list with day promotion

fix(ui): keep task numbering stable after deletion

refactor(core): extract day rollover from session

    Rollover logic was tangled with persistence, which made it impossible
    to test without touching the filesystem.

feat(storage): switch to atomic writes

    BREAKING CHANGE: data file layout changed, see migrations.py
```

## Branches and merging

- One branch per task, prefixed with the commit type: `feat/`, `fix/`,
  `refactor/`, `build/`, `ci/`, `docs/`, `test/`, `chore/`.
- Merge through a pull request, never a direct push to `main`.
- Squash merge only, one commit per pull request. Merge commits and rebase
  merge are disabled in the repository settings, so the rule is enforced by
  the tool, not by memory.
- History stays linear, no merge commits.
- Commits are GPG-signed, for the "Verified" badge on GitHub.

## Versioning

Semantic versioning. The increment that applies to a merge is called out at
merge time.

- `fix` alone: patch, `0.1.0` to `0.1.1`.
- `feat`: minor, `0.1.1` to `0.2.0`.
- `BREAKING CHANGE`: major.
- Before 1.0, a break takes a minor bump only.

What `0.9.x` and `1.0.0` mean for this project: see
`docs/internal/ROADMAP.md`.

## Releases

One tag per version, one CHANGELOG entry in the Keep a Changelog format,
never a release without green CI.

## Interface

Follow the GNOME Human Interface Guidelines and keyboard accessibility. Every
frequent action has a shortcut.

## Translations

gettext, catalogues in `po/`, French first. Regenerate the template, merge
new strings, and check completeness with:

```
meson compile -C build rature-pot
meson compile -C build rature-update-po
msgfmt --statistics po/fr.po -o /dev/null
```

## Reference commands

Beyond the setup and pre-PR checks above:

```bash
# core/ coverage gate, enforced from milestone 1 on (see docs/internal/ROADMAP.md)
pytest --cov=rature.core --cov-fail-under=90

# Metadata (appstreamcli reads the source; desktop-file-validate needs the
# merged .desktop, present after `meson compile`)
appstreamcli validate data/io.github.vertours.Rature.metainfo.xml.in
desktop-file-validate build/data/io.github.vertours.Rature.desktop
flatpak run --command=flatpak-builder-lint org.flatpak.Builder \
  manifest build-aux/flatpak/io.github.vertours.Rature.yml
```

Building and running the Flatpak: see `README.md`.

## License

By contributing you agree that your contributions are licensed under
GPL-3.0-or-later.
