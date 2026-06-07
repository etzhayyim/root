---
id: adr-2605262400-public-data-organism-ipfs-ingestion
title: "ADR-2605262400: Artificial-organism ingestion of public-domain datasets (OSM / RIR / GeoLite2 / BGP / DNS / Web-graph) via IPFS-pinned DataLad subdatasets — passive-only perception sensors + cold-path training corpus, with Tier-A/Tier-C ladder and G13 fleet-internal NC carve-out"
status: proposed
doc_type: adr
topic: public-data-organism-ingestion
authoritative: true
last_verified: 2026-05-26
priority: 6.0
axis: architecture
weight: 0.55
priority_note: "Single SoT for how `pymagatama.organism` actors consume large public-domain corpora (OSM Planet, RIR delegated stats, MaxMind GeoLite2, RIPE-RIS / Routeviews BGP MRT dumps, IANA root zone, Rapid7 Sonar FDNS, OpenINTEL, CAIDA AS-rank, Common Crawl host index) without violating the religious-corp substrate boundary. Two-path split: (A) PERCEPTION = hot-path organism heartbeat sensors that resolve the latest datasetPin CID, stream a bounded sample into InboxBuffer, and feed joucho 情緒; (B) TRAINING = cold-path corpus assembly that emits an IPFS-pinned shard manifest into baien-moemoekyun-train / baien-distill, eval-gated under R1.5 commit_node pattern. Tier-A sources (OSM ODbL / GeoNames CC-BY / Wikidata CC0 / RIR public / IANA public / GeoLite2 CC-BY-SA / RIPE-RIS / Routeviews) produce publishable artifacts. Tier-C sources (Rapid7 Sonar / CAIDA / OpenINTEL / Common Crawl URL index / CZDS per-TLD opt-in = CC-BY-NC or research-use) are admitted under G13 fleet-internal carve-out (artifact name MUST carry `-nc-` infix, MUST NOT publish, served via judah LiteLLM + SBT-gate only — same gate pattern as ADR-2605262100 R1.4). All ingestion is PASSIVE — organisms MUST NOT perform active DNS resolution / port probing / traceroute / WHOIS lookups (CHARTER-RIDER §2(c) covert-ops avoidance). PII filter precedes Charter Rider §2 scan. Inference path UNCHANGED per ADR-2605215000 (Murakumo fleet only, no commercial GPU rental for perception or for any artifact derived from this ADR's data unless the ADR-2605262200 train-rental amendment ratifies). 14 gates G1..G14, 12 non-goals N1..N12, 4-wave delivery W0..W4."
authoritative_for:
  - public-data ingestion policy for the artificial-organism ecosystem
  - separation of perception (hot path) vs training (cold path) data flows
  - Tier-A vs Tier-C license ladder for organism-consumed datasets
  - G13 fleet-internal carve-out applied to NC-licensed source data
  - DatasetSensor protocol for pymagatama.organism.sensors.*
  - passive-only constraint on organism network behavior (no active DNS/IP probing)
  - new fetcher set in 70-tools/e7m-dataset/src/e7m_dataset/fetchers/ (RIR, GeoLite2, RIPE-RIS, Routeviews, IANA root, Rapid7 Sonar, OpenINTEL, CAIDA, CZDS, Common Crawl CDX)
  - new subdataset taxonomy under 90-docs/baien/datasets/{geo,netreg,routing,dns,web}/
  - corpus-recipe.toml schema for assemble-public-corpus.py
  - 3 new KaizenObserver rules R7 (stale-sensor-pin) / R8 (charter-fail-rate) / R9 (tier-c-leak backstop)
  - PII filter contract (precedes Charter Rider §2 scan; covers WHOIS / mailing-list dumps / contact records)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605221411-etzhayyim-artificial-organism-ecosystem
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605240200-unispsc-organism-kaizen-self-reflection
  - adr-2605241500-etzhayyim-dataset-cid-substrate
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2605081430-osm-ingest-rw-tuning-and-k8s-utilization
  - adr-2605200300-defense-isr-sensor-fusion
  - adr-2605215100-etzhayyim-maps-sentinel-mlx-murakumo-fleet
  - adr-2605262200-charter-rider-2i-baien-train-rental-carveout
  - adr-2605262300-baien-moemoekyun-r2-runpod-b200-train-architecture
