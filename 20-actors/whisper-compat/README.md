# Whisper Clean Room Actor

Clean-room, API-compatible implementation of an audio **speech-to-text (STT/ASR)**
platform (OpenAI `audio/transcriptions` + `audio/translations` shape), backed by
Datomic and Py Kotodama WASM.

This actor closes the **one missing primitive** identified in
ADR-2606271930: `elevenlabs-compat` gives TTS (speech *out*) but there was no
clean-room STT (speech *in*). `whisper-compat` is the input half of `denwaban`'s
voice I/O.

## Architecture
- **State:** Datomic-backed, immutable/time-travel record keeping (transcripts are
  transient by default — see G1 no-secret-recording in ADR-2606271930).
- **Schema:** `schema/whisper.kotoba`.
- **Execution:** Py Kotodama WASM, intercepting inbound REST + a streaming transcript
  channel (partial → final) for barge-in.

## Status

**R0 scaffold** — socket-free core only. No live audio, no socket. `transcribe`
materializes against the in-memory `*store*`; streaming is fixture-driven. Live
audio ingest is outward-gated (G7) and lands in a later R-cycle.

```
bb test   # cljc contract test under babashka
```
