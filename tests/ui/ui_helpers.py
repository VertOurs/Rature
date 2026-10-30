# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Helpers shared by the UI tests. Imported only once conftest.py let gi in."""

from gi.repository import GLib


def process_events() -> None:
    """Run the main loop until GTK has nothing left to do right now."""
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(may_block=False)
