/**
 * @etzhayyim/signal — Signal Protocol E2E primitives.
 *
 * Per ADR-2604261110, this is the SSoT for the CRITICAL `Signal Protocol E2E`
 * convention (replacing the pruned wproto signal module).
 */

export type {
  SignalIdentity,
  PreKeyBundle,
  SignalSession,
} from './signal.js';

export {
  hasIdentity,
  generateIdentity,
  loadIdentity,
  registerPreKeys,
  fetchPeerBundle,
  ensureSignalIdentity,
  isSignalEncrypted,
  isEncryptedVal,
  deriveFieldKey,
  encryptFieldVal,
  decryptFieldVal,
  clearSignalData,
  SIGNAL_CONTENT_TYPE,
  SIGNAL_MULTI_CONTENT_TYPE,
  SIGNAL_VAL_PREFIX,
} from './signal.js';

export {
  setSignalTransport,
  getSignalTransport,
  atpAgentTransport,
  type SignalTransport,
} from './transport.js';