supersedes: []
superseded_by: []
---

# ADR-2605262400: Public-data ingestion for the artificial-organism ecosystem via IPFS-pinned DataLad subdatasets

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The religious-corp artificial-organism ecosystem (ADR-2605221411,
ADR-2605232345, ADR-2605240200) currently has:

- `e7m-dataset` (ADR-2605241500) — a DataLad + git-annex `directory` +
  sidecar IPFS pinner with four fetchers (HF / GeoNames / OSM Geofabrik
  / Wikidata SPARQL) and the `com.etzhayyim.substrate.datasetPin`
  Lexicon as the receipt.
- `pymagatama.organism` — joucho 情緒 cadence, `InboxBuffer`,
  `KaizenObserver` (6 rules), and a single sensor module
  (`pymagatama.organism.sensors.charter_rider`).
- A `maps_sentinel_murakumo` M1 T0 preprocessing pipeline
  (ADR-2605215100) that already proved OSM PBF + raster fusion at fleet
  scale.
- A `baien-moemoekyun R1` training discipline (ADR-2605262100) with
  three-tier license ladder (Tier A Apache/MIT/CC0/CC-BY publishable —
  Tier B CC-BY-SA — Tier C CC-BY-NC fleet-internal only) and the G13
  invariant that NC-trained artifacts MUST NOT publish.

What is **missing**, and what the user explicitly asked for in session
2026-05-26 13:18 JST, is a coherent design for how an organism consumes
**public-domain large-scale datasets** — specifically:

- **OSM Planet** (already partially handled, but only as a fetcher; no
  organism-side sensor abstraction exists);
- **global DNS information** (root zone, TLD zones, forward-DNS
  archives, OpenINTEL active-measurements);
- **global IP-address information** (RIR delegated stats, GeoLite2,
  prefix-to-ASN);
- **global routing information** (BGP MRT dumps from RIPE-RIS /
  Routeviews);
- **web-host graph** (Common Crawl URL index, CAIDA AS-rank).

The decisions to make are:

1. How does the perception path differ from the training path, and where
   does the boundary sit?
2. Which sources are admissible under CHARTER-RIDER v2.0 §2, and at
   which Tier (A / B / C / D)?
3. Are organisms allowed to perform any **active** network probing
   themselves (DNS resolve, port probe, traceroute, WHOIS query), or
   are they strictly readers of pre-captured public archives?
4. What is the sensor abstraction in `pymagatama.organism.sensors.*`
   that does NOT leak Tier-C bytes to public-facing PostSink paths?
5. What does the cold-path training corpus assembly look like, and how
   does it reuse ADR-2605262100 R1.5 eval-gated commit_node?
6. What new fetchers must land in
   `70-tools/e7m-dataset/src/e7m_dataset/fetchers/`?
7. What new KaizenObserver rules guard the system against drift and
   against accidental tier-leak?

The constraint surface is dense:

- **CHARTER-RIDER §2(c)** — covert-ops avoidance prohibits active
  reconnaissance of third-party infrastructure (active DNS probing of
  arbitrary domains, active port scans, traceroute campaigns) when
  performed at religious-corp scale and without informed consent.
  Reading a pre-published public archive of someone else's scan
  (Rapid7 Sonar, RIPE-RIS) is categorically different from running
  the scan ourselves.
- **CHARTER-RIDER §2(d)** — PII-aware data handling. WHOIS dumps
  routinely carry individual contact emails / phone numbers / postal
  addresses; the organism MUST NOT ingest those without a PII filter.
- **CHARTER-RIDER §2(i)** — Murakumo-only inference. Anything an
  organism perceives still has to be processed under religious-corp
  inference (no shipping a sample to OpenAI/Anthropic vendor APIs for
  classification mid-tick). The train-rental amendment ADR-2605262200
  is gated on Council ratification and is independent of this ADR.
- **ADR-2605262130 (Kotoba)** — read-path queries should not reintroduce
  Kotoba/Datomic / Postgres / Lance projection layers; sensor output is
  in-memory streamed and may be staged into `kotoba-kqe`
  arrangements if the sensor needs an attribute index, never into a
  separate projection backend.
