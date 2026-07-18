// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Gateway-layer in-memory WarifuSubstrate fake (ADR-2605302000). Implements the same surface as
// sdk.ts `WarifuSubstrate` so handlers can be tested end-to-end without a real @etzhayyim/sdk
// client. Mirrors the cells-layer InMemorySubstrate (orgs/etzhayyim/com-etzhayyim-warifu/cells/substrate.py); both
// stand in for kotoba EAVT + ERC-4337 in production. Fee is always 0; no key held.

export class MemorySubstrate {
  constructor({ phase2 = false } = {}) {
    this.phase2 = phase2;
    this.cards = {}; // token -> account
    this.bal = {}; // account -> USDC minor
    this.holds = {};
    this.settlements = {};
    this._n = 0;
    this.authorizeCalls = 0; // test observability
  }

  addCard(token, account, { balance = 0 } = {}) {
    this.cards[token] = account;
    this.bal[account] = balance;
    return this;
  }

  async phase2Enabled() {
    return this.phase2;
  }

  async authorize(input) {
    this.authorizeCalls++;
    const acct = this.cards[input.cardToken];
    if (!acct) return { decision: 'decline', feeUsdc: 0, reason: 'card not found' };
    if ((this.bal[acct] ?? 0) < input.amountUsdc) {
      return { decision: 'decline', feeUsdc: 0, reason: 'insufficient funds' };
    }
    const authId = `auth-${++this._n}`;
    this.holds[authId] = { acct, amount: input.amountUsdc, merchant: input.merchantDid, captured: 0 };
    return { decision: 'approve', authId, feeUsdc: 0 };
  }

  async settle({ authId }) {
    const h = this.holds[authId];
    if (!h) return { settled: false, feeUsdc: 0, finality: 'T+0' };
    this.bal[h.acct] -= h.amount;
    this.bal[h.merchant] = (this.bal[h.merchant] ?? 0) + h.amount;
    const sid = `settle-${++this._n}`;
    this.settlements[sid] = { ...h, refunded: 0 };
    return { settled: true, settlementId: sid, tx: `0xtx-${sid}`, feeUsdc: 0, finality: 'T+0' };
  }

  async refund({ settlementId, amountUsdc }) {
    const s = this.settlements[settlementId];
    if (!s) return { refunded: false, feeUsdc: 0, reason: 'settlement not found' };
    const remaining = s.amount - s.refunded;
    const amt = amountUsdc ?? remaining;
    if (amt <= 0 || amt > remaining) {
      return { refunded: false, feeUsdc: 0, reason: 'refund exceeds refundable amount' };
    }
    s.refunded += amt;
    this.bal[s.merchant] -= amt;
    this.bal[s.acct] += amt;
    const rid = `refund-${++this._n}`;
    return { refunded: true, refundId: rid, amountUsdc: amt, tx: `0xtx-${rid}`, feeUsdc: 0 };
  }
}
