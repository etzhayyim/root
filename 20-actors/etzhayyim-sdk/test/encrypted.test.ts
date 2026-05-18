/**
 * Integration tests for `@etzhayyim/sdk/encrypted` — full Tahoe-pattern
 * round-trip on the in-memory fake PDS.
 *
 * Topology:
 *
 *   Alice (sender)  ──encryptedWriteStandalone──▶  fake-pds (single repo:
 *                                                  records keyed by repo DID)
 *                                                          │
 *   Bob (recipient) ◀──encryptedReadStandalone────────────┘
 *
 * The DID-binding verification path is exercised against a deterministic
 * Ed25519 keypair we control. The recipient identity resolver enumerates
 * `app.etzhayyim.encrypted.signalIdentity` from the recipient's fake-PDS
 * repo and returns the publishable bundle + the verification key.
 */

import {describe, it, expect, beforeAll, afterAll} from "vitest";
// @ts-expect-error — fake-pds is JS, no .d.ts
import {startFakePds} from "./fake-pds.mjs";
import {AtpAgent} from "@atproto/api";
import {ed25519} from "@noble/curves/ed25519";

import {
  signSignalIdentity,
  type SignedSignalIdentity,
} from "../src/did-signal.js";
import {
  generateLocalIdentity,
  type LocalIdentityBundle,
} from "../src/signal.js";
import {
  encryptedReadStandalone,
  encryptedWriteStandalone,
  publishSignalIdentity,
  type ResolvedRecipientIdentity,
} from "../src/encrypted.js";

// ── Test rig ─────────────────────────────────────────────────────────────────

const ALICE_DID = "did:test:alice";
const BOB_DID = "did:test:bob";

interface Actor {
  did: string;
  identity: LocalIdentityBundle;
  didSigningKey: Uint8Array;
  didVerificationKey: Uint8Array;
  signed: SignedSignalIdentity;
}

async function makeActor(did: string): Promise<Actor> {
  const identity = await generateLocalIdentity({signedPreKeyId: 1});

  // Generate a separate Ed25519 keypair that "represents" the actor's DID
  // signing key. In production this would be resolved from the DID document.
  const didSigningKey = ed25519.utils.randomPrivateKey();
  const didVerificationKey = ed25519.getPublicKey(didSigningKey);

  // Sign the publishable Signal identity with the DID key (binding).
  const signed = signSignalIdentity(
    {
      did,
      signalIdentityKey: identity.publishable.signalIdentityKey,
      signalRegistrationId: identity.publishable.signalRegistrationId,
      signedPreKey: identity.publishable.signedPreKey,
      signedPreKeyId: identity.publishable.signedPreKeyId,
      signedPreKeySignature: identity.publishable.signedPreKeySignature,
      createdAt: new Date().toISOString(),
    },
    didSigningKey
  );

  return {did, identity, didSigningKey, didVerificationKey, signed};
}

