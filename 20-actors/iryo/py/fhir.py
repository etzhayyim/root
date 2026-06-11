#!/usr/bin/env python3
"""iryo 医療 — FHIR export (Coverage / Condition / Claim) + SS-MIX2 hint.

Maps the computed レセプト to an interoperable FHIR R4 Bundle so a clinic can hand a
machine-readable claim to an external system without exposing PHI. The Bundle carries
codes only (傷病名 ICD-10, 診療行為/医薬品コード, pseudonym patient reference) — name/DOB
stay in the encrypted envelope, consistent with the karte PHI gate.

  傷病名      → Condition (ICD-10-JP urn:oid binding)
  保険資格    → Coverage
  レセプト    → Claim (item per 算定明細, total in 点 and 円)

This is a faithful FHIR *shape*; a production exporter binds the official JP Core profiles.
"""
from __future__ import annotations

from karte import Karte
from rezept import RezeptResult

ICD10_JP_SYSTEM = "urn:oid:1.2.392.200119.4.504.4"      # ICD-10 対応標準病名 (日本)
SHINRYO_SYSTEM = "urn:oid:1.2.392.200119.4.403.1"        # 診療行為マスター
IYAKU_SYSTEM = "urn:oid:1.2.392.100495.20.2.74"          # 医薬品 HOT/レセ電
HOKEN_SYSTEM = "urn:oid:1.2.392.200119.4.204"            # 保険者番号


def to_fhir_bundle(karte: Karte, rez: RezeptResult, *, claim_id: str = "rezept-1") -> dict:
    patient_ref = {"reference": f"Patient/{_tail(karte.patient.pseudonym_did)}"}
    entries: list[dict] = []

    # Coverage
    entries.append({"resource": {
        "resourceType": "Coverage",
        "id": "coverage-1",
        "status": "active",
        "beneficiary": patient_ref,
        "payor": [{"identifier": {
            "system": HOKEN_SYSTEM, "value": karte.insurance.hokensha_bango}}],
        "extension": [{
            "url": "https://iryo.etzhayyim.com/fhir/futanWari",
            "valueDecimal": karte.insurance.futan_wari,
        }],
    }})

    # Condition (傷病名)
    for i, d in enumerate(karte.diagnoses):
        entries.append({"resource": {
            "resourceType": "Condition",
            "id": f"condition-{i+1}",
            "subject": patient_ref,
            "clinicalStatus": {"coding": [{"code": _condition_status(d.outcome)}]},
            "code": {"coding": [{"system": ICD10_JP_SYSTEM, "code": d.icd10,
                                 "display": d.name}]},
            "onsetString": d.onset or "",
        }})

    # Claim (レセプト)
    items = []
    for n, line in enumerate(rez.lines, start=1):
        system = IYAKU_SYSTEM if line.kind == "drug" else SHINRYO_SYSTEM
        items.append({
            "sequence": n,
            "productOrService": {"coding": [{
                "system": system, "code": line.code, "display": line.name}]},
            "quantity": {"value": line.count},
            "unitPrice": {"value": line.unit_ten, "unit": "点"},
            "net": {"value": line.ten, "unit": "点"},
            "category": {"text": line.kubun},
        })
    entries.append({"resource": {
        "resourceType": "Claim",
        "id": claim_id,
        "status": "active",
        "type": {"coding": [{"code": "institutional"}]},
        "use": "claim",
        "patient": patient_ref,
        "insurance": [{"sequence": 1, "focal": True,
                       "coverage": {"reference": "Coverage/coverage-1"}}],
        "item": items,
        "total": {"value": rez.total_ten, "unit": "点"},
        "extension": [
            {"url": "https://iryo.etzhayyim.com/fhir/totalIryohiYen",
             "valueInteger": rez.total_iryohi_yen},
            {"url": "https://iryo.etzhayyim.com/fhir/patientPayYen",
             "valueInteger": rez.patient_pay_yen},
            {"url": "https://iryo.etzhayyim.com/fhir/kogakuApplied",
             "valueBoolean": rez.kogaku_applied},
        ],
    }})

    return {"resourceType": "Bundle", "type": "collection", "entry": entries}


def _tail(did: str) -> str:
    return did.rsplit(":", 1)[-1]


def _condition_status(outcome: str) -> str:
    return {"治癒": "resolved", "軽快": "remission", "中止": "inactive",
            "死亡": "inactive"}.get(outcome, "active")
