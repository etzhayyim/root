/**
 * Shinkansen — Bullet train reservation intelligence agent.
 *
 * Covers: SmartEX / EX-IC / ekinet reservation, timetable search,
 * fare comparison (regular/early-bird/Green/reserved/unreserved),
 * seat selection, real-time operation status (delay/suspension/transfer).
 *
 * Data path (kagami):
 *   Write: sdk.pds.dispatch -> PDS -> kagami CF Worker -> RisingWave (P10v2 GraphAr)
 *   Read:  createKyselyDb (Hyperdrive) -> RisingWave (P10v2 GraphAr typed columns)
 *
 * Actor composition (Multi-DID):
 *   :actor:smartex      (3339)  -- SmartEX reservation proxy
 *   :actor:ekinet       (3339)  -- ekinet reservation proxy
 *   :actor:availability (4222)  -- seat availability checker
 *   :actor:fare         (3313)  -- fare comparison engine
 *   :actor:timetable    (2120)  -- timetable search
 *   :actor:operation    (4323)  -- real-time operation status
 *   :actor:seat         (5223)  -- seat assignment optimizer
 */
import {
  createWorkerExport,
  asAgentTool,
  withCapabilityTags,
  withOCELEvent,
  resolveHeartbeatCadence,
  createCadenceState,
  createInboxBuffer,
  createKyselyDb,
  sql,
  nowISO,
  str,
  num,
  decodeJson,
  type AppDef,
  type HostSDK,
  type ComAtprotoSyncSubscribeReposCommit,
} from "@etzhayyim/kotodama-host-sdk";

const APP_DEF: AppDef = {
  id: "sh1nk4n0",
  name: "Shinkansen",
  description: "Bullet train reservation intelligence — SmartEX / ekinet / timetable / fare / operation",
};

const A = {
  smartex: "did:web:shinkansen.etzhayyim.com:actor:smartex",
  ekinet: "did:web:shinkansen.etzhayyim.com:actor:ekinet",
  availability: "did:web:shinkansen.etzhayyim.com:actor:availability",
  fare: "did:web:shinkansen.etzhayyim.com:actor:fare",
  timetable: "did:web:shinkansen.etzhayyim.com:actor:timetable",
  operation: "did:web:shinkansen.etzhayyim.com:actor:operation",
  seat: "did:web:shinkansen.etzhayyim.com:actor:seat",
} as const;

const cadenceState = createCadenceState();
const inbox = createInboxBuffer();

type Row = Record<string, unknown>;

// ---------------------------------------------------------------------------
// Shinkansen Line Definitions
// ---------------------------------------------------------------------------

interface ShinkansenLine {
  lineId: string;
  name: string;
  nameEn: string;
  operator: string;
  terminals: [string, string];
}

const lines: ShinkansenLine[] = [
  { lineId: "tokaido", name: "東海道新幹線", nameEn: "Tokaido Shinkansen", operator: "JR東海", terminals: ["東京", "新大阪"] },
  { lineId: "sanyo", name: "山陽新幹線", nameEn: "Sanyo Shinkansen", operator: "JR西日本", terminals: ["新大阪", "博多"] },
  { lineId: "tohoku", name: "東北新幹線", nameEn: "Tohoku Shinkansen", operator: "JR東日本", terminals: ["東京", "新青森"] },
  { lineId: "joetsu", name: "上越新幹線", nameEn: "Joetsu Shinkansen", operator: "JR東日本", terminals: ["東京", "新潟"] },
  { lineId: "hokuriku", name: "北陸新幹線", nameEn: "Hokuriku Shinkansen", operator: "JR東日本/JR西日本", terminals: ["東京", "敦賀"] },
  { lineId: "kyushu", name: "九州新幹線", nameEn: "Kyushu Shinkansen", operator: "JR九州", terminals: ["博多", "鹿児島中央"] },
  { lineId: "hokkaido", name: "北海道新幹線", nameEn: "Hokkaido Shinkansen", operator: "JR北海道", terminals: ["新青森", "新函館北斗"] },
  { lineId: "nishi-kyushu", name: "西九州新幹線", nameEn: "Nishi-Kyushu Shinkansen", operator: "JR九州", terminals: ["武雄温泉", "長崎"] },
];

