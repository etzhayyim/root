#!/usr/bin/env python3
"""iryo 医療 — 診療報酬マスタ ingestion (官公式マスタ全件対応).

The engine resolves every point/price through a master, so "all 診療行為 / 薬剤 / 特定器材
/ 病名 に対応" means: **be able to ingest the complete official master**, not embed it. The
official 厚生労働省 基本マスター / 社会保険診療報酬支払基金 レセプト電算マスター are tens of
thousands of CSV rows (copyrighted, redistributed by the 支払基金). This module loads them.

Two input formats are supported:

1. **Normalized CSV** (the format iryo defines + fully tests) — one file per master class:

       shinryo.csv : code,name,ten,shikibetsu[,unit]
       iyaku.csv   : code,name,yakka,unit
       tokutei.csv : code,name,yakka,unit
       shobyo.csv  : code,name,icd10
       shushokugo.csv (修飾語) : code,name
       comment.csv : code,pattern,name

   A clinic that has exported / normalized the official master uses this path.

2. **MHLW 官公式マスター** (`load_mhlw_*`) — the raw 基本マスター CSV. Column positions are
   given by an overridable :class:`ColMap` with documented defaults; because the official
   record layout has ~90 columns and changes by 改定, the operator MUST verify the column
   map against the current 記録条件仕様 before trusting a production load. The parser itself
   is format-tolerant (quoted CSV, variable column count).

Both paths feed :meth:`Masters.merge`, so seed + official master compose: load the official
master over the representative seed and every code is covered.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass

from masters import Masters


# --------------------------------------------------------------------------- #
# 1) normalized CSV (iryo-defined, fully tested)
# --------------------------------------------------------------------------- #
def _read_rows(path: str) -> list[list[str]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return [r for r in csv.reader(fh) if r and not r[0].lstrip().startswith("#")]


def load_normalized(directory: str) -> dict:
    """Load a directory of normalized CSVs into a raw masters dict (→ Masters.from_dict)."""
    raw: dict = {"version": f"normalized:{os.path.basename(directory.rstrip('/'))}",
                 "tensu_tanka_yen": 10,
                 "shinryo": {}, "iyaku": {}, "tokutei": {}, "shobyo": {},
                 "shushokugo": {}, "comment": {}}

    def _opt(name: str) -> list[list[str]]:
        p = os.path.join(directory, name)
        return _read_rows(p) if os.path.exists(p) else []

    for r in _opt("shinryo.csv"):
        code, name, ten, shikibetsu = r[0], r[1], int(r[2]), r[3]
        raw["shinryo"][code] = {"name": name, "ten": ten, "shikibetsu": shikibetsu}
    for r in _opt("iyaku.csv"):
        raw["iyaku"][r[0]] = {"name": r[1], "yakka": float(r[2]),
                              "unit": r[3] if len(r) > 3 else ""}
    for r in _opt("tokutei.csv"):
        raw["tokutei"][r[0]] = {"name": r[1], "yakka": float(r[2]),
                                "unit": r[3] if len(r) > 3 else ""}
    for r in _opt("shobyo.csv"):
        raw["shobyo"][r[0]] = {"name": r[1], "icd10": r[2] if len(r) > 2 else ""}
    for r in _opt("shushokugo.csv"):
        raw["shushokugo"][r[0]] = {"name": r[1]}
    for r in _opt("comment.csv"):
        raw["comment"][r[0]] = {"pattern": r[1] if len(r) > 1 else "",
                                "name": r[2] if len(r) > 2 else ""}
    return raw


# --------------------------------------------------------------------------- #
# 2) MHLW 官公式マスター (column-map driven; defaults documented as approximate)
# --------------------------------------------------------------------------- #
@dataclass
class ColMap:
    """0-indexed column positions in an MHLW 基本マスター CSV row.

    Defaults approximate the documented 記録条件仕様; OVERRIDE per the current 改定 spec.
    Negative / out-of-range indices are skipped gracefully.
    """
    code: int
    name: int
    value: int          # 点数 (診療行為) / 薬価・価格 (医薬品・特定器材)
    unit: int = -1
    shikibetsu: int = -1  # 診療行為のみ (診療識別/データ区分由来)
    icd10: int = -1       # 傷病名のみ


# Documented-approximate defaults. (The real 診療行為マスタ has 新又は現点数 near col 22;
# 省略名称 near col 5; code at col 3. These are the common positions but MUST be verified.)
MHLW_DEFAULTS = {
    "shinryo": ColMap(code=2, name=4, value=22, shikibetsu=8),
    "iyaku":   ColMap(code=2, name=4, value=8, unit=6),
    "tokutei": ColMap(code=2, name=4, value=8, unit=6),
    "shobyo":  ColMap(code=2, name=5, value=-1, icd10=6),
}


def _cell(row: list[str], idx: int) -> str:
    return row[idx].strip() if 0 <= idx < len(row) else ""


def load_mhlw_shinryo(path: str, colmap: ColMap | None = None) -> dict:
    cm = colmap or MHLW_DEFAULTS["shinryo"]
    out: dict = {}
    for row in _read_rows(path):
        code = _cell(row, cm.code)
        if not code:
            continue
        try:
            ten = int(float(_cell(row, cm.value) or 0))
        except ValueError:
            ten = 0
        out[code] = {"name": _cell(row, cm.name), "ten": ten,
                     "shikibetsu": _cell(row, cm.shikibetsu) or "80"}
    return out


def load_mhlw_priced(path: str, kind: str, colmap: ColMap | None = None) -> dict:
    """医薬品 / 特定器材 (価格を持つマスタ)."""
    cm = colmap or MHLW_DEFAULTS[kind]
    out: dict = {}
    for row in _read_rows(path):
        code = _cell(row, cm.code)
        if not code:
            continue
        try:
            yakka = float(_cell(row, cm.value) or 0)
        except ValueError:
            yakka = 0.0
        out[code] = {"name": _cell(row, cm.name), "yakka": yakka,
                     "unit": _cell(row, cm.unit)}
    return out


def load_mhlw_shobyo(path: str, colmap: ColMap | None = None) -> dict:
    cm = colmap or MHLW_DEFAULTS["shobyo"]
    out: dict = {}
    for row in _read_rows(path):
        code = _cell(row, cm.code)
        if not code:
            continue
        out[code] = {"name": _cell(row, cm.name), "icd10": _cell(row, cm.icd10)}
    return out


def load_mhlw_dir(directory: str, *, colmaps: dict | None = None) -> dict:
    """Load a directory of MHLW masters by filename prefix (s=診療行為 y=医薬品 t=特定器材 b=傷病名)."""
    cmaps = colmaps or {}
    raw: dict = {"version": f"mhlw:{os.path.basename(directory.rstrip('/'))}",
                 "tensu_tanka_yen": 10,
                 "shinryo": {}, "iyaku": {}, "tokutei": {}, "shobyo": {},
                 "shushokugo": {}, "comment": {}}
    for fn in sorted(os.listdir(directory)):
        p = os.path.join(directory, fn)
        low = fn.lower()
        if not low.endswith(".csv"):
            continue
        if low.startswith("s"):
            raw["shinryo"].update(load_mhlw_shinryo(p, cmaps.get("shinryo")))
        elif low.startswith("y"):
            raw["iyaku"].update(load_mhlw_priced(p, "iyaku", cmaps.get("iyaku")))
        elif low.startswith("t"):
            raw["tokutei"].update(load_mhlw_priced(p, "tokutei", cmaps.get("tokutei")))
        elif low.startswith("b") or low.startswith("shobyo"):
            raw["shobyo"].update(load_mhlw_shobyo(p, cmaps.get("shobyo")))
    return raw


# --------------------------------------------------------------------------- #
# convenience: seed + official master composed
# --------------------------------------------------------------------------- #
def masters_with_official(directory: str, *, fmt: str = "normalized",
                          base: Masters | None = None) -> Masters:
    """Compose the representative seed (or `base`) with a loaded official/normalized master."""
    raw = load_normalized(directory) if fmt == "normalized" else load_mhlw_dir(directory)
    loaded = Masters.from_dict(raw)
    base = base or Masters.load()
    return base.merge(loaded)
