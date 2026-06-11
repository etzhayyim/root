---
id: adr-2606111954-hinagata-legal-template-commons
title: "ADR-2606111954: hinagata 雛形 — legal-document-template commons (EDN-bound to statutes, content-addressed, e-signable)"
status: active
doc_type: adr
topic: hinagata-legal-template-commons
authoritative: true
last_verified: 2026-06-12
priority: 5.0
axis: architecture
weight: 0.55
priority_note: "First template-commons actor; binds the gap between chigiri (procedure) and the legal-corpus (statutes)."
authoritative_for:
  - legal-document-template-commons
  - legal-template-ontology
  - template-to-statute-binding
  - electronic-contract-bridge
depends_on:
  - 2605262700
  - 2605262800
  - 2605231230
  - 2605231525
  - 2605181100
  - 2605312345
  - 2605215000
  - 2606101000
related:
  - 2606072100
  - 2605302000
  - 2605263400
supersedes: []
superseded_by: []
---

# ADR-2606111954: hinagata 雛形 — legal-document-template commons

**Status**: active
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

The repo had a comprehensive legal-procedure design (**chigiri 契**, ADR-2605262700) and a
global **legal-corpus** ingestion design (ADR-2605262800) — but a survey on 2026-06-11
confirmed four concrete gaps between "design" and "working code":

1. **Fair worldwide legal-document templates + a publish mechanism** existed only as a
   path-reserve in chigiri's lexicons and the legal-corpus `law/templates/` bucket; **no
   actual templates and no publish surface** existed.
2. **EDN linking templates to actual statutes** was *not even specified*: chigiri §8 declared
   cell→statute dependencies in prose, but there was no `:clause/cites-statute` edge schema,
   no template↔statute graph — the single largest gap.
3. **"Anyone can use it"** — there was no content-addressed, openly-licensed published corpus.
4. **Electronic contracts** — the `com.etzhayyim.esign.*` lexicons (ADR-2605231230) existed,
   but **nothing rendered a template into a signable document or built/verified an envelope**;
   the covenant-attestation schema had no signature path.

These are the fairness/access half of the legal lineage: chigiri runs **procedure**, the
legal-corpus ingests **statutes**, and what was missing is the **published, fair, reusable
document templates** that rest on those statutes and that anyone may execute.

# Decision

Introduce **hinagata 雛形** (template / mould), a Tier-B KG-mirror actor reusing the rasen/inochi
architecture (edge-primary, aggregate-first, non-adjudicating), specialised to legal documents.

