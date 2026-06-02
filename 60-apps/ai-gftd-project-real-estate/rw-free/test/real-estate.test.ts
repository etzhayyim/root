import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  createListing,
  getListing,
  listListings,
  createOffer,
  getOffer,
  acceptOffer,
  settleOffer,
  splitTithe,
  parseMicros,
  type SettlementExecutor,
} from "../src/index.js";

const fakeSettle: SettlementExecutor = async () => ({ txHash: "0xdeed" });
const ESCROW = "0x8888888888888888888888888888888888888888";

describe("real-estate rw-free", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:real-estate.etzhayyim.com" });
  });

  it("tithe splits 10% with no leak", () => {
    const s = splitTithe(parseMicros("100000000"));
    expect(s.tithe).toBe(10_000_000n);
    expect(s.tithe + s.net).toBe(s.gross);
  });

  describe("listing", () => {
    const l = {
      listingId: "L-1",
      sellerDid: "did:web:alice.etzhayyim.com",
      title: "Kyoto machiya",
      propertyType: "house" as const,
      askingPriceMicros: "500000000000",
      location: "kyoto",
      sizeM2: 120,
    };
    it("creates active + gets + lists", async () => {
      expect((await createListing(e, l)).status).toBe("created");
      expect((await getListing(e, { listingId: "L-1" })).listing?.status).toBe("active");
      expect((await listListings(e, { propertyType: "house" })).total).toBe(1);
    });
    it("rejects invalid type / non-positive price", async () => {
      expect((await createListing(e, { ...l, propertyType: "castle" as any })).status).toBe("rejected");
      expect((await createListing(e, { ...l, askingPriceMicros: "0" })).status).toBe("rejected");
    });
  });

  describe("offer + on-chain deposit", () => {
    beforeEach(async () => {
      await createListing(e, {
        listingId: "L-1",
        sellerDid: "did:web:alice.etzhayyim.com",
        title: "Kyoto machiya",
        propertyType: "house",
        askingPriceMicros: "500000000000",
      });
    });
    it("creates pending offer; rejects when listing missing", async () => {
      expect((await createOffer(e, { offerId: "O-1", listingId: "L-1", buyerDid: "did:web:bob.etzhayyim.com", amountMicros: "480000000000" })).status).toBe("created");
      expect((await getOffer(e, { offerId: "O-1" })).offer?.status).toBe("pending");
      expect((await createOffer(e, { offerId: "O-2", listingId: "NOPE", buyerDid: "x", amountMicros: "1" })).status).toBe("listingNotFound");
    });
    it("requires acceptance before deposit", async () => {
      await createOffer(e, { offerId: "O-1", listingId: "L-1", buyerDid: "did:web:bob.etzhayyim.com", amountMicros: "480000000000" });
      const early = await settleOffer(e, fakeSettle, { offerId: "O-1", to: ESCROW, depositMicros: "50000000000" });
      expect(early.status).toBe("notAccepted");
    });
    it("accept → on-chain deposit: tithe split + offer deposited + listing under_offer", async () => {
      await createOffer(e, { offerId: "O-1", listingId: "L-1", buyerDid: "did:web:bob.etzhayyim.com", amountMicros: "480000000000" });
      expect((await acceptOffer(e, { offerId: "O-1" })).status).toBe("accepted");
      const s = await settleOffer(e, fakeSettle, { offerId: "O-1", to: ESCROW, depositMicros: "50000000000" });
      expect(s.status).toBe("settled");
      expect(s.titheMicros).toBe("5000000000"); // 10% of 50,000 USDC
      expect((await getOffer(e, { offerId: "O-1" })).offer?.status).toBe("deposited");
      expect((await getListing(e, { listingId: "L-1" })).listing?.status).toBe("under_offer");
    });
    it("does not double-deposit", async () => {
      await createOffer(e, { offerId: "O-1", listingId: "L-1", buyerDid: "did:web:bob.etzhayyim.com", amountMicros: "480000000000" });
      await acceptOffer(e, { offerId: "O-1" });
      await settleOffer(e, fakeSettle, { offerId: "O-1", to: ESCROW, depositMicros: "50000000000" });
      const again = await settleOffer(e, fakeSettle, { offerId: "O-1", to: ESCROW, depositMicros: "50000000000" });
      expect(again.status).toBe("alreadyDeposited");
    });
  });
});