- **ADR-2605241500 §D6** — `replicationMin: 2`. Every subdataset added
  under this ADR MUST be pinned on at least two nodes before any
  organism is allowed to depend on it for production-class behavior.

The user's explicit answers to the three clarifying questions in this
session (2026-05-26):

- **Tier-C admitted, with G13 fleet-internal carve-out**. Rapid7 Sonar,
  CAIDA, OpenINTEL, Common Crawl URL index, CZDS per-TLD opt-in zones
  go into the design, but every derived artifact carries `-nc-` infix
  and serves only through judah LiteLLM + SBT-gate.
- **No active probing**. Organisms are strict readers of public
  archives. Active DNS / port / WHOIS / traceroute behavior is out of
  scope for this ADR. (If a future use case demands it, it must come
  back as a Council Lv6+ separate ADR.)
- **Commit this ADR first**, then implement W1 in a follow-up commit.

# Decision

Adopt a two-path public-data ingestion architecture with a strict
license ladder, a passive-only network discipline, and a sensor
abstraction that respects the G13 NC-leak backstop.

## §1. Two-path architecture (perception vs training)

```
public archive on the open internet
        │
        ▼
e7m-dataset add / pull <source>
        │  (Charter Rider §2 scan + PII filter; license tag attached)
        ▼
DataLad subdataset under 90-docs/baien/datasets/<bucket>/<source>/<rev>/
        │
        ▼
git-annex `directory` special remote on local volume
        │
        ▼
e7m-dataset publish-ipfs <subdataset>
        │  (sha256e-key → IPFS-CID map; map itself pinned)
        ▼
IPFS Kubo (replicationMin: 2, at least two religious-corp nodes pin)
        │
        ▼
com.etzhayyim.substrate.datasetPin record on PDS (receipt)
        │
        ├─────────────► (A) PERCEPTION / hot path
        │                organism heartbeat tick → sensor.latest_pin()
        │                → sensor.hot_sample(pin, n=8) (in-memory only;
        │                                                no annex write-back)
        │                → InboxBuffer push (with tier flag)
        │                → joucho 情緒 update → cadence flag → action
        │                  (PostSink BLOCKS tier-C-tagged Observations
        │                   on public posting paths — G13 backstop)
        │
        └─────────────► (B) TRAINING / cold path
                         corpus-recipe.toml (per-target-artifact)
                         → assemble-public-corpus.py
                            (multi-source IPFS-CID resolve + shard write)
                         → Charter Rider §2 + PII re-scan (defense in depth)
                         → IPFS-pinned corpus subdataset (own CID)
                         → baien-moemoekyun-train SFT / baien-distill
                            on Murakumo fleet (EVO-X2 / mac-260317)
                         → R1.5-style eval-gated commit_node
                         → distilled-models.jsonl row (with `-nc-` infix
                           if any source.tier == "C")
```

The boundary between (A) and (B) is the `corpus-recipe.toml` file:
perception is **CID-aware, lazy, sampled, ephemeral**; training is
**CID-frozen, recipe-declared, full-shard, persisted**.

## §2. Data-source ladder (license × tier × admissibility)

