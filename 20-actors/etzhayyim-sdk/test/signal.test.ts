/**
 * Unit tests for `@etzhayyim/sdk/signal` — real libsignal round-trip.
 *
 * Two-party (Alice → Bob) wrap/unwrap. Verifies that:
 *   - generateLocalIdentity produces a publishable bundle with the right
 *     fields,
 *   - establishSession + wrapKey from Alice produces a PreKey-type
 *     CiphertextMessage on first contact,
 *   - Bob can decrypt it back to the original symmetric key,
 *   - subsequent messages flip to Whisper type,
 *   - the deterministic sessionIdOf matches both directions of computation.
 */

import {describe, it, expect, beforeAll} from "vitest";
import {
  establishSession,
  generateLocalIdentity,
  sessionIdOf,
  unwrapKey,
  wrapKey,
  type LocalIdentityBundle,
} from "../src/signal.js";

describe("signal — libsignal round-trip (Alice → Bob)", () => {
  const ALICE = "did:test:alice";
  const BOB = "did:test:bob";

  let alice: LocalIdentityBundle;
  let bob: LocalIdentityBundle;

  beforeAll(async () => {
    alice = await generateLocalIdentity({signedPreKeyId: 1});
    bob = await generateLocalIdentity({signedPreKeyId: 1});
  });

  it("generateLocalIdentity yields the publishable bundle shape", () => {
    expect(alice.publishable.signalIdentityKey).toBeInstanceOf(Uint8Array);
    expect(alice.publishable.signalIdentityKey.length).toBeGreaterThan(0);
    expect(alice.publishable.signalRegistrationId).toBeGreaterThanOrEqual(1);
    expect(alice.publishable.signalRegistrationId).toBeLessThan(1 << 14);
    expect(alice.publishable.signedPreKey).toBeInstanceOf(Uint8Array);
    expect(alice.publishable.signedPreKeyId).toBe(1);
    expect(alice.publishable.signedPreKeySignature).toBeInstanceOf(Uint8Array);
  });

  it("sessionIdOf is deterministic and direction-sensitive", () => {
    expect(sessionIdOf(ALICE, BOB)).toBe(sessionIdOf(ALICE, BOB));
    expect(sessionIdOf(ALICE, BOB)).not.toBe(sessionIdOf(BOB, ALICE));
    expect(sessionIdOf(ALICE, BOB).length).toBe(32);
  });

  it("Alice wraps a symmetric key that Bob unwraps to the same bytes", async () => {
    const aliceToBob = await establishSession({
      senderDid: ALICE,
      recipientDid: BOB,
      recipientIdentity: bob.publishable,
      senderStores: alice.stores,
    });
    expect(aliceToBob.sessionId).toBe(sessionIdOf(ALICE, BOB));

    const symKey = new Uint8Array(32);
    for (let i = 0; i < 32; i++) symKey[i] = i;

    const wrapped = await wrapKey({
      session: aliceToBob,
      symmetricKey: symKey,
      senderStores: alice.stores,
    });
    expect(wrapped.ciphertext.length).toBeGreaterThan(32); // libsignal envelope > raw key
    expect(wrapped.signalSessionId).toBe(aliceToBob.sessionId);
    // First send is PreKey (type 3) because Bob's session hasn't bootstrapped yet.
    expect(wrapped.messageType).toBe(3);

    // Bob's view of the session is the reverse direction.
    const bobReceives = {
      sessionId: sessionIdOf(ALICE, BOB),
      senderDid: ALICE,
      recipientDid: BOB,
    };
    const unwrapped = await unwrapKey({
      session: bobReceives,
      ciphertext: wrapped.ciphertext,
      messageType: wrapped.messageType,
      recipientStores: bob.stores,
    });
    expect(Array.from(unwrapped)).toEqual(Array.from(symKey));
  });

  it("second send Alice → Bob still round-trips (one-way PreKey stays type 3)", async () => {
    // In the Signal protocol the sender keeps sending PreKey-type messages
    // until the recipient replies (otherwise the sender cannot be sure the
    // recipient has the session). Once Bob replies once, Alice's next
    // sends would be Whisper. For one-way key-wrap delivery (our use case
    // — recipients enumerate keyWraps in their own PDS, they don't write
    // back) every send remains type 3, which is fine.
    const session = {
      sessionId: sessionIdOf(ALICE, BOB),
      senderDid: ALICE,
      recipientDid: BOB,
    };
    const symKey2 = new Uint8Array(32).fill(0xaa);

    const wrapped = await wrapKey({
      session,
      symmetricKey: symKey2,
      senderStores: alice.stores,
    });
    expect(wrapped.messageType).toBe(3);

    const unwrapped = await unwrapKey({
      session,
      ciphertext: wrapped.ciphertext,
      messageType: wrapped.messageType,
      recipientStores: bob.stores,
    });
    expect(Array.from(unwrapped)).toEqual(Array.from(symKey2));
  });

  it("Whisper round-trip after Bob ratchets back", async () => {
    // Bob now sends a PreKey-back to Alice to ratchet the session. Alice's
    // subsequent send to Bob should switch to Whisper (type 2).
    const bobToAlice = await establishSession({
      senderDid: BOB,
      recipientDid: ALICE,
      recipientIdentity: alice.publishable,
      senderStores: bob.stores,
    });
    const bobReply = await wrapKey({
      session: bobToAlice,
      symmetricKey: new Uint8Array(32).fill(0x42),
      senderStores: bob.stores,
    });
    await unwrapKey({
      session: {
        sessionId: sessionIdOf(BOB, ALICE),
        senderDid: BOB,
        recipientDid: ALICE,
      },
      ciphertext: bobReply.ciphertext,
      messageType: bobReply.messageType,
      recipientStores: alice.stores,
    });

    // Now Alice → Bob ratchets to Whisper.
    const aliceAgain = await wrapKey({
      session: {
        sessionId: sessionIdOf(ALICE, BOB),
        senderDid: ALICE,
        recipientDid: BOB,
      },
      symmetricKey: new Uint8Array(32).fill(0xbb),
      senderStores: alice.stores,
    });
    expect(aliceAgain.messageType).toBe(2);
    const unwrapped = await unwrapKey({
      session: {
        sessionId: sessionIdOf(ALICE, BOB),
        senderDid: ALICE,
        recipientDid: BOB,
      },
      ciphertext: aliceAgain.ciphertext,
      messageType: aliceAgain.messageType,
      recipientStores: bob.stores,
    });
    expect(Array.from(unwrapped)).toEqual(
      Array.from(new Uint8Array(32).fill(0xbb))
    );
  });

  it("rejects establishSession when recipientIdentity is missing signed prekey", async () => {
    await expect(
      establishSession({
        senderDid: ALICE,
        recipientDid: "did:test:carol",
        recipientIdentity: {
          signalIdentityKey: new Uint8Array(32),
          signalRegistrationId: 42,
          // signedPreKey omitted on purpose
        },
        senderStores: alice.stores,
      })
    ).rejects.toThrow(/signedPreKey/);
  });
});
