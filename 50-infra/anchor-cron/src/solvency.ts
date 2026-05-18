/**
 * Solvency monitoring for the anchor-cron signer account.
 *
 * Stage 4 of ADR-2605171800 spends gas every time anchor-cron runs. The
 * signer is a separately-funded EOA (per README §Solvency). This module
 * reads the signer balance from the L2 RPC each tick and emits a
 * structured warning to stderr when the balance dips below a configured
 * floor — typically "7 days of operation" worth of gas headroom.
 *
 * The warning shape (single line, `[anchor-cron] solvency: ...`) is
 * intended to be parsed by the cluster's log-shipping pipeline /
 * Prometheus log-based alert rules. We deliberately do not throw on a
 * low balance — anchoring continues until the EOA actually runs out;
 * the warning is so operators top it up BEFORE that happens.
 */
import {
  createPublicClient,
  http,
  type Address,
  type Hex,
  type PublicClient,
} from "viem";
import {privateKeyToAccount} from "viem/accounts";

export interface SolvencyCheckOpts {
  rpcUrl: string;
  signerKey: Hex;
  /** Minimum balance to suppress the warning (wei). */
  warnBelowWei: bigint;
  /** Optional pre-built public client (used by the tests + tick reuse). */
  publicClient?: PublicClient;
}

export interface SolvencyStatus {
  /** EOA address read from the signer key. */
  signer: Address;
  /** Latest balance on the target chain, in wei. */
  balanceWei: bigint;
  /** True iff balanceWei >= warnBelowWei. */
  ok: boolean;
  /** The configured floor, echoed back for the warning message. */
  warnBelowWei: bigint;
}

/**
 * Read the signer balance and decide whether to warn. Pure data — the
 * caller is responsible for emitting the log line (so tests can assert
 * on the return value without capturing stderr).
 */
export async function checkSolvency(
  opts: SolvencyCheckOpts,
): Promise<SolvencyStatus> {
  const account = privateKeyToAccount(opts.signerKey);
  const client: PublicClient =
    opts.publicClient ??
    createPublicClient({transport: http(opts.rpcUrl)});
  const balanceWei = await client.getBalance({address: account.address});
  return {
    signer: account.address,
    balanceWei,
    ok: balanceWei >= opts.warnBelowWei,
    warnBelowWei: opts.warnBelowWei,
  };
}

/**
 * Single-line stderr warning emit. Idempotent; safe to call every tick.
 * The structured prefix makes the line greppable / Prometheus-compat.
 */
export function emitSolvencyWarning(status: SolvencyStatus): void {
  if (status.ok) return;
  console.error(
    `[anchor-cron] solvency: signer=${status.signer} ` +
      `balanceWei=${status.balanceWei} ` +
      `warnBelowWei=${status.warnBelowWei} ` +
      "action=top-up-required",
  );
}
