# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Drop-box file listing, reading and filing, SPECIFICATION.md §2.8."""

from pathlib import Path

import pytest

from rature.core.inbox import (
    list_inbox_files,
    move_to_processed,
    processed_dir,
    read_inbox_lines,
)


def test_list_inbox_files_matches_the_exact_pattern(tmp_path: Path) -> None:
    (tmp_path / "inbox-phone-20260922-120000.txt").write_text("a", encoding="utf-8")
    assert list_inbox_files(tmp_path) == [tmp_path / "inbox-phone-20260922-120000.txt"]


def test_list_inbox_files_ignores_a_sync_client_temp_file(tmp_path: Path) -> None:
    (tmp_path / "inbox-phone-20260922-120000.txt.tmp").write_text("a", encoding="utf-8")
    (tmp_path / "inbox-phone-20260922-120000.txt.part").write_text(
        "a", encoding="utf-8"
    )
    assert list_inbox_files(tmp_path) == []


def test_list_inbox_files_ignores_an_unrelated_name(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("a", encoding="utf-8")
    (tmp_path / "inbox-.txt").write_text("a", encoding="utf-8")
    assert list_inbox_files(tmp_path) == []


def test_list_inbox_files_ignores_a_subdirectory(tmp_path: Path) -> None:
    (tmp_path / "inbox-phone-1.txt").mkdir()
    assert list_inbox_files(tmp_path) == []


def test_list_inbox_files_ignores_the_processed_directory_content(
    tmp_path: Path,
) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "inbox-phone-1.txt").write_text("a", encoding="utf-8")
    assert list_inbox_files(tmp_path) == []


def test_list_inbox_files_is_empty_without_the_folder(tmp_path: Path) -> None:
    assert list_inbox_files(tmp_path / "missing") == []


def test_list_inbox_files_is_sorted_by_name(tmp_path: Path) -> None:
    (tmp_path / "inbox-phone-2.txt").write_text("a", encoding="utf-8")
    (tmp_path / "inbox-laptop-1.txt").write_text("a", encoding="utf-8")
    assert list_inbox_files(tmp_path) == [
        tmp_path / "inbox-laptop-1.txt",
        tmp_path / "inbox-phone-2.txt",
    ]


def test_read_inbox_lines_strips_and_drops_empty_lines(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("  water the plants  \n\n\ncall the bank\n", encoding="utf-8")
    assert read_inbox_lines(path) == ["water the plants", "call the bank"]


def test_read_inbox_lines_on_an_empty_file_is_an_empty_list(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("", encoding="utf-8")
    assert read_inbox_lines(path) == []


def test_read_inbox_lines_on_blank_lines_only_is_an_empty_list(
    tmp_path: Path,
) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("   \n\t\n", encoding="utf-8")
    assert read_inbox_lines(path) == []


def test_read_inbox_lines_rejects_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_bytes(b"\xff\xfe not utf-8")
    with pytest.raises(UnicodeDecodeError):
        read_inbox_lines(path)


def test_read_inbox_lines_keeps_accented_text(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("café résumé", encoding="utf-8")
    assert read_inbox_lines(path) == ["café résumé"]


def test_processed_dir_is_a_subfolder_of_the_watched_folder(tmp_path: Path) -> None:
    assert processed_dir(tmp_path) == tmp_path / "processed"


def test_move_to_processed_creates_the_directory(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("a", encoding="utf-8")
    move_to_processed(path, tmp_path)
    assert (tmp_path / "processed").is_dir()


def test_move_to_processed_moves_the_file_there(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("a", encoding="utf-8")
    target = move_to_processed(path, tmp_path)
    assert target == tmp_path / "processed" / "inbox-phone-1.txt"
    assert target.read_text(encoding="utf-8") == "a"
    assert not path.exists()


def test_move_to_processed_keeps_the_content_byte_for_byte(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("café résumé", encoding="utf-8")
    target = move_to_processed(path, tmp_path)
    assert target.read_text(encoding="utf-8") == "café résumé"


def test_move_to_processed_reuses_an_existing_directory(tmp_path: Path) -> None:
    (tmp_path / "processed").mkdir()
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("a", encoding="utf-8")
    move_to_processed(path, tmp_path)
    assert (tmp_path / "processed" / "inbox-phone-1.txt").exists()
