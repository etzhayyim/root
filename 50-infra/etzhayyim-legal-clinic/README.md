# etzhayyim-legal-clinic

Free legal-aid intake front-end for **etzhayyim.com** (ADR-2605302345 §D1). The
adherent-facing door to the clinic. **Substrate + orchestration only — renders
no legal advice (G14).**

## What it does

- `POST /xrpc/com.etzhayyim.chigiri.legalAid.intake` (member-signed) — opens a
  free matter (`intakeState=intake`) and relays it to the
  `chigiri_legal_aid_clinic` cell, which assigns Public-Fund counsel (G16).
- `GET /xrpc/com.etzhayyim.chigiri.legalAid.status?matter=…` — read-only status.

The endpoint accepts the adherent's OWN description and returns intake status —
**never an answer**. Advice comes only from the licensed lawyer the cell assigns.

## Constitutional posture

- **G14**: no advice produced here.
- **G15**: nothing charged — no payment path, no fee field; gratuitous.
- **no-server-key** (ADR-2605231525): the Worker holds no signing key. Intake
  writes are member-signed (passkey-derived ES256); the Worker relays them via
  `@etzhayyim/sdk`. Reads are anonymous (`// no-server-key: read-only`).
- **no-cookie / no-ads**: identity is DID-bound; no Set-Cookie, no trackers.
- **substrate-boundary**: substrate access via `@etzhayyim/sdk` only.

Lexicon: `com.etzhayyim.chigiri.legalAidMatter`. Cell:
`40-engine/kotoba/crates/kotoba-kotodama/cells/chigiri_legal_aid_clinic/`.
