# claim-consumer actor

Python LangServer worker for claim.gftd.ai operational tasks that should not run in
Cloudflare Workers.

## Tasks

- `claim.unchallenged.sweep`
  - scans expired pending claims without challenges from RisingWave
  - re-scores expired claims with Murakumo
  - persists witness alarms to `vertex_yoro_monitor_attestation`
  - submits the unchallenged claim batch to authz via HMAC

Cloudflare remains the edge/router surface. Long scans, model calls, and
settlement batch orchestration live here.
