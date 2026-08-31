# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The main window. Its layout lives in data/ui/window.ui."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, Gtk  # noqa: E402

from rature.core.app import App  # noqa: E402
from rature.ui import APP_ID  # noqa: E402


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/window.ui")
class RatureWindow(Adw.ApplicationWindow):
    """Owns the App instance for the process. Content is still a placeholder."""

    __gtype_name__ = "RatureWindow"

    split_view: Adw.NavigationSplitView = Gtk.Template.Child()
    sidebar_list: Gtk.ListBox = Gtk.Template.Child()
    day_page: Adw.NavigationPage = Gtk.Template.Child()
    reserve_page: Adw.NavigationPage = Gtk.Template.Child()
    recurring_page: Adw.NavigationPage = Gtk.Template.Child()

    def __init__(self, *, app: App, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app = app
        self._settings = Gio.Settings.new(APP_ID)
        self._restore_geometry()
        self.connect("close-request", self._on_close_request)
        self.sidebar_list.connect("row-selected", self._on_row_selected)

    def _on_row_selected(
        self, _list_box: Gtk.ListBox, row: Gtk.ListBoxRow | None
    ) -> None:
        if row is None:
            return
        # Fixed order, matching the sidebar rows in window.ui:
        # Day, Reserve, Recurring (SPECIFICATION.md §3.1).
        pages = (self.day_page, self.reserve_page, self.recurring_page)
        self.split_view.set_content(pages[row.get_index()])

    def _restore_geometry(self) -> None:
        self.set_default_size(
            self._settings.get_int("window-width"),
            self._settings.get_int("window-height"),
        )
        if self._settings.get_boolean("window-maximized"):
            self.maximize()

    def _on_close_request(self, _window: Gtk.Window) -> bool:
        # SPECIFICATION.md §3.1: no Gio.Settings.bind on width/height, they
        # would otherwise capture the maximized window's dimensions as if
        # they were the user's chosen size.
        maximized = self.is_maximized()
        self._settings.set_boolean("window-maximized", maximized)
        if not maximized:
            width, height = self.get_default_size()
            self._settings.set_int("window-width", width)
            self._settings.set_int("window-height", height)
        return False