| Source | Coverage | License | Tier | Fetcher | Bucket | Train? | Perceive? |
|---|---|---|---|---|---|---|---|
| OSM Geofabrik PBF | global vector | ODbL 1.0 | A | exists (`osm.py`) | `geo/osm/` | yes | yes |
| GeoNames bulk | global toponym | CC-BY 4.0 | A | exists (`geonames.py`) | `geo/geonames/` | yes | yes |
| Wikidata SPARQL | structured knowledge | CC0 1.0 | A | exists (`wikidata.py`) | `geo/wikidata/` | yes | yes |
| RIR delegated stats (APNIC / ARIN / RIPE / AFRINIC / LACNIC) | global IPv4/v6 alloc | public-domain de facto | A | new `rir_delegated.py` | `netreg/rir-delegated/` | yes | yes |
| MaxMind GeoLite2 (City/Country/ASN) | IP → geo / ASN | CC-BY-SA 4.0 | A (SA propagates) | new `maxmind_geolite.py` | `netreg/geolite2/` | yes (SA derivative) | yes |
| IANA root zone | DNS root | public-domain | A | new `iana_root.py` | `netreg/iana-root/` | yes | yes |
| RIPE NCC RIS MRT | global BGP | open (RIPE TOU) | A | new `ripe_ris.py` | `routing/ris-mrt/` | yes | yes |
| Routeviews MRT | global BGP | open (UO TOU) | A | new `routeviews.py` | `routing/routeviews/` | yes | yes |
| Rapid7 Open Data Sonar FDNS | global forward DNS scans (archived) | research-use (accept-terms) | **C** | new `rapid7_sonar.py` | `dns/rapid7-sonar-fdns/` | yes (G13 `-nc-`) | yes (internal-only) |
| OpenINTEL | DNS active-measurement archive | CC-BY-NC 4.0 | **C** | new `openintel.py` | `dns/openintel-tranco1m/` | yes (G13) | yes (internal-only) |
| CAIDA AS-rank / prefix2as / AS-relationship | global AS graph | CC-BY-NC | **C** | new `caida.py` | `routing/caida-as-rank/` | yes (G13) | yes (internal-only) |
| ICANN CZDS per-TLD zones | per-TLD DNS | per-TLD agreement | **C/D** (per TLD) | new `czds.py` (manual opt-in per TLD) | `dns/czds-<tld>/` | per-TLD | per-TLD |
| Common Crawl URL index (CDX) | web host graph | CC-BY-NC-SA-ish (S3 free) | **C** | new `commoncrawl_cdx.py` | `web/commoncrawl-cdx/` | yes (G13) | yes (internal-only) |

Tier D (e.g. proprietary commercial DNS feeds, paid threat-intel feeds)
is **out of scope for this ADR** and remains prohibited by
CHARTER-RIDER §2.

## §3. Sensor abstraction (`pymagatama.organism.sensors.*`)

New module: `20-actors/magatama/py/src/pymagatama/organism/sensors/base.py`.

```python
# Protocol definition (excerpt; full type-checked impl lands in W1)
class DatasetSensor(Protocol):
    name: str                                    # "netreg/rir-delegated/apnic"
    license: str                                 # SPDX or per-source slug
    tier: Literal["A", "B", "C", "D"]            # Charter Rider tier
    refresh_cadence_sec: int                     # minimum interval between latest_pin()
    pii_filter: PiiFilterPolicy                  # required (default = STRICT)

    def latest_pin(self) -> DatasetPin: ...      # AT record lookup
    def stream(self, pin: DatasetPin) -> Iterator[Observation]: ...
    def hot_sample(self, pin: DatasetPin, n: int) -> list[Observation]: ...
```

Wave-1 sensor implementations:

| Sensor module | Subdataset bucket | Observation shape |
|---|---|---|
| `osm_region_sensor.py` | `geo/osm/<region>/` | `(lat, lon, feature_tags, name?, admin_level?)` |
| `rir_delegated_sensor.py` | `netreg/rir-delegated/` | `(prefix, cc, allocated_at, holder_opaque_id)` |
| `geolite2_sensor.py` | `netreg/geolite2/` | `(ip_or_prefix → {country, city, asn, lat, lon})` |
| `ris_routing_sensor.py` | `routing/ris-mrt/` | `(prefix, origin_asn, as_path, collector, ts)` |
| `iana_root_sensor.py` | `netreg/iana-root/` | `(tld, ns, ds, expires)` |

The organism tick integration is additive (does **not** change the
existing joucho cadence):

```python
class UnispscOrganism:
    def __init__(self, ..., sensors: list[DatasetSensor] = ()): ...
    def tick(self, ts) -> OrganismTickResult:
        for s in self.sensors:
            if self._should_poll(s, ts):
                pin = s.latest_pin()
                samples = s.hot_sample(pin, n=8)
                # Charter Rider scan already ran at e7m-dataset add time.
                # tier == "C" attaches `internal_only=True` here.
                self.inbox.push_observations(
                    samples, sensor=s.name, tier=s.tier,
                    internal_only=(s.tier == "C"),
                )
        # existing cadence path runs unchanged
        return super().tick(ts)
```

The `PostSink` contract is amended to **drop** every Observation whose
`internal_only=True` flag is set, regardless of joucho mood. This is
the G13 backstop on the perception side.

## §4. Training corpus assembly (cold path)

New tool: `70-tools/baien-moemoekyun-train/scripts/assemble-public-corpus.py`.

