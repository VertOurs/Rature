# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One row in the Day view's two blocks. SPECIFICATION.md §3.2."""

from __future__ import annotations

from gettext import gettext as _
from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App
    from rature.core.models import Task


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/task_row.ui")
class TaskRow(Gtk.ListBoxRow):
    """Number, text, strike button, row menu (Delete; Rename arrives next)."""

    __gtype_name__ = "RatureTaskRow"

    num_label: Gtk.Label = Gtk.Template.Child()
    text_label: Gtk.Label = Gtk.Template.Child()
    strike_button: Gtk.Button = Gtk.Template.Child()
    row_popover: Gtk.Popover = Gtk.Template.Child()
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
        self.delete_button.connect("clicked", self._on_delete_clicked)

    def _on_strike_clicked(self, _button: Gtk.Button) -> None:
        if self.task.done:
            self.run_action(lambda: self.app.unstrike(self.task.id))
        else:
            self.run_action(lambda: self.app.strike(self.task.id))

    def _on_delete_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.run_action(lambda: self.app.delete(self.task.id))
