# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One row in the Day view's two blocks. SPECIFICATION.md §3.2."""

from __future__ import annotations

from gettext import gettext as _
from typing import TYPE_CHECKING, ClassVar

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402

from rature.ui.editable_row import EditableRow  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App
    from rature.core.models import Task


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/task_row.ui")
class TaskRow(EditableRow):
    """Send-back button, number, text, strike button, row menu."""

    __gtype_name__ = "RatureTaskRow"

    # SPECIFICATION.md §3.2: the row currently being dragged, for a reorder
    # or a send-back onto the Reserve sidebar entry (window.py).
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
        self.task = task
        self.send_to_reserve = send_to_reserve
        self.move_to_tomorrow = move_to_tomorrow
        super().__init__(
            task, app=app, run_action=run_action, perform=perform, **kwargs
        )

        self.num_label.set_label(str(task.num))
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

        self.send_back_button.connect("clicked", self._on_send_back_clicked)
        self.strike_button.connect("clicked", self._on_strike_clicked)
        self.move_to_tomorrow_button.connect(
            "clicked", self._on_move_to_tomorrow_clicked
        )

    def _rename_in_core(self, text: str) -> None:
        self.app.rename(self.task.id, text)

    def _set_priority_in_core(self, *, priority: bool) -> None:
        self.app.set_priority(self.task.id, priority=priority)

    def _delete_in_core(self) -> None:
        self.app.delete(self.task.id)

    def _move_before_in_core(self, entry_id: str, target_id: str | None) -> None:
        self.app.move_before(entry_id, target_id)

    def _accepts_drop_of(self, source: EditableRow) -> bool:
        # SPECIFICATION.md §3.2: rows reorder within their own block. A drop
        # onto the other block is refused and never shows a "drop here"
        # cue, since view() always lifts struck tasks above active ones and
        # the move would have no visible effect (§2.1 point 5).
        return isinstance(source, TaskRow) and source.task.done == self.task.done

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
