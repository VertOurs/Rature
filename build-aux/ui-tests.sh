#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
#
# The UI tests (tests/ui/) against real widgets, inside the GNOME SDK: the
# runtime the Flatpak ships on, with GTK, libadwaita, PyGObject and
# gtk4-broadwayd. Run from the repository root:
#
#   flatpak run --share=network --filesystem="$PWD" --cwd="$PWD" \
#     --command=bash org.gnome.Sdk//51 build-aux/ui-tests.sh
#
# Network is for pip only: the SDK has no pytest, so the version pinned in
# pyproject.toml goes into a scratch venv that also sees the SDK's gi.
set -euo pipefail

work=$(mktemp -d)
display=:42
trap 'kill "${broadway_pid:-0}" 2>/dev/null || true; rm -rf "$work"' EXIT

meson setup "$work/build" --prefix="$work/prefix" >/dev/null
meson install -C "$work/build" >/dev/null

python3 -m venv --system-site-packages "$work/venv"
pytest_pin=$(python3 -c 'import tomllib
dev = tomllib.load(open("pyproject.toml", "rb"))["dependency-groups"]["dev"]
print(next(d for d in dev if d.startswith("pytest==")))')
"$work/venv/bin/pip" install --quiet --disable-pip-version-check "$pytest_pin"

gtk4-broadwayd "$display" >"$work/broadway.log" 2>&1 &
broadway_pid=$!
# The socket must exist before GTK connects; broadwayd says so once ready.
for _ in $(seq 50); do
  grep -q '^Listening on' "$work/broadway.log" && break
  sleep 0.1
done
grep -q '^Listening on' "$work/broadway.log" || {
  cat "$work/broadway.log" >&2
  exit 1
}

# Broadway: a headless GDK backend, no compositor or X server needed.
# Memory GSettings: the window geometry the tests touch is never saved.
# fatal-criticals: a GTK critical aborts the run instead of scrolling by.
GDK_BACKEND=broadway \
BROADWAY_DISPLAY="$display" \
G_DEBUG=fatal-criticals \
GSETTINGS_BACKEND=memory \
GSETTINGS_SCHEMA_DIR="$work/prefix/share/glib-2.0/schemas" \
RATURE_UI_PREFIX="$work/prefix" \
  "$work/venv/bin/python" -m pytest tests/ui -p no:cacheprovider "$@"
