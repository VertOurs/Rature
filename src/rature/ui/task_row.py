# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One row in the Day view's two blocks. SPECIFICATION.md §3.2."""

from __future__ import annotations

from gettext import gettext as _
from typing import TYPE_CHECKING, ClassVar

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, Gtk  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App
    from rature.core.models import Task


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/task_row.ui")
class TaskRow(Gtk.ListBoxRow):
    """Number, text, strike button, row menu (Rename, then Delete)."""

    __gtype_name__ = "RatureTaskRow"

    # SPECIFICATION.md §3.2: the row currently being dragged for a reorder.
    # Shared across every row so a drop target can identify its source
    # without waiting on asynchronous content negotiation. One drag at a
    # time in one process, so a class attribute is enough.
    _dragged: ClassVar[TaskRow | None] = None

    num_label: Gtk.Label = Gtk.Template.Child()
    text_label: Gtk.Label = Gtk.Template.Child()
    rename_entry: Gtk.Entry = Gtk.Template.Child()
    strike_button: Gtk.Button = Gtk.Template.Child()
    row_popover: Gtk.Popover = Gtk.Template.Child()
    rename_button: Gtk.Button = Gtk.Template.Child()
    delete_button: Gtk.Button = Gtk.Template.Child()

    def __init__(
        self,
        task: Task,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        perform: Callable[[Callable[[], None]], bool],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.task = task
        self.app = app
        self.run_action = run_action
        self.perform = perform

        self.num_label.set_label(str(task.num))
        self.text_label.set_label(task.text)
        if task.done:
            self.text_label.add_css_class("rature-struck")
            self.strike_button.set_icon_name("edit-undo-symbolic")
            self.strike_button.set_tooltip_text(_("Undo the strike"))
        else:
            self.strike_button.set_icon_name("object-select-symbolic")
            self.strike_button.set_tooltip_text(_("Strike through"))

        self.strike_button.connect("clicked", self._on_strike_clicked)
        self.rename_button.connect("clicked", self._on_rename_clicked)
        self.delete_button.connect("clicked", self._on_delete_clicked)

        self._editing = False
        self.rename_entry.connect(
            "activate", lambda _entry: self.commit_pending_rename()
        )
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_rename_key_pressed)
        self.rename_entry.add_controller(key_controller)
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect("leave", lambda _c: self.commit_pending_rename())
        self.rename_entry.add_controller(focus_controller)

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
        if y < self.get_height() / 2:
            target_id: str | None = self.task.id
        else:
            sibling = self.get_next_sibling()
            target_id = sibling.task.id if isinstance(sibling, TaskRow) else None
        self.run_action(lambda: self.app.move_before(source.task.id, target_id))
        return True

    def _on_strike_clicked(self, _button: Gtk.Button) -> None:
        if self.task.done:
            self.run_action(lambda: self.app.unstrike(self.task.id))
        else:
            self.run_action(lambda: self.app.strike(self.task.id))

    def _on_delete_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.run_action(lambda: self.app.delete(self.task.id))

    def _on_rename_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self._editing = True
        self.rename_entry.set_text(self.task.text)
        self.text_label.set_visible(False)
        self.rename_entry.set_visible(True)
        self.rename_entry.grab_focus()
        self.rename_entry.select_region(0, -1)

    def _on_rename_key_pressed(
        self, _controller: Gtk.EventControllerKey, keyval: int, _keycode: int, _state
    ) -> bool:
        if keyval == Gdk.KEY_Escape:
            self._cancel_rename()
            return True
        return False

    def _cancel_rename(self) -> None:
        # SPECIFICATION.md §3.2: Escape discards the typed text outright,
        # unlike Enter or losing focus, which both commit.
        if not self._editing:
            return
        self._editing = False
        self.rename_entry.set_visible(False)
        self.text_label.set_visible(True)

    def commit_pending_rename(self) -> None:
        """Validate an in-progress rename. A no-op if not editing.

        Never triggers a view refresh: called both on Enter/focus-out and,
        by DayView, to flush a pending edit before it rebuilds every row.
        The label is updated locally instead, which is enough either way.
        """
        if not self._editing:
            return
        text = self.rename_entry.get_text().strip()
        self._editing = False
        self.rename_entry.set_visible(False)
        self.text_label.set_visible(True)
        if text and text != self.task.text:
            self.text_label.set_label(text)
            self.perform(lambda: self.app.rename(self.task.id, text))
