# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Small plumbing shared by the list-based views (Day, Reserve, Recurring)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import GLib, Gtk  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Iterator


def rows(list_box: Gtk.ListBox) -> Iterator[Gtk.ListBoxRow]:
    """Yield every row of a ListBox, in order."""
    row = list_box.get_row_at_index(0)
    while row is not None:
        yield row
        row = row.get_next_sibling()


def clear(list_box: Gtk.ListBox) -> None:
    """Remove every row from a ListBox."""
    while (row := list_box.get_row_at_index(0)) is not None:
        list_box.remove(row)


def scroll_to_bottom(scrolled_window: Gtk.ScrolledWindow) -> None:
    """Scroll to the end once the pending layout has settled.

    A fresh entry is always appended last, so the end is where it is.
    GLib.idle_add defers the move past the new row's own allocation, so
    the adjustment's upper bound already accounts for it. An earlier
    grab_focus()-based attempt never actually scrolled when checked
    against a real window.
    """

    def scroll_once() -> bool:
        adjustment = scrolled_window.get_vadjustment()
        adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())
        return GLib.SOURCE_REMOVE

    GLib.idle_add(scroll_once)
