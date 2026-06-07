#!/usr/bin/env python3
"""iryo 医療 — レセプト/医療保険請求 engine cell (kotoba WASM cell).

iryo is the **billing counterpart** to the karute 電子カルテ (EMR): karute holds the
encrypted clinical record, iryo computes the レセプト (診療報酬請求) FROM it and emits the
レセ電 (online-claim) stream + a FHIR claim. It is the charter-clean inversion of a
proprietary レセコン / EHR-billing vendor (ORCA-proprietary / Epic / Cerner):

  handle_rezept   診療録(encounter) → 点数計算 (区分集計 / 一部負担金 / 高額療養費)
  handle_receden  karte + rezept → レセ電 (レセプト電算) record stream + 件数 reconciliation
  handle_validate karte + rezept → 算定整合性チェック (病名なし投薬 / 上限 等) — non-adjudicating

Constitutional posture (G-gates):

  G1 member-principal   — the licensed 保険医療機関 is the billing PRINCIPAL; iryo is open
                          substrate only. iryo never originates a claim on its own key.
  G2 PHI-encrypted      — clinical free-text / 氏名 / 生年月日 are PHI; they enter the レセ電
                          stream only via the operator's decrypt callback at submission time,
                          never the public substrate (ADR-2605181100).
  G3 no-server-key      — online 請求 (送信) is operator-gated; iryo computes + drafts only.
  G4 master-honest      — points are resolved through a loaded 厚労省 master; the bundled seed
                          is representative and the engine never hard-codes a tariff value.
  G5 non-adjudicating   — validation EMITS discrepancy observations; the 審査支払機関 (基金/国保連)
                          and the clinic decide. iryo does not approve/deny a claim.
  G6 Murakumo-only      — any narration is via the kotoba `llm` host binding (no external LLM).
"""
from __future__ import annotations

from typing import TypedDict

try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

import receden as _receden
from fhir import to_fhir_bundle
from karte import Diagnosis, Insurance, Karte, Patient
from masters import Masters, default_masters
from rezept import (ActLine, DrugDose, Encounter, MaterialLine, Prescription,
                    compute)

INTENT = "member-principal-claim-substrate; non-adjudicating"


# --------------------------------------------------------------------------- #
# input decoding (plain dict → dataclasses, so cells can be driven from JSON)
# --------------------------------------------------------------------------- #
def _encounter_from(d: dict) -> Encounter:
    fw = d.get("futanWari", 0.3)
    return Encounter(
        futan_wari=(None if fw is None else float(fw)),
        kogaku_kubun=d.get("kogakuKubun"),
        age=d.get("age"),
        gen_eki=bool(d.get("genEki", False)),
        ittei_ijo=bool(d.get("itteiIjo", False)),
        nyuin=bool(d.get("nyuin", False)),
        kohi=d.get("kohi", []),
        shokuji_meals=int(d.get("shokujiMeals", 0)),
        shokuji_tanka_yen=int(d.get("shokujiTankaYen", 490)),
        acts=[ActLine(a["code"], int(a.get("count", 1))) for a in d.get("acts", [])],
        prescriptions=[
            Prescription(
                shikibetsu=p.get("shikibetsu", "21"),
                drugs=[DrugDose(x["code"], float(x.get("amount", 1))) for x in p["drugs"]],
                days=int(p.get("days", 1)),
                label=p.get("label", ""),
            )
            for p in d.get("prescriptions", [])
        ],
        materials=[
            MaterialLine(mt["code"], float(mt.get("amount", 1)), mt.get("shikibetsu", "40"))
            for mt in d.get("materials", [])
        ],
    )


def _karte_from(d: dict) -> Karte:
    p = d.get("patient", {})
    ins = d.get("insurance", {})
    return Karte(
        patient=Patient(
            pseudonym_did=p.get("pseudonymDid", "did:web:patient.iryo.etzhayyim.com:anon"),
            sex=p.get("sex", "U"),
            birth_year=p.get("birthYear"),
            encrypted_payload_cid=p.get("encryptedPayloadCid"),
        ),
        insurance=Insurance(
            hokensha_bango=ins.get("hokenshaBango", "00000000"),
            futan_wari=float(ins.get("futanWari", 0.3)),
            honnin_kazoku=ins.get("honninKazoku", "honnin"),
            kogaku_kubun=ins.get("kogakuKubun"),
            kohi=ins.get("kohi", []),
        ),
        diagnoses=[
            Diagnosis(
                shobyo_code=x["shobyoCode"], icd10=x.get("icd10", ""),
                name=x.get("name", ""), onset=x.get("onset"),
                outcome=x.get("outcome", "継続"), is_main=bool(x.get("isMain", False)),
            )
            for x in d.get("diagnoses", [])
        ],
    )


