# meeting-recorder deploy runbook (Phase 1)

- Actor: `did:web:meeting-recorder.etzhayyim.com` (nanoid `m33tr3c0`)
- Control-plane: CF Worker `meeting-recorder.etzhayyim.com` (XRPC + MCP facade, ADR-0042)
- Media-plane: Vultr VKE LAX, node pool `meeting-recorder` (vhf-4c-16gb × 2)
- Storage: Backblaze B2 `etzhayyim-recordings/meeting-recorder/...` (ADR-0048 egress-free)
- Transcription: Murakumo MLX `whisper-large-v3`
- Providers: Microsoft Teams, Google Meet, Zoom

## T-7d: provider onboarding

### Microsoft Teams

1. etzhayyim Japan tenant で Azure AD app `etzhayyim-meeting-recorder` を作成。
2. Application permissions 付与 + tenant admin consent:
   - `Calls.JoinGroupCall.All`
   - `Calls.AccessMedia.All`
   - `OnlineMeetings.Read.All`
3. Client secret を生成し `etzhayyim vault add --folder meeting-recorder --name AZURE_AD_CLIENT_SECRET`。
4. Notification URL を CF Worker `meeting-recorder.etzhayyim.com/_graph/callbacks` に設定。

### Google Meet

1. GCP project で Meet Media API を有効化 (2025 GA, requires Workspace admin consent)。
2. Service Account を作成し scope `https://www.googleapis.com/auth/meetings.media.audio.readonly` + `...video.readonly` を付与。
3. Service Account JSON を `etzhayyim vault add --folder meeting-recorder --name GOOGLE_SERVICE_ACCOUNT_JSON`。

### Zoom

1. Zoom Marketplace で Server-to-Server OAuth app を作成、scope `meeting:read:admin` + `meeting:write:admin`。
2. Zoom Meeting SDK for Linux を別途ライセンス取得、SDK key / secret を vault 登録。
3. Host アカウントで "Automatic recording" を disable、bot 側で制御。

## T-3d: Vultr infra provisioning

```bash
# 1. Node pool 追加 (既存 RW cluster に相乗り)
vultr-cli kubernetes node-pool create \
  --cluster-id a61d513b-f9b7-4121-abb9-b53732aa5ec4 \
  --label meeting-recorder \
  --plan vhf-4c-16gb \
  --node-quantity 2 \
  --tag vke.vultr.com/node-pool=meeting-recorder

# 2. B2 bucket + app key (prefix-scoped)
b2 bucket create etzhayyim-recordings allPrivate
b2 key create --bucket etzhayyim-recordings \
  --namePrefix meeting-recorder/ \
  meeting-recorder-rw readFiles,writeFiles,deleteFiles

# 3. Cloudflare Tunnel (control-plane のみ)
cloudflared tunnel create meeting-recorder-control
cloudflared tunnel route dns meeting-recorder-control meeting-recorder-ctrl.etzhayyim.com
```

## T-1d: CI / image build

```bash
cd 50-infra/vultr/meeting-recorder
docker build -t registry.etzhayyim.com/meeting-recorder-unix:0.1.0 container/
docker push registry.etzhayyim.com/meeting-recorder-unix:0.1.0
```

## Day 0: cutover

### Step 1. Graph migration

```bash
cd 30-graph/graph-schema
pnpm migrate up   # 20260422090000_vertex_meeting_recorder_tables.ts
```

Verify:

```sql
SELECT relname FROM pg_class
WHERE relname LIKE 'vertex_meetingrecorder_%' OR relname LIKE 'edge_meetingrecorder_%';
-- expect 5 tables
```

### Step 2. Vultr VKE deploy

```bash
cd 50-infra/vultr/meeting-recorder
etzhayyim vault run --folder meeting-recorder -- ./deploy.sh
```

### Step 3. CF Worker control-plane deploy

```bash
cd 60-apps/etzhayyim-project-meeting-recorder
etzhayyim deploy   # writes did.json, configures XRPC routes, MCP facade
```

### Step 4. Smoke tests (per provider)

```bash
# Teams
etzhayyim agent-token --lxm com.etzhayyim.apps.meetingRecorder.joinMeeting \
  | xargs -I{} curl -H "Authorization: Bearer {}" \
    https://meeting-recorder.etzhayyim.com/xrpc/com.etzhayyim.apps.meetingRecorder.joinMeeting \
    -d '{"provider":"teams","joinTarget":{"joinUrl":"<test-meeting>"},"onBehalfOfDid":"did:web:jun.etzhayyim.com","consentToken":"<signed-jwt>"}'

# Meet / Zoom も同様
```

期待応答: `{"sessionDid":"did:web:meeting-recorder.etzhayyim.com:session:<provider>:<mtgId>", "status":"joining"}`。

### Step 5. Regression (既存 topology 非破壊確認)

- PDS `/_app/meta` が 200 応答
- Kotoba/Datomic `vertex_repo_commit` が通常 rate で append される (recorder writes が graph を専有していない)
- Murakumo `/v1/audio/transcriptions` latency p95 < 2s (whisper-large-v3)

## T+1d: 監視

| metric | threshold | alert |
|---|---|---|
| pod OOM kill | > 0 / 24h | pagerduty, scale node to vhf-8c-32gb |
| B2 write error rate | > 1% / 1h | vault auth rotate |
| chunk sha256 mismatch | > 0 | immediate, stop recording, audit |
| transcript cipher length = 0 | > 5% | Murakumo fleet health check |
| Teams bot join failure rate | > 10% / 1h | Azure AD app secret expiry check |

## Rollback

```bash
helm -n meeting-recorder rollback meeting-recorder 0
# CF Worker: etzhayyim deploy --version <prev>
# Graph migration: pnpm migrate down  (safe — no data lost, tables retain content)
```

## Phase 2 (deferred)

- Auto-join via Outlook Calendar MCP + Google Calendar trigger
- Speaker diarization (pyannote) on top of whisper segments
- Real-time streaming transcript via SSE to Svelte UI
- Multi-region: Vultr VKE NRT / FRA replicas for latency-sensitive APAC/EU meetings
- did:plc migration per ADR-0019 (before 2026-10-01)

## References

- ADR-0042 — kotodama MCP Tool Facade (XRPC ↔ MCP co-exposure)
- ADR-0036 — Worker-direct Hyperdrive Persistence
- ADR-0048 — Kotoba/Datomic Vultr + B2 primary (egress-free)
- ADR-0018 — PII Tier 3 (transcript encrypt)
- ADR-0022 — Auth 2-token model (Service Auth `lxm` scoping)
- ADR-0019 — atproto-native identifier topology (did:plc deadline)
