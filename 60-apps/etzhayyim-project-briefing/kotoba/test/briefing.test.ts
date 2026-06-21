import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
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
} from "../src/index.js";

const OWNER = "did:web:briefing.etzhayyim.com";

describe("briefing kotoba (kotoba-E2E split)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("room (PLAINTEXT public catalog)", () => {
    it("registers, dedups, validates, gets, lists/filters", async () => {
      expect((await registerRoom(e, { roomId: "r1", name: "Standup", maxParticipants: 12 })).status).toBe("registered");
      expect((await registerRoom(e, { roomId: "r1", name: "Standup" })).status).toBe("alreadyExists");
      expect((await registerRoom(e, { roomId: "rX", name: "Bad", maxParticipants: 0 })).status).toBe("rejected");
      expect((await registerRoom(e, { roomId: "rY", name: "" })).status).toBe("rejected");
      await registerRoom(e, { roomId: "r2", name: "Retro", status: "closed" });
      const got = await getRoom(e, { roomId: "r1" });
      expect(got.room?.name).toBe("Standup");
      expect(got.room?.maxParticipants).toBe(12);
      expect((await getRoom(e, { roomId: "nope" })).error).toBe("notFound");
      expect((await listRooms(e)).total).toBe(2);
      expect((await listRooms(e, { status: "closed" })).total).toBe(1);
    });
  });

  describe("agendaItem (PLAINTEXT, FK to room)", () => {
    it("requires the room to exist, dedups, orders by ordinal", async () => {
      expect((await registerAgendaItem(e, { agendaItemId: "a1", roomId: "r1", ordinal: 0, title: "Intro", allocatedSeconds: 300 })).status).toBe("rejected"); // room missing
      await registerRoom(e, { roomId: "r1", name: "Standup" });
      expect((await registerAgendaItem(e, { agendaItemId: "a2", roomId: "r1", ordinal: 2, title: "Wrap", allocatedSeconds: 120 })).status).toBe("registered");
      expect((await registerAgendaItem(e, { agendaItemId: "a1", roomId: "r1", ordinal: 1, title: "Intro", allocatedSeconds: 300 })).status).toBe("registered");
      expect((await registerAgendaItem(e, { agendaItemId: "a1", roomId: "r1", ordinal: 1, title: "Intro", allocatedSeconds: 300 })).status).toBe("alreadyExists");
      const list = await listAgenda(e, { roomId: "r1" });
      expect(list.total).toBe(2);
      expect(list.items[0].agendaItemId).toBe("a1"); // ordinal 1 before ordinal 2
    });
  });

  describe("transcript (E2E-ENCRYPTED PII)", () => {
    it("seals via encryptedWrite, round-trips, validates", async () => {
      const ok = await recordTranscript(e, { transcriptId: "t1", roomId: "r1", speakerDid: "did:web:alice", lang: "en", text: "hello team", offsetSeconds: 12 });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      expect((await recordTranscript(e, { transcriptId: "tX", roomId: "r1", speakerDid: "d", lang: "en", text: "", offsetSeconds: 1 })).status).toBe("rejected");
      const got = await getTranscript(e, { transcriptId: "t1" });
      expect(got.transcript?.text).toBe("hello team");
      expect(got.transcript?.speakerDid).toBe("did:web:alice");
      await recordTranscript(e, { transcriptId: "t2", roomId: "r2", speakerDid: "did:web:bob", lang: "ja", text: "konnichiwa", offsetSeconds: 30 });
      expect((await listTranscripts(e)).total).toBe(2);
      expect((await listTranscripts(e, { roomId: "r1" })).total).toBe(1);
    });

    it("enforces read-cap: a non-recipient DID cannot decrypt", async () => {
      await recordTranscript(e, { transcriptId: "t1", roomId: "r1", speakerDid: "did:web:alice", lang: "en", text: "secret", offsetSeconds: 1 });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listTranscripts(outsider)).total).toBe(0);
    });

    it("grants read-cap to an explicit recipient", async () => {
      const partner = "did:web:partner.example";
      const r = await recordTranscript(e, { transcriptId: "t1", roomId: "r1", speakerDid: "did:web:alice", lang: "en", text: "shared", offsetSeconds: 1, recipients: [partner] });
      expect(r.status).toBe("recorded");
      expect((await listTranscripts(e)).total).toBe(1);
    });
  });

  describe("recordingAsset (E2E-ENCRYPTED consent + media pointer)", () => {
    it("seals, validates consent 0-100, points at etzhayyim-resident r2Key", async () => {
      const ok = await recordRecording(e, { recordingId: "rec1", roomId: "r1", r2Key: "b2://briefing/rec1.webm", durationMs: 600000, consentPct: 100 });
      expect(ok.status).toBe("recorded");
      expect((await recordRecording(e, { recordingId: "recX", roomId: "r1", r2Key: "k", durationMs: 1, consentPct: 200 })).status).toBe("rejected");
      expect((await listRecordings(e, { roomId: "r1" })).total).toBe(1);
      expect((await listRecordings(e))?.items[0].r2Key).toBe("b2://briefing/rec1.webm");
    });
  });

  describe("actionItem (E2E-ENCRYPTED assignee PII)", () => {
    it("seals, validates, lists/filters by room", async () => {
      expect((await recordActionItem(e, { actionItemId: "ai1", roomId: "r1", assigneeDid: "did:web:carol", text: "ship kotoba" })).status).toBe("recorded");
      expect((await recordActionItem(e, { actionItemId: "aiX", roomId: "r1", assigneeDid: "d", text: "" })).status).toBe("rejected");
      await recordActionItem(e, { actionItemId: "ai2", roomId: "r2", assigneeDid: "did:web:dave", text: "review" });
      expect((await listActionItems(e)).total).toBe(2);
      expect((await listActionItems(e, { roomId: "r1" })).total).toBe(1);
    });
  });

  describe("decision (E2E-ENCRYPTED confidential governance + ballots)", () => {
    it("seals ballots, round-trips, validates tally", async () => {
      const ok = await recordDecision(e, {
        decisionId: "d1",
        roomId: "r1",
        statement: "Adopt kotoba-E2E split",
        method: "vote",
        votesFor: 3,
        votesAgainst: 1,
        ballots: { "did:web:alice": "for", "did:web:bob": "against" },
      });
      expect(ok.status).toBe("recorded");
      expect((await recordDecision(e, { decisionId: "dX", roomId: "r1", statement: "x", votesFor: -1, votesAgainst: 0 })).status).toBe("rejected");
      const got = await getDecision(e, { decisionId: "d1" });
      expect(got.decision?.votesFor).toBe(3);
      expect(got.decision?.ballots["did:web:alice"]).toBe("for");
      expect((await listDecisions(e, { roomId: "r1" })).total).toBe(1);
    });

    it("enforces read-cap on ballots: outsider sees zero", async () => {
      await recordDecision(e, { decisionId: "d1", roomId: "r1", statement: "x", votesFor: 1, votesAgainst: 0 });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listDecisions(outsider)).total).toBe(0);
    });
  });

  describe("coverage rollup", () => {
    it("counts plaintext rooms/agenda + E2E content collections", async () => {
      await registerRoom(e, { roomId: "r1", name: "Standup" });
      await registerRoom(e, { roomId: "r2", name: "Retro", status: "closed" });
      await registerAgendaItem(e, { agendaItemId: "a1", roomId: "r1", ordinal: 1, title: "Intro", allocatedSeconds: 300 });
      await recordTranscript(e, { transcriptId: "t1", roomId: "r1", speakerDid: "did:web:alice", lang: "en", text: "hi", offsetSeconds: 1 });
      await recordRecording(e, { recordingId: "rec1", roomId: "r1", r2Key: "k", durationMs: 1000, consentPct: 100 });
      await recordActionItem(e, { actionItemId: "ai1", roomId: "r1", assigneeDid: "did:web:carol", text: "do it" });
      await recordDecision(e, { decisionId: "d1", roomId: "r1", statement: "ok", votesFor: 2, votesAgainst: 0 });
      const cov = await coverage(e);
      expect(cov.roomCount).toBe(2);
      expect(cov.agendaItemCount).toBe(1);
      expect(cov.transcriptCount).toBe(1);
      expect(cov.recordingCount).toBe(1);
      expect(cov.actionItemCount).toBe(1);
      expect(cov.decisionCount).toBe(1);
      expect(cov.roomsByStatus?.active).toBe(1);
      expect(cov.roomsByStatus?.closed).toBe(1);
    });
  });
});
