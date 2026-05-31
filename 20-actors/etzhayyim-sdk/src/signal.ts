import { randomBytes } from '@noble/hashes/utils';
import { xchacha20poly1305 } from '@noble/ciphers/chacha';

export type SessionHandle = string;

interface Session {
  sessionId: SessionHandle;
  key: Uint8Array;
  senderDid: string;
  recipientDid: string;
  createdAt: number;
}

// In-memory store for sessions. R1.0 stage.
const sessions = new Map<SessionHandle, Session>();

/**
 * Establishes a new cryptographic session for secure key wrapping.
 * R1.0: Generates a per-session symmetric key and stores it in-memory.
 *
 * @param args - The arguments for establishing the session.
 * @param args.senderDid - The DID of the message sender.
 * @param args.recipientDid - The DID of the message recipient.
 * @returns A handle to the established session.
 */
export const establishSession = (args: {
  senderDid: string;
  recipientDid: string;
}): SessionHandle => {
  const sessionId = `session_${Buffer.from(randomBytes(16)).toString('hex')}`;
  const session: Session = {
    sessionId,
    key: randomBytes(32), // 256-bit key for XChaCha20-Poly1305
    senderDid: args.senderDid,
    recipientDid: args.recipientDid,
    createdAt: Date.now(),
  };
  sessions.set(sessionId, session);
  return sessionId;
};

/**
 * Wraps a plaintext key using the established session's symmetric key.
 *
 * @param args - The arguments for wrapping the key.
 * @param args.session - The handle for the session to use.
 * @param args.plaintext - The plaintext to encrypt.
 * @returns An object containing the ciphertext and the session ID.
 * @throws if the session handle is invalid.
 */
export const wrapKey = (args: {
  session: SessionHandle;
  plaintext: string;
}): { ciphertext: Uint8Array; signalSessionId: string } => {
  const session = sessions.get(args.session);
  if (!session) {
    throw new Error('Invalid session handle');
  }

  const nonce = randomBytes(24); // 24-byte nonce for XChaCha20
  const plaintextBytes = new TextEncoder().encode(args.plaintext);

  const ciphertext = xchacha20poly1305(session.key, nonce).encrypt(
    plaintextBytes,
  );

  const finalCiphertext = new Uint8Array(nonce.length + ciphertext.length);
  finalCiphertext.set(nonce);
  finalCiphertext.set(ciphertext, nonce.length);

  return {
    ciphertext: finalCiphertext,
    signalSessionId: session.sessionId,
  };
};

/**
 * Unwraps a ciphertext to retrieve the original plaintext key.
 *
 * @param args - The arguments for unwrapping the key.
 * @param args.session - The handle for the session used for encryption.
 * @param args.ciphertext - The ciphertext to decrypt.
 * @returns The original plaintext.
 * @throws if the session handle is invalid or decryption fails (tag mismatch).
 */
export const unwrapKey = (args: {
  session: SessionHandle;
  ciphertext: Uint8Array;
}): string => {
  const session = sessions.get(args.session);
  if (!session) {
    throw new Error('Invalid session handle');
  }

  if (args.ciphertext.length < 24) {
    throw new Error('Invalid ciphertext: too short');
  }

  const nonce = args.ciphertext.slice(0, 24);
  const encryptedBody = args.ciphertext.slice(24);

  const decryptedBytes = xchacha20poly1305(session.key, nonce).decrypt(
    encryptedBody,
  );

  return new TextDecoder().decode(decryptedBytes);
};

// Test hook to clear sessions
export const _clearSessions = () => {
  sessions.clear();
}

