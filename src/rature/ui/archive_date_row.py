# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One entry in the Archives window's sidebar. SPECIFICATION.md §3.5."""

from __future__ import annotations

from datetime import date

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/archive_date_row.ui")
class ArchiveDateRow(Adw.ActionRow):
    """A single archived date, most recent first order set by the caller."""

    __gtype_name__ = "RatureArchiveDateRow"

    def __init__(self, day_date: date, **kwargs) -> None:
        super().__init__(**kwargs)
        self.day_date = day_date
        # SPECIFICATION.md §3.5: no count, no preview, no summary next to
        # a date, so the title is the formatted date and nothing else.
        self.set_title(day_date.strftime("%d %B %Y"))
