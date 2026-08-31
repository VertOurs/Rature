# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Adw.Application subclass: process lifecycle, actions, shortcuts."""

from gettext import gettext as _
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, Gtk  # noqa: E402

from rature import config  # noqa: E402
from rature.core import storage  # noqa: E402
from rature.core.app import App  # noqa: E402
from rature.core.migrations import FutureVersionError  # noqa: E402
from rature.ui import APP_ID  # noqa: E402
from rature.ui.window import RatureWindow  # noqa: E402


class RatureApplication(Adw.Application):
    """Owns the single main window, the App instance, and the app-wide actions."""

    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._app: App | None = None
        self._add_action("quit", self._on_quit, accels=["<primary>q"])
        self._add_action("about", self._on_about)

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        provider = Gtk.CssProvider()
        provider.load_from_resource("/io/github/vertours/Rature/style.css")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _add_action(self, name, callback, accels=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if accels:
            self.set_accels_for_action(f"app.{name}", accels)

    def do_activate(self) -> None:
        # SPECIFICATION.md §3.1: App is built once, before any window, and
        # kept; nothing else calls App.open.
        if self._app is None:
            data_dir = storage.xdg_data_dir()
            try:
                self._app = App.open(data_dir)
            except FutureVersionError:
                self._show_future_version_error_and_quit(
                    storage.main_file_path(data_dir=data_dir)
                )
                return

        window = self.props.active_window or RatureWindow(
            application=self, app=self._app
        )
        window.present()

    def _show_future_version_error_and_quit(self, path: Path) -> None:
        # SPECIFICATION.md §3.6 point 1: no window exists yet, so hold() is
        # what keeps the process alive long enough for the alert to show;
        # without it GApplication would shut down the moment do_activate
        # returns, before the async dialog is even visible.
        self.hold()
        dialog = Gtk.AlertDialog()
        dialog.set_message(_("This file was saved by a newer version of Rature."))
        dialog.set_detail(
            _("Opening it could overwrite data. Update Rature to open this file: %s")
            % path
        )
        dialog.set_buttons([_("Quit")])
        dialog.choose(None, None, self._on_future_version_dialog_response)

    def _on_future_version_dialog_response(self, dialog, result) -> None:
        dialog.choose_finish(result)
        self.release()
        self.quit()

    def _on_about(self, _action, _param) -> None:
        dialog = Adw.AboutDialog(
            application_name="Rature",
            version=config.VERSION,
            developer_name="VertOurs",
            license_type=Gtk.License.GPL_3_0,
            website="https://github.com/VertOurs/Rature",
            issue_url="https://github.com/VertOurs/Rature/issues",
            application_icon=APP_ID,
        )
        dialog.present(self.props.active_window)

    def _on_quit(self, _action, _param) -> None:
        self.quit()
