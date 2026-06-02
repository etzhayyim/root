import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  submitItem,
  getItem,
  listItems,
  requestReuse,
  handover,
  expire,
  requestRitual,
  ritualize,
} from "../src/index.js";

describe("otakiage rw-free", () => {
  let e: any;

  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:otakiage.etzhayyim.com" });
  });

  describe("submitItem", () => {
    it("submits a reuse_only item with valid input", async () => {
      const result = await submitItem(e, {
        itemId: "item-001",
        ownerDid: "did:plc:owner1",
        title: "Bookshelf",
        mode: "reuse_only",
      });

      expect(result.status).toBe("registered");
      expect(result.itemUri).toBeDefined();
      expect(result.itemStatus).toBe("reuse_open");
    });

    it("submits a ritual_only item (goes to ritual_pending)", async () => {
      const result = await submitItem(e, {
        itemId: "item-002",
        ownerDid: "did:plc:owner1",
        title: "Sacred Item",
        mode: "ritual_only",
      });

      expect(result.status).toBe("registered");
      expect(result.itemStatus).toBe("ritual_pending");
    });

    it("rejects item with missing required fields", async () => {
      const result = await submitItem(e, {
        itemId: "",
        ownerDid: "did:plc:owner1",
        title: "Item",
        mode: "reuse_only",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("missingRequiredFields");
    });

    it("is idempotent on itemId", async () => {
      const input = {
        itemId: "item-003",
        ownerDid: "did:plc:owner1",
        title: "Table",
        mode: "reuse_only",
      };

      const first = await submitItem(e, input);
      expect(first.status).toBe("registered");
      const firstDid = first.did;

      const second = await submitItem(e, input);
      expect(second.status).toBe("alreadyExists");
      expect(second.did).toBe(firstDid);
    });

    it("supports optional metadata", async () => {
      const result = await submitItem(e, {
        itemId: "item-004",
        ownerDid: "did:plc:owner1",
        title: "Chair",
        mode: "reuse_only",
        description: "Wooden chair in good condition",
        category: "furniture",
        locationHint: "Tokyo, Shibuya",
      });

      expect(result.status).toBe("registered");
      const item = await getItem(e, { itemId: "item-004" });
      expect(item.item?.category).toBe("furniture");
      expect(item.item?.description).toBe("Wooden chair in good condition");
    });
  });

  describe("getItem", () => {
    beforeEach(async () => {
      await submitItem(e, {
        itemId: "item-get1",
        ownerDid: "did:plc:owner1",
        title: "Test Item",
        mode: "reuse_only",
      });
    });

    it("retrieves an existing item", async () => {
      const result = await getItem(e, { itemId: "item-get1" });

      expect(result.error).toBeUndefined();
      expect(result.item).toBeDefined();
      expect(result.item?.itemId).toBe("item-get1");
      expect(result.item?.status).toBe("reuse_open");
    });

    it("returns error for non-existent item", async () => {
      const result = await getItem(e, { itemId: "item-notfound" });

      expect(result.error).toBe("notFound");
      expect(result.item).toBeUndefined();
    });

    it("returns error when itemId is missing", async () => {
      const result = await getItem(e, { itemId: "" });

      expect(result.error).toBeDefined();
    });
  });

  describe("listItems", () => {
    beforeEach(async () => {
      await submitItem(e, {
        itemId: "item-list1",
        ownerDid: "did:plc:owner1",
        title: "Reuse Item 1",
        mode: "reuse_only",
        category: "furniture",
      });
      await submitItem(e, {
        itemId: "item-list2",
        ownerDid: "did:plc:owner1",
        title: "Ritual Item",
        mode: "ritual_only",
        category: "ceremonial",
      });
      await submitItem(e, {
        itemId: "item-list3",
        ownerDid: "did:plc:owner2",
        title: "Reuse Item 2",
        mode: "reuse_only",
        category: "furniture",
      });
    });

    it("lists all items", async () => {
      const result = await listItems(e, {});

      expect(result.items.length).toBe(3);
      expect(result.total).toBe(3);
    });

    it("filters by status", async () => {
      const result = await listItems(e, { status: "reuse_open" });

      expect(result.items.length).toBe(2);
      expect(result.items.every((i) => i.status === "reuse_open")).toBe(true);
    });

    it("filters by mode", async () => {
      const result = await listItems(e, { mode: "ritual_only" });

      expect(result.items.length).toBe(1);
      expect(result.items[0]?.mode).toBe("ritual_only");
    });

    it("filters by ownerDid", async () => {
      const result = await listItems(e, { ownerDid: "did:plc:owner2" });

      expect(result.items.length).toBe(1);
      expect(result.items[0]?.ownerDid).toBe("did:plc:owner2");
    });

    it("filters by category", async () => {
      const result = await listItems(e, { category: "furniture" });

      expect(result.items.length).toBe(2);
      expect(result.items.every((i) => i.category === "furniture")).toBe(true);
    });

    it("respects limit parameter", async () => {
      const result = await listItems(e, { limit: 2 });

      expect(result.items.length).toBeLessThanOrEqual(2);
    });
  });

  describe("requestReuse", () => {
    beforeEach(async () => {
      await submitItem(e, {
        itemId: "item-reuse1",
        ownerDid: "did:plc:owner1",
        title: "Item for Reuse",
        mode: "reuse_only",
      });
    });

    it("records a reuse request when status is reuse_open", async () => {
      const result = await requestReuse(e, {
        itemId: "item-reuse1",
        requesterDid: "did:plc:requester1",
        message: "Interested in this item",
      });

      expect(result.status).toBe("registered");
      expect(result.itemId).toBe("item-reuse1");
    });

    it("rejects reuse request for non-existent item", async () => {
      const result = await requestReuse(e, {
        itemId: "item-notfound",
        requesterDid: "did:plc:requester1",
      });

      expect(result.status).toBe("rejected");
      expect(result.error).toBe("itemNotFound");
    });

    it("is idempotent on (itemId, requesterDid)", async () => {
      const input = {
        itemId: "item-reuse1",
        requesterDid: "did:plc:requester2",
      };

      const first = await requestReuse(e, input);
      expect(first.status).toBe("registered");

      const second = await requestReuse(e, input);
      expect(second.status).toBe("alreadyExists");
    });
  });

  describe("handover", () => {
    beforeEach(async () => {
      await submitItem(e, {
        itemId: "item-handover1",
        ownerDid: "did:plc:owner1",
        title: "Item for Handover",
        mode: "reuse_only",
      });
    });

    it("transitions item from reuse_open to handed_over", async () => {
      const result = await handover(e, {
        itemId: "item-handover1",
        recipientDid: "did:plc:recipient1",
      });

      expect(result.status).toBe("handed_over");
      const item = await getItem(e, { itemId: "item-handover1" });
      expect(item.item?.status).toBe("handed_over");
    });

    it("rejects handover for non-existent item", async () => {
      const result = await handover(e, {
        itemId: "item-notfound",
        recipientDid: "did:plc:recipient1",
      });

      expect(result.status).toBe("rejected");
    });
  });

  describe("expire", () => {
    beforeEach(async () => {
      await submitItem(e, {
        itemId: "item-expire1",
        ownerDid: "did:plc:owner1",
        title: "Item to Expire",
        mode: "reuse_only",
      });
    });

    it("transitions item from reuse_open to reuse_expired", async () => {
      const result = await expire(e, { itemId: "item-expire1" });

      expect(result.status).toBe("reuse_expired");
      const item = await getItem(e, { itemId: "item-expire1" });
      expect(item.item?.status).toBe("reuse_expired");
    });

    it("rejects expire for non-existent item", async () => {
      const result = await expire(e, { itemId: "item-notfound" });

      expect(result.status).toBe("rejected");
    });
  });

  describe("requestRitual", () => {
    beforeEach(async () => {
      await submitItem(e, {
        itemId: "item-ritual1",
        ownerDid: "did:plc:owner1",
        title: "Item for Ritual",
        mode: "ritual_only",
      });
    });

    it("records a ritual request", async () => {
      const result = await requestRitual(e, {
        itemId: "item-ritual1",
        requesterDid: "did:plc:requester1",
        notes: "Please perform ceremony",
      });

      expect(result.status).toBe("registered");
      expect(result.itemId).toBe("item-ritual1");
    });

    it("rejects ritual request for non-existent item", async () => {
      const result = await requestRitual(e, {
        itemId: "item-notfound",
      });

      expect(result.status).toBe("rejected");
    });
  });

  describe("ritualize", () => {
    beforeEach(async () => {
      await submitItem(e, {
        itemId: "item-ritualize1",
        ownerDid: "did:plc:owner1",
        title: "Item to Ritualize",
        mode: "ritual_only",
      });
    });

    it("transitions item from ritual_pending to ritualized with certificate", async () => {
      const result = await ritualize(e, {
        itemId: "item-ritualize1",
        certificateUri:
          "at://did:web:otakiage.etzhayyim.com/com.etzhayyim.otakiage.certificate/cert-001",
      });

      expect(result.status).toBe("ritualized");
      const item = await getItem(e, { itemId: "item-ritualize1" });
      expect(item.item?.status).toBe("ritualized");
      expect(item.item?.certificateUri).toBeDefined();
    });

    it("rejects ritualize for non-existent item", async () => {
      const result = await ritualize(e, {
        itemId: "item-notfound",
        certificateUri: "at://did:web:otakiage.etzhayyim.com/cert/cert-001",
      });

      expect(result.status).toBe("rejected");
    });
  });

  describe("state machine invariants", () => {
    it("handover only succeeds when status=reuse_open", async () => {
      // Submit item (status=reuse_open)
      await submitItem(e, {
        itemId: "item-inv1",
        ownerDid: "did:plc:owner1",
        title: "Item",
        mode: "reuse_only",
      });

      // First handover succeeds
      const handover1 = await handover(e, {
        itemId: "item-inv1",
        recipientDid: "did:plc:recipient1",
      });
      expect(handover1.status).toBe("handed_over");

      // Second handover should fail (already handed_over)
      const handover2 = await handover(e, {
        itemId: "item-inv1",
        recipientDid: "did:plc:recipient2",
      });
      expect(handover2.status).toBe("rejected");
    });

    it("ritual_only items skip reuse_open and go directly to ritual_pending", async () => {
      const result = await submitItem(e, {
        itemId: "item-inv2",
        ownerDid: "did:plc:owner1",
        title: "Sacred Item",
        mode: "ritual_only",
      });

      expect(result.itemStatus).toBe("ritual_pending");
      const item = await getItem(e, { itemId: "item-inv2" });
      expect(item.item?.reuseOpenAt).toBeUndefined();
      expect(item.item?.ritualPendingAt).toBeDefined();
    });
  });
});
