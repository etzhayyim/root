---
id: adr-2605302130-himotoki-disclosure-request-tier-b-actor-r0
title: "ADR-2605302130: 繙き (himotoki) — kotoba-native ACTIVE disclosure-request Tier-B actor that files consent-bound data-subject access requests (APPI/GDPR/CCPA) to private controllers + freedom-of-information requests (情報公開法) to public organs, with a coded target-registry of each organization's 窓口 / address / email / portal / procedure (R0 scaffold)"
status: proposed
doc_type: adr
topic: himotoki-disclosure-request-actor
authoritative: true
last_verified: 2026-05-30
priority: 8.0
axis: actor-architecture
weight: 0.80
priority_note: "Names a new Tier-B actor (himotoki) as the ACTIVE (outbound) counterpart to the passive-only oversight/ingest actors. Where danjo (ADR-2605301600) only reads pre-published open data and tadori (ADR-2605301400) only reads the chain, himotoki EXERCISES A RIGHT OF ACCESS: it files (a) data-subject access / 個人情報開示請求 (APPI §33 / GDPR Art.15 / CCPA) to private controllers (Discord / Google / LINE / Meta / Amazon …) on behalf of CONSENTING members, and (b) freedom-of-information / 行政文書開示請求 (情報公開法) to public organs. It carries a CODED target-registry (`disclosureTarget`) of each organization's 窓口 / postal address / contact email / web portal / required form / fee / statutory deadline so the actor can route + file procedurally. Bounded as: consent-gated + identity-bound (G3), transparent + non-pretextual (G4), UPL-equivalent (G5), PII lands ONLY in encrypted DID-bound envelopes (G6, ADR-2605181100), rate-limited / non-vexatious (G8), dispatch ONLY against a human/Council-verified target entry (G14), Murakumo-only (G7), Transparent-Religious-Force-disciplined (G11, ADR-2605192100 §1.12)."
authoritative_for:
  - new Tier-B actor `himotoki` (active disclosure-request filer + response custodian)
  - `com.etzhayyim.himotoki.*` Lexicon namespace (disclosureTarget / disclosureRequest / requestDispatch / disclosureResponse / appealRecord)
  - the coded disclosure-target registry schema (per-organization 窓口 / address / email / portal / form / fee / statutory-deadline / legal-regime) and its verification gate
  - the boundary between chigiri (procedure templates + legal characterization + UPL routing) and himotoki (the ACTIVE filer + tracker + encrypted response custodian)
  - the boundary between himotoki (active right-of-access requests) and danjo/tadori (passive-only reading)
  - how disclosed personal data enters the substrate: `com.etzhayyim.encrypted.*` DID-bound envelopes ONLY (never plaintext PII on MST)
depends_on:
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605181100-etzhayyim-confidentiality-encrypted-records
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605301400-tadori-onchain-tracing-actor-and-kotoba-eavt-migration
  - adr-2605263900-public-data-open-government-ipfs-ingestion
  - adr-2605263800-public-data-corporate-disclosure-ipfs-ingestion
  - adr-2605291100-manimani-kotoba-native-personal-knowledge-router
  - adr-2605264000-ossekai-info-arbitrage-actor
supersedes: []
superseded_by: []
notes: |
  Session 2026-05-30: user asked whether an actor exists that performs 情報開示請求
  ("情報開示請求を行う actor は設計されている?"), clarifying the targets as
  "discord, google, line, meta, amazon, 国家、行政組織 など", and then adding
  "公開企業の窓口、住所、連絡先、メールアドレス、手続きなどをすべて コードに,
  actor が手続きできるように" (encode every organization's contact-window / address /
  contact / email / procedure in code so the actor can file procedurally).

  Audit established: NO active disclosure-request actor existed. The only adjacent
  thing was chigiri's `data_privacy` cell (ADR-2605262700) — but that is a PROCEDURE
  TEMPLATING substrate (renders the form, routes DSAR), UPL-bound, and at R3 maturity
  (essentially deferred); it does not FILE, TRACK, or CUSTODY responses. All other
  data actors (danjo / tadori / gov+corp sensors) are constitutionally passive-only.

  himotoki is therefore the new ACTIVE-outbound actor. The name 繙き (himotoki —
  to unbind and peruse a scroll; to consult records as of right) is chosen to frame
  the actor as the exercise of a *right to read* records one is entitled to (one's
  OWN personal data; public administrative documents), NOT surveillance of others.
  Active-outbound is a deliberate, narrowly-gated EXCEPTION to the passive-only norm,
  justified because the actor only ever (a) requests the requester's OWN data with
  explicit consent, or (b) requests PUBLIC records the law entitles any citizen to —
  it never requests third parties' personal data, never uses pretext, never accesses
  systems without authorization.

  NAME IS PROVISIONAL — `himotoki` (繙き) chosen by the author; alternatives considered
  were ひらき (開き, etymological tie to 開示) and もとめ (求め). Council may rename at
  ratification without re-opening the design.
