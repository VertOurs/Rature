# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Strict reading of the data files: every field, every list, every key."""

import copy
import json
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from rature.core import storage, validation
from rature.core.app import App, DataFileUnreadableError, StartupOutcome
from rature.core.models import (
    Deletion,
    Origin,
    PreparedTask,
    RecurringItem,
    ReserveItem,
    ReserveSource,
    Task,
)
from rature.core.session import Day

FORMATS = Path(__file__).parent / "data" / "formats"
TAGS = sorted(path.name for path in FORMATS.iterdir() if path.is_dir())
PARIS = timezone(timedelta(hours=2))


# Files written by released versions (tests/data/formats/generate.py),
# loaded with the current code, migration included. A failure here means
# a migration leaves a file the strict reading refuses: fix the
# migration, not the validation.


def test_every_file_format_is_represented() -> None:
    versions = {
        json.loads((FORMATS / tag / "data.json").read_text(encoding="utf-8"))["version"]
        for tag in TAGS
    }
    assert versions == {1, 2, 3, 4}


@pytest.mark.parametrize("tag", TAGS)
def test_a_released_main_file_loads(tmp_path: Path, tag: str) -> None:
    shutil.copy(FORMATS / tag / "data.json", tmp_path / "data.json")
    store = storage.load(data_dir=tmp_path)
    assert store.day.tasks
    assert store.day.deletions
    assert store.reserve


@pytest.mark.parametrize("tag", TAGS)
def test_released_archives_load(tmp_path: Path, tag: str) -> None:
    shutil.copytree(FORMATS / tag / "archive", tmp_path / "archive")
    days = storage.list_archives(data_dir=tmp_path)
    assert len(days) == 3
    for day_date in days:
        assert storage.load_archive(day_date, data_dir=tmp_path).date == day_date


@pytest.mark.parametrize("tag", TAGS)
def test_a_released_data_directory_opens_as_loaded(tmp_path: Path, tag: str) -> None:
    shutil.copytree(FORMATS / tag, tmp_path / "data")
    moment = datetime(2026, 8, 27, 9, 0, tzinfo=PARIS)
    app = App.open(tmp_path / "data", clock=lambda: moment)
    assert app.startup is StartupOutcome.LOADED
    assert len(app.statistics()) == 3


# The key sets from_dict accepts are exactly what to_dict writes.

SOURCE = ReserveSource(id="r1", created=date(2026, 8, 20))
MOMENT = datetime(2026, 8, 24, 9, 0, tzinfo=PARIS)

SAMPLES = [
    Task(num=1, text="x", origin=Origin.RESERVE, source=SOURCE),
    PreparedTask(text="x", origin=Origin.DAY),
    ReserveItem(text="x", created=date(2026, 8, 20)),
    RecurringItem(text="x", weekdays=[0]),
    Deletion(id="d", num=1, text="x", origin=Origin.DAY, deleted_at=MOMENT, index=0),
    Day(date=date(2026, 8, 24)),
]


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: type(s).__name__)
def test_from_dict_accepts_what_to_dict_writes(sample: Any) -> None:
    assert type(sample).from_dict(sample.to_dict()) == sample


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: type(s).__name__)
def test_from_dict_refuses_an_unknown_key(sample: Any) -> None:
    with pytest.raises(ValueError, match="unexpected keys: note"):
        type(sample).from_dict({**sample.to_dict(), "note": "x"})


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: type(s).__name__)
def test_from_dict_refuses_a_missing_key(sample: Any) -> None:
    data = sample.to_dict()
    del data["text" if "text" in data else "date"]
    with pytest.raises(KeyError, match="missing keys"):
        type(sample).from_dict(data)


# A valid current main file, then one wrong value at a time.


def _main_file() -> dict[str, Any]:
    path = FORMATS / "v2.1.1" / "data.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _load(tmp_path: Path, data: dict[str, Any]) -> storage.Store:
    (tmp_path / "data.json").write_text(json.dumps(data), encoding="utf-8")
    return storage.load(data_dir=tmp_path)


# (path to the value, wrong value): a key of the top level, or a key of
# the first entry of a list.
WRONG_TYPES = [
    (("date",), 20260827),
    (("counter",), "3"),
    (("counter",), True),
    (("counter",), 2.5),
    (("locked",), 0),
    (("tasks",), {}),
    (("tasks",), ["a task"]),
    (("deletions",), None),
    (("reserve",), {}),
    (("tomorrow",), "none"),
    (("recurring",), [[1]]),
    (("tasks", "id"), 7),
    (("tasks", "num"), "1"),
    (("tasks", "num"), True),
    (("tasks", "text"), 42),
    (("tasks", "done"), "yes"),
    (("tasks", "done"), 1),
    (("tasks", "done_at"), 0),
    (("tasks", "origin"), 1),
    (("tasks", "source_id"), 5),
    (("tasks", "source_created"), ["2026-08-20"]),
    (("tasks", "template_id"), False),
    (("tasks", "priority"), None),
    (("deletions", "index"), "0"),
    (("deletions", "deleted_at"), None),
    (("deletions", "done"), "no"),
    (("reserve", "text"), None),
    (("reserve", "created"), 20260820),
    (("reserve", "priority"), "true"),
    (("tomorrow", "text"), []),
    (("tomorrow", "priority"), 0),
    (("recurring", "weekdays"), "12"),
    (("recurring", "weekdays"), [True]),
    (("recurring", "weekdays"), [1.0]),
    (("recurring", "every_other_week_from"), 0),
]


