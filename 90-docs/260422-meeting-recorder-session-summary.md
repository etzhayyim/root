# meeting-recorder — 2026-04-22 セッション統合サマリ

etzhayyim Japan の AI agent が user 代理で Microsoft Teams / Google Meet / Zoom meeting に参加し、音声・動画・transcript を記録する recorder actor の **設計 → 実装 → 検証** を 1 session で完了。次 session 引き継ぎ用。

## Final Status

| 領域 | 状態 |
|---|---|
| Actor 登録 (did:web:meeting-recorder.etzhayyim.com, nanoid m33tr3c0) | ✅ `deps.toml` |
| Lexicon (7 本) | ✅ `00-contracts/lexicons/com/etzhayyim/apps/meetingRecorder/*.json` |
| Graph migration (5 tables) | ✅ `30-graph/graph-schema/migrations/20260422090000_vertex_meeting_recorder_tables.ts` |
| Control-plane CF Worker | ✅ `60-apps/etzhayyim-project-meeting-recorder/appview/etzhayyim-wasm-meeting-recorder-m33tr3c0/` |
| Media-plane Vultr VKE container (skeleton) | ✅ `50-infra/vultr/meeting-recorder/container/` |
| Provisioning script | ✅ `50-infra/vultr/meeting-recorder/provision.sh` |
| Deploy runbook | ✅ `90-docs/260422-meeting-recorder-deploy-runbook.md` |
| Phase 1 verification runbook | ✅ `90-docs/260422-meeting-recorder-phase1-verification.md` |
| ADR | ✅ `90-docs/adr/0050-meeting-recorder-multi-provider.md` (status: proposed) |
| Mock-path E2E smoke | ✅ pass (6 chunks + 9 AT records + sha256 integrity) |

## 合意済 Design Decisions

### Actor topology (ADR-0050)

- **単一 actor + provider adapter 構成**: 3 provider で共通の lexicon / graph table / MCP facade。`provider: "teams" | "meet" | "zoom"` enum で adapter dispatch。ADR-0005 redundancy prohibition 遵守
- **Control-plane** = CF Worker (XRPC + MCP facade + consent gate)
- **Media-plane** = Vultr VKE LAX node pool `meeting-recorder` (vhf-4c-16gb × 2, $192/mo)
- **Storage** = Backblaze B2 `etzhayyim-recordings/meeting-recorder/{sessionDid}/{seq}.{opus|webm}` (ADR-0048 Bandwidth Ally egress-free)
- **Transcription** = Murakumo MLX `whisper-large-v3` (sovereignty 完全、provider 内蔵 caption 非使用)
- **Graph** = Worker-direct Hyperdrive → Kotoba/Datomic (ADR-0036)

### Consent gate — 6 defense layers

| layer | mechanism |
|---|---|
| 1 | Session binding: `accountDidFromBearer(Authorization) === onBehalfOfDid === consentToken.sub === consentToken.iss` |
| 2 | Structural JWT claim validation (aud / lxm / sub / iss / exp) |
| 3 | Exp bounded (`exp - now ≤ CONSENT_MAX_EXPIRY_SECONDS`, default 600s) |
| 4 | Alg whitelist (ES256 or ES256K only; `none` / RS* reject) |
| 5 | Alg-key match (`parseDidKey(didKey).jwtAlg === header.alg`) — substitution attack defense |
| 6 | Cryptographic signature verify via `@atproto/crypto.verifySignature` (WebCrypto P-256 + `@noble/curves` secp256k1) |

### DID coverage

| method | multibase (atproto native) | publicKeyJwk P-256 | resolver |
|---|---|---|---|
| did:web | ✅ | ✅ (Phase 4) | `/.well-known/did.json` or `/<path>/did.json` |
| did:plc | ✅ | — | `https://plc.directory/{did}` (override: `DID_PLC_RESOLVER`) |
| did:etzhayyim (ADR-0029) | ✅ | ✅ | `https://did.etzhayyim.com/1.0/identifiers/{did}` (override: `DID_etzhayyim_RESOLVER`) |

### Worker ↔ Container auth (ADR-0022 準拠)

- Container は ES256 signing key を持たない
- Container ⇒ Worker `/_internal/mint-pds-bearer` (HMAC-SHA256 `x-recorder-auth`, constant-time compare)
- Worker ⇒ AUTH_SERVICE binding `/xrpc/com.atproto.server.getServiceAuth` → ES256 JWT (aud=PDS_DID, iss=RECORDER_DID, lxm=com.atproto.repo.createRecord)
- 60s TTL、Container `TokenRotator` が concurrent-coalescing + pre-expiry refresh

### PII Tier 3 (ADR-0018)

- AT Repo: session did / chunk sha256 / b2Key / timings のみ (PII-free)
- Graph: `participant.provider_id_hash` (sha256)、`display_name_cipher` / `text_cipher` は `signal:v1:` field-encrypt
- Transcript recipient = onBehalfOfDid + 明示 grant された DID のみ

## Implementation (commits already landed)

