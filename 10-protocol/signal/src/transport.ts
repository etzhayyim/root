/**
 * Transport injection for @etzhayyim/signal.
 *
 * Per ADR-2604261110, this package does not depend on @etzhayyim/wproto. The caller
 * wires an XRPC dispatcher (typically a thin wrapper over `@atproto/api`'s
 * AtpAgent) and the Signal client uses it for the two server calls it needs:
 *   - com.etzhayyim.signal.registerPrekeys (procedure, body)
 *   - com.etzhayyim.signal.getPrekeyBundle (query, params)
 *
 * Single global slot is intentional: Signal identity is per-user, and the
 * browser session has exactly one. Tests can reset by calling
 * `setSignalTransport(null)`.
 */

export interface SignalTransport {
  /** AT Protocol XRPC procedure (POST). */
  procedure<T = unknown>(nsid: string, body: unknown): Promise<T>;
  /** AT Protocol XRPC query (GET). */
  query<T = unknown>(nsid: string, params: Record<string, unknown>): Promise<T>;
}

let _transport: SignalTransport | null = null;

export function setSignalTransport(transport: SignalTransport | null): void {
  _transport = transport;
}

export function getSignalTransport(): SignalTransport {
  if (!_transport) {
    throw new Error(
      '@etzhayyim/signal: transport not configured. Call setSignalTransport(...) at app startup.',
    );
  }
  return _transport;
}

/**
 * Convenience adapter for @atproto/api AtpAgent. Caller passes a function that
 * returns the agent (allowing late-binding / re-login flows).
 *
 * Usage:
 *   import { AtpAgent } from '@atproto/api';
 *   import { setSignalTransport, atpAgentTransport } from '@etzhayyim/signal';
 *   const agent = new AtpAgent({ service: '...' });
 *   setSignalTransport(atpAgentTransport(() => agent));
 */
export function atpAgentTransport(
  getAgent: () => { call: (nsid: string, params?: unknown, body?: unknown) => Promise<{ data: unknown }> },
): SignalTransport {
  return {
    async procedure<T>(nsid: string, body: unknown): Promise<T> {
      const res = await getAgent().call(nsid, undefined, body);
      return res.data as T;
    },
    async query<T>(nsid: string, params: Record<string, unknown>): Promise<T> {
      const res = await getAgent().call(nsid, params, undefined);
      return res.data as T;
    },
  };
}
