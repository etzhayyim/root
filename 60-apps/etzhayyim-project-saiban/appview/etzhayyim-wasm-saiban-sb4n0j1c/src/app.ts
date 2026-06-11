import {
  asAgentTool,
  decodeJson,
  createKyselyDb,
  nowISO,
  str,
  withCapabilityTags,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK,
  createWorkerExport,
  resolveHeartbeatCadence,
  createCadenceState,
  createInboxBuffer,
  genID,
  nsid,
} from "@etzhayyim/kotodama-host-sdk";

type AnyRow = Record<string, unknown>;
type KyselyDb = ReturnType<typeof createKyselyDb>;

let appId = "";
let actorDID = "";
let db: KyselyDb | null = null;

function getDb(): KyselyDb {
  if (!db) db = createKyselyDb();
  return db;
}

// ---------------------------------------------------------------------------
// Court Definitions (JP 8 + USA 5 + UK 6 + DE 8 + FR 6 = 33)
// ---------------------------------------------------------------------------

interface CourtDef {
  path: string;
  nameJa: string;
  nameEn: string;
  level: string;
  jurisdiction: string;
  did: string;
}

const courts: CourtDef[] = [
  // --- Japan ---
  { path: "court:summary", nameJa: "簡易裁判所", nameEn: "Summary Courts", level: "summary", jurisdiction: "jpn", did: "" },
  { path: "court:district", nameJa: "地方裁判所", nameEn: "District Courts", level: "district", jurisdiction: "jpn", did: "" },
  { path: "court:family", nameJa: "家庭裁判所", nameEn: "Family Courts", level: "family-court", jurisdiction: "jpn", did: "" },
  { path: "court:high", nameJa: "高等裁判所", nameEn: "High Courts", level: "high", jurisdiction: "jpn", did: "" },
  { path: "court:supreme", nameJa: "最高裁判所", nameEn: "Supreme Court", level: "supreme", jurisdiction: "jpn", did: "" },
  { path: "court:administrative", nameJa: "行政裁判所", nameEn: "Administrative Court", level: "administrative-court", jurisdiction: "jpn", did: "" },
  { path: "court:arbitration", nameJa: "仲裁機関", nameEn: "Arbitration", level: "arbitration", jurisdiction: "jpn", did: "" },
  { path: "court:mediation", nameJa: "調停機関", nameEn: "Mediation", level: "mediation", jurisdiction: "jpn", did: "" },
  // --- USA ---
  { path: "court:usa:scotus", nameJa: "米国最高裁判所", nameEn: "US Supreme Court", level: "supreme", jurisdiction: "usa", did: "" },
  { path: "court:usa:circuit", nameJa: "米国巡回控訴裁判所", nameEn: "US Circuit Courts of Appeals", level: "high", jurisdiction: "usa", did: "" },
  { path: "court:usa:district", nameJa: "米国連邦地方裁判所", nameEn: "US District Courts", level: "district", jurisdiction: "usa", did: "" },
  { path: "court:usa:bankruptcy", nameJa: "米国破産裁判所", nameEn: "US Bankruptcy Courts", level: "district", jurisdiction: "usa", did: "" },
  { path: "court:usa:tax", nameJa: "米国租税裁判所", nameEn: "US Tax Court", level: "district", jurisdiction: "usa", did: "" },
  // --- UK ---
  { path: "court:gbr:uksc", nameJa: "英国最高裁判所", nameEn: "UK Supreme Court", level: "supreme", jurisdiction: "gbr", did: "" },
  { path: "court:gbr:appeal", nameJa: "控訴院", nameEn: "Court of Appeal", level: "high", jurisdiction: "gbr", did: "" },
  { path: "court:gbr:high", nameJa: "高等法院", nameEn: "High Court", level: "high", jurisdiction: "gbr", did: "" },
  { path: "court:gbr:crown", nameJa: "刑事法院", nameEn: "Crown Court", level: "district", jurisdiction: "gbr", did: "" },
  { path: "court:gbr:magistrates", nameJa: "治安判事裁判所", nameEn: "Magistrates' Courts", level: "summary", jurisdiction: "gbr", did: "" },
  { path: "court:gbr:tribunal", nameJa: "審判所", nameEn: "First-tier Tribunal", level: "administrative-court", jurisdiction: "gbr", did: "" },
  // --- Germany ---
  { path: "court:deu:bverfg", nameJa: "連邦憲法裁判所", nameEn: "Bundesverfassungsgericht", level: "supreme", jurisdiction: "deu", did: "" },
  { path: "court:deu:bgh", nameJa: "連邦通常裁判所", nameEn: "Bundesgerichtshof", level: "supreme", jurisdiction: "deu", did: "" },
  { path: "court:deu:bverwg", nameJa: "連邦行政裁判所", nameEn: "Bundesverwaltungsgericht", level: "supreme", jurisdiction: "deu", did: "" },
  { path: "court:deu:bag", nameJa: "連邦労働裁判所", nameEn: "Bundesarbeitsgericht", level: "supreme", jurisdiction: "deu", did: "" },
  { path: "court:deu:bsg", nameJa: "連邦社会裁判所", nameEn: "Bundessozialgericht", level: "supreme", jurisdiction: "deu", did: "" },
  { path: "court:deu:bfh", nameJa: "連邦財政裁判所", nameEn: "Bundesfinanzhof", level: "supreme", jurisdiction: "deu", did: "" },
  { path: "court:deu:lg", nameJa: "地方裁判所", nameEn: "Landgericht", level: "district", jurisdiction: "deu", did: "" },
  { path: "court:deu:ag", nameJa: "区裁判所", nameEn: "Amtsgericht", level: "summary", jurisdiction: "deu", did: "" },
  // --- France ---
  { path: "court:fra:cc", nameJa: "憲法院", nameEn: "Conseil constitutionnel", level: "supreme", jurisdiction: "fra", did: "" },
  { path: "court:fra:cass", nameJa: "破毀院", nameEn: "Cour de cassation", level: "supreme", jurisdiction: "fra", did: "" },
  { path: "court:fra:ce", nameJa: "国務院", nameEn: "Conseil d'État", level: "supreme", jurisdiction: "fra", did: "" },
  { path: "court:fra:ca", nameJa: "控訴院", nameEn: "Cour d'appel", level: "high", jurisdiction: "fra", did: "" },
  { path: "court:fra:tgi", nameJa: "司法裁判所", nameEn: "Tribunal judiciaire", level: "district", jurisdiction: "fra", did: "" },
  { path: "court:fra:ta", nameJa: "行政裁判所", nameEn: "Tribunal administratif", level: "administrative-court", jurisdiction: "fra", did: "" },
];

