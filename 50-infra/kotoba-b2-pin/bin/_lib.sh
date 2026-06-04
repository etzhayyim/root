#!/usr/bin/env bash
# _lib.sh — shared config + secret resolution for kotoba-b2-pin.
#
# Substrate boundary (CLAUDE.md): IPFS is the cold *block* backend under the
# canonical kotoba Datom log (ADR-2605312345). This tool adds an even-colder,
# off-host durable tier — Backblaze B2 (S3-compatible) — reached through a
# git-annex special remote inside a DataLad dataset (the sanctioned
# DataLad + git-annex + IPFS-pinner pattern, ADR-2605241500). It mirrors raw
# IPFS *blocks* keyed by their CID; it is NOT a parallel canonical state.
#
# SECRETS (CLAUDE.md "Do not commit secrets"): B2 credentials are read at
# runtime from 1Password via `op` and exported only into the child process
# environment. They are NEVER written to this repo, the DataLad dataset, or the
# git-annex config (embedcreds=no). git-annex's S3 backend reads the standard
# AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY names, which we map from B2.
set -euo pipefail

# ---- config (override via env) ---------------------------------------------
: "${KOTOBA_IPFS_API:=http://127.0.0.1:5001}"          # kubo RPC (block put, refs)
: "${KOTOBA_IPFS_GATEWAY:=http://127.0.0.1:8080}"       # kubo gateway (?format=raw)
: "${KOTOBA_IPNS_HEADS:=$HOME/.local/kotoba-etzhayyim/sled/ipns-heads.json}"

# DataLad dataset that holds the annex index + B2 special remote.
# Default lives on the external volume so transient annex objects never pressure
# the internal boot disk; git metadata is tiny and the durable index.
: "${KOTOBA_B2_STORE:=/Volumes/260317/etzhayyim/kotoba-b2-pin-store}"

# B2 (S3-compatible) target. Bucket + region come from the operator / deps.toml
# convention (B2_ENDPOINT default region us-west-004).
: "${B2_S3_HOST:=s3.us-west-004.backblazeb2.com}"
: "${B2_KOTOBA_BUCKET:=etzhayyim-kotoba-blockstore}"
: "${B2_ANNEX_REMOTE:=b2}"

# 1Password item reference for the B2 application key. Override to match the
# actual vault/item. Fields expected: "access key id" + "secret access key"
# (or set B2_OP_KEYID_REF / B2_OP_SECRET_REF to full op:// references).
: "${B2_OP_ITEM:=Backblaze B2 — etzhayyim kotoba}"
: "${B2_OP_VAULT:=Private}"

log()  { printf '\033[2m[b2-pin]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[31m[b2-pin] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "missing tool: $1"; }

# Resolve B2 creds from 1Password into AWS_* env (git-annex S3 reads those).
# Honors pre-set AWS_ACCESS_KEY_ID/SECRET (CI / op run) — only calls op if unset.
load_b2_creds() {
  if [[ -n "${AWS_ACCESS_KEY_ID:-}" && -n "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
    log "B2 creds: using pre-set AWS_* env"
    return 0
  fi
  if [[ -n "${B2_ACCESS_KEY_ID:-}" && -n "${B2_SECRET_ACCESS_KEY:-}" ]]; then
    export AWS_ACCESS_KEY_ID="$B2_ACCESS_KEY_ID"
    export AWS_SECRET_ACCESS_KEY="$B2_SECRET_ACCESS_KEY"
    log "B2 creds: using pre-set B2_* env"
    return 0
  fi
  need op
  if [[ -n "${B2_OP_KEYID_REF:-}" && -n "${B2_OP_SECRET_REF:-}" ]]; then
    AWS_ACCESS_KEY_ID="$(op read "$B2_OP_KEYID_REF")"   || die "op read keyid failed (unlock 1Password: '! eval \$(op signin)')"
    AWS_SECRET_ACCESS_KEY="$(op read "$B2_OP_SECRET_REF")" || die "op read secret failed"
  else
    AWS_ACCESS_KEY_ID="$(op item get "$B2_OP_ITEM" --vault "$B2_OP_VAULT" --fields label='access key id' --reveal 2>/dev/null)" \
      || die "op item get failed — unlock 1Password ('! eval \$(op signin)') and/or set B2_OP_ITEM/B2_OP_VAULT or B2_OP_KEYID_REF/B2_OP_SECRET_REF"
    AWS_SECRET_ACCESS_KEY="$(op item get "$B2_OP_ITEM" --vault "$B2_OP_VAULT" --fields label='secret access key' --reveal 2>/dev/null)" \
      || die "op item get (secret) failed"
  fi
  export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
  log "B2 creds: loaded from 1Password (item: $B2_OP_ITEM)"
}

ipfs_api() {  # ipfs_api <path> [curl-args...]
  local path="$1"; shift
  curl -fsS -m 120 -X POST "$KOTOBA_IPFS_API/api/v0/$path" "$@"
}
