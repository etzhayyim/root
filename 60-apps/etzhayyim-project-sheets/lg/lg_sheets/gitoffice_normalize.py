"""GitOffice edge adapter — :sheet/gridJson blob <-> sparse :cell/* datoms.

doc e §13 option 1 (sheets side; mirror of the docs adapter).

The deployed sheets store one workbook as ``:sheet/gridJson`` = ``{title: [[cell]]}``.
Cell-level diff / merge / review need each non-empty cell as its own datom, keyed by
its absolute A1 ref (``"<sheet>!<A1>"``) — the save-stable id. This converts blob ->
``[:db/add e a v]`` ops and rows -> blob (trimmed to the non-empty bounding box,
the sparse round-trip fixed point). Byte-for-byte parity with gitoffice.cljc /
kotoba.gitoffice is asserted in tests/test_gitoffice_normalize.py.
"""

from __future__ import annotations

from typing import Any, Iterable

from .edn import tx_add


# --- A1 notation ------------------------------------------------------------

def col_to_a1(c: int) -> str:
    n, s = c + 1, ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def a1_to_col(letters: str) -> int:
    acc = 0
    for ch in letters:
        acc = acc * 26 + (ord(ch) - 64)
    return acc - 1


def cell_id(sheet: str, row: int, col: int) -> str:
    return f"{sheet}!{col_to_a1(col)}{row + 1}"


def _nonempty(v: Any) -> bool:
    return not (v is None or v == "")


def _bare(a: Any) -> str:
    s = str(a)
    return s[1:] if s.startswith(":") else s


# --- blob -> datom ops ------------------------------------------------------

def grid_to_cell_ops(book_id: str, grid_json: dict[str, list[list[Any]]]) -> list[list[Any]]:
    """``:sheet/gridJson`` -> ``[:db/add e a v]`` ops (sparse: only non-empty cells)."""
    ops: list[list[Any]] = []
    for sheet, grid in grid_json.items():
        for r, rowvals in enumerate(grid):
            for c, val in enumerate(rowvals):
                if not _nonempty(val):
                    continue
                cid = cell_id(sheet, r, c)
                ops.append(tx_add(cid, "cell/book", book_id))
                ops.append(tx_add(cid, "cell/sheet", sheet))
                ops.append(tx_add(cid, "cell/ref", f"{col_to_a1(c)}{r + 1}"))
                ops.append(tx_add(cid, "cell/row", r))
                ops.append(tx_add(cid, "cell/col", c))
                ops.append(tx_add(cid, "cell/value", val))
    return ops


# --- datom rows -> blob -----------------------------------------------------

def cells_to_grid(rows: Iterable[tuple[Any, Any, Any]],
                  book_id: str) -> dict[str, list[list[str]]]:
    """Decoded ``(e, a, v)`` rows -> ``:sheet/gridJson`` (each sheet trimmed to bbox)."""
    cells: dict[str, dict[str, Any]] = {}
    for e, a, v in rows:
        attr = _bare(a)
        if attr.startswith("cell/"):
            cells.setdefault(e, {})[attr] = v
    cells = {e: at for e, at in cells.items() if at.get("cell/book") == book_id}
    by_sheet: dict[str, list[tuple[int, int, Any]]] = {}
    for at in cells.values():
        by_sheet.setdefault(at["cell/sheet"], []).append(
            (at["cell/row"], at["cell/col"], at["cell/value"]))
    out: dict[str, list[list[str]]] = {}
    for sheet, items in by_sheet.items():
        rows_n = max(r for r, _, _ in items) + 1
        cols_n = max(c for _, c, _ in items) + 1
        grid = [["" for _ in range(cols_n)] for _ in range(rows_n)]
        for r, c, val in items:
            grid[r][c] = val
        out[sheet] = grid
    return out


def trim_grid(grid: list[list[Any]]) -> list[list[Any]]:
    """One grid -> non-empty bounding rectangle (the sparse round-trip fixed point)."""
    coords = [(r, c) for r in range(len(grid)) for c in range(len(grid[r]))
              if _nonempty(grid[r][c])]
    if not coords:
        return []
    rows_n = max(r for r, _ in coords) + 1
    cols_n = max(c for _, c in coords) + 1
    return [[(grid[r][c] if c < len(grid[r]) and grid[r][c] is not None else "")
             for c in range(cols_n)] for r in range(rows_n)]


def ops_to_rows(ops: list[list[Any]]) -> list[tuple[Any, Any, Any]]:
    return [(op[1], op[2], op[3]) for op in ops if len(op) == 4]
