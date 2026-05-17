#!/usr/bin/env sh
# init-config.sh — first-boot Kubo setup for ipfs.etzhayyim.com (ADR-2604261936).
#
# Phase 1 ships with the **default flatfs+levelds** layout `ipfs init`
# generates on a fresh repo — the official `ipfs/kubo` image does NOT
# bundle the `s3ds` (`go-ds-s3`) plugin, so swapping in a B2-backed
# datastore would crash the daemon with `unknown datastore type: s3ds`.
# Phase 1.5 will introduce a custom Kubo image
# (`ghcr.io/etzhayyim/kubo-s3ds:0.31.x`) compiled with go-ds-s3 baked in,
# and at that point this script reapplies `Datastore.Spec` from the
# rendered B2 spec. The reference B2 spec lives at
# `config/datastore_spec_b2.json`.
#
# Idempotent: this script only patches the bits we care about (gateway,
# swarm conn manager) on top of the canonical `ipfs init --profile server`
# defaults. It runs on every pod start; the canonical datastore_spec
# fingerprint is owned by Kubo and never overwritten here.
#
# Env contract (provided by the StatefulSet):
#   IPFS_PATH = /data/ipfs   (volumeMount of PVC kubo-repo)

set -eu

: "${IPFS_PATH:=/data/ipfs}"
export IPFS_PATH

if [ ! -f "$IPFS_PATH/config" ]; then
  echo "[init] no repo at $IPFS_PATH; initializing with profile=server"
  ipfs init --profile server --empty-repo
else
  echo "[init] existing repo at $IPFS_PATH, patching config in place"
fi

# Public gateway: no listing, no writable, CORS open for read GETs.
ipfs config --json Gateway.NoFetch false
ipfs config --json Gateway.PublicGateways '{"ipfs.etzhayyim.com":{"Paths":["/ipfs","/ipns"],"UseSubdomains":false,"NoDNSLink":false}}'
ipfs config --json Gateway.HTTPHeaders.Access-Control-Allow-Methods '["GET","HEAD","OPTIONS"]'
ipfs config --json Gateway.HTTPHeaders.Access-Control-Allow-Origin '["*"]'

# API: bind on 0.0.0.0 inside cluster only (Service is ClusterIP). The CF
# Worker is the only thing that should ever talk to it; HMAC enforcement
# happens at the Worker layer.
ipfs config Addresses.API "/ip4/0.0.0.0/tcp/5001"
ipfs config Addresses.Gateway "/ip4/0.0.0.0/tcp/8080"

# Swarm: keep `server` profile defaults (filters out RFC1918 etc.) and cap
# the connection manager so a public swarm doesn't OOM the 4 Gi pod.
ipfs config --json Swarm.ConnMgr.LowWater 200
ipfs config --json Swarm.ConnMgr.HighWater 400
ipfs config Swarm.ConnMgr.GracePeriod 30s

echo "[init] done. Repo at $IPFS_PATH (Phase 1: flatfs+levelds, B2 in Phase 1.5)"
