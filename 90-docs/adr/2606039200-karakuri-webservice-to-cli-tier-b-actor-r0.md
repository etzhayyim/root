---
id: adr-2606039200-karakuri-webservice-to-cli
title: "ADR-2606039200: karakuri (絡繰) — web-service-to-CLI Tier-B actor (R0)"
status: proposed
doc_type: adr
topic: karakuri-webservice-to-cli
authoritative: true
last_verified: 2026-06-03
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/karakuri
  - com.etzhayyim.karakuri.*
depends_on:
  - "2606012100"
  - "2605231525"
  - "2605215000"
  - "2605181100"
  - "2605192200"
related:
  - "2606038400"
  - "2606033600"
  - "2605302130"
  - "2605312030"
  - "2606013800"
supersedes: []
superseded_by: []
---

# ADR-2606039200: karakuri (絡繰) — web-service-to-CLI Tier-B actor (R0)

**Status**: proposed
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

The triggering reference: **`clianything.org`** — a commercial service that wraps GUI-only web
services (Squarespace, Notion, Wix, …) behind a uniform command-line / programmatic interface, so a
human (or an agent) can *script* a service that the vendor ships only as a point-and-click GUI. The
request: *「squarespace のような webservice も CLI にする actor を設計して」.*

This is squarely the labor-liberation mission (CLAUDE.md §Mission, ADR-2605192100): GUI-only SaaS is
a vast reservoir of **manual clicking toil** — re-keying the same form, exporting a CSV by hand,
copy-pasting between two dashboards. A CLI handle turns that toil into a one-line command and a
replayable script. This is the **software-actor analogue of the karakuri-kaizen** the factory wave
already embraces (the Toyota sense: clever, low-cost automation that removes manual labour) — hence
the name **絡繰 (karakuri)**, *the mechanism that drives a manual service by command*.

But a literal clone of `clianything.org` would import several constitutional violations, the same way
a literal GoDaddy clone would (yadori, ADR-2606038400) or a literal Amazon clone would (okaimono,
ADR-2606012100). karakuri is the **inversion**, not the clone:

1. **Scraping / surveillance shape.** A generic "drive any website" tool trivially becomes a
   third-party scraper / surveillance harvester. karakuri operates **only the member's OWN
   authenticated accounts** (member-principal), never harvests third-party data — the same boundary
   as himotoki own-data-only (ADR-2605302130) and toritsugi self-submit (ADR-2605312030).
2. **Detection-evasion / anti-bot circumvention.** The commercial "automate anything" pitch slides
   into captcha-farming, rotating-proxy cloaking, and rate-limit circumvention — exactly the
   malicious-automation patterns the operating policy forbids. karakuri **prefers the official API**,
   uses headless-browser automation **only where the service's ToS permits it**, and never evades
   bot-detection.
3. **Server-held credentials.** A SaaS-CLI vendor stores your service passwords/tokens on its servers
   ("connect your account"). That is precisely the platform-held-key anti-pattern. karakuri holds
   **no** member credential or session (G5 / ADR-2605231525); secrets live with the member-operator,
   encrypted, and the member signs every mutating action.
4. **Opaque action log.** A vendor agent acts on your account and you cannot audit what it did.
   karakuri records **every planned and executed operation as kotoba Datoms** (`as-of`, replayable):
   the member can see exactly which command touched their account and when.

Framed positively, karakuri is an **anti-lock-in / data-portability** tool: it gives a member
programmatic, scriptable, **exportable** control over services that deliberately trap them in a GUI —
the structural-liberation inverse of vendor lock-in, the way okaimono inverts Amazon.

# Decision

Create **karakuri (絡繰)**, a Tier-B R0 actor at `did:web:etzhayyim.com:actor:karakuri`.

**Mission.** Give a member a uniform **CLI / command vocabulary over heterogeneous web services**,
driving **the member's own account** through the safest available adapter, recording every operation
to the kotoba Datom log, and prioritising **data portability** (export/round-trip) over deeper lock-in.

