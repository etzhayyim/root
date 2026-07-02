---
id: adr-2607020900-mst-projector-query-layer-relocation-to-kotoba-lang
title: "ADR-2607020900: mst-projector indexer + query-api relocation from Python to kotoba-lang/mst-projector (Clojure)"
status: accepted
doc_type: adr
topic: mst-projector-query-layer-relocation
authoritative: true
last_verified: 2026-07-02
priority: 3.0
axis: architecture
weight: 0.30
priority_note: "Housekeeping/placement ADR, not a design change to mst-projector's live deployment."
authoritative_for:
  - kotoba-lang/mst-projector repo location and scope
  - the decision to keep subscriber.py in Python (reaffirms prior founder guidance, does not introduce it)
depends_on:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
related:
  - adr-2607011300-nv-compat-relocation-to-kotoba-lang
  - adr-2607011830-pqh-crypto-relocation-to-kotoba-lang
  - adr-2607011930-ipfs-checkpointer-relocation-to-kotoba-lang
  - adr-2607011940-l2-datomic-atproto-relocation-to-kotoba-lang
supersedes: []
superseded_by: []
---

# ADR-2607020900: mst-projector indexer + query-api relocation from Python to kotoba-lang/mst-projector (Clojure)

**Status**: accepted
**Date**: 2026-07-02
**Deciders**: Jun Kawasaki

# Context

Following the etzhayyim-sdk TypeScript generic-substrate sweep (ADR-2607011300
through ADR-2607011940, all six modules ported to Clojure/CLJC and verified),
the same org-taxonomy library-placement rule was extended to Python:
generic library/substrate code with zero etzhayyim-specific coupling belongs
in `kotoba-lang`; etzhayyim-specific business/governance logic stays in
`etzhayyim/root`.

`50-infra/mst-projector/py/src/mst_projector/` is a small package with three
modules: `indexer.py` (a LanceDB-backed indexed-view writer for AT Protocol
MST commit records — table-per-collection, upsert-by-(did,rkey) semantics),
`query_api.py` (an aiohttp XRPC server exposing 4 NSIDs —
`queryByCollection`/`queryByDid`/`queryByField`/`countByCollection` — over the
indexed tables), and `subscriber.py` (consumes the AT Protocol firehose,
`com.atproto.sync.subscribeRepos`, dispatching decoded ops to the indexer).

Investigation before relocating (per this session's established discipline)
surfaced two load-bearing findings:

1. **A prior, independent migration had already settled `subscriber.py`'s
   fate.** `20-actors/etzhayyim-sdk-py/MIGRATION-TODO.md` — documenting an
   in-flight py→cljc port of the `etzhayyim_sdk` package that
   `subscriber.py` imports (`etzhayyim_sdk.cursor.subscribe_with_checkpoint`,
   `etzhayyim_sdk.pds`) — records explicit founder guidance: porting the AT
   Protocol firehose / CBOR-frame websocket subscriber to babashka/Clojure is
   "impractical," and it is deliberately left in place to coexist with the
   now-mostly-Clojure `etzhayyim_sdk` package. This ADR does not
   re-litigate that decision; it only covers the two modules that
   guidance does *not* cover.
2. **A tested Clojure XRPC client for the query API already exists.**
   `etzhayyim_sdk.mst-projector` (`etzhayyim-sdk-py/src/etzhayyim_sdk/
   mst_projector.cljc`, 17 tests / 47 assertions green) calls the exact 4
   NSIDs `query_api.py` implements. Porting `query_api.py` to a
   wire-compatible Clojure server completes a client/server pair that
   was previously split across languages for no architectural reason.

`indexer.py`'s LanceDB dependency has no real JVM/Clojure equivalent, and
this ecosystem's substrate posture (ADR-2605262130, ADR-2605312345) is
already moving read-path/query concerns toward `kotoba-kqe` over the
canonical Datom log rather than bolt-on projection databases — so the port
does not bring LanceDB along; it defines an injected storage protocol
(`IIndex`) instead, matching the injected-transport pattern
`kotoba-lang/ipfs` established this session (`IHttp`).

# Decision

Port (not merely physically relocate — direct Python→Clojure, no
intermediate as-is-Python staging repo) `indexer.py` + `query_api.py` +
`main.py`'s `--serve` path to a new **`kotoba-lang/mst-projector`** repo:

- `kotoba.lang.mst-projector.indexer` — pure record-flattening/orchestration
  logic driving an injected `IIndex` protocol (`-upsert!`/`-delete!`/
  `-query`/`-count-rows`/`-list-collections`/`-describe`).
- `kotoba.lang.mst-projector.mem-index` — one concrete reference `IIndex`
  (in-memory, optional EDN-file persistence).
- `kotoba.lang.mst-projector.query-api` — the XRPC server (JDK-native
  `com.sun.net.httpserver.HttpServer`, zero extra dependency), byte-for-byte
  wire-compatible with the existing `etzhayyim_sdk.mst-projector` Clojure
  client: same 4 NSIDs, same camelCase wire keys, same real 4xx/5xx status
  codes.
- `kotoba.lang.mst-projector.cli` — entrypoint for the `--serve` path only;
  `--subscribe` exits with a clear pointer at the still-Python subscriber
  rather than silently no-op'ing or shipping a stub.

One latent bug was fixed, not faithfully ported: `query_api.py`'s
`_healthz` referenced `indexer.data_dir`, an attribute the Python `Indexer`
class never actually set, so every real health check would have raised and
always returned 503. The Clojure port replaces it with a real `-describe`
diagnostic while keeping the wire key name (`"data_dir"`) unchanged for
response-shape compatibility.

**`subscriber.py` is explicitly NOT ported** and is not touched by this
ADR. `50-infra/mst-projector/py`'s Python implementation is **left running
unchanged** — this is coexistence, matching the `pqh`/`ipfs` precedent
where the original implementation keeps serving existing deployments while
the new implementation becomes canonical for new Clojure/babashka
consumers, not a cutover. No re-export-shim is created (a Python module
cannot re-export from a JVM/Clojure package the way `checkpointer.ts`
could re-export from `@etzhayyim/checkpointer`), so this ADR records the
relocation without modifying `50-infra/mst-projector/py`'s source.

# Consequences

- `kotoba-lang/mst-projector` becomes independently versioned and
  installable; a future non-etzhayyim actor or a Clojure/babashka-only
  deployment can depend on the indexer+query-api pair directly.
- `50-infra/mst-projector/py`'s deployment (Dockerfile, launchd) is
  **unchanged** by this ADR — cutting the live service over to the Clojure
  implementation, if ever desired, is a separate, deliberate follow-up
  decision, not an automatic consequence of this port existing.
- The `etzhayyim_sdk.mst-projector` Clojure client now has a real,
  wire-verified Clojure server counterpart it can be pointed at, closing a
  client/server language split that had no architectural justification.
- `indexer.py`'s LanceDB-specific behaviors (dot-to-underscore table-name
  translation, its lossy reverse mapping) are intentionally NOT preserved
  in the Clojure port — the injected `IIndex` protocol has no such
  restriction, so `list-collections` is exactly correct there, an
  improvement over the Python original's lossy diagnostic-only mapping.

