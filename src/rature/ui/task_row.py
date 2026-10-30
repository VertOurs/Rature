# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One row in the Day view's two blocks. SPECIFICATION.md §3.2."""

from __future__ import annotations

from gettext import gettext as _
from typing import TYPE_CHECKING, ClassVar

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, Gtk  # noqa: E402

from rature.ui import reorder  # noqa: E402
from rature.ui.inline_rename import InlineRename  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App
    from rature.core.models import Task


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/task_row.ui")
class TaskRow(Gtk.ListBoxRow):
    """Send-back button, number, text, strike button, row menu."""

    __gtype_name__ = "RatureTaskRow"

    # SPECIFICATION.md §3.2: the row currently being dragged, for a reorder
    # or a send-back onto the Reserve sidebar entry (window.py).
    # Shared across every row so a drop target can identify its source
    # without waiting on asynchronous content negotiation. One drag at a
    # time in one process, so a class attribute is enough.
    _dragged: ClassVar[TaskRow | None] = None

    send_back_button: Gtk.Button = Gtk.Template.Child()
    num_label: Gtk.Label = Gtk.Template.Child()
    text_label: Gtk.Label = Gtk.Template.Child()
    rename_entry: Gtk.Entry = Gtk.Template.Child()
    strike_button: Gtk.Button = Gtk.Template.Child()
    row_popover: Gtk.Popover = Gtk.Template.Child()
    rename_button: Gtk.Button = Gtk.Template.Child()
    priority_button: Gtk.Button = Gtk.Template.Child()
    move_to_tomorrow_button: Gtk.Button = Gtk.Template.Child()
    delete_button: Gtk.Button = Gtk.Template.Child()
    priority_icon: Gtk.Image = Gtk.Template.Child()

    def __init__(
        self,
        task: Task,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        perform: Callable[[Callable[[], None]], bool],
        send_to_reserve: Callable[[str], None],
        move_to_tomorrow: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.task = task
        self.app = app
        self.run_action = run_action
        self.perform = perform
        self.send_to_reserve = send_to_reserve
        self.move_to_tomorrow = move_to_tomorrow

        self.num_label.set_label(str(task.num))
        self.text_label.set_label(task.text)
        if task.done:
            self.text_label.add_css_class("rature-struck")
            self.strike_button.set_icon_name("edit-undo-symbolic")
            strike_text = _("Undo the strike")
        else:
            self.strike_button.set_icon_name("object-select-symbolic")
            strike_text = _("Strike through")
        # SPECIFICATION.md §3.8: the accessible name follows the tooltip;
        # GTK exposes a tooltip as the description, not the name.
        self.strike_button.set_tooltip_text(strike_text)
        self.strike_button.update_property(
            [Gtk.AccessibleProperty.LABEL], [strike_text]
        )

        # SPECIFICATION.md §3.2: hidden, not insensitive, on a struck or a
        # recurring task, since no state will ever make it usable there.
        # Left sensitive on a frozen list (SPECIFICATION.md §2.5).
        # set_child_visible, not set_visible: the button is neither drawn
        # nor focusable, but keeps its width, so the number and text
        # columns line up with the rows that do show it.
        self.send_back_button.set_child_visible(task.can_go_back_to_reserve)
        # SPECIFICATION.md §3.2: Move to tomorrow exists where ← does,
        # absent rather than insensitive elsewhere, active on a frozen list.
        self.move_to_tomorrow_button.set_visible(task.can_go_back_to_reserve)
        # SPECIFICATION.md §3.2: same trick for the priority column, so
        # an unmarked row keeps the slot and nothing shifts.
        self.priority_icon.set_child_visible(task.priority)
        self.priority_button.set_label(
            _("Remove priority") if task.priority else _("Mark as priority")
        )

        self.send_back_button.connect("clicked", self._on_send_back_clicked)
        self.strike_button.connect("clicked", self._on_strike_clicked)
        self.rename_button.connect("clicked", self._on_rename_clicked)
        self.priority_button.connect("clicked", self._on_priority_clicked)
        self.move_to_tomorrow_button.connect(
            "clicked", self._on_move_to_tomorrow_clicked
        )
        self.delete_button.connect("clicked", self._on_delete_clicked)

        self._rename = InlineRename(
            entry=self.rename_entry,
            label=self.text_label,
            current_text=lambda: self.task.text,
            commit=lambda text: self.perform(
                lambda: self.app.rename(self.task.id, text)
            ),
        )

        self._wire_drag_and_drop()

    def _wire_drag_and_drop(self) -> None:
        # SPECIFICATION.md §3.2: rows reorder by drag-and-drop within their
        # own block. A drop onto the other block is refused and never shows
        # a "drop here" cue, since view() always lifts struck tasks above
        # active ones and the move would have no visible effect.
        source = Gtk.DragSource(actions=Gdk.DragAction.MOVE)
        source.connect("prepare", self._on_drag_prepare)
        source.connect("drag-begin", self._on_drag_begin)
        source.connect("drag-end", self._on_drag_end)
        self.add_controller(source)

        target = Gtk.DropTarget(actions=Gdk.DragAction.MOVE)
        target.set_gtypes([type(self).__gtype__])
        target.connect("motion", self._on_drop_motion)
        target.connect("drop", self._on_drop)
        self.add_controller(target)

    def _on_drag_prepare(
        self, _source: Gtk.DragSource, _x: float, _y: float
    ) -> Gdk.ContentProvider:
        return Gdk.ContentProvider.new_for_value(self)

    def _on_drag_begin(self, source: Gtk.DragSource, _drag: Gdk.Drag) -> None:
        TaskRow._dragged = self
        self.add_css_class("rature-drag-source")
        source.set_icon(Gtk.WidgetPaintable.new(self), 0, 0)

    def _on_drag_end(
        self, _source: Gtk.DragSource, _drag: Gdk.Drag, _delete: bool
    ) -> None:
        TaskRow._dragged = None
        self.remove_css_class("rature-drag-source")

    def _dragged_peer(self) -> TaskRow | None:
        """The row being dragged, or None if it may not drop on this one.

        Refuses a row dropped on itself and a row from the other block:
        struck and active tasks never mix (SPECIFICATION.md §2.1 point 5).
        """
        source = TaskRow._dragged
        if source is None or source is self or source.task.done != self.task.done:
            return None
        return source

    def _on_drop_motion(
        self, _target: Gtk.DropTarget, _x: float, _y: float
    ) -> Gdk.DragAction:
        return Gdk.DragAction.MOVE if self._dragged_peer() else Gdk.DragAction(0)

    def _on_drop(
        self, _target: Gtk.DropTarget, _value: object, _x: float, y: float
    ) -> bool:
        source = self._dragged_peer()
        if source is None:
            return False
        sibling = self.get_next_sibling()
        next_id = sibling.task.id if isinstance(sibling, TaskRow) else None
        target_id = reorder.drop_target_id(y, self.get_height(), self.task.id, next_id)
        self.run_action(lambda: self.app.move_before(source.task.id, target_id))
        return True

    @classmethod
    def dragged(cls) -> TaskRow | None:
        """The row being dragged right now, or None outside a drag."""
        return cls._dragged

    def _on_send_back_clicked(self, _button: Gtk.Button) -> None:
        self.send_to_reserve(self.task.id)

    def _on_strike_clicked(self, _button: Gtk.Button) -> None:
        if self.task.done:
            self.run_action(lambda: self.app.unstrike(self.task.id))
        else:
            self.run_action(lambda: self.app.strike(self.task.id))

    def _on_move_to_tomorrow_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.move_to_tomorrow(self.task.id)

    def _on_delete_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.run_action(lambda: self.app.delete(self.task.id))

    def _on_priority_clicked(self, _button: Gtk.Button) -> None:
        # Allowed on a frozen list and a struck task, like a rename
        # (SPECIFICATION.md §3.2).
        self.row_popover.popdown()
        self.run_action(
            lambda: self.app.set_priority(self.task.id, priority=not self.task.priority)
        )

    def _on_rename_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self._rename.begin()

    def commit_pending_rename(self) -> None:
        """Flush a pending edit, e.g. before DayView rebuilds every row."""
        self._rename.commit()
