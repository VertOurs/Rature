# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The main window. Its layout lives in data/ui/window.ui."""

import sys
import traceback
from gettext import gettext as _

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

from rature.core.app import App, LockedError, StartupOutcome  # noqa: E402
from rature.ui import APP_ID  # noqa: E402
from rature.ui.day_view import DayView  # noqa: E402

# SPECIFICATION.md §3.1: the day may roll over while the app stays open.
_ENSURE_DAY_INTERVAL_SECONDS = 60


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/window.ui")
class RatureWindow(Adw.ApplicationWindow):
    """Owns the App instance. Reserve and Recurring panes are placeholders."""

    __gtype_name__ = "RatureWindow"

    split_view: Adw.NavigationSplitView = Gtk.Template.Child()
    sidebar_list: Gtk.ListBox = Gtk.Template.Child()
    day_page: Adw.NavigationPage = Gtk.Template.Child()
    reserve_page: Adw.NavigationPage = Gtk.Template.Child()
    recurring_page: Adw.NavigationPage = Gtk.Template.Child()

    def __init__(self, *, app: App, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app = app
        self.day_view = DayView(
            app=app, run_action=self._run_app_action, perform=self._perform
        )
        self.day_page.set_child(self.day_view)
        self._settings = Gio.Settings.new(APP_ID)
        self._restore_geometry()
        self.connect("close-request", self._on_close_request)
        self.connect("destroy", self._on_destroy)
        self.sidebar_list.connect("row-selected", self._on_row_selected)

        self._write_failure_active = False
        self._quarantine_dismissed = False
        self._new_day_pending = False
        self._new_day_dismissed = False
        self.day_view.banner.connect("button-clicked", self._on_banner_button_clicked)
        # StartupOutcome.RECOVERED_FROM_CORRUPTION is already known at this
        # point; show its banner immediately, not after the first tick.
        self._update_banner()

        self._timer_id = GLib.timeout_add_seconds(
            _ENSURE_DAY_INTERVAL_SECONDS, self._on_ensure_day_tick
        )

    def _on_destroy(self, _window: Gtk.Window) -> None:
        GLib.source_remove(self._timer_id)

    def _on_ensure_day_tick(self) -> bool:
        def tick() -> None:
            archived = self.app.ensure_day()
            if archived is not None:
                self._new_day_pending = True
                self._new_day_dismissed = False

        self._run_app_action(tick)
        return GLib.SOURCE_CONTINUE

    def _refresh_all(self) -> None:
        # Reserve and Recurring add their own line here, chantier 3 steps
        # 6 and 8.
        self.day_view.refresh()

    def _perform(self, action) -> bool:
        # SPECIFICATION.md §3.6 point 3: the one place that catches OSError,
        # for every action. LockedError/KeyError/ValueError are refused
        # business commands the interface should have made impossible by
        # disabling the control; per §3.6's "Refus métier" they are a bug,
        # logged and swallowed, never shown.
        try:
            action()
        except OSError:
            self._write_failure_active = True
            success = False
        except (LockedError, KeyError, ValueError):
            traceback.print_exc(file=sys.stderr)
            success = False
        else:
            self._write_failure_active = False
            success = True
        self._update_banner()
        return success

    def _run_app_action(self, action) -> bool:
        # App does not roll back an in-memory mutation on a save failure
        # (documented on the class), so the view refreshes unconditionally:
        # skipping it would leave the screen contradicting the session
        # until the next timer tick. For a business error nothing changed,
        # and the redraw is a no-op.
        success = self._perform(action)
        self._refresh_all()
        return success

    def _update_banner(self) -> None:
        # SPECIFICATION.md §3.6: one AdwBanner, one message at a time,
        # picked fresh on every call: write failure, then quarantine, then
        # new day. A dismissed message is skipped even if still "active".
        banner = self.day_view.banner
        if self._write_failure_active:
            banner.set_title(_("Changes could not be saved to disk."))
            banner.set_button_label("")
            banner.set_revealed(True)
        elif (
            self.app.startup is StartupOutcome.RECOVERED_FROM_CORRUPTION
            and not self._quarantine_dismissed
        ):
            banner.set_title(
                _("The data file could not be read. It was moved aside as %s.")
                % self.app.quarantined_path.name
            )
            banner.set_button_label(_("Dismiss"))
            banner.set_revealed(True)
        elif self._new_day_pending and not self._new_day_dismissed:
            banner.set_title(
                _("A new day has started. The previous one has been archived.")
            )
            banner.set_button_label(_("Dismiss"))
            banner.set_revealed(True)
        else:
            banner.set_revealed(False)

    def _on_banner_button_clicked(self, _banner: Adw.Banner) -> None:
        if (
            self.app.startup is StartupOutcome.RECOVERED_FROM_CORRUPTION
            and not self._quarantine_dismissed
        ):
            self._quarantine_dismissed = True
        else:
            self._new_day_dismissed = True
        self._update_banner()

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
