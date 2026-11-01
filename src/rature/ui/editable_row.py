# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""What the Day, Reserve and Tomorrow rows have in common."""

from __future__ import annotations

from gettext import gettext as _
from typing import TYPE_CHECKING, ClassVar, Protocol

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, GObject, Gtk  # noqa: E402

from rature.ui import reorder  # noqa: E402
from rature.ui.inline_rename import InlineRename  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from rature.core.app import App


class _Model(Protocol):
    """A Task, a ReserveItem or a PreparedTask, as far as a row cares."""

    id: str
    text: str
    priority: bool


class EditableRow(Gtk.ListBoxRow):
    """Inline rename, priority, delete and drag-and-drop reordering.

    TaskRow, ReserveRow and PreparedRow subclass it with their own template;
    each template provides the children named below. A subclass exposes
    its model under its own name (`task` or `item`), says which App call
    does each change, and keeps the rest: the strike and send buttons.

    Not a template itself, and never instantiated directly. The three
    templates name it as their parent, hence the fixed GType name.
    """

    __gtype_name__ = "RatureEditableRow"

    # The template children every subclass provides.
    text_label: Gtk.Label
    rename_entry: Gtk.Entry
    row_popover: Gtk.Popover
    rename_button: Gtk.Button
    priority_button: Gtk.Button
    delete_button: Gtk.Button
    priority_icon: Gtk.Image

    # The row being dragged, per subclass: a drop target identifies its
    # source without asynchronous content negotiation. One drag at a time
    # in one process, so a class attribute is enough. Each subclass
    # declares its own, so the three views never see each other's drags.
    _dragged: ClassVar[EditableRow | None] = None
    # MOVE for the Day and Tomorrow rows. The reserve overrides it with
    # COPY: see reserve_row.py.
    drag_action: ClassVar[Gdk.DragAction] = Gdk.DragAction.MOVE

    def __init__(
        self,
        model: _Model,
        *,
        app: App,
        run_action: Callable[[Callable[[], None]], bool],
        perform: Callable[[Callable[[], None]], bool],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._model = model
        self.app = app
        self.run_action = run_action
        self.perform = perform

        self.text_label.set_label(model.text)
        # SPECIFICATION.md §3.2: the priority column keeps its width when
        # empty (set_child_visible, not set_visible), so the text columns
        # line up across marked and unmarked rows.
        self.priority_icon.set_child_visible(model.priority)
        self.priority_button.set_label(
            _("Remove priority") if model.priority else _("Mark as priority")
        )

        self.rename_button.connect("clicked", self._on_rename_clicked)
        self.priority_button.connect("clicked", self._on_priority_clicked)
        self.delete_button.connect("clicked", self._on_delete_clicked)

        self._rename = InlineRename(
            entry=self.rename_entry,
            label=self.text_label,
            current_text=lambda: self._model.text,
            commit=lambda text: self.perform(lambda: self._rename_in_core(text)),
            finished=self._on_editor_closed,
        )
        self.row_popover.connect("closed", lambda _popover: self._on_editor_closed())
        self._wire_drag_and_drop()

    # What a subclass must say: which App call does each change.

    def _rename_in_core(self, text: str) -> None:
        raise NotImplementedError

    def _set_priority_in_core(self, *, priority: bool) -> None:
        raise NotImplementedError

    def _delete_in_core(self) -> None:
        raise NotImplementedError

    def _move_before_in_core(self, entry_id: str, target_id: str | None) -> None:
        raise NotImplementedError

    # What a subclass may change.

    def _drag_value(self) -> object:
        """What a drag carries; the drop target accepts its type only."""
        return self

    def _drag_gtype(self) -> GObject.GType:
        return type(self).__gtype__

    def _accepts_drop_of(self, _source: EditableRow) -> bool:
        """Whether ``source``, a peer row and not this one, may land here."""
        return True

    # Shared behaviour.

    def _wire_drag_and_drop(self) -> None:
        source = Gtk.DragSource(actions=self.drag_action)
        source.connect("prepare", self._on_drag_prepare)
        source.connect("drag-begin", self._on_drag_begin)
        source.connect("drag-end", self._on_drag_end)
        self.add_controller(source)

        target = Gtk.DropTarget(actions=self.drag_action)
        target.set_gtypes([self._drag_gtype()])
        target.connect("motion", self._on_drop_motion)
        target.connect("drop", self._on_drop)
        self.add_controller(target)

    def _on_drag_prepare(
        self, _source: Gtk.DragSource, _x: float, _y: float
    ) -> Gdk.ContentProvider:
        return Gdk.ContentProvider.new_for_value(self._drag_value())

    def _on_drag_begin(self, source: Gtk.DragSource, _drag: Gdk.Drag) -> None:
        type(self)._dragged = self
        self.add_css_class("rature-drag-source")
        source.set_icon(Gtk.WidgetPaintable.new(self), 0, 0)

    # GTK's drag-end signal passes delete_data positionally.
    def _on_drag_end(
        self,
        _source: Gtk.DragSource,
        _drag: Gdk.Drag,
        _delete: bool,  # noqa: FBT001
    ) -> None:
        type(self)._dragged = None
        self.remove_css_class("rature-drag-source")

    @classmethod
    def dragged(cls) -> EditableRow | None:
        """The row of this class being dragged right now, or None."""
        return cls._dragged

    def _dragged_peer(self) -> EditableRow | None:
        """The row being dragged, or None if it may not drop on this one.

        Refuses a row dropped on itself, anything dragged in from outside
        this class's rows, and whatever the subclass refuses.
        """
        source = type(self)._dragged
        if source is None or source is self or not self._accepts_drop_of(source):
            return None
        return source

    def _on_drop_motion(
        self, _target: Gtk.DropTarget, _x: float, _y: float
    ) -> Gdk.DragAction:
        return self.drag_action if self._dragged_peer() else Gdk.DragAction(0)

    def _on_drop(
        self, _target: Gtk.DropTarget, _value: object, _x: float, y: float
    ) -> bool:
        source = self._dragged_peer()
        if source is None:
            return False
        sibling = self.get_next_sibling()
        next_id = sibling._model.id if isinstance(sibling, type(self)) else None
        target_id = reorder.drop_target_id(
            y, self.get_height(), self._model.id, next_id
        )
        self.run_action(lambda: self._move_before_in_core(source._model.id, target_id))
        return True

    def _on_rename_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self._rename.begin()

    def _on_priority_clicked(self, _button: Gtk.Button) -> None:
        # Allowed on a frozen list and a struck task, like a rename
        # (SPECIFICATION.md §3.2).
        self.row_popover.popdown()
        self.run_action(
            lambda: self._set_priority_in_core(priority=not self._model.priority)
        )

    def _on_delete_clicked(self, _button: Gtk.Button) -> None:
        self.row_popover.popdown()
        self.run_action(self._delete_in_core)

    @property
    def editor_open(self) -> bool:
        """Whether a rebuild would destroy this row under the user's hands."""
        return self.row_popover.get_visible() or self._rename.editing

    def _on_editor_closed(self) -> None:
        self.activate_action("win.row-editor-closed", None)

    def commit_pending_rename(self) -> None:
        """Flush a pending edit, e.g. before the view rebuilds its rows."""
        self._rename.commit()
