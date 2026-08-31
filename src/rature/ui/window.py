# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The main window. Its layout lives in data/ui/window.ui."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402

from rature.core.app import App  # noqa: E402


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/window.ui")
class RatureWindow(Adw.ApplicationWindow):
    """Owns the App instance for the process. Content is still a placeholder."""

    __gtype_name__ = "RatureWindow"

    def __init__(self, *, app: App, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app = app
