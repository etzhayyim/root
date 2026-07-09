---
id: adr-2605312030-toritsugi-government-procedure-concierge-tier-b-actor-r0
title: "ADR-2605312030: 取次 (toritsugi) — citizen-facing government-procedure concierge Tier-B actor (R0)"
status: proposed
doc_type: adr
topic: toritsugi-government-procedure-concierge
authoritative: true
last_verified: 2026-05-31
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - toritsugi-government-procedure-concierge
depends_on:
  - "2605262700"
  - "2605302130"
  - "2605302357"
  - "2605302358"
  - "2605181100"
  - "2605262130"
  - "2605192100"
  - "2605192200"
  - "2605192300"
  - "2605215000"
related:
  - "2605262900"
  - "2605302000"
  - "2605301600"
  - "2605263400"
  - "2605260000"
supersedes: []
superseded_by: []
---

# ADR-2605312030: 取次 (toritsugi) — citizen-facing government-procedure concierge Tier-B actor (R0)

**Status**: proposed
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

The 2026-05-31 audit asked: *"etzhayyim で LINE のように自治体や政府手続きを
行ってくれる actor は設計されているか?(atproto ベースで)"* — i.e. is there a
**citizen-facing digital-government concierge** that, like Japanese
municipalities' LINE 公式アカウント, helps a person **complete** 自治体・政府
手続き (resident registration 住民票, certificates, 給付金 applications, 届出,
tax procedures, e-Gov flows) through a chat / atproto interface.

**Finding: this is a gap.** Every government-touching actor in the monorepo
faces the *state*, not the *citizen*:

- **danjo (弾正, ADR-2605301600)** — watches the state: ingests 国会会議録 /
  予算書 / 政府調達 and emits non-adjudicating discrepancy observations.
  **Passive oversight; censor's eye, never sword.**
- **himotoki (繙き, ADR-2605302130)** — exercises a *right of access*: files
  DSAR / FOIA disclosure requests and custodies responses. **Pulls data out
  of organizations; does not help a member DO a procedure.**
- **chigiri (契, ADR-2605262700)** — legal-procedure *substrate* (NOT a law
  firm; UPL-bound): templates + legal characterization + appeal procedure.
  **Knows the form and the law; does not run a citizen through it.**
- **toritate (執帳, ADR-2605262900)** — the religious-corp's own on-chain
  books, incl. tax accounting; not a citizen-procedure assistant.
- **kanae (鼎, ADR-2605302300)** — renders fiscal flows; visualization only.
- **gov-municipality (ADR-2605250800)** — building-permit (建築確認申請)
  workflow for the *construction actor* (tatekata), project-level, not
  resident-facing.
- **産土 ubusuna / §1.16 Social Security delivery (ADR-2605302357/2605302358)**
  — delivers *etzhayyim's own* in-kind social security to adherents
  (outreach → vow → eligibility → notice → publish). It is the closest
  sibling, but it is **not** a government-procedure execution arm: it does
  not know 自治体 procedures, does not fill 申請書, does not route a member
  to a 窓口.
- **ADR-2605260000 (L5 Gov-Auth / MyNumber + WebAuthn)** — an *authentication*
  layer (binds a member to MyNumber); not procedure assistance.

So the "knows-the-form" piece (chigiri) and the "files-an-access-request"
piece (himotoki) exist, but **no actor proactively helps a member/citizen
complete a government or municipal procedure** — the LINE-公式アカウント role.

This ADR creates that actor: **取次 (toritsugi)**.

> **取次** = *to relay / to broker at the counter* (窓口取次). The name frames
> the actor as the **service-delivery counterpart** to himotoki (right of
> access) and danjo (oversight): toritsugi stands at the 窓口 *on the
> citizen's side*, relaying the member to the right procedure and walking
> them through it. Name is provisional; Council may rename at ratification.

# Decision

Create **取次 toritsugi** as a Tier-B actor at
`did:web:toritsugi.etzhayyim.com` (`20-actors/toritsugi/`), kotoba-EAVT-native
(ADR-2605262130; no Kotoba/Datomic / no projection layer), Murakumo-only inference
(ADR-2605215000), atproto/MST-native for member-facing channels.

