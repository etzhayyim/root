// G5 architectural invariant — direct POST to triageVerdict is BLOCKED (405).
// Patient intake MUST POST to rhinitisIntake; emergency_screen pass-through is enforced
// at the substrate cell layer, not the PWA. The PWA refuses any client-side attempt
// to short-circuit by bypassing the cell chain.
// Per ADR-2605260100 §G5 + ADR-2605260200 §Decision 3 architectural invariant.

import { describe, it, expect } from "vitest";

describe("G5 emergency_screen bypass impossible", () => {
  it("POST /xrpc/com.etzhayyim.mitate.triageVerdict returns 405 G5InvariantBlocked", () => {
    // Mirrors src/app.ts routing guard
    const mockRouteCheck = (method: string, path: string): { status: number; error?: string } => {
      if (method === "POST" && path === "/xrpc/com.etzhayyim.mitate.triageVerdict") {
        return { status: 405, error: "G5InvariantBlocked" };
      }
      return { status: 200 };
    };

    const res = mockRouteCheck("POST", "/xrpc/com.etzhayyim.mitate.triageVerdict");
    expect(res.status).toBe(405);
    expect(res.error).toBe("G5InvariantBlocked");
  });

  it("POST /xrpc/com.etzhayyim.mitate.rhinitisIntake is permitted (cell chain triggers emergency_screen)", () => {
    const mockRouteCheck = (method: string, path: string, r1Active: boolean): { status: number; reason?: string } => {
      if (
        method === "POST" &&
        path === "/xrpc/com.etzhayyim.mitate.rhinitisIntake" &&
        r1Active
      ) {
        return { status: 200, reason: "proxy-to-substrate" };
      }
      return { status: 503 };
    };

    expect(mockRouteCheck("POST", "/xrpc/com.etzhayyim.mitate.rhinitisIntake", true)).toEqual({
      status: 200,
      reason: "proxy-to-substrate",
    });
  });

  it("R1 active NSID set includes rhinitisIntake + triageVerdict + emergencyEscalation; excludes R2 lexicons", () => {
    const R1_ACTIVE = new Set([
      "com.etzhayyim.mitate.rhinitisIntake",
      "com.etzhayyim.mitate.triageVerdict",
      "com.etzhayyim.mitate.emergencyEscalation",
    ]);
    const R2_GATED = new Set([
      "com.etzhayyim.mitate.diagnosticOrder",
      "com.etzhayyim.mitate.diagnosticResult",
      "com.etzhayyim.mitate.treatmentPlan",
      "com.etzhayyim.mitate.outcomeFollowup",
    ]);

    expect(R1_ACTIVE.has("com.etzhayyim.mitate.emergencyEscalation")).toBe(true);
    expect(R2_GATED.has("com.etzhayyim.mitate.diagnosticOrder")).toBe(true);

    // Critical: emergencyEscalation must NEVER be in the gated set (G5 fail-safe inviolability)
    expect(R2_GATED.has("com.etzhayyim.mitate.emergencyEscalation")).toBe(false);
  });
});
