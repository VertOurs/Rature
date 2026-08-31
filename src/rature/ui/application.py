# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Adw.Application subclass: process lifecycle, actions, shortcuts."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio  # noqa: E402

from rature.ui.window import RatureWindow  # noqa: E402

APP_ID = "io.github.vertours.Rature"


class RatureApplication(Adw.Application):
    """Owns the single main window and the app-wide actions."""

    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._add_action("quit", self._on_quit, accels=["<primary>q"])

    def _add_action(self, name, callback, accels=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if accels:
            self.set_accels_for_action(f"app.{name}", accels)

    def do_activate(self) -> None:
        window = self.props.active_window or RatureWindow(application=self)
        window.present()

    def _on_quit(self, _action, _param) -> None:
        self.quit()
