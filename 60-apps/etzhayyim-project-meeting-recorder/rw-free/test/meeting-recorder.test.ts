import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
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
} from "../src/index.js";

const OWNER = "did:web:meeting-recorder.etzhayyim.com";

describe("meeting-recorder rw-free (WAVE 2 kotoba-E2E split)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("providerCapability (PLAINTEXT public catalog)", () => {
    it("registers, dedups, validates, gets, lists/filters", async () => {
      expect(
        (await registerProvider(e, { provider: "teams", displayName: "Microsoft Teams", codecs: ["opus", "h264"], minChunkSeconds: 15, maxChunkSeconds: 300, supportsVideo: true, supportsTranscription: true })).status,
      ).toBe("registered");
      // dedup on same provider
      expect(
        (await registerProvider(e, { provider: "teams", displayName: "Microsoft Teams", codecs: ["opus"], minChunkSeconds: 15, maxChunkSeconds: 300 })).status,
      ).toBe("alreadyExists");
      // invalid provider
      expect(
        (await registerProvider(e, { provider: "skype" as any, displayName: "x", codecs: [], minChunkSeconds: 15, maxChunkSeconds: 60 })).status,
      ).toBe("rejected");
      // invalid chunk bounds (min > max)
      expect(
        (await registerProvider(e, { provider: "meet", displayName: "Google Meet", codecs: ["opus"], minChunkSeconds: 100, maxChunkSeconds: 30 })).status,
      ).toBe("rejected");
      await registerProvider(e, { provider: "meet", displayName: "Google Meet", codecs: ["opus", "vp9"], minChunkSeconds: 30, maxChunkSeconds: 120, supportsVideo: true });
      await registerProvider(e, { provider: "zoom", displayName: "Zoom", codecs: ["opus"], minChunkSeconds: 15, maxChunkSeconds: 200, supportsVideo: false });

      const got = await getProvider(e, { provider: "meet" });
      expect(got.provider?.displayName).toBe("Google Meet");
      expect(got.provider?.supportsVideo).toBe(true);
      expect((await getProvider(e, { provider: "zoom" })).provider?.supportsVideo).toBe(false);
      expect((await listProviders(e)).total).toBe(3);
      expect((await listProviders(e, { supportsVideo: true })).total).toBe(2);
    });
  });

  describe("session (E2E-ENCRYPTED, per-person consent-gated)", () => {
    it("seals via encryptedWrite, round-trips via encryptedRead, validates, gets, lists/filters", async () => {
      const ok = await recordSession(e, { sessionId: "s1", provider: "teams", onBehalfOfDid: "did:web:jun.example", externalMeetingId: "ext-abc", status: "joined", durationMs: 360000, chunkCount: 6, participantCount: 3 });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      // missing onBehalfOfDid
      expect((await recordSession(e, { sessionId: "sX", provider: "teams", onBehalfOfDid: "", status: "joined" })).status).toBe("rejected");
      // invalid provider
      expect((await recordSession(e, { sessionId: "sY", provider: "webex" as any, onBehalfOfDid: "did:web:x", status: "joined" })).status).toBe("rejected");

      const got = await getSession(e, { sessionId: "s1" });
      expect(got.session?.onBehalfOfDid).toBe("did:web:jun.example");
      expect(got.session?.externalMeetingId).toBe("ext-abc");
      expect(got.session?.chunkCount).toBe(6);

      await recordSession(e, { sessionId: "s2", provider: "zoom", onBehalfOfDid: "did:web:ann.example", status: "left", durationMs: 120000, chunkCount: 2, participantCount: 2 });
      expect((await listSessions(e)).total).toBe(2);
      expect((await listSessions(e, { provider: "teams" })).total).toBe(1);
      expect((await listSessions(e, { status: "left" })).total).toBe(1);
      expect((await listSessions(e, { onBehalfOfDid: "did:web:ann.example" })).total).toBe(1);
    });

    it("enforces read-cap: a non-recipient DID cannot decrypt the session", async () => {
      await recordSession(e, { sessionId: "s1", provider: "teams", onBehalfOfDid: "did:web:jun.example", status: "joined" });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listSessions(outsider)).total).toBe(0);
      expect((await getSession(outsider, { sessionId: "s1" })).error).toBe("notFound");
    });

    it("grants read-cap to an explicit recipient", async () => {
      const partner = "did:web:partner.example";
      const r = await recordSession(e, { sessionId: "s1", provider: "teams", onBehalfOfDid: "did:web:jun.example", status: "joined", recipients: [partner] });
      expect(r.status).toBe("recorded");
      expect((await listSessions(e)).total).toBe(1);
    });
  });

  describe("recordingChunk (E2E-ENCRYPTED, B2 pointer + PII Tier 1)", () => {
    it("seals B2 pointer + participantHashes, round-trips, validates, lists by session", async () => {
      const ok = await recordChunk(e, { sessionId: "s1", provider: "teams", seq: 0, kind: "mixed", codec: "opus", b2Bucket: "mr", b2Key: "meeting-recorder/s1/0.webm", sha256: "abc123", sizeBytes: 1048576, durationMs: 60000, participantHashes: ["h1", "h2"] });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      // invalid kind
      expect((await recordChunk(e, { sessionId: "s1", provider: "teams", seq: 1, kind: "hologram" as any, b2Key: "k", sha256: "z", durationMs: 1000 })).status).toBe("rejected");
      // missing b2Key
      expect((await recordChunk(e, { sessionId: "s1", provider: "teams", seq: 2, kind: "audio", b2Key: "", sha256: "z", durationMs: 1000 })).status).toBe("rejected");
      // negative seq
      expect((await recordChunk(e, { sessionId: "s1", provider: "teams", seq: -1, kind: "audio", b2Key: "k", sha256: "z", durationMs: 1000 })).status).toBe("rejected");

      await recordChunk(e, { sessionId: "s1", provider: "teams", seq: 1, kind: "audio", b2Key: "meeting-recorder/s1/1.opus", sha256: "def456", durationMs: 60000 });
      await recordChunk(e, { sessionId: "s2", provider: "zoom", seq: 0, kind: "audio", b2Key: "meeting-recorder/s2/0.opus", sha256: "ghi789", durationMs: 30000 });
      expect((await listChunks(e)).total).toBe(3);
      expect((await listChunks(e, { sessionId: "s1" })).total).toBe(2);
      const c = (await listChunks(e, { sessionId: "s1" })).items[0];
      expect(c.participantHashes).toEqual(["h1", "h2"]);
    });
  });

  describe("transcriptSegment (E2E-ENCRYPTED, transcript content)", () => {
    it("seals text in the envelope, round-trips, validates confidencePct integer 0-100", async () => {
      const ok = await recordSegment(e, { sessionId: "s1", chunkSeq: 0, seq: 0, startedAtMs: 0, endedAtMs: 4200, speakerHash: "spk1", lang: "ja", confidencePct: 92, text: "こんにちは", model: "whisper-large-v3" });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      // confidence > 100 rejected (float-to-int migration guard)
      expect((await recordSegment(e, { sessionId: "s1", chunkSeq: 0, seq: 1, startedAtMs: 0, endedAtMs: 1, confidencePct: 200, text: "x" })).status).toBe("rejected");
      // float confidence rejected
      expect((await recordSegment(e, { sessionId: "s1", chunkSeq: 0, seq: 2, startedAtMs: 0, endedAtMs: 1, confidencePct: 0.9 as any, text: "x" })).status).toBe("rejected");

      await recordSegment(e, { sessionId: "s1", chunkSeq: 0, seq: 1, startedAtMs: 4200, endedAtMs: 8000, lang: "ja", confidencePct: 88, text: "ありがとう" });
      await recordSegment(e, { sessionId: "s2", chunkSeq: 0, seq: 0, startedAtMs: 0, endedAtMs: 2000, lang: "en", confidencePct: 95, text: "hello" });
      expect((await listSegments(e)).total).toBe(3);
      const s1segs = await listSegments(e, { sessionId: "s1" });
      expect(s1segs.total).toBe(2);
      expect(s1segs.items[0].text).toBe("こんにちは");
      expect(s1segs.items[0].confidencePct).toBe(92);
    });

    it("enforces read-cap: outsider cannot read transcript segments", async () => {
      await recordSegment(e, { sessionId: "s1", chunkSeq: 0, seq: 0, startedAtMs: 0, endedAtMs: 1000, confidencePct: 90, text: "secret" });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listSegments(outsider)).total).toBe(0);
    });
  });

  describe("coverage rollup (per-innerType isolation across one wrapper)", () => {
    it("counts plaintext catalog + each E2E inner-type separately, no cross-contamination", async () => {
      await registerProvider(e, { provider: "teams", displayName: "Teams", codecs: ["opus"], minChunkSeconds: 15, maxChunkSeconds: 300 });
      await registerProvider(e, { provider: "zoom", displayName: "Zoom", codecs: ["opus"], minChunkSeconds: 15, maxChunkSeconds: 200 });
      await recordSession(e, { sessionId: "s1", provider: "teams", onBehalfOfDid: "did:web:jun", status: "joined" });
      await recordSession(e, { sessionId: "s2", provider: "teams", onBehalfOfDid: "did:web:ann", status: "left" });
      await recordSession(e, { sessionId: "s3", provider: "zoom", onBehalfOfDid: "did:web:bob", status: "joined" });
      await recordChunk(e, { sessionId: "s1", provider: "teams", seq: 0, kind: "audio", b2Key: "k0", sha256: "h0", durationMs: 60000 });
      await recordChunk(e, { sessionId: "s1", provider: "teams", seq: 1, kind: "audio", b2Key: "k1", sha256: "h1", durationMs: 60000 });
      await recordSegment(e, { sessionId: "s1", chunkSeq: 0, seq: 0, startedAtMs: 0, endedAtMs: 1000, confidencePct: 90, text: "t" });

      const cov = await coverage(e);
      expect(cov.providerCapabilityCount).toBe(2);
      expect(cov.sessionCount).toBe(3);
      expect(cov.recordingChunkCount).toBe(2);
      expect(cov.transcriptSegmentCount).toBe(1);
      expect(cov.sessionsByProvider?.teams).toBe(2);
      expect(cov.sessionsByProvider?.zoom).toBe(1);
    });
  });
});
