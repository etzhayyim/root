#!/usr/bin/env bash
# organism-pulse-deploy — regenerate the /organism live feeds and publish to etzhayyim.com.
#
# SUBSTRATE: ALL organism state is the kotoba Datom log (NO KV — CLAUDE.md substrate boundary).
# `bb vitals:pulse|joucho|report` transact into kotoba journals (80-data/{organism,vitals}/) and
# materialize content-addressed `.kotoba.edn` snapshots (public/organism/*.kotoba.edn) — THOSE are
# the canonical artifacts (like public/kotoba/blocks). The *.json the page reads are derived
# read-models/projections of those Datom logs.
#
# The CF Worker serves [assets] statically, so production "realtime" = re-running this on a cron
# (coarse cadence — 1–2 min — not the 6 s local loop, since each run re-deploys). `wrangler login`
# first (operator). Fuller path: the page queries the .kotoba.edn snapshot client-side (kotoba-wasm
# already at public/kotoba/) — then nothing but the Datom log is served. No KV anywhere.
#
# Usage:  ./scripts/organism-pulse-deploy.sh           # pulse only (fast feeds)
#         ./scripts/organism-pulse-deploy.sh --full      # also refresh vitals + joucho + trajectory
#
# Cron (every 2 min):  */2 * * * * cd <repo> && bb vitals:pulse && \
#   wrangler -c 50-infra/etzhayyim-did-web/wrangler.toml deploy >/dev/null 2>&1
set -euo pipefail
cd "$(dirname "$0")/../../.."        # repo root (etzhayyim/root)

echo "[organism] regenerating live feeds…"
bb vitals:pulse
if [[ "${1:-}" == "--full" ]]; then
  bb vitals:joucho
  bb vitals:trajectory >/dev/null 2>&1 || true
fi

echo "[organism] publishing to etzhayyim.com (wrangler deploy)…"
wrangler -c 50-infra/etzhayyim-did-web/wrangler.toml deploy
echo "[organism] live → https://etzhayyim.com/organism/"