## §1 Scope (per founder decision 2026-05-31: option 1 + 2)

toritsugi delivers, **in escalating phases**:

1. **案内 + 伴走 + 本人提出支援 (R0→R2, the default mode)** — proactively
   surface available 制度/給付/手続き to a consenting member, explain the
   procedure, assemble the 必要書類 checklist, and **assist the member in
   filling the 様式/フォーム**, so that the **member themselves submits and
   signs**. toritsugi never becomes the 申請者. This is the himotoki-safe,
   行政書士法-safe baseline (see G5/G15).

2. **本人同意ベース提出代行 (R3, gated exception)** — with explicit
   per-submission consent + DID/SBT binding, toritsugi files the application
   through the official channel **on the member's behalf for the member's own
   procedure**. This is the active-outbound capability and is **constitutionally
   gated** (G14 verified-procedure-only + G15 self-submission-default +
   行政書士法 clearance + Council Lv7+); it is NOT enabled at R0.

JP-first at R0; architecture jurisdiction-generic (regime field on every
procedure record).

## §2 Coded procedure registry (the LINE-like core)

The analogue of himotoki's coded target registry. Every government /
municipal procedure is encoded as an
`com.etzhayyim.toritsugi.procedure` record holding the **窓口 / 所管 (省庁・
自治体) / オンライン申請URL / 必要書類 / 様式 / 手数料 / 法定処理期間 / 根拠
法令 / オンライン or 窓口 or 郵送 channel** so a cell can guide + (eventually)
file procedurally.

Seed at `registry/procedures.seed.json` (6 entries, all `unverified-seed`):
住民票の写し交付請求 · 転入届 · 出生届 · マイナンバーカード交付申請 ·
児童手当認定請求 · 確定申告 (e-Tax, → toritate boundary). Like himotoki, the
**verification gate (G14)** means seeds enable routing/guide design only; no
live submission against an `unverified-seed` / stale entry. Concrete
窓口/様式/手数料 drift and are best-effort references as of 2026-05-31.

## §3 Cells (7 Pregel cells, R0 path-reserved)

All raise `RuntimeError("toritsugi R0 scaffold: …")` until Council
ratification.

| Cell | Node | Phase | I/O |
|---|---|---|---|
| `toritsugi_procedure_registry` | reuben | continuous | maintain + resolve the coded `procedure` catalog; enforce G14 verification status |
| `toritsugi_eligibility_match` | reuben | event | consenting member's life-event/profile (OWN data) → `benefitMatch` (proactive "you may be eligible for X" — the LINE-like notify; never a third party) |
| `toritsugi_intake` | reuben | event | member consent + DID/SBT + need/life-event → `procedureGuide` session |
| `toritsugi_guide` | gad | event | pull chigiri procedure template + resolved `procedure` → step-by-step 案内 + 必要書類 checklist (UPL boundary G5) |
| `toritsugi_draft` | gad | event | assist filling the 様式/フォーム → `applicationDraft` artifact (member reviews + owns; assist, NOT 作成代理) |
| `toritsugi_submit` | naphtali | event | **the only / gated active-outbound cell** — default hands the draft back for member self-submission; 代行 submission only under G14+G15+R3 → `submissionRecord` |
| `toritsugi_status_track` | naphtali | continuous | 処理状況 / 法定処理期間 clock + follow-up + 結果 intake (encrypted PII, G6); refusal → appeal route via chigiri |

## §4 Constitutional gates (G1–G15, immutable; Council Lv6+ + new ADR to amend)

- **G1** Charter Rider §2(a)–(h) scan on every authored artifact + outbound action.
- **G2** kotoba attestation lineage on every record (EAVT datoms; no RW).
- **G3** **Consent-gated + identity-bound, OWN procedure only** — every guide /
  draft / submission is member-initiated with explicit consent + Adherent-SBT/DID
  binding and concerns **the member's own** procedure; **never** acts for a
  non-consenting person; **never** a third party's procedure or data.