```
057917ca6bb feat(meeting-recorder): add contracts, infra, appview, and runbook
fa5c4a7b1ae feat(meeting-recorder): add app and container source files
802506d604c feat(meeting-recorder): add phase1 verification and token rotation updates
1506decbef8 feat: update meeting recorder and add game play uploader app
63fbe8e9057 chore: update gameplay uploader page and verification notes
a2d58dd364b feat: add contracts actor wiring and meeting recorder updates
```

## Verified (live smoke, wrangler dev + tsx container)

### Consent gate (`POST /xrpc/com.etzhayyim.apps.meetingRecorder.joinMeeting`)

| test | result |
|---|---|
| No session | `session required (Authorization: Bearer <session JWT>)` |
| session ≠ onBehalfOfDid | `caller session did ≠ onBehalfOfDid` |
| Expired consent | `consent rejected: consent expired` |
| aud mismatch | `consent rejected: aud mismatch: got did:web:wrong.etzhayyim.com` |
| ES256 JWT + secp256k1 DID key | `JWT alg=ES256 ≠ DID key alg=ES256K` (substitution reject) |
| ES256K JWT + secp256k1 DID + fake sig | noble-curves verify reached, `compact sig expected 64 bytes` reject |
| did:plc resolution (`did:plc:ewvi7nxzyoun6zhxrhs64oiz`) | plc.directory 200 fetch OK |
| did:key 未対応 | `unsupported DID method: did:key:xyz` |
| JWK P-256 → `did:key:zDnaerGBD7...` conversion (RFC 7515 A.3.1) | PASS |

### Worker ↔ Container bearer mint (`POST /_internal/mint-pds-bearer`)

| test | result |
|---|---|
| No HMAC | 401 `unauthorized` |
| Wrong HMAC | 401 `unauthorized` |
| Valid HMAC + invalid lxm (非 com.atproto.*) | 400 `lxm must be com.atproto.*` |
| Valid HMAC + valid lxm + AUTH_SERVICE unreachable | 500 `getServiceAuth failed: 503 ... "etzhayyim-auth"` |

### Mock-path E2E (fake-services + container)

Container (`tsx src/server.ts` on :50052) + fake services (fake mint + fake PDS + fake Murakumo on :9100)。`provider: "mock"` adapter で 3 × 500ms 合成 chunk を emit:

- 6 chunks on disk (3 × audio.opus + 3 × video.webm)
- 9 AT records via fake PDS (6 `recordingChunk` + 3 `transcriptSegment`)
- 3 transcripts with `signal:v1:` AES-GCM ciphertext
- chunk file sha256 ≡ AT record sha256 field (integrity verified)
- `POST /v1/leave` → `{status:"left", durationMs:3641}`

## Artifacts (fresh this session)

```
00-contracts/lexicons/com/etzhayyim/apps/meetingRecorder/
  joinMeeting.json leaveMeeting.json getSession.json listSessions.json
  getTranscript.json recordingChunk.json transcriptSegment.json

30-graph/graph-schema/migrations/
  20260422090000_vertex_meeting_recorder_tables.ts  (4 vertex + 1 edge)

50-infra/vultr/meeting-recorder/
  provision.sh                   one-shot idempotent infra create
  deploy.sh                      helm deploy wrapper
  helm/values.yaml               Vultr VKE chart values
  container/
    package.json                 "type":"module" for ESM adapter resolution
    Dockerfile
    control-plane/
      proto/meeting-recorder.proto
      src/server.ts              gRPC :50051 + HTTP :50052
      src/chunk-writer.ts        B2 (or RECORDER_LOCAL_CHUNK_DIR fs-stub) + PDS createRecord
      src/transcript-pipeline.ts Murakumo whisper → signal:v1: → PDS
      src/token-rotator.ts       HMAC mint endpoint + pre-expiry refresh
      src/fake-services.ts       dev-only combined fake backend
    adapters/
      interface.ts               common RecorderAdapter
      teams/index.ts + README    .NET sidecar bridge (stub)
      meet/src/index.ts          Meet Media API + lazy google-auth-library
      zoom/stub/index.ts         Zoom SDK sidecar bridge (stub)
      mock/index.ts              synthetic emitter (RECORDER_ENABLE_MOCK=1)

60-apps/etzhayyim-project-meeting-recorder/appview/etzhayyim-wasm-meeting-recorder-m33tr3c0/
  kotodama.jsonld                actor profile + MCP facade flag
  wrangler.jsonc                 CF bindings + PDS_DID + DID_*_RESOLVER vars
  package.json                   @atproto/crypto@0.4.5
  src/app.ts                     5 XRPC handlers + /_internal/mint-pds-bearer + consent verify

90-docs/
  260422-meeting-recorder-deploy-runbook.md         T-7d..T+1d provisioning
  260422-meeting-recorder-phase1-verification.md    live smoke + phase TODO list
  260422-meeting-recorder-session-summary.md        this file
  adr/0050-meeting-recorder-multi-provider.md       authoritative design record

deps.toml
  [[mitama_actors]]     meeting-recorder entry (m33tr3c0, T3)
  [[legacy_nanoids]]    grandfathered to 2026-10-01 (ADR-0019 Phase 4)
```

