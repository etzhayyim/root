/**
 * meeting-recorder rw-free — barrel. WAVE 2 maximal migration (kotoba-E2E
 * split, ADR-2605181100): plaintext provider catalog + three E2E per-person
 * record kinds (session / recordingChunk / transcriptSegment). Recorder-bot
 * join/capture execution, GPU/MLX whisper inference, B2 media-blob custody, and
 * consentToken custody stay etzhayyim via consent-capability.
 */
export * from "./types.js";
export {
  registerProvider,
  getProvider,
  listProviders,
  recordSession,
  getSession,
  listSessions,
  recordChunk,
  listChunks,
  recordSegment,
  listSegments,
  coverage,
} from "./registry.js";
