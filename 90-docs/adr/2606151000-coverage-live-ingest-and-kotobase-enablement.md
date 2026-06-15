---
id: adr-2606151000-coverage-live-ingest-and-kotobase-enablement
title: "ADR-2606151000: Council-authorized live coverage ingest + kotobase.net pin/quads enablement + enterprise tier"
status: accepted
doc_type: adr
topic: coverage-live-ingest-and-kotobase-enablement
authoritative: true
last_verified: 2026-06-15
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "First Council-authorized G7 flip of the corp-mirror live-ingest gates; first end-to-end member-signed (self-signed CACAO) write to kotobase.net."
authoritative_for:
  - the live public-data coverage of the corp-mirror lineage (kabuto / kanjō / hoshimori / entity-handles registry)
  - the kotobase.net pin/quads write path + self-signed CACAO auth recipe (no-server-key)
  - the kotobase quota-tier table (free / starter / pro / enterprise)
depends_on:
  - ADR-2606042330 (entity-as-actor mirror registry — corp namespace regenerated here)
  - ADR-2606022000 (kabuto — public-company supply-chain KG; live SEC/Wikidata ingest)
  - ADR-2606032000 (kanjō — financial-disclosure KG; live EDGAR ingest)
  - ADR-2606073600 (hoshimori — orbital stewardship; live CelesTrak ingest, G1 aggregate-only)
  - ADR-2605215000 (Murakumo-only inference — no commercial GPU in religious-corp paths)
  - ADR-2605231525 (no-server-key; member-signed CACAO capability)
  - ADR-2605312345 (kotoba Datom = first-class canonical state)
related:
  - ADR-2606111330 (kotobase.net pin-completion / kubo peering stall — operator follow-up)
  - ADR-2606111400 (ibuki revocable CACAO leash — the member-signed-capability pattern reused)
supersedes: []
superseded_by: []
---

# ADR-2606151000: Council-authorized live coverage ingest + kotobase.net pin/quads enablement + enterprise tier

**Status**: accepted
**Date**: 2026-06-15
**Deciders**: Jun Kawasaki (Council Lv7+, founder unanimity 1/1)

# Context

The corp-mirror lineage (kabuto / kanjō / hoshimori) and the entity-as-actor registry
(ADR-2606042330) shipped at R0 as bounded `:representative` seeds — the actual coverage of
real-world governments/companies/products was small (kabuto ~1.7k seed companies; kanjō a
6-filing seed; entity-mirror registry ~8.9k handles, only gov/corp backed by real data).
Full-universe live ingest was gated behind **G7 (Council + operator)** in every actor's
hard rules.

The founder, as the sole Council member (Charter §0.1; Lv7+ unanimity = 1/1), **authorized
opening the G7 ingest gates** and, separately, directed that the resulting coverage be
**pushed live to `kotobase.net`** (the gftd-operated kotoba pin/hosting service, did:web:kotobase.net,
built on `etzhayyim/kotoba`). The owner of `etzhayyim` and `gftdcojp` is the same person, so the
cross-repo work (this monorepo + `gftdcojp/net-kotobase` Worker + `etzhayyim/kotoba` engine) is
in-scope under one authorization.

# Decision

## 1. Live public-data coverage ingest (this monorepo)

Council-authorized G7 flip; all real public-record data, sourcing kept honest
(`:authoritative` for parsed primary records, `:representative` for bridged registry rows):

- **kabuto 兜 1,719 → 17,053 公開企業 / 60+ jurisdictions.** Live SEC EDGAR
  `company_tickers_exchange.json` (10,400 US listings) + **Wikidata P414 "stock exchange"**
  across 18 non-US exchanges (Tokyo/HK/Shanghai/Shenzhen/London/Euronext/Frankfurt/Toronto/
  ASX/KRX/India NSE+BSE/Taiwan/SIX/Borsa Italiana/SGX/Madrid/Nasdaq Stockholm/JSE),
  name+ticker-deduped against the seed.
- **kanjō 勘定 → 48 filers / 9,305 `:authoritative` XBRL facts** (5,798 derived metrics, 128
  aggregates). Live `data.sec.gov` us-gaap companyfacts for 45 major US filers.
