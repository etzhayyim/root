/**
 * Unit tests for `@etzhayyim/sdk/signal` (scaffold).
 *
 * Scope: shape of the public API — the v0.0.0 scaffold throws
 * "not yet implemented" for everything that requires libsignal, so these
 * tests pin the surface and the expected error messages.
 *
 * Real round-trip tests land alongside the libsignal-backed implementation.
 */

import {describe, it, expect} from "vitest";
import {
  establishSession,
  generateLocalIdentity,
  unwrapKey,
  wrapKey,
} from "../src/signal.js";

describe("signal module scaffold", () => {
  it("establishSession is a function and throws not-yet-implemented", async () => {
    await expect(
      establishSession({
        senderDid: "did:web:alice.example",
        recipientDid: "did:web:bob.example",
        recipientIdentity: {
          signalIdentityKey: new Uint8Array(32),
          signalRegistrationId: 1,
        },
      })
    ).rejects.toThrow(/not yet implemented/);
  });

  it("wrapKey throws not-yet-implemented", async () => {
    await expect(
      wrapKey({
        session: {
          sessionId: "s1",
          senderDid: "did:web:alice.example",
          recipientDid: "did:web:bob.example",
        },
        symmetricKey: new Uint8Array(32),
      })
    ).rejects.toThrow(/not yet implemented/);
  });

  it("unwrapKey throws not-yet-implemented", async () => {
    await expect(
      unwrapKey({
        session: {
          sessionId: "s1",
          senderDid: "did:web:alice.example",
          recipientDid: "did:web:bob.example",
        },
        ciphertext: new Uint8Array([1, 2, 3]),
      })
    ).rejects.toThrow(/not yet implemented/);
  });

  it("generateLocalIdentity throws not-yet-implemented", async () => {
    await expect(generateLocalIdentity()).rejects.toThrow(
      /not yet implemented/
    );
  });
});