// ---------------------------------------------------------------------------
// Kysely query helpers
// ---------------------------------------------------------------------------

async function queryRows(
  table: string,
  match: Record<string, unknown>,
  columns: string[],
  opts?: { orderBy?: string; desc?: boolean; skip?: number; limit?: number },
): Promise<Row[]> {
  const db = createKyselyDb();
  let q = db.selectFrom(table as any).select(columns as any[]);
  for (const [k, v] of Object.entries(match)) {
    q = q.where(k as any, "=", v) as any;
  }
  if (opts?.orderBy) q = (opts.desc ? q.orderBy(opts.orderBy as any, "desc") : q.orderBy(opts.orderBy as any)) as any;
  if (opts?.skip) q = q.offset(opts.skip) as any;
  if (opts?.limit) q = q.limit(opts.limit) as any;
  return (await q.execute()) as Row[];
}

async function countRows(table: string, match: Record<string, unknown>): Promise<number> {
  const db = createKyselyDb();
  let q = db.selectFrom(table as any).select(sql<number>`count(*)`.as("count"));
  for (const [k, v] of Object.entries(match)) {
    q = q.where(k as any, "=", v) as any;
  }
  const r = await q.executeTakeFirstOrThrow();
  return Number(r.count);
}

// ---------------------------------------------------------------------------
// App export
// ---------------------------------------------------------------------------

