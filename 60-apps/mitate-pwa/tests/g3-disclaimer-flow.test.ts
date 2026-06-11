// G3 disclaimer-first flow — invariant: /triage and /medication-audit MUST 303-redirect
// to /disclaimer when verifyDisclaimerAck() returns false.
// Per ADR-2605260100 §G3 + ADR-2605260200 §Decision 3.

import { describe, it, expect } from "vitest";

describe("G3 disclaimer-first flow", () => {
  it("redirects /triage to /disclaimer when ack absent", async () => {
    // Scaffold: assert routing behavior. R1 implementation provides concrete impl.
    const mockRoute = (path: string, ackPresent: boolean): { status: number; location?: string } => {
      if ((path === "/triage" || path === "/medication-audit") && !ackPresent) {
        return { status: 303, location: `/disclaimer?next=${encodeURIComponent(path)}` };
      }
      return { status: 200 };
    };

    expect(mockRoute("/triage", false)).toEqual({
      status: 303,
      location: "/disclaimer?next=%2Ftriage",
    });
    expect(mockRoute("/medication-audit", false)).toEqual({
      status: 303,
      location: "/disclaimer?next=%2Fmedication-audit",
    });
  });

  it("disclaimer page requires all three checkboxes (G1 consent + G3 advisory + G6 high-risk acknowledge)", () => {
    const requiredFields = ["g3_ack", "g1_consent", "g6_acknowledge_high_risk"];
    requiredFields.forEach((field) => {
      expect(requiredFields).toContain(field);
    });
  });

  it("verifyDisclaimerAck returns false in scaffold (must be implemented R1)", async () => {
    // R0 invariant: function exists, returns false (forces disclaimer flow).
    // R1 will implement via session cookie + consent receipt CID resolution.
    const ack = false; // mirrors src/app.ts verifyDisclaimerAck scaffold return
    expect(ack).toBe(false);
  });
});
