import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  seedEvent,
  listEvents,
  recordJoucho,
  listJoucho,
  getJoucho,
  coverage,
} from "../src/index.js";

const OWNER = "did:web:shinka.etzhayyim.com";

describe("shinka rw-free (kotoba-E2E split)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("historicalEvent (PLAINTEXT public catalog)", () => {
    it("records, dedups, validates, lists/filters by partition + sponsorable", async () => {
      expect((await seedEvent(e, { eventId: "ev1", title: "Fall of X", partition: "medieval-asia", eventAt: "1200-01-01T00:00:00Z", propagationCount: 12, sponsorable: true })).status).toBe("recorded");
      expect((await seedEvent(e, { eventId: "ev1", title: "Fall of X", partition: "medieval-asia", eventAt: "1200-01-01T00:00:00Z", propagationCount: 12 })).status).toBe("alreadyExists");
      expect((await seedEvent(e, { eventId: "evBad", title: "t", partition: "p", eventAt: "x", propagationCount: -1 })).status).toBe("rejected");
      expect((await seedEvent(e, { eventId: "", title: "t", partition: "p", eventAt: "x", propagationCount: 1 })).status).toBe("rejected");
      await seedEvent(e, { eventId: "ev2", title: "Treaty", partition: "modern-europe", eventAt: "1815-06-09T00:00:00Z", propagationCount: 4, sponsorable: false });
      expect((await listEvents(e)).total).toBe(2);
      expect((await listEvents(e, { partition: "medieval-asia" })).total).toBe(1);
      expect((await listEvents(e, { sponsorableOnly: true })).total).toBe(1);
    });
  });

  describe("jouchoAssessment (E2E-ENCRYPTED per-actor CUI)", () => {
    beforeEach(async () => {
      // FK target: a known partition must exist.
      await seedEvent(e, { eventId: "ev1", title: "Fall of X", partition: "medieval-asia", eventAt: "1200-01-01T00:00:00Z", propagationCount: 12 });
      await seedEvent(e, { eventId: "ev2", title: "Treaty", partition: "modern-europe", eventAt: "1815-06-09T00:00:00Z", propagationCount: 4 });
    });

    it("seals via encryptedWrite, round-trips via encryptedRead, validates scores + FK", async () => {
      const ok = await recordJoucho(e, { assessmentId: "a1", actorDid: "did:web:actor1", partition: "medieval-asia", joy: 60, calm: 40, stress: 20, gratitude: 50, focus: 70, mood: "focused", summary: "kyumei: gap in source provenance" });
      expect(ok.status).toBe("recorded");
      expect(ok.keyId).toBeTruthy();
      // score out of 0-100 range rejected
      expect((await recordJoucho(e, { assessmentId: "aX", actorDid: "d", partition: "medieval-asia", joy: 200, calm: 0, stress: 0, gratitude: 0, focus: 0, mood: "m", summary: "" })).status).toBe("rejected");
      // unknown partition rejected (FK)
      expect((await recordJoucho(e, { assessmentId: "aY", actorDid: "d", partition: "no-such-partition", joy: 1, calm: 1, stress: 1, gratitude: 1, focus: 1, mood: "m", summary: "" })).status).toBe("rejected");
      const got = await getJoucho(e, { assessmentId: "a1" });
      expect(got.assessment?.actorDid).toBe("did:web:actor1");
      expect(got.assessment?.focus).toBe(70);
      expect(got.assessment?.summary).toBe("kyumei: gap in source provenance");
      await recordJoucho(e, { assessmentId: "a2", actorDid: "did:web:actor2", partition: "modern-europe", joy: 10, calm: 80, stress: 5, gratitude: 30, focus: 20, mood: "calm", summary: "stable" });
      expect((await listJoucho(e)).total).toBe(2);
      expect((await listJoucho(e, { partition: "medieval-asia" })).total).toBe(1);
      expect((await listJoucho(e, { mood: "calm" })).total).toBe(1);
    });

    it("enforces read-cap: a non-recipient DID cannot decrypt the assessment", async () => {
      await recordJoucho(e, { assessmentId: "a1", actorDid: "did:web:actor1", partition: "medieval-asia", joy: 60, calm: 40, stress: 20, gratitude: 50, focus: 70, mood: "focused", summary: "private" });
      // A distinct actor (no read-cap, separate PDS view) sees zero assessments.
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listJoucho(outsider)).total).toBe(0);
    });

    it("grants read-cap to an explicit recipient", async () => {
      const partner = "did:web:partner.example";
      const r = await recordJoucho(e, { assessmentId: "a1", actorDid: "did:web:actor1", partition: "medieval-asia", joy: 60, calm: 40, stress: 20, gratitude: 50, focus: 70, mood: "focused", summary: "shared", recipients: [partner] });
      expect(r.status).toBe("recorded");
      // owner can still read
      expect((await listJoucho(e)).total).toBe(1);
    });
  });

  describe("coverage rollup", () => {
    it("counts plaintext events + E2E joucho assessments by partition", async () => {
      await seedEvent(e, { eventId: "ev1", title: "A", partition: "medieval-asia", eventAt: "1200-01-01T00:00:00Z", propagationCount: 1 });
      await seedEvent(e, { eventId: "ev2", title: "B", partition: "medieval-asia", eventAt: "1300-01-01T00:00:00Z", propagationCount: 2 });
      await recordJoucho(e, { assessmentId: "a1", actorDid: "did:web:actor1", partition: "medieval-asia", joy: 1, calm: 1, stress: 1, gratitude: 1, focus: 1, mood: "neutral", summary: "" });
      const cov = await coverage(e);
      expect(cov.historicalEventCount).toBe(2);
      expect(cov.jouchoAssessmentCount).toBe(1);
      expect(cov.eventsByPartition?.["medieval-asia"]).toBe(2);
    });
  });
});