## What's NOT yet done (next session)

### Blocking for live production

1. **`./provision.sh` 実行** (user 側、credentials 要): Vultr VKE node pool + B2 bucket + Cloudflare Tunnel + etzhayyim Vault folder + wrangler secret + graph migration apply
2. **`etzhayyim deploy` 初回実行**: meeting-recorder Worker を CF account に展開 → `com.atproto.admin.registerApp` で ES256 signing key を auth Worker `KEYS_DB` に envelope encrypt 保存
3. **Provider credentials 投入** (etzhayyim Vault `meeting-recorder` folder):
   - Microsoft: Azure AD app + tenant admin consent (`Calls.JoinGroupCall.All` + `Calls.AccessMedia.All`)
   - Google: Workspace admin consent で Meet Media API 有効化 + Service Account
   - Zoom: marketplace Server-to-Server OAuth app + Meeting SDK for Linux license

### Provider SDK 本実装 (別 session、大作業)

4. **Teams .NET 8 sidecar** (`adapters/teams/bin/RecorderTeams`): Microsoft.Graph.Communications.Calls.Media SDK + `CallHandler` + raw media → HTTP 5100 bridge
5. **Meet Media API gRPC stream** (`adapters/meet/src/index.ts`): auth path は完成、`MeetMediaClient.subscribe` で data event → onAudioChunk/onVideoChunk wire が残
6. **Zoom C++ sidecar** (`adapters/zoom/bin/RecorderZoom`): SDK 再配布不可 → k8s initContainer で signed URL pull + Zoom SDK raw recording callback

### Phase 4+ (security hardening)

7. **Signal X25519 shared-secret bootstrap** (`transcript-pipeline.ts`): 現在は dev key fallback (sessionDid hash)。`com.etzhayyim.signal.getPrekeyBundle` + HKDF に置換、container が onBehalfOfDid の prekey を pull して session 限りの秘密を導出
8. **did:etzhayyim + did:plc multibase JWK 両対応** は完了 (Phase 4)。`did:key` method 対応は別 ADR で検討

## Smoke をもう一度流す手順 (mock-path, 次 session 用)

```bash
cd 50-infra/vultr/meeting-recorder/container/control-plane
pnpm install --ignore-workspace                                    # once

# terminal 1 — fake backend (mint + PDS + Murakumo 全部入り)
RECORDER_TUNNEL_SECRET=fake-tunnel-secret ./node_modules/.bin/tsx src/fake-services.ts
# → [fake-services] listening on :9100

# terminal 2 — container
rm -rf /tmp/mrec-chunks && mkdir -p /tmp/mrec-chunks
RECORDER_ENABLE_MOCK=1 \
  RECORDER_MOCK_ITER_MS=500 RECORDER_MOCK_ITERATIONS=3 \
  RECORDER_LOCAL_CHUNK_DIR=/tmp/mrec-chunks \
  RECORDER_TUNNEL_SECRET=fake-tunnel-secret \
  PDS_XRPC=http://localhost:9100/xrpc \
  MURAKUMO_ENDPOINT=http://localhost:9100/v1/audio/transcriptions \
  MURAKUMO_API_KEY=fake \
  SIGNAL_SESSION_KEY_HEX=$(openssl rand -hex 32) \
  ./node_modules/.bin/tsx src/server.ts
# → http gateway :50052 + grpc :50051

# terminal 3 — drive
curl -X POST http://localhost:50052/v1/join -H "content-type: application/json" -d '{
  "sessionId":"ses_smoke_003", "sessionDid":"did:web:meeting-recorder.etzhayyim.com:session:mock:smoke003",
  "provider":"mock", "joinTarget":{}, "onBehalfOfDid":"did:web:jun.etzhayyim.com",
  "recordAudio":true, "recordVideo":true, "transcribe":true, "chunkSeconds":1,
  "pdsBearerMint": {"url":"http://localhost:9100/_internal/mint-pds-bearer","secret":"fake-tunnel-secret"}
}'
sleep 3
curl http://localhost:9100/_smoke/state | jq .
find /tmp/mrec-chunks -type f
curl -X POST http://localhost:50052/v1/leave -d '{"sessionId":"ses_smoke_003"}'
```

Expected: 6 chunks on disk + 9 AT records via fake PDS + sha256 integrity.

## References

- ADR-0050 — meeting-recorder multi-provider actor (authoritative)
- ADR-0048 — Kotoba/Datomic Vultr + B2 primary (egress-free storage)
- ADR-0042 — kotodama MCP Tool Facade (per-actor MCP endpoint)
- ADR-0036 — Worker-direct Hyperdrive Persistence
- ADR-0029 — did:etzhayyim Method Specification
- ADR-0022 — Auth 2-token model (ServiceAuth `lxm` scoping SSoT)
- ADR-0018 — PII Tier 3 + Cohort-First Pattern
- ADR-0005 — Shannon Redundancy Prohibition
- 260413 — Path F Agent Loop Unification (memory/consent/audit/scheduler middleware)
- `@atproto/crypto` v0.4.5 — multibase + multi-alg verify
