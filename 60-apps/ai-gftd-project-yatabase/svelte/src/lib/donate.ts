/**
 * yatabase useDonate() composable — USDC donation widget (v0.2).
 *
 * Svelte 5 reactive wrapper around /api/donate endpoint.
 * Returns: { donate, loading, error, success, txHash }
 *
 * Usage:
 *   const { donate, loading, error } = useDonate();
 *   await donate({
 *     to: "0x...",
 *     amountUsdc: "50.00",
 *     purpose: "donation",
 *     memo: "Support etzhayyim mission"
 *   });
 */

import { writable, type Readable } from "svelte/store";

export interface DonateRequest {
  to: string;
  amountUsdc: string | number;
  purpose: string;
  memo?: string;
  forUri?: string;
}

export interface DonatePaymentReceipt {
  txHash: string;
  blockNumber?: number;
  recordUri?: string;
  from?: string;
  to?: string;
  amount?: string;
}

export interface DonateResponse {
  ok?: boolean;
  error?: string;
  code?: string;
  txHash?: string;
  paymentReceipt?: DonatePaymentReceipt;
  message?: string;
}

export interface UseDonateReturn {
  /** Trigger the donation submission. */
  donate: (opts: DonateRequest) => Promise<DonateResponse>;
  /** True while request is in-flight. */
  loading: Readable<boolean>;
  /** Error message, if any. */
  error: Readable<string | null>;
  /** True if donation succeeded. */
  success: Readable<boolean>;
  /** Transaction hash, if successful. */
  txHash: Readable<string | null>;
}

/**
 * Reactive donation widget hook.
 *
 * @example
 *   const { donate, loading, error, txHash } = useDonate();
 *   let amount = "50.00";
 *   let to = "0x123...";
 *
 *   async function handleSubmit() {
 *     const result = await donate({
 *       to,
 *       amountUsdc: amount,
 *       purpose: "donation"
 *     });
 *     if (result.ok) {
 *       console.log("Success:", result.txHash);
 *     }
 *   }
 */
export function useDonate(): UseDonateReturn {
  const loading = writable(false);
  const error = writable<string | null>(null);
  const success = writable(false);
  const txHash = writable<string | null>(null);

  const donate = async (opts: DonateRequest): Promise<DonateResponse> => {
    loading.set(true);
    error.set(null);
    success.set(false);
    txHash.set(null);

    try {
      const apiKey = localStorage.getItem("sk_live_yata_key");
      const headers: Record<string, string> = {
        "content-type": "application/json",
      };
      if (apiKey) {
        headers.authorization = `Bearer ${apiKey}`;
      }

      const response = await fetch("/api/donate", {
        method: "POST",
        headers,
        body: JSON.stringify(opts),
      });

      const result = (await response.json()) as DonateResponse;

      if (!response.ok || result.error) {
        const errorMsg = result.error || result.message || "Donation failed";
        error.set(errorMsg);
        return result;
      }

      if (result.txHash) {
        txHash.set(result.txHash);
        success.set(true);
      }

      return result;
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : "Network error";
      error.set(errorMsg);
      return { error: errorMsg };
    } finally {
      loading.set(false);
    }
  };

  return {
    donate,
    loading,
    error,
    success,
    txHash,
  };
}

/**
 * Allowed donation purposes for validation.
 */
export const ALLOWED_PURPOSES = [
  "donation",
  "kisha",
  "grant",
  "tithe",
  "escrow-refund",
  "internal-purchase",
  "internal-subscription",
  "internal-promo",
] as const;

/**
 * Validate donation purpose.
 */
export function isValidDonationPurpose(purpose: string): boolean {
  return ALLOWED_PURPOSES.includes(purpose as (typeof ALLOWED_PURPOSES)[number]);
}
