"""Tests for the sheets GitOffice edge adapter (gridJson <-> sparse :cell/* datoms).

Parity fixtures identical to gitoffice.cljc / kotoba.gitoffice (drift guard).
"""

from lg_sheets import gitoffice_normalize as gn


SAMPLE_GRID = {
    "Sheet1": [
        ["売上", "Q1", "Q2"],
        ["製品A", "100", "120"],
        ["製品B", "", "80"],
    ]
}


def test_a1_roundtrip():
    assert gn.col_to_a1(0) == "A"
    assert gn.col_to_a1(1) == "B"
    assert gn.col_to_a1(25) == "Z"
    assert gn.col_to_a1(26) == "AA"
    assert gn.col_to_a1(27) == "AB"
    for c in [0, 1, 25, 26, 27, 51, 52, 700]:
        assert gn.a1_to_col(gn.col_to_a1(c)) == c
    assert gn.cell_id("Sheet1", 1, 1) == "Sheet1!B2"


def test_grid_roundtrip_trimmed():
    ops = gn.grid_to_cell_ops("book1", SAMPLE_GRID)
    rows = gn.ops_to_rows(ops)
    out = gn.cells_to_grid(rows, "book1")
    expected = {"Sheet1": gn.trim_grid(SAMPLE_GRID["Sheet1"])}
    assert out == expected


def test_cells_are_sparse():
    ops = gn.grid_to_cell_ops("book1", SAMPLE_GRID)
    ids = {op[1] for op in ops}
    assert "Sheet1!B3" not in ids  # the empty cell is not stored
    assert "Sheet1!C2" in ids


def test_trailing_empties_dropped():
    grid = {"S": [["x", "", ""], ["", "", ""]]}
    rows = gn.ops_to_rows(gn.grid_to_cell_ops("bk", grid))
    assert gn.cells_to_grid(rows, "bk") == {"S": [["x"]]}


def test_value_preserved():
    ops = gn.grid_to_cell_ops("book1", SAMPLE_GRID)
    rows = gn.ops_to_rows(ops)
    vals = {e: v for (e, a, v) in rows if gn._bare(a) == "cell/value"}
    assert vals["Sheet1!C2"] == "120"
    assert vals["Sheet1!A1"] == "売上"