Input format `corpus-recipe.toml`:

```toml
target_artifact = "baien-server-moemoekyun-r2-netgraph-nc"   # `-nc-` because tier C source present
output_subdataset = "training/corpora/netgraph-r2-261015/"

[[source]]
subdataset    = "netreg/rir-delegated/apnic"
datasetPin_at = "at://did:web:dataset-pinner.etzhayyim.com/com.etzhayyim.substrate.datasetPin/<rkey>"
shard_glob    = "*.txt"
tier          = "A"
weight        = 0.05

[[source]]
subdataset    = "dns/rapid7-sonar-fdns"
datasetPin_at = "at://...<rkey>"
shard_glob    = "fdns-a-*.json.gz"
tier          = "C"
weight        = 0.20

# ... more sources
```

Behavior:

1. Resolve every `datasetPin_at` → IPFS CID map.
2. Apply Charter Rider §2 scan + PII filter to every shard (defense in
   depth; the same shards passed the gate at ingest, but the corpus is
   the final boundary before SFT).
3. Compute the **maximum tier** across sources. If any tier == "C",
   enforce the `-nc-` infix in `target_artifact`. If absent, abort
   fail-closed.
4. Emit NDJSON shards into the output subdataset
   (`training/corpora/<name>/`), DataLad save, annex copy,
   `e7m-dataset publish-ipfs`, datasetPin emit. The corpus is itself a
   pinned IPFS artifact and is what `baien-distill` / SFT consumes.
5. Eval gate at the end of training reuses ADR-2605262100 R1.5
   pattern: `commit_node` only fires if KPI Δ thresholds pass, else
   `aborted` row written to `90-docs/baien/distilled-models.jsonl`.

## §5. Kaizen rules (self-reflection)

Three new rules in `pymagatama.organism.kaizen` (registry-extension,
ADR-2605240200 contract preserved):

| Rule ID | Trigger | Proposal |
|---|---|---|
| **R7-stale-sensor-pin** | any sensor's `latest_pin().createdAt` is older than `refresh_cadence_sec * 4` | "re-pull `<name>`, run `e7m-dataset publish-ipfs <name>`, emit new datasetPin" |
| **R8-charter-fail-rate** | Charter Rider scanner false-positive rate > 5% over a 24h sliding window on a given sensor's shards | "review threshold + regex for `<sensor>`; submit revised scanner spec to Council" |
| **R9-tier-c-leak** | any Observation tagged `tier="C"` was observed reaching a PostSink that is not `NullPostSink` or `NdjsonQueuePostSink` with `internal_only=True` honored | (critical) emit critical KaizenProposal, halt the offending organism cell, escalate to Council Lv6+ |

R9 is the **constitutional backstop** — it is the runtime expression of
G13 (NC-trained / NC-perceived artifacts MUST NOT publish). It is
designed to fire **before** the leak goes external; if it ever fires
post-hoc, that is itself a Council-grade incident.

## §6. PII filter (precedes Charter Rider scan)

New module: `20-actors/magatama/py/src/pymagatama/organism/sensors/pii_filter.py`.

Scope (Wave 1):

- Email addresses (RFC-5321 grammar, regex + dnspython MX optional
  sanity check on the literal string only — no live DNS lookup).
- E.164 phone numbers.
- Postal addresses with country code (heuristic; conservative — over-
  redact rather than under).
- WHOIS-style registrant blocks (`registrant: ...`, `tech-c: ...`,
  `admin-c: ...`).

Sources where the PII filter runs hot:

- Rapid7 Sonar (contains random user email artifacts from TXT records).
- WHOIS-derived corpora (we do **not** ingest direct WHOIS by default;
  if a Council-approved RIR mirror appears later, the PII filter is
  the first gate).
- Common Crawl pages (best-effort; the URL index itself is host-level
  and rarely contains direct PII, but CDX records can).

Policy: PII matches are **redacted in place** (not just flagged).
Original shard bytes are preserved in annex; the redacted view is what
sensors / corpus assembly see. The Charter Rider §2 scan runs on the
redacted view.

## §7. Passive-only network discipline

Organisms instantiated under this ADR:

- MUST NOT perform live DNS resolution against third-party domains
  beyond what is intrinsically required to fetch from the religious-
  corp DID infrastructure (`etzhayyim.com`, `pds.etzhayyim.com`,
  `dataset-pinner.etzhayyim.com`, fleet-local Kubo HTTP API).
- MUST NOT perform port scans, traceroute campaigns, or active probes
  of any kind against IPs / prefixes / ASes / hosts observed in the
  dataset.
- MUST NOT submit live queries to WHOIS, RDAP, DNS-over-HTTPS, or
  similar interactive services on behalf of organism logic.
- MAY fetch a **published archive** (Rapid7 / OpenINTEL / RIS / CAIDA)
  via IPFS or HTTPS at ingest time. Those fetches go through
  `e7m-dataset` and are subject to all the gates above.

If a future use case requires active probing, it is **out of scope**
and requires a separate ADR with Council Lv6+ approval.

## §8. Wave delivery plan

| Wave | Scope | Estimate |
|---|---|---|
| **W0 (this ADR)** | proposed-status ADR + deps.toml entry + README index + CLAUDE.md Status row | half-day |
| **W1 (Tier-A foundations)** | `rir_delegated.py` + `geolite2_sensor.py` + `iana_root.py` fetchers; `DatasetSensor` Protocol + 3 sensors (`osm_region_sensor` / `rir_delegated_sensor` / `geolite2_sensor`); Wave-1 corpus recipe (Tier A only); `pii_filter.py` first cut; R7 + R8 + R9 Kaizen rules | 2-3 days |
| **W2 (Routing)** | `ripe_ris.py` + `routeviews.py` fetchers; `ris_routing_sensor.py` + `iana_root_sensor.py`; W2 corpus recipe additions | 2-3 days |
| **W3 (Tier-C NC carve-out)** | `rapid7_sonar.py` + `openintel.py` + `caida.py` fetchers; G13 enforcement verify; R9 leak-test harness; `-nc-` artifact naming gate; SBT-gate plumbing through judah LiteLLM | 3-4 days |
| **W4 (CZDS + Common Crawl)** | `czds.py` per-TLD opt-in; `commoncrawl_cdx.py`; per-TLD Council attestation rows for each enabled TLD | per-TLD individual |

W1 lands in a follow-up commit to this ADR; W2 / W3 / W4 each get their
own commit and individual eval rows.

## §9. Gates (14)

- **G1**: Every subdataset ingested under this ADR runs Charter Rider §2
  scan at `e7m-dataset add` time. Fail = abort, no IPFS write, no
  datasetPin emit.
- **G2**: PII filter runs **before** Charter Rider §2 scan on any source
  marked `pii_sensitive=true` in its fetcher metadata (Rapid7 default
  true; OpenINTEL default true; CAIDA default false; OSM / RIR / IANA
  / RIS / Routeviews / GeoLite2 default false; CZDS per-TLD).
- **G3**: Every subdataset honors `replicationMin: 2`. Production
  organism sensors REFUSE to bind to a subdataset whose datasetPin
  reports fewer than 2 distinct `assignedNodes` DIDs.
- **G4**: Sensor `tier == "C"` Observations attach `internal_only=True`
  unconditionally. `PostSink` implementations MUST drop them on
  external paths. Verified by R9 backstop.
- **G5**: Cold-path corpus recipes with any tier-C source MUST encode
  `-nc-` infix in `target_artifact`. The assembler aborts fail-closed
  if the convention is violated.
- **G6**: NC-derived artifacts MUST route through judah LiteLLM + SBT-
  gate. Direct serve to public endpoints is prohibited. Same gate
  pattern as ADR-2605262100 G13.
- **G7**: Inference of any artifact derived from this ADR's data flows
  through Murakumo fleet (ADR-2605215000). No commercial GPU rental
  for inference. Train rental is independent (ADR-2605262200 amendment
  ratify pending).
- **G8**: Sensor implementations MUST NOT perform active network probes
  (G6 of §7). Enforced by unit-test + lint hook
  (`70-tools/scripts/lint/sensor-no-active-probe.mjs` — Wave 1).
- **G9**: Sensor implementations MUST be deterministic on
  `hot_sample(pin, n)` given a fixed `pin.cid` (modulo declared
  randomness seed). Reproducibility is required for KaizenObserver
  delta tracking.
