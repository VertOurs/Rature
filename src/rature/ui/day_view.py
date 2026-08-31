# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Day view: SPECIFICATION.md §3.2. Read-only for chantier 3 step 3."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402

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
        self.refresh()

    def refresh(self) -> None:
        session = self.app.session
        # SPECIFICATION.md §2.5: the reference date, never the calendar
        # date; between midnight and 04:00 they disagree.
        self.header.set_title_widget(
            Gtk.Label(label=session.day.date.strftime("%A %d %B"))
        )
        self._fill(self.struck_list, session.struck)
        self._fill(self.active_list, session.active)
        self.struck_list.set_visible(bool(session.struck))
        self.active_list.set_visible(bool(session.active))
        self.stack.set_visible_child_name("tasks" if session.day.tasks else "empty")

    @staticmethod
    def _fill(list_box: Gtk.ListBox, tasks: Iterable[Task]) -> None:
        while (row := list_box.get_row_at_index(0)) is not None:
            list_box.remove(row)
        for task in tasks:
            list_box.append(TaskRow(task))
