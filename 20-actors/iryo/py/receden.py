#!/usr/bin/env python3
"""iryo 医療 — レセプト電算処理システム (レセ電 / UKE) record generator.

Emits the comma-separated, 2-char-identifier record stream consumed by the
審査支払機関 (社会保険診療報酬支払基金 / 国保連) online claim system:

  IR 医療機関情報   — 1件/ファイル: 審査支払機関・都道府県・点数表・医療機関コード
  RE レセプト共通   — 1件/レセプト: レセプト種別・診療年月・氏名・性別・生年月日
  HO 保険者         — 保険者番号・給付割合・診療実日数・合計点数・一部負担金
  KO 公費           — 公費負担者番号 (任意)
  SY 傷病名         — 傷病名コード・診療開始日・転帰・主傷病・ICD-10
  SI 診療行為       — 診療識別・負担区分・診療行為コード・数量・点数・回数
  IY 医薬品         — 診療識別・負担区分・医薬品コード・使用量・点数・回数
  TO 特定器材       — 診療識別・負担区分・特定器材コード・使用量・点数・回数
  CO コメント       — コメントコード + 文字データ

PHI discipline (charter): real レセ電 carries 氏名/生年月日, but that transmission is to
the 審査支払機関 over the closed オンライン請求 IP-VPN — never the public substrate. So PHI is
injected here only through the optional ``phi`` callback at submission time; by default the
氏名 field carries the pseudonym DID tail and 生年月日 is blank, so demo/test output holds
no patient-identifying data.

Field layouts follow the documented レセ電 record shape; a production submitter MUST validate
against the current 厚生労働省 記録条件仕様 before live online 請求.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional

from karte import Karte
from rezept import RezeptResult

# 元号コード (レセ電 日付 GYYMMDD の先頭1桁)
_ERAS = [
    (date(2019, 5, 1), 5, 2018),   # 令和
    (date(1989, 1, 8), 4, 1988),   # 平成
    (date(1926, 12, 25), 3, 1925),  # 昭和
    (date(1912, 7, 30), 2, 1911),  # 大正
    (date(1868, 1, 25), 1, 1867),  # 明治
]


def wareki(d: date) -> str:
    """date → GYYMMDD (G=元号1桁, YY=和暦年2桁, MMDD)."""
    for start, code, base in _ERAS:
        if d >= start:
            yy = d.year - base
            return f"{code}{yy:02d}{d.month:02d}{d.day:02d}"
    raise ValueError(f"date out of supported 元号 range: {d}")


def wareki_ym(year: int, month: int) -> str:
    """診療年月 → GYYMM (G=元号, YY=和暦年, MM=月)."""
    return wareki(date(year, month, 1))[:5]


# レセプト種別 4桁 = [医保点数表][入院/入院外][本人/家族] (representative encoding).
#   1桁目: 1=医科  2桁目: 1=医保(社保系) 2=国保  3桁目: 1=入院 2=入院外  4桁目: 2=本人 6=家族 ...
def rezept_shubetsu(*, nyuin: bool, honnin: bool, kokuho: bool) -> str:
    seido = "2" if kokuho else "1"
    nyuin_d = "1" if nyuin else "2"
    honkazoku = "2" if honnin else "6"
    return f"1{seido}{nyuin_d}{honkazoku}"


def _sex_code(sex: str) -> str:
    return {"M": "1", "男": "1", "1": "1", "F": "2", "女": "2", "2": "2"}.get(sex, "3")


@dataclass
class Institution:
    """医療機関情報 (IR レコード)."""
    shinsa_shiharai: str   # 審査支払機関 1=社保 2=国保
    prefecture: str        # 都道府県コード 2桁
    tensu_hyo: str = "1"   # 点数表 1=医科
    iryokikan_code: str = "0000000"  # 医療機関コード 7桁
    name: str = ""


def build_receden(
    inst: Institution,
    karte: Karte,
    rez: RezeptResult,
    *,
    shinryo_year: int,
    shinryo_month: int,
    jitsunissu: int = 1,
    nyuin: bool = False,
    rezept_no: int = 1,
    phi: Optional[Callable[[Karte], dict]] = None,
    tokki: Optional[list[str]] = None,        # 特記事項コード (TY)
    comments: Optional[list[dict]] = None,    # [{"shikibetsu","code","text"}] (CO)
    shojo_shoki: Optional[list[str]] = None,  # 症状詳記 (SJ) — operator-supplied, may be PHI
) -> list[list[str]]:
    """Build the レセ電 record stream (list of CSV rows) for one レセプト.

    ``phi(karte) -> {"name": .., "birth": date, ...}`` is the only path PHI enters the
    stream; omit it (default) for charter-clean, PHI-free demo/test output.
    """
    rows: list[list[str]] = []
    phi_data = phi(karte) if phi else {}

    # IR — 医療機関情報
    rows.append([
        "IR", inst.shinsa_shiharai, inst.prefecture, inst.tensu_hyo,
        inst.iryokikan_code, "1", wareki_ym(shinryo_year, shinryo_month),
    ])

    # RE — レセプト共通
    shubetsu = rezept_shubetsu(
        nyuin=nyuin,
        honnin=(karte.insurance.honnin_kazoku == "honnin"),
        kokuho=(len(karte.insurance.hokensha_bango) == 6),
    )
    name = phi_data.get("name") or karte.patient.pseudonym_did.rsplit(":", 1)[-1]
    birth = wareki(phi_data["birth"]) if phi_data.get("birth") else ""
    rows.append([
        "RE", str(rezept_no), shubetsu, wareki_ym(shinryo_year, shinryo_month),
        name, _sex_code(karte.patient.sex), birth,
    ])

    # TY — 特記事項 (任意; 高額療養費区分 等)
    if tokki:
        rows.append(["TY"] + list(tokki))

    # HO — 保険者
    kyufu = int(round((1.0 - rez.futan_wari) * 10))  # 給付割合 (10割中)
    rows.append([
        "HO", karte.insurance.hokensha_bango, phi_data.get("hihokensha", ""),
        str(kyufu), str(jitsunissu), str(rez.total_ten), str(rez.patient_pay_yen),
    ])

    # KO — 公費 (任意)
    for fusha in karte.insurance.kohi:
        rows.append(["KO", fusha, str(rez.total_ten), str(rez.patient_pay_yen)])

    # SY — 傷病名
    for d in karte.diagnoses:
        onset = ""
        if d.onset:
            y, mo, da = (int(x) for x in d.onset.split("-"))
            onset = wareki(date(y, mo, da))
        rows.append([
            "SY", d.shobyo_code, onset, _tenki_code(d.outcome),
            "01" if d.is_main else "", d.icd10,
        ])

    # SI / IY / TO — 算定明細 (負担区分は line から; 保険単独=1 / 保険+公費=2,3 …)
    for line in rez.lines:
        fk = getattr(line, "futan_kubun", "1")
        if line.kind == "act":
            rows.append(["SI", line.shikibetsu, fk, line.code,
                         str(line.count), str(line.unit_ten), str(line.count)])
        elif line.kind == "drug":
            rows.append(["IY", line.shikibetsu, fk, line.code,
                         "", str(line.unit_ten), str(line.count)])
        elif line.kind == "material":
            rows.append(["TO", line.shikibetsu, fk, line.code,
                         "", str(line.ten), str(line.count)])

    # CO — コメント (コメントコード + 文字データ; 区分つき)
    for c in (comments or []):
        rows.append(["CO", c.get("shikibetsu", ""), c.get("code", ""), c.get("text", "")])

    # SJ — 症状詳記 (operator-supplied free text; may be PHI → operator's responsibility)
    for i, sj in enumerate(shojo_shoki or [], start=1):
        rows.append(["SJ", f"{i:02d}", sj])

    return rows


def _tenki_code(outcome: str) -> str:
    return {"継続": "", "治癒": "1", "死亡": "2", "中止": "3", "軽快": "4"}.get(outcome, "")


def to_csv(rows: list[list[str]], *, newline: str = "\r\n") -> str:
    """Serialize the record stream to レセ電 CSV text (CR+LF per spec)."""
    return newline.join(",".join(_q(c) for c in row) for row in rows) + newline


def _q(cell: str) -> str:
    s = str(cell)
    return f'"{s}"' if ("," in s or '"' in s) else s


def record_summary(rows: list[list[str]]) -> dict[str, int]:
    """Count records by identifier (for the 件数 reconciliation a submitter performs)."""
    out: dict[str, int] = {}
    for r in rows:
        out[r[0]] = out.get(r[0], 0) + 1
    return out


def uke_filename(inst: Institution, year: int, month: int) -> str:
    """レセ電ファイル名 (RECEIPTC.UKE 慣行の代表; 実運用は審査支払機関の規定に従う)."""
    return f"RECEIPTC_{inst.iryokikan_code}_{year}{month:02d}.UKE"
