#!/usr/bin/env bash
# pin-snapshot.sh — mirror the kotoba IPFS block store to B2 (durable cold pin).
#
# For every block in the local kubo repo (`ipfs refs local` — multihash-keyed,
# complete coverage), fetch the raw bytes, add to the DataLad/git-annex dataset
# keyed by its CID, copy to the B2 special remote, then drop the local annex
# copy (the bytes live in kubo + B2 — no third copy bloats disk). Incremental:
# only blocks not already recorded in meta/backed.txt are processed.
#
#   ./pin-snapshot.sh                 # to B2 (default remote)
#   B2_ANNEX_REMOTE=b2-localtest ./pin-snapshot.sh   # to local directory remote (self-test)
#   KOTOBA_B2_MAX=500 ./pin-snapshot.sh              # cap blocks this run (batching)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/_lib.sh"
need git-annex; need datalad

REMOTE="${B2_ANNEX_REMOTE:-b2}"
MAX="${KOTOBA_B2_MAX:-0}"          # 0 = no cap
BATCH="${KOTOBA_B2_BATCH:-200}"
DROP_LOCAL="${KOTOBA_B2_DROP_LOCAL:-1}"

[[ -d "$KOTOBA_B2_STORE/.git" ]] || die "dataset missing — run init-store.sh first"
[[ "$REMOTE" == b2-localtest ]] || load_b2_creds
cd "$KOTOBA_B2_STORE"
mkdir -p blocks meta
touch meta/backed.txt
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

# self-heal: anything git-annex already tracks as present on the remote counts as
# backed (recovers partial prior runs without re-uploading). Location tracking is
# local metadata — no B2 round-trip, no creds needed.
git annex find --in "$REMOTE" 2>/dev/null | while IFS= read -r f; do basename "$f"; done >> meta/backed.txt
sort -u meta/backed.txt -o meta/backed.txt

# 1) snapshot the durable roots (small, kept in git): signed IPNS head records.
if [[ -f "$KOTOBA_IPNS_HEADS" ]]; then
  cp "$KOTOBA_IPNS_HEADS" "meta/ipns-heads.$STAMP.json"
  cp "$KOTOBA_IPNS_HEADS" "meta/ipns-heads.latest.json"
fi

# 2) full local block set (raw CIDs) minus what we've already backed.
log "enumerating local blocks (ipfs refs local) ..."
ipfs_api refs/local | python3 -c 'import sys,json
[print(json.loads(l)["Ref"]) for l in sys.stdin if l.strip()]' \
  | sort -u > meta/refs.$STAMP.txt
TOTAL=$(wc -l < meta/refs.$STAMP.txt | tr -d ' ')
comm -23 meta/refs.$STAMP.txt <(sort -u meta/backed.txt) > meta/todo.$STAMP.txt
NEW=$(wc -l < meta/todo.$STAMP.txt | tr -d ' ')
log "blocks: total=$TOTAL already_backed=$(wc -l < meta/backed.txt | tr -d ' ') new=$NEW"
[[ "$MAX" != "0" ]] && { head -n "$MAX" meta/todo.$STAMP.txt > meta/todo.$STAMP.cap && mv meta/todo.$STAMP.cap meta/todo.$STAMP.txt; NEW=$(wc -l < meta/todo.$STAMP.txt|tr -d ' '); log "capped to $NEW (KOTOBA_B2_MAX=$MAX)"; }

[[ "$NEW" -eq 0 ]] && { log "nothing new to back up. up to date."; exit 0; }

# 3) fetch -> add -> copy -> drop, in batches.
done_total=0; fail=0
mapfile -t ALL < meta/todo.$STAMP.txt
i=0
while [[ $i -lt ${#ALL[@]} ]]; do
  added=()
  for ((j=0; j<BATCH && i<${#ALL[@]}; j++, i++)); do
    cid="${ALL[$i]}"
    [[ -z "$cid" ]] && continue
    shard="${cid:0:6}"
    out="blocks/$shard/$cid"
    mkdir -p "blocks/$shard"
    if ipfs_api "block/get?arg=$cid" --output "$out" 2>/dev/null && [[ -s "$out" ]]; then
      added+=("$out")
    else
      log "WARN fetch failed: $cid"; rm -f "$out"; fail=$((fail+1))
    fi
  done
  [[ ${#added[@]} -eq 0 ]] && continue
  # Resilient batch: a transient B2 error on one block must NOT abort the whole
  # 26k run. Tolerate per-command failure, then record/drop ONLY the blocks that
  # git-annex confirms are actually present on the remote (idempotent + resumable).
  git annex add "${added[@]}" >/dev/null 2>&1 || log "WARN annex add issues (continuing)"
  git -c user.name=kotoba-b2-pin -c user.email=b2-pin@etzhayyim.local \
      commit -q -m "pin-snapshot $STAMP batch ($(( done_total+1 ))..)" >/dev/null 2>&1 || true
  git annex copy "${added[@]}" --to "$REMOTE" -J"${KOTOBA_B2_JOBS:-4}" >/dev/null 2>&1 \
      || log "WARN some copies failed this batch (will retry next run)"
  ok_files=()
  while IFS= read -r kf; do [[ -n "$kf" ]] && ok_files+=("$kf"); done \
      < <(git annex find "${added[@]}" --in "$REMOTE" 2>/dev/null)
  if [[ ${#ok_files[@]} -gt 0 ]]; then
    for f in "${ok_files[@]}"; do basename "$f"; done >> meta/backed.txt
    [[ "$DROP_LOCAL" == "1" ]] && git annex drop --force "${ok_files[@]}" >/dev/null 2>&1 || true
    done_total=$(( done_total + ${#ok_files[@]} ))
  fi
  log "progress: $done_total/$NEW confirmed on '$REMOTE' (batch added ${#added[@]}, ok ${#ok_files[@]})"
done

sort -u meta/backed.txt -o meta/backed.txt
git -c user.name=kotoba-b2-pin -c user.email=b2-pin@etzhayyim.local \
    add -A meta >/dev/null 2>&1 || true
git -c user.name=kotoba-b2-pin -c user.email=b2-pin@etzhayyim.local \
    commit -q -m "pin-snapshot $STAMP: +$done_total blocks -> $REMOTE (fail=$fail), heads@$STAMP" >/dev/null || true
log "DONE snapshot $STAMP: copied=$done_total fail=$fail remote=$REMOTE total_backed=$(wc -l < meta/backed.txt|tr -d ' ')"