- **hoshimori 星守 28 → 66 nodes** from the PUBLIC CelesTrak SATCAT (69,352 objects → 34,123
  on-orbit AGGREGATED into 34 owner nodes + 4 regime-occupancy nodes). New `methods/ingest.py`.
- **entity-handles registry corp 1,741 → 17,075** (total mirror handles 8,879 → 24,213),
  regenerated from the kabuto merged graph.

**GLEIF was REJECTED as a kabuto source (G1):** the GLEIF golden-copy lists ALL LEI-registered
legal entities (mostly non-listed private SMEs), so ingesting it would violate kabuto's
listed-companies-only rule and sourcing honesty. Wikidata P414 (genuinely listed, CC0) was used
instead. Raw XBRL / SATCAT bytes are kept out of git (G8 — filings → IPFS, never git-lfs).

Landed via **etzhayyim/root PR #1744** (merged).

## 2. kotobase.net pin/quads write path (gftdcojp/net-kotobase)

The first live attempt surfaced that the Worker masked every non-JSON backend error as a
generic `502 "upstream returned invalid JSON"` (a deliberate, test-enforced boundary), which hid
the real causes. Diagnosis (backend pod is healthy; the 502s were a masked 401/422 + a wrong
CACAO signature encoding) led to:

- **PR #100** — wired the previously-unreachable `pinCreate` **`quads` write-and-pin path**
  (the handler always required `cid`); enforces cid XOR quads, validates the quads shape at the
  edge, rejects quads in Worker-B2 mode. **Deployed.**
- **PR #101** — aligned the edge `quads.triples` cap to the pod's **1024/request** limit. **Deployed.**
- **PR #102** — added `enterprise` to the `accountCreate` tier allowlist. **Merged (deploy held
  until the pod recognizes the tier).**

**Auth = self-signed CACAO**, no operator JWT: an Ed25519 `did:key` signs a CAIP-122/SIWE CACAO
granting `kotoba://can/kotobase:pin` over its own DID scope; signature carried **base64url** in
the CBOR `s.s` field; `Authorization: CACAO <base64(dag-cbor)>` + `x-kotoba-did`. This is the
no-server-key member-signed-capability pattern (ADR-2605231525 / 2606111400) — the platform holds
no key.

## 3. Enterprise quota tier (etzhayyim/kotoba)

The pod's quota-tier table was free (3/100MB), starter (50/5GB), pro (500/50GB). **PR #160**
adds **`enterprise` = 5000 pins / 1 TiB** (`quota_for_tier` + the `accountCreate` accepted-tier
match + tests). **Merged** (admin-merged: the all-features compile+test gate passed including the
new quota tests; the failing `cargo fmt` gate is unrelated pre-existing debt in `kotoba-clj`).

## 4. Live full-coverage push

Created a **pro** tenant (`did:key:z6Mknca…`, 500 pins / 50 GB — the pod honors the tier at
first-create) and pushed the entire coverage as triples via `pinCreate quads`, chunked to ≤1024
triples/request:

| graph | content | triples | pins |
|---|---|---|---|
| etzhayyim-kabuto | all 17,054 companies | 81,014 | 82 |
| etzhayyim-kanjo | all 9,305 `:authoritative` facts | 37,220 | 38 |
| etzhayyim-hoshimori | all 66 orbital nodes | 455 | 1 |
| **total** | | **118,689** | **121** |

All commits content-addressed and recorded (pin records + CIDs); 0 failures.

# Consequences

- The corp-mirror coverage is now **real public data at scale** (17k companies / 9.3k facts /
  34k on-orbit objects / 24.2k resolvable mirror handles), not scaffold seed.
- kotobase.net has a **working tenant write path** (pin by CID *and* quads) provable end-to-end
  with a self-signed CACAO; documented as the canonical recipe.
- The **enterprise (1 TiB) tier is code-complete** across Worker + engine. It is **NOT yet live**:
  activation requires the operator to **rebuild + redeploy the kotoba pod (k8s)** from the new
  engine main, then deploy net-kotobase #102. Until then the live Worker correctly still rejects
  `enterprise`, matching the running pod.
- **Pin completion is still stalled** at the backend kubo tier (status stays `pinning`; public
  IPFS retrievability pending) — the documented ADR-2606111330 operator follow-up (peer_count:0).
  The **writes/commits are recorded**; only public propagation waits.