- **G4** **Transparent + non-pretextual** — the member is always the named
  申請者本人; no impersonation / sockpuppet / false identity (§2(c)). toritsugi
  is an *unofficial* assistant and never represents itself as an official 自治体
  channel.
- **G5** **行政書士法 / UPL-equivalent boundary** — toritsugi provides 情報提供 +
  案内 + 入力補助 + 伴走; it renders **NO legal/tax advice** and performs **NO
  官公署提出書類の作成代理** reserved to 行政書士/弁護士/税理士. Legal
  characterization + 作成代理 + appeals route to **chigiri + licensed
  行政書士/external counsel** (Public Fund Council Lv6+); tax procedures route to
  **toritate** boundary. (CRITICAL gate for this actor.)
- **G6** **PII confidentiality** — member PII + 申請内容 + 結果 land ONLY in
  `com.etzhayyim.encrypted.*` XChaCha20-Poly1305 DID-bound envelopes
  (ADR-2605181100); **never** plaintext PII on MST. (Outbound third-party PII
  not brought in by member ingress stays outside the Covenant Transparency
  ingress scope — ADR-2605310100 §4(2).)
- **G7** Murakumo-only inference (ADR-2605215000); no vendor LLM callout.
- **G8** **Non-fabrication / accuracy** — never invent 手続き / 様式 / 根拠法令 /
  手数料 / 期限; every `procedure` cites 根拠法令 + `provenance`; the member
  **always confirms** before any submission; no hallucinated legal facts.
- **G9** **No commercialization** — non-profit; no paid filing-mill; no fee for
  the service (donation-only per substrate boundary); no resale of member or
  制度 data (Charter Rider §2(e)).
- **G10** **Lawful-channel-only** — the only external mutation is a lawful
  submission through an **official** channel **with member authorization**;
  never alters records; never unauthorized access / access-control circumvention;
  respects 自治体 portal ToS + rate limits.
- **G11** **Transparent Religious Force discipline** (§1.12) — assist + submit +
  track only; no coercion / extra-legal pressure; appeals via lawful 不服申立
  (審査請求) routed to chigiri.
- **G12** **Scope / data-minimization** — collect only what the specific
  procedure requires; no fishing / profile-building beyond the active need.
- **G13** `stateAlignedFlag` pass-through into derived records (G13 parity with
  himotoki/danjo).
- **G14** **Verified-procedure-only submission** — `toritsugi_submit` refuses any
  `procedure` whose `verificationStatus` is `unverified-seed` or whose
  `lastVerified` is outside the freshness window; live filing requires
  `maintainer-verified` (public-procedure) / `council-verified` (代行 path).
- **G15** **Member-self-submission default** — the default mode is
  guide-the-member-to-submit-themselves; `toritsugi_submit` active-outbound 代行
  is the **gated exception** (R3), requiring explicit per-submission consent +
  行政書士法 clearance + Council Lv7+. Encodes the §1 scope decision (option 1 is
  the floor; option 2 is gated).

## §5 Non-goals (N1–N14, explicitly excluded)

- **N1** NOT a 行政書士 / 司法書士 / 税理士 / 弁護士 firm (作成代理 reserve →
  chigiri + licensed professionals).
- **N2** NOT a replacement for the member's own right/duty — assists, does not
  supplant; the member is always the 申請者本人.
- **N3** NOT a surveillance / profiling system.
- **N4** NOT a data-broker / reseller of member data or 制度 data.
- **N5** NOT a pretext / impersonation tool (never submits as someone else).
- **N6** NOT an unauthorized-access / scrape-around / control-evading portal bot.
- **N7** NOT a mass-filing / 窓口-DoS tool.
- **N8** NOT a state-granted legal personality, NOT an official 自治体 channel
  (unofficial assistant; Preamble §0.4 Lv7+ lock).
- **N9** NOT a closed-source / secret-method engine.
- **N10** NOT a plaintext-PII store.
- **N11** NOT Japan-exclusive in architecture (JP-first R0; jurisdiction-generic).
- **N12** NOT a paid service / filing-mill (donation-only).
- **N13** NOT legal / tax advice (routes to chigiri / toritate / licensed).
- **N14** NOT an oversight / audit actor — that is danjo. toritsugi **serves the
  citizen**; danjo **watches the state**. Opposite posture, deliberately
  separated.

