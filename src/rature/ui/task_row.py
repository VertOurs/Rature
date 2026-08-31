# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One row in the Day view's two blocks. Read-only: SPECIFICATION.md §3.2."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402

if TYPE_CHECKING:
    from rature.core.models import Task


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/task_row.ui")
class TaskRow(Gtk.ListBoxRow):
    """Number and text only; row controls arrive with chantier 3 step 4."""

    __gtype_name__ = "RatureTaskRow"

    num_label: Gtk.Label = Gtk.Template.Child()
    text_label: Gtk.Label = Gtk.Template.Child()

    def __init__(self, task: Task, **kwargs) -> None:
        super().__init__(**kwargs)
        self.num_label.set_label(str(task.num))
        self.text_label.set_label(task.text)
        if task.done:
            self.text_label.add_css_class("rature-struck")
