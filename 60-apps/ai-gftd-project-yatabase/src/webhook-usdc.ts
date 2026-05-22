/**
 * yatabase /webhook/usdc — USDC donation webhook (v0.2).
 *
 * Replaces the disabled /webhook/stripe flow.
 * Receives a Base L2 USDC Transfer event payload (via ChartersComplianceRegistry attestation).
 *
 * Per ADR-2605192115:
 *   - Verifies donation purpose (donation|kisha|grant|tithe|escrow-refund|internal-*)
 *   - Updates recipient's plan / SBT mint state if eligible
 *   - Emits vertex_donation_event audit row
 *
 * TODO(v0.2): ChartersComplianceRegistry signature verification.
 * Current scaffold uses placeholder signature validation.
 */

export interface UsdcTransferPayload {
  /** Transfer event identifier (USDC Transfer log). */
  txHash: string;
  blockNumber: number;
  /** Sender address. */
  from: string;
  /** Recipient address. */
  to: string;
  /** Amount in USDC base units (6 decimals). */
  amountUsdcMicros: number | string;
  /** Donation purpose (enum). */
  purpose: string;
  /** Optional memo. */
  memo?: string;
  /** ChartersComplianceRegistry attestation signature (placeholder). */
  signature?: string;
  /** Council member DID who attested this transfer. */
  attesterDid?: string;
}

export interface UsdcWebhookResponse {
  ok?: boolean;
  error?: string;
  code?: string;
  message?: string;
  txHash?: string;
  orgDid?: string;
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
 * Placeholder: verify a ChartersComplianceRegistry attestation.
 *
 * TODO(v0.2): Real implementation calls the on-chain registry contract
 * to verify the attester's signature + multisig approval status.
 * For now, returns true if signature is present.
 */
async function verifyComplianceAttestation(
  payload: UsdcTransferPayload,
  _env?: Record<string, unknown>
): Promise<boolean> {
  // TODO: Call ChartersComplianceRegistry.verify(signature, payload, attesterDid)
  // Real impl: fetch registry state from Base L2 RPC, validate multisig threshold
  return !!payload.signature;
}

/**
 * POST /webhook/usdc — Receive a USDC transfer notification.
 *
 * Payload signature:
 *   {
 *     txHash: "0x...",
 *     blockNumber: 12345,
 *     from: "0x...",
 *     to: "0x...",
 *     amountUsdcMicros: "50000000",
 *     purpose: "donation",
 *     memo?: "...",
 *     signature?: "0x...",
 *     attesterDid?: "did:web:..."
 *   }
 *
 * TODO(v0.2): wire real SBT mint + plan state updates based on
 * donation amount + recipient org status.
 */
export async function handleUsdcWebhook(
  req: Request,
  env?: Record<string, unknown>
): Promise<Response> {
  // Parse body
  let payload: UsdcTransferPayload = {} as UsdcTransferPayload;
  try {
    payload = await req.json();
  } catch {
    return new Response(
      JSON.stringify({
        error: "BadRequest",
        message: "request body must be valid JSON",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  // Validate required fields
  if (!payload.txHash || typeof payload.txHash !== "string") {
    return new Response(
      JSON.stringify({
        error: "MissingField",
        message: "txHash is required",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  if (!payload.from || typeof payload.from !== "string") {
    return new Response(
      JSON.stringify({
        error: "MissingField",
        message: "from (sender address) is required",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  if (!payload.to || typeof payload.to !== "string") {
    return new Response(
      JSON.stringify({
        error: "MissingField",
        message: "to (recipient address) is required",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  if (!payload.purpose || typeof payload.purpose !== "string") {
    return new Response(
      JSON.stringify({
        error: "MissingField",
        message: "purpose is required",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  // Validate purpose is in allowed enum
  if (!ALLOWED_PURPOSES.includes(payload.purpose)) {
    return new Response(
      JSON.stringify({
        error: "InvalidPurpose",
        code: "INVALID_DONATION_PURPOSE",
        message: `purpose must be one of: ${ALLOWED_PURPOSES.join(", ")}`,
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  // Placeholder: verify attestation signature
  // TODO(v0.2): Real implementation verifies ChartersComplianceRegistry multisig
  const attested = await verifyComplianceAttestation(payload, env);
  if (!attested) {
    return new Response(
      JSON.stringify({
        error: "InvalidSignature",
        code: "ATTESTATION_VERIFICATION_FAILED",
        message: "ChartersComplianceRegistry attestation signature is invalid or missing",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  // TODO(v0.2): Main business logic
  // 1. Look up recipient org from Base address (reverse lookup in KV / RW)
  // 2. Determine SBT mint eligibility based on purpose + amount
  // 3. If tithe (purpose="tithe"): record 10% Public Fund allocation
  // 4. If donation ≥ threshold: increment plan tier or mint SBT
  // 5. Write vertex_donation_event audit row (RW or KV)
  // 6. Emit success

  const result: UsdcWebhookResponse = {
    ok: true,
    txHash: payload.txHash,
    message:
      "[v0.2 scaffold] Donation received. Real SBT mint + plan state update via RisingWave pending implementation.",
  };

  return new Response(JSON.stringify(result), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}
