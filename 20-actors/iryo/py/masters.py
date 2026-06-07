#!/usr/bin/env python3
"""iryo 医療 — 診療報酬マスタ loader (診療行為 / 医薬品 / 特定器材 / 傷病名).

Pure stdlib. Loads a master table from JSON. The bundled ``seed_masters.json`` is a
REPRESENTATIVE seed for engine verification only — a production 保険医療機関 loads the
official 厚生労働省 / 社会保険診療報酬支払基金 master via :func:`Masters.load`.

The four master classes mirror the official レセプト電算処理システム masters:

  - 診療行為マスタ (shinryo) — keyed by 9-digit 診療行為コード → 点数 (ten) + 診療識別 (shikibetsu)
  - 医薬品マスタ   (iyaku)   — keyed by 医薬品コード → 薬価 (yakka, 円) + 単位 (unit)
  - 特定器材マスタ (tokutei) — keyed by 特定器材コード → 価格 (yakka, 円) + 単位 (unit)
  - 傷病名マスタ   (shobyo)  — keyed by 傷病名コード → 名称 + ICD-10

The engine never hard-codes a point value; everything is resolved through a Masters
instance so a clinic can swap in the official master without touching engine code.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

_SEED_PATH = os.path.join(os.path.dirname(__file__), "seed_masters.json")


@dataclass(frozen=True)
class ShinryoItem:
    code: str
    name: str
    ten: int          # 点数 (1点 = tensu_tanka_yen 円)
    shikibetsu: str   # 診療識別 (レセ電 2桁), e.g. "11" 初診 / "60" 検査


@dataclass(frozen=True)
class DrugItem:
    code: str
    name: str
    yakka: float      # 薬価 (円 / 単位)
    unit: str


@dataclass(frozen=True)
class MaterialItem:
    code: str
    name: str
    yakka: float      # 価格 (円 / 単位)
    unit: str


@dataclass(frozen=True)
class ShobyoItem:
    code: str
    name: str
    icd10: str


class MasterError(KeyError):
    """Raised when a code is not present in the loaded master."""


class Masters:
    """A resolved set of the four 診療報酬 masters."""

    def __init__(self, raw: dict):
        self.version: str = raw.get("version", "unknown")
        self.tensu_tanka_yen: int = int(raw.get("tensu_tanka_yen", 10))
        self._shinryo = {
            k: ShinryoItem(k, v["name"], int(v["ten"]), v["shikibetsu"])
            for k, v in raw.get("shinryo", {}).items()
        }
        self._iyaku = {
            k: DrugItem(k, v["name"], float(v["yakka"]), v.get("unit", ""))
            for k, v in raw.get("iyaku", {}).items()
        }
        self._tokutei = {
            k: MaterialItem(k, v["name"], float(v["yakka"]), v.get("unit", ""))
            for k, v in raw.get("tokutei", {}).items()
        }
        self._shobyo = {
            k: ShobyoItem(k, v["name"], v.get("icd10", ""))
            for k, v in raw.get("shobyo", {}).items()
        }

    # -- constructors ------------------------------------------------------ #
    @classmethod
    def load(cls, path: str | None = None) -> "Masters":
        with open(path or _SEED_PATH, encoding="utf-8") as fh:
            return cls(json.load(fh))

    @classmethod
    def from_dict(cls, raw: dict) -> "Masters":
        return cls(raw)

    # -- lookups ----------------------------------------------------------- #
    def shinryo(self, code: str) -> ShinryoItem:
        try:
            return self._shinryo[code]
        except KeyError:
            raise MasterError(f"診療行為コード not in master: {code}")

    def drug(self, code: str) -> DrugItem:
        try:
            return self._iyaku[code]
        except KeyError:
            raise MasterError(f"医薬品コード not in master: {code}")

    def material(self, code: str) -> MaterialItem:
        try:
            return self._tokutei[code]
        except KeyError:
            raise MasterError(f"特定器材コード not in master: {code}")

    def shobyo(self, code: str) -> ShobyoItem:
        try:
            return self._shobyo[code]
        except KeyError:
            raise MasterError(f"傷病名コード not in master: {code}")

    def has_shinryo(self, code: str) -> bool:
        return code in self._shinryo

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"Masters(version={self.version!r}, shinryo={len(self._shinryo)}, "
            f"iyaku={len(self._iyaku)}, tokutei={len(self._tokutei)}, "
            f"shobyo={len(self._shobyo)})"
        )


# A module-level default for convenience / tests.
def default_masters() -> Masters:
    return Masters.load()
