#!/usr/bin/env python3
"""iryo 医療 — 電子カルテ (診療録) data model with a structural PHI gate.

This is the clinical record that レセプト is computed *from*. The charter discipline
(mirrors karute/iyashi): any field that can identify a patient or carries clinical
free-text is PHI and MUST be carried as an encrypted-envelope CID, never as plaintext
on the shared substrate (ADR-2605181100 XChaCha20-Poly1305 + Signal key-wrap).

Structurally enforced here: :class:`Karte` separates a *public-meta* projection (codes
only — 傷病名コード/ICD-10/診療行為コード, dates, pseudonym DID) from the *PHI payload*
(name, DOB, address, SOAP free-text). The PHI payload is only ever exposed as an opaque
``encrypted_payload_cid``; attempting to attach a plaintext PHI field raises ``PhiLeak``.

Patient identity uses a rotating pseudonym DID (ADR-2605181200), never a stable MRN, so
the public-meta projection is not adversary-correlatable.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

# Fields that must NEVER appear in the public-meta projection (PHI).
PHI_FIELDS = frozenset({
    "name", "kana", "dob", "birthdate", "address", "phone", "email",
    "soap_s", "soap_o", "soap_a", "soap_p", "free_text", "note", "mrn",
})


class PhiLeak(ValueError):
    """Raised when a plaintext PHI field is attached to public meta."""


# --------------------------------------------------------------------------- #
# patient
# --------------------------------------------------------------------------- #
@dataclass
class Patient:
    """A patient referenced only by a rotating pseudonym DID in public meta.

    The PHI payload (name/DOB/address) lives behind ``encrypted_payload_cid`` and is
    never stored on this object as plaintext.
    """
    pseudonym_did: str               # did:web rotating pseudonym (ADR-2605181200)
    sex: str = "U"                   # 1男/2女 のレセ電区分は receden 側で変換
    birth_year: Optional[int] = None  # 年齢区分(乳幼児/高齢)算定にのみ使う粗い年; 月日はPHI
    encrypted_payload_cid: Optional[str] = None  # name/DOB/address envelope CID

    def age_on(self, on: date) -> Optional[int]:
        if self.birth_year is None:
            return None
        return on.year - self.birth_year


# --------------------------------------------------------------------------- #
# insurance (保険)
# --------------------------------------------------------------------------- #
@dataclass
class Insurance:
    """被保険者の保険資格. 記号・番号は識別子のため PHI envelope 側で扱う想定で,
    ここでは算定に必要な公的属性(保険者番号・給付割合・本人家族区分)のみを持つ。"""
    hokensha_bango: str              # 保険者番号 (8桁: 社保 / 6桁: 国保)
    futan_wari: float = 0.3          # 給付に対する患者負担割合
    honnin_kazoku: str = "honnin"    # honnin 本人 / kazoku 家族
    kogaku_kubun: Optional[str] = None  # 高額療養費 所得区分 ア〜オ
    kohi: list[str] = field(default_factory=list)  # 公費負担者番号 (任意)


# --------------------------------------------------------------------------- #
# 傷病名 (diagnosis) — codes are NOT PHI (terminology binding)
# --------------------------------------------------------------------------- #
@dataclass
class Diagnosis:
    shobyo_code: str                 # 傷病名マスタコード
    icd10: str
    name: str                        # 標準傷病名 (マスタ名称; 個人を識別しない)
    onset: Optional[str] = None      # 診療開始日 YYYY-MM-DD
    outcome: str = "継続"            # 転帰: 継続/治癒/死亡/中止
    is_main: bool = False            # 主傷病


# --------------------------------------------------------------------------- #
# SOAP — free text is PHI; only the encrypted CID is retained
# --------------------------------------------------------------------------- #
@dataclass
class SoapNote:
    """SOAP 経過記録. 本文は PHI → encrypted_cid のみ保持. 公開メタは作成日と署名者のみ。"""
    encounter_date: str              # YYYY-MM-DD
    author_did: str
    encrypted_cid: str               # SOAP free-text envelope CID (MANDATORY)

    def __post_init__(self):
        if not self.encrypted_cid:
            raise PhiLeak("SoapNote requires encrypted_cid (SOAP free-text is PHI)")


# --------------------------------------------------------------------------- #
# karte aggregate
# --------------------------------------------------------------------------- #
@dataclass
class Karte:
    """One patient's chart slice for a billing month."""
    patient: Patient
    insurance: Insurance
    diagnoses: list[Diagnosis] = field(default_factory=list)
    notes: list[SoapNote] = field(default_factory=list)

    def public_meta(self) -> dict:
        """The non-PHI projection safe to index on the public graph (codes + DIDs only)."""
        return {
            "patientDid": self.patient.pseudonym_did,
            "sex": self.patient.sex,
            "hokenshaBango": self.insurance.hokensha_bango,
            "futanWari": self.insurance.futan_wari,
            "diagnoses": [
                {"shobyoCode": d.shobyo_code, "icd10": d.icd10,
                 "isMain": d.is_main, "outcome": d.outcome, "onset": d.onset}
                for d in self.diagnoses
            ],
            "noteCount": len(self.notes),
            "encryptedPayloadCid": self.patient.encrypted_payload_cid,
        }

    @staticmethod
    def assert_no_phi(meta: dict) -> None:
        """Guard: reject any public-meta dict that smuggled a plaintext PHI field."""
        for key in meta:
            if key.lower() in PHI_FIELDS:
                raise PhiLeak(f"plaintext PHI field in public meta: {key}")
            if key == "diagnoses":
                for d in meta["diagnoses"]:
                    for dk in d:
                        if dk.lower() in PHI_FIELDS:
                            raise PhiLeak(f"plaintext PHI field in diagnosis: {dk}")


def rotating_pseudonym_did(stable_secret: str, period: str) -> str:
    """Derive a rotating pseudonym DID (ADR-2605181200) from a patient secret + period.

    period e.g. "2026-06" → a new pseudonym each month, so the public-meta projection
    cannot be correlated across periods by an adversary.
    """
    h = hashlib.blake2b(f"{stable_secret}|{period}".encode(), digest_size=16).hexdigest()
    return f"did:web:patient.iryo.etzhayyim.com:{h}"
