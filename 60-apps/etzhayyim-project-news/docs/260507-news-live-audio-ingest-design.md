# News Live Audio Ingest Design

Date: 2026-05-07

## Goal

Add a public broadcast ingestion path for live news and radio sources:

```
public stream URL -> short audio window -> Murakumo STT -> transcript -> claim extraction -> news intel report
```

This is separate from `meetingRecorder`. Meeting recordings are private,
consent-bound, and Signal-encrypted. Live audio ingest is for public broadcast
monitoring and must keep source attribution, retention, and publication gates
visible.

## Contract

- XRPC/BPMN NSID: `com.etzhayyim.apps.news.liveAudioIngest`
- BPMN process: `news_live_audio_ingest`
- Source contract: `sourceId`, `sourceName`, `streamUrl`
- Optional metadata: `sourceUrl`, `sourceType`, `region`, `country`, `topic`, `lang`
- Capture controls: `captureSeconds`, `maxBytes`, optional `retainAudio`,
  `retentionDays`, and `rightsPolicy`

## Source Registry

- Record collection: `com.etzhayyim.apps.news.liveAudioSource`
- Write command: `com.etzhayyim.apps.news.registerLiveAudioSource`
- Read query: `com.etzhayyim.apps.news.listLiveAudioSources`
- Policy audit query: `com.etzhayyim.apps.news.auditLiveAudioPolicies`
- Scheduler command: `com.etzhayyim.apps.news.scheduleLiveAudioIngest`
- Scheduler state collection: `com.etzhayyim.apps.news.liveAudioScheduleState`
- Registry records include stream URL, language, region/country, topic set,
  capture limits, scheduler cadence/cooldown, retention policy, rights policy,
  and `active | paused | disabled` status.
- Register/list/schedule responses include `policyGate` or `policySummary` so
  operators can see whether publication, maps export, and audio retention are
  currently allowed before launching the ingest.
- `auditLiveAudioPolicies` returns source-level blocked flags and aggregate
  counts for publication, maps export, and audio retention. Use `onlyBlocked`
  for rights review queues.
- The scheduler lists `status=active` records, applies cadence, cooldown, and
  dispatch-failure backoff, then posts due sources to the BPMN dispatcher for
  `news_live_audio_ingest` with policy-gated capture parameters. If the source
  policy does not allow audio retention, `retainAudio` and `retentionDays` are
  forced to `false` and `0` in the dispatched payload.
- Heartbeat invokes the scheduler with `maxLaunches=3` unless
  `NEWS_LIVE_AUDIO_SCHEDULER_DISABLED=true`.

## Pipeline

1. `news.liveAudio.transcribeWindow`
   - Capture a bounded byte window from a public direct audio stream.
   - Resolve HLS `.m3u8` playlists to recent media segments when needed.
   - Detect MPEG-TS HLS segments and remux them to `audio/mp4` for STT with
     ffmpeg, while retaining the original capture hash and optional artifact.
   - Submit the chunk to Murakumo audio transcription.
   - Return `transcriptText`, language, segments, byte count, stream kind,
     resolved segment URLs, remux status, STT upload metadata, and audio hash
     metadata.
   - Enforce retention policy before storing original audio. Audio retention is
     disabled unless `rightsPolicy` explicitly allows archival/retention.
2. `generic.llm.json`
   - Extract title, summary, facts, findings, and entities from transcript text.
   - Treat partial transcript uncertainty explicitly.
3. `xrpc.com.etzhayyim.apps.news.analyzeIntel`
   - Write an attributed `com.etzhayyim.apps.intel.report`.
   - Use `sourceType=broadcast` unless a source-specific type is supplied.
   - Evaluate `policyGate` from `rightsPolicy`, country, and source type.
     Publication and maps export are blocked when the source policy does not
     permit them.
   - Forward spatial entity/incident candidates from transcript entities to
     `com.etzhayyim.apps.maps.spatialEventRecord` as
     `news.broadcast.entityMention` events. Set
     `NEWS_MAPS_SPATIAL_EXPORT_DISABLED=true` to disable this bridge.
4. Optional `xrpc.com.etzhayyim.apps.news.publishIntel`
   - Publish only when the process input sets `publish=true` and
     `policyGate.allowPublish=true`.
5. `generic.audit.emit`
   - Record source, byte count, STT language, LLM model, and report metadata.

## Initial Scope

The first worker supports direct public audio streams such as MP3/AAC/Icecast
URLs and HLS media playlists. HLS MPEG-TS captures are remuxed to M4A before
Murakumo STT when ffmpeg is available in the worker image. When
`retainAudio=true` and B2 credentials are configured, the original captured
window is stored under `news/live-audio/{sourceId}/`. DASH playlist handling
and diarization remain follow-up work.

## Follow-Ups

- Add DASH segment resolver with per-source rate limits.
- Emit maps `SpatialEvent` candidates when transcript entities include place
  or incident hints.
- Add a UI surface for editing source rights policy, retention, and scheduler
  status without direct XRPC calls.
