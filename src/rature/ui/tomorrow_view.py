# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Tomorrow view: SPECIFICATION.md §3.16."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gtk  # noqa: E402

from rature.ui import list_helpers  # noqa: E402
from rature.ui.prepared_row import PreparedRow  # noqa: E402
from rature.ui.tomorrow_recurring_row import TomorrowRecurringRow  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/tomorrow_view.ui")
class TomorrowView(Adw.Bin):
    """Recurring tasks due tomorrow on top, read-only; prepared tasks below.

    Wraps an AdwToolbarView rather than subclassing it, like DayView.
    """

    __gtype_name__ = "RatureTomorrowView"

    entry: Gtk.Entry = Gtk.Template.Child()
    scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    stack: Gtk.Stack = Gtk.Template.Child()
    recurring_list: Gtk.ListBox = Gtk.Template.Child()
    prepared_list: Gtk.ListBox = Gtk.Template.Child()

    def __init__(
        self,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        perform: Callable[[Callable[[], None]], bool],
        send_to_reserve: Callable[[str], None],
        move_to_today: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.app = app
        # run_action refreshes after; perform does not (a rename updates
        # its own label, see prepared_row.py).
        self.run_action = run_action
        self.perform = perform
        self.send_to_reserve = send_to_reserve
        self.move_to_today = move_to_today
        self.entry.connect("activate", self._on_entry_activate)
        # SPECIFICATION.md §3.16: Shift+Enter adds normally, nothing is
        # struck in Tomorrow. Caught in the capture phase, as in DayView,
        # since a GtkEntry does not turn Shift+Return into "activate".
        key_controller = Gtk.EventControllerKey()
        key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        key_controller.connect("key-pressed", self._on_entry_key_pressed)
        self.entry.add_controller(key_controller)
        self.refresh()

    def refresh(self) -> None:
        # Commit a rename in progress before the rows are rebuilt, as the
        # Day and Reserve views do.
        for row in list_helpers.rows(self.prepared_list):
            row.commit_pending_rename()
        # The interface computes neither the weekday nor the parity:
        # App gives the templates due on the reference date plus one.
        recurring = self.app.recurring_due_tomorrow()
        prepared = self.app.session.tomorrow
        with list_helpers.keeping_place(
            self.scrolled_window, self.recurring_list, self.prepared_list
        ):
            list_helpers.clear(self.recurring_list)
            for item in recurring:
                self.recurring_list.append(TomorrowRecurringRow(item))
            list_helpers.clear(self.prepared_list)
            for task in prepared:
                self.prepared_list.append(
                    PreparedRow(
                        task,
                        app=self.app,
                        run_action=self.run_action,
                        perform=self.perform,
                        send_to_reserve=self.send_to_reserve,
                        move_to_today=self.move_to_today,
                    )
                )
            # SPECIFICATION.md §3.16: an empty block is not shown.
            self.recurring_list.set_visible(bool(recurring))
            self.prepared_list.set_visible(bool(prepared))
        # The status page only when both blocks are empty.
        self.stack.set_visible_child_name("tasks" if recurring or prepared else "empty")

    def _on_entry_activate(self, _entry: Gtk.Entry) -> None:
        self._submit()

    def _on_entry_key_pressed(
        self, _controller: Gtk.EventControllerKey, keyval: int, _keycode: int, state
    ) -> bool:
        enter = keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_ISO_Enter)
        accel_mods = Gtk.accelerator_get_default_mod_mask()
        if enter and state & accel_mods == Gdk.ModifierType.SHIFT_MASK:
            self._submit()
            return True
        return False

    def _submit(self) -> None:
        text = self.entry.get_text().strip()
        if not text:
            return
        # Never de-duplicated, never refused: Tomorrow has no lock (§2.5).
        if self.run_action(lambda: self.app.add_to_tomorrow(text)):
            self.entry.set_text("")
            self.entry.grab_focus()
            list_helpers.scroll_to_bottom(self.scrolled_window)
