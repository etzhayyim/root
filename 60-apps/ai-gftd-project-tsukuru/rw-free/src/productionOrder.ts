/**
 * tsukuru rw-free — productionOrder create + cancel reference impl.
 *
 * Replaces vendor `60-apps/ai-gftd-project-tsukuru/appview/tsukuru-
 * tsukr8u0/src/app.ts:740-870` with @etzhayyim/sdk equivalents:
 *
 *   vendor (RW + Stripe)              → etzhayyim (PDS + escrow_intent)
 *   ─────────────────────────────       ────────────────────────────────
 *   createKyselyDb().insertInto()      → e.write({ collection, record })
 *   recordWrite(sdk, ...)              → e.write({ ... })
 *   invoke(sdk, STRIPE_DID,            → escrow.openIntent() (no tx)
 *     "chargeCustomer", ...)
 *   invoke(sdk, STRIPE_DID,            → escrow.refundIntent()
 *     "cancelCard", ...)                 (no tx)
 *
 * Per ADR-2605202900 Phase 2, the actual USDC.transfer at delivery
 * confirmation lives in qualityInspection module (next PR), not here.
 *
 * Other 44 tsukuru commands (manufacturerRegistry / euv / cnt / etc.)
 * follow the same pattern: replace `createKyselyDb` write with
 * `e.write()`, eliminate `invoke(STRIPE_DID, ...)` for payment ops.
 * Filed as Phase 2 follow-up PRs.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import { openIntent, refundIntent } from "./escrow.js";
import {
  CANCELLABLE_STATUSES,
  type CancelOrderInput,
  type CancelOrderOutput,
  type CreateOrderInput,
  type CreateOrderOutput,
  type ProductionOrderRecord,
} from "./types.js";

const MS_PER_DAY = 86_400_000;

/** Default lead-time estimate by priority. Used when no industry profile is supplied. */
function defaultLeadTimeDays(priority: string): number {
  switch (priority) {
    case "urgent":
      return 7;
    case "high":
      return 21;
    case "low":
      return 90;
    default:
      return 45;
  }
}

/**
 * Create a production order.
 *
 *   1. (caller pre-screens manufacturer activeness + sanctions —
 *      separate module; the rw-free reference focuses on the order
 *      write + escrow intent.)
 *   2. Compute estimated completion date from priority.
 *   3. Build productionOrder record body.
 *   4. If payment.method === "escrow_intent": openIntent() →
 *      escrowIntentUri threaded into the record body.
 *   5. e.write() the productionOrder record.
 *   6. Return CreateOrderOutput.
 */
export async function createProductionOrder(
  e: Etzhayyim,
  input: CreateOrderInput,
  opts: { manufacturerWalletAddress?: string } = {}
): Promise<CreateOrderOutput> {
  if (!input.manufacturerDid || !input.customerDid) {
    return {
      productionOrderUri: "",
      status: "rejected",
      error: "missingRequiredFields",
    };
  }

  const priority = input.priority ?? "normal";
  const estimatedDays = defaultLeadTimeDays(priority);
  const estimatedCompletion = new Date(
    Date.now() + estimatedDays * MS_PER_DAY
  )
    .toISOString()
    .split("T")[0];

  // Step 4: open escrow intent if payment.method === "escrow_intent".
  let escrowIntentUri: string | undefined;
  if (input.payment?.method === "escrow_intent") {
    if (!opts.manufacturerWalletAddress) {
      return {
        productionOrderUri: "",
        status: "rejected",
        error: "missingManufacturerWalletForEscrowIntent",
      };
    }
    // forUri is updated after the productionOrder write; for now use
    // a placeholder that the caller can rebind. The escrowOpened
    // record's `forUri` field is informational, not a hard FK.
    const result = await openIntent(e, {
      to: opts.manufacturerWalletAddress,
      payment: input.payment,
      forUri: `at-pending:${input.customerDid}/${Date.now()}`,
      memo: `tsukuru order ${input.manufacturerDid}`,
    });
    escrowIntentUri = result.escrowIntentUri;
  }

  // Step 5: build + write productionOrder record.
  const record: ProductionOrderRecord = {
    manufacturerDid: input.manufacturerDid,
    customerDid: input.customerDid,
    factoryDid: input.factoryDid,
    productSpec: input.productSpec,
    fulfillmentMode: input.fulfillmentMode ?? "bto",
    priority,
    deadline: input.deadline,
    payment: input.payment,
    okaimonoOrderRef: input.okaimonoOrderRef,
    certificationsRequired: input.certificationsRequired,
    status: "pending",
    estimatedCompletion: `${estimatedCompletion}T00:00:00Z`,
    estimatedDays,
    escrowIntentUri,
    createdAt: new Date().toISOString(),
  };

  const receipt = await e.write({
    collection: "ai.gftd.apps.tsukuru.productionOrder",
    record: record as unknown as Record<string, unknown>,
  });

  return {
    productionOrderUri: receipt.uri,
    status: "pending",
    escrowIntentUri,
    estimatedCompletion: record.estimatedCompletion,
    estimatedDays,
    manufacturerDid: input.manufacturerDid,
  };
}