1. **`legal-template-ontology` (`00-contracts/schemas/legal-template-ontology.kotoba.edn`)** —
   the EDN vocabulary that closes gap #2. Nodes `:lt/kind` ∈ `{:template :clause :statute
   :jurisdiction :concept :license}`; edges `:en/kind` ∈ `{:has-clause :cites-statute
   :mandated-by :instantiates :governed-by :applies-in :translates :supersedes :conflicts-with
   :derived-from}` carrying `:en/binding-load` ∈ [0,1] and a disclosed `:en/force`
   (`:mandated`/`:cited`/`:referenced`). **`:cites-statute` / `:mandated-by` is the binding to
   actual public law** — the link that makes a template traceable rather than free-floating.
2. **Seed graph** — 11 real templates (international sale, mutual NDA, GDPR DPA, JP lease + EN
   translation, ILO-aligned employment, consulting, Apache contribution, zero-interest
   benevolent loan, donation, JP consumer sale) decomposed into 23 reusable clauses, bound to
   19 real public statutes (CISG, NY Convention, UNCITRAL Model Law, ILO C87/C105, eIDAS,
   GDPR Arts. 15/28/33, 民法601, 借地借家法, 利息制限法, 特定商取引法, 電子署名法, ESIGN, UETA,
   Apache-2.0) — each statute with its **official source URL**.
3. **Edge-primary analyzer (`analyze.py`)** — a template's **groundedness** = the integral of
   its incident clause `:cites-statute`/`:mandated-by` + direct citations × disclosed
   optionality weight (`:mandatory 1.0 :recommended 0.6 :optional 0.3`), computed on read, never
   stored (N1/G2). Plus clause reusability, statute pull, jurisdictional reach.
4. **Content-addressed publish (`publish.py`, gap #1 + #3)** — renders every template body and
   content-addresses it to a kotoba IPFS CIDv1 (raw/sha2-256), **verified byte-identical to
   `ipfs add --cid-version=1 --raw-leaves`**, snapshotting bodies + a manifest (CID, license,
   jurisdiction, per-template statute citations) into git-tracked `80-data/legal-templates/`.
   Apache-2.0 + Charter Rider; anyone may fetch, verify the CID, and reuse.
5. **Electronic-contract bridge (`esign.py`, gap #4)** — renders a template into a deterministic
   signable document that carries its statutory provenance, content-addresses it (CIDv1 +
   SHA-256), builds the **UNSIGNED** `com.etzhayyim.esign.envelope`, and verifies a signature's
   structural binding (roster + anti-tamper + accepted WebAuthn algorithm), firing a
   `completedEvent` only when every roster signer has a valid signature. **no-server-key**: the
   member signs client-side with their own passkey; the cryptographic verification is
   kotoba-auth's job (ADR-2605231525).
6. **Lexicons** — `com.etzhayyim.hinagata.{template, clause, statuteCitation}` (the published
   template, the reusable clause, the clause↔statute binding record) complementing the reused
   `com.etzhayyim.esign.*` records.
7. **kotoba pywasm component** — `analyze` / `datoms` / `coverage` / `envelope` exports,
   build-ready via componentize-py; G1 + no-server-key hold in WASM.

**Constitutional gates**: G1 commons-not-counsel (UPL structurally excluded, shared boundary
with chigiri G14) · G2 edge-primary · G3 non-adjudicating (citations are disclosed facts, never
validity/enforceability verdicts) · G4 public venue + open license + content-addressed · G5
sourcing honesty (unbound clauses surfaced) · G6 Murakumo-only · G7 outward-gated (live
legal-corpus binding + IPFS pin/IPNS) · G8 no-server-key.

# Consequences

- **Positive**: closes all four surveyed gaps with working, tested code (23 tests green); gives
  the repo its first EDN template↔statute binding; produces a content-addressed, openly-licensed
  template commons anyone can use; lands the missing electronic-contract flow on top of the
  existing esign substrate without a server key. CID parity with `ipfs` verified.
- **Boundary**: hinagata is **not** a law firm and issues **no advice** (G1) — it supplies fair
  public templates + a faithful signing envelope. Live statute binding to the legal-corpus
  (ADR-2605262800) and IPFS pin / IPNS publish are **G7-gated** (Council + operator DID); R1
  ships the analyzer, schema, seed, and content-addressed publish snapshot.
- **Coverage honesty (G5)**: coverage of all template families / all jurisdictions is ~0 by
  design; `coverage_report.py` measures it and names the next-wave binding worklist (more
  jurisdictions; UK/other sources are in the allowlist but not yet seeded).
- **Negative / deferred**: clause body-text fragments are not yet individually content-addressed
  (template-level only); the legal-corpus live binding is future work gated on ADR-2605262800 W1.

## Coverage expansion — `/loop` waves 1–22 (2026-06-11 / 06-12, PR #1649)

The R1 seed (11 templates / 23 clauses / 18 statutes / 5 jurisdictions / 1 language / 23 tests,
117 縁) was expanded over 22 self-paced `/loop` iterations into a mature, worldwide corpus while
keeping every test green and the integrity validator clean. Final state:

- **Size**: 51 templates · 46 clauses · 132 statutes · 19 jurisdictions · 32 concepts ·
  10 languages · 619 縁 · 33 tests green.
- **Worldwide grounding**: the eight most cross-cutting clauses (electronic signature,
  data-protection, sale-of-goods warranty, employment, tenancy, IP-licensing, consumer
  cooling-off, dispute-resolution) are each grounded in real public law across many
  jurisdictions; all six legal systems (civil / common / international / religious / customary /
  mixed) are represented; 28/30→33/35→… ending at all clauses but two (`:definitions`,
  `:service-levels`, both genuinely non-statutory) statute-bound.
- **~30 contract families** incl. sale, NDA, DPA (+2021 SCC version), lease (JP/DE +
  jurisdiction-neutral), employment (ILO/DE/global), consulting, OSS/CC/copyleft licensing,
  zero-interest + heter-iska finance, donation, consumer-sale, partnership, power-of-attorney,
  settlement, guaranty, franchise, distribution, security-interest, insurance, construction,
  services-SLA, joint-venture, SaaS-subscription, escrow.
- **10 languages** (en/ja/fr/de/es/zh/pt/ko/hi/ar) with 23 `:translates` pairs.
- **Maturity tooling added**: `validate.py` (integrity checker, 0 errors / 0 warnings),
  `maturity.py` (generated `MATURITY.md` scorecard), and per-language + per-jurisdiction +
  relational-depth (`:conflicts-with` / `:derived-from` / `:supersedes`) measurement in
  `coverage_report.py`. **All ten ontology edge kinds are now exercised.**

Live legal-corpus binding (ADR-2605262800) + IPFS pin / IPNS publish remain G7-gated; clause
body-text fragments and rendered full bodies (vs structural stubs) remain future work.

# Alternatives Considered

- **Extend chigiri instead of a new actor** — rejected: chigiri is the *procedure* substrate
  (UPL-bounded workflows); the *document commons* + *statute-binding graph* is a distinct
  concern with a distinct ontology, and keeping them separate keeps each gate set clean.
- **Store template→statute links as prose in lexicons** (status quo) — rejected: that is what
  left gap #2 unfillable; an explicit edge schema is required for the binding to be queryable
  and content-addressable.
- **A new bespoke signing flow** — rejected: the `com.etzhayyim.esign.*` substrate already
  exists (ADR-2605231230) with no-server-key discipline; hinagata wires into it rather than
  reinventing it.
- **Server-side signing for convenience** — rejected: violates ADR-2605231525; the member's own
  WebAuthn passkey signs client-side.

# References

- ADR-2605262700 (chigiri 契 — legal-procedure substrate)
- ADR-2605262800 (global legal-corpus ingestion)
- ADR-2605231230 (esign envelope substrate)
- ADR-2605231525 (no-server-key invariant)
- ADR-2605181100 (Signal key-wrap confidentiality envelope)
- ADR-2605312345 (kotoba Datom = first-class canonical state)
- ADR-2606101000 (rasen — same KG-mirror architecture)
- ADR-2606072100 (shomei — signer identity assurance) · ADR-2605302000 (warifu — payment leg)
