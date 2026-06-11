/**
 * Shinkansen Reservation Intelligence — Integration Tests
 * Tests: route search, availability check, fare comparison, reservation CRUD,
 *        operation status, line listing, reactive commit handler.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

let writtenRecords: Array<{ collection: string; record: Record<string, unknown> }> = [];
let postedTexts: string[] = [];

vi.mock("@etzhayyim/kotodama-host-sdk", () => ({
  createWorkerExport: (setup: (sdk: any) => void) => {
    const commands = new Map<string, (sdk: any, params: string) => Promise<string>>();
    const queries = new Map<string, (sdk: any, params: string) => Promise<string>>();
    let heartbeatFn: any = null;
    let commitFn: any = null;
    let streamFn: any = null;
    const mockSdk = {
      app: {
        command: (nsid: string, handler: any) => { commands.set(nsid, handler); },
        query: (nsid: string, handler: any) => { queries.set(nsid, handler); },
        onHeartbeat: (fn: any) => { heartbeatFn = fn; },
        onCommit: (fn: any) => { commitFn = fn; },
        handleStream: (name: string, fn: any, opts: any) => { streamFn = fn; },
      },
      pds: {
        dispatch: (action: any) => {
          if (action.type === "com.atproto.repo.createRecord") {
            const { collection, recordJson } = action.payload;
            writtenRecords.push({ collection, record: JSON.parse(recordJson) });
          } else if (action.type === "app.bsky.feed.post") {
            postedTexts.push(action.payload.text);
          }
        },
      },
      hostImports: {
        comAtprotoIdentityCreate: (slug: string) => `did:web:shinkansen.etzhayyim.com:${slug}`,
      },
    };
    setup(mockSdk);
    return { __mockSdk: mockSdk, __commands: commands, __queries: queries, __heartbeat: heartbeatFn, __commit: commitFn, __stream: streamFn };
  },
  asAgentTool: (fn: any, _meta: any) => {
    // Wrap: (input: T) => Promise<R> → (sdk: any, paramsJson: string) => Promise<string>
    return async (sdk: any, paramsJson: string) => {
      const input = JSON.parse(paramsJson || "{}");
      const result = await fn(input);
      return JSON.stringify(result);
    };
  },
  withCapabilityTags: (_tags: string[]) => (fn: any) => fn,
  withOCELEvent: (_tag: string) => (fn: any) => fn,
  resolveHeartbeatCadence: () => ({ nextMs: 60000 }),
  createCadenceState: () => ({}),
  createInboxBuffer: () => ({ inboundCommits: [], reactions: [] }),
  createKyselyDb: () => {
    const execute = (state: { table: string; filters: Array<[string, string, unknown]> }) => {
      // Return matching written records mapped to row shape
      const rows = writtenRecords
        .filter((entry) => {
          const tableLabel = state.table.replace("graphar.vertex_", "");
          return entry.collection.includes("shinkansen");
        })
        .map((entry) => entry.record)
        .filter((record) =>
          state.filters.every(([column, op, value]) => op === "=" ? record[column] === value : true),
        );
      return Promise.resolve(rows);
    };
    return {
      selectFrom(table: string) {
        const state = { table, filters: [] as Array<[string, string, unknown]> };
        const chain: any = {
          select(_cols: any) { return chain; },
          selectAll() { return chain; },
          where(column: string, op: string, value: unknown) {
            state.filters.push([column, op, value]);
            return chain;
          },
          orderBy() { return chain; },
          offset() { return chain; },
          limit() { return chain; },
          execute() { return execute(state); },
          executeTakeFirstOrThrow() {
            return execute(state).then((rows) => rows[0] ?? { count: 0 });
          },
        };
        return chain;
      },
    };
  },
  sql: (strings: TemplateStringsArray, ...values: any[]) => ({
    as: (_alias: string) => ({ count: 0 }),
  }),
  nowISO: () => "2026-04-13T00:00:00.000Z",
  str: (v: any) => String(v ?? ""),
  num: (v: any) => Number(v ?? 0),
  decodeJson: (s: string) => { try { return JSON.parse(s || "{}"); } catch { return {}; } },
}));

import appExport from "./app.js";
const { __commands: commands, __queries: queries, __mockSdk: sdk, __commit: commitFn } = appExport as any;

async function invokeCommand(nsid: string, params: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
  const handler = commands.get(nsid);
  if (!handler) throw new Error(`Command not found: ${nsid}`);
  return JSON.parse(await handler(sdk, JSON.stringify(params)));
}

async function invokeQuery(nsid: string, params: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
  const handler = queries.get(nsid);
  if (!handler) throw new Error(`Query not found: ${nsid}`);
  return JSON.parse(await handler(sdk, JSON.stringify(params)));
}

describe("Shinkansen Reservation Intelligence — Integration Tests", () => {
  beforeEach(() => { writtenRecords = []; postedTexts = []; });

  // ── Registration counts ──

  it("registers 5 XRPC commands", () => {
    expect(commands.size).toBe(5);
  });

  it("registers 7 XRPC queries", () => {
    expect(queries.size).toBe(7);
  });

  // ── Queries ──

  describe("Queries", () => {
    it("listLines returns all 8 shinkansen lines", async () => {
      const result = await invokeQuery("com.etzhayyim.apps.shinkansen.listLines");
      expect(result.lines).toBeDefined();
      expect(Array.isArray(result.lines)).toBe(true);
      const lines = result.lines as any[];
      expect(lines.length).toBe(8);
      const lineIds = lines.map((l: any) => l.lineId);
      expect(lineIds).toContain("tokaido");
      expect(lineIds).toContain("sanyo");
      expect(lineIds).toContain("tohoku");
      expect(lineIds).toContain("hokuriku");
      expect(lineIds).toContain("kyushu");
      expect(lineIds).toContain("hokkaido");
      expect(lineIds).toContain("nishi-kyushu");
      expect(lineIds).toContain("joetsu");
    });

    it("searchRoute returns routes array", async () => {
      const result = await invokeQuery("com.etzhayyim.apps.shinkansen.searchRoute", {
        from: "東京", to: "新大阪", date: "2026-04-20",
      });
      expect(result).toHaveProperty("routes");
      expect(result).toHaveProperty("count");
    });

    it("checkAvailability returns availability array", async () => {
      const result = await invokeQuery("com.etzhayyim.apps.shinkansen.checkAvailability", {
        trainNumber: "のぞみ1号", date: "2026-04-20",
      });
      expect(result).toHaveProperty("availability");
    });

    it("compareFare returns fares with cheapest", async () => {
      const result = await invokeQuery("com.etzhayyim.apps.shinkansen.compareFare", {
        from: "東京", to: "新大阪", date: "2026-04-20",
      });
      expect(result).toHaveProperty("fares");
      expect(result).toHaveProperty("cheapest");
    });

    it("getReservation returns not found for unknown ID", async () => {
      const result = await invokeQuery("com.etzhayyim.apps.shinkansen.getReservation", {
        reservationId: "nonexistent",
      });
      expect(result.error).toBe("not found");
    });

    it("listReservations returns with offset/limit", async () => {
      const result = await invokeQuery("com.etzhayyim.apps.shinkansen.listReservations", {});
      expect(result).toHaveProperty("reservations");
      expect(result).toHaveProperty("offset");
      expect(result).toHaveProperty("limit");
    });

    it("getOperation returns operations array", async () => {
      const result = await invokeQuery("com.etzhayyim.apps.shinkansen.getOperation", {});
      expect(result).toHaveProperty("operations");
    });
  });

  // ── Commands ──

  describe("Commands", () => {
    it("createReservation writes reservation record", async () => {
      const result = await invokeCommand("com.etzhayyim.apps.shinkansen.createReservation", {
        trainNumber: "のぞみ1号",
        departureStation: "東京",
        arrivalStation: "新大阪",
        departDate: "2026-04-20",
        departTime: "06:00",
        seatClass: "ordinary",
        platform: "smartex",
        userDid: "did:web:user.example.com",
      });
      expect(result.reservationId).toBeDefined();
      expect(result.status).toBe("confirmed");
      const written = writtenRecords.find((r) => r.collection === "com.etzhayyim.apps.shinkansen.reservation");
      expect(written).toBeDefined();
      expect(written!.record.trainNumber).toBe("のぞみ1号");
      expect(written!.record.departureStation).toBe("東京");
      expect(written!.record.arrivalStation).toBe("新大阪");
      expect(written!.record.platform).toBe("smartex");
      expect(written!.record.status).toBe("confirmed");
    });

    it("cancelReservation writes cancelled record", async () => {
      const result = await invokeCommand("com.etzhayyim.apps.shinkansen.cancelReservation", {
        reservationId: "rsv-test123",
        reason: "schedule change",
      });
      expect(result.status).toBe("cancelled");
      expect(result.reservationId).toBe("rsv-test123");
      const written = writtenRecords.find((r) => r.record.status === "cancelled");
      expect(written).toBeDefined();
      expect(written!.record.cancelReason).toBe("schedule change");
    });

    it("selectSeat writes seat assignment", async () => {
      const result = await invokeCommand("com.etzhayyim.apps.shinkansen.selectSeat", {
        reservationId: "rsv-test123",
        carNumber: 7,
        seatNumber: "3A",
      });
      expect(result.carNumber).toBe(7);
      expect(result.seatNumber).toBe("3A");
      const written = writtenRecords.find((r) => r.record.seatNumber === "3A");
      expect(written).toBeDefined();
    });

    it("reportOperation writes operation status", async () => {
      const result = await invokeCommand("com.etzhayyim.apps.shinkansen.reportOperation", {
        lineId: "tokaido",
        status: "delay",
        detail: "強風のため15分遅延",
        cause: "strong wind",
        affectedSection: "名古屋-新大阪",
      });
      expect(result.lineId).toBe("tokaido");
      expect(result.status).toBe("delay");
      const written = writtenRecords.find((r) => r.collection === "com.etzhayyim.apps.shinkansen.operation");
      expect(written).toBeDefined();
      expect(written!.record.lineName).toBe("東海道新幹線");
    });

    it("seedTimetable writes timetable record", async () => {
      const result = await invokeCommand("com.etzhayyim.apps.shinkansen.seedTimetable", {
        lineId: "tohoku",
      });
      expect(result.lineId).toBe("tohoku");
      expect(result.status).toBe("seeded");
      const written = writtenRecords.find((r) => r.collection === "com.etzhayyim.apps.shinkansen.timetable");
      expect(written).toBeDefined();
      expect(written!.record.lineName).toBe("東北新幹線");
    });

    it("seedTimetable returns error for unknown line", async () => {
      const result = await invokeCommand("com.etzhayyim.apps.shinkansen.seedTimetable", {
        lineId: "nonexistent",
      });
      expect(result.error).toContain("unknown line");
    });
  });

  // ── Reactive commit handler ──

  describe("Reactive Commit Handler", () => {
    it("calendar event with 出張 triggers social post", async () => {
      await commitFn(
        {
          action: "create",
          collection: "com.etzhayyim.apps.calendar.event",
          recordJson: JSON.stringify({ title: "大阪出張" }),
        },
        sdk,
      );
      expect(postedTexts.length).toBe(1);
      expect(postedTexts[0]).toContain("大阪出張");
    });

    it("calendar event with 新幹線 triggers social post", async () => {
      await commitFn(
        {
          action: "create",
          collection: "com.etzhayyim.apps.calendar.event",
          recordJson: JSON.stringify({ title: "新幹線で京都へ" }),
        },
        sdk,
      );
      expect(postedTexts.length).toBe(1);
      expect(postedTexts[0]).toContain("新幹線で京都へ");
    });

    it("calendar event without travel keywords does not post", async () => {
      await commitFn(
        {
          action: "create",
          collection: "com.etzhayyim.apps.calendar.event",
          recordJson: JSON.stringify({ title: "チーム定例" }),
        },
        sdk,
      );
      expect(postedTexts.length).toBe(0);
    });

    it("operation delay triggers social post", async () => {
      await commitFn(
        {
          action: "create",
          collection: "com.etzhayyim.apps.shinkansen.operation",
          recordJson: JSON.stringify({ lineName: "東海道新幹線", status: "delay", detail: "強風15分遅延" }),
        },
        sdk,
      );
      expect(postedTexts.length).toBe(1);
      expect(postedTexts[0]).toContain("東海道新幹線");
      expect(postedTexts[0]).toContain("delay");
    });

    it("operation normal status does not trigger social post", async () => {
      await commitFn(
        {
          action: "create",
          collection: "com.etzhayyim.apps.shinkansen.operation",
          recordJson: JSON.stringify({ lineName: "東海道新幹線", status: "normal", detail: "平常運転" }),
        },
        sdk,
      );
      expect(postedTexts.length).toBe(0);
    });

    it("ignores non-create actions", async () => {
      await commitFn(
        {
          action: "delete",
          collection: "com.etzhayyim.apps.shinkansen.operation",
          recordJson: JSON.stringify({ lineName: "東海道新幹線", status: "delay", detail: "test" }),
        },
        sdk,
      );
      expect(postedTexts.length).toBe(0);
    });
  });
});
