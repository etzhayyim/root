# Demo script + seeded tenant — open-salesforce

> Reverse-topo node 09 / 13. Back-solves 08 (pricing): the demo has to move past the flat-price calculator to prove residency + per-seat LLM + operability. Back-solves 05 / 01 too: qualification Q2 "what killed alternatives" + case-study claim "stage change → activity in 200ms" must both land live. 40 minutes wall-clock, 5-act structure. No slides in acts 2–5. Every act has a gate; miss a gate and we cut the next act, not the time per act.

## Who's on the call
- Prospect side: VP Sales / CRO (economic), RevOps (champion), optionally CISO / DPO (Security).
- Our side: AE drives narrative, SE drives the screen.

## Seeded tenant
Before the call:
- Spin up `did:web:democo.opensaas.etzhayyim.com` (SE does this once, re-used across demos; auto-rollback nightly via `migrate --rollback --older-than 24h`).
- Seed 6 accounts, 18 contacts, 4 leads, 12 opportunities (mix of stages), 6 cases, 30 activities. Company names are plausible JP mid-market fictitious entities ("Niigata Seiki K.K.", "Osaka Trade Partners Ltd.") so the prospect can imagine their own data.
- Pre-bind one seat DID `did:web:democo.opensaas.etzhayyim.com:seat:ae-01` to a passkey on the SE's laptop.
- Pre-warm `mv_opensaas_salesforce_pipeline_by_stage` so `listPipeline` is sub-100ms.
- Pre-draft one Murakumo summarisation prompt for act 4.

## Act 0 — Framing (3 min, slide is allowed here only)
- One slide: "3 things this demo will prove, 2 it won't."
- WILL: (a) Salesforce-equivalent UX on a DID-native stack, (b) residency + PII topology, (c) per-seat LLM in the workflow.
- WON'T: (a) not a full UX parity (open-salesforce has no Apex / Flow / Lightning App Builder), (b) not a one-click Salesforce import — that's the reconciliation-gated migration weekend (SOW §C).
- Ask: "What's the 1 outcome that would make this 40 minutes worthwhile for you?" — steer act ordering by the answer.

## Act 1 — "Tenant = DID" (5 min)

Goal: prove multi-tenant is a primitive, not a row filter.

Steps:
1. Open `https://salesforce.opensaas.etzhayyim.com/` in a fresh incognito. Login → WebAuthn passkey prompt → seat DID activates.
2. In a second browser, open `https://democo.opensaas.etzhayyim.com/` (same code, different tenant DID routing). Show the `did.json` at `/.well-known/did/web/democo.opensaas.etzhayyim.com` — explain this is the tenant's identity doc, signed by a key the tenant could in principle custody themselves.
3. Terminal side-by-side: `curl https://salesforce.opensaas.etzhayyim.com/_app/meta | jq .tenant` vs the democo one. Different tenant DID, identical Worker build.

Gate: "If we spun up `<prospect>.opensaas.etzhayyim.com` right now, you'd see your own subdomain resolve within 3 minutes and zero cross-tenant data leakage is the default, not a setting." → wait for nod.

## Act 2 — Pipeline + convertLead (8 min)

Goal: prove Salesforce-equivalent happy-path UX; land the "atomic convert" claim from node 01 / 06.

Steps:
1. Open the pipeline view → it renders from `listPipeline({tenantDid: "did:web:democo.opensaas.etzhayyim.com"})`. Hover a stage bucket → shows `stageRollup[stage].weightedAmountJpy`. Note: this is a streaming MV; latency <100ms.
2. Click into the lead list → pick "Osaka Trade Partners Ltd." (status=qualifying). Trigger the "Convert" action. In the right-hand drawer, show the `convertLead` XRPC call's payload (SE has the devtools open).
3. One click → server-side: three `createRecord`s (account, contact, opportunity) + one `lead` update + one derived `activity`(kind=conversion) land in a single commit pipeline pass.
4. Click the new Activity row → "View source commit" opens `/at/democo.opensaas.etzhayyim.com/com.etzhayyim.apps.opensaas.salesforce.activity/<rkey>`. Show the AT URI in the browser; copy-paste it to a curl in the terminal to show anyone-who-has-the-URI can verify the record (federation-grade).

Gate: "3 records atomically, 1 activity auto-derived, 1 URI that's verifiable outside the CRM — is that the 'kill Apex Flow' story your team was asking about?"

## Act 3 — Residency + Art-17 (8 min, CISO / DPO in the room)

Goal: prove the APPI / GDPR posture is runnable, not paperwork.

