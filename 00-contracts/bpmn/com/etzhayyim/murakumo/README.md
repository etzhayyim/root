# com.etzhayyim.murakumo BPMN — etzhayyim variant

BPMN process contracts for the etzhayyim distributed murakumo cluster. Verdicts assigned per **ADR-2605214000 §2** substrate-fit rules.

## Verdicts (2026-05-21)

| File | bpmn:id | Verdict | Adaptation |
|---|---|---|---|
| `cronTick.bpmn` | `murakumo_cron_tick` | **PORT-adapted** | XRPC endpoint default: `murakumo.etzhayyim.com` → `murakumo.etzhayyim.com`. Process structure + bpmn:id stable. |
| `fleetHealthCheck.bpmn` | `murakumo_fleet_health_check` | **PORT-direct** | No vendor infrastructure coupling. Substrate-fit conditions 1–5 all met as-is. |

## Migration source

The vendor directory (`etzhayyim.com/etzhayyim-apps-etzhayyimcojp/00-contracts/bpmn/com/etzhayyim/murakumo/`) **does not exist** in the current vendor repo state — these two BPMN files are religious-corp-originated, written for etzhayyim under ADR-2605202100 (magatama-cell-runner launchd) and ADR-2605191645 (heartbeat). They are listed under `com.etzhayyim.*` NSID per the shared-namespace pattern (ADR-2605214000 §2 namespace placement rule).

## Substrate-fit conditions (recap)

1. No required RisingWave / Hyperdrive / Postgres-only field or referenced table.
2. No required commercial K8s control-plane primitive (Karmada, VKE LoadBalancer, k3s API).
3. No required fiat payment processor.
4. No required commercial SaaS dependency (RunPod, Linode GPU, vendor-billed OpenAI/Anthropic key).
5. AT MST + IPFS + Base L2 + LanceDB-WASM + tonbo + yata CRDT + Pregel cells cover the read/write path.

Both BPMN files pass all five conditions. The `cronTick.bpmn` adaptation is limited to one endpoint default URL — process bpmn:id, task definitions, and event flows are byte-stable.

## Constraints

- **Do not rename bpmn:id** — these IDs are shared with any vendor implementation that adopts the same process definitions. Renaming breaks downstream registries (process_def lookup, BPMN dispatcher routing).
- Endpoint defaults inside `<extensionElements>` or `<bpmn:documentation>` may be PORT-adapted (vendor → etzhayyim URL) — wire shape is preserved.
- Required input/output variables on user tasks and service tasks must stay byte-identical for vendor/religious-corp interop.

## See also

- ADR-2605214000 — Murakumo distributed cluster (no-VKE mesh) + vendor→religious-corp lexicon port rules
- ADR-2605202100 — magatama-cell-runner launchd LaunchAgent (origin of cronTick contract)
- ADR-2605191645 — heartbeat (origin of fleetHealthCheck contract)
- `00-contracts/lexicons/com/etzhayyim/murakumo/README.md` — sister registry for murakumo lexicons
- `50-infra/cluster/murakumo/cell-runner/com.etzhayyim.magatama-cell-runner.plist` — launchd binding that fires these BPMN definitions
