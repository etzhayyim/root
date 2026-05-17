#!/usr/bin/env bash
# Global DNS/IP collector — Tranco top-1M → RisingWave direct SQL
# Usage: ./collect-dns-global.sh [OFFSET] [BATCH_SIZE]
#   OFFSET: starting rank (default: 1)
#   BATCH_SIZE: domains per run (default: 100)
#
# Designed for /loop cron: each invocation processes BATCH_SIZE domains
# starting at OFFSET, then prints the next offset for the caller.
#
# Data path: curl (RDAP/DoH) → bash → psql → RisingWave LB :4566
# Tables: vertex_dns_observation, vertex_ip_address, edge_resolves_to

set -uo pipefail

RW="REDACTED_USE_DATABASE_URL_ENV?sslmode=disable"
TRANCO="/tmp/tranco/top-1m.csv"
GEOIP_TOKEN="3009b811ddb7498373031d744a7dc042e036df42e1763602d8b268e1d105536d"
GEOIP_URL="http://localhost:8083/json"
OWNER="did:web:c0ll3ct1.etzhayyim.com"
REPO="c0ll3ct1"

OFFSET=${1:-1}
BATCH=${2:-100}
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TODAY=$(date -u +%Y-%m-%d)

if [ ! -f "$TRANCO" ]; then
  echo "ERROR: Tranco list not found at $TRANCO. Run: curl -sL https://tranco-list.eu/top-1m.csv.zip | funzip > $TRANCO"
  exit 1
fi

rdap_for() {
  local d="$1"
  case "${d##*.}" in
    com|net) echo "https://rdap.verisign.com/${d##*.}/v1/domain/$d" ;;
    org)     echo "https://rdap.org/domain/$d" ;;
    io)      echo "https://rdap.nic.io/domain/$d" ;;
    app|dev) echo "https://rdap.google.com/rdap/domain/$d" ;;
    *)       echo "https://rdap.org/domain/$d" ;;
  esac
}

DNS_OK=0; IP_OK=0; EDGE_OK=0; SKIP=0
END=$((OFFSET + BATCH - 1))

