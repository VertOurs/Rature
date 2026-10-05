# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Small plumbing shared by the list-based views (Day, Reserve, Recurring)."""

from __future__ import annotations

from contextlib import contextmanager
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


@contextmanager
def keeping_place(
    scrolled_window: Gtk.ScrolledWindow, *list_boxes: Gtk.ListBox
) -> Iterator[None]:
    """Rebuild the rows of ``list_boxes`` without moving the user's place.

    Rebuilding destroys the focused row, often the very row whose button
    triggered the rebuild, and GtkWindow then hands focus to the first
    focusable widget, which drags the list back to its top. Checked
    against a real window: sending the 31st reserve item to the day left
    focus on the first row. So focus goes to the row now at the same
    index, or the last row if the list got shorter, and the scroll
    offset is put back once the new rows are allocated.
    """
    adjustment = scrolled_window.get_vadjustment()
    value = adjustment.get_value()
    focused = _focused_row(list_boxes)
    yield
    if focused is not None:
        list_box, index = focused
        row = list_box.get_row_at_index(index) or list_box.get_last_child()
        if row is not None:
            row.grab_focus()

    def restore_once() -> bool:
        adjustment.set_value(value)
        return GLib.SOURCE_REMOVE

    GLib.idle_add(restore_once)


def _focused_row(
    list_boxes: tuple[Gtk.ListBox, ...],
) -> tuple[Gtk.ListBox, int] | None:
    """The list holding the focus widget and the index of its row, if any."""
    root = list_boxes[0].get_root() if list_boxes else None
    focus = root.get_focus() if root is not None else None
    if focus is None:
        return None
    row = focus.get_ancestor(Gtk.ListBoxRow)
    for list_box in list_boxes:
        if row is not None and row.get_parent() is list_box:
            return list_box, row.get_index()
    return None


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


def scroll_into_view(
    scrolled_window: Gtk.ScrolledWindow, widget: Gtk.Widget | None
) -> None:
    """Scroll on the next idle so ``widget`` is fully visible.

    Moves the adjustment the least amount needed, up or down; a no-op when
    the widget already fits. ``None`` is tolerated (an empty block).
    """
    if widget is None:
        return

    def scroll_once() -> bool:
        found, bounds = widget.compute_bounds(scrolled_window)
        if found:
            adjustment = scrolled_window.get_vadjustment()
            page = adjustment.get_page_size()
            top = bounds.get_y()
            bottom = top + bounds.get_height()
            if bottom > page:
                adjustment.set_value(adjustment.get_value() + bottom - page)
            elif top < 0:
                adjustment.set_value(adjustment.get_value() + top)
        return GLib.SOURCE_REMOVE

    GLib.idle_add(scroll_once)