**The uniform vocabulary — `ServiceOp`.** One normalized op shape across all services (one vocab, two
runtimes — the sumitsubo `ModelOp` pattern, ADR-2606033600): `service` · `noun` · `verb` ·
`args` · a classified **safety** (`:read` / `:create` / `:update` / `:delete`) and a **destructive**
flag. A CLI string `karakuri <service> <noun>.<verb> [--flags]` parses into exactly one `ServiceOp`.

**Three adapter tiers (safest-first, per service):**

- **T1 official-API adapter** *(preferred)* — the service's published API (Squarespace API, Notion
  API, Shopify Admin API, Stripe API, GitHub API, …). Stable, ToS-sanctioned, rate-limit-documented.
- **T2 headless-browser adapter** — Playwright/Puppeteer-shape automation of the member's GUI
  session, **only when the service has no usable API AND its ToS permits automation** (G2). Never
  used to evade bot-detection.
- **T3 structured-export adapter** — import/export round-trip (the data-liberation leg): pull the
  member's own data out into a portable, kotoba-native form; push it back or into another service.

**Per-service capability + ToS registry** (`data/service-registry.kotoba.edn`, `:representative`):
each service records official-API availability, auth model, **ToS automation stance**
(`:api-ok` / `:automation-allowed` / `:automation-restricted` / `:automation-prohibited`),
rate-limit, and the selected tier. The ToS stance is the T2 gate.

**Cells (5; langgraph → WASM; Murakumo-only; `.solve()` raises at R0):**
`service_resolve` · `command_plan` · **`session_broker`** (coded reference cell) · `adapter_invoke`
· `export_roundtrip`.

**Gates (immutable R0→R3):**

- **G1 member-principal / own-account-only** *(defining)* — karakuri drives **only** accounts the
  member owns and has authenticated; **no** third-party-account access, **no** harvesting of other
  people's data, **no** "scrape this site" product. Mirrors himotoki own-data-only.
- **G2 official-API-preferred / ToS-honest** *(defining)* — prefer the official API (T1);
  headless-browser (T2) is permitted **only** where the service's ToS allows automation; **no
  detection-evasion** of any kind (no captcha-solving-as-evasion, no rotating-proxy/IP cloaking, no
  rate-limit circumvention); robots/rate-limit/backoff respected. A service marked
  `:automation-prohibited` refuses T2 by construction.
- **G3 no-server-key** — the member's service credentials/sessions are held by the member-operator,
  encrypted (`com.etzhayyim.encrypted.*`, ADR-2605181100), **never** platform-held; every mutating
  op is authorized by a **member signature** and a server signature is refused (ADR-2605231525).
- **G4 murakumo-only** — NL → command planning via LiteLLM `127.0.0.1:4000` only (ADR-2605215000).
- **G5 read-default / mutate-gated** — `:read` and `:export` ops ship at R0; `:create` / `:update` /
  and especially **destructive `:delete`** ops are member-sig + explicit dry-run-confirmed, and live
  execution is Council Lv6+ + operator gated (G6).
- **G6 outward-gated** — **any** live network call to a third-party service (every adapter
  execution, T1/T2/T3) is Council Lv6+ + operator gated; R0 = offline parse / plan / dry-run only.
- **G7 kotoba-EAVT audit** — every planned and every executed `ServiceOp` is written to the kotoba
  Datom log (`as-of`, replayable); the member can audit exactly what touched their account.
- **G8 sourcing-honesty** — `:representative` service registry; bounded subset; unknown service or
  unknown op degrades honestly (`:unknown-service` / `:unsupported-op`), never guesses.
- **G9 PII / portability-consent** — exported member data is consent-bound + encrypted
  (`com.etzhayyim.encrypted.*`); export is the member's own data only; no third-party PII collection.

**Non-goals:** N1 not a scraper / surveillance / third-party-data-harvesting tool · N2 no
detection-evasion / anti-bot circumvention / captcha-farming / proxy-cloaking · N3 no
credential-stuffing / account-takeover / shared-or-borrowed-account abuse · N4 no paywall / license /
DRM circumvention or content piracy (the portability goal is the member's **own** data, not others'
gated content) · N5 not a bot-farm / mass-automation / spam / fake-engagement engine · N6 no driving
of prohibited-content or third-party ad / affiliate systems (Charter-Rider §2(a)–(h), ADR-2605192200).

