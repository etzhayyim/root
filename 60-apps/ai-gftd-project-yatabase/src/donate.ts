/**
 * yatabase /api/donate — USDC donation endpoint (v0.2).
 *
 * Replaces the disabled /auth/v1/upgrade (Stripe) flow.
 * Routes requests from yatabaseJS SDK to @etzhayyim/sdk/donate.
 *
 * Per ADR-2605192115 §3, allowed purposes:
 *   donation | kisha | grant | tithe | escrow-refund |
 *   internal-purchase | internal-subscription | internal-promo
 *
 * TODO: implement actual USDC tx signing + ChartersComplianceRegistry attestation
 */

export interface DonateRequestBody {
  /** Recipient address on Base L2. */
  to: string;
  /** Amount in human-readable format ("50.00") or base units. */
  amountUsdc: string | number;
  /** Purpose category (DonatePurpose enum). */
  purpose: string;
  /** Optional memo (≤280 chars). */
  memo?: string;
  /** Optional AT URI being funded. */
  forUri?: string;
}

export interface DonateResponseBody {
  ok?: boolean;
  error?: string;
  code?: string;
  txHash?: string;
  paymentReceipt?: {
    txHash: string;
    blockNumber: number;
    recordUri: string;
    from?: string;
    to?: string;
    amount?: string;
  };
  message?: string;
}

const ALLOWED_PURPOSES = [
  "donation",
  "kisha",
  "grant",
  "tithe",
  "escrow-refund",
  "internal-purchase",
  "internal-subscription",
  "internal-promo",
];

/**
 * POST /api/donate — Submit a USDC donation.
 *
 * TODO(v0.2): wire @etzhayyim/sdk/donate() to perform the actual
 * on-chain USDC transfer via PayClient or ERC-4337 SmartAccount.
 *
 * For now, this is a scaffold that validates the request shape and
 * returns a placeholder response.
 */
export async function handleDonate(
  req: Request,
  env?: Record<string, unknown>
): Promise<Response> {
  // Parse body
  let body: DonateRequestBody = {};
  try {
    body = await req.json();
  } catch {
    return new Response(
      JSON.stringify({
        error: "BadRequest",
        message: "request body must be valid JSON",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  // Validate fields
  if (!body.to || typeof body.to !== "string") {
    return new Response(
      JSON.stringify({
        error: "MissingField",
        message: "to (recipient address) is required",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  if (!body.amountUsdc) {
    return new Response(
      JSON.stringify({
        error: "MissingField",
        message: "amountUsdc is required",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  if (!body.purpose || typeof body.purpose !== "string") {
    return new Response(
      JSON.stringify({
        error: "MissingField",
        message: "purpose is required",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  // Validate purpose is in allowed enum
  if (!ALLOWED_PURPOSES.includes(body.purpose)) {
    return new Response(
      JSON.stringify({
        error: "InvalidPurpose",
        code: "INVALID_DONATION_PURPOSE",
        message: `purpose must be one of: ${ALLOWED_PURPOSES.join(", ")}`,
        allowed: ALLOWED_PURPOSES,
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  // Validate address format (simplified; should be isAddress() from viem)
  if (!body.to.match(/^0x[a-fA-F0-9]{40}$/)) {
    return new Response(
      JSON.stringify({
        error: "InvalidAddress",
        message: "to must be a valid Base L2 address (0x...)",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  // Validate amount (simple string/number check; parseUsdc does detailed validation)
  const amount = typeof body.amountUsdc === "string"
    ? body.amountUsdc
    : body.amountUsdc.toString();
  if (!amount || !/^\d+(\.\d{1,6})?$/.test(amount)) {
    return new Response(
      JSON.stringify({
        error: "InvalidAmount",
        message: "amountUsdc must be a valid decimal (e.g., '50.00')",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  // TODO(v0.2): Call @etzhayyim/sdk/donate() here
  // Current scaffold returns a stub response
  // Real flow:
  //   1. Load SDK config from env (RPC_URL, PRIVATE_KEY or SPONSORED_BUNDLE)
  //   2. Call donate({ to, amountUsdc, purpose, memo, forUri }, config)
  //   3. On success: emit audit log, record to RisingWave vertex_donation_event
  //   4. On failure: validate Charter Rider §2 compliance, return error details

  const txHashStub = "0x" + Array.from({ length: 64 }, () =>
    Math.floor(Math.random() * 16).toString(16)
  ).join("");

  const result: DonateResponseBody = {
    ok: true,
    txHash: txHashStub,
    paymentReceipt: {
      txHash: txHashStub,
      blockNumber: 12345678,
      recordUri: `at://did:web:yatabase.etzhayyim.com/ai.gftd.apps.payment.sent/${Date.now()}`,
      from: "0x1234567890123456789012345678901234567890",
      to: body.to,
      amount: amount,
    },
    message: "[v0.2 scaffold] Donation accepted. Real USDC transfer via PayClient.pay() pending implementation.",
  };

  return new Response(JSON.stringify(result), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}
