---
id: adr-2607061800-saisei-self-filing-debt-relief-actor
title: "ADR-2607061800: saisei (再生) — self-filing debt-relief concierge actor, and relocating bankruptcy intelligence off the vendor"
status: accepted
doc_type: adr
topic: saisei-actor
authoritative: true
last_verified: 2026-07-06
priority: 6.0
axis: architecture
weight: 0.55
priority_note: "New Tier-B non-profit actor + a vendor→etzhayyim relocation of a domain (formal insolvency procedure) previously placed on the for-profit side."
authoritative_for:
  - saisei actor design (self-filing debt-relief concierge)
  - non-profit ownership of debtor-initiated formal insolvency procedure information
  - relocation of bankruptcy.gftd.ai's stated scope off gftdcojp
depends_on:
  - adr-2606112301-tate-legal-defense-concierge-r0
  - adr-2606112400-tate-worldwide
  - adr-2605262700-chigiri-upl-prior-art
  - adr-2605312030-toritsugi-government-procedure-concierge-tier-b-actor-r0
  - adr-2605201800-etzhayyim-yobel-debt-release-actor
  - adr-2605202000-etzhayyim-amnesty-legal-person-debt-actor
  - adr-2605231525-no-server-key
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2606302300-org-taxonomy-4-orgs
supersedes: []
superseded_by: []
---

# ADR-2607061800: saisei (再生) — self-filing debt-relief concierge actor, and relocating bankruptcy intelligence off the vendor

**Status**: accepted
**Date**: 2026-07-06
**Deciders**: Jun Kawasaki

# Context

