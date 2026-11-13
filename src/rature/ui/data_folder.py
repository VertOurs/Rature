# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The dialogs that lead to joining a data folder (SPECIFICATION.md §3.17).

The same steps from the main menu, where an App and a window exist, and
from the message of a folder out of reach, where neither may exist: pick a
folder through the portal, examine it, say what joining will do, join. What
examining and joining mean is handed in, the dialogs are the same.
"""

import logging
from collections.abc import Callable
from gettext import gettext as _
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

from rature.core import storage  # noqa: E402
from rature.core.app import (  # noqa: E402
    FolderChangedError,
    FolderPreview,
    JoinRefusal,
    JoinRefusedError,
)

_logger = logging.getLogger(__name__)

_CANCEL = "cancel"
_CONFIRM = "confirm"


def alert(
    parent: Gtk.Widget | None,
    heading: str,
    lines: list[str],
    responses: list[tuple[str, str]],
    on_response: Callable[[str], None],
    *,
    close_response: str,
    suggested: str | None = None,
    destructive: str | None = None,
) -> None:
    """An AdwAlertDialog, on parent's window or as a window of its own."""
    dialog = Adw.AlertDialog()
    dialog.set_heading(heading)
    dialog.set_body("\n\n".join(lines))
    for response_id, label in responses:
        dialog.add_response(response_id, label)
    if suggested is not None:
        dialog.set_response_appearance(suggested, Adw.ResponseAppearance.SUGGESTED)
    if destructive is not None:
        dialog.set_response_appearance(destructive, Adw.ResponseAppearance.DESTRUCTIVE)
    # Escape, and the default for Enter: never a write by accident.
    dialog.set_close_response(close_response)
    dialog.set_default_response(close_response)

    def on_chosen(source: Adw.AlertDialog, result: Gio.AsyncResult) -> None:
        on_response(source.choose_finish(result))

    dialog.choose(parent, None, on_chosen)


def _wait_for_first_sync() -> str:
    return _(
        "If this folder is synced, wait until its first sync "
        "has finished before copying."
    )


class FolderJoiner:
    """From the portal's folder picker to the join, one folder at a time.

    examine raises JoinRefusedError for a folder that cannot be joined.
    join returns the FolderChangedError of a folder that changed since its
    dialog showed, None once the join went its way. back runs when the user
    leaves without joining: cancelled, refused, or no folder picked.
    """

    def __init__(
        self,
        *,
        parent: Gtk.Window | None,
        examine: Callable[[Path], FolderPreview],
        join: Callable[[FolderPreview], FolderChangedError | None],
        has_local_data: bool,
        back: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._examine = examine
        self._join = join
        self._has_local_data = has_local_data
        self._back = back

    def choose(self) -> None:
        # Through the portal under Flatpak: the manifest gains no file
        # system permission (§3.17).
        Gtk.FileDialog().select_folder(self._parent, None, self._on_folder_picked)

    def _on_folder_picked(
        self, source: Gtk.FileDialog, result: Gio.AsyncResult
    ) -> None:
        try:
            picked = source.select_folder_finish(result)
        except GLib.Error:
            # Dismissed, the usual case: nothing to tell.
            self._back()
            return
        path = picked.get_path() if picked is not None else None
        if path is None:
            # A location with no local path, which the portal does not hand out.
            _logger.warning("the picked folder has no local path")
            self._back()
            return
        try:
            preview = self._examine(Path(path))
        except JoinRefusedError as refused:
            self._refuse(refused.folder, refused.reason)
        else:
            self._offer(preview)

    def _refuse(self, folder: Path, reason: JoinRefusal) -> None:
        data_file = storage.main_file_path(data_dir=folder)
        if reason is JoinRefusal.UNREADABLE:
            detail = _("Its data file cannot be read: %s") % data_file
        elif reason is JoinRefusal.NEWER_VERSION:
            detail = (
                _("Its data file was saved by a newer version of Rature: %s")
                % data_file
            )
        elif reason is JoinRefusal.CURRENT_FOLDER:
            detail = _("This is already the data folder: %s") % folder
        else:
            detail = _("This folder cannot be read: %s") % folder
        alert(
            self._parent,
            _("This folder cannot be used."),
            [detail],
            [(_CANCEL, _("Close"))],
            lambda _response: self._back(),
            close_response=_CANCEL,
        )

    def _offer(self, preview: FolderPreview) -> None:
        lines: list[str] = []
        destructive = None
        if preview.has_data:
            heading = _("Use the data in this folder?")
            if preview.set_aside_as is not None:
                lines.append(
                    _(
                        "Your current data will be set aside as %s, "
                        "in the previous folder."
                    )
                    % preview.set_aside_as.name
                )
            confirm = _("Use This Folder")
        elif self._has_local_data:
            heading = _("Copy your data to this folder?")
            lines.append(_wait_for_first_sync())
            confirm = _("Copy Data Here")
        else:
            # Nothing to set aside or copy: the empty day of §3.6, written
            # into the folder as soon as it is confirmed. On a second
            # computer, an empty folder has most often not finished its
            # first sync: the empty day would go to the other device.
            heading = _("Start from an empty day?")
            lines.append(
                _(
                    "This empty day will also replace the data "
                    "on your other synced devices."
                )
            )
            lines.append(_wait_for_first_sync())
            confirm = _("Start Empty")
            destructive = _CONFIRM
        if preview.archives_stay_in is not None:
            lines.append(
                _("Archives stay in the previous folder: %s") % preview.archives_stay_in
            )
        if preview.other_files:
            lines.append(_("This folder also contains other files."))

        def on_response(response: str) -> None:
            if response != _CONFIRM:
                self._back()
                return
            changed = self._join(preview)
            if changed is None:
                return
            # §3.17: nothing was written, the dialog says what is there now.
            if changed.preview is not None:
                self._offer(changed.preview)
            else:
                self._refuse(preview.folder, changed.refusal)

        alert(
            self._parent,
            heading,
            lines,
            [(_CANCEL, _("Cancel")), (_CONFIRM, confirm)],
            on_response,
            close_response=_CANCEL,
            suggested=None if destructive else _CONFIRM,
            destructive=destructive,
        )
