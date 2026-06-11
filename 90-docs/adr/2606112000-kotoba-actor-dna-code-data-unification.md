---
id: adr-2606112000-kotoba-actor-dna-code-data-unification
title: "ADR-2606112000: Actor DNA — binding kotoba CODE + DATA into one content-addressed unit (Holochain-/Ethereum-iso)"
status: accepted
doc_type: adr
topic: actor-dna-code-data-unification
authoritative: true
last_verified: 2026-06-11
priority: 4.0
axis: architecture
weight: 0.4
priority_note: "Defines the Actor DNA manifest: one content-addressed unit binding an actor's WASM code + data graph + integrity rules + lexicon, so kotoba gains the code+data co-location Ethereum (account) and Holochain (DNA hash) have. R0 = client/actor-tier (this repo): manifest + content-addressed integrity ruleset + deploy descriptor, pure-stdlib, 33 tests. Engine-tier enforcement (kotoba transact validates before commit) is the gated follow-up in the 40-engine/kotoba submodule."
authoritative_for:
  - the Actor DNA manifest format (kotoba-actor-dna/v0)
  - the integrity ruleset format (kotoba-integrity/v0) — client-tier data validation
  - the actor deploy descriptor (kotoba-actor-deploy/v0)
depends_on:
  - adr-2606013800
  - adr-2606014500
  - adr-2606015400
  - adr-2605312345
  - adr-2606111400
  - adr-2606091500
related:
  - adr-2606015600
  - adr-2606036000
  - adr-2605231525
supersedes: []
superseded_by: []
---

# ADR-2606112000: Actor DNA — binding kotoba CODE + DATA into one content-addressed unit

- **Status**: accepted (R0 — client/actor tier landed; **engine-tier enforcement LANDED 2026-06-11** via the kotoba submodule bump, see Update below; only true single-tx atomic deploy remains gated)
- **Date**: 2026-06-11 (JST)
- **Deciders**: founder seat (「いまの kotoba, kotobase の設計では ethereum, holochain のように
  コードとデータが一体化して deploy できている?」→ "ok, do it")

## Context

A code-read of the current design (ADR-2606013800 actor-profile + dynamic did.json, ADR-2606014500
"One Worker many WASM actors", ADR-2606015400 content-addressed did.json, ADR-2605312345 Datom-log-
as-canonical-state, and the live `40-engine/kotoba` submodule) found that kotoba **content-addresses
both code and data and re-verifies both on load** (the trustless half — equal to Ethereum bytecode-
CID and Holochain DNA-hash), but does **not** unify them the way those systems do:

1. **No single binding ID.** A WASM program CID, the data-graph CID, the validation rules, and the
   lexicon are **four separate content-addresses** linked only by references inside `did.json`.
   Ethereum binds bytecode + storage at one account; Holochain binds WASM zomes + integrity rules +
   the DHT at one DNA hash. kotoba had no equivalent.
2. **No code-defined data validation.** The kotoba transact / `kg.ingest` path is **append-only with
   CACAO auth** (verified in `40-engine/kotoba/crates/kotoba-server/src/kg.rs` — auth check, no
   `validate()` hook). CACAO governs *who* may write; nothing governs *what* is written. Holochain's
   integrity zomes validate every entry before it lands in the DHT; kotoba's integrity was an
   operational gate (G7/Council), not structural.
3. **Non-atomic deploy.** Deploying an actor is several uncoordinated operations (pin WASM, ingest
   actor profile, pin did.json) at separate times — no single artifact says "deploy THIS actor".

## Decision

Introduce the **Actor DNA manifest** — one canonical-EDN object binding an actor's code + data +
rules + lexicon, content-addressed to a single **DNA CID** that becomes the actor's identity.

### 1. The DNA manifest (`kotoba-actor-dna/v0`)

```
{:dna/spec "kotoba-actor-dna/v0"
 :dna/actor-did   "did:web:etzhayyim.com:actor:<h>"
 :dna/wasm-cid    "bafkrei…"   ; CODE  (raw CID, ipfs add --raw-leaves)
 :dna/graph       "<name>"     ; DATA  (the graph this code governs)
 :dna/graph-cid   "bafyrei…"   ; DERIVED = graph_cid(:dna/graph), ASSERTED + re-checked by verify
 :dna/validation-cid "bafkrei…"; the integrity ruleset
 :dna/lexicon-cid "bafkrei…"
 :dna/capability  "datom:transact"}
```

`dna_cid(manifest)` = the raw CIDv1 of the canonical EDN bytes (byte-identical to
`ipfs add --cid-version=1 --raw-leaves`; pinnable to kotobase.net, ADR-2606091500). **`did.json`
points at `ipfs://<dna-cid>` and nothing else.** Change any part → a new wasm/validation/graph CID
→ a new DNA CID → a different actor. Code and data are fused into one tamper-evident hash. The
`:dna/graph-cid` is **derived** from `:dna/graph` and re-checked by `verify()`, so the manifest
*asserts* "this code governs THIS graph" rather than implying it via a separate reference.