// ---------------------------------------------------------------------------
// Write helpers
// ---------------------------------------------------------------------------

// writeRecordAs remains for path-based DID court registrations (social/AT layer).
function writeRecordAs(sdk: HostSDK, did: string, collection: string, recordJson: string): void {
  sdk.pds.dispatch({ type: "com.atproto.repo.createRecordAs", payload: { did, collection, recordJson } });
}

// ---------------------------------------------------------------------------
// Commands — Court Registration
// ---------------------------------------------------------------------------

async function cmdRegisterCourtProfiles(sdk: HostSDK, _payload: Uint8Array): Promise<unknown> {
  const results: Record<string, unknown>[] = [];
  for (const c of courts) {
    const did = str(sdk.hostImports.comAtprotoIdentityCreate(c.path, JSON.stringify({
      displayName: c.nameEn,
      description: `${c.nameEn} — ${c.nameJa}`,
      category: "court",
      country: c.jurisdiction,
    })));
    if (did) c.did = did;
    const courtId = c.path.replace("court:", "");
    const vertexId = `at://${actorDID}/com.etzhayyim.apps.saiban.court/${courtId.replace(/:/g, "-")}`;
    await getDb().insertInto("vertex_saiban_court" as any).values({
      vertex_id: vertexId,
      court_id: courtId,
      name_ja: c.nameJa,
      name_en: c.nameEn,
      court_level: c.level,
      jurisdiction: c.jurisdiction,
      court_did: did || c.did || null,
      status: "active",
      actor_did: did || actorDID,
      org_did: "anon",
      created_at: nowISO(),
    }).execute();
    results.push({ path: c.path, nameEn: c.nameEn, jurisdiction: c.jurisdiction, did: did || c.did });
  }
  return { courts: results, total: results.length };
}

