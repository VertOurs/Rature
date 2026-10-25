# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""A recurring task due tomorrow, read-only. SPECIFICATION.md §3.16."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402

if TYPE_CHECKING:
    from rature.core.models import RecurringItem


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/tomorrow_recurring_row.ui")
class TomorrowRecurringRow(Gtk.ListBoxRow):
    """Text only: no number, no button, no menu, no drag (§3.16)."""

    __gtype_name__ = "RatureTomorrowRecurringRow"

    spacer: Gtk.Button = Gtk.Template.Child()
    text_label: Gtk.Label = Gtk.Template.Child()

    def __init__(self, item: RecurringItem, **kwargs) -> None:
        super().__init__(**kwargs)
        # Neither drawn nor focusable, but keeps its width.
        self.spacer.set_child_visible(False)
        self.text_label.set_label(item.text)