## §6 Lexicons (6 namespaces, `com.etzhayyim.toritsugi.*`)

- `procedure` — coded government-procedure registry entry (窓口/所管/様式/必要
  書類/手数料/法定処理期間/根拠法令/channel; `verificationStatus` gate).
- `benefitMatch` — proactive eligibility match for a consenting member (OWN data).
- `procedureGuide` — a member-facing 案内/伴走 session (steps + checklist state).
- `applicationDraft` — assisted form draft artifact (member-owned; pre-submission).
- `submissionRecord` — record of a submission (member self-submit, or gated 代行).
- `statusTrack` — 処理状況 + deadline clock + result/appeal pointer.

## §7 Cross-actor boundaries

- **chigiri (ADR-2605262700)**: chigiri = procedure templates + legal
  characterization + 作成代理 + appeal procedure (UPL); toritsugi = citizen
  intake + proactive match + interactive guide + draft-assist + (gated) submit +
  status-track. toritsugi **pulls** templates from chigiri; it does not duplicate
  chigiri's templating or render advice.
- **himotoki (ADR-2605302130)**: sibling active-outbound. himotoki files
  **開示請求** (data out); toritsugi files **申請/届出** (member into a
  procedure). Shared dispatch discipline (G3/G4/G10/G14); disjoint purpose.
- **toritate (ADR-2605262900)**: tax procedures (確定申告 etc.) and any
  accounting characterization route to toritate; toritsugi only guides the
  citizen-side mechanics.
- **warifu (ADR-2605302000)**: 申請手数料 / 証紙 settled via warifu (USDC /
  lawful official payment channel), never a platform-held instrument.
- **musubi (ADR-2605263400)** / **shidemori / hagukumi**: life-events (婚姻 /
  出生 / 死亡 / 育児) that trigger both a covenant act and a government 届出 —
  musubi performs the ceremony, toritsugi handles the corresponding 行政手続き.
- **産土 ubusuna / §1.16 (ADR-2605302357/2605302358)**: toritsugi is the
  **government-procedure execution arm** complementing etzhayyim's own
  social-security delivery — when a member's wellbeing need maps to an external
  state benefit, the social-security pipeline routes to toritsugi.
- **danjo (ADR-2605301600)**: opposite posture (serves citizen vs watches state).
- **manimani (ADR-2605291100)**: a member's own procedure history → that
  member's personal knowledge graph (with consent).
- **`com.etzhayyim.encrypted.*` (ADR-2605181100)**: the only home for member PII.
- **kotoba EAVT (ADR-2605262130)**: procedure catalog + guide/draft/submission
  lifecycle datoms; no Kotoba/Datomic / no projection layer.

## §8 Roadmap

- **R0 (this ADR, now)** — scaffold only. 7 cells path-reserved (import-time
  RuntimeError). 6 Lexicon skeletons. Procedure-registry seed (6 entries, all
  `unverified-seed`). manifest + README + CLAUDE.md. **No submission, no live
  guide dispatch.**
- **R1** (post-Bootstrap-Council + ≥1 Council Lv6+ ratify) — `procedure_registry`
  live + maintainer-verification flow (G14); `eligibility_match` + `intake` +
  `guide` build `procedureGuide` artifacts from chigiri templates. **案内 only,
  no draft submission.**
- **R2** (post-R1 + 30-day public comment) — `draft` assist + `status_track`;
  member **self-submits** (toritsugi assembles + hands back). 案内+伴走+本人提出
  支援 fully live (option 1). No 代行.
- **R3** (post-R2 + Council Lv7+ unanimity + 行政書士法 clearance) —
  `toritsugi_submit` active-outbound **本人同意ベース提出代行** (option 2) for
  the member's own procedure; encrypted result custody; appeal routing;
  multi-jurisdiction.

# R1 Technical Build (2026-07-09, ratify-pending)