// ---------------------------------------------------------------------------
// Commands — Jiken (Case) Management
// ---------------------------------------------------------------------------

async function cmdCreateJiken(sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const id = genID();
  const caseType = str(req.caseType) || "civil";
  const courtId = str(req.courtId) || "";
  const title = str(req.title) || "";
  const did = str(sdk.hostImports.comAtprotoIdentityCreate(`jiken:${id}`, JSON.stringify({
    displayName: title || `${caseType} case ${id}`,
    description: `Jiken ${caseType} at ${courtId}`,
    category: "jiken",
  })));
  const now = nowISO();
  await getDb().insertInto("vertex_saiban_jiken" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.saiban.jiken/${id}`,
    jiken_id: id,
    jiken_did: did || null,
    case_number: str(req.caseNumber) || "",
    case_type: caseType,
    status: "filed",
    court_id: courtId,
    court_level: str(req.courtLevel) || "",
    judge_id: str(req.judgeId) || "",
    title,
    plaintiff: str(req.plaintiff) || "",
    defendant: str(req.defendant) || "",
    filed_at: str(req.filedAt) || now,
    lawfirm_case_id: str(req.lawfirmCaseId) || "",
    hanrei_rkey: "",
    actor_did: actorDID,
    org_did: "anon",
    created_at: now,
    updated_at: now,
  }).execute();
  // Cross-actor: notify hanrei to link case law
  if (title) {
    sdk.pds.dispatch({ type: "kotodama.invoke", payload: {
      did: "did:web:hanrei.etzhayyim.com",
      method: "com.etzhayyim.hanrei.searchCases",
      params: JSON.stringify({ query: title, caseType }),
    }});
  }
  // Cross-actor: notify lawfirm if linked
  const lawfirmCaseId = str(req.lawfirmCaseId);
  if (lawfirmCaseId) {
    sdk.pds.dispatch({ type: "kotodama.invoke", payload: {
      did: "did:web:lawfirm.etzhayyim.com",
      method: "com.etzhayyim.apps.lawfirm.notifyLinkedCase",
      params: JSON.stringify({ jikenId: id, lawfirmCaseId }),
    }});
  }
  return { id, did, caseType, status: "filed" };
}

async function cmdGetJiken(_sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const id = str(req.id);
  const rows = await getDb()
    .selectFrom("vertex_saiban_jiken" as any)
    .selectAll()
    .where("jiken_id" as any, "=", id)
    .limit(1)
    .execute();
  return rows.length > 0 ? rows : [];
}

async function cmdSearchJiken(_sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const query = str(req.query) || "";
  const caseType = str(req.caseType) || "";
  const offset = Number(req.offset) || 0;
  const limit = Math.min(Number(req.limit) || 50, 100);
  let q = getDb().selectFrom("vertex_saiban_jiken" as any).selectAll();
  if (caseType) q = q.where("case_type" as any, "=", caseType);
  const rows = await q.execute() as AnyRow[];
  const filtered = query
    ? rows.filter((row) => {
        return [str(row.case_number), str(row.title), str(row.jiken_id)].includes(query);
      })
    : rows;
  return filtered.slice(offset, offset + limit);
}

async function cmdUpdateJikenStatus(_sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const id = str(req.id);
  const status = str(req.status);
  const updatedAt = nowISO();
  await getDb().updateTable("vertex_saiban_jiken" as any)
    .set({ status, updated_at: updatedAt })
    .where("jiken_id" as any, "=", id)
    .execute();
  return { id, status, updatedAt };
}

async function cmdLinkJikenToHanrei(_sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const jikenId = str(req.jikenId) || str(req.rkey);
  const hanreiRkey = str(req.hanreiRkey);
  await getDb().updateTable("vertex_saiban_jiken" as any)
    .set({ hanrei_rkey: hanreiRkey, updated_at: nowISO() })
    .where("jiken_id" as any, "=", jikenId)
    .execute();
  return { jikenId, hanreiRkey, linked: true };
}

async function cmdLinkJikenToLawfirm(_sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const jikenId = str(req.jikenId);
  const lawfirmCaseId = str(req.lawfirmCaseId);
  await getDb().updateTable("vertex_saiban_jiken" as any)
    .set({ lawfirm_case_id: lawfirmCaseId, updated_at: nowISO() })
    .where("jiken_id" as any, "=", jikenId)
    .execute();
  return { jikenId, lawfirmCaseId, linked: true };
}

// ---------------------------------------------------------------------------
// Commands — Judge Registry (restricted)
// ---------------------------------------------------------------------------

async function cmdRegisterJudge(sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const id = genID();
  const did = str(sdk.hostImports.comAtprotoIdentityCreate(`judge:${id}`, JSON.stringify({
    displayName: str(req.nameEn) || str(req.nameJa) || `Judge ${id}`,
    description: "Judge profile (restricted)",
    category: "judge",
  })));
  const now = nowISO();
  await getDb().insertInto("vertex_saiban_judge" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.saiban.judge/${id}`,
    judge_id: id,
    judge_did: did || null,
    name_ja: str(req.nameJa) || "",
    name_en: str(req.nameEn) || "",
    current_court_id: str(req.courtId) || "",
    current_court_level: str(req.courtLevel) || "",
    status: "active",
    appointed_at: str(req.appointedAt) || "",
    actor_did: actorDID,
    org_did: "anon",
    created_at: now,
    updated_at: now,
  }).execute();
  return { id, did, status: "active" };
}