---

# Context

A 2026-05-30 audit answered the question *"is there an actor that performs
情報開示請求 (information-disclosure requests)?"* The honest answer was **no
active one**:

1. **Every existing data actor is passive-only.** danjo (ADR-2605301600)
   reads pre-published open-government data; tadori (ADR-2605301400) reads
   the chain; the `gov.*` / `corp.*` sensors (ADR-2605263900 / 2605263800)
   ingest pre-published bulk archives. None of them *asks anyone for
   anything* — passive-only is their constitutional bound (§2(c)
   covert-ops avoidance).

2. **The only adjacent design was chigiri's `data_privacy` cell**
   (ADR-2605262700): it routes a DSAR (GDPR / CCPA / APPI / LGPD) to a
   **procedure template** and is **UPL-bound** (renders the form, never
   legal advice). It is at **R3** maturity (post-R2 + Council Lv7+
   unanimity) — essentially deferred. Critically, chigiri **templates**
   the request; it does not **file** it, **track** the statutory deadline,
   **receive** the response, or **custody** the returned personal data.

3. **The user wants the active filer, with a coded target registry.**
   The clarified requirement is an actor that files 情報開示請求 to:
   - **private controllers** — Discord, Google, LINE, Meta, Amazon, … —
     i.e. a **data-subject access request** (個人情報開示請求): APPI §33
     開示等の請求 (JP) / GDPR Art.15 right of access (EU) / CCPA §1798.110
     right to know (US-CA), on behalf of a **consenting member** for that
     member's **own** personal data; and
   - **public organs** (国家・行政組織) — i.e. a **freedom-of-information
     request** (行政文書開示請求): 行政機関情報公開法 (JP) / FOIA (US) /
     EU Reg.1049/2001, for **administrative documents** any citizen is
     entitled to.
   And — explicitly — the actor must **carry in code** each organization's
   **窓口 (contact window) / 住所 (postal address) / 連絡先 (contact) /
   メールアドレス (email) / 手続き (procedure)** so it can **route and file
   procedurally** rather than ask a human to look each one up.

# Decision

Create **`himotoki`** (繙き), DID `did:web:himotoki.etzhayyim.com`, namespace
`com.etzhayyim.himotoki.*`, as a **Tier-B kotoba-native ACTIVE
disclosure-request actor** in **R0 scaffold**. JP-first at R0 (APPI §33 +
行政機関情報公開法), jurisdiction-generic in architecture (GDPR Art.15 /
CCPA / FOIA / Reg.1049/2001 are added as `disclosureTarget` regime values).

himotoki is the **active-outbound** sibling of the passive danjo/tadori:
it does not merely *read* records — it **exercises a right of access** to
*obtain* them, then lands them into the substrate. Active-outbound is a
narrowly-gated **exception** to the passive-only norm, permitted ONLY under
the gates in §4.

## §1 — Scope

himotoki is a **disclosure-request filing + tracking + response-custody
substrate**. It:

1. **Carries a coded target registry** (`disclosureTarget`) — one open
   record per organization × jurisdiction × regime, holding that
   organization's **窓口 / postal address / contact email / web-portal URL /
   required form reference / fee / statutory-deadline-days / language /
   accepted channels**. Seed entries (Discord / Google / LINE / Meta /
   Amazon / JP 行政機関 template) ship at R0 in
   `20-actors/himotoki/registry/targets.seed.json`, each flagged
   `verificationStatus: "unverified-seed"`.
2. **Intakes a member's request** with explicit consent + DID/Adherent-SBT
   binding (for DSAR — own data only), or as a citizen FOIA request (public
   records), producing a `disclosureRequest`.
3. **Composes** the request artifact by pulling the jurisdiction+target
   procedure template from **chigiri** (UPL boundary, G5) and filling it
   against the resolved `disclosureTarget`.
4. **Dispatches** the request through the target's declared channel —
   transparently, with the true requester identified, never by pretext —
   logging a `requestDispatch`. Dispatch is permitted ONLY against a
   **verified** target entry (G14).
