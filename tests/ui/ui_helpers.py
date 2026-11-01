# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Helpers shared by the UI tests. Imported only once conftest.py let gi in."""

from collections.abc import Callable
from typing import Any

from gi.repository import GLib, GObject, Gtk


class FakeAlertDialog:
    """A real Gtk.AlertDialog whose answer comes from the test."""

    shown: list["FakeAlertDialog"] = []  # noqa: RUF012
    _real_class: Any = None

    def __init__(self) -> None:
        self._real = FakeAlertDialog._real_class()
        self._callback: Callable[[Any, Any], None] | None = None
        self._choice: int | None = None
        self.parent: Any = None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)

    def choose(self, _parent: Any, _cancellable: Any, callback: Any) -> None:
        self.parent = _parent
        self._callback = callback
        FakeAlertDialog.shown.append(self)

    def choose_finish(self, _result: Any) -> int:
        if self._choice is None:
            raise GLib.Error("dismissed")
        return self._choice

    def press(self, label: str) -> None:
        self._choice = list(self._real.get_buttons()).index(label)
        self._callback(self, None)

    def dismiss(self) -> None:
        self._callback(self, None)


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


def _controller(widget: Gtk.Widget, kind: type) -> Any:
    controllers = widget.observe_controllers()
    return next(
        controller
        for index in range(controllers.get_n_items())
        if isinstance(controller := controllers.get_item(index), kind)
    )


def _payload(source: Any) -> GObject.Value:
    """What ``source`` carries when dragged, from its real drag source.

    Emits the row's GtkDragSource::prepare and checks the type it offers.
    PyGObject cannot read a GValue back out of a GdkContentProvider, so the
    value itself comes from _drag_value, the method prepare wraps.
    """
    provider = _controller(source, Gtk.DragSource).emit("prepare", 0.0, 0.0)
    offered = provider.ref_formats().get_gtypes()
    assert offered == [source._drag_gtype()], offered
    return GObject.Value(offered[0], source._drag_value())


def drop(row_class: Any, source: Any, target: Gtk.Widget, *, y: float) -> bool:
    """Drop ``source`` on ``target`` at height ``y`` inside it.

    Broadway cannot synthesise a pointer drag. So this plays the part of
    the source's drag-begin, the one piece of state it sets (the row
    class's dragged row), then emits the target's real GtkDropTarget::drop
    with the source's real payload, which runs the production handler
    unchanged. Returns whether the drop was accepted.
    """
    value = _payload(source)
    row_class._dragged = source
    try:
        accepted = _controller(target, Gtk.DropTarget).emit("drop", value, 0.0, y)
    finally:
        row_class._dragged = None
    process_events()
    return bool(accepted)


def drop_on_half(
    row_class: Any, source: Any, target: Gtk.Widget, *, upper_half: bool
) -> bool:
    """Drop ``source`` on the upper or lower half of the row ``target``."""
    wait_for_layout(target)
    y = target.get_height() * (0.25 if upper_half else 0.75)
    return drop(row_class, source, target, y=y)
