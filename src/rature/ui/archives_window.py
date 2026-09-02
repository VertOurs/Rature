# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Archives window: SPECIFICATION.md §3.5. Read-only, opened from the menu."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gtk  # noqa: E402

from rature.core.migrations import FutureVersionError  # noqa: E402
from rature.ui import list_helpers  # noqa: E402
from rature.ui.archive_date_row import ArchiveDateRow  # noqa: E402
from rature.ui.archive_task_row import ArchiveTaskRow  # noqa: E402

if TYPE_CHECKING:
    from datetime import date

    from rature.core.app import App
    from rature.core.session import Day


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/archives_window.ui")
class ArchivesWindow(Adw.Window):
    """A sidebar of archived dates, most recent first, and one day's content.

    Built fresh every time the menu action opens it, so the sidebar always
    reflects the current archive/ directory rather than a stale snapshot
    from an earlier open.
    """

    __gtype_name__ = "RatureArchivesWindow"

    sidebar_stack: Gtk.Stack = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    date_list: Gtk.ListBox = Gtk.Template.Child()
    header: Adw.HeaderBar = Gtk.Template.Child()
    title: Adw.WindowTitle = Gtk.Template.Child()
    copy_button: Gtk.Button = Gtk.Template.Child()
    content_stack: Gtk.Stack = Gtk.Template.Child()
    struck_list: Gtk.ListBox = Gtk.Template.Child()
    active_list: Gtk.ListBox = Gtk.Template.Child()

    def __init__(self, *, app: App, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app = app
        # SPECIFICATION.md §3.12: the date the Copy as text button acts on,
        # or None while nothing readable is shown.
        self._shown_date = None
        # SPECIFICATION.md §3.13: each archive parsed at most once and kept
        # for the window's lifetime, so filtering as you type never rereads
        # a file. None marks an archive that will not load.
        self._match_cache: dict[date, Day | None] = {}
        self.copy_button.set_sensitive(False)
        self.copy_button.connect("clicked", self._on_copy_clicked)
        # SPECIFICATION.md §3.5: most recent first, exactly App.archives'
        # order, never re-sorted here.
        self._dates = app.archives()
        self.date_list.connect("row-selected", self._on_row_selected)
        # GtkSearchEntry::search-changed already carries a ~150 ms debounce,
        # the "court délai anti-rebond" of §3.13; no timer of our own.
        self.search_entry.connect("search-changed", self._on_search_changed)
        if not self._dates:
            self.search_entry.set_sensitive(False)
            self.sidebar_stack.set_visible_child_name("empty")
            self.content_stack.set_visible_child_name("no-archives")
            return
        # Populates the list and selects the first date, which fires
        # _on_row_selected synchronously: the first archived day is read
        # before __init__ returns. Archives are small single-day files and
        # the window is not shown yet, so the blocking read is fine.
        self._apply_filter()

    def _on_row_selected(
        self, _list_box: Gtk.ListBox, row: Gtk.ListBoxRow | None
    ) -> None:
        if row is None or row.day_date == self._shown_date:
            # None: the list was cleared to re-filter. Same date: the row
            # object is new after that rebuild but the shown day has not
            # changed, so there is nothing to redraw.
            return
        # Read the date the row carries, never self._dates[row.get_index()]:
        # that couples correctness to the row order in the ListBox, the
        # coupling removed from RatureWindow in #38.
        self._show_day(row.day_date)

    def _on_search_changed(self, _entry: Gtk.SearchEntry) -> None:
        self._apply_filter()

    def _apply_filter(self) -> None:
        # SPECIFICATION.md §3.13: filter the date list to the days holding a
        # task whose text matches the query; a blank query shows every date.
        # Order stays App.archives'; no count, no preview (§3.5).
        query = self.search_entry.get_text().strip()
        if query:
            visible = [
                day_date
                for day_date in self._dates
                if (day := self._archived_day(day_date)) is not None
                and self.app.archive_matches(day, query)
            ]
        else:
            visible = list(self._dates)
        list_helpers.clear(self.date_list)
        for day_date in visible:
            self.date_list.append(ArchiveDateRow(day_date))
        if not visible:
            # Archives exist (the no-archives case returned early in
            # __init__); the query just matched none. §3.13: a status page
            # in the sidebar, an emptied content pane, Copy as text back to
            # insensitive.
            self.sidebar_stack.set_visible_child_name("no-match")
            list_helpers.clear(self.struck_list)
            list_helpers.clear(self.active_list)
            self.content_stack.set_visible_child_name("no-match")
            self._shown_date = None
            self.copy_button.set_sensitive(False)
            return
        self.sidebar_stack.set_visible_child_name("dates")
        # §3.13: keep the shown date selected when it survives the filter,
        # otherwise fall back to the first remaining date.
        row = next(
            (
                candidate
                for candidate in list_helpers.rows(self.date_list)
                if candidate.day_date == self._shown_date
            ),
            self.date_list.get_row_at_index(0),
        )
        self.date_list.select_row(row)

    def _archived_day(self, day_date: date) -> Day | None:
        if day_date not in self._match_cache:
            try:
                self._match_cache[day_date] = self.app.read_archive(day_date)
            except (OSError, ValueError, KeyError, TypeError, FutureVersionError):
                self._match_cache[day_date] = None
        return self._match_cache[day_date]

    def _show_day(self, day_date: date) -> None:
        # SPECIFICATION.md §3.2's header format, reused as-is: same
        # weekday-day-month long form as the Day view's title. The widget
        # lives in the .ui; only its text changes as the selection moves.
        self.title.set_title(day_date.strftime("%A %d %B"))
        list_helpers.clear(self.struck_list)
        list_helpers.clear(self.active_list)
        day = self._archived_day(day_date)
        if day is None:
            self.content_stack.set_visible_child_name("unreadable")
            self._shown_date = None
            self.copy_button.set_sensitive(False)
            return
        # SPECIFICATION.md §3.2: block order is Session.view()'s, never
        # recomputed here. archive_session_from wraps the Day _archived_day
        # already parsed and cached, so moving between dates does no file
        # I/O once each archive has been read.
        session = self.app.archive_session_from(day)
        self._shown_date = day_date
        self.copy_button.set_sensitive(True)
        for task in session.struck:
            self.struck_list.append(ArchiveTaskRow(task))
        for task in session.active:
            self.active_list.append(ArchiveTaskRow(task))
        self.struck_list.set_visible(bool(session.struck))
        self.active_list.set_visible(bool(session.active))
        self.content_stack.set_visible_child_name(
            "tasks" if session.day.tasks else "empty"
        )

    def _on_copy_clicked(self, _button: Gtk.Button) -> None:
        # SPECIFICATION.md §3.12: the shown archived day to the clipboard,
        # plain text, no feedback. The button is insensitive when nothing
        # readable is shown, so _shown_date is set here.
        if self._shown_date is None:
            return
        try:
            text = self.app.archived_day_text(self._shown_date)
        except (OSError, ValueError, KeyError, TypeError, FutureVersionError):
            return
        self.get_clipboard().set_content(Gdk.ContentProvider.new_for_value(text))
