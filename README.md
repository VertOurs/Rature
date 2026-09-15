# Rature

**Your day, one line at a time.** A daily-list desktop application for
GNOME.

[![CI](https://github.com/VertOurs/Rature/actions/workflows/ci.yml/badge.svg)](https://github.com/VertOurs/Rature/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/VertOurs/Rature)](https://github.com/VertOurs/Rature/releases)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-blue.svg)](LICENSE)

## What it is

Rature keeps one numbered list for the day. You add tasks one by one, in no
particular order, and strike them through as the day goes. Struck tasks stay
visible in a block at the top, as a trace of what got done. There is no
planning, no categories, no scoring, no encouragement. Rature is a support,
not a coach.

The method it reproduces:

- Tasks are dictated one at a time, in bulk, with no imposed order.
- Each task joins a numbered list, without comment.
- Striking a task bars it and moves it to a "Struck" block at the top.
- Deleting a task removes it without a visible trace. It is distinct from
  striking: an abandonment, not an achievement. The two actions are never
  merged.
- The list can be frozen to end the composition of the day while striking,
  renaming and reordering stay possible.

## Screenshots

![The Day view](data/screenshots/day.png)
![The Recurring view](data/screenshots/recurring.png)
![The Archives window](data/screenshots/archives.png)
![The Statistics window](data/screenshots/statistics.png)

## Features

- **Day view** — add, strike, unstrike, rename in place, delete, reorder by
  drag-and-drop, freeze the list. `Shift+Enter` logs a task already struck.
- **Reserve** — an undated list you draw from in the morning; unfinished
  day tasks return to it at the day rollover.
- **Recurring** — task templates tied to weekdays, injected automatically
  each new day.
- **Archives window** — every past day, read-only, with a search over task
  text.
- **Statistics window** — a plain table of counts per archived day, no
  chart and no judgement.
- **Undo the last deletion**, **copy a day as plain text**, keyboard
  shortcuts with a help window, and a full French translation.

## Installing

From the self-hosted Flatpak repository, with automatic updates:

```
flatpak remote-add --if-not-exists rature \
  https://vertours.github.io/Rature/io.github.vertours.Rature.flatpakrepo
flatpak install rature io.github.vertours.Rature
```

A standalone `.flatpak` bundle is attached to each
[release](https://github.com/VertOurs/Rature/releases) for a one-off
install without adding the repository.

AUR, COPR and Mageia packages are prepared (`build-aux/`) but not yet
submitted. Flathub is deliberately not a target
([`docs/adr/0001-rejet-de-flathub.md`](docs/adr/0001-rejet-de-flathub.md)).

## Status

Built from a written specification. Version 1 (`1.0.0`) is complete and
installable from the self-hosted Flatpak repository above: the business
logic, the three views, the Archives and Statistics windows, keyboard
shortcuts, plain-text export, a full French translation, and self-updating
publication.

Version 2 is under way: structured logging, native packaging, a refreshed
README and project page, and further comfort features.

Built with AI assistance (Claude Code); the author writes the
specification, reviews every change, and merges it.

Design decisions and the roadmap live under `docs/internal/` (in French).
The architecture is [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Building from source

Requires Meson, GTK 4, libadwaita, GLib and the gettext tools, and Python
3.13 or newer.

```
meson setup build
meson compile -C build
meson install -C build
```

Run the checks:

```
meson test -C build
```

### Flatpak

```
flatpak-builder --user --install --force-clean build-flatpak \
  build-aux/flatpak/io.github.vertours.Rature.yml
flatpak run io.github.vertours.Rature
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
