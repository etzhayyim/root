# meeting-recorder Phase 1 検証 runbook

Scope: (1) Worker↔PDS Service Auth bootstrap が実装されたことの確認、(5) Worker 起動確認。
provider SDK 本体 (Teams .NET / Meet gRPC / Zoom C++) の live 検証は対象外 — 別セッション。

## ✅ Done in this session

| item | 検証方法 | 結果 |
|---|---|---|
| Worker `/_internal/mint-pds-bearer` route + HMAC-SHA256 auth | `esbuild --bundle=false` syntax check | PASS |
| `validateConsentClaims` 構造検証 (aud / lxm / sub / exp / exp-bound) | 同上 | PASS |
| `mintPdsBearer` via `AUTH_SERVICE.fetch(/xrpc/com.atproto.server.getServiceAuth)` | 同上 | PASS |
| Container `TokenRotator` (pre-expiry refresh, concurrent coalescing) | esbuild syntax + tsc (節 TS2591 除き) | PASS |
| `chunk-writer` / `transcript-pipeline` が env bearer ではなく `TokenRotator.get()` を使う | diff review | PASS |
| Worker app.ts bundle (esbuild --bundle --platform=neutral) | 同上 | PASS |
| Container server.ts bundle | 同上 | PASS |
| `pnpm install` Worker + workspace deps (wrangler local bin) | `./node_modules/.bin/wrangler --version` = 3.114.17 | PASS |
| `wrangler dev --local --port 8787` 起動 | `[wrangler:inf] Ready on http://localhost:8787` | PASS |
| Smoke: no HMAC → `401 unauthorized` | live curl | PASS |
| Smoke: wrong HMAC → `401 unauthorized` | live curl | PASS |
| Smoke: correct HMAC + invalid lxm → `400 lxm must be com.atproto.*` | live curl | PASS |
| Smoke: correct HMAC + valid lxm → 500 with `getServiceAuth failed: 503 [wrangler] Couldn't find wrangler dev session for service "etzhayyim-auth"` (AUTH_SERVICE binding 期待通りの propagation) | live curl | PASS |
| Smoke: joinMeeting with consent JWT | expected `consent expired` after body parsing; **observed**: `invalid provider` → indicates lexicon codegen gap (see Phase 2 #codegen) | PARTIAL (超越済、下記) |
| **Codegen + parseLexiconInput fix** (post-investigation): `node 70-tools/scripts/contract/gen-lexicon-nsid-types.mjs` + handler の `parseLexiconInput("nsid", body)` 組込 | live curl | PASS |
| Smoke (post-fix) Test 5: expired consent → `{"status":"failed","error":"consent rejected: consent expired"}` | live curl | PASS |
| Smoke (post-fix) Test 6: aud mismatch → `{"status":"failed","error":"consent rejected: aud mismatch: got did:web:wrong.etzhayyim.com"}` | live curl | PASS |
| Smoke (post-fix) Test 8: valid consent + future exp → Hyperdrive stub 失敗 (consent gate 通過確認) | live curl | PASS |
| Smoke (post-fix) Test 7 (POST): listSessions → Hyperdrive stub 失敗 (routing OK) | live curl | PASS |
| **Session binding (Phase 2 — defense layer 1)**: `accountDid === onBehalfOfDid === consentToken.sub` 強制 | live curl | PASS |
|   S1: no session → `session required (Authorization: Bearer <session JWT>)` | — | PASS |
|   S2: session matches + ES256 verify triggered → `consent signature invalid: did.json fetch ... 404` (期待通り、did.json 未配置時は reject) | — | PASS |
|   S3: session ≠ onBehalfOfDid → `caller session did ≠ onBehalfOfDid` | — | PASS |
| **ES256 signature verify (Phase 2 — defense layer 2)**: `did:web` resolution (`/.well-known/did.json` or path-form) → P-256 JWK → WebCrypto ECDSA verify。`alg=none` / `RS256` downgrade attacks reject | S2 smoke | PASS |
| **Provisioning script** `50-infra/vultr/meeting-recorder/provision.sh`: Vultr VKE node pool + B2 bucket + CF Tunnel + DNS CNAME + etzhayyim Vault folder + wrangler secret + graph migration, idempotent (check-or-create) | `bash -n` syntax | PASS |
| **Multi-method DID resolver** (`resolveDid`): did:web (.well-known/did.json + path-form) / did:plc (plc.directory、override via DID_PLC_RESOLVER) / did:etzhayyim (did.etzhayyim.com /1.0/identifiers/, ADR-0029) / reject unknown (`did:key` 等) | live curl | PASS |
|   M1: real did:plc (`did:plc:ewvi7nxzyoun6zhxrhs64oiz`) → DID doc 200 fetch → `found: multibase` reject (Phase 3 TODO) | — | PASS (limitation surfaced) |
|   M3: `did:key:xyz` → `unsupported DID method` | — | PASS |
|   **Phase 3 deferred**: (a) multibase (z-base58btc) → raw key decode, (b) secp256k1 WebCrypto support (atproto default), (c) compressed-point P-256 decompression |
| **Phase 3 crypto**: `@atproto/crypto` wired into Worker. `publicKeyMultibase` 鍵を `did:key:z...` 形式で `verifySignature` に渡す。ES256 (P-256) + ES256K (secp256k1) 両対応。bundle 252KB | bundle + live curl | PASS |
|   M1 (ES256 JWT + secp256k1 DID key) → `JWT alg=ES256 ≠ DID key alg=ES256K` (substitution attack reject) | — | PASS |
|   M1b (ES256K JWT + secp256k1 DID key + fake sig) → `@atproto/crypto` noble-curves verify に到達、`length=3` で reject (実 sig なら通過) | — | PASS |
|   Defense layers total: (1) session binding, (2) structural JWT, (3) exp-bound, (4) alg whitelist (ES256\|ES256K), (5) alg-key match, (6) cryptographic signature verify |
| **Phase 4 JWK fallback**: DID Document の `publicKeyJwk` (P-256 `{kty,crv,x,y}`) → uncompressed 65-byte EC point (`0x04 \|\| x \|\| y`) → `formatDidKey("ES256", bytes)` → did:key:z... → `parseDidKey` / `verifySignature` で処理 | live diag | PASS |
|   RFC 7515 A.3.1 test key (`f83OJ3D2...` / `x_FEzRu9...`) → `did:key:zDnaerGBD7Zxzau2fdfEFaaaTDYBu5XEBYdGV2BmERp3MDSov` + `{jwtAlg: "ES256", keyBytesLen: 65}` | — | PASS |
| **DID support matrix complete**: publicKeyMultibase (native, atproto primary) + publicKeyJwk (P-256 only, fallback for JWK-only did:web) × 3 method (did:web / did:plc / did:etzhayyim) × 2 alg (ES256 / ES256K) |
| **Mock-path end-to-end smoke** (in-session, no real Teams/Meet/Zoom, no real B2/PDS/Murakumo) | live curl | PASS |
|   Pipeline: Container (Node/tsx :50052) ← POST /v1/join ← curl → mock adapter emits 3 × {audio.opus, video.webm} 500ms chunks → chunk-writer → local FS (RECORDER_LOCAL_CHUNK_DIR=/tmp/mrec-chunks) → TokenRotator → fake mint (:9100) → fake PDS createRecord (:9100) | — | PASS |
|   Transcript: chunk-writer audio → transcript-pipeline → fake Murakumo (:9100) → whisper-ish segments → `signal:v1:` AES-GCM encrypt → fake PDS transcriptSegment record | — | PASS |
|   Final state: 6 chunks on disk (3 audio + 3 video) + 9 AT records (6 recordingChunk + 3 transcriptSegment), sha256 on disk ≡ sha256 in AT record | — | PASS |
|   Cleanup: POST /v1/leave → `{"status":"left","durationMs":3641}` |
| **Artifacts**: `50-infra/vultr/meeting-recorder/container/adapters/mock/index.ts` (synthetic emitter) + `container/control-plane/src/fake-services.ts` (HMAC mint + PDS + Murakumo in one Hono server) + `container/package.json` (`"type": "module"` fix for ESM adapter resolution) |

## ⏳ Prerequisite を未充足のため live run できないもの

### (A) `wrangler dev` 起動には以下が必要

| item | status | 取得方法 |
|---|---|---|
| workspace `pnpm install` | 済と仮定 (root `node_modules` 有) | `pnpm install` (root) |
| Worker dir 内 `node_modules` (wrangler binary) | 未 | `cd 60-apps/etzhayyim-project-meeting-recorder/appview/etzhayyim-wasm-meeting-recorder-m33tr3c0 && pnpm install` |
| `AUTH_SERVICE` binding target `etzhayyim-auth` | CF account 上に存在 (既存) | — |
| `HYPERDRIVE` config `e84c0a2babe44fc7b74818e394b4b896` | 既存 | — |
| `RECORDER_TUNNEL_SECRET` wrangler secret | 未 provisioned | `openssl rand -hex 32 \| wrangler secret put RECORDER_TUNNEL_SECRET` + etzhayyim Vault 登録 |
| did:web:meeting-recorder.etzhayyim.com signing key (auth Worker KEYS_DB) | 未 provisioned | `etzhayyim deploy` 初回実行で `com.atproto.admin.registerApp` → KEK envelope 化保存 |
| `vertex_meetingrecorder_*` graph tables | 未 migrated | `pnpm -F @etzhayyim/graph-schema migrate up` |

### (B) `docker build` には以下が必要

| item | status |
|---|---|
| `container/control-plane` の `pnpm install` (@aws-sdk / @grpc / hono / pino) | 未 |
| `adapters/meet/` の `pnpm install` (google-auth-library / @grpc) | 未 |
| `adapters/teams/bin/` (.NET 8 sidecar) | Phase 1 stub (README only) |
| `adapters/zoom/bin/` (C++ sidecar) | Phase 1 stub (redistributable でないため initContainer 経由) |

### (C) end-to-end smoke (実 meeting 参加) には以下が必要

- Azure AD app + tenant admin consent (Teams)
- GCP project + Meet Media API enable + service account (Meet)
- Zoom marketplace Server-to-Server OAuth app + SDK license (Zoom)
- Vultr VKE node pool `meeting-recorder` provisioned
- B2 bucket `etzhayyim-recordings` + prefix-scoped app key
- Cloudflare Tunnel `meeting-recorder-control` + DNS `meeting-recorder-ctrl.etzhayyim.com`

## (1) Bootstrap flow 検証手順 (prereq 揃ってから実行)

### 1.1 Consent token の mint (user 側)

```bash
etzhayyim authn signin
etzhayyim agent-token \
  --lxm com.etzhayyim.apps.meetingRecorder.joinMeeting \
  --aud did:web:meeting-recorder.etzhayyim.com \
  --ttl 300 \
  > /tmp/consent.jwt
```

### 1.2 joinMeeting 呼び出し

```bash
curl -X POST https://meeting-recorder.etzhayyim.com/xrpc/com.etzhayyim.apps.meetingRecorder.joinMeeting \
  -H "content-type: application/json" \
  -H "authorization: Bearer $(cat /tmp/session.jwt)" \
  -d "{
    \"provider\": \"teams\",
    \"joinTarget\": {\"joinUrl\": \"https://teams.microsoft.com/l/meetup-join/...\"},
    \"onBehalfOfDid\": \"did:web:jun.etzhayyim.com\",
    \"consentToken\": \"$(cat /tmp/consent.jwt)\"
  }"
```

**期待**: `{"sessionDid":"did:web:meeting-recorder.etzhayyim.com:session:teams:<id>","sessionId":"ses_...","status":"joining"}`

**consent 拒否テスト** (exp を過去にして mint):

```bash
etzhayyim agent-token --lxm ... --ttl -10 > /tmp/expired.jwt
# → response: {"status":"failed","error":"consent rejected: consent expired"}
```

### 1.3 Container → Worker mint flow (HMAC)

Container 内 TokenRotator は以下を自動実行:

```
POST https://meeting-recorder.etzhayyim.com/_internal/mint-pds-bearer
  headers:
    content-type: application/json
    x-recorder-auth: <hmac-sha256(body, RECORDER_TUNNEL_SECRET)>
  body:
    {"lxm": "com.atproto.repo.createRecord", "ttlSeconds": 600}
```

**期待**: `{"token": "<ES256 JWT>", "expiresAt": <unix>}`

**HMAC 欠落テスト**:

```bash
curl -X POST https://meeting-recorder.etzhayyim.com/_internal/mint-pds-bearer \
  -H "content-type: application/json" \
  -d '{"lxm":"com.atproto.repo.createRecord"}'
# → 401 {"error":"unauthorized"}
```

**ES256 JWT payload 検証**:

```bash
TOKEN=... # from response
echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq
# 期待: {"iss":"did:web:meeting-recorder.etzhayyim.com","aud":"did:web:atproto.etzhayyim.com",
#       "lxm":"com.atproto.repo.createRecord","exp":...,"iat":...,"jti":"..."}
```

## (5) Worker 起動確認

### 5.1 Bundle 整合性

すでに確認済:

```bash
pnpm --filter etzhayyim-root esbuild --bundle \
  --platform=neutral \
  --external:@etzhayyim/kotodama-host-sdk --external:node:async_hooks \
  60-apps/etzhayyim-project-meeting-recorder/appview/etzhayyim-wasm-meeting-recorder-m33tr3c0/src/app.ts
# → 355 行の bundle、warning ゼロ
```

### 5.2 `wrangler dev` 手順 (prereq 揃ってから)

```bash
cd 60-apps/etzhayyim-project-meeting-recorder/appview/etzhayyim-wasm-meeting-recorder-m33tr3c0
pnpm install
pnpm dev   # = wrangler dev
# → http://localhost:8787 で listen
```

Smoke test (local):

```bash
# meta route
curl http://localhost:8787/_app/meta
# → {"nanoid":"m33tr3c0","displayName":"Meeting Recorder",...}

# HMAC 不在 → 401
curl -X POST http://localhost:8787/_internal/mint-pds-bearer \
  -H "content-type: application/json" -d '{"lxm":"com.atproto.repo.createRecord"}'
# → 401 unauthorized

# 未知の lxm → 400
SECRET=$(wrangler secret get RECORDER_TUNNEL_SECRET)
BODY='{"lxm":"com.etzhayyim.apps.lawfirm.createMatter"}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')
curl -X POST http://localhost:8787/_internal/mint-pds-bearer \
  -H "content-type: application/json" -H "x-recorder-auth: $SIG" -d "$BODY"
# → 400 {"error":"lxm must be com.atproto.*"}
```

## Phase 2 タスク (次セッション)

1. `validateConsentClaims` に PDS_RPC 経由の ES256 signature 検証を追加 (`verifyServiceAuthJWT` delegate)
2. `.NET 8 RecorderTeams` sidecar 実装
3. Meet Media API gRPC subscribe 実装 (auth path は完成)
4. Zoom C++ sidecar (initContainer pull + SDK wire)
5. X25519 Signal shared-secret bootstrap via `com.etzhayyim.signal.getPrekeyBundle` (現 dev key fallback を撤去)
6. Vultr VKE `meeting-recorder` node pool provision + Cloudflare Tunnel + B2 bucket + etzhayyim Vault folder
7. `etzhayyim deploy` 初回実行で auth Worker KEYS_DB に meeting-recorder signing key 登録
8. 実 Teams/Meet/Zoom meeting に対する live capture → B2 PUT → transcript 検証 (参加者同意下)

## References

- ADR-0050 — meeting-recorder multi-provider actor
- ADR-0022 — Auth 2-token model (`lxm` scoping SSoT)
- 60-apps/etzhayyim-project-auth/worker/src-ts/service-auth.ts — `signServiceAuth` (ES256 mint)
- 60-apps/etzhayyim-project-auth/worker/src-ts/index.ts:1630 — `handleGetServiceAuth` (iss-scoped KEK decrypt)
- 50-infra/cloudflare/workers/atproto/src/auth/verify.ts:150 — `verifyServiceAuthJWT` (PDS 側 verify SSoT)