while IFS=',' read -r RANK DOMAIN; do
  DOMAIN="${DOMAIN%$'\r'}"  # Strip Windows \r line ending
  [ -z "$DOMAIN" ] && continue

  # Check if already collected
  EXISTS=$(psql "$RW" -t -A -c "SELECT count(*) FROM vertex_dns_observation WHERE domain = '$DOMAIN';" 2>/dev/null || echo "0")
  if [ "$EXISTS" != "0" ]; then
    ((SKIP++))
    continue
  fi

  # RDAP
  RDAP_URL=$(rdap_for "$DOMAIN")
  RDAP=$(curl -sS -m 6 "$RDAP_URL" 2>/dev/null || echo '{}')
  REGISTRAR=$(echo "$RDAP" | jq -r '.entities[]? | select(.roles[]? == "registrar") | .vcardArray[1][]? | select(.[0] == "fn") | .[3] // ""' 2>/dev/null | head -1)
  REG_HANDLE=$(echo "$RDAP" | jq -r '.entities[]? | select(.roles[]? == "registrar") | .handle // ""' 2>/dev/null | head -1)
  STATUS=$(echo "$RDAP" | jq -r '[.status[]?] | join(",")' 2>/dev/null)
  REG_DATE=$(echo "$RDAP" | jq -r '.events[]? | select(.eventAction == "registration") | .eventDate // ""' 2>/dev/null | head -1)
  EXP_DATE=$(echo "$RDAP" | jq -r '.events[]? | select(.eventAction == "expiration") | .eventDate // ""' 2>/dev/null | head -1)
  LAST_CHANGE=$(echo "$RDAP" | jq -r '.events[]? | select(.eventAction == "last changed") | .eventDate // ""' 2>/dev/null | head -1)
  DNSSEC=$(echo "$RDAP" | jq -r 'if .secureDNS.delegationSigned == true then "signed" else "unsigned" end' 2>/dev/null)

  # DoH
  NS=$(curl -sS -m 4 "https://cloudflare-dns.com/dns-query?name=${DOMAIN}&type=NS" -H "Accept: application/dns-json" | jq -r '[.Answer[]? | .data] | join(",")' 2>/dev/null)
  A_REC=$(curl -sS -m 4 "https://cloudflare-dns.com/dns-query?name=${DOMAIN}&type=A" -H "Accept: application/dns-json" | jq -r '[.Answer[]? | .data] | join(",")' 2>/dev/null)
  MX_REC=$(curl -sS -m 4 "https://cloudflare-dns.com/dns-query?name=${DOMAIN}&type=MX" -H "Accept: application/dns-json" | jq -r '[.Answer[]? | .data] | join(",")' 2>/dev/null)

  VID="dns:${DOMAIN}"
  RKEY=$(echo -n "$DOMAIN" | shasum -a 256 | cut -c1-12)
  DID="did:web:c0ll3ct1.etzhayyim.com:dns:${DOMAIN}"
  REGISTRAR_ESC="${REGISTRAR//\'/\'\'}"
  PROPS="{\"a\":\"${A_REC}\",\"mx\":\"${MX_REC}\",\"rank\":${RANK}}"

  R=$(psql "$RW" -c "INSERT INTO vertex_dns_observation (vertex_id, created_date, sensitivity_ord, owner_did, rkey, repo, label, did, domain, registrar, registrar_handle, nameservers, registration_date, expiration_date, last_changed_date, dnssec, status, observed_at, props) VALUES ('$VID', '$TODAY', 0, '$OWNER', '$RKEY', '$REPO', 'DnsObservation', '$DID', '$DOMAIN', '$REGISTRAR_ESC', '$REG_HANDLE', '$NS', '$REG_DATE', '$EXP_DATE', '$LAST_CHANGE', '$DNSSEC', '$STATUS', '$NOW', '$PROPS');" 2>&1)
  if echo "$R" | grep -q "INSERT 0 1"; then
    ((DNS_OK++))
  else
    continue
  fi

  # GeoIP + edge for each A record IP
  IFS=',' read -ra IPS <<< "$A_REC"
  for IP in "${IPS[@]}"; do
    [ -z "$IP" ] && continue
    IP_VID="ip:${IP}"

    # IP insert (skip if exists)
    IP_EXISTS=$(psql "$RW" -t -A -c "SELECT count(*) FROM vertex_ip_address WHERE address = '$IP';" 2>/dev/null || echo "0")
    if [ "$IP_EXISTS" = "0" ]; then
      GEO=$(curl -sS -m 4 "$GEOIP_URL/${IP}" -H "X-Auth-Token: $GEOIP_TOKEN" 2>/dev/null || echo '{}')
      CC=$(echo "$GEO" | jq -r '.countryCode // ""')
      CITY=$(echo "$GEO" | jq -r '.city // ""')
      REGION=$(echo "$GEO" | jq -r '.region // ""')
      LAT=$(echo "$GEO" | jq -r '.lat // 0')
      LON=$(echo "$GEO" | jq -r '.lon // 0')
      ASN=$(echo "$GEO" | jq -r '.asn // ""')
      ASN_ORG=$(echo "$GEO" | jq -r '.asnOrg // ""')
      ISP=$(echo "$GEO" | jq -r '.isp // ""')
      IS_PROXY=$(echo "$GEO" | jq -r '.isProxy // false')
      IS_DC=$(echo "$GEO" | jq -r '.isDatacenter // false')
      IS_TOR=$(echo "$GEO" | jq -r '.isTorExitNode // false')
      IP_DID="did:web:c0ll3ct1.etzhayyim.com:ip:${IP}"
      IP_RKEY=$(echo -n "$IP" | shasum -a 256 | cut -c1-12)
      ASN_ORG_ESC="${ASN_ORG//\'/\'\'}"
      CITY_ESC="${CITY//\'/\'\'}"
      REGION_ESC="${REGION//\'/\'\'}"
      ISP_ESC="${ISP//\'/\'\'}"

      IR=$(psql "$RW" -c "INSERT INTO vertex_ip_address (vertex_id, created_date, sensitivity_ord, owner_did, rkey, repo, label, did, address, country_code, city, region, lat, lon, asn, asn_org, isp, is_proxy, is_datacenter, is_tor, observed_at) VALUES ('$IP_VID', '$TODAY', 0, '$OWNER', '$IP_RKEY', '$REPO', 'IPAddress', '$IP_DID', '$IP', '$CC', '$CITY_ESC', '$REGION_ESC', $LAT, $LON, '$ASN', '$ASN_ORG_ESC', '$ISP_ESC', $IS_PROXY, $IS_DC, $IS_TOR, '$NOW');" 2>&1)
      echo "$IR" | grep -q "INSERT 0 1" && ((IP_OK++))
    fi

    # Edge insert
    EDGE_ID="resolves:${DOMAIN}:${IP}"
    E_EXISTS=$(psql "$RW" -t -A -c "SELECT count(*) FROM edge_resolves_to WHERE edge_id = '$EDGE_ID';" 2>/dev/null || echo "0")
    if [ "$E_EXISTS" = "0" ]; then
      ER=$(psql "$RW" -c "INSERT INTO edge_resolves_to (edge_id, src_vid, dst_vid, created_date, sensitivity_ord, owner_did, record_type, observed_at) VALUES ('$EDGE_ID', '$VID', '$IP_VID', '$TODAY', 0, '$OWNER', 'A', '$NOW');" 2>&1)
      echo "$ER" | grep -q "INSERT 0 1" && ((EDGE_OK++))
    fi
  done

  # Progress every 10 domains
  if (( DNS_OK % 10 == 0 && DNS_OK > 0 )); then
    echo "[progress] rank=$RANK dns=+$DNS_OK ip=+$IP_OK edge=+$EDGE_OK skip=$SKIP"
  fi
done < <(sed -n "${OFFSET},${END}p" "$TRANCO")

echo ""
echo "=== Batch complete: offset=$OFFSET batch=$BATCH dns=+$DNS_OK ip=+$IP_OK edge=+$EDGE_OK skip=$SKIP ==="
echo "NEXT_OFFSET=$((END + 1))"

# Print totals
psql "$RW" -c "SELECT count(*) as total_dns FROM vertex_dns_observation; SELECT count(*) as total_ips FROM vertex_ip_address; SELECT count(*) as total_edges FROM edge_resolves_to;"