export default createWorkerExport((sdk) => {
  // ── Queries ──

  sdk.app.query(
    "com.etzhayyim.apps.shinkansen.searchRoute",
    asAgentTool(
      withCapabilityTags(["timetable-search"])(
        withOCELEvent("shinkansen:searchRoute")(async (input: { from: string; to: string; date: string; time?: string }) => {
          const rows = await queryRows(
            "graphar.vertex_ShinkansenTimetable",
            { departure_station: input.from, arrival_station: input.to },
            ["train_number", "train_type", "departure_station", "arrival_station", "departure_time", "arrival_time", "line_id", "duration_minutes"],
            { orderBy: "departure_time", limit: 20 },
          );
          return { routes: rows, count: rows.length };
        }),
      ),
      { name: "searchRoute", description: "Search shinkansen train routes. Params: from (departure station, e.g. '東京'), to (arrival station, e.g. '新大阪'), date (YYYY-MM-DD), time (optional, HH:MM preferred departure). Returns candidate trains with times and duration." },
    ),
  );

  sdk.app.query(
    "com.etzhayyim.apps.shinkansen.checkAvailability",
    asAgentTool(
      withCapabilityTags(["timetable-search"])(
        withOCELEvent("shinkansen:checkAvailability")(async (input: { trainNumber: string; date: string; seatClass?: string }) => {
          const rows = await queryRows(
            "graphar.vertex_ShinkansenAvailability",
            { train_number: input.trainNumber, date: input.date },
            ["train_number", "date", "seat_class", "available_count", "status"],
          );
          return { availability: rows };
        }),
      ),
      { name: "checkAvailability", description: "Check seat availability for a specific train. Params: trainNumber (e.g. 'のぞみ1号'), date (YYYY-MM-DD), seatClass (optional: 'ordinary'|'green'|'unreserved'). Call this AFTER searchRoute to verify seats." },
    ),
  );

  sdk.app.query(
    "com.etzhayyim.apps.shinkansen.compareFare",
    asAgentTool(
      withCapabilityTags(["fare-comparison"])(
        withOCELEvent("shinkansen:compareFare")(async (input: { from: string; to: string; date: string; seatClass?: string }) => {
          const seatClass = input.seatClass ?? "ordinary";
          const rows = await queryRows(
            "graphar.vertex_ShinkansenFare",
            { departure_station: input.from, arrival_station: input.to },
            ["fare_type", "seat_class", "price", "currency", "discount_name", "valid_from", "valid_to", "platform"],
          );
          const filtered = rows.filter((r) => !seatClass || r.seat_class === seatClass);
          return { fares: filtered, cheapest: filtered.sort((a, b) => num(a.price) - num(b.price))[0] ?? null };
        }),
      ),
      { name: "compareFare", description: "Compare ticket fares across platforms and discount types. Params: from (departure station), to (arrival station), date (YYYY-MM-DD), seatClass (optional: 'ordinary'|'green'|'unreserved'). Returns fare list sorted by price with cheapest highlighted." },
    ),
  );

  sdk.app.query(
    "com.etzhayyim.apps.shinkansen.getReservation",
    asAgentTool(
      withCapabilityTags(["reservation-management"])(
        withOCELEvent("shinkansen:getReservation")(async (input: { reservationId: string }) => {
          const rows = await queryRows(
            "graphar.vertex_ShinkansenReservation",
            { reservation_id: input.reservationId },
            ["reservation_id", "user_did", "train_number", "departure_station", "arrival_station", "depart_date", "depart_time", "seat_class", "seat_number", "car_number", "fare", "platform", "status", "created_at"],
          );
          return rows[0] ?? { error: "not found" };
        }),
      ),
      { name: "getReservation", description: "Get reservation details. Params: reservationId (e.g. 'rsv-xxx'). Returns train, date, time, seat, fare, status." },
    ),
  );

  sdk.app.query(
    "com.etzhayyim.apps.shinkansen.listReservations",
    asAgentTool(
      withCapabilityTags(["reservation-management"])(
        withOCELEvent("shinkansen:listReservations")(async (input: { userDid?: string; status?: string; offset?: number; limit?: number }) => {
          const match: Record<string, unknown> = {};
          if (input.userDid) match.user_did = input.userDid;
          if (input.status) match.status = input.status;
          const limit = input.limit ?? 20;
          const offset = input.offset ?? 0;
          const rows = await queryRows(
            "graphar.vertex_ShinkansenReservation",
            match,
            ["reservation_id", "train_number", "departure_station", "arrival_station", "depart_date", "seat_class", "fare", "platform", "status", "created_at"],
            { orderBy: "created_at", desc: true, skip: offset, limit },
          );
          return { reservations: rows, offset, limit };
        }),
      ),
      { name: "listReservations", description: "List user's reservations. Params: userDid (optional, auto-resolved from convo), status (optional: 'confirmed'|'cancelled'), offset, limit. Use this when user says '予約一覧' or '予約確認'." },
    ),
  );

  sdk.app.query(
    "com.etzhayyim.apps.shinkansen.getOperation",
    asAgentTool(
      withCapabilityTags(["operation-status"])(
        withOCELEvent("shinkansen:getOperation")(async (input: { lineId?: string }) => {
          const match: Record<string, unknown> = {};
          if (input.lineId) match.line_id = input.lineId;
          const rows = await queryRows(
            "graphar.vertex_ShinkansenOperation",
            match,
            ["line_id", "line_name", "status", "detail", "cause", "affected_section", "estimated_recovery", "updated_at"],
            { orderBy: "updated_at", desc: true, limit: 20 },
          );
          return { operations: rows };
        }),
      ),
      { name: "getOperation", description: "Get real-time operation status (delays, suspensions). Params: lineId (optional, e.g. 'tokaido'). Call this BEFORE booking if user mentions delays or 運行情報. Also call proactively if booking Tokaido during typhoon season." },
    ),
  );

  sdk.app.query(
    "com.etzhayyim.apps.shinkansen.listLines",
    asAgentTool(
      withCapabilityTags(["timetable-search"])(
        withOCELEvent("shinkansen:listLines")(async () => {
          return { lines };
        }),
      ),
      { name: "listLines", description: "List all 8 shinkansen lines with operators and terminal stations. Call this when user is unsure which line to take or asks about available routes." },
    ),
  );

  // ── Commands (Tier 2 Domain write) ──

  sdk.app.command(
    "com.etzhayyim.apps.shinkansen.createReservation",
    asAgentTool(
      withCapabilityTags(["reservation-management"])(
        withOCELEvent("shinkansen:createReservation")(async (input: {
          trainNumber: string;
          departureStation: string;
          arrivalStation: string;
          departDate: string;
          departTime: string;
          seatClass: string;
          carNumber?: number;
          seatPreference?: string;
          platform: string;
          userDid: string;
        }) => {
          const reservationId = `rsv-${Date.now().toString(36)}`;
          await createKyselyDb().insertInto("vertex_shinkansen_reservation" as any).values({
            vertex_id: `at://${A.smartex}/com.etzhayyim.apps.shinkansen.reservation/${reservationId}`,
            sensitivity_ord: 2,
            owner_did: A.smartex,
            reservation_id: reservationId,
            user_did: input.userDid,
            train_number: input.trainNumber,
            departure_station: input.departureStation,
            arrival_station: input.arrivalStation,
            depart_date: input.departDate,
            depart_time: input.departTime,
            seat_class: input.seatClass,
            car_number: input.carNumber ?? null,
            seat_preference: input.seatPreference ?? "window",
            platform: input.platform,
            status: "confirmed",
            created_at: nowISO(),
            actor_id: APP_DEF.id,
          }).execute();
          return { reservationId, status: "confirmed" };
        }),
      ),
      { name: "createReservation", description: "Book a shinkansen ticket. Params: trainNumber (e.g. 'のぞみ1号'), departureStation, arrivalStation, departDate (YYYY-MM-DD), departTime (HH:MM), seatClass ('ordinary'|'green'|'unreserved'), platform ('smartex'|'ekinet'), userDid (caller DID, auto-resolved from convo context), carNumber (optional), seatPreference (optional: 'window'|'aisle'). Call AFTER searchRoute + compareFare + user confirmation." },
    ),
  );

  sdk.app.command(
    "com.etzhayyim.apps.shinkansen.cancelReservation",
    asAgentTool(
      withCapabilityTags(["reservation-management"])(
        withOCELEvent("shinkansen:cancelReservation")(async (input: { reservationId: string; reason?: string }) => {
          await createKyselyDb().insertInto("vertex_shinkansen_reservation" as any).values({
            vertex_id: `at://${A.smartex}/com.etzhayyim.apps.shinkansen.reservation/cancel-${input.reservationId}`,
            sensitivity_ord: 2,
            owner_did: A.smartex,
            reservation_id: input.reservationId,
            status: "cancelled",
            cancel_reason: input.reason ?? "",
            cancelled_at: nowISO(),
            actor_id: APP_DEF.id,
          }).execute();
          return { reservationId: input.reservationId, status: "cancelled" };
        }),
      ),
      { name: "cancelReservation", description: "Cancel a reservation. Params: reservationId, reason (optional). Use when user says キャンセル or 'cancel my booking'." },
    ),
  );

  sdk.app.command(
    "com.etzhayyim.apps.shinkansen.selectSeat",
    asAgentTool(
      withCapabilityTags(["reservation-management"])(
        withOCELEvent("shinkansen:selectSeat")(async (input: { reservationId: string; carNumber: number; seatNumber: string }) => {
          await createKyselyDb().insertInto("vertex_shinkansen_reservation" as any).values({
            vertex_id: `at://${A.seat}/com.etzhayyim.apps.shinkansen.reservation/seat-${input.reservationId}`,
            sensitivity_ord: 2,
            owner_did: A.seat,
            reservation_id: input.reservationId,
            car_number: input.carNumber,
            seat_number: input.seatNumber,
            updated_at: nowISO(),
            actor_id: APP_DEF.id,
          }).execute();
          return { reservationId: input.reservationId, carNumber: input.carNumber, seatNumber: input.seatNumber };
        }),
      ),
      { name: "selectSeat", description: "Choose a specific seat after booking. Params: reservationId, carNumber (1-16), seatNumber (e.g. '3A' window, '3C' aisle). Nozomi: cars 1-3 unreserved, 4-7 reserved, 8-10 Green, 11-16 reserved." },
    ),
  );

  sdk.app.command(
    "com.etzhayyim.apps.shinkansen.reportOperation",
    asAgentTool(
      withCapabilityTags(["operation-status"])(
        withOCELEvent("shinkansen:reportOperation")(async (input: {
          lineId: string;
          status: string;
          detail: string;
          cause?: string;
          affectedSection?: string;
          estimatedRecovery?: string;
        }) => {
          const line = lines.find((l) => l.lineId === input.lineId);
          const opRkey = `op-${input.lineId}-${Date.now().toString(36)}`;
          await createKyselyDb().insertInto("vertex_shinkansen_operation" as any).values({
            vertex_id: `at://${A.operation}/com.etzhayyim.apps.shinkansen.operation/${opRkey}`,
            sensitivity_ord: 2,
            owner_did: A.operation,
            line_id: input.lineId,
            line_name: line?.name ?? input.lineId,
            status: input.status,
            detail: input.detail,
            cause: input.cause ?? "",
            affected_section: input.affectedSection ?? "",
            estimated_recovery: input.estimatedRecovery ?? "",
            updated_at: nowISO(),
            actor_id: APP_DEF.id,
          }).execute();
          return { lineId: input.lineId, status: input.status };
        }),
      ),
      { name: "reportOperation", description: "Report operation status update for a line. Params: lineId (e.g. 'tokaido'), status ('normal'|'delay'|'suspended'), detail, cause (optional), affectedSection (optional), estimatedRecovery (optional)." },
    ),
  );

  sdk.app.command(
    "com.etzhayyim.apps.shinkansen.seedTimetable",
    asAgentTool(
      withCapabilityTags(["timetable-search"])(
        withOCELEvent("shinkansen:seedTimetable")(async (input: { lineId: string }) => {
          const line = lines.find((l) => l.lineId === input.lineId);
          if (!line) return { error: `unknown line: ${input.lineId}` };
          await createKyselyDb().insertInto("vertex_shinkansen_timetable" as any).values({
            vertex_id: `at://${A.timetable}/com.etzhayyim.apps.shinkansen.timetable/${line.lineId}`,
            sensitivity_ord: 2,
            owner_did: A.timetable,
            line_id: line.lineId,
            line_name: line.name,
            operator: line.operator,
            terminals: JSON.stringify(line.terminals),
            seeded_at: nowISO(),
            actor_id: APP_DEF.id,
          }).execute();
          return { lineId: line.lineId, status: "seeded" };
        }),
      ),
      { name: "seedTimetable", description: "Seed timetable reference data for a line. Params: lineId (e.g. 'tokaido'). Admin use — populates timetable graph." },
    ),
  );

  // ── HandleStream (wRPC output) ──

  sdk.app.handleStream("stream-operations", async function* () {
    const rows = await queryRows(
      "graphar.vertex_ShinkansenOperation",
      {},
      ["line_id", "line_name", "status", "detail", "updated_at"],
      { orderBy: "updated_at", desc: true, limit: 50 },
    );
    for (const row of rows) yield row;
  }, { requireCallerRole: "subscriber" });

  // ── ComAtprotoSyncSubscribeRepos: reactive pipeline entry ──

  sdk.app.onCommit(handleComAtprotoSyncSubscribeReposCommit);

  // ── Shinka heartbeat ──

  sdk.app.onHeartbeat(async () => {
    const cadence = resolveHeartbeatCadence(cadenceState, inbox);
    return { nextMs: cadence.nextMs };
  });
});