- **G10**: `corpus-recipe.toml` files live under
  `70-tools/baien-moemoekyun-train/recipes/` and are themselves
  committed to git. The recipe IS the audit trail for which CIDs went
  into which artifact.
- **G11**: Charter Rider scanner false-positive rate over a 24h sliding
  window per sensor MUST stay ≤ 5% (R8 ceiling). Threshold breach
  blocks new training rounds on that sensor until threshold is
  revised by Council.
- **G12**: Sensor refresh cadence MUST NOT undercut the upstream
  publisher's stated update cadence (e.g. RIR delegated is daily —
  sensor MUST NOT poll more often than daily; RIS dumps are 8-hourly
  — sensor MUST NOT poll more often than 8-hourly).
- **G13**: Every ingestion emits one `com.etzhayyim.substrate.datasetPin`
  record. Missing record = the subdataset is invisible to organisms
  (sensors MUST fail-closed on missing receipt).
- **G14**: Every commit under this ADR (Wave 1+) emits an entry in
  `90-docs/baien/datasets.jsonl` (append-only manifest, ADR-2605241500
  §D contract).

## §10. Non-goals (12)

- **N1**: NOT a live DNS / IP / BGP probing tool. Out of scope; passive
  archive only.
- **N2**: NOT a WHOIS query engine. Out of scope; PII filter is the
  only WHOIS touchpoint and runs over pre-captured corpora only.
- **N3**: NOT a port scanner / vulnerability scanner / reconnaissance
  framework.
- **N4**: NOT a route hijack detector / RPKI validator runtime. Future
  work; this ADR ships data not detection.
- **N5**: NOT a NetFlow / sFlow / IPFIX collector. Out of scope; those
  are operator-owned data sources, not public archives.
- **N6**: NOT a tor / onion / I2P address harvester.
- **N7**: NOT an alternative to BIND / Unbound / Knot / PowerDNS as a
  resolver. Organisms do not serve DNS; they consume DNS *data*.
- **N8**: NOT a substrate-engine choice. Storage / read path follow
  ADR-2605262130 (Kotoba) and ADR-2605241500 (DataLad + annex + IPFS);
  this ADR adds sources and sensors only.
- **N9**: NOT a vendor-data-feed integrator. Tier D (paid threat-intel
  feeds, commercial DNS subscription feeds) is excluded.
- **N10**: NOT a commercial GPU rental enabler. Inference path remains
  Murakumo-only (ADR-2605215000). Train rental is the subject of a
  separate amendment (ADR-2605262200, Council ratify pending).
- **N11**: NOT a federation / aggregation contract for multiple
  religious-corps. This ADR is internal to `etzhayyim`.
- **N12**: NOT a replacement for `maps_sentinel_murakumo M1` (raster
  fusion, ADR-2605215100). That pipeline remains the authoritative
  geospatial fusion path; this ADR plugs into it as a sensor + corpus
  feeder.

# Consequences

**Positive**:

- Organisms gain situational awareness over a substantial fraction of
  the world's public network metadata (IP allocation, AS topology, BGP
  reachability, root DNS structure, OSM-grade ground truth) without
  any active third-party probing.
- The license ladder makes admissibility decisions explicit and
  reviewable, with G13 backstop preventing accidental NC-data
  artifact publication.
- Training corpora become declarative (`corpus-recipe.toml`) and
  reproducible (IPFS CIDs are content-addressed; the recipe pins
  exact CIDs of source subdatasets).
- The PII filter + Charter Rider scan double layer addresses
  CHARTER-RIDER §2(c) / §2(d) concerns explicitly, with the
  KaizenObserver R9 rule providing runtime verification.
- Reuses every substrate primitive (`e7m-dataset` / `datasetPin` /
  joucho cadence / InboxBuffer / KaizenObserver); no new substrate
  engine name is invented (per ADR-2605262130 Kotoba unification).

**Negative / cost**:

- Disk + IPFS pin footprint grows substantially. Rough Wave-1 estimate
  per node: RIR delegated ~ 50 MB, GeoLite2 ~ 200 MB, IANA root ~ 5
  MB, OSM Planet ~ 80 GB (per region extract optional). Wave-3 adds
  Rapid7 Sonar ~ 200 GB / month, OpenINTEL ~ 10 GB / day. Pin policy
  must include retention rules (Wave 3 ADR).
