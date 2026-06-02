#!/usr/bin/env bash
set -euo pipefail

# Seed JSON-LD articles into PDS via AT Protocol XRPC.
# Usage:
#   ATPROTO_IDENTIFIER=atproto.etzhayyim.com ATPROTO_PASSWORD=... ./scripts/seed-news-articles.sh [PDS_BASE]
#
# Defaults to https://atproto.etzhayyim.com if PDS_BASE is not provided.
# Non-internal writes must target the authenticated repo DID returned by createSession.
# Articles are read from resources/content/ja/**/*.jsonld

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTENT_DIR="$PROJECT_DIR/resources/content/ja"
PDS_BASE="${1:-https://atproto.etzhayyim.com}"
XRPC_BASE="$PDS_BASE/xrpc"
SESSION_URL="$XRPC_BASE/com.atproto.server.createSession"
CREATE_URL="$XRPC_BASE/com.atproto.repo.createRecord"
ATPROTO_IDENTIFIER="${ATPROTO_IDENTIFIER:-}"
ATPROTO_PASSWORD="${ATPROTO_PASSWORD:-}"
ATPROTO_REPO="${ATPROTO_REPO:-}"
COLLECTION="${ATPROTO_COLLECTION:-com.etzhayyim.apps.news.article}"

if [ ! -d "$CONTENT_DIR" ]; then
  echo "ERROR: Content directory not found: $CONTENT_DIR"
  exit 1
fi

if [ -z "$ATPROTO_IDENTIFIER" ] || [ -z "$ATPROTO_PASSWORD" ]; then
  echo "ERROR: ATPROTO_IDENTIFIER and ATPROTO_PASSWORD are required"
  exit 1
fi

echo "Seeding articles from: $CONTENT_DIR"
echo "PDS endpoint: $PDS_BASE"
echo "XRPC createSession: $SESSION_URL"
echo "XRPC createRecord:  $CREATE_URL"

TOTAL=0
SUCCESS=0
FAIL=0
ACCESS_JWT=""
SESSION_DID=""

SESSION_PAYLOAD=$(python3 - <<'PY'
import json
import os
print(json.dumps({
    "identifier": os.environ["ATPROTO_IDENTIFIER"],
    "password": os.environ["ATPROTO_PASSWORD"],
}))
PY
)

HTTP_CODE=$(curl -sS -o /tmp/news-seed-session.json -w '%{http_code}' \
  -X POST "$SESSION_URL" \
  -H 'Content-Type: application/json' \
  -d "$SESSION_PAYLOAD")

if [ "$HTTP_CODE" != "200" ]; then
  echo "ERROR: createSession failed with HTTP $HTTP_CODE"
  sed -n '1,120p' /tmp/news-seed-session.json
  exit 1
fi

SESSION_DID=$(python3 - <<'PY'
import json
with open('/tmp/news-seed-session.json', 'r', encoding='utf-8') as fh:
    data = json.load(fh)
print(data.get('did', ''))
PY
)

ACCESS_JWT=$(python3 - <<'PY'
import json
with open('/tmp/news-seed-session.json', 'r', encoding='utf-8') as fh:
    data = json.load(fh)
print(data.get('accessJwt', ''))
PY
)

if [ -z "$ACCESS_JWT" ]; then
  echo "ERROR: createSession returned no accessJwt"
  exit 1
fi

REPO="${ATPROTO_REPO:-$SESSION_DID}"

if [ -z "$REPO" ]; then
  echo "ERROR: target repo is empty"
  exit 1
fi

echo "Authenticated DID: $SESSION_DID"
echo "Target repo:        $REPO"
echo "Collection:         $COLLECTION"

for jsonld in $(find "$CONTENT_DIR" -name '*.jsonld' -type f | sort); do
  REL_PATH="${jsonld#"$PROJECT_DIR"/}"
  IDENTIFIER=$(python3 - "$jsonld" <<'PY'
import json
import sys
with open(sys.argv[1], 'r', encoding='utf-8') as fh:
    data = json.load(fh)
print(data.get('identifier', ''))
PY
  )

  if [ -z "$IDENTIFIER" ]; then
    echo "SKIP (no identifier): $REL_PATH"
    continue
  fi

  TOTAL=$((TOTAL + 1))

  PAYLOAD=$(python3 - "$jsonld" "$REPO" "$COLLECTION" "$REL_PATH" <<'PY'
import json
import os
import sys

jsonld_path, repo, collection, source_path = sys.argv[1:5]

with open(jsonld_path, 'r', encoding='utf-8') as fh:
    raw = json.load(fh)

article_id = raw.get('identifier') or raw.get('@id') or os.path.basename(jsonld_path)
title = raw.get('headline') or raw.get('name') or article_id
summary = raw.get('description') or ''
content = raw.get('articleBody') or raw.get('text') or ''
category = raw.get('articleSection') or 'general'
language = raw.get('inLanguage') or 'ja'
published_at = raw.get('datePublished') or raw.get('dateCreated') or ''
updated_at = raw.get('dateModified') or published_at
url = raw.get('url') or ''
author = raw.get('author') or {}
author_name = ''
if isinstance(author, dict):
    author_name = author.get('name', '')
elif isinstance(author, list) and author and isinstance(author[0], dict):
    author_name = author[0].get('name', '')
writer_did = raw.get('writer_did') or 'did:web:news.etzhayyim.com:writer:llm'
source = raw.get('source') or author_name or 'resource-seed'
record = {
    '$type': collection,
    'article_id': article_id,
    'title': title,
    'title_slug': article_id,
    'summary': summary,
    'content': content,
    'category': category,
    'language': language,
    'source': source,
    'url': url,
    'status': 'published',
    'published_at': published_at,
    'updated_at': updated_at,
    'quality_score': str(raw.get('quality_score', '0')),
    'needs_quality': str(raw.get('needs_quality', '0')),
    'translation_of': raw.get('translationOf', ''),
    'canonical_lang': raw.get('canonical_lang') or language,
    'writer_did': writer_did,
    'source_type': raw.get('source_type') or 'llm-generated',
    'org_id': 'pds',
    'user_id': repo,
    'actor_id': writer_did,
    'source_path': source_path,
    'raw_json': raw,
}
print(json.dumps({
    'repo': repo,
    'collection': collection,
    'record': record,
}, ensure_ascii=False))
PY
  )

  HTTP_CODE=$(curl -sS -o /tmp/seed-response.json -w '%{http_code}' \
    -X POST "$CREATE_URL" \
    -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $ACCESS_JWT" \
    -d "$PAYLOAD")

  if [ "$HTTP_CODE" = "200" ]; then
    SUCCESS=$((SUCCESS + 1))
    if [ $((TOTAL % 50)) -eq 0 ]; then
      echo "  [$TOTAL] $IDENTIFIER ... OK"
    fi
  else
    FAIL=$((FAIL + 1))
    echo "  FAIL ($HTTP_CODE): $IDENTIFIER — $REL_PATH"
  fi
done

echo ""
echo "=== Seed complete ==="
echo "Total:   $TOTAL"
echo "Success: $SUCCESS"
echo "Failed:  $FAIL"
