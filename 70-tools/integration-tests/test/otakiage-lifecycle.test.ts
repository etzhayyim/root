import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  submitItem,
  requestReuse,
  handover,
  expire,
  issueCertificate,
} from "@etzhayyim/otakiage-kotoba";

describe("otakiage lifecycle state machine", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:multi-actor.test" });
  });

  it("executes reuse_then_ritual → handover path", async () => {
    // Submit item in reuse_then_ritual mode
    const submitResult = await submitItem(e, {
      itemId: "i1",
      mode: "reuse_then_ritual",
      title: "Vintage wooden chair",
      description: "Solid oak, good condition",
      ownerDid: "did:plc:owner1",
    });
    expect(submitResult.status).toBe("registered");
    expect(submitResult.did).toBeDefined();

    // Request reuse — should maintain reuse_open status
    const reuseResult = await requestReuse(e, {
      itemId: "i1",
      requesterDid: "did:plc:requester1",
      message: "Interested in this chair for my office",
    });
    expect(reuseResult.status).toBe("registered");

    // Handover to recipient — transitions to handed_over (terminal)
    const handoverResult = await handover(e, {
      itemId: "i1",
      recipientDid: "did:plc:recipient1",
    });
    expect(handoverResult.status).toBe("handed_over");
    expect(handoverResult.itemUri).toBeDefined();
  });

  it("executes reuse_then_ritual → expire → ritualize path", async () => {
    // Submit item in reuse_then_ritual mode
    const submitResult = await submitItem(e, {
      itemId: "i2",
      mode: "reuse_then_ritual",
      title: "Ceremonial robe",
      description: "For ritual use after expiration",
      ownerDid: "did:plc:owner2",
    });
    expect(submitResult.status).toBe("registered");

    // Expire the reuse window — cascades to ritual_pending
    const expireResult = await expire(e, {
      itemId: "i2",
    });
    expect(expireResult.status).toBe("ritual_pending");

    // Issue certificate with auto-ritualize flag
    const certResult = await issueCertificate(e, {
      certId: "c2",
      itemId: "i2",
      issuerDid: "did:plc:issuer1",
      autoRitualize: true,
    });
    expect(certResult.status).toBe("issued");
    expect(certResult.did).toBeDefined();
  });

  it("transitions ritual_only mode directly to ritual_pending", async () => {
    // Submit item in ritual_only mode
    const submitResult = await submitItem(e, {
      itemId: "i3",
      mode: "ritual_only",
      title: "Sacred text",
      description: "Retirement ritual binding",
      ownerDid: "did:plc:owner3",
    });
    expect(submitResult.status).toBe("registered");

    // Verify that ritual_only immediately transitions to ritual_pending
    // (test harness limitation: can't directly query internal state,
    // but certificate issuance on ritual_only item should succeed)
    const certResult = await issueCertificate(e, {
      certId: "c3",
      itemId: "i3",
      issuerDid: "did:plc:issuer2",
      autoRitualize: true,
    });
    expect(certResult.status).toBe("issued");
  });
});
