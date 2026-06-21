import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerPerson,
  getPerson,
  listPersons,
  addAppointment,
  endAppointment,
  listAppointments,
  coverage,
} from "../src/index.js";

const ENTITY = "did:web:legal-entity.etzhayyim.com:le:acme";

describe("business-person kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:business-person.etzhayyim.com" });
  });

  describe("person registry", () => {
    it("registers, reads, lists by role + app-layer search; idempotent; validates", async () => {
      expect((await registerPerson(e, { slug: "jane-doe", fullName: "Jane Doe", primaryRole: "ceo", nationality: "us", sourceUrl: "https://example.com" })).status).toBe("registered");
      expect((await getPerson(e, { slug: "jane-doe" })).person?.primaryRole).toBe("ceo");
      expect((await registerPerson(e, { slug: "jane-doe", fullName: "dup", primaryRole: "cfo" })).status).toBe("alreadyExists");
      await registerPerson(e, { slug: "john-roe", fullName: "John Roe", primaryRole: "director" });
      expect((await listPersons(e, { primaryRole: "ceo" })).total).toBe(1);
      expect((await listPersons(e, { q: "roe" })).total).toBe(1);
      expect((await listPersons(e, { nationality: "US" })).total).toBe(1);
      expect((await registerPerson(e, { slug: "Bad Slug!", fullName: "x", primaryRole: "ceo" })).status).toBe("rejected");
      expect((await registerPerson(e, { slug: "x", fullName: "y", primaryRole: "boss" as any })).status).toBe("rejected");
    });
  });

  describe("appointments", () => {
    beforeEach(async () => {
      await registerPerson(e, { slug: "jane-doe", fullName: "Jane Doe", primaryRole: "ceo" });
    });
    it("adds (FK→person), rejects missing person + bad entity DID; lists + ends", async () => {
      expect((await addAppointment(e, { appointmentId: "AP-1", personSlug: "jane-doe", entityDid: ENTITY, role: "ceo", startDate: "2020-01-01" })).status).toBe("added");
      expect((await getAppt(e, "jane-doe")).total).toBe(1);
      expect((await addAppointment(e, { appointmentId: "AP-X", personSlug: "ghost", entityDid: ENTITY, role: "director" })).status).toBe("personNotFound");
      expect((await addAppointment(e, { appointmentId: "AP-Y", personSlug: "jane-doe", entityDid: "not-a-did", role: "director" })).status).toBe("rejected");
      // current defaults true when no endDate
      expect((await listAppointments(e, { personSlug: "jane-doe", current: true })).total).toBe(1);
      expect((await endAppointment(e, { appointmentId: "AP-1", endDate: "2026-01-01" })).status).toBe("ended");
      expect((await listAppointments(e, { current: true })).total).toBe(0);
      expect((await endAppointment(e, { appointmentId: "AP-1", endDate: "2026-02-01" })).status).toBe("rejected"); // already ended
    });
    it("coverage rolls up persons + appointments", async () => {
      await addAppointment(e, { appointmentId: "AP-1", personSlug: "jane-doe", entityDid: ENTITY, role: "ceo" });
      const cov = await coverage(e);
      expect(cov.personCount).toBe(1);
      expect(cov.appointmentCount).toBe(1);
      expect(cov.personsByRole?.ceo).toBe(1);
      expect(cov.currentAppointments).toBe(1);
    });
  });
});

async function getAppt(e: any, personSlug: string) {
  return listAppointments(e, { personSlug });
}