// ---------------------------------------------------------------------------
// Commands — Trial Events
// ---------------------------------------------------------------------------

async function cmdScheduleTrialEvent(sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const id = genID();
  const jikenId = str(req.jikenId);
  const eventType = str(req.eventType) || "hearing";
  const scheduledAt = str(req.scheduledAt) || "";
  await getDb().insertInto("vertex_saiban_trial_event" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.saiban.trialEvent/${id}`,
    event_id: id,
    jiken_id: jikenId,
    event_type: eventType,
    status: "scheduled",
    title: str(req.title) || "",
    court_id: str(req.courtId) || "",
    judge_id: str(req.judgeId) || "",
    scheduled_at: scheduledAt,
    location: str(req.location) || "",
    notes: str(req.notes) || "",
    next_event_date: "",
    actor_did: actorDID,
    org_did: "anon",
    created_at: nowISO(),
  }).execute();
  // Cross-actor: notify lawfirm of trial event
  if (jikenId) {
    sdk.pds.dispatch({ type: "kotodama.invoke", payload: {
      did: "did:web:lawfirm.etzhayyim.com",
      method: "com.etzhayyim.apps.lawfirm.notifyTrialEvent",
      params: JSON.stringify({ jikenId, eventType, scheduledAt }),
    }});
  }
  return { id, status: "scheduled" };
}

async function cmdListTrialEvents(_sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const jikenId = str(req.jikenId);
  const offset = Number(req.offset) || 0;
  const limit = Math.min(Number(req.limit) || 50, 100);
  let q = getDb().selectFrom("vertex_saiban_trial_event" as any).selectAll();
  if (jikenId) q = q.where("jiken_id" as any, "=", jikenId);
  const rows = await q.execute() as AnyRow[];
  return rows.slice(offset, offset + limit);
}

// ---------------------------------------------------------------------------
// Commands — Jurisdiction Mapping
// ---------------------------------------------------------------------------

async function cmdRegisterJurisdictionMap(_sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const id = genID();
  const courtId = str(req.courtId);
  // Serialize arrays as JSON strings for VARCHAR storage
  const prefectureCodes = Array.isArray(req.prefectureCodes)
    ? JSON.stringify(req.prefectureCodes)
    : "";
  const subjectMatter = Array.isArray(req.subjectMatter)
    ? JSON.stringify(req.subjectMatter)
    : "";
  const threshold = req.monetaryThresholdYen != null ? Number(req.monetaryThresholdYen) : null;
  await getDb().insertInto("vertex_saiban_jurisdiction_map" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.saiban.jurisdictionMap/${id}`,
    map_id: id,
    court_id: courtId,
    court_level: str(req.courtLevel) || "",
    region_code: str(req.regionCode) || "",
    region_name_ja: str(req.regionNameJa) || "",
    prefecture_codes: prefectureCodes,
    subject_matter: subjectMatter,
    monetary_threshold_yen: threshold,
    notes: str(req.notes) || "",
    actor_did: actorDID,
    org_did: "anon",
    created_at: nowISO(),
  }).execute();
  return { id, courtId };
}

