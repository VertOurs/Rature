# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One row in the Recurring view. SPECIFICATION.md §3.4."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402

from rature.ui import weekdays  # noqa: E402
from rature.ui.recurring_form import RecurringForm  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App
    from rature.core.models import RecurringItem


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/recurring_row.ui")
class RecurringRow(Adw.ActionRow):
    """Text as title, abbreviated weekdays as subtitle, an Edit/Delete menu."""

    __gtype_name__ = "RatureRecurringRow"

    menu_button: Gtk.MenuButton = Gtk.Template.Child()
    row_popover: Gtk.Popover = Gtk.Template.Child()
    edit_button: Gtk.Button = Gtk.Template.Child()
    delete_button: Gtk.Button = Gtk.Template.Child()

    def __init__(
        self,
        item: RecurringItem,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.item = item
        self.app = app
        self.run_action = run_action

        self.set_title(item.text)
        self.set_subtitle(weekdays.subtitle(item.weekdays))

        self.edit_button.connect("clicked", self._on_edit_clicked)
        self.delete_button.connect("clicked", self._on_delete_clicked)

    def _on_edit_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        form = RecurringForm(app=self.app, run_action=self.run_action, item=self.item)
        form.present(self)

    def _on_delete_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.run_action(lambda: self.app.delete_recurring(self.item.id))
