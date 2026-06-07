"""Canonical sheets method handlers (ai.etzhayyim.apps.sheets.*).

Storage-agnostic (takes a :class:`lg_sheets.store.SheetStore`). The sheets-compat
worker reshapes results into Google Sheets v4 / Microsoft Graph workbook JSON.
Cell values are strings throughout (no-float rule); the edge casts per
valueRenderOption/valueInputOption.
"""

from __future__ import annotations

import time
from typing import Any

from . import a1, ids, mapping
from .store import SheetStore


def _now_ms() -> int:
    return int(time.time() * 1000)


async def _resolve(store: SheetStore, spreadsheet_id: str | None):
    slug = ids.resolve_slug(spreadsheet_id or "")
    if slug:
        attrs = await store.get_book_attrs(slug)
        if attrs:
            return slug, attrs
    for attr in ("sheet/googleSpreadsheetId", "sheet/msDriveItemId"):
        if not spreadsheet_id:
            break
        found = await store.lookup_slug(attr, spreadsheet_id)
        if found:
            attrs = await store.get_book_attrs(found)
            if attrs:
                return found, attrs
    return None, None


def _first_sheet_title(book: dict[str, Any]) -> str:
    sheets = book.get("sheets") or []
    return sheets[0]["title"] if sheets else "Sheet1"


# ── spreadsheetsCreate ────────────────────────────────────────────────────────


async def spreadsheets_create(store: SheetStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug = ids.new_slug()
    now = _now_ms()
    sheets = inp.get("sheets") or [{"sheetId": 0, "title": "Sheet1", "index": 0, "rowCount": 1000, "columnCount": 26}]
    grid = {s["title"]: [] for s in sheets}
    book: dict[str, Any] = {
        "title": inp["title"],
        "revision": 0,
        "createdAtMs": now,
        "updatedAtMs": now,
        "sheets": sheets,
        "grid": grid,
    }
    for opt in ("ownerDid", "googleSpreadsheetId", "msDriveItemId"):
        if inp.get(opt) is not None:
            book[opt] = inp[opt]
    await store.write_ops(mapping.create_ops(slug, book))
    attrs = await store.get_book_attrs(slug)
    return {"spreadsheetId": slug, "spreadsheet": mapping.attrs_to_book(attrs or {})}


# ── spreadsheetsGet ───────────────────────────────────────────────────────────


async def spreadsheets_get(store: SheetStore, params: dict[str, Any]) -> dict[str, Any]:
    _slug, attrs = await _resolve(store, params.get("spreadsheetId"))
    if not attrs:
        return {"found": False}
    return {"found": True, "spreadsheet": mapping.attrs_to_book(attrs)}


# ── grid helpers ──────────────────────────────────────────────────────────────


def _slice(grid: dict[str, list[list[str]]], rng: a1.A1Range, default_sheet: str) -> tuple[str, list[list[str]]]:
    sheet = rng.sheet or default_sheet
    data = grid.get(sheet, [])
    r0 = rng.r0 or 0
    r1 = rng.r1 if rng.r1 is not None else (len(data) - 1 if data else 0)
    out: list[list[str]] = []
    for r in range(r0, r1 + 1):
        row = data[r] if r < len(data) else []
        c0 = rng.c0 or 0
        c1 = rng.c1 if rng.c1 is not None else (len(row) - 1 if row else 0)
        out.append([str(row[c]) if c < len(row) and row[c] is not None else "" for c in range(c0, c1 + 1)])
    return sheet, out


def _write_block(grid: dict[str, list[list[str]]], sheet: str, r0: int, c0: int, rows: list[list[str]]) -> int:
    data = grid.setdefault(sheet, [])
    written = 0
    for i, row in enumerate(rows):
        rr = r0 + i
        while len(data) <= rr:
            data.append([])
        target = data[rr]
        for j, cell in enumerate(row):
            cc = c0 + j
            while len(target) <= cc:
                target.append("")
            target[cc] = "" if cell is None else str(cell)
            written += 1
    return written


def _rows_from_input(value_range: dict[str, Any]) -> list[list[str]]:
    rows = value_range.get("rows") or []
    out: list[list[str]] = []
    for r in rows:
        cells = r.get("cells") if isinstance(r, dict) else r
        out.append(["" if c is None else str(c) for c in (cells or [])])
    return out


# ── valuesGet ─────────────────────────────────────────────────────────────────


async def values_get(store: SheetStore, params: dict[str, Any]) -> dict[str, Any]:
    _slug, attrs = await _resolve(store, params.get("spreadsheetId"))
    if not attrs:
        return {"found": False}
    book = mapping.attrs_to_book(attrs)
    grid = mapping.attrs_to_grid(attrs)
    rng = a1.parse_range(params.get("range", ""))
    sheet, block = _slice(grid, rng, _first_sheet_title(book))
    major = params.get("majorDimension", "ROWS")
    if major == "COLUMNS":
        block = [list(col) for col in zip(*block)] if block else []
    rows = [{"cells": row} for row in block]
    in_range = params.get("range", "")
    if "!" in in_range:
        out_range = in_range
    elif in_range:
        out_range = f"{sheet}!{in_range}"
    else:
        out_range = sheet
    return {"found": True, "valueRange": {"range": out_range, "majorDimension": major, "rows": rows}}


# ── valuesUpdate ──────────────────────────────────────────────────────────────


async def values_update(store: SheetStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug, attrs = await _resolve(store, inp.get("spreadsheetId"))
    if not attrs:
        return {"ok": False, "notFound": True}
    if inp.get("ifRevision") is not None and attrs.get("sheet/revision") != inp["ifRevision"]:
        return {"ok": False, "conflict": True}
    book = mapping.attrs_to_book(attrs)
    grid = mapping.attrs_to_grid(attrs)
    vr = inp["valueRange"]
    rng = a1.parse_range(vr.get("range", ""))
    sheet = rng.sheet or _first_sheet_title(book)
    written = _write_block(grid, sheet, rng.r0 or 0, rng.c0 or 0, _rows_from_input(vr))
    new_rev = int(attrs.get("sheet/revision", 0)) + 1
    await store.write_ops(mapping.update_ops(slug, attrs, {"grid": grid, "revision": new_rev, "updatedAtMs": _now_ms()}))
    return {"ok": True, "updatedCells": written, "updatedRange": vr.get("range"), "revision": new_rev}


# ── valuesBatchUpdate ─────────────────────────────────────────────────────────


async def values_batch_update(store: SheetStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug, attrs = await _resolve(store, inp.get("spreadsheetId"))
    if not attrs:
        return {"ok": False, "notFound": True}
    if inp.get("ifRevision") is not None and attrs.get("sheet/revision") != inp["ifRevision"]:
        return {"ok": False, "conflict": True}
    book = mapping.attrs_to_book(attrs)
    grid = mapping.attrs_to_grid(attrs)
    total = 0
    for vr in inp.get("data", []):
        rng = a1.parse_range(vr.get("range", ""))
        sheet = rng.sheet or _first_sheet_title(book)
        total += _write_block(grid, sheet, rng.r0 or 0, rng.c0 or 0, _rows_from_input(vr))
    new_rev = int(attrs.get("sheet/revision", 0)) + 1
    await store.write_ops(mapping.update_ops(slug, attrs, {"grid": grid, "revision": new_rev, "updatedAtMs": _now_ms()}))
    return {"ok": True, "totalUpdatedCells": total, "revision": new_rev}
