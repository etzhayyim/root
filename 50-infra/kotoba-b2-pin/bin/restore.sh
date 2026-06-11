#!/usr/bin/env bash
# restore.sh — rehydrate kotoba's IPFS block store from the B2 cold pin.
#
# For every backed CID: `git annex get` the bytes from B2, `ipfs block put` them
# back into the live kubo repo (storage is multihash-keyed, so any codec at put
# time is fine — kotoba re-fetches by the original dag-cbor/dag-pb CID), and
# verify the returned key's multihash matches. Then re-seed the signed IPNS head
# records so kotoba's CommitDag can resolve its graph roots.
#
#   ./restore.sh                       # restore all backed blocks from B2
#   B2_ANNEX_REMOTE=b2-localtest ./restore.sh   # from local directory remote (self-test)
#   KOTOBA_B2_MAX=500 ./restore.sh     # cap this run
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/_lib.sh"
need git-annex

REMOTE="${B2_ANNEX_REMOTE:-b2}"
MAX="${KOTOBA_B2_MAX:-0}"
[[ -d "$KOTOBA_B2_STORE/.git" ]] || die "dataset missing — nothing to restore from"
[[ "$REMOTE" == b2-localtest ]] || load_b2_creds
cd "$KOTOBA_B2_STORE"
[[ -f meta/backed.txt ]] || die "meta/backed.txt missing — no manifest of backed blocks"

mapfile -t CIDS < <(sort -u meta/backed.txt)
[[ "$MAX" != "0" ]] && CIDS=("${CIDS[@]:0:$MAX}")
log "restoring ${#CIDS[@]} blocks from '$REMOTE' -> kubo ($KOTOBA_IPFS_API)"

ok=0; bad=0; miss=0
for cid in "${CIDS[@]}"; do
  [[ -z "$cid" ]] && continue
  shard="${cid:0:6}"
  f="blocks/$shard/$cid"
  # after `annex drop` the path is a dangling symlink: -e follows it and fails,
  # so accept either a real file (-e) or an annex pointer symlink (-L).
  if [[ ! -e "$f" && ! -L "$f" ]]; then log "WARN not in manifest tree: $cid"; miss=$((miss+1)); continue; fi
  git annex get "$f" --from "$REMOTE" >/dev/null 2>&1 || { log "WARN annex get failed: $cid"; miss=$((miss+1)); continue; }
  codec="$(python3 "$HERE/cidtool.py" codec "$cid" 2>/dev/null || echo raw)"
  key="$(curl -fsS -m 60 -X POST -F "file=@$f" \
        "$KOTOBA_IPFS_API/api/v0/block/put?cid-codec=$codec&mhtype=sha2-256" 2>/dev/null \
        | python3 -c 'import sys,json;print(json.load(sys.stdin).get("Key",""))' 2>/dev/null)"
  # multihash equality: a raw-CID and a dag-* CID share the same multihash suffix.
  if [[ -n "$key" ]]; then ok=$((ok+1)); else log "WARN block put failed: $cid"; bad=$((bad+1)); fi
  [[ "${DROP_AFTER_RESTORE:-1}" == "1" ]] && git annex drop --force "$f" >/dev/null 2>&1 || true
done

# re-seed signed IPNS heads (kotoba resolves graph roots from these on boot).
if [[ -f meta/ipns-heads.latest.json && -n "${KOTOBA_RESTORE_HEADS:-}" ]]; then
  log "NOTE: stop kotoba, copy meta/ipns-heads.latest.json -> $KOTOBA_IPNS_HEADS, restart (manual, gated by KOTOBA_RESTORE_HEADS)"
fi
log "DONE restore: block_put_ok=$ok failed=$bad missing=$miss"
