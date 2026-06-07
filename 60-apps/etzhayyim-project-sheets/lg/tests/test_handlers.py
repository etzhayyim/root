"""Deterministic sheets-handler + A1 tests using FakeSheetStore.

Verifies create/get, A1 range read/write into the cell grid, range slicing,
COLUMNS major dimension, batch update, revision-based optimistic concurrency,
and not-found — without a live kotoba pod.
"""

from __future__ import annotations

import pytest

from lg_sheets import a1, handlers
from lg_sheets.store import FakeSheetStore


@pytest.fixture()
def store() -> FakeSheetStore:
    return FakeSheetStore()


def test_a1_parse() -> None:
    assert a1.parse_range("Sheet1!A1:C10") == a1.A1Range("Sheet1", 0, 0, 9, 2)
    assert a1.parse_range("B2") == a1.A1Range(None, 1, 1, 1, 1)
    assert a1.col_to_idx("A") == 0 and a1.col_to_idx("Z") == 25 and a1.col_to_idx("AA") == 26
    assert a1.idx_to_col(0) == "A" and a1.idx_to_col(26) == "AA"


async def test_create_get(store: FakeSheetStore) -> None:
    res = await handlers.spreadsheets_create(store, {"title": "Budget"})
    assert res["spreadsheet"]["title"] == "Budget"
    assert res["spreadsheet"]["revision"] == 0
    assert res["spreadsheet"]["sheets"][0]["title"] == "Sheet1"
    got = await handlers.spreadsheets_get(store, {"spreadsheetId": res["spreadsheetId"]})
    assert got["found"] is True and got["spreadsheet"]["title"] == "Budget"


async def test_get_missing(store: FakeSheetStore) -> None:
    assert await handlers.spreadsheets_get(store, {"spreadsheetId": "missing001"}) == {"found": False}


async def test_values_update_then_get_roundtrip(store: FakeSheetStore) -> None:
    sid = (await handlers.spreadsheets_create(store, {"title": "T"}))["spreadsheetId"]
    upd = await handlers.values_update(store, {
        "spreadsheetId": sid,
        "valueRange": {"range": "Sheet1!A1:B2", "rows": [{"cells": ["a", "b"]}, {"cells": ["c", "d"]}]},
    })
    assert upd["ok"] is True
    assert upd["updatedCells"] == 4
    assert upd["revision"] == 1

    got = await handlers.values_get(store, {"spreadsheetId": sid, "range": "Sheet1!A1:B2"})
    assert got["found"] is True
    assert [r["cells"] for r in got["valueRange"]["rows"]] == [["a", "b"], ["c", "d"]]

    # partial range read
    sub = await handlers.values_get(store, {"spreadsheetId": sid, "range": "Sheet1!B1:B2"})
    assert [r["cells"] for r in sub["valueRange"]["rows"]] == [["b"], ["d"]]


async def test_values_get_columns_major(store: FakeSheetStore) -> None:
    sid = (await handlers.spreadsheets_create(store, {"title": "T"}))["spreadsheetId"]
    await handlers.values_update(store, {"spreadsheetId": sid, "valueRange": {"range": "Sheet1!A1:B2", "rows": [{"cells": ["a", "b"]}, {"cells": ["c", "d"]}]}})
    got = await handlers.values_get(store, {"spreadsheetId": sid, "range": "Sheet1!A1:B2", "majorDimension": "COLUMNS"})
    assert [r["cells"] for r in got["valueRange"]["rows"]] == [["a", "c"], ["b", "d"]]


async def test_batch_update(store: FakeSheetStore) -> None:
    sid = (await handlers.spreadsheets_create(store, {"title": "T"}))["spreadsheetId"]
    res = await handlers.values_batch_update(store, {
        "spreadsheetId": sid,
        "data": [
            {"range": "Sheet1!A1", "rows": [{"cells": ["x"]}]},
            {"range": "Sheet1!C3:C4", "rows": [{"cells": ["y"]}, {"cells": ["z"]}]},
        ],
    })
    assert res["ok"] is True and res["totalUpdatedCells"] == 3
    c3 = await handlers.values_get(store, {"spreadsheetId": sid, "range": "Sheet1!C3:C4"})
    assert [r["cells"] for r in c3["valueRange"]["rows"]] == [["y"], ["z"]]


async def test_revision_concurrency(store: FakeSheetStore) -> None:
    sid = (await handlers.spreadsheets_create(store, {"title": "T"}))["spreadsheetId"]
    ok = await handlers.values_update(store, {"spreadsheetId": sid, "ifRevision": 0, "valueRange": {"range": "Sheet1!A1", "rows": [{"cells": ["1"]}]}})
    assert ok["ok"] is True and ok["revision"] == 1
    stale = await handlers.values_update(store, {"spreadsheetId": sid, "ifRevision": 0, "valueRange": {"range": "Sheet1!A1", "rows": [{"cells": ["2"]}]}})
    assert stale == {"ok": False, "conflict": True}
    missing = await handlers.values_update(store, {"spreadsheetId": "nope01", "valueRange": {"range": "A1", "rows": []}})
    assert missing == {"ok": False, "notFound": True}


async def test_lookup_by_provider_id(store: FakeSheetStore) -> None:
    await handlers.spreadsheets_create(store, {"title": "Imported", "googleSpreadsheetId": "gsheet_1"})
    got = await handlers.spreadsheets_get(store, {"spreadsheetId": "gsheet_1"})
    assert got["found"] is True and got["spreadsheet"]["title"] == "Imported"
