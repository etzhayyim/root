# actor-registry — Holochain-iso actor registration (PoC)

Registers actors the **agent-centric / Holochain way** instead of as a central
constant in the apex Worker (`unispsc-handles.gen.ts`, `ENTITY_TOTAL_COUNT`).
Grounded in the repo's existing Holochain-isomorphic substrate (ADR-2605231400 /
2606011330 / 2606015600 / 2606112000).

## The idea

There is **no master list**. Each actor is an **agent = its own ed25519 key**
(`did:key`, self-certifying — no CA, no TLS anchor). To register, an agent:

1. mints its keypair → `did:key:z6Mk…`,
2. authors a **signed genesis entry** on its **own kotoba Datom source-chain**
   (a content-addressed commit-DAG; the genesis `:cid` is its join address),
3. gets a **witness membrane attestation** (a validator signs the same `:cid` —
   stands in for the Pregel witness quorum / `kotoba-dht` validating DHT),
4. self-publishes the source-chain doc.

The **registry is an emergent materialized-view fold** over those genesis
entries — never hand-kept. In full migration all ~27.5k actors would each author
their own genesis like this.

## Run

```sh
clojure -M:register     # mint + sign + attest the roster → public/kotoba/agents/
clojure -M:test         # ed25519 did:key roundtrip, self-sign+witness, tamper detection
clojure -M:wire         # encode a Datom query response as transit+json → public/kotoba/wire/
clojure -M:sync         # live kotoba sync node on :8720 (XRPC sync.subscribe, transit+json SSE)
```

## Live sync node (transit+json wire)

`sync_node.clj` serves the live Datom tail over the XRPC endpoint

```
GET http://localhost:8720/xrpc/com.etzhayyim.apps.kotoba.sync.subscribe?cursor=0
```

as **Server-Sent Events whose frames are transit+json** (the Datomic-client wire
standard) — read from the vitals EAVT snapshot (content-addressed EDN on disk),
streamed from the cursor, then held open with heartbeats. CORS is open so the
browser at `:8710` can subscribe cross-origin.

The browser live tail (`live.cljs`) points at `window.__SYNC_BASE__`
(`http://localhost:8720` on localhost, same-origin in production) and decodes
each frame with `transit-cljs` — keywords/types survive end to end. Open
`/nodes`, click **“go live”** to stream. Verified end-to-end: a transit-js client
decodes the live frames with attributes reconstructed as real keywords
(`:vitals.actor/cells`, nested vectors preserved). Production form is a `bb` task
under launchd, fronted by the apex Worker proxying the XRPC route.

Output (git-ignored, served to the browser):
- `public/kotoba/agents/<handle>.agent.kotoba.edn` — each agent's self-published,
  signed genesis source-chain.
- `public/kotoba/agents/registry-mv.kotoba.edn` — the emergent registry fold
  (count + `handle → did:key → head-cid` index).

## Verified end-to-end

- **clj** (`agent.clj` / `register.clj`, JDK Ed25519): every agent's genesis is
  content-address-consistent, self-signed by its own key, and witness-attested;
  a tampered datom breaks both the CID and the signature (tests green).
- **browser** (`src/.../chain/agent.cljs`): `/explorer`'s "agent registration"
  card decodes each `did:key` (base58btc), recomputes the genesis `:cid` via the
  canonical `kotoba.datom` codec, and verifies the agent self-signature +
  witness attestation with **Web Crypto Ed25519** — all `✓ chain ✓ self-sig ✓
  membrane`, no server in the trust path. `/nodes` census shows the emergent
  `self-registered` tier.

## Files

```
actor-registry/
├── deps.edn
└── src/etzhayyim/registry/
    ├── agent.clj      # ed25519 keygen, did:key encode/decode, base58, sign/verify
    └── register.clj   # signed genesis source-chains + witness attestation + MV fold
```

## The validating membrane (phase 2 — implemented)

Registration is now gated by a real membrane, not a single witness:

- **CACAO member vouch (Sybil boundary).** An agent cannot self-admit. An existing
  **SBT member** (in the published `member-roster`) signs a CACAO capability
  `{iss=member, aud=agent, att, exp}` (the revocable-leash shape, ADR-2606111400).
  A genesis with no valid roster-member vouch is **rejected** (`no-member-vouch`).
- **Witness quorum.** N validators (the DHT neighbourhood) each independently run
  the DNA rules — self-sig ok · vouch ok & issuer∈roster · handle unique · content
  address ok — and emit a **signed attestation** (`:valid`) or a **signed warrant**
  (`:invalid` + reason). The genesis is durable iff **≥ threshold** attestations
  (2-of-3 here).
- **kotoba-dht replication.** Each entry is held by the **r validator-nodes whose
  ids are XOR-closest** to the genesis `:cid` (ADR-2606011330 neighbourhood).
- **Emergent, rejecting registry.** The MV folds ONLY quorum-validated agents.
  The run registers 5 vouched agents (✓) plus two adversarial ones that are
  **rejected**: `rogue-sybil` (no vouch) and a duplicate `busshi` (handle taken).

Every check is re-run **in the browser** (`/explorer`): chain recompute + Web
Crypto Ed25519 over the self-signature, the member vouch (against the roster), and
the validator quorum (against the validator set) — rejected agents show their
warrant reason. Proven by `membrane_test.clj` (clj) + `agent_test.cljs` (browser).

## Still ahead (the honest edge)

Live gossip/replication (real `kotoba-dht` GossipSub epochs + warrant propagation
across peers) and binding the SBT roster to the on-chain membership contract are
the remaining steps; here the quorum + DHT neighbourhood are computed
deterministically and the roster is a generated key set.
