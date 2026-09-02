# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Where a drag-and-drop reorder lands. No gi import, so it is unit tested.

SPECIFICATION.md §3.2: a task row dropped on the top half of another row
moves in front of it; dropped on the bottom half, in front of the next
row, or to the end of the block when there is none.
"""

from __future__ import annotations


def drop_target_id(
    y: float, height: float, row_id: str, next_id: str | None
) -> str | None:
    """The id Session.move_before should place the dragged row before.

    ``y`` is the pointer offset inside the row the drop happened on,
    ``height`` that row's height, ``row_id`` its task id and ``next_id``
    the following row's task id, or None when it is the last of its block.
    The exact midpoint counts as the bottom half.
    """
    if y < height / 2:
        return row_id
    return next_id