/**
 * Cancel a production order before delivery.
 *
 *   1. Read existing productionOrder record by uri.
 *   2. Verify currentStatus ∈ CANCELLABLE_STATUSES.
 *   3. If escrowIntentUri present: refundIntent() → escrowRefundUri.
 *      (record-only — no on-chain tx since USDC was never moved.)
 *   4. e.write() update productionOrder record with status=cancelled
 *      + cancelReason + cancelledAt + escrowRefundUri.
 *   5. Return CancelOrderOutput.
 *
 * Phase 2 quirk: AT Protocol records are append-only. "Update" here
 * actually writes a new record with the same rkey replacing the
 * previous version (createRecord with explicit rkey on the same DID).
 * Phase 3+ may switch to dedicated state-transition records
 * (productionOrderCancelled) per AT firehose best practices.
 */
export async function cancelProductionOrder(
  e: Etzhayyim,
  input: CancelOrderInput
): Promise<CancelOrderOutput> {
  // Step 1: read existing record. The Etzhayyim.read() API supports
  // rkey-direct lookup; for this reference we read via the explicit
  // rkey. In production the caller normally has the record already
  // loaded from a prior dispatch decision.
  const { uri } = parseAtUri(input.productionOrderUri);
  const rkey = uri.rkey;
  if (!rkey) {
    return {
      status: "cannotCancel",
      productionOrderUri: input.productionOrderUri,
      error: "invalidAtUri",
    };
  }

  const readResp = await e.read<ProductionOrderRecord>({
    collection: "ai.gftd.apps.tsukuru.productionOrder",
    rkey,
  });
  const order = readResp.records[0]?.value;
  if (!order) {
    return {
      status: "cannotCancel",
      productionOrderUri: input.productionOrderUri,
      error: "notFound",
    };
  }

  // Step 2: cancellable status check.
  if (
    !CANCELLABLE_STATUSES.includes(
      order.status as (typeof CANCELLABLE_STATUSES)[number]
    )
  ) {
    return {
      status: "cannotCancel",
      productionOrderUri: input.productionOrderUri,
      currentStatus: order.status,
      cancellableStatuses: [...CANCELLABLE_STATUSES],
    };
  }

  // Step 3: refund escrow intent (record-only) if present.
  let escrowRefundUri: string | undefined;
  if (order.escrowIntentUri && input.cancelledByDid) {
    const refund = await refundIntent(e, {
      escrowIntentUri: order.escrowIntentUri,
      productionOrderUri: input.productionOrderUri,
      reason: input.reason ?? "user-cancelled",
      refundedByDid: input.cancelledByDid,
    });
    escrowRefundUri = refund.escrowRefundUri;
  }

  // Step 4: write updated record (same rkey for in-place state machine).
  const updated: ProductionOrderRecord = {
    ...order,
    status: "cancelled",
    cancelReason: input.reason,
    cancelledAt: new Date().toISOString(),
    cancelledByDid: input.cancelledByDid,
    escrowRefundUri,
  };
  await e.write({
    collection: "ai.gftd.apps.tsukuru.productionOrder",
    record: updated as unknown as Record<string, unknown>,
    rkey,
  });

  return {
    status: "cancelled",
    productionOrderUri: input.productionOrderUri,
    escrowRefundUri,
  };
}

/** Minimal AT URI parser. `at://<did>/<collection>/<rkey>`. */
function parseAtUri(s: string): {
  uri: { did: string; collection: string; rkey: string };
} {
  // Strip `at://` prefix.
  const body = s.startsWith("at://") ? s.slice(5) : s;
  const parts = body.split("/");
  // [did, collection, rkey] — collection can contain dots; rkey is the
  // trailing segment after the last collection NSID separator. For our
  // tsukuru.productionOrder collection the NSID is the second-to-last
  // dotted run; rkey is the final path segment.
  // Practical parse:
  if (parts.length < 3)
    return { uri: { did: parts[0] ?? "", collection: "", rkey: "" } };
  const did = parts[0];
  const rkey = parts[parts.length - 1];
  const collection = parts.slice(1, -1).join("/");
  return { uri: { did, collection, rkey } };
}
