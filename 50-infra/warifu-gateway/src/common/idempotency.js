// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Idempotency layer — anti-double-charge for all 3 surfaces (ADR-2605302000). An authorize/settle
// MUST NOT execute twice for the same idempotency key (Stripe Idempotency-Key / ISO 8583 STAN /
// NFC tap correlation). Replaying a completed key returns the SAME stored result; replaying an
// in-flight key is refused; a failed attempt clears the key so the caller may retry.
//
// Plain ESM (JSDoc-typed): runnable by node (tests) AND importable by the TypeScript handlers.
// R0 uses an in-memory store; R1 backs it with kotoba (the idempotency record is itself an EAVT
// fact keyed by the idempotency key, so dedupe survives process restarts).

/** @typedef {{status:'inflight'} | {status:'done', result:any}} IdemEntry */

export class InMemoryIdempotencyStore {
  constructor() {
    /** @type {Map<string, IdemEntry>} */
    this.m = new Map();
  }
  /** @param {string} key @returns {IdemEntry|undefined} */
  get(key) {
    return this.m.get(key);
  }
  /** @param {string} key */
  begin(key) {
    this.m.set(key, { status: 'inflight' });
  }
  /** @param {string} key @param {any} result */
  complete(key, result) {
    this.m.set(key, { status: 'done', result });
  }
  /** @param {string} key — clear so a failed attempt can be retried */
  fail(key) {
    this.m.delete(key);
  }
}

/**
 * Run `fn` at most once per `key`. Returns the cached result on replay of a completed key.
 * @template T
 * @param {{get:Function, begin:Function, complete:Function, fail:Function}} store
 * @param {string} key
 * @param {() => Promise<T>} fn
 * @returns {Promise<T>}
 */
export async function withIdempotency(store, key, fn) {
  if (!key) throw new Error('idempotency: key required');
  const existing = store.get(key);
  if (existing) {
    if (existing.status === 'done') return existing.result;
    throw new Error('idempotency: a request with this key is already in flight');
  }
  store.begin(key);
  try {
    const result = await fn();
    store.complete(key, result);
    return result;
  } catch (e) {
    store.fail(key); // allow retry on transient failure — money never moved
    throw e;
  }
}
