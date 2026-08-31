# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Create or edit one recurring template. SPECIFICATION.md §3.4."""

from __future__ import annotations

from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk  # noqa: E402

from rature.ui import weekdays  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App
    from rature.core.models import RecurringItem


@Gtk.Template(resource_path="/io/github/vertours/Rature/ui/recurring_form.ui")
class RecurringForm(Adw.Dialog):
    """A text field and seven weekday toggles, Monday first.

    One dialog for both create and edit. It keeps the template id, not
    the object: the 60-second timer may rebuild the session between the
    dialog opening and Save, so the write goes back by id. An id that no
    longer exists raises KeyError, which SPECIFICATION.md §3.6 swallows.
    """

    __gtype_name__ = "RatureRecurringForm"

    text_entry: Gtk.Entry = Gtk.Template.Child()
    days_box: Gtk.Box = Gtk.Template.Child()
    cancel_button: Gtk.Button = Gtk.Template.Child()
    save_button: Gtk.Button = Gtk.Template.Child()

    def __init__(
        self,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        item: RecurringItem | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.app = app
        self.run_action = run_action
        self._item_id = item.id if item is not None else None

        self._day_toggles: list[Gtk.ToggleButton] = []
        toggle = self.days_box.get_first_child()
        weekday = 0
        while toggle is not None:
            # Labels are set here, never in the .ui: they are locale
            # abbreviations (Mon/lun.), with the full name as a tooltip.
            toggle.set_label(weekdays.abbrev(weekday))
            toggle.set_tooltip_text(weekdays.full(weekday))
            toggle.connect("toggled", lambda _t: self._validate())
            self._day_toggles.append(toggle)
            toggle = toggle.get_next_sibling()
            weekday += 1

        if item is not None:
            self.text_entry.set_text(item.text)
            for day in item.weekdays:
                self._day_toggles[day].set_active(True)

        self.text_entry.connect("changed", lambda _e: self._validate())
        self.cancel_button.connect("clicked", lambda _b: self.close())
        self.save_button.connect("clicked", self._on_save_clicked)
        self._validate()

    def _selected_weekdays(self) -> list[int]:
        return [i for i, toggle in enumerate(self._day_toggles) if toggle.get_active()]

    def _validate(self) -> None:
        # SPECIFICATION.md §2.7.2: Save stays insensitive until there is
        # text and at least one day. core refuses an empty weekday list
        # too, the two barriers are deliberate.
        has_text = bool(self.text_entry.get_text().strip())
        has_day = bool(self._selected_weekdays())
        self.save_button.set_sensitive(has_text and has_day)

    def _on_save_clicked(self, _button: Gtk.Button) -> None:
        text = self.text_entry.get_text().strip()
        weekdays_selected = self._selected_weekdays()
        if self._item_id is None:
            saved = self.run_action(
                lambda: self.app.add_recurring(text, weekdays_selected)
            )
        else:
            saved = self.run_action(
                lambda: self.app.edit_recurring(
                    self._item_id, text=text, weekdays=weekdays_selected
                )
            )
        # SPECIFICATION.md §3.6: on a write failure the mutation is not
        # rolled back but nothing is persisted; keep the dialog open so
        # the typed text is not lost while the banner says so, same rule
        # as the entry bars that only clear on success.
        if saved:
            self.close()
