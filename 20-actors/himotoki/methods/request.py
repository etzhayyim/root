#!/usr/bin/env python3
"""himotoki 繙き — DSAR/FOIA disclosure-request draft generator (R0/R1, offline).

ADR-2605302130. Turns a consenting member's own-data request against a coded
disclosureTarget into a ready-to-send request DRAFT — never a live dispatch. The active,
consent-bound counterpart to passive danjo/tadori.

Structural charter invariants (enforced here, three-places-each pattern):
  G3 — DSAR is OWN-DATA-ONLY: a DSAR draft REQUIRES the member's requester DID and an
       explicit ownDataOnly assertion; otherwise refused.
  G4 — TRUE requester, no pretext: every draft identifies the real requester DID; a
       pretext / sockpuppet / impersonation field is UNREPRESENTABLE (asserted).
  G6 — PII NEVER inline: the member's identifying details ride as an encrypted DID-bound
       envelope REFERENCE (com.etzhayyim.encrypted.*), never as plaintext in the draft.
  G8 — no mass-filing: a batch over more than MAX_BATCH targets is refused.
  G14 — verify-before-dispatch: dispatch is REFUSED against an unverified-seed / stale
       target. Draft generation is always allowed offline; live send needs a VERIFIED
       target + operator gate.
  G10 — outbound-gated: live dispatch needs HIMOTOKI_OPERATOR_GATE=1 + a verified target.

stdlib only. Usage:
    python3 request.py --target "Discord Inc.:ccpa-110" --member did:web:...:member:alice
                       [--out OUTDIR]
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent.parent
_REGISTRY = _HERE / "registry" / "targets.seed.json"

MAX_BATCH = 5                       # G8 — no mass-filing / agency flooding
DSAR_REGIME_PREFIXES = ("gdpr", "ccpa", "cpra", "appi", "lgpd", "pipeda", "pdpa", "pipl")
_FORBIDDEN_PRETEXT_FIELDS = ("pretext", "sockpuppet", "impersonat", "alias", "false-identity")


def load_registry(path: pathlib.Path = _REGISTRY) -> dict[str, dict]:
    """Return {targetId: target}. targetId = '<organization>:<regime>' (stable, human)."""
    d = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for t in d.get("targets", []):
        tid = f"{t.get('organization')}:{t.get('regime')}"
        out[tid] = t
    return out


def is_dsar(target: dict) -> bool:
    """DSAR (own-data) vs FOIA (public records), inferred from the regime."""
    regime = str(target.get("regime", "")).lower()
    if regime.startswith(DSAR_REGIME_PREFIXES):
        return True
    if "foia" in regime or "情報公開" in regime or regime.endswith("-foia"):
        return False
    # altRegimes fallback
    return any(str(r).lower().startswith(DSAR_REGIME_PREFIXES)
               for r in target.get("altRegimes", []))


def is_verified(target: dict) -> bool:
    return str(target.get("verificationStatus", "")) == "verified"


def build_request(target: dict, member: dict) -> dict:
    """Build a disclosure-request draft. RAISES on a charter violation (G3/G4/G6)."""
    requester = member.get("requesterDid") or ""
    if not requester:
        raise ValueError("G4: every request must identify the true requester DID (no pretext)")
    # G4 — no pretext/sockpuppet field may be supplied.
    for k in member:
        if any(b in k.lower() for b in _FORBIDDEN_PRETEXT_FIELDS):
            raise ValueError(f"G4: pretext field {k!r} is unrepresentable; the true requester must file")
    dsar = is_dsar(target)
    if dsar and not member.get("ownDataOnly") is True:
        raise ValueError("G3: a DSAR is own-data-only; member must assert ownDataOnly=true")
    # G6 — the member's PII must be an encrypted envelope ref, never plaintext in the draft.
    env = member.get("subjectEnvelopeRef") or ""
    if not env.startswith("com.etzhayyim.encrypted:"):
        raise ValueError("G6: member identity must be a com.etzhayyim.encrypted:* envelope ref, "
                         "never plaintext PII in the draft")
    for forbidden in ("name", "email", "address", "phone"):
        if forbidden in member and member[forbidden]:
            raise ValueError(f"G6: plaintext PII {forbidden!r} must not be in the request; use the envelope")

    return {
        "type": "himotoki.disclosureRequest",
        "kind": "DSAR" if dsar else "FOIA",
        "regime": target.get("regime"),
        "organization": target.get("organization"),
        "jurisdiction": target.get("jurisdiction"),
        "channelType": target.get("channelType"),
        "requesterDid": requester,                       # G4 — true requester
        "subjectEnvelopeRef": env,                       # G6 — encrypted, never plaintext
        "ownDataOnly": bool(dsar),                       # G3
        "statutoryDeadlineDays": target.get("statutoryDeadlineDays"),
        "targetVerified": is_verified(target),           # G14 input
        "dispatchReady": False,                          # never ready at R0 (G10/G14)
        "sourcing": ":representative",
    }


def can_dispatch(target: dict, operator_gate: bool) -> tuple[bool, str]:
    """G14 + G10: a draft may be transmitted ONLY against a verified target AND with the
    operator gate. Returns (allowed, reason-if-refused)."""
    if not is_verified(target):
        return False, ("G14: target is unverified-seed / stale; verify (and re-check within the "
                       "freshness window) before any dispatch")
    if not operator_gate:
        return False, "G10: live dispatch needs HIMOTOKI_OPERATOR_GATE=1 (Council + operator)"
    return True, ""


def build_batch(target_ids: list[str], member: dict, registry: dict[str, dict]) -> list[dict]:
    """Build drafts for several targets. RAISES (G8) if more than MAX_BATCH — no mass-filing."""
    if len(target_ids) > MAX_BATCH:
        raise ValueError(f"G8: no mass-filing — at most {MAX_BATCH} targets per batch, got {len(target_ids)}")
    return [build_request(registry[t], member) for t in target_ids]


def render_edn(drafts: list[dict]) -> str:
    L = [";; himotoki-request-drafts.kotoba.edn — disclosure-request DRAFTS (never dispatched).",
         ";; G3 own-data-only DSAR · G4 true-requester (no pretext) · G6 PII = encrypted",
         ";; envelope ref (never plaintext) · G14 dispatch refused vs unverified target ·",
         ";; G10 outbound-gated. DERIVED :representative. ADR-2605302130.", "", "["]
    for d in drafts:
        L.append(
            f' {{:himotoki.req/kind :{d["kind"]} :himotoki.req/regime "{d["regime"]}" '
            f':himotoki.req/organization "{d["organization"]}" '
            f':himotoki.req/requester-did "{d["requesterDid"]}" '
            f':himotoki.req/subject-envelope-ref "{d["subjectEnvelopeRef"]}" '
            f':himotoki.req/own-data-only {str(d["ownDataOnly"]).lower()} '
            f':himotoki.req/target-verified {str(d["targetVerified"]).lower()} '
            f':himotoki.req/dispatch-ready false :himotoki.req/sourcing :representative}}')
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    if "--target" not in argv or "--member" not in argv:
        sys.exit(__doc__)
    registry = load_registry()
    tid = argv[argv.index("--target") + 1]
    if tid not in registry:
        sys.exit(f"unknown target {tid!r}; e.g. one of: " + ", ".join(list(registry)[:3]))
    member = {
        "requesterDid": argv[argv.index("--member") + 1],
        "ownDataOnly": True,
        "subjectEnvelopeRef": "com.etzhayyim.encrypted:env:demo-subject",
    }
    target = registry[tid]
    draft = build_request(target, member)
    allowed, reason = can_dispatch(target, os.environ.get("HIMOTOKI_OPERATOR_GATE") == "1")
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "himotoki-request-drafts.kotoba.edn").write_text(render_edn([draft]))
    print(f"himotoki draft: {draft['kind']} to {draft['organization']} ({draft['regime']}, "
          f"{draft['jurisdiction']}); deadline {draft['statutoryDeadlineDays']}d")
    print(f"  dispatch: {'ALLOWED' if allowed else 'REFUSED — ' + reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
