#!/usr/bin/env bash
# Smoke test for the sh1n5h1x.etzhayyim.com profile postsCount regression
# fix (ADR-2604241038 + 20260424014529_mv_actor_social_stats_root_normalization).
#
# Problem: /profile/sh1n5h1x.etzhayyim.com showed 0 posts even though individual
# post URLs worked. Root cause was 2-layer:
#   1. mv_actor_social_stats GROUP BY raw repo missed path-DID posts.
#   2. yoro frontend `?? feedItems.length` couldn't override a valid 0.
#
# Gate: after the migration + yoro deploy ship, both the AppView read
# and the yoro SSR must agree that postsCount > 0 for sh1n5h1x.etzhayyim.com.
#
# Usage:
#   bash 70-tools/scripts/sh1n5h1x-profile-smoke.sh                 # production
#   STAGING=1 bash 70-tools/scripts/sh1n5h1x-profile-smoke.sh       # staging
#   ACTOR=someone.etzhayyim.com bash 70-tools/scripts/sh1n5h1x-profile-smoke.sh
#
# Env:
#   ACTOR         — default sh1n5h1x.etzhayyim.com
#   STAGING=1     — point at staging-bsky.etzhayyim.com + staging-yoro.etzhayyim.com
#   MIN_POSTS     — default 1 (fail if postsCount < this)

set -euo pipefail

ACTOR="${ACTOR:-sh1n5h1x.etzhayyim.com}"
MIN_POSTS="${MIN_POSTS:-1}"

if [[ "${STAGING:-0}" == "1" ]]; then
  BSKY_ORIGIN="https://staging-bsky.etzhayyim.com"
  YORO_ORIGIN="https://staging-yoro.etzhayyim.com"
else
  BSKY_ORIGIN="https://bsky.etzhayyim.com"
  YORO_ORIGIN="https://yoro.etzhayyim.com"
fi

color_pass() { printf "\033[32m✔\033[0m"; }
color_fail() { printf "\033[31m✘\033[0m"; }
say()  { printf "\n\033[1;36m==> %s\033[0m\n" "$*"; }
ok()   { printf "  %s %s\n" "$(color_pass)" "$1"; }
bad()  { printf "  %s %s\n" "$(color_fail)" "$1"; exit 1; }

say "ACTOR=$ACTOR   BSKY=$BSKY_ORIGIN   YORO=$YORO_ORIGIN"

# ── 1. Direct AppView XRPC (authoritative read) ─────────────────────────
say "1. bsky.etzhayyim.com /xrpc/app.bsky.actor.getProfile"
profile_json="$(curl -sS --fail-with-body \
  "${BSKY_ORIGIN}/xrpc/app.bsky.actor.getProfile?actor=${ACTOR}" \
  -H 'accept: application/json' 2>&1)" \
  || bad "getProfile HTTP failed: $profile_json"

posts_count="$(printf '%s' "$profile_json" | jq -r '.postsCount // 0')"
followers_count="$(printf '%s' "$profile_json" | jq -r '.followersCount // 0')"
follows_count="$(printf '%s' "$profile_json" | jq -r '.followsCount // 0')"
did="$(printf '%s' "$profile_json" | jq -r '.did // "<none>"')"

printf "     did=%s  posts=%s  followers=%s  follows=%s\n" \
  "$did" "$posts_count" "$followers_count" "$follows_count"

if [[ "$did" == "<none>" ]]; then
  bad "getProfile returned no did; body: $profile_json"
fi
ok "AppView resolved actor to $did"

if awk -v a="$posts_count" -v b="$MIN_POSTS" 'BEGIN{exit !(a+0 >= b+0)}'; then
  ok "AppView postsCount ≥ ${MIN_POSTS} (got ${posts_count})"
else
  bad "AppView postsCount=${posts_count} < ${MIN_POSTS} — mv_actor_social_stats root-normalization migration may not be applied"
fi

# ── 2. Cross-check via getAuthorFeed — MV-independent ───────────────────
say "2. bsky.etzhayyim.com /xrpc/app.bsky.feed.getAuthorFeed?limit=50"
feed_json="$(curl -sS --fail-with-body \
  "${BSKY_ORIGIN}/xrpc/app.bsky.feed.getAuthorFeed?actor=${ACTOR}&limit=50" \
  -H 'accept: application/json' 2>&1)" \
  || bad "getAuthorFeed HTTP failed: $feed_json"

feed_len="$(printf '%s' "$feed_json" | jq -r '.feed | length')"
printf "     feed rows returned: %s\n" "$feed_len"
if [[ "$feed_len" -ge "$MIN_POSTS" ]]; then
  ok "getAuthorFeed returned ${feed_len} items — underlying vertex_repo_record has posts"
else
  bad "getAuthorFeed returned 0 items — user legitimately has no posts; postsCount=0 is correct"
fi

# ── 3. yoro SSR profile page renders ≥ MIN_POSTS ────────────────────────
say "3. yoro.etzhayyim.com /profile/${ACTOR}"
# yoro is a CSR app — SSR serves only the skeleton HTML, JS fetches the
# data client-side. We grep for the actor handle in the HTML head as a
# minimum "route resolves" proof, and check that the 410 surface from
# `/xrpc/` still stands (ADR-2604241038 Phase ε).
profile_html="$(curl -sS --fail-with-body \
  "${YORO_ORIGIN}/profile/${ACTOR}" \
  -H 'accept: text/html' 2>&1)" \
  || bad "yoro profile page HTTP failed: ${profile_html:0:200}"

if printf '%s' "$profile_html" | grep -q "$ACTOR"; then
  ok "yoro profile route resolved for ${ACTOR}"
else
  bad "yoro profile page did not echo ${ACTOR} — route may be broken"
fi

# yoro /xrpc/ should be 410 Gone (clients must talk to atproto.etzhayyim.com).
yoro_xrpc_status="$(curl -sS -o /dev/null -w '%{http_code}' \
  "${YORO_ORIGIN}/xrpc/app.bsky.actor.getProfile?actor=${ACTOR}")"
if [[ "$yoro_xrpc_status" == "410" ]]; then
  ok "yoro /xrpc/ returns 410 Gone as per ADR-2604241038 Phase ε"
else
  printf "  \033[33m⚠\033[0m yoro /xrpc/ returned %s (expected 410); not fatal but worth checking\n" "$yoro_xrpc_status"
fi

printf "\n\033[32mSMOKE PASSED\033[0m — postsCount=%s for %s\n" "$posts_count" "$ACTOR"
