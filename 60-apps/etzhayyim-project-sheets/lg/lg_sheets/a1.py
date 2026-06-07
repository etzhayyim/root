"""A1-notation parsing for spreadsheet ranges.

Supports the subset both Google Sheets and Microsoft Graph workbook clients use:
  - ``Sheet1!A1:C10``  → (sheet, r0, c0, r1, c1)  (0-based inclusive)
  - ``A1:C10``         → (None, …)                (default/first sheet)
  - ``Sheet1``         → (sheet, None…)           (whole sheet)
"""

from __future__ import annotations

import re
from typing import NamedTuple


class A1Range(NamedTuple):
    sheet: str | None
    r0: int | None  # top row, 0-based
    c0: int | None  # left col, 0-based
    r1: int | None  # bottom row, 0-based inclusive
    c1: int | None  # right col, 0-based inclusive


_CELL = re.compile(r"^([A-Za-z]+)([0-9]+)$")


def col_to_idx(col: str) -> int:
    n = 0
    for ch in col.upper():
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n - 1


def idx_to_col(idx: int) -> str:
    s = ""
    idx += 1
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        s = chr(ord("A") + rem) + s
    return s


def parse_range(range_str: str) -> A1Range:
    sheet: str | None = None
    rng = range_str.strip()
    if "!" in rng:
        sheet, rng = rng.split("!", 1)
        sheet = sheet.strip().strip("'")
    rng = rng.strip()
    if not rng:
        return A1Range(sheet, None, None, None, None)
    parts = rng.split(":")
    start = _CELL.match(parts[0])
    if not start:
        # bare sheet name with no cell range
        return A1Range(sheet or range_str.strip().strip("'"), None, None, None, None)
    c0, r0 = col_to_idx(start.group(1)), int(start.group(2)) - 1
    if len(parts) == 1:
        return A1Range(sheet, r0, c0, r0, c0)
    end = _CELL.match(parts[1])
    if not end:
        return A1Range(sheet, r0, c0, None, None)
    c1, r1 = col_to_idx(end.group(1)), int(end.group(2)) - 1
    return A1Range(sheet, r0, c0, r1, c1)


def format_range(sheet: str, r0: int, c0: int, r1: int, c1: int) -> str:
    return f"{sheet}!{idx_to_col(c0)}{r0 + 1}:{idx_to_col(c1)}{r1 + 1}"
