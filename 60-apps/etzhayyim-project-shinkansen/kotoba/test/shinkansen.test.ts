import { describe, it, expect, beforeEach } from "vitest";
import { MockEtzhayyim } from "@etzhayyim/sdk-mock";
import {
  registerLine,
  listLines,
  addTimetable,
  listTimetable,
  addFare,
  listFares,
  recordOperation,
  listOperations,
  coverage,
} from "../src/index.js";

const SRC = "https://www.jr-central.co.jp/example";

describe("shinkansen kotoba", () => {
  let e: any;
  beforeEach(() => {
    e = new MockEtzhayyim({ did: "did:web:shinkansen.etzhayyim.com" });
  });

  describe("line + timetable", () => {
    it("registers lines, adds timetable (FK→line, HH:MM validated), lists", async () => {
      expect((await registerLine(e, { lineId: "tokaido", name: "東海道新幹線", operator: "JR-Central" })).status).toBe("registered");
      expect((await addTimetable(e, { entryId: "T-1", lineId: "tokaido", trainNumber: "Nozomi 1", trainType: "Nozomi", departureStation: "Tokyo", arrivalStation: "Shin-Osaka", departTime: "06:00", arriveTime: "08:27" })).status).toBe("added");
      expect((await addTimetable(e, { entryId: "T-X", lineId: "tokaido", trainNumber: "x", trainType: "x", departureStation: "a", arrivalStation: "b", departTime: "6am", arriveTime: "08:27" })).status).toBe("rejected"); // HH:MM
      expect((await addTimetable(e, { entryId: "T-G", lineId: "ghost", trainNumber: "x", trainType: "x", departureStation: "a", arrivalStation: "b", departTime: "06:00", arriveTime: "08:27" })).status).toBe("lineNotFound");
      expect((await listLines(e, { operator: "JR-Central" })).total).toBe(1);
      expect((await listTimetable(e, { lineId: "tokaido", trainType: "Nozomi" })).total).toBe(1);
    });
  });

  describe("fare comparison", () => {
    it("adds fares (enums + JPY-string validated), lists with cheapest highlight", async () => {
      expect((await addFare(e, { fareId: "F-1", fromStation: "Tokyo", toStation: "Shin-Osaka", fareType: "regular", seatClass: "ordinary", priceJpy: "14720", platform: "jr" })).status).toBe("added");
      await addFare(e, { fareId: "F-2", fromStation: "Tokyo", toStation: "Shin-Osaka", fareType: "early-bird", seatClass: "ordinary", priceJpy: "11000", discountName: "EX早特", platform: "smartex" });
      await addFare(e, { fareId: "F-3", fromStation: "Tokyo", toStation: "Shin-Osaka", fareType: "regular", seatClass: "green", priceJpy: "19590", platform: "jr" });
      expect((await addFare(e, { fareId: "F-X", fromStation: "a", toStation: "b", fareType: "regular", seatClass: "first" as any, priceJpy: "1", platform: "jr" })).status).toBe("rejected"); // seatClass
      expect((await addFare(e, { fareId: "F-F", fromStation: "a", toStation: "b", fareType: "regular", seatClass: "ordinary", priceJpy: "100.5", platform: "jr" })).status).toBe("rejected"); // price float-string
      const ordinary = await listFares(e, { fromStation: "Tokyo", toStation: "Shin-Osaka", seatClass: "ordinary" });
      expect(ordinary.total).toBe(2);
      expect(ordinary.cheapest?.fareId).toBe("F-2"); // 11000 < 14720
      expect((await listFares(e, { platform: "smartex" })).total).toBe(1);
    });
  });

  describe("operation status + coverage", () => {
    beforeEach(async () => {
      await registerLine(e, { lineId: "tokaido", name: "東海道新幹線", operator: "JR-Central" });
    });
    it("records operation (FK→line, status + uint delay), lists, coverage rolls up", async () => {
      expect((await recordOperation(e, { operationId: "O-1", lineId: "tokaido", status: "delayed", delayMinutes: 25, reason: "強風", observedAt: "2026-06-01T09:00:00Z" })).status).toBe("recorded");
      expect((await recordOperation(e, { operationId: "O-X", lineId: "tokaido", status: "exploded" as any, observedAt: "x" })).status).toBe("rejected"); // status
      expect((await recordOperation(e, { operationId: "O-F", lineId: "tokaido", status: "delayed", delayMinutes: 2.5 as any, observedAt: "x" })).status).toBe("rejected"); // float
      expect((await listOperations(e, { lineId: "tokaido", status: "delayed" })).total).toBe(1);
      await addTimetable(e, { entryId: "T-1", lineId: "tokaido", trainNumber: "N1", trainType: "Nozomi", departureStation: "Tokyo", arrivalStation: "Shin-Osaka", departTime: "06:00", arriveTime: "08:27" });
      await addFare(e, { fareId: "F-1", fromStation: "Tokyo", toStation: "Shin-Osaka", fareType: "regular", seatClass: "green", priceJpy: "19590", platform: "jr" });
      const cov = await coverage(e);
      expect(cov.lineCount).toBe(1);
      expect(cov.timetableCount).toBe(1);
      expect(cov.fareCount).toBe(1);
      expect(cov.operationCount).toBe(1);
      expect(cov.faresBySeatClass?.green).toBe(1);
    });
  });
});
