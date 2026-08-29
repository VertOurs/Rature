# Contributing to Rature

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

## Development setup

```
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
pip install --group dev
meson setup build
meson compile -C build
meson test -C build
```

The installed launcher runs under the interpreter Meson picks at setup time.
On a host where the tooling interpreter has no PyGObject, point the launcher
at one that does:

```
meson setup build -Dpython=/usr/bin/python3
```

## Checks before a pull request

```
ruff check .
ruff format --check .
pytest
```

CI runs the same checks and a Flatpak build.

## Code style

- No inline explanatory comments. A function that seems to need one should be
  renamed or split.
- One-line docstrings only, stating the purpose of a module, class or
  function.
- Every user-visible string goes through `_()` and is marked translatable in
  `.ui` files.
- English everywhere in the repository: names, comments, commit messages. The
  documents under `docs/internal/` are in French, deliberately.

## Commits

[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

```
<type>(<optional scope>): <imperative description>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `ci`, `i18n`,
`chore`. Description in the imperative, lower case, no trailing period, at
most 72 characters. One intent per commit. Scopes follow the tree: `core`,
`ui`, `storage`, `i18n`, `flatpak`, `meson`.

## Branches and merging

- One branch per task, prefixed with the commit type: `feat/`, `fix/`,
  `build/`, `ci/`, `docs/`.
- Merge through a pull request, never a direct push to `main`.
- Squash merge only. History stays linear.
- Commits are GPG-signed.

## Translations

gettext, catalogues in `po/`, French first. Regenerate the template and
merge new strings with:

```
meson compile -C build rature-pot
meson compile -C build rature-update-po
```

## License

By contributing you agree that your contributions are licensed under
GPL-3.0-or-later.
