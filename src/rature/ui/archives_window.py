# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Archives window: SPECIFICATION.md §3.5. Read-only, opened from the menu."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402

from rature.core.migrations import FutureVersionError  # noqa: E402
from rature.ui import list_helpers  # noqa: E402
from rature.ui.archive_date_row import ArchiveDateRow  # noqa: E402
from rature.ui.archive_task_row import ArchiveTaskRow  # noqa: E402

if TYPE_CHECKING:
    from datetime import date

    from rature.core.app import App


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/archives_window.ui")
class ArchivesWindow(Adw.Window):
    """A sidebar of archived dates, most recent first, and one day's content.

    Built fresh every time the menu action opens it, so the sidebar always
    reflects the current archive/ directory rather than a stale snapshot
    from an earlier open.
    """

    __gtype_name__ = "RatureArchivesWindow"

    sidebar_stack: Gtk.Stack = Gtk.Template.Child()
    date_list: Gtk.ListBox = Gtk.Template.Child()
    header: Adw.HeaderBar = Gtk.Template.Child()
    title: Gtk.Label = Gtk.Template.Child()
    content_stack: Gtk.Stack = Gtk.Template.Child()
    struck_list: Gtk.ListBox = Gtk.Template.Child()
    active_list: Gtk.ListBox = Gtk.Template.Child()

    def __init__(self, *, app: App, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app = app
        # SPECIFICATION.md §3.5: most recent first, exactly App.archives'
        # order, never re-sorted here.
        self._dates = app.archives()
        for day_date in self._dates:
            self.date_list.append(ArchiveDateRow(day_date))
        self.sidebar_stack.set_visible_child_name("dates" if self._dates else "empty")
        self.date_list.connect("row-selected", self._on_row_selected)
        if self._dates:
            # Fires _on_row_selected synchronously, so the first archived
            # day is read from disk before __init__ returns. Archives are
            # small single-day files and the window is not shown yet, so
            # the blocking read is not worth deferring to an idle callback.
            self.date_list.select_row(self.date_list.get_row_at_index(0))
        else:
            self.content_stack.set_visible_child_name("no-archives")

    def _on_row_selected(
        self, _list_box: Gtk.ListBox, row: Gtk.ListBoxRow | None
    ) -> None:
        if row is None:
            return
        # Read the date the row carries, never self._dates[row.get_index()]:
        # that couples correctness to the row order in the ListBox, the
        # coupling removed from RatureWindow in #38.
        self._show_day(row.day_date)

    def _show_day(self, day_date: date) -> None:
        # SPECIFICATION.md §3.2's header format, reused as-is: same
        # weekday-day-month long form as the Day view's title. The label
        # lives in the .ui; only its text changes as the selection moves.
        self.title.set_label(day_date.strftime("%A %d %B"))
        list_helpers.clear(self.struck_list)
        list_helpers.clear(self.active_list)
        try:
            # SPECIFICATION.md §3.2: block order is Session.view()'s, never
            # recomputed here. archived_session hands back the same
            # struck/active split the Day view reads from a live Session.
            session = self.app.archived_session(day_date)
        except (OSError, ValueError, KeyError, TypeError, FutureVersionError):
            self.content_stack.set_visible_child_name("unreadable")
            return
        for task in session.struck:
            self.struck_list.append(ArchiveTaskRow(task))
        for task in session.active:
            self.active_list.append(ArchiveTaskRow(task))
        self.struck_list.set_visible(bool(session.struck))
        self.active_list.set_visible(bool(session.active))
        self.content_stack.set_visible_child_name(
            "tasks" if session.day.tasks else "empty"
        )
