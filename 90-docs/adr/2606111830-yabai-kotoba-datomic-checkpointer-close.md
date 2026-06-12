# ADR-2606111830: Yabai CTI queue/checkpointer closed on Kotoba Datomic

Status: accepted
Date: 2026-06-11

## Context

`YabaiTorTorrentCtiPersistenceCell` was moved from cron-style execution to a
job queue/checkpointer so work can start immediately when queued and so
Murakumo resources are used continuously instead of waiting for a schedule tick.

The queue/checkpoint store must be the Kotoba Datom log, not SQLite. This keeps
Yabai CTI persistence under ADR-2605262130 and ADR-2605231525: canonical Kotoba
state, no platform-held key, and append-only operational history.

## Decision

Use a local Kotoba server on issachar as the Datomic endpoint for the Yabai
queue/checkpointer:

- `KOTOBA_URL=http://127.0.0.1:8077`
- queue graph `bafyreibecj2jpykhim5loq4q3qcfottu6v2xqziktv5kdqxvq5rslqtvei`
- graph name seed `KotobaCid::from_bytes(b"etzhayyim/yabai/cti-persistence-queue")`
- Yabai API worker on `127.0.0.1:13171`
- `KOTOBA_TOKEN` is supplied from the local process/launchd environment and is
  not committed

The worker installs queue schema into the graph, enqueues jobs as Datomic entity
maps, records step checkpoints as Datomic entities, and updates job status in
the same graph. SQLite is not a fallback.

## Boundaries

The CTI actor remains defensive:

- Tor input is public exit-node infrastructure only.
- BitTorrent input is case-bound, evidence-backed observation only.
- The actor does not deanonymize private persons, infer real-world identity, or
  perform broad swarm surveillance.

## Close Record

Closed live on issachar on 2026-06-11 JST.

Verified:

- Kotoba server listening on `*:8077`
- Yabai worker listening on `127.0.0.1:13171`
- `GET /healthz` reports `store=kotoba-datomic`
- `POST /enqueue` writes a Datomic job
- the worker processed the smoke job to `done`
- `/jobs?limit=5` returns Datomic-backed jobs

Observed process snapshot at close:

- Kotoba server PID `53503`
- Yabai worker PID `53964`
- queue health `{"done": 5}`

The launchd plists are placed on issachar. Remote SSH `launchctl bootstrap`
against the user/gui domains was rejected by macOS session-domain policy, so the
close verification used the same environment via `nohup`. On next interactive
login or root bootstrap, the installed LaunchAgents can take over the same
configuration.

## Consequences

Yabai CTI persistence is now event-driven and checkpointed in Kotoba Datomic.
The queue has no cron wait and no SQLite state. If Kotoba is unavailable, the
worker fails closed instead of silently using a side store.
