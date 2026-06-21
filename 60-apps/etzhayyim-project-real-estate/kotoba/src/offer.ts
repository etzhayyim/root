/**
 * real-estate kotoba — offer + on-chain earnest deposit tier.
 *
 * createOffer writes an offer (pending) against an active listing. acceptOffer
 * marks it accepted. settleOffer performs the on-chain earnest deposit via an
 * injected SettlementExecutor (real: wrap @etzhayyim/sdk donate() → TitheRouter
 * 10% split), writes a payment record, marks the offer deposited, and moves the
 * listing to under_offer. No Stripe, no RW.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  LISTING_COLLECTION,
  OFFER_COLLECTION,
  PAYMENT_COLLECTION,
  listingRkey,
  offerDid,
  offerRkey,
  paymentRkey,
  type AcceptOfferInput,
  type AcceptOfferOutput,
  type CreateOfferInput,
  type CreateOfferOutput,
  type GetOfferInput,
  type GetOfferOutput,
  type ListingRecord,
  type OfferRecord,
  type PaymentRecord,
  type SettlementExecutor,
  type SettleOfferInput,
  type SettleOfferOutput,
} from "./types.js";
import { parseMicros, splitTithe } from "./tithe.js";

export async function createOffer(
  e: Etzhayyim,
  input: CreateOfferInput
): Promise<CreateOfferOutput> {
  if (!input.offerId || !input.listingId || !input.buyerDid) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  try {
    if (parseMicros(input.amountMicros) <= 0n) {
      return { status: "rejected", error: "amountMustBePositive" };
    }
  } catch {
    return { status: "rejected", error: "invalidAmount" };
  }

  const listingResp = await e
    .read<ListingRecord>({ collection: LISTING_COLLECTION, rkey: listingRkey(input.listingId) })
    .catch(() => ({ records: [] }));
  const listing = listingResp.records[0]?.value;
  if (!listing) return { status: "listingNotFound", error: "listingNotFound" };
  if (listing.status !== "active") {
    return { status: "rejected", error: `listingNotActive:${listing.status}` };
  }

  const rkey = offerRkey(input.offerId);
  const existing = await e
    .read<OfferRecord>({ collection: OFFER_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      offerUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      offerId: input.offerId,
    };
  }

  const did = offerDid(input.offerId);
  const record: OfferRecord = {
    did,
    offerId: input.offerId,
    listingId: input.listingId,
    buyerDid: input.buyerDid,
    amountMicros: input.amountMicros,
    status: "pending",
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({
    collection: OFFER_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return { status: "created", offerUri: receipt.uri, did, offerId: input.offerId };
}

export async function getOffer(
  e: Etzhayyim,
  input: GetOfferInput
): Promise<GetOfferOutput> {
  if (!input.offerId) return { error: "invalidOfferId" };
  const resp = await e
    .read<OfferRecord>({ collection: OFFER_COLLECTION, rkey: offerRkey(input.offerId) })
    .catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { offer: { ...r.value, offerUri: r.uri } };
}

export async function acceptOffer(
  e: Etzhayyim,
  input: AcceptOfferInput
): Promise<AcceptOfferOutput> {
  if (!input.offerId) return { status: "rejected", error: "invalidOfferId" };
  const rkey = offerRkey(input.offerId);
  const resp = await e
    .read<OfferRecord>({ collection: OFFER_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  const offer = resp.records[0]?.value;
  if (!offer) return { status: "notFound", error: "offerNotFound" };
  if (offer.status !== "pending") {
    return { status: "rejected", error: `offerNotPending:${offer.status}` };
  }
  await e.write({
    collection: OFFER_COLLECTION,
    record: { ...offer, status: "accepted" } as unknown as Record<string, unknown>,
    rkey,
  });
  return { status: "accepted", offerId: input.offerId };
}

export async function settleOffer(
  e: Etzhayyim,
  settle: SettlementExecutor,
  input: SettleOfferInput
): Promise<SettleOfferOutput> {
  if (!input.offerId || !input.to) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  let deposit: bigint;
  try {
    deposit = parseMicros(input.depositMicros);
    if (deposit <= 0n) return { status: "rejected", error: "depositMustBePositive" };
  } catch {
    return { status: "rejected", error: "invalidDeposit" };
  }

  const rkey = offerRkey(input.offerId);
  const resp = await e
    .read<OfferRecord>({ collection: OFFER_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  const offerRec = resp.records[0];
  if (!offerRec?.value) return { status: "notFound", error: "offerNotFound" };
  const offer = offerRec.value;
  if (offer.status === "deposited") {
    return { status: "alreadyDeposited", error: "offerAlreadyDeposited" };
  }
  if (offer.status !== "accepted") {
    return { status: "notAccepted", error: `offerNotAccepted:${offer.status}` };
  }

  const split = splitTithe(deposit);
  const { txHash } = await settle({
    to: input.to,
    amountMicros: split.gross,
    purpose: "internal-purchase",
    memo: input.memo,
    forUri: offerRec.uri,
  });

  const payment: PaymentRecord = {
    offerId: offer.offerId,
    listingId: offer.listingId,
    buyerDid: offer.buyerDid,
    purpose: "internal-purchase",
    grossMicros: split.gross.toString(),
    titheMicros: split.tithe.toString(),
    netMicros: split.net.toString(),
    txHash,
    settledAt: new Date().toISOString(),
  };
  const payReceipt = await e.write({
    collection: PAYMENT_COLLECTION,
    record: payment as unknown as Record<string, unknown>,
    rkey: paymentRkey(offer.offerId),
  });

  await e.write({
    collection: OFFER_COLLECTION,
    record: { ...offer, status: "deposited", txHash } as unknown as Record<string, unknown>,
    rkey,
  });

  // Move listing to under_offer.
  const listingResp = await e
    .read<ListingRecord>({ collection: LISTING_COLLECTION, rkey: listingRkey(offer.listingId) })
    .catch(() => ({ records: [] }));
  const listing = listingResp.records[0]?.value;
  if (listing && listing.status === "active") {
    await e.write({
      collection: LISTING_COLLECTION,
      record: { ...listing, status: "under_offer" } as unknown as Record<string, unknown>,
      rkey: listingRkey(offer.listingId),
    });
  }

  return {
    status: "settled",
    paymentUri: payReceipt.uri,
    txHash,
    titheMicros: payment.titheMicros,
    netMicros: payment.netMicros,
  };
}
