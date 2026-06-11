# yabai Murakumo persistence

`YabaiTorTorrentCtiPersistenceCell` runs on `issachar` as a `lan-api` queue
worker through `kotoba-kotodama-cell-runner`.

The cell exposes:

- `GET /healthz` on port `13171`
- `GET /jobs`
- `POST /enqueue`

Jobs are stored in `cti-correlator-queue.sqlite3` with per-step checkpoints.
The worker executes `20-actors/yabai/methods/ingest.py`, `analyze.py`, and
`transact.py` immediately after enqueue. It also appends an execution marker to
`/var/lib/etzhayyim/yabai/cti-correlator-runs.ndjson` and falls back to
`20-actors/yabai/out/` if the system path is not writable.

Live Kotoba writes require `YABAI_GRAPH_CID` and either `KOTOBA_TOKEN` or
`KOTOBA_CACAO_B64`. Without those values the cell is a dry run but still keeps
the local durable marker. Set `YABAI_REQUIRE_LIVE=1` to fail the cron invocation
when live persistence credentials are missing.

Boundary: Tor data is public exit-node infrastructure only. BitTorrent rows are
accepted only as case-bound, evidence-backed `:btobs/*` observations; the actor
does not infer private-person identity or perform broad swarm surveillance.
