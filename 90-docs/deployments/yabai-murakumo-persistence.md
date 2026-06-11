# yabai Murakumo persistence

`YabaiTorTorrentCtiPersistenceCell` runs on `issachar` as a `lan-api` queue
worker through `kotoba-kotodama-cell-runner`.

The cell exposes:

- `GET /healthz` on port `13171`
- `GET /jobs`
- `POST /enqueue`

Jobs are stored in the Kotoba Datomic graph
`etzhayyim/yabai/cti-persistence-queue` with per-step checkpoints.
The worker executes `20-actors/yabai/methods/ingest.py`, `analyze.py`, and
`transact.py` immediately after enqueue. It also appends an execution marker to
`/var/lib/etzhayyim/yabai/cti-correlator-runs.ndjson` and falls back to
`20-actors/yabai/out/` if the system path is not writable.

The queue/checkpointer itself requires a reachable Kotoba Datomic node:

- `KOTOBA_URL`, defaulting to `http://127.0.0.1:8077`
- `KOTOBA_TOKEN` or `KOTOBA_SESSION_POP` for writes
- optional `YABAI_QUEUE_GRAPH`, defaulting to `etzhayyim/yabai/cti-persistence-queue`

Actor graph writes still require `YABAI_GRAPH_CID` and a Kotoba write credential.
Without those actor graph values the pipeline records the job/checkpoint in
Kotoba Datomic and keeps the local marker, but the actor graph step remains a
dry run. Set `YABAI_REQUIRE_LIVE=1` to fail the job when actor graph persistence
credentials are missing.

Boundary: Tor data is public exit-node infrastructure only. BitTorrent rows are
accepted only as case-bound, evidence-backed `:btobs/*` observations; the actor
does not infer private-person identity or perform broad swarm surveillance.