def _set(data: dict[str, Any], path: tuple[str, ...], value: object) -> None:
    if len(path) == 1:
        data[path[0]] = value
    else:
        data[path[0]][0][path[1]] = value


@pytest.mark.parametrize(
    ("path", "value"),
    WRONG_TYPES,
    ids=[f"{'.'.join(p)}={v!r}" for p, v in WRONG_TYPES],
)
def test_a_wrong_type_is_refused(
    tmp_path: Path, path: tuple[str, ...], value: object
) -> None:
    data = _main_file()
    _set(data, path, value)
    with pytest.raises(TypeError):
        _load(tmp_path, data)


def test_an_empty_done_at_is_refused_not_read_as_null(tmp_path: Path) -> None:
    data = _main_file()
    struck = next(task for task in data["tasks"] if task["done"])
    struck["done_at"] = ""
    with pytest.raises(ValueError):
        _load(tmp_path, data)


def test_an_empty_every_other_week_from_is_refused(tmp_path: Path) -> None:
    data = _main_file()
    data["recurring"][0]["every_other_week_from"] = ""
    with pytest.raises(ValueError):
        _load(tmp_path, data)


@pytest.mark.parametrize("key", ["reserve", "tomorrow", "recurring"])
def test_a_main_file_list_is_required(tmp_path: Path, key: str) -> None:
    data = _main_file()
    del data[key]
    with pytest.raises(KeyError, match=key):
        _load(tmp_path, data)


def test_an_unknown_top_level_key_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unexpected keys: note"):
        _load(tmp_path, {**_main_file(), "note": "x"})


def test_an_unknown_key_in_a_list_entry_is_refused(tmp_path: Path) -> None:
    data = _main_file()
    data["reserve"][0]["note"] = "x"
    with pytest.raises(ValueError, match="unexpected keys: note"):
        _load(tmp_path, data)


def test_an_archive_with_main_file_keys_is_refused(tmp_path: Path) -> None:
    data = _main_file()
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive" / "2026-08-27.json").write_text(
        json.dumps(data), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="unexpected keys"):
        storage.load_archive(date(2026, 8, 27), data_dir=tmp_path)


def test_an_invalid_main_file_is_refused_and_left_alone(tmp_path: Path) -> None:
    data = _main_file()
    data["tasks"][0]["done"] = "yes"
    (tmp_path / "data.json").write_text(json.dumps(data), encoding="utf-8")
    moment = datetime(2026, 8, 27, 9, 0, tzinfo=PARIS)
    before = (tmp_path / "data.json").read_bytes()
    with pytest.raises(DataFileUnreadableError):
        App.open(tmp_path, clock=lambda: moment)
    assert (tmp_path / "data.json").read_bytes() == before


# Messages name the key and the types, never the value: it can be the
# text of a task.


def test_a_message_never_carries_the_value() -> None:
    data = {"text": ["my secret task"], "done": "my secret task"}
    for read, key in [
        (validation.text, "text"),
        (validation.flag, "done"),
        (validation.integer, "done"),
        (validation.objects, "done"),
        (validation.integers, "text"),
        (validation.optional_text, "text"),
    ]:
        with pytest.raises(TypeError) as caught:
            read(data, key)
        assert "secret" not in str(caught.value)
        assert key in str(caught.value)


def test_the_generated_files_are_not_edited_by_hand() -> None:
    # A guard against "fixing" a fixture instead of a migration: every
    # file still carries the version its tag wrote.
    expected = {
        "v1.0.0": 1,
        "v1.5.0": 1,
        "v1.6.0": 2,
        "v1.7.1": 3,
        "v1.8.0": 4,
        "v2.1.1": 4,
    }
    for tag, version in expected.items():
        for path in (FORMATS / tag).rglob("*.json"):
            raw = json.loads(path.read_text(encoding="utf-8"))
            assert raw["version"] == version, path


def test_load_leaves_the_input_untouched() -> None:
    data = _main_file()
    original = copy.deepcopy(data)
    storage.Store.from_dict(data)
    assert data == original
