#!/usr/bin/env bash
# NHTSA vPIC GetModelsForMake loop ingest → vertex_repo_record
# Iterates top car makers, fetches all models per maker, bulk inserts to RW.
#
# Usage: PG_URL=postgres://root@127.0.0.1:14566/dev?sslmode=disable \
#          bash 70-tools/scripts/nhtsa-models-ingest.sh

set -euo pipefail

: "${PG_URL:?set PG_URL}"

# Top ~80 global car makers likely present in NHTSA.
MAKERS=(
  toyota honda nissan mazda subaru mitsubishi lexus infiniti acura suzuki daihatsu
  ford chevrolet gmc cadillac buick chrysler dodge jeep ram lincoln
  bmw mercedes-benz audi volkswagen porsche tesla mini smart maybach
  hyundai kia genesis
  ferrari lamborghini maserati alfa-romeo fiat abarth
  volvo jaguar land-rover rolls-royce bentley aston-martin mclaren lotus
  peugeot renault citroen dacia bugatti ds ds-automobiles
  skoda seat cupra
  ssangyong daewoo proton perodua tata mahindra
  bajaj geo eagle saturn scion plymouth pontiac oldsmobile mercury hummer
  lada zaz
  byd nio xpeng geely great-wall haval chery baic
  isuzu hino freightliner kenworth peterbilt mack international western-star
)

REPO="did:web:kuruma.etzhayyim.com"
COLL="com.etzhayyim.apps.kuruma.model"
TMP=$(mktemp)
trap "rm -f $TMP" EXIT

NOW_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
NOW_MS=$(date +%s000)

total_models=0
total_makers=0

for m in "${MAKERS[@]}"; do
  url="https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMake/${m}?format=json"
  resp=$(curl -s --max-time 20 "$url" || echo '{"Results":[]}')
  count=$(echo "$resp" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d.get("Results",[])))')
  if [ "$count" -eq 0 ]; then
    continue
  fi
  total_makers=$((total_makers+1))
  echo "$m: $count models"

  # Emit VALUES rows to TMP for batched INSERT.
  echo "$resp" | python3 -c "
import sys, json
d = json.load(sys.stdin)
import datetime
now_iso = '$NOW_ISO'
now_ms = $NOW_MS
for r in d.get('Results', []):
    model_id = r.get('Model_ID','')
    model_name = (r.get('Model_Name','') or '').replace(chr(39), chr(39)+chr(39))
    make_name = (r.get('Make_Name','') or '').replace(chr(39), chr(39)+chr(39))
    if not model_id or not model_name:
        continue
    rkey = f'nhtsa-m{model_id}'
    uri = f'at://$REPO/$COLL/' + rkey
    value = json.dumps({
        '\$type': '$COLL',
        'nhtsaModelId': str(model_id),
        'name': r.get('Model_Name',''),
        'maker': r.get('Make_Name',''),
        'makerId': str(r.get('Make_ID','')),
        'source': 'nhtsa-vpic',
    }, ensure_ascii=False).replace(chr(39), chr(39)+chr(39))
    print(f\"('{uri}', '', '$COLL', '{rkey}', '$REPO', '', '{value}', '{now_iso}', NULL, {now_ms}, '{now_iso}'),\")
" >> "$TMP"
  total_models=$((total_models+count))
done

# Trim trailing comma and bulk INSERT.
if [ -s "$TMP" ]; then
  # Remove trailing comma from last line
  sed -i.bak '$ s/,$//' "$TMP"
  rm -f "$TMP.bak"

  # Split into chunks of 500 rows to avoid single statement being too large.
  SQL_FILE=$(mktemp)
  chunk=0
  row_in_chunk=0
  MAX_ROWS=500
  {
    echo "BEGIN;"
    while IFS= read -r line; do
      if [ "$row_in_chunk" -eq 0 ]; then
        echo "INSERT INTO vertex_repo_record (uri, cid, collection, rkey, repo, repo_rev, value_json, indexed_at, takedown_ref, ts_ms, created_at) VALUES"
        echo "${line%,}" # strip trailing comma just in case
      else
        echo ",${line%,}"
      fi
      row_in_chunk=$((row_in_chunk+1))
      if [ "$row_in_chunk" -ge "$MAX_ROWS" ]; then
        echo ";"
        row_in_chunk=0
      fi
    done < "$TMP"
    if [ "$row_in_chunk" -gt 0 ]; then
      echo ";"
    fi
    echo "COMMIT;"
  } > "$SQL_FILE"

  echo "Executing $total_models INSERT rows across $total_makers makers..."
  psql "$PG_URL" -f "$SQL_FILE" 2>&1 | tail -5
  rm -f "$SQL_FILE"
fi

echo "Done. $total_models models from $total_makers makers."