describe("encrypted — full encryptedWrite → encryptedRead round-trip", () => {
  let pds: Awaited<ReturnType<typeof startFakePds>>;
  let agent: AtpAgent;
  let alice: Actor;
  let bob: Actor;

  beforeAll(async () => {
    // fake-pds claims a single sessionDid; we send writes with arbitrary
    // `repo` values, so it functions as a multi-DID store in practice.
    pds = await startFakePds({sessionDid: ALICE_DID, sessionHandle: "alice.test"});
    agent = new AtpAgent({service: pds.url});
    await agent.resumeSession({
      did: ALICE_DID,
      handle: "alice.test",
      accessJwt: "stub",
      refreshJwt: "stub",
      active: true,
    });

    alice = await makeActor(ALICE_DID);
    bob = await makeActor(BOB_DID);

    // Both actors publish their signed signalIdentity record to their own
    // PDS repo so the recipient resolver can pick it up.
    await publishSignalIdentity({agent, selfDid: ALICE_DID, signed: alice.signed});
    await publishSignalIdentity({agent, selfDid: BOB_DID, signed: bob.signed});
  });

  afterAll(async () => {
    await pds.stop();
  });

  // ── Resolver that drives encryptedWrite ────────────────────────────────────

  function makeResolver(actors: Actor[]) {
    return async (
      recipientDid: string
    ): Promise<ResolvedRecipientIdentity | null> => {
      const actor = actors.find((a) => a.did === recipientDid);
      if (!actor) return null;
      return {
        publishable: actor.identity.publishable,
        signed: actor.signed,
        didVerificationKey: actor.didVerificationKey,
      };
    };
  }

  // ── Tests ──────────────────────────────────────────────────────────────────

  it("Alice encrypts a record for Bob → Bob decrypts back to the original", async () => {
    const plaintext = {
      title: "council deliberation #1",
      body: "merge motion for ADR-2605181100 reference impl",
      authorDid: ALICE_DID,
    };

    const writeReceipt = await encryptedWriteStandalone(
      {
        agent,
        senderDid: ALICE_DID,
        senderStores: alice.identity.stores,
        resolveRecipientIdentity: makeResolver([alice, bob]),
      },
      {
        record: plaintext,
        innerType: "app.etzhayyim.governance.proposal",
        recipients: [BOB_DID],
      }
    );

    expect(writeReceipt.uri).toMatch(
      /^at:\/\/did:test:alice\/app\.etzhayyim\.encrypted\.record\//
    );
    expect(writeReceipt.keyWraps).toHaveLength(2); // Bob + self (wrapToSelf default)
    expect(writeReceipt.skipped).toEqual([]);

    // Bob enumerates keyWraps from Alice's PDS (where the sender writes
    // them) and filters by recipient == bob. Atproto repos are
    // single-writer; cross-PDS keyWrap distribution is a sender-poll model.
    const readResp = await encryptedReadStandalone<typeof plaintext>(
      {
        agent,
        selfDid: BOB_DID,
        selfStores: bob.identity.stores,
      },
      {
        innerType: "app.etzhayyim.governance.proposal",
        fromSenders: [ALICE_DID],
      }
    );

    expect(readResp.failed).toEqual([]);
    expect(readResp.records).toHaveLength(1);
    expect(readResp.records[0].value).toEqual(plaintext);
    expect(readResp.records[0].sender).toBe(ALICE_DID);
  });

  it("Bob can encrypt a reply for Alice (symmetric DM flow)", async () => {
    // wrapToSelf=false so Bob's own store doesn't get tangled — single-store
    // self-wrap is a known degenerate case for libsignal (sessions have a
    // direction; reusing the same store for sender + recipient roles breaks
    // session state). Multi-device self-wrap works in practice because
    // each device gets its own identity store; tests here use one store
    // per actor for simplicity.
    const plaintext = {
      ref: "council deliberation #1",
      vote: "approve",
      voterDid: BOB_DID,
    };
    const writeReceipt = await encryptedWriteStandalone(
      {
        agent,
        senderDid: BOB_DID,
        senderStores: bob.identity.stores,
        resolveRecipientIdentity: makeResolver([alice, bob]),
      },
      {
        record: plaintext,
        innerType: "app.etzhayyim.governance.vote",
        recipients: [ALICE_DID],
        wrapToSelf: false,
      }
    );
    expect(writeReceipt.skipped).toEqual([]);
    expect(writeReceipt.keyWraps).toHaveLength(1);

    const readResp = await encryptedReadStandalone<typeof plaintext>(
      {
        agent,
        selfDid: ALICE_DID,
        selfStores: alice.identity.stores,
      },
      {
        innerType: "app.etzhayyim.governance.vote",
        fromSenders: [BOB_DID],
      }
    );
    expect(readResp.failed).toEqual([]);
    expect(readResp.records).toHaveLength(1);
    expect(readResp.records[0].value).toEqual(plaintext);
    expect(readResp.records[0].sender).toBe(BOB_DID);
  });

  it("skips a recipient whose DID-binding signature fails to verify", async () => {
    // Carol's signalIdentity is signed with a key that does NOT match the
    // verification key we declare. encryptedWrite must skip her.
    const carolDid = "did:test:carol";
    const carolIdentity = await generateLocalIdentity({signedPreKeyId: 1});
    const carolWrongSigningKey = ed25519.utils.randomPrivateKey();
    const carolFakeVerificationKey = ed25519.getPublicKey(
      ed25519.utils.randomPrivateKey()
    ); // unrelated to the actual signing key
    const carolSigned = signSignalIdentity(
      {
        did: carolDid,
        signalIdentityKey: carolIdentity.publishable.signalIdentityKey,
        signalRegistrationId: carolIdentity.publishable.signalRegistrationId,
        signedPreKey: carolIdentity.publishable.signedPreKey,
        signedPreKeyId: carolIdentity.publishable.signedPreKeyId,
        signedPreKeySignature: carolIdentity.publishable.signedPreKeySignature,
        createdAt: new Date().toISOString(),
      },
      carolWrongSigningKey
    );

    const resolverWithBadCarol = async (
      recipientDid: string
    ): Promise<ResolvedRecipientIdentity | null> => {
      if (recipientDid === BOB_DID) {
        return {
          publishable: bob.identity.publishable,
          signed: bob.signed,
          didVerificationKey: bob.didVerificationKey,
        };
      }
      if (recipientDid === ALICE_DID) {
        return {
          publishable: alice.identity.publishable,
          signed: alice.signed,
          didVerificationKey: alice.didVerificationKey,
        };
      }
      if (recipientDid === carolDid) {
        return {
          publishable: carolIdentity.publishable,
          signed: carolSigned,
          didVerificationKey: carolFakeVerificationKey,
        };
      }
      return null;
    };

    const receipt = await encryptedWriteStandalone(
      {
        agent,
        senderDid: ALICE_DID,
        senderStores: alice.identity.stores,
        resolveRecipientIdentity: resolverWithBadCarol,
      },
      {
        record: {x: 1},
        recipients: [BOB_DID, carolDid],
      }
    );

    expect(receipt.skipped).toHaveLength(1);
    expect(receipt.skipped[0].recipient).toBe(carolDid);
    expect(receipt.skipped[0].reason).toMatch(/DID-binding/);
    // Bob got his keyWrap; self-wrap also.
    expect(receipt.keyWraps.map((w) => w.recipient).sort()).toEqual(
      [ALICE_DID, BOB_DID].sort()
    );
  });

  it("skips a recipient whose signalIdentity is not resolvable", async () => {
    const ghostDid = "did:test:ghost";
    const receipt = await encryptedWriteStandalone(
      {
        agent,
        senderDid: ALICE_DID,
        senderStores: alice.identity.stores,
        resolveRecipientIdentity: makeResolver([alice, bob]),
      },
      {
        record: {hello: "world"},
        recipients: [ghostDid],
      }
    );
    expect(receipt.skipped).toHaveLength(1);
    expect(receipt.skipped[0].recipient).toBe(ghostDid);
    expect(receipt.skipped[0].reason).toMatch(/no.*signalIdentity/);
  });
});
