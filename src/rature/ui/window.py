# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The main window. Its layout lives in data/ui/window.ui."""

import sys
import traceback
from gettext import gettext as _

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk  # noqa: E402

from rature.core.app import App, LockedError, StartupOutcome  # noqa: E402
from rature.ui import APP_ID  # noqa: E402
from rature.ui.day_view import DayView  # noqa: E402
from rature.ui.recurring_view import RecurringView  # noqa: E402
from rature.ui.reserve_view import ReserveView  # noqa: E402

# SPECIFICATION.md §3.1: the day may roll over while the app stays open.
_ENSURE_DAY_INTERVAL_SECONDS = 60


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/window.ui")
class RatureWindow(Adw.ApplicationWindow):
    """Owns the App instance and mounts the Day, Reserve and Recurring views."""

    __gtype_name__ = "RatureWindow"

    split_view: Adw.NavigationSplitView = Gtk.Template.Child()
    sidebar_list: Gtk.ListBox = Gtk.Template.Child()
    day_sidebar_row: Gtk.ListBoxRow = Gtk.Template.Child()
    reserve_sidebar_row: Gtk.ListBoxRow = Gtk.Template.Child()
    recurring_sidebar_row: Gtk.ListBoxRow = Gtk.Template.Child()
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
        self.reserve_view = ReserveView(
            app=app,
            run_action=self._run_app_action,
            perform=self._perform,
            send_to_day=self.send_to_day,
        )
        self.reserve_page.set_child(self.reserve_view)
        self.recurring_view = RecurringView(app=app, run_action=self._run_app_action)
        self.recurring_page.set_child(self.recurring_view)

        # Each sidebar row carries the content page it selects, so
        # _on_row_selected never depends on the row order in window.ui.
        self.day_sidebar_row.page = self.day_page
        self.reserve_sidebar_row.page = self.reserve_page
        self.recurring_sidebar_row.page = self.recurring_page

        # SPECIFICATION.md §3.7: collapsed AdwNavigationSplitView shows the
        # sidebar page unless show-content is set, so a narrow window would
        # otherwise open on the sidebar list instead of the Day view.
        self.split_view.set_show_content(True)

        # SPECIFICATION.md §3.3: a reserve row dragged onto the Day sidebar
        # entry draws it into the day. COPY, not MOVE: the source row
        # leaves the reserve as a business consequence of draw_from_reserve,
        # refreshed away by _refresh_all, never by a widget removal here.
        drop_target = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.COPY)
        drop_target.connect("accept", self._on_sidebar_drop_accept)
        drop_target.connect("drop", self._on_sidebar_drop)
        self.day_sidebar_row.add_controller(drop_target)

        self._settings = Gio.Settings.new(APP_ID)
        self._restore_geometry()
        self.connect("close-request", self._on_close_request)
        self.connect("destroy", self._on_destroy)
        self.sidebar_list.connect("row-selected", self._on_row_selected)
        self.sidebar_list.connect("row-activated", self._on_row_activated)

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
        self.day_view.refresh()
        self.reserve_view.refresh()
        self.recurring_view.refresh()

    def send_to_day(self, item_id: str) -> None:
        # SPECIFICATION.md §3.3: the Reserve view's send button and the
        # sidebar entry's drop target call this one method, never two
        # parallel paths. Goes through _run_app_action like every mutation:
        # the item may have vanished between drag start and drop (a day
        # rollover on the timer, say), so an unknown id raises KeyError,
        # which §3.6 already swallows and logs.
        self._run_app_action(lambda: self.app.draw_from_reserve(item_id))

    def _on_sidebar_drop_accept(self, _target: Gtk.DropTarget, _drop: Gdk.Drop) -> bool:
        # SPECIFICATION.md §3.3: a frozen day list refuses the drop and its
        # row never highlights, so the refusal happens here in accept, not
        # in drop. The lock is read live every attempt: the list can be
        # frozen while the app runs. GdkDrop has not read the payload yet
        # at this point, so this may only look at the lock and the type
        # (the type is already filtered by the DropTarget's gtype).
        return not self.app.session.day.locked

    def _on_sidebar_drop(
        self, _target: Gtk.DropTarget, value: str, _x: float, _y: float
    ) -> bool:
        self.send_to_day(value)
        return True

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
        self.split_view.set_content(row.page)

    def _on_row_activated(self, _list_box: Gtk.ListBox, _row: Gtk.ListBoxRow) -> None:
        # SPECIFICATION.md §3.7: a click always navigates to the content
        # page while collapsed, even when the row was already selected
        # (returning to Day after the back button), a case "row-selected"
        # does not fire for since the selection itself did not change.
        self.split_view.set_show_content(True)

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
