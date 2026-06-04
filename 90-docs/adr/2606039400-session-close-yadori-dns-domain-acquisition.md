---
id: adr-2606039400-session-close-yadori-dns-domain-acquisition
title: "ADR-2606039400: Session close — yadori (宿り) DNS-availability + domain-acquisition actor (R0)"
status: active
doc_type: adr
topic: session-close-yadori-dns-domain-acquisition
authoritative: true
last_verified: 2026-06-03
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Documentation-only session-close. Authoritative design = ADR-2606038400. Records the build + the empirical RDAP verification behind the 「DNS の空きを確認・予約する actor は設計されているか」 question."
authoritative_for:
  - session-close-2606039400
depends_on:
  - adr-2606038400-yadori-dns-availability-and-domain-acquisition
related:
  - adr-2606012100-okaimono-provisioning-commons
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605222330-etzhayyim-com-substrate-violation-transition-window
  - adr-2606013800-actor-profile-and-dynamic-did-json
supersedes: []
superseded_by: []
---

# ADR-2606039400: Session close — yadori (宿り) DNS-availability + domain-acquisition actor

**Status**: active
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

Origin question (from a GoDaddy ad link): *「DNS の空きを確認、予約を行う actor は設計されている?」*
The honest answer at the time was **no** — domain handling was a manual Cloudflare-Registrar action
(`etzhayyim.com`, ADR-2605222330) plus a Squarespace→CF *transfer* module in magatama; there was no
availability check and no acquisition actor between minting an actor DID and the name existing.

This session designed and built that actor, **yadori (宿り)**, as the charter-clean inverse of a
retail registrar. Authoritative design = **ADR-2606038400**.

# Decision

Documentation-only closure recording what shipped this session. No invariant amendments.

**Shipped — Tier-B actor `20-actors/yadori/` (R0):**

- **Design + governance**: `manifest.edn` / `manifest.jsonld` (DID `did:web:etzhayyim.com:actor:yadori`,
  glyph 宿, 9 gates G1–G9, 5 non-goals N1–N5, roadmap R0→R3), `CLAUDE.md`, `README.md`.
- **5 cells** (langgraph→WASM, Murakumo-only, `.solve()` raises at R0): **`availability_check`**
  (coded — wraps the RDAP classifier) · `name_suggest` · `registrar_quote` · **`reservation`**
  (coded reference cell) · `dns_provision`.
- **Empirical method** `methods/availability.py` (stdlib only): IDN/punycode normalization,
  `:representative` IANA RDAP bootstrap, RDAP-URL construction, status→availability classification,
  cross-TLD alternatives; descriptive RDAP `User-Agent` (PIR/.org 403s a bare request).
- **`availability_check` cell** orchestrates normalize → resolve-rdap → classify → record; the
  **live RDAP fetch is wired but G7-gated** — it fires only when an operator passes
  `operator_gate=True` AND the process env `YADORI_ALLOW_LIVE_RDAP=1` is set; otherwise offline
  (fixture or `:unknown`, never a socket, never a guessed `:available`, G8).
- **`reservation` cell** state machine enforces the constitutional shape purely: **G2** member-
  principal (yadori never the buyer; okaimono assisted-checkout, ADR-2606012100; §1.3 preserved) ·
  **G3** Cloudflare-registrar-default (GoDaddy/external fiat-markup Council-gated) · **G5** no-server-
  key (member signs; server signature refused, ADR-2605231525) · **G6** no-squatting (held-trademark
  + confusable + speculation screen).
- **Vocab + lexicons**: `kotoba/schema.edn` + `seed.edn`, `data/registrar-registry.kotoba.edn`,
  5 lexicons `com.etzhayyim.yadori.*` (EDN + JSON mirrors under `00-contracts/lexicons/`),
  primary ontology `00-contracts/schemas/dns-domain-ontology.kotoba.edn`.
- **Registration**: `actor-profile-seed.kotoba.edn` (yadori entry), root `CLAUDE.md` Tier-B table
  row, `90-docs/adr/README.md`, `deps.toml` `[[adrs]]`.

**EMPIRICAL.** **31 tests green** (11 RDAP classifier + 20 cell state-machine: availability_check
G7 live-gate + reservation G2/G3/G5/G6). The gated live RDAP path was verified read-only across
`.com` / `.org` / `.dev`: `example.com` + `etzhayyim.com` + `wikipedia.org` → **registered**;
unregistered names → **available**.

> Note on the test harness: the repo's pytest plugin environment is currently broken (`pydantic` /
> `langsmith` version mismatch in site-packages, unrelated to this work); the suites run clean with
> `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.

# Consequences

Availability checking is usable today (offline + operator-gated live); acquisition reuses the
ratified okaimono member-principal pattern, so no new payment primitive and no §1.3 amendment. The
substrate is kept off cybersquatting/speculation by the G6 screen.

**Honest R0 / not done:** no live registration (intent only — G7); `name_suggest`/`registrar_quote`/
`dns_provision` are `.edn`-defined but not coded (Murakumo wiring + okaimono settlement deferred);
RDAP bootstrap is a bounded `:representative` subset (unsupported TLD → `:unsupported-tld`); cells'
`.solve()` raise until a Council activation ADR. Not committed at session close (working tree under
`20-actors/yadori/` + `00-contracts/` + docs).

# Alternatives Considered

Covered in the design ADR (2606038400 §Alternatives): a fiat registrar integration; folding into
okaimono as a SKU; extending magatama `dns.py`; WHOIS port-43 scraping; server-held registrar
credentials — all rejected for the reasons recorded there.

# References

- ADR-2606038400 — yadori DNS-availability + domain-acquisition (authoritative design)
- ADR-2606012100 — okaimono provisioning commons (member-principal assisted-checkout)
- ADR-2605231525 — no platform-held signing key (G5)
- ADR-2605222330 — etzhayyim.com substrate transition (manual CF Registrar registration)
- ADR-2606013800 — actor profile + dynamic did.json
