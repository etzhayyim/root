---
id: adr-2605172000-malak-onion-frontier-ransomware-tracking
title: "malak onion frontier expansion for ransomware actor tracking"
status: active
doc_type: adr
topic: malak-onion-frontier-ransomware-tracking
authoritative: true
last_verified: 2026-05-17
authoritative_for:
  - malak ransomware actor tracking from onion crawl metadata
  - onion crawl frontier expansion policy
  - Kotoba/Datomic-compatible publish pattern for ransomware_actor_activity
priority: 8.4
axis: malak-orchestration
weight: 0.84
related:
  - adr-2605131600-malak-orchestration-langgraph-pregel-langserve
  - adr-2605131500-malak-surveillance-collapse-from-mehikari
  - adr-2605151500-bitnest-exit-pursuit-pregel-link-back-pattern
supersedes: []
superseded_by: []
---

# Context

`malak` is the immune-system actor for cybercrime and threat tracking. The
existing onion crawl path could periodically revisit known `.onion` seeds,
but it only fetched depth-1 pages within the same hidden-service host. Links
to other `.onion` hosts were discarded, so ransomware leak-site and actor
infrastructure discovery could not expand from observed pages.

The production crawl also had operational fragility:

- `darkweb-proxy.etzhayyim.com/health` was accidentally served by the SvelteKit
  worker path instead of the Cloudflare Container companion.
- `onion_crawl_seeds` was not passing queued seeds into `process_queue`.
- The topology assistant state did not preserve `runs`, so the static graph
  fix was skipped at runtime.
- `crawler-resident` and the CronJob parsed run IDs with brittle grep
  patterns.
- `ransomware_actor_activity` attempted `ON CONFLICT`, which Kotoba/Datomic does
  not accept in the deployed path.

# Decision

Keep active probing out of `malak`, but make onion crawl metadata a growing
frontier for passive actor tracking.

1. `onion_crawl.py` now splits discovered onion links into:
   - same-host links fetched in the current depth-1 crawl;
   - cross-host `.onion` links inserted into `vertex_onion_site` as frontier.

2. Frontier rows use `last_seen = NULL`, so the next
   `onion_crawl_seeds` cycle claims them through the existing stale-seed
   mechanism.

3. Ransomware context is preserved:
   - pages classified as ransomware produce `ransomware-frontier` seeds;
   - actor keywords such as LockBit, Akira, ALPHV/BlackCat, Cl0p,
     Black Basta, RansomHub, Rhysida, Medusa, and Qilin populate
     `threat_actor_ref` when present.

4. Seed priority is now:
   - ransomware category first;
   - rows with `threat_actor_ref` second;
   - other stale/frontier rows after that.

5. `ransomware_actor_activity` consumes onion metadata and publishes Yabai
   rows with Kotoba/Datomic-compatible `DELETE -> INSERT` writes instead of
   `ON CONFLICT`.

6. Until a fresh image can be built, the live `langgraph-server` mounts a
   ConfigMap override for:
   - `pymagatama/langgraph_graphs/onion_crawl_seeds.py`
   - `pymagatama/primitives/onion_crawl.py`
   - `pymagatama/langgraph_graphs/ransomware_actor_activity.py`

   The Deployment includes a checksum annotation for the ConfigMap so future
   override changes roll the Pod automatically.

# Consequences

`malak` can now expand its `.onion` observation frontier without adding
exploit, negotiation, authentication-bypass, or intrusive behavior. The
system remains passive OSINT: it fetches public onion pages through the
existing Tor + Playwright `darkweb-proxy` and writes crawl metadata to
Kotoba/Datomic.

The current `langgraph-server` has one Granian worker. Long onion crawl runs
can temporarily occupy that worker and make readiness probes slow until the
run completes. This is acceptable for the current low-frequency 6-hour
cadence, but a future image/config rollout should increase worker count or
move crawl execution to a separate worker process if frontier volume grows.

# Verification

Verified on 2026-05-17:

- `darkweb-proxy.etzhayyim.com/health` returns 200 with Tor proxy status.
- `onion_crawl_seeds` CronJob is enabled: `suspend=false`, schedule
  `0 */6 * * *`.
- `langgraph-server`, `crawler-resident`, and `malak-langserver` are all
  ready.
- Manual frontier primitive run:
  `processed=1`, `completed=1`, `failed=0`, `frontierAdded=14`.
- Normal LangGraph API run:
  `queued=2`, `processed=2`, `completed=2`, `failed=0`,
  `pagesWritten=11`.
- `ransomware_actor_activity` run:
  `evaluated=4`, `active=4`, top actors include `LockBit` and `Akira`.
- Yabai publish after RW-compatible write fix:
  `entities=4`, `evidence=4`, `risks=4`, `alerts=4`, `ok=true`.
- `/healthz` and `/readyz` return 200; readyz reports `graphs=66`.

# References

- `20-actors/magatama/py/src/pymagatama/primitives/onion_crawl.py`
- `20-actors/magatama/py/src/pymagatama/langgraph_graphs/onion_crawl_seeds.py`
- `20-actors/magatama/py/src/pymagatama/langgraph_graphs/ransomware_actor_activity.py`
- `50-infra/vultr/mitama-langgraph-pool/templates/langgraph-server.yaml`
- `50-infra/vultr/mitama-langgraph-pool/templates/onion-crawl-seeds-override-configmap.yaml`
- `60-apps/etzhayyim-project-browser/provider/darkweb-proxy/wrangler.jsonc`