// ---------------------------------------------------------------------------
// Reactive commit handler (CRITICAL — no empty handler)
// ---------------------------------------------------------------------------

async function handleComAtprotoSyncSubscribeReposCommit(
  commit: ComAtprotoSyncSubscribeReposCommit,
  sdk: HostSDK,
) {
  if (commit.action !== "create") return;

  // Calendar event -> auto-suggest reservation
  if (commit.collection === "com.etzhayyim.apps.calendar.event") {
    const record = decodeJson(commit.recordJson);
    const title = str(record.title ?? record.summary ?? "");
    if (title.includes("新幹線") || title.includes("shinkansen") || title.includes("出張")) {
      await sdk.pds.dispatch({
        type: "app.bsky.feed.post",
        did: A.smartex,
        payload: {
          text: `Travel event detected: "${title}". Use /shinkansen searchRoute to find trains.`,
        },
      });
    }
    return;
  }

  // Operation status change -> social post (derive rule backup)
  if (commit.collection === "com.etzhayyim.apps.shinkansen.operation") {
    const record = decodeJson(commit.recordJson);
    const status = str(record.status ?? "");
    if (status === "delay" || status === "suspended") {
      await sdk.pds.dispatch({
        type: "app.bsky.feed.post",
        did: A.operation,
        payload: {
          text: `${str(record.lineName)} ${status}: ${str(record.detail)}`,
        },
      });
    }
    return;
  }
}
