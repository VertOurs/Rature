# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Reserve view: SPECIFICATION.md §3.3."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402

from rature.ui import list_helpers  # noqa: E402
from rature.ui.reserve_row import ReserveRow  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/reserve_view.ui")
class ReserveView(Adw.Bin):
    """A single list plus an entry bar, same shape as the Day view.

    Wraps an AdwToolbarView rather than subclassing it: AdwToolbarView is
    a final GObject class, it cannot be a @Gtk.Template base.
    """

    __gtype_name__ = "RatureReserveView"

    entry: Gtk.Entry = Gtk.Template.Child()
    scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    stack: Gtk.Stack = Gtk.Template.Child()
    item_list: Gtk.ListBox = Gtk.Template.Child()

    def __init__(
        self,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        perform: Callable[[Callable[[], None]], bool],
        send_to_day: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.app = app
        # run_action refreshes after; perform does not (see reserve_row.py's
        # rename, which updates its own label and never needs a rebuild).
        self.run_action = run_action
        self.perform = perform
        self.send_to_day = send_to_day
        self.entry.connect("activate", self._on_entry_activate)
        self.refresh()

    def refresh(self) -> None:
        # SPECIFICATION.md §3.2's "losing focus commits" applied to another
        # trigger: rebuilding the rows would otherwise discard whatever the
        # user was mid-typing.
        self._commit_pending_renames()
        reserve = self.app.session.reserve
        list_helpers.clear(self.item_list)
        for item in reserve:
            self.item_list.append(
                ReserveRow(
                    item,
                    app=self.app,
                    run_action=self.run_action,
                    perform=self.perform,
                    send_to_day=self.send_to_day,
                )
            )
        self.stack.set_visible_child_name("items" if reserve else "empty")

    def _on_entry_activate(self, entry: Gtk.Entry) -> None:
        text = entry.get_text().strip()
        if not text:
            return
        # SPECIFICATION.md §2.7.4: manual reserve entries are never
        # de-duplicated; nothing here checks for an existing text.
        if self.run_action(lambda: self.app.add_to_reserve(text)):
            entry.set_text("")
            entry.grab_focus()
            list_helpers.scroll_to_bottom(self.scrolled_window)

    def _commit_pending_renames(self) -> None:
        for row in list_helpers.rows(self.item_list):
            row.commit_pending_rename()
