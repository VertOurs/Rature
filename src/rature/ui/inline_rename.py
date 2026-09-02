# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""In-place label editing, shared by the rows that carry an editable text."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, Gtk  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable


class InlineRename:
    """Swaps a label for an entry in place and commits the edited text.

    Composed by TaskRow and ReserveRow so the editing flag and the
    keyboard/focus wiring live in one place. SPECIFICATION.md §3.2: Enter
    and losing focus commit, Escape discards. Committing updates the label
    locally and calls ``commit`` with the new text; it never triggers a
    view refresh, so a caller may flush a pending edit before rebuilding
    its rows.
    """

    def __init__(
        self,
        *,
        entry: Gtk.Entry,
        label: Gtk.Label,
        current_text: Callable[[], str],
        commit: Callable[[str], None],
    ) -> None:
        self._entry = entry
        self._label = label
        self._current_text = current_text
        self._commit = commit
        self._editing = False

        entry.connect("activate", lambda _entry: self.commit())
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        entry.add_controller(key_controller)
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect("leave", lambda _controller: self.commit())
        entry.add_controller(focus_controller)

    def begin(self) -> None:
        """Show the entry primed with the current text, all of it selected."""
        self._editing = True
        self._entry.set_text(self._current_text())
        self._label.set_visible(False)
        self._entry.set_visible(True)
        self._entry.grab_focus()
        self._entry.select_region(0, -1)

    def commit(self) -> None:
        """Validate an in-progress edit. A no-op if not editing."""
        if not self._editing:
            return
        text = self._entry.get_text().strip()
        self._editing = False
        self._entry.set_visible(False)
        self._label.set_visible(True)
        if text and text != self._current_text():
            self._label.set_label(text)
            self._commit(text)

    def _on_key_pressed(
        self, _controller: Gtk.EventControllerKey, keyval: int, _keycode: int, _state
    ) -> bool:
        if keyval == Gdk.KEY_Escape:
            self._cancel()
            return True
        return False

    def _cancel(self) -> None:
        # SPECIFICATION.md §3.2: Escape discards the typed text outright,
        # unlike Enter or losing focus, which both commit.
        if not self._editing:
            return
        self._editing = False
        self._entry.set_visible(False)
        self._label.set_visible(True)
