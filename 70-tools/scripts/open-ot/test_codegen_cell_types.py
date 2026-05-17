"""Tests for `codegen-cell-types.py` — layout calculation correctness.

Run from this directory:
    python3 -m pytest test_codegen_cell_types.py
"""

from __future__ import annotations

import importlib.util
import struct
import sys
from pathlib import Path

import pytest

THIS_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = THIS_DIR / "codegen-cell-types.py"

spec = importlib.util.spec_from_file_location("codegen_cell_types", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
codegen = importlib.util.module_from_spec(spec)
# `@dataclass` looks the class's module up via sys.modules during decoration —
# register before exec so the lookup succeeds for hyphenated-filename modules
# loaded outside the normal import path.
sys.modules["codegen_cell_types"] = codegen
spec.loader.exec_module(codegen)


# ---------------------------------------------------------------------------
# Layout primitives
# ---------------------------------------------------------------------------


def _layout(fields: list[tuple[str, str]]) -> codegen.Layout:
    return codegen.compute_layout(
        [{"name": n, "rust_type": t} for n, t in fields]
    )


def test_single_i32_no_padding():
    L = _layout([("x", "i32")])
    assert L.fmt == "<i"
    assert L.size == 4


def test_two_i32_packed():
    L = _layout([("a", "i32"), ("b", "i32")])
    assert L.fmt == "<ii"
    assert L.size == 8


def test_pid_limited_data_in_layout():
    """`pid-limited` DataIn = i32, i32, u8, bool → expect <iiBB2x size 12."""
    L = _layout([("pv", "i32"), ("sp", "i32"), ("pv_quality", "u8"), ("enable", "bool")])
    assert L.fmt == "<iiBB2x"
    assert L.size == 12


def test_pid_limited_internal_layout():
    """`pid-limited` Internal = i64, i32, bool → expect <qiB3x size 16."""
    L = _layout(
        [("integral_micro", "i64"), ("last_pv_micro", "i32"), ("initialized", "bool")]
    )
    assert L.fmt == "<qiB3x"
    assert L.size == 16


def test_anti_islanding_data_out_layout():
    """ANTI_ISLANDING DataOut = bool, u8, i64, i32, i64, u8, u8, u8 → <BB6xqi4xqBBB5x size 40."""
    L = _layout(
        [
            ("trip", "bool"),
            ("trip_reason", "u8"),
            ("rocof", "i64"),
            ("voltage_dev", "i32"),
            ("freq_dev", "i64"),
            ("rcnt", "u8"),
            ("vcnt", "u8"),
            ("fcnt", "u8"),
        ]
    )
    assert L.fmt == "<BB6xqi4xqBBB5x"
    assert L.size == 40


def test_anti_islanding_params_layout():
    """ANTI_ISLANDING Params = i64, u32, i64, i64, u32, i64, i64, u32, u32 → 64 bytes."""
    L = _layout(
        [
            ("rocof_thr", "i64"),
            ("rocof_win", "u32"),
            ("v_min", "i64"),
            ("v_max", "i64"),
            ("v_win", "u32"),
            ("f_min", "i64"),
            ("f_max", "i64"),
            ("f_win", "u32"),
            ("cycle_ms", "u32"),
        ]
    )
    assert L.fmt == "<qI4xqqI4xqqII"
    assert L.size == 64


def test_anti_islanding_data_in_layout():
    """ANTI_ISLANDING DataIn = i64×4 + u8×2 + bool → <qqqqBBB5x size 40."""
    L = _layout(
        [
            ("grid_freq", "i64"),
            ("freq_nominal", "i64"),
            ("grid_voltage", "i64"),
            ("voltage_nominal", "i64"),
            ("freq_quality", "u8"),
            ("voltage_quality", "u8"),
            ("enable", "bool"),
        ]
    )
    assert L.fmt == "<qqqqBBB5x"
    assert L.size == 40


def test_anti_islanding_internal_layout():
    """ANTI_ISLANDING Internal = i64 + u32×3 + u8 + bool → <qIIIBB2x size 24."""
    L = _layout(
        [
            ("last_freq", "i64"),
            ("rocof_count", "u32"),
            ("voltage_count", "u32"),
            ("freq_count", "u32"),
            ("last_trip_reason", "u8"),
            ("initialized", "bool"),
        ]
    )
    assert L.fmt == "<qIIIBB2x"
    assert L.size == 24


def test_struct_pack_round_trip_with_computed_format():
    L = _layout([("a", "i32"), ("b", "u8"), ("c", "bool"), ("d", "i64")])
    # i32 @ 0, u8 @ 4, bool @ 5, then 2 pad → i64 @ 8 → size 16
    assert L.size == 16
    assert L.fmt == "<iBB2xq"
    packed = struct.pack(L.fmt, 42, 7, 1, 999_999_999_999)
    a, b, c, d = struct.unpack(L.fmt, packed)
    assert (a, b, c, d) == (42, 7, 1, 999_999_999_999)


def test_unknown_rust_type_raises():
    with pytest.raises(ValueError, match="unknown rust_type"):
        _layout([("x", "u128")])


def test_empty_fields_yields_zero_size():
    L = codegen.compute_layout([])
    assert L.size == 0
    assert L.fmt == "<"


# ---------------------------------------------------------------------------
# emit_module smoke
# ---------------------------------------------------------------------------


def test_emit_module_produces_valid_python(tmp_path):
    manifest = {
        "iec61499_fbtype": "TEST_FB",
        "abi": {"init_export": "test_init", "tick_export": "test_tick"},
        "ecc": {"states": ["A", "B"], "initial": "A"},
        "tick_max_emitted": 1,
        "tick_max_neighbor_msgs": 0,
        "data_in_schema": [{"name": "x", "rust_type": "i32"}],
        "data_out_schema": [{"name": "y", "rust_type": "i32"}],
        "params_schema": [{"name": "k", "rust_type": "i32"}],
        "internal_schema": [{"name": "s", "rust_type": "i32"}],
    }
    fake_path = tmp_path / "mock-cell" / "manifest.json"
    fake_path.parent.mkdir()
    body = codegen.emit_module(manifest, fake_path)
    # Should parse as valid Python.
    out_file = tmp_path / "out.py"
    out_file.write_text(body)
    compile(out_file.read_text(), str(out_file), "exec")
    # Sanity: pack/unpack functions present.
    assert "def pack_data_in" in body
    assert "def unpack_data_out" in body
    assert "FBTYPE       = 'TEST_FB'" in body
    assert "DATA_IN_SIZE = 4" in body


# ---------------------------------------------------------------------------
# main(): --check flag detects drift
# ---------------------------------------------------------------------------


def test_check_mode_passes_when_files_in_sync(tmp_path):
    cells = tmp_path / "cells"
    out = tmp_path / "out"
    (cells / "cell-a").mkdir(parents=True)
    (cells / "cell-a" / "manifest.json").write_text(
        '{"iec61499_fbtype":"X","abi":{"init_export":"i","tick_export":"t"},'
        '"ecc":{"states":["A"],"initial":"A"},"tick_max_emitted":1,'
        '"data_in_schema":[],"data_out_schema":[],"params_schema":[],"internal_schema":[]}'
    )
    rc = codegen.main(["--cells-dir", str(cells), "--output-dir", str(out)])
    assert rc == 0
    rc2 = codegen.main(["--cells-dir", str(cells), "--output-dir", str(out), "--check"])
    assert rc2 == 0


def test_check_mode_fails_when_stale(tmp_path):
    cells = tmp_path / "cells"
    out = tmp_path / "out"
    (cells / "cell-a").mkdir(parents=True)
    (cells / "cell-a" / "manifest.json").write_text(
        '{"iec61499_fbtype":"X","abi":{"init_export":"i","tick_export":"t"},'
        '"ecc":{"states":["A"],"initial":"A"},"tick_max_emitted":1,'
        '"data_in_schema":[{"name":"x","rust_type":"i32"}],"data_out_schema":[],'
        '"params_schema":[],"internal_schema":[]}'
    )
    out.mkdir()
    (out / "cell_a.py").write_text("# stale stub")
    (out / "__init__.py").write_text("# stale __init__")
    rc = codegen.main(
        ["--cells-dir", str(cells), "--output-dir", str(out), "--check"]
    )
    assert rc == 1
