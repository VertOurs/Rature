<div align="center">

# Rature

<img src="data/icons/hicolor/scalable/apps/io.github.vertours.Rature.svg" width="96" height="96" alt="Rature icon">

**A support, not a coach.**

[![CI](https://github.com/VertOurs/Rature/actions/workflows/ci.yml/badge.svg)](https://github.com/VertOurs/Rature/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/VertOurs/Rature)](https://github.com/VertOurs/Rature/releases)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-blue.svg)](LICENSE)

</div>

## Why another todo app

Dozens of task managers already exist; I tried a fair number of them
before writing this one. Most assume a working memory and a motivation
system that ADHD and depression do not reliably provide: a plan to hold
in mind, priorities to keep straight, a backlog to catch up on, a streak
to protect. Those are exactly the mechanisms that make a list stop
working when executive function or motivation is the part that is
missing, turning a task manager into one more source of guilt. Rature
removes them instead of managing around them: nothing to plan, nothing
to prioritize, nothing to fall behind on, nothing scored.

A struck task stays visible in its block instead of disappearing: a
small, precious hit of "I did that" in a context where it does not come
easily otherwise. Unfinished work does not carry over as a growing
backlog on the next day's list either; it returns to the reserve
instead, and it is up to me, the next day, to decide what goes on the
list according to whatever energy I actually have.

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

Version 2 is under way. Milestone 6 (`1.1.0`) is done: structured
logging, native packaging prepared for AUR/COPR/Mageia (submission still
pending), and this refreshed README and project page. Capture from a
synced folder and further comfort features are next.

Built with AI assistance (Claude Code); I write the specification,
review every change, and merge it.

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

## Sponsoring

If Rature is useful to you, sponsoring is welcome through the "Sponsor"
button at the top of this repository, or directly on
[GitHub Sponsors](https://github.com/sponsors/VertOurs). Entirely
optional: the app, its updates and its packages stay free regardless.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
