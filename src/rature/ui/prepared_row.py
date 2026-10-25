# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One prepared task in the Tomorrow view. SPECIFICATION.md §3.16."""

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
    from rature.core.models import PreparedTask


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/prepared_row.ui")
class PreparedRow(Gtk.ListBoxRow):
    """Send-back button, text, row menu. No number and no strike button."""

    __gtype_name__ = "RaturePreparedRow"

    # The row being dragged, for a reorder or a drop on the Day or Reserve
    # sidebar entry (window.py), as TaskRow._dragged does for the Day view.
    _dragged: ClassVar[PreparedRow | None] = None

    send_back_button: Gtk.Button = Gtk.Template.Child()
    text_label: Gtk.Label = Gtk.Template.Child()
    rename_entry: Gtk.Entry = Gtk.Template.Child()
    row_popover: Gtk.Popover = Gtk.Template.Child()
    rename_button: Gtk.Button = Gtk.Template.Child()
    priority_button: Gtk.Button = Gtk.Template.Child()
    move_to_today_button: Gtk.Button = Gtk.Template.Child()
    delete_button: Gtk.Button = Gtk.Template.Child()
    priority_icon: Gtk.Image = Gtk.Template.Child()

    def __init__(
        self,
        task: PreparedTask,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        perform: Callable[[Callable[[], None]], bool],
        send_to_reserve: Callable[[str], None],
        move_to_today: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.task = task
        self.app = app
        self.run_action = run_action
        self.perform = perform
        self.send_to_reserve = send_to_reserve
        self.move_to_today = move_to_today

        self.text_label.set_label(task.text)
        # SPECIFICATION.md §3.16: insensitive while the day is frozen, like
        # the reserve's send button; core refuses it too (§2.1 point 3).
        self.move_to_today_button.set_sensitive(not app.session.day.locked)
        # The Day view's priority column, kept even when empty.
        self.priority_icon.set_child_visible(task.priority)
        self.priority_button.set_label(
            _("Remove priority") if task.priority else _("Mark as priority")
        )

        self.send_back_button.connect("clicked", self._on_send_back_clicked)
        self.rename_button.connect("clicked", self._on_rename_clicked)
        self.priority_button.connect("clicked", self._on_priority_clicked)
        self.move_to_today_button.connect("clicked", self._on_move_to_today_clicked)
        self.delete_button.connect("clicked", self._on_delete_clicked)

        self._rename = InlineRename(
            entry=self.rename_entry,
            label=self.text_label,
            current_text=lambda: self.task.text,
            commit=lambda text: self.perform(
                lambda: self.app.rename_tomorrow(self.task.id, text)
            ),
        )

        self._wire_drag_and_drop()

    def _wire_drag_and_drop(self) -> None:
        # SPECIFICATION.md §3.16: same drag-and-drop as the Day view, one
        # block only, so any peer row is a valid target.
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
        PreparedRow._dragged = self
        self.add_css_class("rature-drag-source")
        source.set_icon(Gtk.WidgetPaintable.new(self), 0, 0)

    def _on_drag_end(
        self, _source: Gtk.DragSource, _drag: Gdk.Drag, _delete: bool
    ) -> None:
        PreparedRow._dragged = None
        self.remove_css_class("rature-drag-source")

    def _dragged_peer(self) -> PreparedRow | None:
        source = PreparedRow._dragged
        if source is None or source is self:
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
        next_id = sibling.task.id if isinstance(sibling, PreparedRow) else None
        target_id = reorder.drop_target_id(y, self.get_height(), self.task.id, next_id)
        self.run_action(
            lambda: self.app.move_tomorrow_before(source.task.id, target_id)
        )
        return True

    @classmethod
    def dragged(cls) -> PreparedRow | None:
        """The row being dragged right now, or None outside a drag."""
        return cls._dragged

    def _on_send_back_clicked(self, _button: Gtk.Button) -> None:
        self.send_to_reserve(self.task.id)

    def _on_move_to_today_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.move_to_today(self.task.id)

    def _on_delete_clicked(self, _button: Gtk.Button) -> None:
        # SPECIFICATION.md §2.7.9: final, no journal and no undo.
        self.row_popover.popdown()
        self.run_action(lambda: self.app.delete_from_tomorrow(self.task.id))

    def _on_priority_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.run_action(
            lambda: self.app.set_tomorrow_priority(self.task.id, not self.task.priority)
        )

    def _on_rename_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self._rename.begin()

    def commit_pending_rename(self) -> None:
        """Flush a pending edit, e.g. before TomorrowView rebuilds its rows."""
        self._rename.commit()
