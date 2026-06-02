# `com.etzhayyim.himotoki.*` — Disclosure-request Lexicons

Lexicon namespace for **himotoki** (繙き), the ACTIVE disclosure-request
Tier-B actor (ADR-2605302130). himotoki files data-subject access requests
(APPI §33 / GDPR Art.15 / CCPA) to private controllers on behalf of
**consenting members** for their **own** data, and freedom-of-information
requests (行政機関情報公開法 / FOIA) to public organs.

| Lexicon | Emitted by | Purpose |
|---|---|---|
| `disclosureTarget` | `himotoki_target_registry` | **The coded 窓口 / 住所 / メールアドレス / portal / 手続き / fee / deadline registry** — one record per organization × jurisdiction × regime. Open data. `verificationStatus` gates live dispatch (G14). |
| `disclosureRequest` | `himotoki_request_intake` | The request spec. DSAR = own-data-only + consent (G3); FOIA = citizen request. |
| `requestDispatch` | `himotoki_dispatch` | Transparent, identified dispatch log (G4); only against a G14-verified target. |
| `disclosureResponse` | `himotoki_response_intake` | Response metadata. PII payload referenced via an `com.etzhayyim.encrypted.*` DID-bound envelope ONLY (G6, ADR-2605181100); never inline. |
| `appealRecord` | `himotoki_appeal_route` | Lawful statutory appeal routing (審査請求 / DPA complaint / FOIA appeal) via chigiri (G5/G11). |

## Constitutional invariants (see ADR-2605302130 §4)

- **G3** consent-gated + identity-bound; DSAR is **own-data-only** (never a third party's PII).
- **G4** transparent + **non-pretextual** — true requester always identified.
- **G5** UPL-equivalent — files + tracks; legal advice routes to chigiri + external counsel.
- **G6** disclosed PII lives **only** in `com.etzhayyim.encrypted.*` DID-bound envelopes.
- **G8** rate-limited / non-vexatious (no mass-filing / agency-DoS).
- **G10** lawful-channel-only (no unauthorized access / no access-control circumvention).
- **G14** **dispatch only against a `maintainer-verified` / `council-verified` target** within the freshness window; `unverified-seed` entries enable routing design only.

Seed target registry: `/20-actors/himotoki/registry/targets.seed.json`.
