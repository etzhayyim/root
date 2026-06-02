# himotoki (繙き) — CLAUDE actor guide

**Active disclosure-request filer.** Tier-B · `did:web:himotoki.etzhayyim.com` ·
ADR-2605302130 · **R0 scaffold (no cells run, no dispatch)**.

## What this actor IS

The **active-outbound** sibling of passive danjo/tadori. It files
disclosure requests and custodies the responses:

- **DSAR** (個人情報開示請求, APPI §33 / GDPR Art.15 / CCPA) to private
  controllers — **own data, consenting member only**.
- **FOIA** (行政文書開示請求, 行政機関情報公開法 / FOIA) to public organs.

Driven by a **coded target registry** (`disclosureTarget`) holding each
org's 窓口 / 住所 / email / portal / 手続き / fee / deadline. Seed at
`registry/targets.seed.json`.

```
target_registry ─┐
request_intake ──┤→ compose → dispatch → deadline_tracker → response_intake ─┐
                 │                                                            ├→ (PII) encrypted.* DID-bound envelope
                 └────────────────────────────────────── appeal_route ←──────┘  (FOIA non-PII) → danjo/ossekai
```

## Do NOT (constitutional invariants — ADR-2605302130 §4)

- **Do not** request a **third party's** personal data, or file without a
  consenting member's explicit consent + Adherent-SBT/DID binding (G3).
  DSAR is **own-data-only**.
- **Do not** use any pretext / sockpuppet / false identity / impersonation;
  every request identifies the **true requester** (G4, §2(c)).
- **Do not** render legal advice; templates + characterization + appeal
  strategy route to **chigiri + external counsel** (G5, UPL).
- **Do not** store disclosed PII anywhere except an
  `com.etzhayyim.encrypted.*` XChaCha20-Poly1305 **DID-bound envelope**
  (G6, ADR-2605181100). **Never** plaintext PII on MST.
- **Do not** mass-file, bulk-enumerate agencies, or flood requests (G8);
  **do not** resell disclosed data or run a paid pretext service (G9).
- **Do not** access systems without authorization or circumvent access
  controls / paywalls / rate limits — **lawful official channel only**
  (G10).
- **Do not** dispatch against a target whose `verificationStatus` is
  `unverified-seed` or whose `lastVerified` is stale (G14). Verify first.
- **Do not** publish disclosed PII or re-disclose it (N13); FOIA public
  records publish only via the §1.12 / 1-SBT-1-vote path (G11).
- **Do not** invent contact data. Registry entries cite `provenance` and
  must be human-verified before live use.

## Boundary with chigiri

chigiri = **what's the form and the law** (procedure templates, UPL
routing, appeal procedure, `data_privacy` cell). himotoki = **send it,
track it, take in the response, encrypt-store it.** himotoki depends on
chigiri; it does not duplicate chigiri's templating.

## Inference

Murakumo-only (G7, ADR-2605215000). No vendor LLM callout.
