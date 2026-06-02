# etzhayyim-legal-comms

Counsel-operated comms gateway (ADR-2605302345 §D2). Bridges fax / email /
e-filing for the legal-services platform. **Transport, not practitioner.**

## G18 — every legal act needs human licensed-counsel actuation

`sendLegalAct(artifact, counselActuation, transports)` transmits a legal-act
artifact (court filing, pleading, 内容証明, demand/representation letter) **only**
after verifying:

1. a `counselActuation` is present (else throws — no autonomous filing);
2. the actuating lawyer is licensed in the artifact's `destinationJurisdiction`;
3. the actuation carries the lawyer's OWN `counselDid` + `counselSignatureRef`.

etzhayyim holds **no signing key, seal or credential** for any legal act
(no-server-key, ADR-2605231525). The corp orchestrates; counsel acts. Lawyer-
absent filing is impossible by construction.

Non-legal-act transport (scheduling, adherent-authored document delivery) goes
through `transmitNonLegalAct` and needs no actuation.

## Endpoints

- `POST /xrpc/com.etzhayyim.legal.sendLegalAct` → 200 receipt, or **422
  CounselActuationRequired** if actuation is missing/mismatched (G18).
- `POST /xrpc/com.etzhayyim.legal.sendNonLegalAct` → scheduling/delivery.

Lexicon: `com.etzhayyim.legal.outboundLegalAct`. Lint gate:
`no-autonomous-legal-act.mjs` (G18).
