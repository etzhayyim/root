"""analyze.py — 証明 (shomei) end-to-end identity-binding membrane (dry-run). ADR-2606072100.

Load the representative seed → for each member: issue challenge → mint a subject-signed
identityClaim per possession (ReferenceVerifier-simulated) → verify (policy + crypto) → aggregate
into a personhoodCredential + W3C VC. gov-* possessions hit the Council gate (GatedError) and are
reported as gated, never silently verified. Writes methods/out/identity-report.md +
methods/out/personhood-credentials.json.

Self-sovereign (G1), own-identity-only (G2), no-PII (G3), proof-mandatory (G4), no-server-key (G7),
identity-assurance-not-social-credit (G8). Stdlib only.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import pathlib

import aggregate as agg
from claims import build_claim, canonical_claim_bytes, external_subject_hash
from factors import FACTOR_CLASS
from revoke import active_verified_factors
from verify import GatedError, ReferenceVerifier, verify_claim

HERE = pathlib.Path(__file__).resolve().parent
SEED = HERE.parent / "data" / "seed-claims.json"
OUT = HERE / "out"


def _ref_token(secret: str, msg: bytes) -> str:
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def _mint(member: dict, p: dict, base_ts: int) -> tuple[dict, dict, dict, str]:
    """DRY-RUN mint of a subject-signed claim + its challenge + proof material (ReferenceVerifier).
    Returns (challenge, claim, proof_material, secret). In production the client signs this."""
    subject = member["subjectDid"]
    salt = member["salt"]
    nonce = "nonce-" + hashlib.blake2b(
        (subject + p["factorKind"] + p["identifier"]).encode(), digest_size=12
    ).hexdigest()
    challenge = {
        "subjectDid": subject,
        "factorKind": p["factorKind"],
        "nonce": nonce,
        "issuedAt": base_ts,
        "expiresAt": base_ts + 600,
    }
    esh = external_subject_hash(salt, p["identifier"])
    # Build an unsigned skeleton to compute the canonical signing bytes, then sign (reference).
    skeleton = {
        "subjectDid": subject,
        "factorKind": p["factorKind"],
        "factorClass": FACTOR_CLASS[p["factorKind"]],
        "proofKind": p["proofKind"],
        "challengeNonce": nonce,
        "externalSubjectHash": esh,
        "verified": True,
        "issuedAt": base_ts,
    }
    subject_sig = _ref_token(p["secret"], canonical_claim_bytes(skeleton))
    claim = build_claim(
        subject_did=subject,
        factor_kind=p["factorKind"],
        proof_kind=p["proofKind"],
        challenge_nonce=nonce,
        external_subject_hash=esh,
        issued_at=base_ts,
        subject_sig=subject_sig,
        verified=True,
        external_handle=p.get("handle"),
        encrypted_payload_cid=p.get("encryptedPayloadCid"),
    )
    proof_material = {"proof": _ref_token(p["secret"], (nonce + "|" + esh).encode())}
    return challenge, claim, proof_material, p["secret"]


def run(seed_path: pathlib.Path = SEED, out_dir: pathlib.Path = OUT) -> dict:
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    base_ts = int(seed.get("baseTs", 1781000000))
    results = []

    for member in seed["members"]:
        subject = member["subjectDid"]
        secrets = {(subject, p["factorKind"]): p["secret"] for p in member["possessions"]}
        verifier = ReferenceVerifier(secrets, allow_gated=False)
        verified_claims, gated, failed = [], [], []
        seen: set[str] = set()
        for p in member["possessions"]:
            challenge, claim, pm, _ = _mint(member, p, base_ts)
            try:
                res = verify_claim(
                    claim, challenge, verifier, proof_material=pm, now=base_ts + 10, seen_nonces=seen
                )
            except GatedError as e:
                gated.append({"factorKind": p["factorKind"], "reason": str(e).split(";")[0]})
                continue
            if res["verified"]:
                claim["cid"] = "claim:" + claim["challengeNonce"]
                verified_claims.append(claim)
            else:
                failed.append({"factorKind": p["factorKind"], "reason": res["reason"]})

        active = active_verified_factors(verified_claims, revocations=[])
        cred = agg.aggregate(subject, active, issued_at=base_ts)
        vc = agg.to_w3c_vc(subject, cred)
        results.append(
            {
                "subjectDid": subject,
                "credential": cred,
                "vc": vc,
                "verifiedCount": len(verified_claims),
                "gated": gated,
                "failed": failed,
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_report(out_dir / "identity-report.md", results)
    (out_dir / "personhood-credentials.json").write_text(
        json.dumps([r["vc"] for r in results], indent=2), encoding="utf-8"
    )
    return {"results": results}


def _write_report(path: pathlib.Path, results: list[dict]) -> None:
    L = [
        "# 証明 (shomei) — believer identity-binding report (dry-run)\n",
        "_Self-sovereign · own-identity-only · no-PII · proof-mandatory · no-server-key. "
        "Identity ASSURANCE, never a social-credit score (G8)._\n",
    ]
    for r in results:
        c = r["credential"]
        L.append(
            f"\n## `{r['subjectDid']}`\n"
            f"- **IAL {c['assuranceLevel']} ({agg.assurance_label(c['assuranceLevel'])})** · "
            f"proof-of-personhood={c['proofOfPersonhood']} · "
            f"factors={c['factorCount']} across {c['distinctClasses']} class(es)\n"
            f"- verified factors: {', '.join(c['verifiedFactors']) or '(none)'}\n"
            f"- issuer: `{c['issuer']}` · subjectDidHash: `{c['subjectDidHash'][:16]}…`"
        )
        if r["gated"]:
            L.append(
                "- gated (Council R0, ADR-2605260000): "
                + ", ".join(g["factorKind"] for g in r["gated"])
            )
        if r["failed"]:
            L.append("- failed: " + ", ".join(f"{f['factorKind']}({f['reason']})" for f in r["failed"]))
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    res = run()
    for r in res["results"]:
        c = r["credential"]
        print(
            f"{r['subjectDid']}: IAL {c['assuranceLevel']} ({agg.assurance_label(c['assuranceLevel'])}) "
            f"pop={c['proofOfPersonhood']} factors={c['factorCount']}/{c['distinctClasses']}cls "
            f"gated={len(r['gated'])} failed={len(r['failed'])}"
        )
    print(f"→ {OUT/'identity-report.md'}  +  {OUT/'personhood-credentials.json'}")
