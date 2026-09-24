# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Drop-box file listing, reading and filing, SPECIFICATION.md §2.8."""

from pathlib import Path

import pytest

from rature.core.inbox import (
    MAX_INBOX_FILE_SIZE,
    InboxFileTooLargeError,
    check_inbox_file,
    claim,
    finalize,
    list_inbox_files,
    list_pending_files,
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


def test_list_inbox_files_ignores_a_symlink(tmp_path: Path) -> None:
    # ADR 0007 addendum: a symlink can point outside what the portal
    # granted access to, so it is skipped even when its name matches and
    # its target is a plain file.
    real = tmp_path / "elsewhere.txt"
    real.write_text("outside the granted folder", encoding="utf-8")
    link = tmp_path / "inbox-phone-1.txt"
    link.symlink_to(real)
    assert list_inbox_files(tmp_path) == []


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


def test_read_inbox_lines_strips_a_leading_bom(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_bytes(b"\xef\xbb\xbfwater the plants\n")
    assert read_inbox_lines(path) == ["water the plants"]


def test_check_inbox_file_accepts_a_small_valid_file(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("a", encoding="utf-8")
    check_inbox_file(path)  # does not raise


def test_check_inbox_file_rejects_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_bytes(b"\xff\xfe not utf-8")
    with pytest.raises(UnicodeDecodeError):
        check_inbox_file(path)


def test_check_inbox_file_rejects_a_file_over_the_size_limit(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_bytes(b"a" * (MAX_INBOX_FILE_SIZE + 1))
    with pytest.raises(InboxFileTooLargeError):
        check_inbox_file(path)


def test_check_inbox_file_accepts_a_file_at_exactly_the_size_limit(
    tmp_path: Path,
) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_bytes(b"a" * MAX_INBOX_FILE_SIZE)
    check_inbox_file(path)  # does not raise


def test_processed_dir_is_a_subfolder_of_the_watched_folder(tmp_path: Path) -> None:
    assert processed_dir(tmp_path) == tmp_path / "processed"


def test_claim_creates_the_processed_directory(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("a", encoding="utf-8")
    claim(path, tmp_path)
    assert (tmp_path / "processed").is_dir()


def test_claim_moves_the_file_there_as_pending(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("a", encoding="utf-8")
    target = claim(path, tmp_path)
    assert target == tmp_path / "processed" / "inbox-phone-1.txt.pending"
    assert target.read_text(encoding="utf-8") == "a"
    assert not path.exists()


def test_claim_keeps_the_content_byte_for_byte(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("café résumé", encoding="utf-8")
    target = claim(path, tmp_path)
    assert target.read_text(encoding="utf-8") == "café résumé"


def test_claim_reuses_an_existing_directory(tmp_path: Path) -> None:
    (tmp_path / "processed").mkdir()
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("a", encoding="utf-8")
    claim(path, tmp_path)
    assert (tmp_path / "processed" / "inbox-phone-1.txt.pending").exists()


def test_claim_never_overwrites_an_existing_pending_of_the_same_name(
    tmp_path: Path,
) -> None:
    # Point 2 of the review: an earlier, still-unfinalized claim of the
    # same name must not be clobbered by a newly dropped file that
    # happens to share it.
    processed = tmp_path / "processed"
    processed.mkdir()
    stale = processed / "inbox-phone-1.txt.pending"
    stale.write_text("earlier, not yet finalized", encoding="utf-8")
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("newly dropped", encoding="utf-8")

    target = claim(path, tmp_path)

    assert target != stale
    assert stale.read_text(encoding="utf-8") == "earlier, not yet finalized"
    assert target.read_text(encoding="utf-8") == "newly dropped"


def test_claim_tries_a_second_suffix_when_the_first_is_also_taken(
    tmp_path: Path,
) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "inbox-phone-1.txt.pending").write_text("first", encoding="utf-8")
    (processed / "inbox-phone-1.txt-2.pending").write_text("second", encoding="utf-8")
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("third", encoding="utf-8")

    target = claim(path, tmp_path)

    assert target == processed / "inbox-phone-1.txt-3.pending"


def test_finalize_renames_pending_to_the_plain_name(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("a", encoding="utf-8")
    pending = claim(path, tmp_path)
    target = finalize(pending)
    assert target == tmp_path / "processed" / "inbox-phone-1.txt"
    assert target.read_text(encoding="utf-8") == "a"
    assert not pending.exists()


def test_finalize_never_overwrites_an_existing_file_of_the_same_name(
    tmp_path: Path,
) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    already_processed = processed / "inbox-phone-1.txt"
    already_processed.write_text("already there", encoding="utf-8")
    pending = processed / "inbox-phone-1.txt.pending"
    pending.write_text("about to finalize", encoding="utf-8")

    target = finalize(pending)

    assert target != already_processed
    assert already_processed.read_text(encoding="utf-8") == "already there"
    assert target.read_text(encoding="utf-8") == "about to finalize"
    assert target.name.endswith(".txt")


def test_list_pending_files_is_empty_without_processed_directory(
    tmp_path: Path,
) -> None:
    assert list_pending_files(tmp_path) == []


def test_list_pending_files_finds_a_leftover_claim(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("a", encoding="utf-8")
    pending = claim(path, tmp_path)
    assert list_pending_files(tmp_path) == [pending]


def test_list_pending_files_ignores_an_already_finalized_file(tmp_path: Path) -> None:
    path = tmp_path / "inbox-phone-1.txt"
    path.write_text("a", encoding="utf-8")
    finalize(claim(path, tmp_path))
    assert list_pending_files(tmp_path) == []


def test_list_pending_files_is_sorted_by_name(tmp_path: Path) -> None:
    (tmp_path / "inbox-b-1.txt").write_text("a", encoding="utf-8")
    (tmp_path / "inbox-a-1.txt").write_text("a", encoding="utf-8")
    claim(tmp_path / "inbox-b-1.txt", tmp_path)
    claim(tmp_path / "inbox-a-1.txt", tmp_path)
    assert list_pending_files(tmp_path) == [
        tmp_path / "processed" / "inbox-a-1.txt.pending",
        tmp_path / "processed" / "inbox-b-1.txt.pending",
    ]
