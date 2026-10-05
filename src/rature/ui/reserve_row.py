# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One row in the Reserve view. SPECIFICATION.md §3.3."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, GObject, Gtk  # noqa: E402

from rature.ui import reorder  # noqa: E402
from rature.ui.inline_rename import InlineRename  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App
    from rature.core.models import ReserveItem


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/reserve_row.ui")
class ReserveRow(Gtk.ListBoxRow):
    """Text, a send-to-day button, and a row menu (Rename, then Delete).

    No number: reserve items are undated and unnumbered (SPECIFICATION.md
    §2.5). The created date is never shown (SPECIFICATION.md §3.3).
    """

    __gtype_name__ = "RatureReserveRow"

    # SPECIFICATION.md §3.3: the row currently being dragged, so a peer
    # row's drop target can identify it without content negotiation, as
    # TaskRow._dragged does for the Day view.
    _dragged: ClassVar[ReserveRow | None] = None

    text_label: Gtk.Label = Gtk.Template.Child()
    rename_entry: Gtk.Entry = Gtk.Template.Child()
    send_button: Gtk.Button = Gtk.Template.Child()
    row_popover: Gtk.Popover = Gtk.Template.Child()
    rename_button: Gtk.Button = Gtk.Template.Child()
    delete_button: Gtk.Button = Gtk.Template.Child()

    def __init__(
        self,
        item: ReserveItem,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        perform: Callable[[Callable[[], None]], bool],
        send_to_day: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.item = item
        self.app = app
        self.run_action = run_action
        self.perform = perform
        self.send_to_day = send_to_day

        self.text_label.set_label(item.text)
        # SPECIFICATION.md §3.3: the send button is insensitive while the
        # day list is frozen; core also refuses the draw (SPECIFICATION.md
        # §2.1 point 3), the two barriers are deliberate.
        self.send_button.set_sensitive(not app.session.day.locked)

        self.send_button.connect("clicked", self._on_send_clicked)
        self.rename_button.connect("clicked", self._on_rename_clicked)
        self.delete_button.connect("clicked", self._on_delete_clicked)

        self._rename = InlineRename(
            entry=self.rename_entry,
            label=self.text_label,
            current_text=lambda: self.item.text,
            commit=lambda text: self.perform(
                lambda: self.app.rename_reserve(self.item.id, text)
            ),
        )

        # SPECIFICATION.md §3.3: the row is a drag source carrying the
        # item id, with two targets: the Day sidebar entry draws it, a
        # peer row reorders it. COPY, not MOVE: either move is a business
        # consequence (draw_from_reserve, move_reserve_before), not a
        # drag-and-drop semantic, and MOVE would arm source-side deletion
        # the window's refresh already handles.
        drag_source = Gtk.DragSource(actions=Gdk.DragAction.COPY)
        drag_source.connect("prepare", self._on_drag_prepare)
        drag_source.connect("drag-begin", self._on_drag_begin)
        drag_source.connect("drag-end", self._on_drag_end)
        self.add_controller(drag_source)

        target = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.COPY)
        target.connect("motion", self._on_drop_motion)
        target.connect("drop", self._on_drop)
        self.add_controller(target)

    def _on_drag_prepare(
        self, _source: Gtk.DragSource, _x: float, _y: float
    ) -> Gdk.ContentProvider:
        return Gdk.ContentProvider.new_for_value(self.item.id)

    def _on_drag_begin(self, source: Gtk.DragSource, _drag: Gdk.Drag) -> None:
        ReserveRow._dragged = self
        self.add_css_class("rature-drag-source")
        source.set_icon(Gtk.WidgetPaintable.new(self), 0, 0)

    def _on_drag_end(
        self, _source: Gtk.DragSource, _drag: Gdk.Drag, _delete: bool
    ) -> None:
        ReserveRow._dragged = None
        self.remove_css_class("rature-drag-source")

    def _dragged_peer(self) -> ReserveRow | None:
        """The row being dragged, or None if it may not drop on this one.

        Refuses a row dropped on itself, and any string dragged in from
        outside the reserve, which has no dragged row behind it.
        """
        source = ReserveRow._dragged
        if source is None or source is self:
            return None
        return source

    def _on_drop_motion(
        self, _target: Gtk.DropTarget, _x: float, _y: float
    ) -> Gdk.DragAction:
        return Gdk.DragAction.COPY if self._dragged_peer() else Gdk.DragAction(0)

    def _on_drop(
        self, _target: Gtk.DropTarget, _value: str, _x: float, y: float
    ) -> bool:
        source = self._dragged_peer()
        if source is None:
            return False
        sibling = self.get_next_sibling()
        next_id = sibling.item.id if isinstance(sibling, ReserveRow) else None
        target_id = reorder.drop_target_id(y, self.get_height(), self.item.id, next_id)
        self.run_action(lambda: self.app.move_reserve_before(source.item.id, target_id))
        return True

    def _on_send_clicked(self, _button: Gtk.Button) -> None:
        # SPECIFICATION.md §3.3: the button and the drag-and-drop drop
        # (chantier 3 step 7) call the same window method, never two
        # parallel paths.
        self.send_to_day(self.item.id)

    def _on_delete_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.run_action(lambda: self.app.delete_from_reserve(self.item.id))

    def _on_rename_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self._rename.begin()

    def commit_pending_rename(self) -> None:
        """Flush a pending edit, e.g. before ReserveView rebuilds its rows."""
        self._rename.commit()
