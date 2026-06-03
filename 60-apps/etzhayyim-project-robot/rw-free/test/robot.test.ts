import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerProduct,
  getProduct,
  listProducts,
  placeOrder,
  listOrders,
  getOrder,
  coverage,
} from "../src/index.js";

const OWNER = "did:web:robot.etzhayyim.com";

describe("robot rw-free (kotoba-E2E split)", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: OWNER });
  });

  describe("productCatalog (PLAINTEXT public storefront)", () => {
    it("registers, dedups, validates, gets, lists/filters", async () => {
      expect((await registerProduct(e, { productId: "reachy-mini", name: "Reachy Mini", assetKind: "robot", region: "global", priceUsd: "299.00" })).status).toBe("registered");
      expect((await registerProduct(e, { productId: "reachy-mini", name: "Reachy Mini", assetKind: "robot", region: "global", priceUsd: "299.00" })).status).toBe("alreadyExists");
      // invalid price (float-as-text is fine; non-decimal string rejected)
      expect((await registerProduct(e, { productId: "bad", name: "Bad", assetKind: "robot", region: "x", priceUsd: "free" })).status).toBe("rejected");
      expect((await registerProduct(e, { productId: "", name: "", assetKind: "", region: "", priceUsd: "1.00" })).status).toBe("rejected");
      await registerProduct(e, { productId: "agv-1", name: "AGV One", assetKind: "agv", region: "jp", priceUsd: "5400.00" });

      const got = await getProduct(e, { productId: "reachy-mini" });
      expect(got.product?.name).toBe("Reachy Mini");
      expect(got.product?.priceUsd).toBe("299.00");
      expect((await getProduct(e, { productId: "nope" })).error).toBe("notFound");

      expect((await listProducts(e)).total).toBe(2);
      expect((await listProducts(e, { assetKind: "robot" })).total).toBe(1);
      expect((await listProducts(e, { region: "jp" })).total).toBe(1);
    });
  });

  describe("customerOrder (E2E-ENCRYPTED confidential)", () => {
    beforeEach(async () => {
      await registerProduct(e, { productId: "reachy-mini", name: "Reachy Mini", assetKind: "robot", region: "global", priceUsd: "299.00" });
    });

    it("seals via encryptedWrite, round-trips via encryptedRead, validates + FK", async () => {
      const ok = await placeOrder(e, { orderId: "o1", productId: "reachy-mini", customerId: "cust:acme", itemOrService: "Reachy Mini", quantity: 3, commercialTerms: "897.00" });
      expect(ok.status).toBe("placed");
      expect(ok.keyId).toBeTruthy();
      // confidential body must not appear in the plaintext catalog store
      expect(e.count("com.etzhayyim.apps.robot.productCatalog")).toBe(1);
      expect(e.encCount()).toBe(1);

      // FK: unknown product rejected
      expect((await placeOrder(e, { orderId: "oX", productId: "ghost", customerId: "c", itemOrService: "x", quantity: 1, commercialTerms: "1.00" })).status).toBe("rejected");
      // quantity must be positive integer
      expect((await placeOrder(e, { orderId: "oY", productId: "reachy-mini", customerId: "c", itemOrService: "x", quantity: 0, commercialTerms: "1.00" })).status).toBe("rejected");
      // commercialTerms must be a decimal string
      expect((await placeOrder(e, { orderId: "oZ", productId: "reachy-mini", customerId: "c", itemOrService: "x", quantity: 1, commercialTerms: "negotiable" })).status).toBe("rejected");

      const got = await getOrder(e, { orderId: "o1" });
      expect(got.order?.customerId).toBe("cust:acme");
      expect(got.order?.quantity).toBe(3);
      expect(got.order?.commercialTerms).toBe("897.00");

      await placeOrder(e, { orderId: "o2", productId: "reachy-mini", customerId: "cust:globex", itemOrService: "Reachy Mini", quantity: 1, commercialTerms: "299.00" });
      expect((await listOrders(e)).total).toBe(2);
      expect((await listOrders(e, { productId: "reachy-mini" })).total).toBe(2);
    });

    it("enforces read-cap: a non-recipient DID cannot decrypt the order", async () => {
      await placeOrder(e, { orderId: "o1", productId: "reachy-mini", customerId: "cust:acme", itemOrService: "Reachy Mini", quantity: 1, commercialTerms: "299.00" });
      const outsider: any = new MockEtzhayyim({ did: "did:web:outsider.example" });
      expect((await listOrders(outsider)).total).toBe(0);
    });

    it("grants read-cap to an explicit recipient", async () => {
      const partner = "did:web:partner.example";
      const r = await placeOrder(e, { orderId: "o1", productId: "reachy-mini", customerId: "cust:acme", itemOrService: "Reachy Mini", quantity: 1, commercialTerms: "299.00", recipients: [partner] });
      expect(r.status).toBe("placed");
      expect((await listOrders(e)).total).toBe(1);
    });
  });

  describe("coverage rollup", () => {
    it("counts plaintext products + E2E orders", async () => {
      await registerProduct(e, { productId: "reachy-mini", name: "Reachy Mini", assetKind: "robot", region: "global", priceUsd: "299.00" });
      await registerProduct(e, { productId: "agv-1", name: "AGV One", assetKind: "agv", region: "jp", priceUsd: "5400.00" });
      await registerProduct(e, { productId: "reachy-pro", name: "Reachy Pro", assetKind: "robot", region: "global", priceUsd: "1299.00" });
      await placeOrder(e, { orderId: "o1", productId: "reachy-mini", customerId: "cust:acme", itemOrService: "Reachy Mini", quantity: 1, commercialTerms: "299.00" });

      const cov = await coverage(e);
      expect(cov.productCatalogCount).toBe(3);
      expect(cov.customerOrderCount).toBe(1);
      expect(cov.productsByAssetKind?.robot).toBe(2);
      expect(cov.productsByAssetKind?.agv).toBe(1);
      expect(cov.truncated).toBe(false);
    });
  });
});
