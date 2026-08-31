# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""One row in the Day view's two blocks. SPECIFICATION.md §3.2."""

from __future__ import annotations

from gettext import gettext as _
from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, Gtk  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App
    from rature.core.models import Task


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/task_row.ui")
class TaskRow(Gtk.ListBoxRow):
    """Number, text, strike button, row menu (Rename, then Delete)."""

    __gtype_name__ = "RatureTaskRow"

    num_label: Gtk.Label = Gtk.Template.Child()
    text_label: Gtk.Label = Gtk.Template.Child()
    rename_entry: Gtk.Entry = Gtk.Template.Child()
    strike_button: Gtk.Button = Gtk.Template.Child()
    row_popover: Gtk.Popover = Gtk.Template.Child()
    rename_button: Gtk.Button = Gtk.Template.Child()
    delete_button: Gtk.Button = Gtk.Template.Child()

    def __init__(
        self,
        task: Task,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        perform: Callable[[Callable[[], None]], bool],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.task = task
        self.app = app
        self.run_action = run_action
        self.perform = perform

        self.num_label.set_label(str(task.num))
        self.text_label.set_label(task.text)
        if task.done:
            self.text_label.add_css_class("rature-struck")
            self.strike_button.set_icon_name("edit-undo-symbolic")
            self.strike_button.set_tooltip_text(_("Undo the strike"))
        else:
            self.strike_button.set_icon_name("object-select-symbolic")
            self.strike_button.set_tooltip_text(_("Strike through"))

        self.strike_button.connect("clicked", self._on_strike_clicked)
        self.rename_button.connect("clicked", self._on_rename_clicked)
        self.delete_button.connect("clicked", self._on_delete_clicked)

        self._editing = False
        self.rename_entry.connect(
            "activate", lambda _entry: self.commit_pending_rename()
        )
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_rename_key_pressed)
        self.rename_entry.add_controller(key_controller)
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect("leave", lambda _c: self.commit_pending_rename())
        self.rename_entry.add_controller(focus_controller)

    def _on_strike_clicked(self, _button: Gtk.Button) -> None:
        if self.task.done:
            self.run_action(lambda: self.app.unstrike(self.task.id))
        else:
            self.run_action(lambda: self.app.strike(self.task.id))

    def _on_delete_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.run_action(lambda: self.app.delete(self.task.id))

    def _on_rename_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self._editing = True
        self.rename_entry.set_text(self.task.text)
        self.text_label.set_visible(False)
        self.rename_entry.set_visible(True)
        self.rename_entry.grab_focus()
        self.rename_entry.select_region(0, -1)

    def _on_rename_key_pressed(
        self, _controller: Gtk.EventControllerKey, keyval: int, _keycode: int, _state
    ) -> bool:
        if keyval == Gdk.KEY_Escape:
            self._cancel_rename()
            return True
        return False

    def _cancel_rename(self) -> None:
        # SPECIFICATION.md §3.2: Escape discards the typed text outright,
        # unlike Enter or losing focus, which both commit.
        if not self._editing:
            return
        self._editing = False
        self.rename_entry.set_visible(False)
        self.text_label.set_visible(True)

    def commit_pending_rename(self) -> None:
        """Validate an in-progress rename. A no-op if not editing.

        Never triggers a view refresh: called both on Enter/focus-out and,
        by DayView, to flush a pending edit before it rebuilds every row.
        The label is updated locally instead, which is enough either way.
        """
        if not self._editing:
            return
        text = self.rename_entry.get_text().strip()
        self._editing = False
        self.rename_entry.set_visible(False)
        self.text_label.set_visible(True)
        if text and text != self.task.text:
            self.text_label.set_label(text)
            self.perform(lambda: self.app.rename(self.task.id, text))