A survey of the debt/insolvency actor landscape across this superproject (triggered
by the owner asking whether an AI actor exists, per-country, that non-profit-ly
handles a person's own bankruptcy/debt-workout procedure) found four adjacent but
non-overlapping pieces, none of which is "help me file my own bankruptcy":

| Actor | Org | Scope | Real footprint |
|---|---|---|---|
| `yobel` (`20-actors/yobel/`) | etzhayyim (non-profit) | Natural-person **voluntary religious/doctrinal** debt release (shmita/jubilee/tokusei-rei/political amnesty) — creditor opt-in, no legal force | S0: ADR + 8 lexicons + scaffold, no cells, no rite ever declared (ADR-2605201800) |
| `amnesty` (`60-apps/etzhayyim-project-amnesty/`) | etzhayyim (non-profit) | Legal-person (sovereign/corporate) voluntary multi-creditor restructuring | proposed/pre-seed: ADR + 8 lexicons only (ADR-2605202000) |
| `tate` (`20-actors/tate/`) | etzhayyim (non-profit) | Citizen defensive concierge — responds to notices an individual **receives**, incl. an `:insolvency` track (129 tests / 7,865 assertions, R2 maturity) | Real, tested, live registry (30 jurisdictions + 50 US states) — but every `:insolvency` entry is **creditor-side** (proof-of-claim / 債権届出 when someone else's insolvency notice arrives). Debtor-initiated self-petition is explicitly out of scope — tate's own N2 non-goal is "defensive only," and its `manifest.edn` `:actor/jurisdictions` comment already names this as a gap ("insolvency track (jp/us/de 債権者側)") |
| `toritsugi` (`20-actors/toritsugi/`) | etzhayyim (non-profit) | Proactive **administrative/municipal** procedure concierge (passport, driving licence, civil registry, tax filing) | Real, R0-registered — but scope is executive-branch窓口 procedures, not court petitions; its own boundary table routes appeals to `chigiri`, not itself |
| `bankruptcy.gftd.ai` | gftdcojp (for-profit vendor) | Referenced by ADR-0016 as "T2 TS Native, live (84 jurisdictions, 170 process types)" — the formal legal insolvency-procedure engine both `yobel` and `amnesty` name as their mandatory-legal-procedure fallback | **Vaporware.** A full-repo grep found exactly 3 lexicon schema JSON files (~59 KB total: `recordYobelRiteReference.json`, `receiverBankruptcy/flagCramDown.json`, `receiverBankruptcy/recordProceeding.json` — the last one's own jurisdiction enum lists 17 codes, not 84) plus one standalone bridge script (`70-tools/scripts/yobel-bridge/`) whose own README says it is "a drop-in for when vendor:bankruptcy.gftd.ai graduates from S0 scaffold" — i.e. the vendor's own documentation already concedes it never left scaffold stage. No `20-actors/bankruptcy/`, no Cloudflare Worker, no cells, no Solidity, no dedicated repo in `manifest/west.yml`/`repos.edn`. ADR-0016's "live" claim traces to a description string in `deps.edn`'s actor registry, not to code. |

So the debtor-initiated formal-procedure gap is real, and the one thing that was
supposed to fill it (`bankruptcy.gftd.ai`) never got built, sits on the wrong side
of the non-profit/for-profit boundary anyway (per ADR-2605172400's 3-axis split,
formal insolvency proceedings carry fiduciary/controllership liability + operator-
held case PII + fee billing — all vendor triggers), and gates access to it behind
`vendor:lawfirm.gftd.ai`, which is itself independently dormant (see `deps.edn
[gftdcojp_agent.product_portfolio]`: "lawfirm + lawyer = 休眠 (k.bakshi 退職・Lead
Advocate 空席)"). Waiting for the vendor side to build this out is not a plan.

Meanwhile `tate` is direct, proven prior art for exactly the hard part of this
problem — a non-profit, UPL-safe (弁護士法72条 and equivalents), jurisdiction-honest,
never-guess-foreign-law, self-submit-only concierge pattern, expressed as a coded
registry + `.cljc` methods + parametric tests. It is the wrong *home* for the
debtor-initiated leg (violates its own N2 defensive-only non-goal — every existing
`:insolvency` entry is a response to a notice **received**, never a petition the
member proactively **files**), but it is exactly the right *pattern*.

# Decision

**New Tier-B actor: `saisei` (再生 — "rehabilitation/rebirth," the term already used
in Japan's own 個人再生 statute, and the closest single word to bankruptcy law's
universal "fresh start" principle).**

| Field | Value |
|---|---|
| DID | `did:web:etzhayyim.com:actor:saisei` (registration in the did-web SSoT deferred to a follow-up wave — see Consequences) |
| Operating entity | etzhayyim (non-profit) |
| Tier | B |
| License | Apache 2.0 + Charter Compliance Rider (repo default) |
| Depends on | `chigiri` (UPL prior art / registry substrate pattern), `kaiyaku` (縁-ledger prepayment-as-claim cross-check), `kokoro` (Wellbecoming routing — bankruptcy is frequently accompanied by acute stress) |

## What saisei is

The **debtor-initiated** counterpart to `tate`'s creditor-side `:insolvency` track:
a member who wants to petition for **their own** formal insolvency relief (self-
bankruptcy / individual rehabilitation / debt relief order / consumer insolvency
proceeding) gets a coded, jurisdiction-keyed procedure registry that discloses:

- **Eligibility signals** (income/asset/debt-type shape, not a means-test verdict)
- **The court/administrative filing track name** and which forum it belongs to
- **Required forms + documents checklist** (self-assemble, never drafted by saisei)
- **Mandatory pre-filing steps** where the law requires them (e.g. Germany's
  außergerichtlicher Einigungsversuch via a certified `Schuldnerberatungsstelle`
  is a **statutory precondition** to filing, not an optional referral — saisei
  surfaces this as a blocking step, not a suggestion)
- **Fee amount + fee-waiver/in-forma-pauperis route** where one exists
- **DISCLOSED discharge-timeline rule** (statute text + anchor, never a computed
  calendar date — mirrors tate G4)
- **Referral-forward** to the jurisdiction's free/public advice channel, always
  present, non-optional for anything past the self-assemble stage

## UPL-safe gates (ported from tate's proven G-series, adapted for a self-petition instead of a notice-response)

| Gate | Rule |
|---|---|
| G1 member-principal | Only the member's own debt situation; live data is consent-gated + encrypted (`com.etzhayyim.encrypted.*`), R0 seeds are `:synthetic` |
| G2 non-adjudicating | Eligibility signals are pattern + disclosed statutory anchor, **never** "you qualify" / "file this" — report language stays 可能性/専門家確認, same as tate |
| G3 UPL (弁護士法72条 + equivalents) | No representation, no filing-on-behalf, no drafting of the petition itself — `make-option` structurally raises on `:representation`, identical to tate's `_make_option` gate. The member assembles + signs + files themselves |
| G4 timeline honesty | Never computes a calendar date; discloses the rule text + anchor, member confirms actual filing/service dates |
| G5 mandatory-precondition honesty | A jurisdiction's statutorily-required pre-filing step (e.g. DE's certified-counselor attempt, US means-test counseling) is modeled as a **blocking step**, not a skippable option — the plan cannot reach "self-submit" without it where the law requires it |
| G7 referral-forward | Always carries the jurisdiction's free/public insolvency-counseling directory; high-asset/high-debt/contested cases escalate harder than tate's line, since misfiling here has worse consequences than a missed civil-notice deadline |
| G10 jurisdiction-honesty | Procedures never cross jurisdictions; an uncovered jurisdiction degrades to `:unknown-jurisdiction` — saisei never guesses foreign insolvency law |

## Non-goals

- Not a law firm, not a licensed insolvency practitioner substitute, no individualized
  legal/financial advice
- Does not draft or file the petition on the member's behalf (UPL, G3) — self-submit
  only, exactly like tate and toritsugi's default posture
- Does not adjudicate eligibility (G2) — a means-test disclosure is not a means-test
  result
- Does not duplicate `tate`'s creditor-side `:insolvency` track (proof-of-claim when
  a third party goes insolvent stays with tate) or `toritsugi`'s administrative
  filings (passport/registry/tax) — saisei owns exactly the debtor-initiated
  court/formal-insolvency-forum petition surface
- Does not duplicate `yobel`/`amnesty` (voluntary, non-legal, doctrinal or
  multi-creditor-consent debt release) — saisei is the **formal, legally-binding**
  procedure info layer those two actors already name as their "when voluntary
  release isn't accepted, formal procedure is the fallback" pointer. **That pointer
  now resolves in-org (etzhayyim/saisei) instead of cross-org (vendor:bankruptcy)**

## R0 seed scope — 4 jurisdictions

Per owner direction, R0 ships a working, tested registry for **jp / us / uk / de**
(matching tate's own R0→R1 wave pattern of shipping a small honest subset first),
not an attempt at the vendor's unbuilt "84 jurisdictions" claim:

| Jurisdiction | Procedures seeded |
|---|---|
| `:jp` | 自己破産 (self-bankruptcy petition, 破産法216条以下) · 個人再生 (individual rehabilitation — 小規模個人再生/給与所得者等再生, 民事再生法221条以下) |
| `:us` | Chapter 7 (liquidation, 11 U.S.C. §701 et seq., incl. §109(h) credit-counseling precondition) · Chapter 13 (wage-earner plan, 11 U.S.C. §1301 et seq.) |
| `:uk` | Bankruptcy (England & Wales, online via adjudicator, Insolvency Act 1986 Pt IX as amended by the Enterprise & Regulatory Reform Act 2013 s.71) · Debt Relief Order (Insolvency Act 1986 Pt 7A, requires an approved intermediary — modeled as a blocking-step referral, not self-submit) |
| `:de` | Verbraucherinsolvenzverfahren + Restschuldbefreiung (InsO §304 ff., incl. the §305 außergerichtlicher Einigungsversuch mandatory precondition and the 2021 reform's 3-year discharge period) |

`coverage_report.cljc` names the remaining ~189 jurisdictions as an explicit,
honest worklist (tate's own G10 pattern) — never silently claimed as covered.

## Relocating `bankruptcy.gftd.ai`'s stated scope

Since the vendor actor never had real content, "moving" it is mostly a documentation
act plus starting saisei for real:

- ADR-0016 (gftdcojp, `90-docs/adr/0016-legal-cluster-topology.md.edn`) gets its
  `bankruptcy.gftd.ai` row marked relocated, pointing here — separate PR in that
  repo (see Consequences).
- The vendor's thin lexicon files (`00-contracts/lexicons/ai/gftd/apps/bankruptcy/`,
  `.../receiverBankruptcy/`) and the now-purposeless `yobel-bridge` script (its own
  purpose was bridging *across* the vendor/etzhayyim boundary for a case that no
  longer needs to cross that boundary) are retired in that same vendor-side PR.
- `yobel`'s README + `amnesty`'s CLAUDE.md, which currently say
  `vendor:bankruptcy.etzhayyim.com` / `vendor:bankruptcy.gftd.ai — mandatory legal
  procedure fallback`, are updated in **this** repo to point at native `saisei`
  instead (no more cross-org vendor reference for this fallback).

# Consequences

**Positive**

- Closes the actual gap the owner asked about, with a UPL-safe design proven by
  tate's 129 tests / 7,865 assertions in production use, not a from-scratch
  experiment
- Removes a cross-org dependency (`yobel`/`amnesty` → `vendor:bankruptcy.gftd.ai`)
  that pointed at code that was never built and whose gating vendor (`lawfirm.gftd.ai`)
  is independently dormant
- All formal + voluntary debt-relief information for natural persons now lives under
  etzhayyim (non-profit): `yobel` (doctrinal voluntary), `tate` (creditor-side
  response), `saisei` (debtor-side formal petition) — three actors, disjoint by
  N2-style non-goals, same UPL discipline
- Honest, bounded R0 (4 jurisdictions) rather than an unverifiable "84 jurisdictions"
  claim with no code behind it

**Negative / risk**

- **This is still information, not representation.** A member who follows saisei's
  disclosed checklist can still file incorrectly; G7 referral-forward is the
  mitigation, same as tate, but bankruptcy misfiling has materially worse
  consequences (non-dischargeable debt, dismissal with prejudice in repeat-filing
  jurisdictions) than a missed civil-notice deadline — hence G5's harder line on
  mandatory preconditions and a lower bar for "always show the free-counseling
  referral" than tate uses
- **DID/publication wiring deferred.** Unlike tate's current R2 state, saisei's R0
  does not yet register in `00-contracts/schemas/actor-profile-seed.kotoba.edn` or
  ship `public/actor/saisei/{did.json,profile.json}` — this ADR scaffolds the
  registry + tested `.cljc` methods only; self-publication (per ADR-2606281500's
  seed-and-grow doctrine) is a follow-up wave, mirroring how `amnesty` explicitly
  deferred phases 2-7 in its own ADR
- **Statute currency.** All entries carry `:verify-current-law true`; German
  insolvency law in particular changed materially in 2021 (discharge period cut
  from 6 to 3 years) and US/UK/JP thresholds move with periodic inflation
  adjustments — this is a standing maintenance burden, same as tate already carries
  across its 30-jurisdiction registry

# Alternatives Considered

## A. Extend `tate`'s `:insolvency` track to include debtor-side self-filing

Rejected. tate's N2 non-goal ("defensive only — responds to notices received") is
a tested, gate-enforced invariant, not a label. A self-bankruptcy petition is not a
response to anything the member received — it is a proactive filing the member
initiates on their own timeline. Bending N2 to fit this in risks weakening the
boundary that makes tate's existing 129-test suite meaningful (a future notice-
response feature could then also claim "well, it's adjacent to insolvency" and the
defensive/proactive line erodes). A disjoint sibling actor, exactly the shape this
codebase already uses for `yobel`/`amnesty` (per that ADR's own "Shannon-optimal
consolidation vs proliferation" reasoning — consolidate when the data model is the
same, split when the *invariant* is different), is cleaner: same registry pattern,
disjoint non-goal, no boundary erosion.

## B. Place it under `toritsugi` instead

Rejected. toritsugi's own boundary table explicitly routes "appeals" and anything
requiring 作成代理/legal characterization to `chigiri` + licensed counsel, and its
scope is executive-branch/municipal 窓口 procedures (passport, registry, tax) —
a court-forum insolvency petition is a different institutional target (courts /
insolvency-court administrators, not a municipal counter) with materially higher
UPL stakes than a driving-licence renewal. Forcing it into toritsugi's "administrative
procedure" frame would understate how consequential a misfiled bankruptcy petition is.

## C. Try to replicate the vendor's claimed "84 jurisdictions / 170 process types" scope immediately

Rejected per owner direction. That number was never backed by real, verified code —
building toward an unverified target invites the same gap between claim and reality
that this ADR is trying to close. R0 ships 4 real, cited jurisdictions; `coverage_report`
names the rest as an honest worklist, exactly as tate already does for its own
30-of-193 coverage.

## D. Leave `bankruptcy.gftd.ai` as the eventual formal-procedure home and just wire `saisei` as a thin non-profit front-end to it

Rejected. There is nothing to wire to — the vendor actor is 3 schema files with no
handler. Waiting on it blocks the actual deliverable indefinitely, exactly as it
already has since ADR-0016 (2026-04-14) without anyone building it.

# References

- ADR-0016 (gftdcojp: legal-cluster-topology — origin of the `bankruptcy.gftd.ai`
  claim this ADR relocates)
- ADR-2605172400 (etzhayyim vendor 3-axis split rule — liability/custody/settlement
  reasoning for why formal insolvency procedure was originally placed vendor-side)
- ADR-2605201800 (yobel — natural-person voluntary doctrinal debt release, sibling actor)
- ADR-2605202000 (amnesty — legal-person voluntary multi-creditor restructuring, sibling actor)
- ADR-2606112301 + 2606112400 (tate — UPL-safe concierge pattern this ADR ports)
- ADR-2605312030 (toritsugi — adjacent but institutionally distinct proactive concierge)
- ADR-2605262700 (chigiri — UPL prior art / registry substrate)
- ADR-2606302300 (org-taxonomy 4-orgs — non-profit vs vendor placement rule)
- 11 U.S.C. §§701 et seq., §1301 et seq., §109(h) (US Bankruptcy Code)
- 破産法216条以下, 民事再生法221条以下 (Japan)
- Insolvency Act 1986 Pt IX (as amended by the Enterprise and Regulatory Reform Act 2013 s.71) + Pt 7A (England & Wales)
- Insolvenzordnung (InsO) §§304-305 (Germany, as amended 2021)
