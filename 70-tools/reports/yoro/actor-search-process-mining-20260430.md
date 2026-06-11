# YORO Actor Search Process Mining Snapshot

- generatedAt: 2026-04-30T03:34:30Z
- target surface: `https://yoro.etzhayyim.com/search`
- live AppView: `https://bsky.etzhayyim.com`
- AppView meta: `etzhayyim-appview`, version `0.1.0-scaffold`, ADR `2604231828`
- AppView health: ok at `2026-04-30T03:34:27.484Z`

## Objective

Confirm that infrastructure actors such as `ipaddress` and `dns` are observable as actor/agent profiles through the AppView search path after the RisingWave/AppView blocker.

## Runtime Event Model

For actor-quality enrichment, the observable process model remains:

1. `candidate.selected`
2. `xrpc.workflow.start.accepted`
3. `bpmn.actorQuality.task.started`
4. `bpmn.actorQuality.task.completed`
5. `repo.profile.self.written`
6. `repo.seedPost.written`
7. `appview.profile.visible`

For the `ipaddress`/`dns` AppView search blocker, the terminal conformance check is `appview.profile.visible` via `app.bsky.actor.searchActors`.

## Actor Search Conformance

Live XRPC checks against `https://bsky.etzhayyim.com/xrpc/app.bsky.actor.searchActors`:

| Query | Expected actor profile | Result |
| --- | --- | --- |
| `ipaddress` | `did:web:ipaddress.etzhayyim.com` / `ipaddress.etzhayyim.com` / `IP/ASN Intelligence` | pass, `totalActors=1` |
| `dns` | `did:web:scndu0rf.etzhayyim.com` / `dns.etzhayyim.com` / `DNS / Cloudflare Registrar` | pass, `totalActors=2` |

`dns` also returns `did:web:ipaddress.etzhayyim.com` because the IP/ASN profile description contains `reverse DNS`.

## Actor-Quality Runtime Snapshot

Command:

```sh
DATABASE_URL='REDACTED_USE_DATABASE_URL_ENV' \
  node 70-tools/scripts/yoro/actor-quality-process-mining.mjs --since-hours=24 --limit=500 --json
```

Summary:

| Metric | Value |
| --- | ---: |
| PDS accepted events | 139 |
| PDS ok events | 139 |
| PDS error events | 0 |
| PDS wall time p50 | 268 ms |
| PDS wall time p95 | 1562 ms |
| PDS wall time max | 19949 ms |
| BPMN activity rows | 718 |
| BPMN instance rows | 0 |
| BPMN signal rows | 0 |
| OCEL rows | 0 |
| reconstructed artifact cases | 126 |

Observed source groups:

| Source hint | Cases | With profile | With seed post |
| --- | ---: | ---: | ---: |
| controlled rollout batch 100 process mining 2026-04-29 | 84 | 84 | 84 |
| controlled rollout batch 25 phase 2026-04-29 | 25 | 25 | 25 |
| controlled rollout batch phase 2026-04-29 | 9 | 9 | 9 |
| unknown | 4 | 4 | 4 |
| llm profile seedfix live smoke 2026-04-29 | 1 | 1 | 1 |
| pilot actor quality dedicated appview fixed 2026-04-29 | 1 | 1 | 1 |
| pilot actor quality live backfill 2026-04-29 | 1 | 1 | 1 |
| manual SEO quality repair 2026-04-29 | 1 | 1 | 1 |

## Findings

- Blocker is resolved for the searched infrastructure actors: `ipaddress` and `dns` are visible through the live AppView actor search endpoint.
- Current search conformance depends on AppView fallback/merge behavior for core actors when RisingWave is degraded or sparse.
- Actor-quality mining has enough BPMN activity rows for task-level runtime analysis, but still lacks BPMN instance, BPMN signal, and OCEL rows.
- The next mining improvement is to close the observability gap by emitting process-instance and OCEL case events, so runtime conformance can be measured beyond artifact reconstruction.

## Next Step

Promote this to a recurring gate:

1. Run `actor-quality-process-mining.mjs` after each actor/profile backfill batch.
2. Add AppView terminal checks for core actor queries: `ipaddress`, `dns`, `cloudflare registrar`, and `yoro`.
3. Fail the gate if PDS ok rate drops below 100%, reconstructed profile+seed cases regress, or core actor search visibility disappears.
4. Add BPMN instance and OCEL emissions for the actor-quality path before raising batch size or concurrency.
