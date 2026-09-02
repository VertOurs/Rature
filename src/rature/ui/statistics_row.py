# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One row of the Statistics window's table. SPECIFICATION.md §3.14."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/statistics_row.ui")
class StatisticsRow(Gtk.Box):
    """A day label and its four counts. Every cell is set here, none translatable.

    Takes plain values, not a core object: the window feeds it one row of
    App.statistics() already formatted.
    """

    __gtype_name__ = "RatureStatisticsRow"

    date_cell: Gtk.Label = Gtk.Template.Child()
    added_cell: Gtk.Label = Gtk.Template.Child()
    struck_cell: Gtk.Label = Gtk.Template.Child()
    deleted_cell: Gtk.Label = Gtk.Template.Child()
    reserve_cell: Gtk.Label = Gtk.Template.Child()

    def __init__(
        self,
        *,
        date_text: str,
        added: int,
        struck: int,
        deleted: int,
        to_reserve: int,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.date_cell.set_text(date_text)
        self.added_cell.set_text(str(added))
        self.struck_cell.set_text(str(struck))
        self.deleted_cell.set_text(str(deleted))
        self.reserve_cell.set_text(str(to_reserve))
