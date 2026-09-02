# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Statistics window: SPECIFICATION.md §3.14. Read-only, opened from the menu."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402

from rature.ui.statistics_row import StatisticsRow  # noqa: E402

if TYPE_CHECKING:
    from rature.core.app import App


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/statistics_window.ui")
class StatisticsWindow(Adw.Window):
    """A table of per-day archive counts, most recent first, with a Total row.

    Built fresh every time the menu action opens it, so it always reflects
    the current archive/ directory rather than a stale snapshot.
    """

    __gtype_name__ = "RatureStatisticsWindow"

    stack: Gtk.Stack = Gtk.Template.Child()
    rows: Gtk.ListBox = Gtk.Template.Child()
    total_added: Gtk.Label = Gtk.Template.Child()
    total_struck: Gtk.Label = Gtk.Template.Child()
    total_deleted: Gtk.Label = Gtk.Template.Child()
    total_reserve: Gtk.Label = Gtk.Template.Child()

    def __init__(self, *, app: App, **kwargs) -> None:
        super().__init__(**kwargs)
        # SPECIFICATION.md §3.14: App.statistics' order, most recent first,
        # never re-sorted here; unreadable archives are already dropped.
        stats = app.statistics()
        if not stats:
            self.stack.set_visible_child_name("empty")
            return
        added = struck = deleted = to_reserve = 0
        for day_date, counts in stats:
            self.rows.append(
                StatisticsRow(
                    date_text=day_date.strftime("%d %B %Y"),
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
        # SPECIFICATION.md §3.14: the "par période" figure is a plain sum,
        # no average, no ratio, no projection.
        self.total_added.set_text(str(added))
        self.total_struck.set_text(str(struck))
        self.total_deleted.set_text(str(deleted))
        self.total_reserve.set_text(str(to_reserve))
        self.stack.set_visible_child_name("table")
