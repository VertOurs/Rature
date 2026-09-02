# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""A read-only row in the Archives window's day content. SPECIFICATION.md §3.5."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402

if TYPE_CHECKING:
    from rature.core.models import Task


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/archive_task_row.ui")
class ArchiveTaskRow(Gtk.ListBoxRow):
    """Number and text only: SPECIFICATION.md §3.5 forbids any button or menu."""

    __gtype_name__ = "RatureArchiveTaskRow"

    num_label: Gtk.Label = Gtk.Template.Child()
    text_label: Gtk.Label = Gtk.Template.Child()

    def __init__(self, task: Task, **kwargs) -> None:
        super().__init__(**kwargs)
        self.num_label.set_label(str(task.num))
        self.text_label.set_label(task.text)
        if task.done:
            self.text_label.add_css_class("rature-struck")
