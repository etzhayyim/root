#!/usr/bin/env bash
# init-store.sh — one-time: create the DataLad dataset + git-annex remotes that
# back the kotoba IPFS block store to Backblaze B2.
#
#   ./init-store.sh                 # create dataset + B2 (S3) special remote (needs op-unlocked B2 creds)
#   B2_TEST_DIR=/tmp/b2sim ./init-store.sh --test-only   # local 'directory' remote only (no creds)
#
# git-annex S3 special remote is created with embedcreds=no: credentials live in
# the environment (AWS_*, mapped from 1Password by _lib.sh) — never in the repo.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/_lib.sh"

TEST_ONLY=0; [[ "${1:-}" == "--test-only" ]] && TEST_ONLY=1

need datalad; need git; need git-annex

if [[ ! -d "$KOTOBA_B2_STORE/.git" ]]; then
  log "creating DataLad dataset: $KOTOBA_B2_STORE"
  mkdir -p "$(dirname "$KOTOBA_B2_STORE")"
  datalad create "$KOTOBA_B2_STORE" >&2
else
  log "DataLad dataset already exists: $KOTOBA_B2_STORE"
fi
cd "$KOTOBA_B2_STORE"
mkdir -p blocks meta

# Optional local 'directory' remote — lets the whole add->copy->drop->get cycle
# be exercised with zero credentials (used by the self-test).
if [[ -n "${B2_TEST_DIR:-}" ]]; then
  if ! git annex info b2-localtest >/dev/null 2>&1; then
    mkdir -p "$B2_TEST_DIR"
    log "initremote b2-localtest (directory $B2_TEST_DIR)"
    git annex initremote b2-localtest type=directory directory="$B2_TEST_DIR" encryption=none
  else
    log "remote b2-localtest already initialised"
  fi
fi

if [[ "$TEST_ONLY" == "0" ]]; then
  load_b2_creds
  if git annex info "$B2_ANNEX_REMOTE" >/dev/null 2>&1; then
    log "remote $B2_ANNEX_REMOTE already initialised"
  else
    log "initremote $B2_ANNEX_REMOTE (S3 -> $B2_S3_HOST / bucket $B2_KOTOBA_BUCKET / prefix $B2_FILEPREFIX)"
    git annex initremote "$B2_ANNEX_REMOTE" \
      type=S3 \
      host="$B2_S3_HOST" port=443 protocol=https \
      bucket="$B2_KOTOBA_BUCKET" \
      fileprefix="$B2_FILEPREFIX" \
      datacenter="$B2_S3_REGION" \
      signature=v4 \
      encryption=none embedcreds=no \
      autoenable=true
  fi
fi

log "init complete. dataset=$KOTOBA_B2_STORE"
git annex info 2>/dev/null | sed 's/^/  /' >&2 || true