5. **Tracks** the statutory deadline + follow-ups + non-response, and
   **routes appeals** (審査請求 / DPA complaint / FOIA appeal) through
   chigiri, recording an `appealRecord`.
6. **Custodies the response**: it records `disclosureResponse` metadata on
   MST, but the **disclosed personal data itself lands ONLY in an
   `com.etzhayyim.encrypted.*` XChaCha20-Poly1305 envelope, DID-bound to
   the requesting member** (ADR-2605181100). Never plaintext PII on MST.
   Public-record FOIA responses (non-PII) may additionally feed danjo /
   ossekai.

## §2 — The coded target registry (the user's explicit requirement)

The registry is the heart of "actor が手続きできるように". Each
`disclosureTarget` record is **open data** (CC0/CC-BY where derived from
the controller's own published privacy/FOIA page) and carries:

| Field | Purpose |
|---|---|
| `organization` / `did?` / `lei?` | who the request goes to |
| `jurisdiction` (`jpn`/`eu`/`usa`/…) + `regime` (`appi-33`/`gdpr-15`/`ccpa-110`/`foia-jp-gyousei`/`foia-us`/`eu-1049`) | which legal right is being exercised |
| `channelType` (`web-portal`/`email`/`postal`/`in-form`) + `portalUrl` / `contactEmail` / `postalAddress` | HOW to file — the 窓口 / 住所 / メールアドレス |
| `formRef` (chigiri template id) + `feeJpy?` + `statutoryDeadlineDays` + `language` | the 手続き (procedure), fee, and deadline clock |
| `provenance` (source URL the entry was derived from) + `lastVerified` + `verificationStatus` (`unverified-seed` / `maintainer-verified` / `council-verified`) | honesty gate (G14) |

**Honesty gate (G14):** seed entries are best-effort and ship as
`unverified-seed`. **No live dispatch may occur against an entry that is
not at least `maintainer-verified` within the freshness window.** This
prevents the actor from auto-emailing a stale or wrong address. R0 ships
the schema + seeds; verification + live dispatch are R1+/R2+ gated.

R0 seed targets (all `unverified-seed`, JP-relevant channels noted):

- **Discord** — DSAR (GDPR-15 / CCPA-110 / APPI-33); web data-request form +
  `privacy@discord.com` (per Discord Privacy Policy).
- **Google / Alphabet** — DSAR; Google Account data-export (Takeout) +
  privacy/help request flow.
- **LINE (LY Corp.)** — DSAR (APPI-33 primary); LINE privacy data-subject
  request form.
- **Meta (Facebook/Instagram/WhatsApp)** — DSAR; Privacy Center "Download
  Your Information" + DSAR form.
- **Amazon (incl. amazon.co.jp)** — DSAR; "Request My Data" page + regional
  privacy contact.
- **JP 行政機関 template** — 行政文書開示請求 (行政機関情報公開法); 各省庁
  情報公開窓口 + 開示請求書 (手数料 300 円/件 目安, 30 日以内 決定 目安).

> Specific addresses/emails/fees in the seed are provisional and MUST be
> human-verified before any dispatch (G14). The schema + the *mechanism* of
> coded routing is what R0 establishes; the verified contents are a living,
> Council/maintainer-curated dataset.

## §3 — Architecture (7 Pregel cells, R0 path-reserved)

All cells path-reserved at R0 under `40-engine/kotoba/crates/kotoba-kotodama/cells/himotoki_*/`;
each is import-time `RuntimeError("himotoki R0 scaffold: activate via
Council ADR + R1 ratification")` at W1 creation.

| Cell | Node | Phase | I/O |
|---|---|---|---|
| `himotoki_target_registry` | reuben | continuous | maintain + resolve `disclosureTarget` entries (the coded 窓口/住所/email/手続き catalog); enforce G14 verification status |
| `himotoki_request_intake` | reuben | event | member consent + DID/SBT binding + scope spec → `disclosureRequest` (DSAR = own-data-only; FOIA = citizen request) |
| `himotoki_compose` | gad | event | pull chigiri procedure template + resolved target → filled request artifact (UPL boundary G5) |
| `himotoki_dispatch` | gad | event | **the ONLY active-outbound cell** — transparent, identified transmission via the target's declared channel → `requestDispatch` (gated on G14 verified target) |
| `himotoki_deadline_tracker` | gad | continuous | statutory-deadline clock + follow-up + non-response escalation |
| `himotoki_response_intake` | naphtali | event | disclosed records → `disclosureResponse` metadata + **encrypted DID-bound PII envelope** (ADR-2605181100); public FOIA → optional danjo/ossekai feed |
| `himotoki_appeal_route` | naphtali | event | non/partial disclosure → appeal procedure via chigiri (審査請求 / DPA complaint / FOIA appeal) → `appealRecord` |

Cross-reference + request-lifecycle datoms live in kotoba QuadStore (EAVT)
per ADR-2605262130. No Kotoba/Datomic, no projection layer.

## §4 — Constitutional gates (G1–G14, IMMUTABLE R0–R3)

Council Lv6+ supermajority + new ADR to amend.

- **G1** Charter Rider §2(a)–(h) scan on every authored artifact + dispatch.
- **G2** kotoba attestation lineage on every record.
- **G3** **Consent-gated + identity-bound.** A DSAR is filed ONLY when
  member-initiated with **explicit consent + Adherent-SBT/DID binding**,
  and ONLY for **that member's OWN personal data**. himotoki MUST NOT
  request a third party's personal data, and MUST NOT file on behalf of a
  non-consenting person. (FOIA/public-record requests need no data-subject
  but are purpose-logged and attributed to the true requester.)
- **G4** **Transparent + non-pretextual** (§2(c) covert-ops avoidance).
  Every request **identifies the true requester**; NO sockpuppet, NO
  pretext, NO false identity, NO social-engineering, NO impersonation.
  Honest, attributable filing only.
- **G5** **UPL-equivalent** (chigiri G14 / toritate G5). himotoki files +
  tracks + custodies; it does NOT render legal advice on whether to
  litigate or on the legal sufficiency of a response. Procedure templates +
  legal characterization + appeal strategy route to external counsel via
  **chigiri + Public Fund** (Council Lv6+).
- **G6** **PII confidentiality mandatory.** Disclosed personal data lands
  ONLY in `com.etzhayyim.encrypted.*` (XChaCha20-Poly1305 envelope,
  Signal-wrapped per-recipient keys, **DID-bound to the requesting
  member**, ADR-2605181100). **NEVER plaintext PII on MST.** The member
  holds the decryption capability; himotoki is a custodian, not a reader.
- **G7** Murakumo-only inference (ADR-2605215000). No vendor LLM callout.
- **G8** **Rate-limited / non-vexatious.** Purpose-bound; one legitimate
  request per genuine need. NO automated mass-filing, NO bulk enumeration
  of controllers/agencies, NO request-flooding. Per-target + per-member
  rate caps; volume above threshold is Council-reviewed. (Anti-DoS /
  anti-administrative-burden — the actor exercises a right, it does not
  weaponize it.)
- **G9** **No data-broker / no pretext-as-a-service.** himotoki MUST NOT
  resell or commercialize disclosed data, and MUST NOT act as a paid
  disclosure-mill / pretext service for third parties. Non-profit +
  member-benefit only (Charter §1, Charter Rider §2(e)).
- **G10** **Lawful-channel-only.** himotoki's only mutation of external
  state is transmitting a **lawful** request through an **official,
  published** channel. It NEVER alters a controller's/agency's records,
  NEVER accesses systems without authorization, NEVER circumvents access
  controls, paywalls, or rate limits, NEVER scrapes around an access
  control. (Distinct from N6.)
- **G11** **Transparent Religious Force discipline** (§1.12). Request +
  tracking + intake ONLY; NO coercion, NO extra-legal pressure; appeals go
  through lawful statutory channels (審査請求 / DPA complaint / FOIA
  appeal). 1 SBT = 1 vote governs any aggregate publication of FOIA-obtained
  public records.
- **G12** **Scope-minimization / data-minimization.** Request only what is
  needed for the stated purpose; no fishing expeditions; honor the
  narrowest sufficient scope.
- **G13** **stateAlignedFlag pass-through** — CN-class / state-aligned
  targets carry `stateAlignedFlag=true` into derived records.
- **G14** **Verified-target-only dispatch.** `himotoki_dispatch` MUST
  refuse any target whose `disclosureTarget.verificationStatus` is
  `unverified-seed` or whose `lastVerified` is outside the freshness
  window. Seeds enable routing design; only human/Council-verified entries
  enable live filing.

## §5 — Non-goals (N1–N13, EXCLUDED R0–R3)

- **N1** NOT a law firm / litigation arm (UPL; no court filing, no legal
  advice — that routes to chigiri + external counsel).
- **N2** NOT a private-investigator / people-search — CANNOT request OTHER
  people's personal data (G3).
- **N3** NOT a surveillance / dossier-building system.
- **N4** NOT a data-broker / reseller of disclosed data (G9).
- **N5** NOT a pretext / social-engineering / impersonation tool (G4).
- **N6** NOT an unauthorized-access / hacking / access-control-circumvention
  / scrape-around tool (G10).
- **N7** NOT a mass-filing / request-flooding / agency-DoS tool (G8).
- **N8** NOT a state-granted legal personality (Preamble §0.4 Lv7+ lock).
- **N9** NOT a closed-source / secret-method engine (registry + method are
  open).
- **N10** NOT a replacement for the member's own direct right — himotoki
  *assists*; the member may always file directly.
- **N11** NOT a plaintext-PII store (G6).
- **N12** NOT Japan-exclusive in architecture (JP-first at R0;
  jurisdiction-generic via `disclosureTarget.regime`).
- **N13** NOT a re-disclosure / leak channel — disclosed PII is for the
  requesting member only; it is never published, and public-record FOIA
  output is published only via the §1.12 / 1-SBT-1-vote path (G11).

## §6 — Cross-actor boundaries

| Actor / substrate | Direction | Purpose |
|---|---|---|
| **chigiri** (ADR-2605262700) | → | **Boundary**: chigiri = procedure TEMPLATES + legal characterization + UPL routing + appeal procedure (`data_privacy` cell); himotoki = the ACTIVE filer + deadline tracker + encrypted response custodian. himotoki pulls templates from chigiri; chigiri renders no dispatch. |
| `com.etzhayyim.encrypted.*` (ADR-2605181100) | → (write) | Disclosed PII lands here ONLY (DID-bound envelope); G6. |
| **manimani** (ADR-2605291100) | → | A member's own disclosed data (decrypted by the member) may be ingested into that member's personal knowledge graph, with member consent. |
| **danjo** (ADR-2605301600) | → | FOIA-obtained PUBLIC administrative documents (non-PII) may feed danjo's open-government cross-reference corpus. PII NEVER flows to danjo. |
| **ossekai** (ADR-2605264000) | → | Aggregate publication of FOIA-obtained public records (non-PII) via the §1.12 path. |
| `corp.{leiReference,ownershipEdge}` (ADR-2605263800) | → (read) | Resolve a controller's canonical identity for the target registry. |
| **kotoba** (ADR-2605262130) | ↔ | Request-lifecycle + registry datoms (EAVT); kotoba-kqe for hot-path queries. |
| **tadori** / **danjo** | ∥ | Sibling investigation actors. himotoki = ACTIVE right-of-access (outbound); they = PASSIVE reading. Shared EAVT pattern, disjoint posture. |

## §7 — Roadmap

| Phase | Timeline | Scope | Fleet | Gate |
|---|---|---|---|---|
| **R0** | 2026-05-30 | Scaffold (this commit): 7 cells path-reserved + 5 Lexicon skeletons + target-registry seed (6 entries, all `unverified-seed`) + manifest + README + CLAUDE.md. NO dispatch. | none | ADR-2605302130 (PROPOSED) |
| **R1** | post-Bootstrap-Council + ≥1 Council Lv6+ ratify | `himotoki_target_registry` live + maintainer-verification flow (G14); `himotoki_request_intake` + `himotoki_compose` build `disclosureRequest` artifacts from chigiri templates. **NO live dispatch yet** (artifacts only). | reuben | Council Lv6+ ≥3 |
| **R2** | post-R1 + 30-day public comment | **FOIA-only live dispatch** (public-record requests to public organs; non-PII) + `himotoki_deadline_tracker` + `himotoki_response_intake` for public records; `disclosureTarget` entries `maintainer-verified`. | reuben + gad | Council Lv6+ ≥4 + 30-day public comment |
| **R3** | post-R2 + Council Lv7+ unanimity | **DSAR live dispatch** (member-consent + DID-bound; private controllers) + encrypted PII response custody (ADR-2605181100) + `himotoki_appeal_route`; named-controller targets `council-verified`; multi-jurisdiction (GDPR/CCPA/FOIA). | naphtali (full fleet) | Council Lv7+ unanimity |

# Consequences

**Positive.**

- Closes the audit gap with a single, named, constitutionally-bounded
  ACTIVE actor — the outbound counterpart the passive danjo/tadori
  deliberately are not.
- Directly satisfies the user's "encode every organization's 窓口 / 住所 /
  email / 手続き in code" requirement via the open `disclosureTarget`
  registry, while the G14 verification gate keeps the actor honest about
  stale/seed data.
- Member-empowering and mission-aligned: exercising one's right of access
  (own data) and the citizen's FOIA right is structural-labor-liberation
  infrastructure (Charter §1), not surveillance.
- kotoba-native by construction; PII handled correctly by construction
  (G6 → ADR-2605181100 encrypted envelopes), so the actor cannot become a
  plaintext-PII honeypot.

**Costs / risks.**

- **Active-outbound is the dominant risk.** It breaks the passive-only
  norm; the gates (G3 consent/own-data, G4 non-pretext, G8 rate-limit, G10
  lawful-channel, G14 verified-target) are the hard wall. Any drift toward
  third-party data, pretext, mass-filing, or unauthorized access is a
  constitutional violation requiring a separate ADR (and would likely fail
  §2(c)).
- **Stale registry data** could mis-route a request — mitigated by G14
  (no dispatch against unverified/expired entries) and the open,
  maintainer-curated registry.
- **PII custody liability** — mitigated by G6 (encrypted, DID-bound, member
  holds the key; himotoki is custodian not reader).
- **Vexatious-request perception** toward agencies — mitigated by G8 +
  G12 scope-minimization; the actor exercises a right, not a flood.

**Neutral.**

- R0 is scaffold-only: no cells run, no dispatch, no inference until
  Council ratification. Even R1 produces artifacts only; live dispatch is
  R2 (FOIA) / R3 (DSAR).

# Alternatives Considered

1. **Fold into chigiri's `data_privacy` cell.** Rejected: chigiri is
   constitutionally a procedure-templating + UPL-routing substrate that
   files nothing and custodies nothing. The ACTIVE filer + deadline tracker
   + encrypted-response custodian is a materially different posture
   (outbound + PII custody) that deserves its own actor + gates. himotoki
   *depends on* chigiri for templates (§6).
2. **Make himotoki passive-only like danjo.** Rejected — fatal to the
   requirement: a passive actor cannot file a request. The whole point is
   the outbound exercise of a right of access. The compromise is narrow
   gating (G3/G4/G8/G10/G14), not passivity.
3. **No coded registry; ask a human to supply each contact.** Rejected:
   the user explicitly asked for the contacts/procedures to be *in code so
   the actor can file procedurally*. The compromise for accuracy is G14
   (verification gate), not omission of the registry.
4. **Store disclosed PII as normal MST records.** Rejected — fatal:
   violates ADR-2605181100 confidentiality invariant. G6 mandates encrypted
   DID-bound envelopes.
5. **Allow third-party / pretext requests for investigative reach.**
   Rejected — fatal: violates §2(c) + APPI/GDPR (DSAR is own-data-only) and
   would make the actor a surveillance/PI tool (N2/N3/N5). G3/G4 are
   constitutional.

# References

- `/90-docs/adr/2605262700-chigiri-legal-procedure-tier-b-actor-r0.md` — chigiri (procedure templates + UPL; `data_privacy` DSAR routing)
- `/90-docs/adr/2605181100-etzhayyim-confidentiality-encrypted-records.md` — `com.etzhayyim.encrypted.*` envelope (PII custody, G6)
- `/90-docs/adr/2605262130-kotoba-storage-substrate-unification.md` — kotoba substrate (EAVT, no Kotoba/Datomic)
- `/90-docs/adr/2605192100-etzhayyim-mission-charter.md` — §1.12 Transparent Religious Force + §2(c) covert-ops avoidance
- `/90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md` — Charter Rider §2(c)/(e)
- `/90-docs/adr/2605301600-danjo-public-accountability-oversight-tier-b-actor-r0.md` — danjo (passive oversight sibling)
- `/90-docs/adr/2605301400-tadori-onchain-tracing-actor-and-kotoba-eavt-migration.md` — tadori (passive chain-tracing sibling)
- `/90-docs/adr/2605291100-manimani-kotoba-native-personal-knowledge-router.md` — manimani (member personal KG; downstream of own-data DSAR)
- `/20-actors/himotoki/` — manifest + README + CLAUDE.md + registry seed
- `/CHARTER-RIDER.md` — License + Rider canonical text
- `/CLAUDE.md` — Religious-corp status table