### 2. The integrity ruleset (`kotoba-integrity/v0`) — the integrity-zome analogue

A content-addressed ruleset (its raw CID = `:dna/validation-cid`) + `validate(datoms, rules)` that
**rejects** non-conforming datoms before a push: `:integrity/append-only` (only `:db/add`),
`:integrity/closed-attrs` (closed vocabulary), `:integrity/attr-types`, `:integrity/deny-attrs`
(structurally forbidden, e.g. ibuki never asserts `:published`), `:integrity/required-attrs`, and
graph-binding. Because the ruleset is content-addressed inside the DNA, editing a rule changes the
DNA CID — integrity is tamper-evident, not policy-by-convention.

### 3. The deploy descriptor (`kotoba-actor-deploy/v0`) — atomicity of identity

An ordered, content-addressed plan — **pin code → pin validation → pin lexicon → pin manifest →
graph-genesis → did-link** — where every step carries the one DNA CID (content pinned *before* the
identity that references it). Execution chains via `expected_parent` (the optimistic-concurrency
primitive ibuki's `kotoba_bridge` already uses). A partially-applied or tampered deploy fails to
reproduce the DNA CID end-to-end.

### Implementation (R0, this repo)

`50-infra/actor-dna/` — pure-stdlib `cid.py` / `dna.py` / `integrity.py` / `deploy.py`, **33 tests /
4 hermetic suites green**. `cid.py` is cross-checked **byte-identical** vs `20-actors/rasen/methods/
cid.py`, and `graph_cid("ibuki")` equals the live engine's graph CID
(`bafyreif6qopha4iwoj2dqbxua3ne3kj7z4qeyjs442yaztjwtqqt2jimba`, observed in the ADR-2606111400
delegation live test). Schema: `00-contracts/schemas/actor-dna.kotoba.edn`.

## Consequences

- kotoba actors gain a **single canonical identity** (the DNA CID) that fuses code + data + rules +
  lexicon — the Holochain-DNA / Ethereum-account property previously absent.
- Data integrity becomes **structural and content-addressed** at the actor tier (the ruleset is part
  of the actor's hash), not merely an operational gate.
- No substrate-ordering change: the Datom log stays first-class canonical state (ADR-2605312345);
  IPFS/kotobase stay the content-addressed block tier; the DNA manifest is just another block.
- Ties together this session's work: the DNA's `:dna/capability` is the ibuki CACAO leash
  (ADR-2606111400); its blocks pin to kotobase.net (ADR-2606091500).

## Honest scope / follow-up

- **Enforced now (client/actor tier):** `integrity.validate()` rejects before `kotoba_bridge.push`.
- **Engine tier — LANDED 2026-06-11 (kotoba submodule `92461b73` → `e3e07439`):** the kotoba
  `datomic.transact` path now validates incoming datoms against a graph's registered DNA integrity
  ruleset *before commit*, so a **peer's** writes are checked too — full Holochain integrity-zome
  parity. `crates/kotoba-server/src/dna_integrity.rs` (`IntegrityRuleset` / `parse_ruleset` /
  `validate_tx` + a node-config registry from `KOTOBA_DNA_RULES`, authoritative server-side, never
  caller-supplied; **no-op + backward-compatible** when no ruleset is registered) + a call in
  `datomic_transact` (422 on violation). 7 Rust unit tests pass; kotoba-server builds clean.
  Upstream record: etzhayyim/kotoba PR #103. The content-addressed ruleset + DNA CID are what make
  this trustless — the actor tier and the engine tier enforce the **byte-identical** ruleset.
- **Still gated:** **true single-tx atomic deploy** (the deploy descriptor gives atomicity-of-identity;
  one atomic block is a deeper engine change). The integrity half of the gap is now closed at both tiers.

## Update — engine-tier enforcement landed (2026-06-11)

The "gated follow-up" above is done for the integrity half. `datomic.transact` validates against the
graph's DNA ruleset before commit (`KOTOBA_DNA_RULES` registry). This means code now governs WHAT is
written into a graph, not only CACAO governing WHO — the Holochain integrity-zome property, at the
engine. With the actor-tier (PR #1610), the tsumugi real-DNA proof (PR #1612), and this engine-tier
hook, kotoba now matches Ethereum/Holochain on **all** of: content-addressed code+data, re-verify on
execute, a single DNA CID fusing code+data, and code-defined data validation. The one remaining
divergence is multi-step (not single-tx) deploy.

## Alternatives Considered

- **Leave code + data as separate did.json references** → rejected: that is exactly the
  no-single-binding gap; a four-CID actor cannot be reasoned about or deployed as one unit.
- **Put validation only in each actor's hand-rolled code** (status quo — ibuki/rasen each re-encode
  append-only/closed-vocab by hand) → rejected: not content-addressed, not tamper-evident, not
  shareable; the ruleset belongs in the actor's hash.
- **Patch the kotoba engine now for engine-tier enforcement** → deferred: the engine is a separate
  submodule repo; a Rust change there cannot be built/tested in this repo's CI. Shipped the
  content-addressed spec + client-tier enforcement first; engine enforcement is the gated next step.
