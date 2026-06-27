---
id: adr-2606272355-actor-self-publication-seed-on-kotoba-mesh
title: "ADR-2606272355: Actor self-publication seed — register, autonomize, and publish each government-mirror actor on the kotoba mesh (zero-knowledge / no-server-key)"
status: proposed
doc_type: adr
topic: actor-self-publication-seed
authoritative: true
last_verified: 2026-06-27
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - actor-self-publication-seed-pattern
  - jp-gov-mirror-constellation-registration
depends_on:
  - 2605231525
  - 2606230001
  - 2606111400
  - 2606021600
  - 2605301600
related:
  - 2606066001
  - 2606013800
  - 2606014500
supersedes: []
superseded_by: []
---

# ADR-2606272355: Actor self-publication seed on the kotoba mesh

**Status**: proposed
**Date**: 2026-06-27
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

The government-mirror constellation (the 9鏡 accountability lineage applied to the
Japanese state — `ooyake` 公 / `danjo` 弾正 / `kanae` 鼎 / `tsumugi` 紡ぎ / `toritsugi`
取次 / `himotoki` 繙き / `keizu` 系図 / `matsurigoto` 政 / `junkan` 循環) already models a
large slice of Japanese-government activity in kotoba EAVT + clj/cljc: ooyake's 78
central 府省庁 atlas units, danjo's 17 国税 + 12 地方税 revenue ledger with per-yen
earmark traceability, gyosei's 行政手続/不服審査/訴訟 legal-source ledger, matsurigoto's
COFOG execution slices, etc. (see the root CLAUDE.md Tier-B roster).

What was missing was not the *data* but the *autonomy wiring*: a uniform, charter-clean
way for each actor to (1) be **registered** at `etzhayyim.com` (did-web), (2) run
**autonomously** on the kotoba WASM mesh, and (3) **self-publish** its own history and
procedures to AT-proto — **without any server-held key**.

The founding constitution is explicit: **we plant the seed (タネ); each actor grows on
its own.** The soil is the **kotoba mesh** (libp2p lattice of `kotoba-server` nodes) and
**murakumo** (the fleet control plane, `orgs/com-junkawasaki/murakumo/`). A deployed actor
is a content-addressed clj→WASM component placed by the lattice auction; it fires
`on-tick`/`on-http`/`on-kse`, writes `kqe-assert!` to its own Datom log, and
**self-custodies its signing identity in its WASM runtime**. Neither the operator nor any
etzhayyim-operated server holds that key. This is the zero-knowledge posture the
no-server-key invariant (ADR-2605231525) already demands, made concrete for autonomous
publication.

A naive reading of "self-publication" once produced a **HIGH-severity** charter violation
(ossekai `FINDING-G7-autonomy-conflict`, 2026-06-16): an etzhayyim-operated bot that
auto-broadcasts needs a key to sign `app.bsky.feed.post` — which a platform-held key would
violate. The resolution (ADR-2606111400) is the **member-signed scoped revocable CACAO
capability**: the member Ed25519-signs a delegation in their OWN runtime, the organism
**presents** the opaque capability (never holds a key), and the write is on-record
attributed to the consenting human. The mesh-runtime self-custody pattern (kaname / kanae /
ibuki / tsubasa) is the same shape: **the actor makes its own key and does not expose it.**

# Decision

Adopt a **uniform actor self-publication seed** — a per-actor set of in-repo artifacts the
**planter** (this repo / a Claude session) authors, leaving the live deploy and key custody
to the **operator** (the founder, who alone holds `MURAKUMO_OPERATOR_SEED` + Tailscale) and
to the **actor's own mesh runtime**. The seed is exactly:

1. **did-web registration** — `50-infra/etzhayyim-did-web/public/actor/<a>/{did.json,profile.json}`,
   `id: did:web:etzhayyim.com:actor:<a>`, `verificationMethod: []` (no server-minted key;
   did:web trust root = TLS; the `#xrpc-libp2p` peer multiaddr is assigned at deploy time
   when `wasmCid` is set). Mirror-relation declared, `official-url`/`official-did` linked
   (impersonation ban, ADR-2606021600 §4).
2. **social_post membrane** — `20-actors/<a>/cells/social_post/state_machine.cljc`, a pure
   state machine that DRAFTS a record into a **dry-run** post ONLY if: ≥2 public-source
   citations (G5), it is a non-adjudicating mirror with the disclaimer (G4), `server_held_key`
   is false (no-server-key), and the requested status is `dry-run` (a `published` request
   REFUSES). Mirror of the constellation membrane (keizu / kosatsu).