**Empirical artifact.** `methods/command.py` (stdlib only): a `ServiceOp` parser/planner — parses a
`karakuri <service> <noun>.<verb> [--flags]` command line into a normalized op, resolves the service
against the `:representative` registry, **classifies safety** (`:read`/`:create`/`:update`/`:delete`
+ destructive), **selects the adapter tier** (official-API-first), enforces the **ToS gate** (refuses
T2 on an `:automation-prohibited` service, G2) and the **mutate gate** (mutating ops require member
authorization, never auto-confirmed, G5), and emits an offline **dry-run plan** (no network, G6).
Tests in `methods/test_command.py`. The defining `session_broker` cell's state machine enforces
G1/G2/G3/G5 purely and is unit-tested (`cells/test_state_machines.py`); `.solve()` raises until a
Council activation ADR.

# Consequences

**Positive.** Answers the `clianything.org`-shaped request with a charter-clean design: members get a
scriptable, auditable, portable handle over GUI-only SaaS, and the toil of manual dashboard-clicking
becomes one-line, replayable, kotoba-logged commands — a direct labor-liberation win. The
official-API-first + ToS-honest + no-server-key + own-account-only stance keeps karakuri off every
malicious-automation pattern by construction. The parser/planner is genuinely usable today (offline
plan/dry-run); the data-portability (T3) leg directly serves anti-lock-in.

**Negative / risk.** R0 ships no live execution (plan/dry-run only) — a real operation still needs
operator + Council action (G6). The service registry is a bounded `:representative` subset; an
unknown service degrades to `:unknown-service` (G8). T2 browser automation is fragile (GUI/DOM
churn) and is deliberately the **last** resort, gated on a per-service ToS stance that an operator
must keep current — a stale `:api-ok` marker could mis-route. Member-principal + no-server-key means
karakuri cannot "just do it" unattended; that friction is intentional (G1/G3). Real adapter SDKs,
the encrypted session vault, and live OAuth flows are deferred to R1+.

# Alternatives Considered

1. **Clone `clianything.org` (server-held creds, drive-anything, generic scraping).** Rejected —
   imports the four violations in Context (scraping shape, detection-evasion, server-held keys,
   opaque log). karakuri is the inversion.
2. **Browser-automation-only (always T2 headless).** Rejected — fragile, ToS-risky, and ignores the
   stable official APIs most target services publish. T1-first with T2 as a gated last resort is the
   safe order.
3. **Fold into okaimono / a generic "integrations" cell.** Rejected as the home — okaimono is the
   provisioning commons (catalog/checkout), not a service-control plane; karakuri *reuses* okaimono's
   member-principal + no-server-key invariants but owns a distinct surface (`ServiceOp`, adapters,
   per-service ToS gating, export round-trip).
4. **Server-held OAuth tokens for one-click convenience.** Rejected — violates G3 / ADR-2605231525
   no-server-key; the member holds the credential and signs each mutate.
5. **A REST/MCP gateway instead of a CLI vocabulary.** Deferred, not rejected — the normalized
   `ServiceOp` is transport-agnostic; an MCP/XRPC surface can re-export the same vocab at R1+. R0
   fixes the vocabulary and the gates first.

# References

- ADR-2606012100 — okaimono provisioning commons (member-principal + no-server-key invariants reused)
- ADR-2605231525 — no platform-held signing key (G3)
- ADR-2605215000 — Murakumo-only inference (G4)
- ADR-2605181100 — `com.etzhayyim.encrypted.*` envelope (G3 session secrets, G9 export PII)
- ADR-2605192200 — Apache-2.0 + Charter-Rider v2.0 §2(a)–(h) (N6 prohibited-use scan)
- ADR-2606038400 — yadori (the registrar inversion; same "invert the retail tool" pattern)
- ADR-2606033600 — sumitsubo (the one-vocab-two-runtimes `ModelOp` pattern, mirrored as `ServiceOp`)
- ADR-2605302130 — himotoki own-data-only (G1 member-principal prior art)
- ADR-2605312030 — toritsugi self-submit-default (member-principal concierge prior art)
- ADR-2606013800 — actor profile + dynamic did.json (apex Worker issues `did:web:…:karakuri`)
