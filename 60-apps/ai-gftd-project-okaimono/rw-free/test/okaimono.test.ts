import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  publishCatalogItem,
  getCatalogItem,
  listCatalogItems,
  createOrder,
  getOrder,
  settleOrder,
  splitTithe,
  parseMicros,
  type SettlementExecutor,
} from "../src/index.js";

const MANUF = "did:web:tsukuru.etzhayyim.com:manufacturer:acme";
const FACTORY = "did:web:tsukuru.etzhayyim.com:factory:osaka-1";

// Fake on-chain executor for tests (real deployments wrap @etzhayyim/sdk/donate).
const fakeSettle: SettlementExecutor = async () => ({ txHash: "0xdeadbeef" });

describe("okaimono rw-free", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:okaimono.etzhayyim.com" });
  });

  describe("tithe math (constitutional 10%)", () => {
    it("splits 10% with tithe + net === gross", () => {
      const s = splitTithe(parseMicros("12000000")); // 12 USDC
      expect(s.tithe).toBe(1_200_000n);
      expect(s.net).toBe(10_800_000n);
      expect(s.tithe + s.net).toBe(s.gross);
    });
    it("floors tithe and keeps remainder in net (no leak)", () => {
      const s = splitTithe(7n); // 0.7 of a micro-tithe → floors to 0
      expect(s.tithe).toBe(0n);
      expect(s.net).toBe(7n);
      expect(s.tithe + s.net).toBe(7n);
    });
    it("rejects negative", () => {
      expect(() => splitTithe(-1n)).toThrow();
    });
    it("rejects non-integer micros strings", () => {
      expect(() => parseMicros("1.5")).toThrow();
    });
  });

  describe("publishCatalogItem (D2C OEM-only)", () => {
    const base = {
      sku: "MAT-001",
      title: "OEM Mattress",
      priceMicros: "120000000",
      manufacturerDid: MANUF,
      factoryDid: FACTORY,
      productionMode: "OEM" as const,
      category: "bedding",
    };
    it("publishes a valid OEM item", async () => {
      const r = await publishCatalogItem(e, base);
      expect(r.status).toBe("published");
      expect(r.itemUri).toBeDefined();
      expect(r.did).toContain("item:mat-001");
    });
    it("is idempotent on sku", async () => {
      await publishCatalogItem(e, base);
      const again = await publishCatalogItem(e, base);
      expect(again.status).toBe("alreadyExists");
    });
    it("rejects items without manufacturer/factory (no external resale)", async () => {
      const r = await publishCatalogItem(e, {
        ...base,
        manufacturerDid: "",
        factoryDid: "",
      });
      expect(r.status).toBe("rejected");
      expect(r.error).toBe("oemRequiresManufacturerAndFactory");
    });
    it("rejects invalid production mode", async () => {
      const r = await publishCatalogItem(e, {
        ...base,
        productionMode: "RESALE" as any,
      });
      expect(r.status).toBe("rejected");
    });
    it("get + list round-trip", async () => {
      await publishCatalogItem(e, base);
      const got = await getCatalogItem(e, { sku: "MAT-001" });
      expect(got.item?.title).toBe("OEM Mattress");
      const list = await listCatalogItems(e, { productionMode: "OEM" });
      expect(list.total).toBe(1);
    });
  });

  describe("order + on-chain settlement", () => {
    const order = {
      orderId: "ORD-1",
      buyerDid: "did:web:alice.etzhayyim.com",
      lines: [
        { sku: "MAT-001", qty: 2, unitPriceMicros: "120000000" },
        { sku: "PIL-001", qty: 1, unitPriceMicros: "30000000" },
      ],
    };
    it("creates an order with computed total + pending_payment", async () => {
      const r = await createOrder(e, order);
      expect(r.status).toBe("created");
      // 2×120 + 1×30 = 270 USDC
      expect(r.totalMicros).toBe("270000000");
      const got = await getOrder(e, { orderId: "ORD-1" });
      expect(got.order?.status).toBe("pending_payment");
    });
    it("rejects empty orders", async () => {
      const r = await createOrder(e, { ...order, lines: [] });
      expect(r.status).toBe("rejected");
    });
    it("settles on-chain: tithe split + payment record + order→paid", async () => {
      await createOrder(e, order);
      const s = await settleOrder(e, fakeSettle, {
        orderId: "ORD-1",
        to: "0x1111111111111111111111111111111111111111",
      });
      expect(s.status).toBe("settled");
      expect(s.txHash).toBe("0xdeadbeef");
      expect(s.titheMicros).toBe("27000000"); // 10% of 270
      expect(s.netMicros).toBe("243000000");
      const got = await getOrder(e, { orderId: "ORD-1" });
      expect(got.order?.status).toBe("paid");
    });
    it("does not double-settle a paid order", async () => {
      await createOrder(e, order);
      await settleOrder(e, fakeSettle, {
        orderId: "ORD-1",
        to: "0x1111111111111111111111111111111111111111",
      });
      const again = await settleOrder(e, fakeSettle, {
        orderId: "ORD-1",
        to: "0x1111111111111111111111111111111111111111",
      });
      expect(again.status).toBe("alreadyPaid");
    });
    it("settling a missing order returns notFound", async () => {
      const s = await settleOrder(e, fakeSettle, {
        orderId: "NOPE",
        to: "0x1111111111111111111111111111111111111111",
      });
      expect(s.status).toBe("notFound");
    });
  });
});