This section records the **technical** completion of the R1 scope (and, honestly,
the R2 scope too — the build went through draft + self-submit + status_track). It
is **ratify-pending**: the Council gate (Lv6+ ≥3) to advance R0→R1 has NOT been
cleared, no live deployment has happened, and no charter invariant has been
amended. The code is the charter made executable; ratification is what earns it
the right to run on a member's behalf. R3 (代行) remains structurally gated and
is NOT part of this build.

**What landed (substrate-native Clojure, `.cljc`):**

- **`src/toritsugi/governor.cljc`** — the independent **ProcedureGovernor**. Its
  HARD surface is exposed as data: `(def hard-gates #{:G3 :G4 :G5 :G6 :G8 :G10
  :G14 :G15})` — the 8 unoverridable charter gates (§4). A HARD violation forces
  HOLD (no human can approve past it); a 代行 submit is ALWAYS high-stakes →
  escalate. The contained concierge advisor is deterministic (G7 Murakumo-only —
  no vendor LLM callout); the Governor censors its proposal before anything is
  recorded. Backend swap: `MemStore` ‖ `DatomicStore` (via `langchain.db :db-api`,
  itself swappable to real Datomic / kotoba-server XRPC).
- **`src/toritsugi/flow.cljc`** — the citizen-concierge flow as one langgraph-clj
  **StateGraph** (one run = one op). `interrupt-before #{:request-approval}`
  turns the 代行 path into a human/Council sign-off (G15). Each cell node ALSO
  runs that cell's pure state-machine membrane; a cell refusal is folded into the
  governor verdict as a HARD violation, so either layer can force a HOLD.
- **`src/toritsugi/cells/{procedure_registry,eligibility_match,intake,guide,draft,submit,status_track}/state_machine.cljc`**
  — the **7 cell membranes** (the same G-gates, structurally, at each step). Pure
  `(state) -> {"cell_state" {…}}`; stdlib only; self-contained.
- **`registry/toritsugi.procedure-flow.bpmn.edn`** — the executable **BPMN-as-edn**
  spine of the StateGraph (14 nodes / 14 flows). The `mode_gw`
  exclusive-gateway encodes G15: `member-self-submit` is the default branch;
  `agent-on-behalf` (代行) is the single gated exception routed through the
  `approval` user-task. FORMAT: BPMN-as-edn per **ADR-2607090900**
  (kotoba-lang/org-omg-bpmn / bpmn-clj).
- **`src/toritsugi/{store,phase}.cljc`** — Store protocol (EAVT ground datoms +
  append-only audit ledger = the concierge genealogy) and the lifecycle/rollout
  phase gate (R0→R3 rollout only adds caution; 代行 is never `:auto`).

**Tests (machine-verified, no silent drift):**

- `clojure -M:test` → **25 tests / 64 assertions, green** (governor-contract:
  pins G3/G4/G5/G6/G8/G10/G14/G15 + MemStore ≡ DatomicStore contract; flow:
  happy-path init→…→tracked, refused/hold, 代行 interrupt + sign-off).
- `bb run_tests.clj` → **12 tests / 52 assertions, green**
  (`methods/test_charter_gates.cljc`: G1–G15 declared in manifest, lexicon
  const verification, **Governor HARD surface == G3/G4/G5/G6/G8/G10/G14/G15
  (parses the `hard-gates` literal from governor.cljc)**, **BPMN `mode_gw`
  reflects G15**; `methods/test_manifest_invariants.cljc`: 15 gates / 6
  lexiconNamespaces / 7 cells ↔ `src/toritsugi/cells/` disk parity).
- `clojure -M:lint` (clj-kondo) → **errors 0, warnings 0**.

**Cross-actor wiring (ooyake):** the `resolve` step references ooyake's
official-process BPMN models by id (`:gov.procedure/bpmn`), per
**ADR-2606021600 R2** — toritsugi consumes, never re-authors, the government's
procedure. The 6 R0 procedures are modeled at
`20-actors/ooyake/registry/gov-procedures.bpmn.edn`.