async function cmdResolveJurisdiction(_sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const prefectureCode = str(req.prefectureCode) || "";
  const subjectMatter = str(req.subjectMatter) || "";
  const amount = Number(req.amount) || 0;
  const rows = await getDb()
    .selectFrom("vertex_saiban_jurisdiction_map" as any)
    .selectAll()
    .execute() as AnyRow[];
  // Filter in application layer: prefectureCodes and subjectMatter are JSON strings
  const filtered = rows.filter((row) => {
    let prefectureCodes: string[] = [];
    let subjectMatters: string[] = [];
    try { prefectureCodes = JSON.parse(str(row.prefecture_codes) || "[]") as string[]; } catch { /* empty */ }
    try { subjectMatters = JSON.parse(str(row.subject_matter) || "[]") as string[]; } catch { /* empty */ }
    const threshold = row.monetary_threshold_yen != null ? Number(row.monetary_threshold_yen) : null;
    if (prefectureCode && !prefectureCodes.includes(prefectureCode)) return false;
    if (subjectMatter && !subjectMatters.includes(subjectMatter)) return false;
    if (amount > 0 && threshold != null && threshold < amount) return false;
    return true;
  });
  return filtered.slice(0, 10);
}

// ---------------------------------------------------------------------------
// Commands — Court Queries
// ---------------------------------------------------------------------------

async function cmdListCourts(_sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const jurisdiction = str(req.jurisdiction) || "";
  const offset = Number(req.offset) || 0;
  const limit = Math.min(Number(req.limit) || 50, 100);
  let q = getDb().selectFrom("vertex_saiban_court" as any).selectAll();
  if (jurisdiction) q = q.where("jurisdiction" as any, "=", jurisdiction);
  const rows = await q.execute() as AnyRow[];
  return rows.slice(offset, offset + limit);
}

async function cmdGetCourt(_sdk: HostSDK, payload: Uint8Array): Promise<unknown> {
  const req = decodeJson<Record<string, unknown>>(payload, {});
  const courtId = str(req.courtId);
  const rows = await getDb()
    .selectFrom("vertex_saiban_court" as any)
    .selectAll()
    .where("court_id" as any, "=", courtId)
    .limit(1)
    .execute();
  return rows.length > 0 ? rows : [];
}

// ---------------------------------------------------------------------------
// ComAtprotoSyncSubscribeRepos — reactive pipeline
// ---------------------------------------------------------------------------

// ADR-0036: domain collections (com.etzhayyim.apps.saiban.*) no longer flow through the
// commit stream. Cross-actor notifications are dispatched inline in each command handler.
// This handler receives only social commits (app.bsky.*).
export async function handleComAtprotoSyncSubscribeReposCommit(
  _sdk: HostSDK,
  _commit: ComAtprotoSyncSubscribeReposCommit,
): Promise<{ ok: boolean }> {
  return { ok: true };
}

// ---------------------------------------------------------------------------
// Heartbeat
// ---------------------------------------------------------------------------

