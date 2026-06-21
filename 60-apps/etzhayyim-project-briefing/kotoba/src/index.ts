/**
 * briefing kotoba — barrel. kotoba-E2E split (ADR-2605181100): public meeting
 * structure (room / agendaItem) plaintext via sdk.write/read; meeting content +
 * per-person data (transcript / recordingAsset / actionItem / decision) sealed
 * E2E via sdk.encryptedWrite/Read. Raw recording-blob archive + GPU/LLM
 * inference stay etzhayyim via consent-capability.
 */
export * from "./types.js";
export {
  registerRoom,
  getRoom,
  listRooms,
  registerAgendaItem,
  listAgenda,
  recordTranscript,
  listTranscripts,
  getTranscript,
  recordRecording,
  listRecordings,
  recordActionItem,
  listActionItems,
  recordDecision,
  listDecisions,
  getDecision,
  coverage,
} from "./registry.js";