**What did NOT change (charter honesty):** no invariant in §4 is amended; the
actor is still 案内 + 伴走 + 本人提出支援 by default (代行 is the gated R3
ceiling, off); PII stays in `com.etzhayyim.encrypted.*` only (G6); Murakumo-only
(G7); non-profit (G9). The advancement R0→R1 needs Council Lv6+ ≥3 — see
`90-docs/toritsugi-r3-ratification-request.md` for the R3 (代行) gate which adds
Lv7+ unanimity + 行政書士法 clearance.

# Consequences

- **Positive**: closes the citizen-facing government-procedure gap with a
  charter-clean design that reuses the himotoki target-registry pattern, the
  chigiri UPL boundary, and the §1.16 social-security pipeline. The 行政書士法 /
  UPL risk — the sharpest risk for this actor — is structurally contained:
  option 1 (guide + self-submit) is the floor and needs no 代理権; option 2
  (代行) is gated behind G14+G15+Council Lv7+ + licensed clearance and is off at
  R0. PII is confined to encrypted DID-bound envelopes.
- **Negative / honest limits**: the seed registry is best-effort and will
  drift; G14 makes that explicit (no live filing against unverified seeds). The
  代行 path may never be enabled if 行政書士法 clearance cannot be obtained —
  that is acceptable; option 1 still delivers the LINE-like value. Mapping every
  自治体 (1,700+ municipalities) procedure is a large, living curation effort,
  not an R0 deliverable.
- **Constitutional**: no invariant is amended. Non-profit / donation-only,
  Murakumo-only, kotoba-native, Transparent Religious Force, encrypted-PII, no
  platform-held key (ADR-2605231525, member/community-operator-signed for any
  submission) all hold. Lexicon ratification + the R3 代行 gate require Council
  after Bootstrap Council Seats 2-5 RFP close (2026-06-19).

# Alternatives Considered

- **Extend chigiri instead of a new actor** — rejected: chigiri is the
  UPL-bound *substrate* (form + law). Bolting citizen intake, proactive
  matching, and an outbound submit path onto it would blur the UPL boundary that
  keeps chigiri safe. A separate actor with its own gates is cleaner (mirrors
  the himotoki-vs-chigiri split).
- **Extend the §1.16 ubusuna pipeline** — rejected: that pipeline delivers
  *etzhayyim's own* benefits to adherents; government procedures face an
  external state with its own forms, deadlines, and reserved-practice law.
  Different boundary, different gates. toritsugi instead *complements* it.
- **Guidance-only (option 3), no submission ever** — considered; rejected by
  founder as too thin. Option 1 (guide + assist + member self-submit) is the
  floor; option 2 (代行) is the gated ceiling.
- **代行 from day one** — rejected: 行政書士法 reserves 官公署提出書類の作成代理;
  enabling 代行 without licensed clearance + Council Lv7+ would breach the UPL
  boundary. Hence G15 self-submission-default + R3 gating.

# References

- This ADR: `/90-docs/adr/2605312030-toritsugi-government-procedure-concierge-tier-b-actor-r0.md`
- Actor: `/20-actors/toritsugi/` (manifest + README + CLAUDE.md + registry seed)
- Lexicons: `/00-contracts/lexicons/com/etzhayyim/toritsugi/`
- ADR-2605262700 (chigiri legal-procedure substrate — UPL boundary)
- ADR-2605302130 (himotoki disclosure-request actor — sibling pattern + registry)
- ADR-2605302357 / 2605302358 (§1.16 Social Security doctrine + delivery pipeline)
- ADR-2605262900 (toritate accounting/tax boundary)
- ADR-2605302000 (warifu — 手数料 settlement)
- ADR-2605301600 (danjo — oversight counterpart)
- ADR-2605181100 (confidentiality — encrypted PII envelopes)
- ADR-2605262130 (kotoba storage substrate — no Kotoba/Datomic)
- ADR-2605231525 (no platform-held signing key)
- ADR-2605192100 §1.12 / §1.16 / §2(c) (mission charter)
- ADR-2605192200 (Charter Rider) · ADR-2605192300 (Bootstrap Council)
- ADR-2605215000 (Murakumo-only inference)
- ADR-2605260000 (L5 Gov-Auth / MyNumber — auth layer toritsugi consumes)