const cadenceState = createCadenceState();
const inboxBuf = createInboxBuffer();

export async function runHeartbeat(sdk: HostSDK): Promise<{ ok: boolean; actions: Array<Record<string, unknown>> }> {
  const actions: Array<Record<string, unknown>> = [];
  const ts = nowISO();
  const cadence = await resolveHeartbeatCadence(`did:web:${appId}.etzhayyim.com`, cadenceState, inboxBuf);
  actions.push({ action: "cadenceResolved", mood: cadence.mood, reason: cadence.reason, ts });
  if (actions.length === 1) actions.push({ action: "noop", mood: cadence.mood, ts });
  return { ok: true, actions };
}

// ---------------------------------------------------------------------------
// App Registration
// ---------------------------------------------------------------------------

function registerSaibanApp(sdk: HostSDK): void {
  sdk.app
    .command(nsid("com.etzhayyim.apps.saiban.registerCourtProfiles"), (_ctx, body) => cmdRegisterCourtProfiles(sdk, body),
      asAgentTool("Register all 33 court DIDs (JP+US+UK+DE+FR)"),
      withCapabilityTags("court", "did", "registration"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.listCourts"), (_ctx, body) => cmdListCourts(sdk, body),
      asAgentTool("List courts by jurisdiction"),
      withCapabilityTags("court", "query"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.getCourt"), (_ctx, body) => cmdGetCourt(sdk, body),
      asAgentTool("Get court by ID"),
      withCapabilityTags("court", "query"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.registerJudge"), (_ctx, body) => cmdRegisterJudge(sdk, body),
      asAgentTool("Register judge profile (restricted)"),
      withCapabilityTags("judge", "did", "registration"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.createJiken"), (_ctx, body) => cmdCreateJiken(sdk, body),
      asAgentTool("Create jiken (case) record"),
      withCapabilityTags("jiken", "create"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.getJiken"), (_ctx, body) => cmdGetJiken(sdk, body),
      asAgentTool("Get jiken by ID"),
      withCapabilityTags("jiken", "query"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.searchJiken"), (_ctx, body) => cmdSearchJiken(sdk, body),
      asAgentTool("Search jiken by title/case number/type"),
      withCapabilityTags("jiken", "search"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.updateJikenStatus"), (_ctx, body) => cmdUpdateJikenStatus(sdk, body),
      asAgentTool("Update jiken status"),
      withCapabilityTags("jiken", "update"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.linkJikenToHanrei"), (_ctx, body) => cmdLinkJikenToHanrei(sdk, body),
      asAgentTool("Link jiken to hanrei case law"),
      withCapabilityTags("jiken", "hanrei", "link"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.linkJikenToLawfirm"), (_ctx, body) => cmdLinkJikenToLawfirm(sdk, body),
      asAgentTool("Link jiken to lawfirm case"),
      withCapabilityTags("jiken", "lawfirm", "link"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.scheduleTrialEvent"), (_ctx, body) => cmdScheduleTrialEvent(sdk, body),
      asAgentTool("Schedule trial event"),
      withCapabilityTags("trial-event", "create"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.listTrialEvents"), (_ctx, body) => cmdListTrialEvents(sdk, body),
      asAgentTool("List trial events for jiken"),
      withCapabilityTags("trial-event", "query"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.registerJurisdictionMap"), (_ctx, body) => cmdRegisterJurisdictionMap(sdk, body),
      asAgentTool("Register jurisdiction mapping"),
      withCapabilityTags("jurisdiction", "registration"),
    )
    .command(nsid("com.etzhayyim.apps.saiban.resolveJurisdiction"), (_ctx, body) => cmdResolveJurisdiction(sdk, body),
      asAgentTool("Resolve court jurisdiction by location/subject/amount"),
      withCapabilityTags("jurisdiction", "resolve"),
    );
}

export default createWorkerExport((sdk) => {
  appId = sdk.pds.selfNanoid ?? "";
  actorDID = sdk.pds.selfRepo ?? "";
  registerSaibanApp(sdk);
});
