# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Recurring view: SPECIFICATION.md §3.4."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402

from rature.ui.recurring_form import RecurringForm  # noqa: E402
from rature.ui.recurring_row import RecurringRow  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/recurring_view.ui")
class RecurringView(Adw.Bin):
    """A boxed list of templates and a header button that opens the form.

    Wraps an AdwToolbarView rather than subclassing it: AdwToolbarView is
    a final GObject class, it cannot be a @Gtk.Template base.
    """

    __gtype_name__ = "RatureRecurringView"

    add_button: Gtk.Button = Gtk.Template.Child()
    stack: Gtk.Stack = Gtk.Template.Child()
    item_list: Gtk.ListBox = Gtk.Template.Child()

    def __init__(
        self,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.app = app
        self.run_action = run_action
        self.add_button.connect("clicked", self._on_add_clicked)
        self.refresh()

    def refresh(self) -> None:
        recurring = self.app.session.recurring
        while (row := self.item_list.get_row_at_index(0)) is not None:
            self.item_list.remove(row)
        for item in recurring:
            self.item_list.append(
                RecurringRow(item, app=self.app, run_action=self.run_action)
            )
        self.stack.set_visible_child_name("items" if recurring else "empty")

    def _on_add_clicked(self, _button: Gtk.Button) -> None:
        form = RecurringForm(app=self.app, run_action=self.run_action)
        form.present(self)
