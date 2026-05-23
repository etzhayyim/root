/**
 * yatabase /api/donate — USDC donation endpoint (Charter Rider §2).
 *
 * Replaces the disabled /auth/v1/upgrade (Stripe) flow.
 * Routes requests from yatabaseJS SDK to @etzhayyim/sdk/donate.
 *
 * Per ADR-2605192115 §3, allowed purposes:
 *   donation | kisha | grant | tithe | escrow-refund |
 *   internal-purchase | internal-subscription | internal-promo
 *
 * The on-chain signer / ERC-4337 sponsored bundle is supplied via env
 * (YATA_DONATE_PRIVATE_KEY for v0.1 EOA path; SmartAccount wiring lands
 * in v0.2). When neither is configured the endpoint returns 503 with
 * `SignerUnconfigured` so the SDK / Studio can route the user to the
 * client-side wallet path (browser-side viem signer) instead of
 * fabricating a server txHash.
 */

export interface DonateRequestBody {
  /** Recipient address on Base L2. */
  to?: string;
  /** Amount in human-readable format ("50.00") or base units. */
  amountUsdc?: string | number;
  /** Purpose category (DonatePurpose enum). */
  purpose?: string;
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
    blockNumber?: number;
    recordUri?: string;
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
] as const;

type DonatePurpose = (typeof ALLOWED_PURPOSES)[number];

interface DonateEnv {
  YATA_DONATE_PRIVATE_KEY?: string;
  YATA_DONATE_RPC_URL?: string;
  YATA_DONATE_TREASURY?: string;
  // Allow extension for sponsored / paymaster wiring (v0.2 / ADR-2605172100).
  [k: string]: unknown;
}

function json<T extends object>(payload: T, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

/**
 * POST /api/donate — submit a USDC donation.
 *
 * Validates the request, then defers to `@etzhayyim/sdk/donate` for the
 * real on-chain transfer. Server-side signing requires
 * `YATA_DONATE_PRIVATE_KEY` (a Worker secret); without it the endpoint
 * returns 503 instead of fabricating a stub txHash.
 */
export async function handleDonate(
  req: Request,
  env?: Record<string, unknown>,
): Promise<Response> {
  let body: DonateRequestBody = {};
  try {
    body = (await req.json()) as DonateRequestBody;
  } catch {
    return json({ error: "BadRequest", message: "request body must be valid JSON" }, 400);
  }

  if (!body.to || typeof body.to !== "string") {
    return json({ error: "MissingField", message: "to (recipient address) is required" }, 400);
  }
  if (body.amountUsdc === undefined || body.amountUsdc === null || body.amountUsdc === "") {
    return json({ error: "MissingField", message: "amountUsdc is required" }, 400);
  }
  if (!body.purpose || typeof body.purpose !== "string") {
    return json({ error: "MissingField", message: "purpose is required" }, 400);
  }
  if (!ALLOWED_PURPOSES.includes(body.purpose as DonatePurpose)) {
    return json(
      {
        error: "InvalidPurpose",
        code: "INVALID_DONATION_PURPOSE",
        message: `purpose must be one of: ${ALLOWED_PURPOSES.join(", ")}`,
      },
      400,
    );
  }
  if (!body.to.match(/^0x[a-fA-F0-9]{40}$/)) {
    return json({ error: "InvalidAddress", message: "to must be a valid Base L2 address" }, 400);
  }
  const amountStr = typeof body.amountUsdc === "string" ? body.amountUsdc : body.amountUsdc.toString();
  if (!/^\d+(\.\d{1,6})?$/.test(amountStr)) {
    return json(
      { error: "InvalidAmount", message: "amountUsdc must be a valid decimal (e.g., '50.00')" },
      400,
    );
  }
  if (body.memo && body.memo.length > 280) {
    return json({ error: "MemoTooLong", message: "memo must be ≤280 chars" }, 400);
  }

  const donateEnv = (env ?? {}) as DonateEnv;
  if (!donateEnv.YATA_DONATE_PRIVATE_KEY) {
    return json(
      {
        error: "SignerUnconfigured",
        code: "DONATE_SIGNER_MISSING",
        message:
          "Server-side USDC signer (YATA_DONATE_PRIVATE_KEY) is not configured. " +
          "Use the client-side wallet flow (browser viem signer) or contact the operator.",
      },
      503,
    );
  }

  let donate: typeof import("@etzhayyim/sdk").donate;
  try {
    ({ donate } = await import("@etzhayyim/sdk"));
  } catch (e) {
    return json(
      {
        error: "SdkUnavailable",
        code: "ETZHAYYIM_SDK_IMPORT_FAILED",
        message: e instanceof Error ? e.message : "Failed to load @etzhayyim/sdk on the Worker.",
      },
      500,
    );
  }

  try {
    const result = await donate(
      {
        to: body.to as `0x${string}`,
        amountUsdc: amountStr,
        purpose: body.purpose as DonatePurpose,
        memo: body.memo,
        forUri: body.forUri,
      },
      {
        rpcUrl: donateEnv.YATA_DONATE_RPC_URL,
        privateKey: donateEnv.YATA_DONATE_PRIVATE_KEY as `0x${string}`,
      },
    );
    return json({
      ok: true,
      txHash: result.txHash,
      paymentReceipt: {
        txHash: result.paymentReceipt.txHash,
        blockNumber: result.paymentReceipt.blockNumber,
        recordUri: result.paymentReceipt.recordUri,
        from: result.paymentReceipt.from,
        to: result.paymentReceipt.to,
        amount: result.paymentReceipt.amount,
      },
    });
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    console.warn("[yatabase][donate] @etzhayyim/sdk donate() failed:", message);
    return json(
      {
        error: "DonateFailed",
        code: "ETZHAYYIM_SDK_DONATE_FAILED",
        message: message.slice(0, 500),
      },
      502,
    );
  }
}
