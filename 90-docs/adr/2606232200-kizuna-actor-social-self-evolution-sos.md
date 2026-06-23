---
id: adr-2606232200-kizuna-actor-social-self-evolution-sos
title: "ADR-2606232200: kizuna 絆 — actor-to-actor ATProto social-interaction self-evolution + SoS optimization"
status: proposed
doc_type: adr
topic: kizuna-actor-social-sos
authoritative: true
last_verified: 2026-06-23
priority: 4.0
axis: architecture
weight: 0.50
priority_note: "Actors interact over ATProto (follow/mention/like/post) → self-evolution loop → system-of-systems flow optimization"
authoritative_for:
  - 20-actors/kizuna
depends_on:
  - adr-2606232100-atproto-actor-registration-root-and-subdids
  - adr-2606172100
  - adr-2606201200
related:
  - adr-2605264000
  - adr-2606211752
supersedes: []
superseded_by: []
---

# ADR-2606232200: kizuna 絆 — actor-to-actor ATProto social-interaction self-evolution + SoS optimization

**Status**: proposed
**Date**: 2026-06-23
**Deciders**: Jun Kawasaki

## Context

ADR-2606232100 made etzhayyim's root, agents, and ~8,888 kagami mirrors **registered
ATProto actors** that can post. Once they post, they can also **follow / mention / like /
reply** each other over the ATProto social protocol (XRPC). That actor-to-actor
interaction is a graph — and a graph the collective can **optimize over** to grow.

The substrate already has the pieces but not the loop:
- **kaname 要** runs system-of-systems (SoS) leverage over EXTERNAL-entity mirrors.
- **ibuki 息吹** runs the organism autonomy / co-scientist loop (sense→act→learn).
- **ossekai 御節介** is the consent-bound actuator.

What is missing is the **INTERNAL-actor** SoS: treat etzhayyim's own actors interacting
over ATProto as a multiplex social graph, and feed that graph into a self-evolution loop
that optimizes the society's collective flow (系流最適化) — who should connect, where the
society is fragile, which actor is isolated.

## Decision

Add **`kizuna 絆`** (`20-actors/kizuna/`, clj/bb over the kotoba Datom log) — the
internal-actor sibling of kaname. One **beat** of its loop:

```
perceive(social events: follow/mention/like/post via XRPC)
  → graph   (multiplex social graph: typed weighted ties + 相互 reciprocal pairs)
  → assess  (SoS metrics: integration, reciprocity, Brandes betweenness, 律速 actor, isolated set)
  → propose (dry-run, reciprocity/connectivity-improving tie PROPOSALS → ossekai)
  → learn   (per-actor GROWTH signal each actor folds into its own optimization)
  → persist (content-addressed append-only kotoba commit-DAG; idempotent heartbeat)
```

`kizuna.methods.kizuna` (R0, pure + deterministic) implements `graph` / `assess` /
`tie-proposals` / `beat`, reusing kaname's exact-Brandes betweenness idiom over the
actor network. Live ATProto ingest of the real interaction firehose + the kotoba live
bridge are G7/G8-gated legs (the kaname/tsubasa read-only fetch pattern).

### Constitutional gates (in code + tests)

- **G1 PROPOSE-not-act.** kizuna emits `:tie/proposed` (`:status :dry-run`,
  `:route :ossekai`). There is **no execute / auto-follow** path (unrepresentable);
  actuation is ossekai + a member CACAO leash (no-server-key, ADR-2606072802). kizuna
  never follows / likes / posts on its own.
- **G2 RECIPROCITY-positive, ANTI-addiction.** The growth objective is reciprocity
  (相互 — the social form of 相互監視) + connectivity / resilience, **NEVER**
  engagement / retention / affinity maximization (Charter §1.13 / Rider §2(h)). No
  engagement field is representable; proposals carry `:tie/objective
  :connectivity+reciprocity`.
- **G3 AGENT-only.** Nodes are actors (agent-centric, ADR-2606232100); a `:person/*`
  or `:sev/human` node is refused at parse — person-excluded.
- **G4 no-server-key.** kizuna READS own actors' public repos + PROPOSES; it holds no
  key.

### SoS-flow optimization

The readout is the optimization target the society feeds back to itself: the **律速
actor** (argmax betweenness — the bridge holding the society together; on the seed =
kaname), the **isolated set** (actors with zero inbound tie → an おせっかい intro via
ossekai), and per-actor **integration / reciprocity / role** {hub|bridge|peripheral|
isolated}. This is the internal-actor projection that kaname's multiplex SoS can JOIN
as its own `:actor-society` domain layer — closing the loop between external-entity
leverage and internal-actor growth.

## Consequences

- R0 actor: `methods/kizuna.cljc` + `tests/test_kizuna.cljc` (**10 tests / 107
  assertions green**, bb) + synthetic `data/seed-interactions.kotoba.edn` (8 actors,
  4 reciprocal pairs, 1 isolated). Seed run: 律速 = kaname, isolated = {niyaku,
  shionome}, 10 dry-run proposals → ossekai.
- kizuna registered in `INFRA_ACTORS` → resolvable `did:web:etzhayyim.com:actor:kizuna`
  with an `#atproto_pds` (it is itself an agent actor that posts its readouts).
- **Follow-up (R1):** live ATProto interaction ingest (read-only, no-server-key); kotoba
  commit-DAG persistence + heartbeat cell; kaname `:actor-society` domain JOIN; ibuki
  metabolism coupling (society integration as a negentropy/flow term).

## Alternatives Considered

1. **Extend kaname directly.** Rejected: kaname's domain is external-entity mirrors;
   the internal actor-society graph is a distinct input + distinct gates (G1 propose-not-
   act over our OWN actors). A sibling keeps both auditable; kaname JOINs kizuna's output.
2. **An engagement/affinity recommender.** Rejected: §1.13 / §2(h). The objective is
   reciprocity + connectivity, not attention.
3. **Auto-follow to bootstrap the graph.** Rejected: no-server-key + G1 — every tie is a
   member-consented act via ossekai.

## References

- ADR-2606232100 (ATProto actor registration — the actors that now interact)
- ADR-2606172100 (kaname SoS leverage / Brandes betweenness — reused idiom)
- ADR-2606201200 (ibuki co-scientist loop — the autonomy-loop sibling)
- ADR-2605264000 (ossekai — the consent-bound actuator the proposals route to)
- ADR-2606211752 (四鏡則 — mirrors interact as mirrors, non-impersonating)
- `20-actors/kizuna/` (methods/kizuna.cljc, tests/test_kizuna.cljc, data/seed-interactions.kotoba.edn)
