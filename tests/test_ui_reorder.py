# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Where a drag-and-drop reorder lands, extracted from TaskRow so it runs
without a display."""

from rature.ui.reorder import drop_target_id


def test_top_half_drops_before_the_row() -> None:
    assert drop_target_id(y=5, height=40, row_id="a", next_id="b") == "a"


def test_bottom_half_drops_before_the_next_row() -> None:
    assert drop_target_id(y=30, height=40, row_id="a", next_id="b") == "b"


def test_bottom_half_of_the_last_row_drops_at_the_end() -> None:
    assert drop_target_id(y=30, height=40, row_id="a", next_id=None) is None


def test_exact_midpoint_counts_as_the_bottom_half() -> None:
    assert drop_target_id(y=20, height=40, row_id="a", next_id="b") == "b"


def test_top_edge_drops_before_the_row() -> None:
    assert drop_target_id(y=0, height=40, row_id="a", next_id="b") == "a"
