import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  defineEntity,
  getEntity,
  listEntities,
  archiveEntity,
  recordEvent,
  listEvents,
  submitReport,
  publishReport,
  listReports,
  coverage,
} from "../src/index.js";

describe("kyber-qzzg06nh rw-free", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:kyber-qzzg06nh.etzhayyim.com" });
  });

  describe("entity graph", () => {
    it("defines, reads, lists by kind + search, archives", async () => {
      expect((await defineEntity(e, { entityId: "EN-1", name: "Procure-to-Pay", kind: "process", category: "apqc" })).status).toBe("defined");
      expect((await getEntity(e, { entityId: "EN-1" })).entity?.status).toBe("active");
      await defineEntity(e, { entityId: "EN-2", name: "Vendor", kind: "actor" });
      expect((await listEntities(e, { kind: "process" })).total).toBe(1);
      expect((await listEntities(e, { q: "procure" })).total).toBe(1);
      expect((await defineEntity(e, { entityId: "EN-1", name: "dup", kind: "process" })).status).toBe("alreadyExists");
      expect((await defineEntity(e, { entityId: "EN-X", name: "", kind: "x" })).status).toBe("rejected");
      expect((await archiveEntity(e, { entityId: "EN-1" })).status).toBe("archived");
      expect((await listEntities(e, { status: "active" })).total).toBe(1);
      expect((await archiveEntity(e, { entityId: "EN-1" })).status).toBe("rejected");
    });
  });

  describe("events + reports against an entity", () => {
    beforeEach(async () => {
      await defineEntity(e, { entityId: "EN-1", name: "Procure-to-Pay", kind: "process" });
    });
    it("records events (FK), rejects missing entity; filters", async () => {
      expect((await recordEvent(e, { eventId: "EV-1", entityId: "EN-1", eventType: "executed", occurredAt: "2026-06-01T00:00:00Z" })).status).toBe("recorded");
      expect((await recordEvent(e, { eventId: "EV-X", entityId: "GHOST", eventType: "x", occurredAt: "x" })).status).toBe("entityNotFound");
      await recordEvent(e, { eventId: "EV-2", entityId: "EN-1", eventType: "failed", occurredAt: "2026-06-05T00:00:00Z" });
      expect((await listEvents(e, { entityId: "EN-1", eventType: "failed" })).total).toBe(1);
      expect((await listEvents(e, { since: "2026-06-03T00:00:00Z" })).total).toBe(1);
    });
    it("submits + publishes reports (optional FK), guards republish; coverage", async () => {
      expect((await submitReport(e, { reportId: "R-1", reportType: "process-review", title: "P2P Review", entityId: "EN-1" })).status).toBe("submitted");
      expect((await submitReport(e, { reportId: "R-2", reportType: "summary", title: "Q2" })).status).toBe("submitted");
      expect((await submitReport(e, { reportId: "R-X", reportType: "x", title: "y", entityId: "GHOST" })).status).toBe("entityNotFound");
      expect((await publishReport(e, { reportId: "R-1" })).newStatus).toBe("published");
      expect((await publishReport(e, { reportId: "R-1" })).status).toBe("rejected");
      expect((await listReports(e, { status: "published" })).total).toBe(1);
      await recordEvent(e, { eventId: "EV-1", entityId: "EN-1", eventType: "executed", occurredAt: "2026-06-01T00:00:00Z" });
      const cov = await coverage(e);
      expect(cov.entityCount).toBe(1);
      expect(cov.eventCount).toBe(1);
      expect(cov.reportCount).toBe(2);
      expect(cov.entitiesByKind?.process).toBe(1);
      expect(cov.reportsByStatus?.published).toBe(1);
    });
  });
});