def _masters(d: dict) -> Masters:
    return Masters.from_dict(d["masters"]) if d.get("masters") else default_masters()


# --------------------------------------------------------------------------- #
# cells
# --------------------------------------------------------------------------- #
class RezeptState(TypedDict, total=False):
    encounter: dict
    masters: dict
    result: dict


def handle_rezept(state: dict) -> dict:
    """encounter → computed レセプト (区分集計 / 一部負担金 / 高額療養費). G4 master-honest."""
    enc = _encounter_from(state["encounter"])
    rez = compute(enc, _masters(state))
    return {"result": rez.to_dict(), "intent": INTENT}


def handle_receden(state: dict) -> dict:
    """karte + encounter → レセ電 record stream + 件数 reconciliation. G2 PHI-free by default."""
    m = _masters(state)
    enc = _encounter_from(state["encounter"])
    karte = _karte_from(state["karte"])
    rez = compute(enc, m)
    inst = state.get("institution", {})
    institution = _receden.Institution(
        shinsa_shiharai=inst.get("shinsaShiharai", "1"),
        prefecture=inst.get("prefecture", "13"),
        iryokikan_code=inst.get("iryokikanCode", "1234567"),
        name=inst.get("name", ""),
    )
    rows = _receden.build_receden(
        institution, karte, rez,
        shinryo_year=int(state.get("shinryoYear", 2026)),
        shinryo_month=int(state.get("shinryoMonth", 6)),
        jitsunissu=int(state.get("jitsunissu", 1)),
        nyuin=bool(state.get("encounter", {}).get("nyuin", False)),
        tokki=state.get("tokki"),
        comments=state.get("comments"),
        shojo_shoki=state.get("shojoShoki"),
    )
    return {
        "records": rows,
        "csv": _receden.to_csv(rows),
        "summary": _receden.record_summary(rows),
        "totalTen": rez.total_ten,
        "patientPayYen": rez.patient_pay_yen,
        "state": "draft",            # G3 no-server-key: online 請求 is operator-gated
        "intent": INTENT,
    }


def handle_validate(state: dict) -> dict:
    """算定整合性チェック → discrepancy observations (G5 non-adjudicating).

    Surfaces (does not block): 病名のない投薬/検査の疑い, 高額療養費 上限超過, 空レセプト。
    The clinic + 審査支払機関 decide; iryo only observes.
    """
    m = _masters(state)
    enc = _encounter_from(state["encounter"])
    karte = _karte_from(state["karte"])
    rez = compute(enc, m)

    obs: list[dict] = []
    if not karte.diagnoses:
        obs.append({"code": "NO_DIAGNOSIS",
                    "msg": "傷病名が1件もない (投薬/検査の算定根拠を要確認)"})
    if not any(d.is_main for d in karte.diagnoses) and karte.diagnoses:
        obs.append({"code": "NO_MAIN_DIAGNOSIS", "msg": "主傷病が指定されていない"})
    if rez.total_ten == 0:
        obs.append({"code": "EMPTY_REZEPT", "msg": "算定点数が0 (空レセプト)"})
    if enc.prescriptions and not karte.diagnoses:
        obs.append({"code": "RX_WITHOUT_DX", "msg": "病名なしで投薬が算定されている"})
    if rez.kogaku_applied:
        obs.append({"code": "KOGAKU_CAPPED",
                    "msg": f"高額療養費適用: 窓口負担が限度額 {rez.kogaku_limit_yen}円 に調整された"})

    return {
        "observations": obs,
        "ok": not any(o["code"] in ("NO_DIAGNOSIS", "EMPTY_REZEPT", "RX_WITHOUT_DX")
                      for o in obs),
        "totalTen": rez.total_ten,
        "intent": INTENT,
    }


def export_fhir(state: dict) -> dict:
    """karte + encounter → FHIR R4 Claim Bundle (codes-only, PHI-free)."""
    m = _masters(state)
    enc = _encounter_from(state["encounter"])
    karte = _karte_from(state["karte"])
    rez = compute(enc, m)
    return {"bundle": to_fhir_bundle(karte, rez), "intent": INTENT}
