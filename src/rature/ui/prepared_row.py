# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One prepared task in the Tomorrow view. SPECIFICATION.md §3.16."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402

from rature.ui.editable_row import EditableRow  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App
    from rature.core.models import PreparedTask


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/prepared_row.ui")
class PreparedRow(EditableRow):
    """Send-back button, text, row menu. No number and no strike button."""

    __gtype_name__ = "RaturePreparedRow"

    # The row being dragged, for a reorder or a drop on the Day or Reserve
    # sidebar entry (window.py). SPECIFICATION.md §3.16: one block only, so
    # any peer row is a valid target.
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
        self.task = task
        self.send_to_reserve = send_to_reserve
        self.move_to_today = move_to_today
        super().__init__(
            task, app=app, run_action=run_action, perform=perform, **kwargs
        )

        # SPECIFICATION.md §3.16: insensitive while the day is frozen, like
        # the reserve's send button; core refuses it too (§2.1 point 3).
        self.move_to_today_button.set_sensitive(not app.session.day.locked)
        self.send_back_button.connect("clicked", self._on_send_back_clicked)
        self.move_to_today_button.connect("clicked", self._on_move_to_today_clicked)

    def _rename_in_core(self, text: str) -> None:
        self.app.rename_tomorrow(self.task.id, text)

    def _set_priority_in_core(self, *, priority: bool) -> None:
        self.app.set_tomorrow_priority(self.task.id, priority=priority)

    def _delete_in_core(self) -> None:
        # SPECIFICATION.md §2.7.9: final, no journal and no undo.
        self.app.delete_from_tomorrow(self.task.id)

    def _move_before_in_core(self, entry_id: str, target_id: str | None) -> None:
        self.app.move_tomorrow_before(entry_id, target_id)

    def _on_send_back_clicked(self, _button: Gtk.Button) -> None:
        self.send_to_reserve(self.task.id)

    def _on_move_to_today_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.move_to_today(self.task.id)
