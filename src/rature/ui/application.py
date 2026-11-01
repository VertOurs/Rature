# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The Adw.Application subclass: process lifecycle, actions, shortcuts."""

import logging
from collections.abc import Callable
from gettext import gettext as _
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from rature import config  # noqa: E402
from rature.core import storage  # noqa: E402
from rature.core.app import (  # noqa: E402
    App,
    DataFileMissingError,
    DataFileUnreadableError,
)
from rature.core.migrations import FutureVersionError  # noqa: E402
from rature.ui import APP_ID  # noqa: E402
from rature.ui.archives_window import ArchivesWindow  # noqa: E402
from rature.ui.statistics_window import StatisticsWindow  # noqa: E402
from rature.ui.window import RatureWindow  # noqa: E402

_logger = logging.getLogger(__name__)


class RatureApplication(Adw.Application):
    """Owns the single main window, the App instance, and the app-wide actions."""

    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._app: App | None = None
        self._held_for_dialogs = False
        # The window a re-read failed on, while its message is open (§3.6).
        self._failing_window: RatureWindow | None = None
        self._add_action("quit", self._on_quit, accels=["<primary>q"])
        self._add_action("about", self._on_about)
        self._add_action("archives", self._on_archives)
        self._add_action("statistics", self._on_statistics)

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        provider = Gtk.CssProvider()
        provider.load_from_resource("/io/github/vertours/Rature/style.css")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _add_action(self, name, callback, accels=None) -> None:
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if accels:
            self.set_accels_for_action(f"app.{name}", accels)

    def do_activate(self) -> None:
        # SPECIFICATION.md §3.1: App is built once, before any window, and
        # kept; nothing else calls App.open. A second launch while a startup
        # dialog is up must not start a second loop of dialogs.
        if self._app is not None:
            self._present_window()
        elif not self._held_for_dialogs:
            self._open_data(App.open)

    def _present_window(self) -> None:
        window = self.props.active_window or RatureWindow(
            application=self, app=self._app
        )
        window.present()
        self._release_after_dialogs()

    def report_read_failure(self, window: RatureWindow, error: Exception) -> None:
        """A re-read failed while running: the messages of §3.6, on the window.

        One at a time: the modal message takes the focus away from an open
        rename, whose commit fails the same way.
        """
        if self._failing_window is not None:
            return
        self._failing_window = window

        def fail_again() -> None:
            raise error

        self._settle(fail_again)

    def _data_folder(self) -> Path:
        if self._failing_window is not None:
            return self._failing_window.app.data_dir
        return storage.xdg_data_dir()

    def _open_data(self, opener: Callable[[Path], App]) -> None:
        def attempt() -> None:
            self._app = opener(storage.xdg_data_dir())

        self._settle(attempt)

    def _settle(self, attempt: Callable[[], object]) -> None:
        data_dir = self._data_folder()
        try:
            attempt()
        except FutureVersionError:
            # SPECIFICATION.md §3.6 situation 1.
            self._show_error_and_quit(
                _("This file was saved by a newer version of Rature."),
                _(
                    "Opening it could overwrite data. "
                    "Update Rature to open this file: %s"
                )
                % storage.main_file_path(data_dir=data_dir),
            )
        except OSError:
            # SPECIFICATION.md §3.6 situation 4: the cause (rights, space,
            # medium) is outside Rature, so nothing is retried or repaired.
            _logger.exception("cannot use the data folder %s", data_dir)
            self._show_folder_error(data_dir)
        except DataFileUnreadableError:
            self._show_unreadable_file_message()
        except DataFileMissingError:
            self._show_missing_file_message()
        else:
            if self._failing_window is None:
                self._present_window()
            else:
                window, self._failing_window = self._failing_window, None
                window.data_recovered()

    def _try_again(self) -> None:
        if self._failing_window is None:
            self._open_data(App.open)
        else:
            self._settle(self._failing_window.app.reread)

    def _show_unreadable_file_message(self) -> None:
        # SPECIFICATION.md §3.6 situation 2.
        path = storage.main_file_path(data_dir=self._data_folder())
        self._show_blocking_message(
            _("The data file cannot be read."),
            _("It may still be syncing, or it may be damaged: %s") % path,
            _("Set Aside and Start Empty")
            if self._failing_window is None
            else _("Set Aside and Save This Device's Data"),
            self._show_unreadable_file_message,
        )

    def _show_missing_file_message(self) -> None:
        # SPECIFICATION.md §3.6 situation 2.
        self._show_blocking_message(
            _("The data file is missing."),
            _("No data file was found in this folder: %s") % self._data_folder(),
            _("Start Empty")
            if self._failing_window is None
            else _("Save This Device's Data"),
            self._show_missing_file_message,
        )

    def _show_blocking_message(
        self,
        message: str,
        detail: str,
        way_out: str,
        show_again: Callable[[], None],
    ) -> None:
        try_again, confirm, leave = 0, 1, 2

        def on_choice(choice: int) -> None:
            if choice == try_again:
                self._try_again()
            elif choice == confirm:
                self._confirm_way_out(show_again)
            else:
                self._release_after_dialogs()
                self.quit()

        self._ask(
            message,
            detail,
            [_("Try Again"), way_out, _("Quit")],
            # Quitting while running discards the copy in memory: a deliberate
            # click, never Escape.
            cancel_button=leave if self._failing_window is None else try_again,
            default_button=try_again,
            on_choice=on_choice,
        )

    def _confirm_way_out(self, show_again: Callable[[], None]) -> None:
        cancel, confirm = 0, 1
        window = self._failing_window

        def on_choice(choice: int) -> None:
            if choice != confirm:
                show_again()
            elif window is None:
                self._open_data(App.start_empty)
            else:
                self._settle(window.app.save_device_data)

        if window is None:
            message = _("Start from an empty day?")
            detail = _(
                "This empty day will also replace the data "
                "on your other synced devices."
            )
            confirm_label = _("Start Empty")
        else:
            message = _("Save this device's data?")
            detail = _(
                "It will also replace the data on your other synced devices. "
                "Recent changes made on them may be lost."
            )
            confirm_label = _("Save This Device's Data")
        self._ask(
            message,
            detail,
            [_("Cancel"), confirm_label],
            cancel_button=cancel,
            default_button=cancel,
            on_choice=on_choice,
        )

    def _show_folder_error(self, data_dir: Path) -> None:
        # SPECIFICATION.md §3.6 situation 4.
        message = _("Rature could not use its data folder.")
        detail = (
            _(
                "Check that this folder can be read and written, "
                "and that the disk is not full: %s"
            )
            % data_dir
        )
        if self._failing_window is None:
            self._show_error_and_quit(message, detail)
            return
        # Quitting here would discard the copy in memory without a choice:
        # back to the message of situation 2, or to the data if it recovered.
        self._ask(
            message,
            detail,
            [_("Close")],
            cancel_button=0,
            default_button=0,
            on_choice=lambda _choice: self._try_again(),
        )

    def _show_error_and_quit(self, message: str, detail: str) -> None:
        # SPECIFICATION.md §3.6 situations 1 and 4.
        def on_choice(_choice: int) -> None:
            self._release_after_dialogs()
            self.quit()

        self._ask(
            message,
            detail,
            [_("Quit")],
            cancel_button=0,
            default_button=0,
            on_choice=on_choice,
        )

    def _ask(
        self,
        message: str,
        detail: str,
        buttons: list[str],
        *,
        cancel_button: int,
        default_button: int,
        on_choice: Callable[[int], None],
    ) -> None:
        # At startup no window exists yet, so hold() is what keeps the process
        # alive while a dialog shows: without it GApplication would shut down
        # the moment do_activate returns. One hold for the whole loop of
        # dialogs, released only once the window is open or on Quit, or the
        # process could end between two dialogs.
        parent = self._failing_window
        if parent is None and not self._held_for_dialogs:
            self.hold()
            self._held_for_dialogs = True
        dialog = Gtk.AlertDialog()
        dialog.set_message(message)
        dialog.set_detail(detail)
        dialog.set_buttons(buttons)
        dialog.set_cancel_button(cancel_button)
        dialog.set_default_button(default_button)

        def on_response(source: Gtk.AlertDialog, result: Gio.AsyncResult) -> None:
            try:
                choice = source.choose_finish(result)
            except GLib.Error:
                choice = cancel_button
            on_choice(choice)

        dialog.choose(parent, None, on_response)

    def _release_after_dialogs(self) -> None:
        if self._held_for_dialogs:
            self._held_for_dialogs = False
            self.release()

    def _on_archives(self, _action, _param) -> None:
        window = ArchivesWindow(
            app=self._app,
            application=self,
            transient_for=self.props.active_window,
        )
        window.present()

    def _on_statistics(self, _action, _param) -> None:
        window = StatisticsWindow(
            app=self._app,
            application=self,
            transient_for=self.props.active_window,
        )
        window.present()

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