- Some Tier-C sources have terms-of-use acceptance requirements
  (Rapid7 Open Data, CZDS). Operator must accept those out-of-band per
  source before the fetcher will pull. The fetcher MUST refuse to run
  without an acceptance flag file in `~/.etzhayyim/source-acceptance/`.
- Adding KaizenObserver R9 increases per-tick overhead slightly (extra
  observation tag check); estimated < 1% on the existing 18,342-cell
  fleet (negligible).
- The Charter Rider scanner false-positive rate cap (5%) is
  speculative — Wave-1 will validate. If real-world FP is higher, G11
  triggers a Council-mediated threshold revision (which is itself part
  of the design, not a failure).

**Forward-compatibility**:

- The DatasetSensor Protocol is extensible — future Tier-A sources
  (e.g. open IXP peering data, open RPKI validator output, open ASN
  WHOIS deltas) can plug in without ADR amendment so long as the
  license tier and PII flag are explicit in the fetcher.
- A potential future "active probing" ADR (Council Lv6+) would
  introduce a separate `ActiveProbeSensor` Protocol orthogonal to
  this one; nothing in this design forecloses that path, but nothing
  in this design enables it either.

# Alternatives Considered

1. **Single unified data path (no perception / training split)**.
   Rejected — it conflates lazy in-memory sampling with full-shard
   training reads, breaks the joucho cadence cost model, and makes
   tier-leak detection harder.

2. **Direct sensor → vendor LLM (e.g. classification via OpenAI for
   complex Observations)**. Rejected — violates ADR-2605215000
   Murakumo-only inference invariant. Any classification an organism
   performs on perceived data goes through fleet inference.

3. **Active DNS / IP probing under organism control**. Rejected per
   user decision 2026-05-26 and CHARTER-RIDER §2(c). The risk of
   accidentally producing a covert-recon footprint at religious-corp
   scale is too high; passive archive consumption captures > 80% of
   the value at < 5% of the risk.

4. **Reject all NC-licensed sources**. Considered, rejected by user
   decision. Losing Rapid7 Sonar + CAIDA + OpenINTEL would gut the
   global DNS / AS-graph information the user explicitly asked for.
   The G13 fleet-internal carve-out is the proven mitigation pattern
   (precedent: ADR-2605262100 R1.4 corpus).

5. **Build a new substrate engine for time-series sensor data**.
   Rejected per ADR-2605262130 (Kotoba is the canonical substrate).
   In-memory streams + DataLad/IPFS-pinned shards + kotoba-kqe
   arrangements (if attribute indexing is needed later) cover the
   read pattern.

6. **Put everything under one Tier-A umbrella and re-license
   downstream**. Rejected — Charter Rider v2.0 §3 requires honest
   tier propagation; downstream re-licensing of NC source data is
   not legally available to us.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605171800 — LangGraph → MST → IPFS → L2 anchor pipeline
- ADR-2605172000 — RW-free substrate
- ADR-2605192100 — Mission Charter (Wellbecoming, 反個人主義)
- ADR-2605192200 — IP-Free-Release with Charter Compliance Rider v2.0
- ADR-2605215000 — Inference Murakumo-only (no RunPod)
- ADR-2605215100 — maps_sentinel_murakumo M1
- ADR-2605221411 — Artificial Organism Ecosystem
- ADR-2605232345 — UNSPSC actor as organism
- ADR-2605240200 — UNSPSC organism Kaizen self-reflection
- ADR-2605241500 — Dataset CID substrate (DataLad + annex + IPFS)
- ADR-2605262100 — baien-moemoekyun R1 Phase 0 (G13 NC carve-out precedent)
- ADR-2605262130 — Kotoba storage substrate unification
- ADR-2605262200 — CHARTER-RIDER §2(i) train-rental carve-out amendment (proposed)
- ADR-2605262300 — baien-moemoekyun R2+ rental train architecture (gated)
- CHARTER-RIDER.md §2 — 8 prohibited categories (a)..(h) and three-tier enforcement
- `70-tools/e7m-dataset/README.md` — fetcher + publish-ipfs + datasetPin contract
- `20-actors/magatama/py/src/pymagatama/organism/` — organism cadence + Kaizen + sensors
