# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Helpers shared by the UI tests. Imported only once conftest.py let gi in."""

from typing import Any

from gi.repository import GLib, GObject, Gtk


def process_events() -> None:
    """Run the main loop until GTK has nothing left to do right now."""
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(may_block=False)


def wait_for_layout(widget: Gtk.Widget, timeout: float = 5.0) -> None:
    """Run the main loop until ``widget`` has a size.

    GTK lays out on its frame clock, not on pending events, so
    process_events alone can return before a new row has a height.
    """
    deadline = GLib.get_monotonic_time() + int(timeout * 1_000_000)
    context = GLib.MainContext.default()
    while widget.get_height() == 0:
        assert GLib.get_monotonic_time() < deadline, f"{widget} never laid out"
        context.iteration(may_block=False)


def type_into(entry: Gtk.Entry, text: str) -> None:
    """Type ``text`` and press Enter: the entry's own activate signal."""
    entry.set_text(text)
    entry.emit("activate")
    process_events()


def drop(
    row_class: Any,
    source: Gtk.Widget,
    target: Gtk.Widget,
    value: GObject.Value,
    *,
    upper_half: bool,
) -> bool:
    """Drop ``source`` on the upper or lower half of ``target``.

    Broadway cannot synthesise a pointer drag. So this plays the part of
    the source's drag-begin, the one piece of state it sets (the row
    class's dragged row), then emits the target row's real
    GtkDropTarget::drop, which runs the production handler unchanged.
    Returns whether the drop was accepted.
    """
    controllers = target.observe_controllers()
    drop_target = next(
        controller
        for index in range(controllers.get_n_items())
        if isinstance(controller := controllers.get_item(index), Gtk.DropTarget)
    )
    wait_for_layout(target)
    height = target.get_height()
    row_class._dragged = source
    try:
        accepted = drop_target.emit(
            "drop", value, 0.0, height * (0.25 if upper_half else 0.75)
        )
    finally:
        row_class._dragged = None
    process_events()
    return bool(accepted)
