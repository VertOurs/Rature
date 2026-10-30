# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One row in the Reserve view. SPECIFICATION.md §3.3."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, GObject, Gtk  # noqa: E402

from rature.ui.editable_row import EditableRow  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App
    from rature.core.models import ReserveItem


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/reserve_row.ui")
class ReserveRow(EditableRow):
    """Text, a send-to-day button, and a row menu (Rename, then Delete).

    No number: reserve items are undated and unnumbered (SPECIFICATION.md
    §2.5). The created date is never shown (SPECIFICATION.md §3.3).
    """

    __gtype_name__ = "RatureReserveRow"

    # SPECIFICATION.md §3.3: the row currently being dragged, for a
    # reorder or a draw onto the Day sidebar entry (window.py).
    _dragged: ClassVar[ReserveRow | None] = None
    # SPECIFICATION.md §3.3: COPY, not MOVE. Either move is a business
    # consequence (draw_from_reserve, move_reserve_before), not a
    # drag-and-drop semantic, and MOVE would arm source-side deletion the
    # window's refresh already handles.
    drag_action: ClassVar[Gdk.DragAction] = Gdk.DragAction.COPY

    text_label: Gtk.Label = Gtk.Template.Child()
    rename_entry: Gtk.Entry = Gtk.Template.Child()
    send_button: Gtk.Button = Gtk.Template.Child()
    row_popover: Gtk.Popover = Gtk.Template.Child()
    rename_button: Gtk.Button = Gtk.Template.Child()
    priority_button: Gtk.Button = Gtk.Template.Child()
    move_to_tomorrow_button: Gtk.Button = Gtk.Template.Child()
    delete_button: Gtk.Button = Gtk.Template.Child()
    priority_icon: Gtk.Image = Gtk.Template.Child()

    def __init__(
        self,
        item: ReserveItem,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        perform: Callable[[Callable[[], None]], bool],
        send_to_day: Callable[[str], None],
        move_to_tomorrow: Callable[[str], None],
        **kwargs,
    ) -> None:
        self.item = item
        self.send_to_day = send_to_day
        self.move_to_tomorrow = move_to_tomorrow
        super().__init__(
            item, app=app, run_action=run_action, perform=perform, **kwargs
        )

        # SPECIFICATION.md §3.3: the send button is insensitive while the
        # day list is frozen; core also refuses the draw (SPECIFICATION.md
        # §2.1 point 3), the two barriers are deliberate.
        self.send_button.set_sensitive(not app.session.day.locked)
        self.send_button.connect("clicked", self._on_send_clicked)
        # SPECIFICATION.md §3.3: always available, a frozen day included.
        self.move_to_tomorrow_button.connect(
            "clicked", self._on_move_to_tomorrow_clicked
        )

    def _rename_in_core(self, text: str) -> None:
        self.app.rename_reserve(self.item.id, text)

    def _set_priority_in_core(self, *, priority: bool) -> None:
        self.app.set_reserve_priority(self.item.id, priority=priority)

    def _delete_in_core(self) -> None:
        self.app.delete_from_reserve(self.item.id)

    def _move_before_in_core(self, entry_id: str, target_id: str | None) -> None:
        self.app.move_reserve_before(entry_id, target_id)

    # SPECIFICATION.md §3.3: the drag carries the item id as a string, the
    # type the Day and Tomorrow sidebar entries accept (window.py).
    def _drag_value(self) -> object:
        return self.item.id

    def _drag_gtype(self) -> GObject.GType:
        return GObject.TYPE_STRING

    def _on_send_clicked(self, _button: Gtk.Button) -> None:
        # SPECIFICATION.md §3.3: the button and the drag-and-drop drop
        # (chantier 3 step 7) call the same window method, never two
        # parallel paths.
        self.send_to_day(self.item.id)

    def _on_move_to_tomorrow_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.move_to_tomorrow(self.item.id)
