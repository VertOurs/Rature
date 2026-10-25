# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Statistics window: SPECIFICATION.md §3.14. Read-only, opened from the menu."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402

from rature.ui import list_helpers  # noqa: E402
from rature.ui.statistics_row import StatisticsRow  # noqa: E402

if TYPE_CHECKING:
    from rature.core.app import App


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/statistics_window.ui")
class StatisticsWindow(Adw.Window):
    """A table of per-day archive counts, most recent first, with a Total row.

    Built fresh every time the menu action opens it, and rebuilt by
    refresh() when the day rollover archives a day while it is open
    (SPECIFICATION.md §3.14), so it never shows a stale snapshot.
    """

    __gtype_name__ = "RatureStatisticsWindow"

    stack: Gtk.Stack = Gtk.Template.Child()
    scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    rows: Gtk.ListBox = Gtk.Template.Child()
    total_added: Gtk.Label = Gtk.Template.Child()
    total_struck: Gtk.Label = Gtk.Template.Child()
    total_deleted: Gtk.Label = Gtk.Template.Child()
    total_reserve: Gtk.Label = Gtk.Template.Child()

    def __init__(self, *, app: App, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app = app
        self.refresh()

    def refresh(self) -> None:
        """Rebuild the table from the archives, keeping the scroll offset.

        SPECIFICATION.md §3.14: nothing draws attention to the change, no
        highlight and no jump back to the top.
        """
        # SPECIFICATION.md §3.14: App.statistics' order, most recent first,
        # never re-sorted here; unreadable archives are already dropped.
        stats = self.app.statistics()
        if not stats:
            self.stack.set_visible_child_name("empty")
            return
        with list_helpers.keeping_place(self.scrolled_window, self.rows):
            totals = self._fill(stats)
        added, struck, deleted, to_reserve = totals
        # SPECIFICATION.md §3.14: the "par période" figure is a plain sum,
        # no average, no ratio, no projection.
        self.total_added.set_text(str(added))
        self.total_struck.set_text(str(struck))
        self.total_deleted.set_text(str(deleted))
        self.total_reserve.set_text(str(to_reserve))
        self.stack.set_visible_child_name("table")

    def _fill(self, stats) -> tuple[int, int, int, int]:
        list_helpers.clear(self.rows)
        added = struck = deleted = to_reserve = 0
        for day_date, counts in stats:
            self.rows.append(
                StatisticsRow(
                    date_text=day_date.strftime("%A %d %B"),
                    added=counts.added,
                    struck=counts.struck,
                    deleted=counts.deleted,
                    to_reserve=counts.to_reserve,
                )
            )
            added += counts.added
            struck += counts.struck
            deleted += counts.deleted
            to_reserve += counts.to_reserve
        return added, struck, deleted, to_reserve
