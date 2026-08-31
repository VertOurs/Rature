# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One row in the Reserve view. SPECIFICATION.md §3.3."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, Gtk  # noqa: E402

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

        # SPECIFICATION.md §3.3: the row is a drag source carrying the
        # item id; the Day sidebar entry is the target. COPY, not MOVE:
        # the move is draw_from_reserve's business consequence, not a
        # drag-and-drop semantic, and MOVE would arm source-side deletion
        # the window's refresh already handles.
        drag_source = Gtk.DragSource(actions=Gdk.DragAction.COPY)
        drag_source.connect("prepare", self._on_drag_prepare)
        drag_source.connect("drag-begin", self._on_drag_begin)
        self.add_controller(drag_source)

    def _on_drag_prepare(
        self, _source: Gtk.DragSource, _x: float, _y: float
    ) -> Gdk.ContentProvider:
        return Gdk.ContentProvider.new_for_value(self.item.id)

    def _on_drag_begin(self, source: Gtk.DragSource, _drag: Gdk.Drag) -> None:
        source.set_icon(Gtk.WidgetPaintable.new(self), 0, 0)

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
        self._editing = True
        self.rename_entry.set_text(self.item.text)
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
        by ReserveView, to flush a pending edit before it rebuilds rows.
        The label is updated locally instead, which is enough either way.
        """
        if not self._editing:
            return
        text = self.rename_entry.get_text().strip()
        self._editing = False
        self.rename_entry.set_visible(False)
        self.text_label.set_visible(True)
        if text and text != self.item.text:
            self.text_label.set_label(text)
            self.perform(lambda: self.app.rename_reserve(self.item.id, text))