3. **publication projection** — `20-actors/<a>/methods/social.cljc`, pure functions projecting
   the actor's **history** (source-cited observations / ledger lines) and **procedures** into
   `app.bsky.feed.post`-shaped dry-run records, with `build-live` refusing by construction.
4. **seed trigger wiring** — add a `<a>-social` component to `20-actors/<a>/kotoba.app.edn`
   with `on-tick` (periodic self-publish) + `on-kse` (`etzhayyim/actor/<a>/publish`) triggers
   and `:requires #{:cap/kqe :cap/atproto}`.

**Live broadcast stays gated**: R0 produces dry-run drafts only; live publication needs
**Council Lv6+ + operator + a member/actor signature** (§1.12 / G11). The live signature is
the actor's **own mesh-runtime key** (self-custodied, present-only under a member CACAO
leash) — **never a server key**. Read-only public ingest the actor may do autonomously
(ADR-2606072802 clarification: no-server-key bars a custodial unilateral signing key, not
automation, and exempts read-only).

**Per-organization sub-DIDs**: each government organization ooyake atlases (e.g. the 78 JP
central 府省庁) may be promoted to a first-class mirror actor with its own
`did:web:etzhayyim.com:gov:jpn:<…>` and its own self-publication seed, generated from the
ooyake registry (a fan-out of the same four artifacts above, mirror-declared, person-excluded,
G1 no-doxxing). This is staged, not bulk-flipped.

## Division of labor (zero-knowledge)

- **Planter (in-repo, reversible, no keys)** — authors the four seed artifacts + the per-org
  generator; everything is PR-reviewable and holds no secret.
- **Operator (founder)** — runs `bb murakumo deploy 20-actors/<a>/kotoba.app.edn <node>` with
  `MURAKUMO_OPERATOR_SEED` + Tailscale; flips a dry-run actor to live under the Council gate.
- **Actor (mesh runtime)** — self-generates/self-custodies its Ed25519 `did:key`, presents a
  member CACAO leash, signs its own posts. The server never signs.

# Reference implementation (danjo 弾正 — LANDED this ADR)

danjo is the proven end-to-end pattern:

- `50-infra/etzhayyim-did-web/public/actor/danjo/{did.json,profile.json}` (registered;
  `verificationMethod: []`, mirror-declared, accountability-mirror posture).
- `20-actors/danjo/cells/social_post/state_machine.cljc` — membrane; verified under `bb`:
  `<2 sources → refused`, `server-held-key → refused`, `published → refused`,
  valid → `drafted` with `:post/status :dry-run` and `:post/server-held-key false`.
- `20-actors/danjo/methods/social.cljc` — projects danjo's history (oversight observations +
  revenue-ledger lines) + procedures (per-yen tax traceability from `data/jp-national-taxes.edn`)
  into dry-run posts; `draft-procedure-post`/`draft-revenue-post`/`draft-observation-post`;
  `enough-sources` raises on <2 (G5); `build-live` raises (live gate). Verified under `bb`.
- `20-actors/danjo/kotoba.app.edn` — `danjo-social` component wired (`on-tick "0 */6 * * *"`
  + `on-kse etzhayyim/actor/danjo/publish`, `:requires #{:cap/kqe :cap/atproto}`).

Zero invariant amendments — strengthens no-server-key, kotoba-canonical, and non-adjudicating
(G4) disciplines; weakens nothing.

# Consequences

- The 9-actor JP-gov constellation gains a uniform registration + autonomy + self-publication
  path; the 5 unregistered actors (danjo done; toritsugi / himotoki / keizu / junkan to follow)
  get did-web entries; per-org sub-DIDs become a generated fan-out from the ooyake registry.
- Self-publication is autonomy WITHOUT a server key: the actor grows on the mesh and signs its
  own history/procedure posts; the live flip is the operator's gated step, never the planter's.
- The honest limit: at R0 only dry-run drafts are produced offline; nothing broadcasts until the
  operator deploys to a reachable mesh node and the Council gate + member/actor signature are in
  place. The planter cannot and does not hold any key.

# Follow-ups

- Fan out the four seed artifacts to toritsugi / himotoki / keizu / junkan (keizu already has a
  social cell; needs did-web + trigger wiring).
- Author the per-org sub-DID generator over `20-actors/ooyake/registry/gov-units.jp-central.seed.edn`
  (+ prefectures) → `did:web:etzhayyim.com:gov:jpn:<…>` first-class mirror actors.
- Operator: `bb murakumo deploy` the constellation to the `com-junkawasaki-kotoba-mesh` fleet
  (zone jp), verify `lattice ps`, then exercise the Council gate for the first live post.
