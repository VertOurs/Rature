# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Day view: SPECIFICATION.md §3.2."""

from __future__ import annotations

from gettext import gettext as _
from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib, Gtk  # noqa: E402

from rature.ui.task_row import TaskRow  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from rature.core.app import App
    from rature.core.models import Task


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/day_view.ui")
class DayView(Adw.Bin):
    """Struck block on top, active block below; order is Session.view()'s.

    Wraps an AdwToolbarView rather than subclassing it: AdwToolbarView is
    a final GObject class, it cannot be a @Gtk.Template base.
    """

    __gtype_name__ = "RatureDayView"

    header: Adw.HeaderBar = Gtk.Template.Child()
    title: Gtk.Label = Gtk.Template.Child()
    lock_button: Gtk.Button = Gtk.Template.Child()
    entry: Gtk.Entry = Gtk.Template.Child()
    scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    stack: Gtk.Stack = Gtk.Template.Child()
    struck_list: Gtk.ListBox = Gtk.Template.Child()
    active_list: Gtk.ListBox = Gtk.Template.Child()
    banner: Adw.Banner = Gtk.Template.Child()

    def __init__(
        self,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        perform: Callable[[Callable[[], None]], bool],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.app = app
        # run_action refreshes after; perform does not (see task_row.py's
        # rename, which updates its own label and never needs a rebuild).
        self.run_action = run_action
        self.perform = perform
        self.entry.connect("activate", self._on_entry_activate)
        self.lock_button.connect("clicked", self._on_lock_clicked)
        self.refresh()

    def refresh(self) -> None:
        # SPECIFICATION.md §3.2's "losing focus commits" applied to another
        # trigger: rebuilding the rows would otherwise discard whatever the
        # user was mid-typing, timer tick or not.
        self._commit_pending_renames()
        session = self.app.session
        # SPECIFICATION.md §2.5: the reference date, never the calendar
        # date; between midnight and 04:00 they disagree. The label lives
        # in the .ui; refresh only rewrites its text.
        self.title.set_label(session.day.date.strftime("%A %d %B"))
        self._fill(self.struck_list, session.struck)
        self._fill(self.active_list, session.active)
        self.struck_list.set_visible(bool(session.struck))
        self.active_list.set_visible(bool(session.active))
        self.stack.set_visible_child_name("tasks" if session.day.tasks else "empty")

        # SPECIFICATION.md §3.2: recomputed from session state every time,
        # never a widget's own toggled state. roll_over unlocks the list
        # (SPECIFICATION.md §2.5 point 5) without this widget knowing, and
        # a GtkToggleButton would need its "toggled" signal blocked during
        # every programmatic update to avoid fighting that.
        if session.day.locked:
            self.lock_button.set_icon_name("changes-allow-symbolic")
            self.lock_button.set_tooltip_text(_("Unfreeze the list"))
        else:
            self.lock_button.set_icon_name("changes-prevent-symbolic")
            self.lock_button.set_tooltip_text(_("Freeze the list"))
        self.entry.set_sensitive(not session.day.locked)

    def _on_entry_activate(self, entry: Gtk.Entry) -> None:
        text = entry.get_text().strip()
        if not text:
            return
        if self.run_action(lambda: self.app.add(text)):
            entry.set_text("")
            entry.grab_focus()
            self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        # A fresh add is always appended last in the active block, so
        # scrolling to the bottom is scrolling to it. GLib.idle_add defers
        # this past the new row's own allocation, so the adjustment's
        # upper bound already accounts for it by the time this runs.
        #
        # Replaces an earlier grab_focus()-based approach (focusing the
        # row, then the entry again) that never actually scrolled anything
        # when checked against a real window: confirmed by hand, not by
        # reasoning about the API.
        def scroll_once() -> bool:
            adjustment = self.scrolled_window.get_vadjustment()
            adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())
            return GLib.SOURCE_REMOVE

        GLib.idle_add(scroll_once)

    def _on_lock_clicked(self, _button: Gtk.Button) -> None:
        if self.app.session.day.locked:
            self.run_action(self.app.unlock)
        else:
            self.run_action(self.app.lock)

    def _commit_pending_renames(self) -> None:
        for list_box in (self.struck_list, self.active_list):
            row = list_box.get_row_at_index(0)
            while row is not None:
                row.commit_pending_rename()
                row = row.get_next_sibling()

    def _fill(self, list_box: Gtk.ListBox, tasks: Iterable[Task]) -> None:
        while (row := list_box.get_row_at_index(0)) is not None:
            list_box.remove(row)
        for task in tasks:
            list_box.append(
                TaskRow(
                    task,
                    app=self.app,
                    run_action=self.run_action,
                    perform=self.perform,
                )
            )
