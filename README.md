# Rature

A daily list desktop application for GNOME. Your day, one line at a time.

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

## Status

Pre-release, built from a written specification. The foundations
(milestone 0) are done; milestone 1, the business logic, is in progress.
Nothing is functional yet and nothing is published. Design decisions and the
roadmap live under `docs/internal/` (in French).

## Building from source

Requires Meson, GTK 4, libadwaita, GLib and gettext development tools, and
Python 3.13 or newer.

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

## Installing

Not published yet. Milestone 5 will provide a self-hosted Flatpak
repository, an AUR package and a COPR package. Flathub is deliberately not a
target.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