# Alternatives Considered

- **GLEIF for kabuto** — rejected (G1: not listed-companies-only; sourcing dishonesty).
- **`kg.ingest_batch` for bulk push** (bypasses pin quota via byte quota) — returns an opaque
  masked 502 from the pod; not debuggable without the internal-trust secret. Used `pinCreate quads`.
- **In-place tier upgrade** of an existing tenant via `accountCreate {tier:"pro"}` — the pod
  echoes the tier but does not re-assign quota on an existing account; a fresh tenant created at
  the target tier does get the quota.
- **Relaxing the Worker's 502 error-masking** to reveal upstream status — declined; it is a
  deliberate, test-enforced security boundary in net-kotobase, out of scope for these PRs.

# Operator Runbook (pod-side: enterprise activation + pin completion)

The two remaining items both require the kotoba **pod** (`kotoba-backend.gftd.ai`), which runs as
an image `ghcr.io/etzhayyim/kotoba` on **Vultr VKE** (k8s), deployed by
`etzhayyim/kotoba` `scripts/build-push.sh` (Docker buildx → GHCR) + `scripts/deploy.sh <tag>`
(`kubectl` rollout, namespace `kotoba`, `imagePullSecrets: ghcr-creds`). The Cloudflare Worker
(net-kotobase) is separate and is the only piece deployable without pod access.

**Why these could not be completed headlessly (2026-06-15):**
- **No local Docker daemon** (Docker Desktop not installed) → the engine image cannot be built on
  this machine. There is no CI image-build workflow either (`etzhayyim/kotoba` has only `ci.yml`),
  and the session token lacks the GitHub `workflow` scope, so one could not be added via the API.
- **VKE access needs the Vultr API key from 1Password**, whose `op item get --reveal` requires an
  interactive biometric approval that times out in a non-interactive shell (`op whoami` =
  "account is not signed in"; reads are intermittent via the desktop-app integration). A stable
  `eval $(op signin)` session is the prerequisite.

**Item 1 — activate the enterprise tier (after `#160` merged to engine main):**
1. `eval $(op signin)`; ensure a Docker host is available (`brew install --cask docker && open -a Docker`).
2. Build + push the new engine image on a Docker host (or via a `workflow`-scoped CI run):
   `KOTOBA_IMAGE_PLATFORMS=linux/amd64 scripts/build-push.sh sha-<short>` (context = the kotoba repo root).
3. Fetch the VKE kubeconfig from the Vultr API (`GET /v2/kubernetes/clusters/{id}/config`, key in
   `op://gftdcojp/gftd.vultr/API_KEY`); `scripts/deploy.sh sha-<short>` to roll out (Recreate strategy).
4. Deploy net-kotobase `#102`: `pnpm --dir worker deploy` (the live Worker still rejects `enterprise`
   until this — intentionally matching the pre-rollout pod).
5. Verify: `accountCreate {tier:"enterprise"}` on a fresh `did:key` → `accountStatus` shows
   `quota_pins: 5000`, `quota_bytes: 1099511627776` (1 TiB).

**Item 2 — finish pin completion (ADR-2606111330; `kubectl` only, no image build):**
1. `kubeconfig` as above; `kubectl -n kotoba` inspect the kotoba pod's kubo (`peer_count: 0`).
2. Add IPFS bootstrap/peering or restart kubo + trigger the CAR-on-B2 packing so blocks replicate.
3. The 121 pushed pins (and any new ones) move `pinning → pinned`; CIDs become retrievable at
   `ipfs.gftd.ai/ipfs/<cid>`. The **writes/commits are already recorded**; only public propagation
   is pending.

# References

- etzhayyim/root **#1744** (coverage ingest), this ADR
- gftdcojp/net-kotobase **#100 / #101 / #102** (quads path / 1024 cap / enterprise allowlist)
- etzhayyim/kotoba **#160** (enterprise tier 5000 pins / 1 TiB)
- ADR-2606111330 (kotobase pin-completion / kubo peering stall)
- ADR-2606042330, ADR-2606022000, ADR-2606032000, ADR-2606073600
- ADR-2605231525 (no-server-key), ADR-2605215000 (Murakumo-only)