# Alternatives Considered

## A1. Also port or stub `subscriber.py`

Rejected. A prior, independent migration already reached and documented an
explicit founder decision on this exact file (impractical to bb-port,
left to coexist). Re-litigating or partially second-guessing that
decision here — even via a "coming soon" stub — would fork the guidance
into two inconsistent records. This ADR treats that decision as settled.

## A2. Physically relocate the Python source as-is first, port later

Rejected for the Python side of the org's generic-substrate sweep,
diverging from the earlier TypeScript sweep's two-phase
physically-move-then-port pattern. Python and Clojure share no runtime, so
an as-is Python staging repo would not offer the TypeScript pattern's real
benefit (a working re-export shim keeping existing import paths resolving
unchanged during the gap between move and port) — there is no equivalent
Python-side shim possible into a Clojure package. Going directly to
Clojure skips a staging step that would have added a repo with no
functional benefit.

## A3. Bring a JVM database dependency (e.g. a JDBC-backed SQL store) as the reference `IIndex` implementation

Rejected for the *reference* implementation specifically (a heavier
`IIndex` remains a legitimate choice for a production deployment that
wants it — the protocol does not preclude it). `indexer.py`'s actual
query surface is a single equality-predicate filter per call; a full SQL
engine is more machinery than that surface needs, and this ecosystem's
established convention this session (`kotoba-lang/ipfs`, `witness-quorum`,
`base-l2`, `atproto-client`) favors minimal/zero extra runtime
dependencies over pulling in a database driver by default.

# References

- ADR-2605171800 (the pipeline umbrella ADR `mst-projector`'s own top-level
  README cites as its Stage 3 design authority; the Python package's own
  docstrings additionally cite "ADR-2605215500," but no ADR file with that
  ID exists in this repo as of this writing — a dangling/miscited
  reference, not something this ADR depends on)
- ADR-2605262130 / ADR-2605312345 (kotoba storage-substrate unification —
  the read-path direction this ADR's `IIndex` choice is consistent with)
- ADR-2607011300 / ADR-2607011830 / ADR-2607011930 / ADR-2607011940 (the
  TypeScript relocation ADRs this ADR follows the same investigate-before-
  relocate discipline from)
- `20-actors/etzhayyim-sdk-py/MIGRATION-TODO.md` (the prior migration whose
  founder guidance on `subscriber.py` this ADR respects)
- `kotoba-lang/mst-projector` (new repo, `README.md` for full provenance +
  design detail)
