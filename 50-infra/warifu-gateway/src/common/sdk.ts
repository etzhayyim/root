// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Substrate facade. Per the substrate boundary (repo CLAUDE.md), the gateway may reach the
// substrate ONLY via `@etzhayyim/sdk` — never `@atproto/api` / `viem` / IPFS clients directly.
// Per the server-side-signing invariant (ADR-2605231525) the gateway holds NO private key:
// cardholder authorization rides on the passkey assertion / smart-account session passed in.
//
// R0 stub: the real client is wired in R1. These methods declare the call surface only.

import type {
  CardAuthorizeInput,
  CardAuthorizeOutput,
  CardSettleInput,
  CardSettleOutput,
  CardRefundInput,
  CardRefundOutput,
} from './types.js';

/** Thin typed wrapper over the `com.etzhayyim.card.*` lexicon procedures. */
export interface WarifuSubstrate {
  /** Phase 2 (external purchase/subscription) gate — read from on-chain SettlementRouter. */
  phase2Enabled(): Promise<boolean>;
  authorize(input: CardAuthorizeInput): Promise<CardAuthorizeOutput>;
  settle(input: CardSettleInput): Promise<CardSettleOutput>;
  refund(input: CardRefundInput): Promise<CardRefundOutput>;
}

/**
 * R0 placeholder. Throws on use so a forgotten wiring fails loudly rather than silently
 * settling. Replace with the `@etzhayyim/sdk`-backed client in R1.
 */
export function createSubstrateStub(): WarifuSubstrate {
  const notWired = (m: string) => {
    throw new Error(`warifu-gateway R0: substrate '${m}' not wired — inject @etzhayyim/sdk client`);
  };
  return {
    async phase2Enabled() {
      // Default-closed: until the on-chain read is wired, external purposes stay gated.
      return false;
    },
    async authorize() {
      return notWired('authorize');
    },
    async settle() {
      return notWired('settle');
    },
    async refund() {
      return notWired('refund');
    },
  };
}
