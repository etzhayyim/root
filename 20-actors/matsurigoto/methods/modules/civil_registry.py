#!/usr/bin/env python3
"""matsurigoto 政 — `civil-registry` module (R0 reference implementation).

ADR-2606052300. Second executable vertical slice: the CRVS (Civil Registration & Vital
Statistics) engine behind `civil.birth.register` / `civil.death.register` /
`civil.marriage.register` / `residency.move-in` / `residency.certificate` — i.e. 住所管理・戸籍.

WHAT IT IS: pure-function VALIDATION + APPEND-ONLY RECORD CONSTRUCTION for vital events,
shaped on the UN CRVS principles + OpenCRVS data model. A registration is validated (a birth
needs a child + ≥1 parent + a non-future occurrence; a marriage needs two DISTINCT, unmarried
partners; a death needs a decedent), then emitted as an immutable kotoba datom + an UNSIGNED
certificate skeleton (a W3C VC the governing organ signs with ITS own key).

Charter invariants (nusa/tazuna/ake pattern), why 住所管理 is charter-clean here:
  G1 no-operator-master-key : SERVER_HELD_AUTHORITY False; certificates returned UNSIGNED — the
                              Council (sovereign) / adopting state signs, never this module.
  G2 spec-derived-only      : UN CRVS + OpenCRVS + W3C VC 2.0 shapes only.
  G5 append-only (非終末論)  : every helper RETURNS A NEW record list; nothing is overwritten.
                              A correction is itself an appended record (kotoba-canonical
                              ADR-2605312345 + ake G5). No :delete / :overwrite exists.
  G6 data-minimization      : only the fields the vital event requires; no surveillance surface.

stdlib only, no I/O, no network. Importable as a kotoba-wasm module contract.
"""
from __future__ import annotations

# G1: this module holds NO signing authority and signs no certificate.
SERVER_HELD_AUTHORITY = False

_VITAL_KINDS = {"birth", "death", "marriage"}


def _iso(s: str) -> str:
    """ISO-8601 strings sort lexically; we only need ordering + non-future checks (no parsing lib)."""
    if not isinstance(s, str) or len(s) < 4 or not s[:4].isdigit():
        raise ValueError(f"timestamp must be ISO-8601, got {s!r}")
    return s


def _unsigned_certificate(kind: str, subject: str, record_id: str) -> dict:
    """A W3C-VC certificate SKELETON. G1: unsigned — the governing organ signs with ITS key."""
    return {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "type": ["VerifiableCredential", f"{kind.capitalize()}Certificate"],
        "credentialSubject": {"id": subject, "record": record_id},
        "proof": None,                                   # G1 — this module signs nothing
        "server_held_authority": SERVER_HELD_AUTHORITY,  # False
        "status": "issued-unsigned",
    }


def _record(kind: str, record_id: str, fields: dict, occurred_at: str) -> dict:
    """An immutable CRVS datom (append-only). 非終末論: this is one event, never a final state."""
    return {
        "record_id": record_id,
        "vital_kind": kind,
        "occurred_at": occurred_at,
        "fields": dict(fields),       # data-minimized (G6)
        "immutable": True,            # G5 — appended, never overwritten
    }


def register_birth(record_id: str, child: str, parents: list, place: str,
                   occurred_at: str, now: str) -> dict:
    """Validate + construct a birth registration (UN CRVS). Pure function.

    Requires a child, at least one parent, a place, and a non-future occurrence.
    Returns the immutable record + an unsigned birth certificate.
    """
    if not child:
        raise ValueError("birth: child is required")
    if not parents:
        raise ValueError("birth: at least one parent is required")
    if not place:
        raise ValueError("birth: place is required")
    if _iso(occurred_at) > _iso(now):
        raise ValueError("birth: occurrence cannot be in the future")
    rec = _record("birth", record_id,
                  {"child": child, "parents": list(parents), "place": place}, occurred_at)
    return {"record": rec, "certificate": _unsigned_certificate("birth", child, record_id)}


def register_death(record_id: str, decedent: str, place: str,
                   occurred_at: str, now: str, cause: str | None = None) -> dict:
    """Validate + construct a death registration (UN CRVS). Pure function."""
    if not decedent:
        raise ValueError("death: decedent is required")
    if not place:
        raise ValueError("death: place is required")
    if _iso(occurred_at) > _iso(now):
        raise ValueError("death: occurrence cannot be in the future")
    fields = {"decedent": decedent, "place": place}
    if cause:
        fields["cause"] = cause  # ICD-11 coded where present
    rec = _record("death", record_id, fields, occurred_at)
    return {"record": rec, "certificate": _unsigned_certificate("death", decedent, record_id)}


def register_marriage(record_id: str, partner_a: str, partner_b: str, place: str,
                      occurred_at: str, now: str, existing_marriages: tuple = ()) -> dict:
    """Validate + construct a marriage registration (UN CRVS). Pure function.

    Requires two DISTINCT partners, a place, a non-future occurrence, and that neither partner
    is already in an active marriage within `existing_marriages` (a tuple of frozensets/pairs).
    """
    if not partner_a or not partner_b:
        raise ValueError("marriage: two partners are required")
    if partner_a == partner_b:
        raise ValueError("marriage: partners must be distinct")
    if not place:
        raise ValueError("marriage: place is required")
    if _iso(occurred_at) > _iso(now):
        raise ValueError("marriage: occurrence cannot be in the future")
    already = {p for pair in existing_marriages for p in pair}
    if partner_a in already or partner_b in already:
        raise ValueError("marriage: a partner is already in an active marriage")
    rec = _record("marriage", record_id,
                  {"partners": sorted([partner_a, partner_b]), "place": place}, occurred_at)
    return {"record": rec, "certificate": _unsigned_certificate("marriage", record_id, record_id)}


def register_residency(record_id: str, person: str, new_address: str,
                       occurred_at: str, now: str, prior_address: str | None = None) -> dict:
    """Residence registration (転入届). Append-only — a move-in is a new datom, the prior
    address is retained in history (非終末論), never overwritten (G5)."""
    if not person:
        raise ValueError("residency: person is required")
    if not new_address:
        raise ValueError("residency: new_address is required")
    if _iso(occurred_at) > _iso(now):
        raise ValueError("residency: occurrence cannot be in the future")
    fields = {"person": person, "address": new_address}
    if prior_address:
        fields["prior_address"] = prior_address
    rec = _record("residency", record_id, fields, occurred_at)
    return {"record": rec, "certificate": _unsigned_certificate("residency", person, record_id)}


def append(history: list, result: dict) -> list:
    """G5: append a registration to a history, returning a NEW list (never mutate in place)."""
    return list(history) + [result["record"]]


def current_address(history: list, person: str) -> str | None:
    """Latest residency datom for a person = current address (max occurred_at). 非終末論."""
    fixes = [r for r in history if r["vital_kind"] == "residency" and r["fields"]["person"] == person]
    if not fixes:
        return None
    return max(fixes, key=lambda r: r["occurred_at"])["fields"]["address"]


def solve(*_args, **_kwargs):
    raise RuntimeError(
        "civil-registry R0: reference validation + record construction only. Live registration "
        "against a real civil register is Council+operator gated (principal A: Council Lv7+; "
        "principal B: adopting state)."
    )


if __name__ == "__main__":
    b = register_birth("birth-1", "child:aoi", ["parent:rin"], "東京都新宿区",
                       "2026-06-01T09:00:00Z", "2026-06-05T00:00:00Z")
    print("birth record:", b["record"]["record_id"], "cert signed?", b["certificate"]["proof"])