Steps:
1. Terminal: `etzhayyim opensaas attest --tenant did:web:democo.opensaas.etzhayyim.com --region JPN` → signed JSON lists: CF colo IDs, RisingWave replica region, vault KMS region. All JPN.
2. In the UI, pick a seeded contact "Akiko Tanaka". Show the record: Tier-1 has `emailHash: sha256:...`, `phoneHash: sha256:...`, `displayLabel: "CTO, Niigata Seiki"`. No raw email.
3. Open the Tier-3 vault panel (operator-only). Show the wrapped `rawEmail` blob linked to the contact's DID. Explain: wrapped with the seat's device key (WebAuthn PRF), server can't decrypt.
4. Fire the purge: `POST /api/vault/purge { subjectHash: "sha256:..." }`. Watch: Tier-3 vault row deleted, Tier-1 `emailHash` rotated to `sha256:deleted-<uuid>`, an `activity(kind=note, source=manual-ui)` drops into the contact's history with the purge attestation.
5. Terminal: `curl https://atproto.etzhayyim.com/xrpc/com.atproto.repo.getRecord?uri=at://...` on the activity → shows the attestation is content-addressed, immutable.

Gate: "Can your DPO run this exact sequence against a test subject in week 1 of the POC and sign off by week 3?"

## Act 4 — Per-seat Murakumo (7 min)

Goal: prove LLM isn't a platform add-on; it's a seat capability.

Steps:
1. Open an opportunity ("Niigata Seiki FY26 Q3 Expansion"). Click the "Summarise" button in the opportunity toolbar.
2. DevTools: show the XRPC call goes to a handler that invokes `kotodama.Invoke(murakumoFleetDid, "summariseOpportunity", { uri, windowDays: 90 })`. The caller identity in the invoke is the seat DID `did:web:democo.opensaas.etzhayyim.com:seat:ae-01`, not a shared API key.
3. LLM returns a 4-paragraph summary pulled from `opportunity` + its linked `activity` + the account's 3 most recent `case` records.
4. Toggle: switch `ConfigPut fleet=did:web:murakumo.etzhayyim.com:fleet:m4`. Rerun. Different model, same call. Show the audit log entry: `activity(kind=note, source=derived-convo)` with `actorDid=<seat>`, `convoUri=<murakumo-invocation>`.
5. Pointer to Pillar 2 URL for the deeper read.

Gate: "If your own LLM plan is `<named vendor>`, swapping Murakumo for it is a `ConfigPut`, not a vendor meeting. Does that kill the Einstein GPT line item?"

## Act 5 — "Something went wrong" + recovery (5 min)

Goal: justify the hyper-care line item; prove operability under stress.

Steps:
1. Simulate a stale passkey: revoke seat `ae-01`'s passkey via `etzhayyim vault revoke-credential`. SE reloads the CRM → access denied, with a human-readable error pointing to the re-issue flow.
2. Operator re-issues: `POST /api/seats/ae-01/passkey/re-issue` from a second operator seat (demonstrates RBAC). New enrollment link emitted. SE walks through the re-enrollment (skip actual re-auth for time — show the email content).
3. Show the audit trail in the operator console: the revoke + re-issue are two `com.etzhayyim.audit.*` events, cross-referenceable to the seat DID's `activity` history.
4. Mention the 30-day / 90-day hyper-care SKU (pricing node 08); this is the kind of operational sequence covered.

Gate: "Would your ops team prefer a ticket-based recovery or this self-serve one? Does the 30-day hyper-care match how you'd ramp internal ownership?"

## Act 6 — Next step (4 min)

- Recap the 3 things we proved (actual, not hand-wave).
- Present the POC Agreement (node 04) on screen. Name the Security reviewer right now if CISO is on the call.
- Send the qualification sheet (node 05) as a shared doc within 10 minutes of call end.
- Book the POC kickoff within 14 days (calendar link live in the meeting chat).

## LLM-assisted demo prep (SE runbook)

- 30 min before the call, Murakumo generates:
  - A 5-bullet "what this prospect will likely push back on" from the CRM's own `activity` records of the AE's past discoveries with similar prospects.
  - A pre-filled pipeline with company names matching the prospect's industry (fintech / logistics / manufacturing).
  - Three candidate opener lines for act 0 based on the prospect's fiscal year-end and public AI press.
- During the call, a side panel runs an `activity(kind=note, source=derived-convo)` stream: every time the AE asks a question that the qualification sheet cares about, Murakumo writes a note so the AE doesn't lose it.

## What this demo forces the landing page (10) to deliver

- The top fold must reference the **one-click convert + auto-derived activity** flow (act 2), not "a CRM built on open protocols".
- There must be a **"see a real AT record" link** above the fold — prospects must be one click from verifying that the demo wasn't a mockup.
- The residency + Art-17 posture needs a **visible "download posture packet" CTA** on the top fold too, because Security is often the first visitor from a forwarded link.
- The "per-seat LLM" section needs to anchor on **seat DID = agent DID**, because that's what distinguishes us from "we use OpenAI" competitors.
- A public demo-tenant URL (`https://democo.opensaas.etzhayyim.com/`) with safe-for-sharing seed data lets prospects self-serve act 1 + act 2 before even booking a call.
