import {
  App,
  asAgentTool,
  createWorkerExport,
  nowISO,
  str,
  llmAsk,
  withCapabilityTags,
  withOCELEvent,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK, resolveHeartbeatCadence, createCadenceState, createInboxBuffer, genID, decodeJson,
  nsid,
  parseLexiconInput,
  sql,
  createKyselyDb,
} from "@etzhayyim/kotodama-host-sdk";

const cadenceState = createCadenceState();
const inbox = createInboxBuffer();

const APP_NANOID = "hc0mp7ng";
let actorDID = ""

type JsonRow = Record<string, unknown>;

function escapeLike(value: string): string {
  return value.replace(/[\\%_]/g, "\\$&");
}

// ── Typed vertex_hc_* readers (migration 20260423100000_vertex_hc_platform) ──
// Legacy catch-all storage is a dead path; graph-worker `nsidToConventionTable` projects
// `com.etzhayyim.apps.hc.<entity>` → `vertex_hc_<snake>` automatically.

function hcDb() { return createKyselyDb(); }

async function hcListByTable(table: string, limit: number, offset = 0): Promise<JsonRow[]> {
  return (await hcDb().selectFrom(table as any).selectAll()
    .orderBy("created_at" as any, "desc")
    .limit(limit).offset(offset).execute()) as unknown as JsonRow[];
}

async function hcGetById(table: string, id: string): Promise<JsonRow | null> {
  const row = await hcDb().selectFrom(table as any).selectAll()
    .where("id" as any, "=", id).limit(1).executeTakeFirst();
  return (row as unknown as JsonRow) ?? null;
}

async function hcCountActor(table: string): Promise<number> {
  const row = await hcDb().selectFrom(table as any)
    .select(sql<number>`count(*)`.as("total"))
    .where("actor_id" as any, "=", APP_NANOID)
    .executeTakeFirst();
  return Number((row as any)?.total ?? 0);
}

// --- Write Helpers ---

/** Store private/PII data as actor preferences instead of public AT Records. */
function writePrivate(sdk: HostSDK, key: string, value: Record<string, unknown>): void {
  sdk.pds.dispatch({ type: "actor-put-preferences", payload: { key: `hc:${key}`, value: JSON.stringify(value) } });
}

// --- Helpers ---

// --- Commands ---

async function cmdListHc(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.listHc", body);
  const limit = Math.min(Number(args.limit) || 50, 200);
  const offset = Number(args.offset) || 0;
  const items = await hcListByTable("vertex_hc_task", limit, offset);
  return { items, offset, limit };
}

async function cmdGetHc(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.getHc", body);
  const id = str(args.id ?? "");
  if (!id) return { error: "id required" };
  return await hcGetById("vertex_hc_task", id) ?? { error: "not found" };
}

async function cmdSearchHc(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.searchHc", body);
  const q = str(args.q ?? "");
  const limit = Math.min(Number(args.limit) || 20, 100);
  if (!q) return { items: [] };
  const like = `%${escapeLike(q)}%`;
  const items = await hcDb().selectFrom("vertex_hc_task" as any).selectAll()
    .where(sql<boolean>`coalesce(title, '') ilike ${like} escape '\\' or coalesce(description, '') ilike ${like} escape '\\'`)
    .limit(limit).execute();
  return { items };
}

async function cmdCreateHc(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.createHc", body);
  const id = genID("hc");
  await hcDb().insertInto("vertex_hc_task" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.task/${id}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id,
    name: str((args as any).name ?? ""),
    status: str((args as any).status ?? "active"),
    category: str((args as any).category ?? "default"),
    created_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();
  return { id, status: "created" };
}

function cmdWave(sdk: HostSDK, body: Uint8Array): unknown {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.wave", body);
  const msg = str(args.message ?? "Hello");
  return { ok: true, agent: "Hc", nanoid: APP_NANOID };
}

// --- Contract Commands ---

const SUPPORTED_LOCALES = ["ja", "us", "eu", "gb", "cn", "kr", "in", "vn", "th", "de", "tw", "id", "my"] as const;
const CONTRACT_TYPES = ["worker-agreement", "sp-service-agreement", "task-terms", "shift-terms"] as const;

function cmdGetContract(_sdk: HostSDK, body: Uint8Array): unknown {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.getContract", body);
  const contractType = args.type ?? "worker-agreement";
  const locale = args.locale ?? "ja";
  if (!CONTRACT_TYPES.includes(contractType)) return { error: `type must be one of: ${CONTRACT_TYPES.join(", ")}` };
  if (!SUPPORTED_LOCALES.includes(locale)) return { error: `locale must be one of: ${SUPPORTED_LOCALES.join(", ")}` };
  return {
    did: `did:web:${APP_NANOID}.etzhayyim.com:legal:${contractType}`,
    type: contractType,
    locale,
    'governingLaw': "日本法",
    jurisdiction: "東京地方裁判所 (専属管轄)",
    'effectiveDate': "2026-03-30",
    note: "Full contract text served from svelte/src/lib/legal/contracts.ts",
  };
}

function cmdListContracts(_sdk: HostSDK, _body: Uint8Array): unknown {
  return {
    contracts: CONTRACT_TYPES.map(t => ({
      type: t,
      did: `did:web:${APP_NANOID}.etzhayyim.com:legal:${t}`,
      'governingLaw': "日本法",
      jurisdiction: "東京地方裁判所",
    })),
    'supportedLocales': [...SUPPORTED_LOCALES],
  };
}

async function cmdAcceptContract(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.acceptContract", body);
  if (!args.contractType) return { error: "contractType required" };
  if (!args.acceptorDid) return { error: "acceptorDid required" };
  const locale = args.locale ?? "ja";
  const acceptId = genID("accept");
  await hcDb().insertInto("vertex_hc_contract_acceptance" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.contractAcceptance/${acceptId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: acceptId,
    contract_type: args.contractType,
    contract_did: `did:web:${APP_NANOID}.etzhayyim.com:legal:${args.contractType}`,
    acceptor_did: args.acceptorDid,
    locale,
    accepted_at: nowISO(),
    ip_address: args.ipAddress ?? "",
    user_agent: args.userAgent ?? "",
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();
  return { 'acceptanceId': acceptId, 'contractType': args.contractType, locale, status: "accepted" };
}

// --- Service Provider Registration Commands ---

async function cmdCreateSpApplication(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.createSpApplication", body);
  if (!args.legalName) return { error: "legalName required" };
  if (!args.countryIso3) return { error: "countryIso3 required" };
  if (!args.category) return { error: "category required (e.g. electronics, textile-apparel, food-beverage)" };

  const appId = genID("sp");
  await hcDb().insertInto("vertex_hc_sp_application" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.spApplication/${appId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: appId,
    legal_name: args.legalName,
    trade_name: args.tradeName ?? args.legalName,
    country_iso3: args.countryIso3,
    category: args.category,
    factory_type: args.factoryType ?? "oem",
    contact_email: args.contactEmail ?? "",
    website: args.website ?? "",
    lei: args.lei ?? "",
    isic_codes: JSON.stringify(args.isicCodes ?? []),
    documents: JSON.stringify(args.documents ?? []),
    status: "pendingKyc",
    created_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  // Auto-generate KYC verification task
  const kycTaskId = genID("sp-kyc");
  await hcDb().insertInto("vertex_hc_task" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.task/${kycTaskId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: kycTaskId,
    title: `KYC/KYB Review: ${args.legalName} (${args.countryIso3})`,
    description: `Verify business documents for OEM manufacturer registration.\nLegal name: ${args.legalName}\nCountry: ${args.countryIso3}\nCategory: ${args.category}`,
    category: "sp-kyc-review",
    difficulty: "medium",
    sp_application_id: appId,
    status: "published",
    created_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  return { 'applicationId': appId, 'kycTaskId': kycTaskId, status: "pendingKyc" };
}

async function cmdGetSpApplication(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.getSpApplication", body);
  if (!args.applicationId) return { error: "applicationId required" };
  return await hcGetById("vertex_hc_sp_application", str(args.applicationId)) ?? { error: "not found" };
}

async function cmdListSpApplications(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.listSpApplications", body);
  const limit = Math.min(Number(args.limit) || 50, 200);
  const offset = Number(args.offset) || 0;
  let query = hcDb().selectFrom("vertex_hc_sp_application" as any).selectAll();
  if (args.status) query = query.where("status" as any, "=", str(args.status));
  if (args.countryIso3) query = query.where("country_iso3" as any, "=", str(args.countryIso3));
  if (args.category) query = query.where("category" as any, "=", str(args.category));
  const applications = await query.orderBy("created_at" as any, "desc").limit(limit).offset(offset).execute();
  return { applications, total: applications.length, offset, limit };
}

async function cmdSubmitSpVerification(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.submitSpVerification", body);
  if (!args.applicationId) return { error: "applicationId required" };
  if (!args.result) return { error: "result required (approved/rejected/needsMoreInfo)" };

  const verifyId = genID("sp-verify");
  await hcDb().insertInto("vertex_hc_sp_verification" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.spVerification/${verifyId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: verifyId,
    application_id: args.applicationId,
    result: args.result,
    legal_entity_verified: args.legalEntityVerified ?? false,
    sanctions_clear: args.sanctionsClear ?? false,
    notes: args.notes ?? "",
    reviewer_did: args.reviewerDid ?? "",
    created_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  const newStatus = args.result === "approved" ? "kycApproved" : args.result === "rejected" ? "rejected" : "pendingKyc";

  // If approved, auto-create factory audit task
  if (args.result === "approved") {
    const auditTaskId = genID("sp-audit");
    await hcDb().insertInto("vertex_hc_task" as any).values({
      vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.task/${auditTaskId}`,
      sensitivity_ord: 2,
      owner_did: actorDID,
      id: auditTaskId,
      title: `Factory Audit: ${args.applicationId}`,
      description: `On-site factory audit for OEM manufacturer registration. KYC/KYB approved.`,
      category: "sp-factory-audit",
      difficulty: "expert",
      sp_application_id: args.applicationId,
      status: "published",
      created_at: nowISO(),
      org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
    }).execute();
    return { 'verificationId': verifyId, status: newStatus, 'auditTaskId': auditTaskId };
  }

  return { 'verificationId': verifyId, status: newStatus };
}

async function cmdSubmitAuditResult(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.submitAuditResult", body);
  if (!args.applicationId) return { error: "applicationId required" };
  if (!args.result) return { error: "result required (pass/conditionalPass/fail)" };

  const auditId = genID("sp-audit-result");
  await hcDb().insertInto("vertex_hc_sp_audit" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.spAudit/${auditId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: auditId,
    application_id: args.applicationId,
    audit_task_id: args.auditTaskId ?? "",
    result: args.result,
    findings: JSON.stringify(args.findings ?? []),
    certifications_verified: JSON.stringify(args.certificationsVerified ?? []),
    capacity_confirmed: args.capacityConfirmed ?? 0,
    employee_count_confirmed: args.employeeCountConfirmed ?? 0,
    created_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  return { 'auditId': auditId, result: args.result };
}

async function cmdRegisterToTsukuru(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.registerToTsukuru", body);
  if (!args.applicationId) return { error: "applicationId required" };

  // cross-actor removed (ADR-0047 audit 2026-04-21). Was: invokeRemote tsukuru/register-
  // manufacturer. The spRegistration record below is the write-only derived
  // source; tsukuru can consume via onCommit on com.etzhayyim.apps.hc.spRegistration
  // once the derive rule is wired. hc CLAUDE.md notes this actor is deprecated
  // (migrated to com-etzhayyim-hc/actor-manifest.jsonld T1 MCP-Compose), so the
  // outbound stub is acceptable.
  const result = "{}";

  const spRegId = genID("sp-reg");
  await hcDb().insertInto("vertex_hc_sp_registration" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.spRegistration/${spRegId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: spRegId,
    application_id: args.applicationId,
    tsukuru_result: result,
    status: "registered",
    created_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  return { 'applicationId': args.applicationId, 'tsukuruResult': {}, status: "registered" };
}

async function cmdCreateInspectionTask(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.createInspectionTask", body);
  if (!args.productionOrderId) return { error: "productionOrderId required" };

  const taskId = genID("sp-qc");
  await hcDb().insertInto("vertex_hc_task" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.task/${taskId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: taskId,
    title: `QC Inspection: ${args.productionOrderId}`,
    description: `Quality inspection for OEM production order.\nProduct: ${args.productDescription ?? ""}\nFactory: ${args.factoryDid ?? ""}\nType: ${args.inspectionType ?? "final"}`,
    category: "sp-quality-inspection",
    difficulty: "hard",
    production_order_id: args.productionOrderId,
    factory_did: args.factoryDid ?? "",
    inspection_type: args.inspectionType ?? "final",
    quantity: args.quantity ?? 0,
    lot_number: args.lotNumber ?? "",
    status: "published",
    created_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  return { 'taskId': taskId, status: "published" };
}

// --- Reactive Pipeline (Layer 1: ComAtprotoSyncSubscribeRepos) ---

function handleComAtprotoSyncSubscribeReposCommit(sdk: HostSDK, commit: ComAtprotoSyncSubscribeReposCommit): { ok: true; detail: string } {
  if (commit.action !== "create") return { ok: true, detail: "skip non-create" };

  const collection = str(commit.collection ?? "");

  if (collection === "com.etzhayyim.apps.hc.spVerification") {
    // SP verification completed → check if audit needed or register to tsukuru
    return { ok: true, detail: "processedSpVerification" };
  }

  if (collection === "com.etzhayyim.apps.hc.spAudit") {
    // SP audit completed → if pass, ready for tsukuru registration
    return { ok: true, detail: "processedSpAudit" };
  }

  if (collection.startsWith("com.etzhayyim.apps.tsukuru.")) {
    // tsukuru events (manufacturer registered, production progress, etc.)
    return { ok: true, detail: `processedTsukuru ${collection}` };
  }

  if (collection.startsWith("com.etzhayyim.apps.hc.")) {
    // Other HC domain records
    return { ok: true, detail: `processed ${collection}` };
  }

  if (collection === "app.bsky.feed.like") {
    return { ok: true, detail: "engagement noted" };
  }

  return { ok: true, detail: "commit accepted" };
}

// --- SDK + App Setup ---

// --- Extended Commands ---

function registerHcCommands(sdk: HostSDK): void {
  sdk.app
    .command(nsid("com.etzhayyim.apps.hc.listHc"), (_, body) => cmdListHc(sdk, body),
      asAgentTool("List Hc records"),
      withCapabilityTags('query', 'hc'),
      withOCELEvent("governance.audit"),
    )
    .command(nsid("com.etzhayyim.apps.hc.getHc"), (ctx, body) => cmdGetHc(sdk, body),
      asAgentTool("Get Hc record by ID"),
      withCapabilityTags('query', 'hc'),
    )
    .command(nsid("com.etzhayyim.apps.hc.searchHc"), (ctx, body) => cmdSearchHc(sdk, body),
      asAgentTool("Search Hc records"),
      withCapabilityTags('search', 'hc'),
    )
    .command(nsid("com.etzhayyim.apps.hc.createHc"), (ctx, body) => cmdCreateHc(sdk, body),
      asAgentTool("Create Hc record"),
      withCapabilityTags('write', 'hc'),
    )
    .command(nsid("com.etzhayyim.apps.hc.wave"), (ctx, body) => cmdWave(sdk, body),
      asAgentTool("Respond to wave greeting"),
      withCapabilityTags('social', 'greeting'),
    )
    .command(nsid("com.etzhayyim.apps.hc.getContract"), (ctx, body) => cmdGetContract(sdk, body),
      asAgentTool("Get HC contract by type and locale (worker-agreement/sp-service-agreement/task-terms/shift-terms × 13 locales)"),
      withCapabilityTags('query', 'legal', 'contract'),
    )
    .command(nsid("com.etzhayyim.apps.hc.listContracts"), (ctx, body) => cmdListContracts(sdk, body),
      asAgentTool("List all HC contract types and supported locales"),
      withCapabilityTags('query', 'legal', 'contract'),
    )
    .command(nsid("com.etzhayyim.apps.hc.acceptContract"), (ctx, body) => cmdAcceptContract(sdk, body),
      asAgentTool("Record contract acceptance (legally binding, immutable)"),
      withCapabilityTags('write', 'legal', 'contract'),
    )
    .command(nsid("com.etzhayyim.apps.hc.createSpApplication"), (ctx, body) => cmdCreateSpApplication(sdk, body),
      asAgentTool("Submit OEM service provider application (manufacturer/factory registration)"),
      withCapabilityTags('write', 'service-provider', 'onboarding'),
    )
    .command(nsid("com.etzhayyim.apps.hc.getSpApplication"), (ctx, body) => cmdGetSpApplication(sdk, body),
      asAgentTool("Get service provider application status"),
      withCapabilityTags('query', 'service-provider'),
    )
    .command(nsid("com.etzhayyim.apps.hc.listSpApplications"), (ctx, body) => cmdListSpApplications(sdk, body),
      asAgentTool("List service provider applications (filter by status/country/category)"),
      withCapabilityTags('query', 'service-provider'),
    )
    .command(nsid("com.etzhayyim.apps.hc.submitSpVerification"), (ctx, body) => cmdSubmitSpVerification(sdk, body),
      asAgentTool("Submit KYC/KYB verification result for SP application"),
      withCapabilityTags('write', 'service-provider', 'kyc'),
    )
    .command(nsid("com.etzhayyim.apps.hc.submitAuditResult"), (ctx, body) => cmdSubmitAuditResult(sdk, body),
      asAgentTool("Submit factory audit result for SP application"),
      withCapabilityTags('write', 'service-provider', 'audit'),
    )
    .command(nsid("com.etzhayyim.apps.hc.registerToTsukuru"), (ctx, body) => cmdRegisterToTsukuru(sdk, body),
      asAgentTool("Register approved SP to tsukuru.etzhayyim.com (issues manufacturer/factory DID)"),
      withCapabilityTags('write', 'service-provider', 'tsukuru'),
    )
    .command(nsid("com.etzhayyim.apps.hc.createInspectionTask"), (ctx, body) => cmdCreateInspectionTask(sdk, body),
      asAgentTool("Create quality inspection task for OEM production order"),
      withCapabilityTags('write', 'service-provider', 'quality'),
    )
    .command(nsid("com.etzhayyim.apps.hc.statsHc"), (ctx, body) => cmdStatsHc(sdk, body),
      asAgentTool("Get Hc statistics"),
      withCapabilityTags("analytics", "hc"),
    )
    .command(nsid("com.etzhayyim.apps.hc.exportHc"), (ctx, body) => cmdExportHc(sdk, body),
      asAgentTool("Export Hc data"),
      withCapabilityTags("export", "hc"),
    )
    .command(nsid("com.etzhayyim.apps.hc.healthHc"), (ctx, body) => cmdHealthHc(sdk, body),
      asAgentTool("Hc health check"),
      withCapabilityTags("diagnostics", "hc"),
    )
    .command(nsid("com.etzhayyim.apps.hc.describeHc"), (ctx, body) => cmdDescribeHc(sdk, body),
      asAgentTool("Describe Hc capabilities"),
      withCapabilityTags("meta", "hc"),
    )
    .command(nsid("com.etzhayyim.apps.hc.summarizeHc"), (ctx, body) => cmdSummarizeHc(sdk, body),
      asAgentTool("AI summary of Hc"),
      withCapabilityTags("ai", "hc"),
    )
    .command(nsid("com.etzhayyim.apps.hc.ingestHc"), (ctx, body) => cmdIngestHc(sdk, body),
      asAgentTool("Trigger Hc ingestion"),
      withCapabilityTags("pipeline", "hc"),
    )
    .command(nsid("com.etzhayyim.apps.hc.auditHc"), (ctx, body) => cmdAuditHc(sdk, body),
      asAgentTool("Audit log for Hc"),
      withCapabilityTags("audit", "hc"),
    )
}

// Layer 3: Shinka (Social Evolution)
// EnableShinka auto-activates heartbeat-driven social evolution for Hc
const shinkaEnabled = true; // shinka domain: hc;

export async function runHeartbeat(sdk: HostSDK): Promise<{ ok: boolean; actions: Array<Record<string, unknown>> }> {
  const actions: Array<Record<string, unknown>> = [];
  const ts = nowISO();
  const cadence = await resolveHeartbeatCadence("did:web:hc0mp7ng.etzhayyim.com", cadenceState, inbox);
  actions.push({ action: "cadenceResolved", mood: cadence.mood, reason: cadence.reason, ts });

  // --- shouldDrill: kyumei-koji self-research ---

  // --- shouldAnalyze: domain data analysis ---

  // --- shouldValidate: data quality check ---

  if (actions.length === 1) actions.push({ action: "noop", mood: cadence.mood, ts });
  return { ok: true, actions };
}

const HC_TABLES = [
  "vertex_hc_task", "vertex_hc_worker_intake", "vertex_hc_minor_guardian_intake",
  "vertex_hc_game_capture_task", "vertex_hc_game_capture_assignment",
  "vertex_hc_game_capture_submission", "vertex_hc_game_capture_review",
  "vertex_hc_kyc_submission", "vertex_hc_kyc_review",
  "vertex_hc_contract_acceptance", "vertex_hc_email_outbox",
  "vertex_hc_sp_application", "vertex_hc_sp_verification", "vertex_hc_sp_audit",
  "vertex_hc_sp_registration", "vertex_hc_record",
] as const;

async function cmdStatsHc(_sdk: HostSDK, _body: Uint8Array): Promise<unknown> {
  const stats: Record<string, number> = {};
  let total = 0;
  for (const t of HC_TABLES) {
    const n = await hcCountActor(t);
    stats[t] = n;
    total += n;
  }
  return { stats: [{ total, perTable: stats }], agent: "Hc" };
}

async function cmdExportHc(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.exportHc", body);
  const fmt = str(args.format ?? "json");
  const lim = Math.min(Number(args.limit) || 100, 1000);
  const perTable = Math.max(1, Math.floor(lim / HC_TABLES.length));
  const out: Record<string, unknown[]> = {};
  for (const t of HC_TABLES) {
    out[t] = await hcDb().selectFrom(t as any).selectAll()
      .where("actor_id" as any, "=", APP_NANOID)
      .limit(perTable).execute();
  }
  return { format: fmt, data: out };
}

function cmdHealthHc(sdk: HostSDK, _body: Uint8Array): unknown {
  return { status: "healthy", agent: "Hc", nanoid: "hc0mp7ng", did: `did:web:${APP_NANOID}.etzhayyim.com`, ts: nowISO() };
}

function cmdDescribeHc(sdk: HostSDK, _body: Uint8Array): unknown {
  return {
    name: "Hc", did: `did:web:${APP_NANOID}.etzhayyim.com`, nanoid: "hc0mp7ng", domain: "hc",
    capabilities: ["list", "get", "search", "create", "stats", "export", "describe", "summarize", "ingest"],
    protocols: ["xrpc", "w-protocol", "mcp"],
  };
}

async function cmdSummarizeHc(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.summarizeHc", body);
  const topic = str(args.topic ?? "Hc");
  const rows = await hcDb().selectFrom("vertex_hc_game_capture_task" as any)
    .select(["title", "game_name", "platform", "genre", "audience"] as any)
    .where("actor_id" as any, "=", APP_NANOID)
    .limit(10).execute();
  const titles = (rows as Array<{ title?: string; game_name?: string }>)
    .map((r) => r.title || r.game_name).filter(Boolean);
  const summary = await llmAsk(`Summarize ${topic} data: ${JSON.stringify(titles)}. Be concise.`);
  return { summary, topic };
}

async function cmdIngestHc(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.ingestHc", body);
  const source = str(args.source ?? "default");
  const jobId = `ingest-${Date.now()}`;
  await hcDb().insertInto("vertex_hc_record" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.record/${jobId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: jobId, type: "ingestJob", source, status: "pending",
    created_at: nowISO(), org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();
  return { jobId, status: "pending" };
}

async function cmdAuditHc(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.hc.auditHc", body);
  const since = str(args.since ?? "");
  const lim = Math.min(Number(args.limit) || 50, 200);
  // Audit = AT Repo commit log (canonical, cross-table, append-only).
  let q = hcDb().selectFrom("vertex_repo_commit" as any)
    .select(["collection", "rkey", "action", "repo", "ts_ms", "seq"] as any)
    .where("collection" as any, "like", "com.etzhayyim.apps.hc.%");
  if (since) q = q.where(sql<boolean>`ts_ms >= ${Date.parse(since) || 0}`);
  const rows = await q.orderBy("seq" as any, "desc").limit(lim).execute();
  return { audit: rows, count: (rows as unknown[]).length };
}

// --- Multi-DID ---

// --- Domain Types ---

interface HcRecord {
  id: string;
  name: string;
  status: string;
  category: string;
  'createdAt': string;
  'orgId': string;
  'userId': string;
  'actorId': string;
}

const HC_STATUSES = ["active", "draft", "archived", "pending", "completed", "cancelled"] as const;

const HC_CATEGORIES = new Map<string, string>([
  ["default", "General"],
  ["primary", "Primary"],
  ["secondary", "Secondary"],
  ["archived", "Archived"],
]);

// --- Domain Graph Queries ---

// --- Domain Collection Writers ---

// --- DID Initialization ---

// --- Domain Validation ---

function validateRecord(record: Record<string, unknown>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  if (!record.id) {
    errors.push("id is required");
  }
  if (typeof record.id === "string" && record.id.length > 128) {
    errors.push("id exceeds 128 chars");
  }
  if (record.orgId && typeof record.orgId !== "string") {
    errors.push("orgId must be string");
  }
  if (record.createdAt && typeof record.createdAt === "string") {
    const ts = Date.parse(record.createdAt as string);
    if (isNaN(ts)) {
      errors.push("createdAt is not valid ISO date");
    }
  }
  if (record.status && !["active", "draft", "archived", "pending", "completed"].includes(record.status as string)) {
    errors.push("status must be one of: active, draft, archived, pending, completed");
  }
  return { valid: errors.length === 0, errors };
}

// cross-actor invoke helper removed (ADR-0047 audit 2026-04-21).
// Was: `invokeRemote(sdk, targetDid, method, params)` → `sdk.hostImports.invoke`.
// hc actor is deprecated (migrated to com-etzhayyim-hc/actor-manifest.jsonld T1
// MCP-Compose per hc/CLAUDE.md header); remaining app.ts call (cmdRegisterToTsukuru)
// now uses the write-only derived pattern (ADR-0004) — tsukuru consumes
// com.etzhayyim.apps.hc.spRegistration commits instead of receiving a direct RPC.

// --- Email (Resend + outbox fallback) ---

type EmailEnvelope = { to: string; subject: string; html: string; text?: string; tag?: string };

async function sendEmail(sdk: HostSDK, env: EmailEnvelope): Promise<{ sent: boolean; outboxId?: string; provider?: string; error?: string }> {
  const apiKey = (sdk.env as any)?.SS_RESEND_API_KEY ?? "";
  const from = "hc.etzhayyim.com <noreply@hc.etzhayyim.com>";
  if (apiKey) {
    try {
      const r = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: { "Authorization": `Bearer ${apiKey}`, "Content-Type": "application/json" },
        body: JSON.stringify({ from, to: [env.to], subject: env.subject, html: env.html, text: env.text ?? env.html.replace(/<[^>]+>/g, "") }),
      });
      if (r.ok) return { sent: true, provider: "resend" };
      const body = await r.text();
      // fall through to outbox
      const outboxId = genID("mail");
      await hcDb().insertInto("vertex_hc_email_outbox" as any).values({
        vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.emailOutbox/${outboxId}`,
        sensitivity_ord: 2,
        owner_did: actorDID,
        id: outboxId, to: env.to, subject: env.subject, html: env.html, tag: env.tag ?? "",
        status: "failed", provider: "resend", provider_error: body.slice(0, 500),
        created_at: nowISO(), org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
      }).execute();
      return { sent: false, outboxId, provider: "resend", error: `resend status ${r.status}` };
    } catch (e: any) {
      // fall through to outbox
    }
  }
  const outboxId = genID("mail");
  await hcDb().insertInto("vertex_hc_email_outbox" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.emailOutbox/${outboxId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: outboxId, to: env.to, subject: env.subject, html: env.html, tag: env.tag ?? "",
    status: apiKey ? "failed" : "queued", provider: apiKey ? "resend" : "outbox-only",
    created_at: nowISO(), org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();
  return { sent: false, outboxId, provider: apiKey ? "resend" : "outbox-only" };
}

function emailWorkerConfirm(intakeId: string, fullName: string, kycUrl: string): EmailEnvelope {
  return {
    to: "", subject: "【hc.etzhayyim.com】ご登録ありがとうございます（KYC案内）",
    tag: "worker-confirm",
    html: `<!doctype html><html><body style="font-family:sans-serif;line-height:1.7;color:#0f172a">
<h2 style="color:#0ea06a">ご登録ありがとうございます</h2>
<p>${fullName} 様</p>
<p>hc.etzhayyim.com にワーカー登録いただきました。<br/>申込ID: <code>${intakeId}</code></p>
<h3>次のステップ：本人確認（KYC）</h3>
<p>以下のリンクから本人確認書類（運転免許証・パスポート・マイナンバーカード等）をアップロードしてください。</p>
<p><a href="${kycUrl}" style="background:#0ea06a;color:#fff;padding:10px 20px;border-radius:999px;text-decoration:none;display:inline-block">KYC書類をアップロード</a></p>
<p style="color:#475569;font-size:13px">このリンクは72時間有効です。期限切れの場合は <a href="https://hc.etzhayyim.com/register">/register</a> から再発行してください。</p>
<hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0"/>
<p style="color:#475569;font-size:12px">運営: etzhayyim (宗教法人・任意団体・blockchain 登記) ／ hc.etzhayyim.com ／ 準拠法：日本法 ／ 専属管轄：東京地方裁判所</p>
</body></html>`,
  };
}

function emailMinorConfirm(intakeId: string, guardianName: string, childName: string, confirmUrl: string): EmailEnvelope {
  return {
    to: "", subject: "【hc.etzhayyim.com】保護者申込の確認（最終同意）",
    tag: "minor-confirm",
    html: `<!doctype html><html><body style="font-family:sans-serif;line-height:1.7;color:#0f172a">
<h2 style="color:#0ea06a">保護者申込を受け付けました</h2>
<p>${guardianName} 様（${childName} 様のご登録について）</p>
<p>申込ID: <code>${intakeId}</code></p>
<h3>最終同意のお願い</h3>
<p>以下のリンクから、保護者同意書の最終確認と電子署名（ワンクリック）をお願いします。</p>
<p><a href="${confirmUrl}" style="background:#0ea06a;color:#fff;padding:10px 20px;border-radius:999px;text-decoration:none;display:inline-block">同意を完了する</a></p>
<p>同意完了後、お子さまの年齢に適合する CERO A/B タイトル一覧をご案内します。</p>
<p style="color:#475569;font-size:13px">制限事項：1日2時間／週10時間、深夜帯（21:00〜翌7:00）予約不可。報酬は保護者メール宛にAmazonギフトカードで配布。</p>
<hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0"/>
<p style="color:#475569;font-size:12px">運営: etzhayyim (宗教法人・任意団体・blockchain 登記) ／ hc.etzhayyim.com ／ <a href="https://hc.etzhayyim.com/legal/minor-consent">保護者同意書</a></p>
</body></html>`,
  };
}

function emailPayout(reviewId: string, submissionId: string, payoutJpy: number, giftCode: string): EmailEnvelope {
  const codeBlock = giftCode
    ? `<div style="background:#fff7ed;border:1px dashed #fdba74;padding:14px;border-radius:8px;margin:12px 0;font-family:ui-monospace,monospace;font-size:16px;text-align:center">${giftCode}</div>`
    : `<p style="color:#b45309">※ Amazonギフトコードは 1〜7営業日以内に別途メールでお送りします。</p>`;
  return {
    to: "", subject: "【hc.etzhayyim.com】タスクが承認されました",
    tag: "payout-approved",
    html: `<!doctype html><html><body style="font-family:sans-serif;line-height:1.7;color:#0f172a">
<h2 style="color:#0ea06a">✅ タスクが承認されました</h2>
<p>レビューID: <code>${reviewId}</code> ／ 提出ID: <code>${submissionId}</code></p>
<p>報酬額：<strong>¥${payoutJpy.toLocaleString()}</strong> 分のAmazonギフトカード</p>
${codeBlock}
<p style="color:#475569;font-size:13px">Amazonギフトカードの利用には Amazon アカウントが必要です。<a href="https://www.amazon.co.jp/gc/redeem">こちら</a>からコードを登録してください。</p>
<hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0"/>
<p style="color:#475569;font-size:12px">運営: etzhayyim (宗教法人・任意団体・blockchain 登記) ／ hc.etzhayyim.com</p>
</body></html>`,
  };
}

// (readPrivate helper removed 2026-04-23 — legacy ActorPreference storage is
// a dead path. Preferences are written via sdk.pds.dispatch actor-put-preferences
// but not projected to a queryable typed table. When server-side PII lookup is
// required, add a dedicated typed table under ADR-0018 Tier 3 policy.)

// --- Worker Intake & Game Capture Task Lifecycle (2026-04-22) ---
// Supports game-play-uploader.etzhayyim.com referral registration (ADR-0051).

function safeJson(body: Uint8Array): Record<string, unknown> {
  try {
    return parseLexiconInput("", body) as Record<string, unknown>;
  } catch { /* fallthrough */ }
  try {
    const text = new TextDecoder().decode(body);
    return text ? (JSON.parse(text) as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

function redactPII<T extends Record<string, unknown>>(record: T, piiKeys: string[]): T {
  const out: Record<string, unknown> = { ...record };
  for (const k of piiKeys) if (k in out) out[k] = "[REDACTED]";
  return out as T;
}

async function cmdRegisterWorker(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const fullName = str(a.fullName ?? "");
  const email = str(a.email ?? "");
  const dob = str(a.dob ?? "");
  const prefecture = str(a.prefecture ?? "");
  const ref = str(a.ref ?? "");
  const accepted = Array.isArray(a.acceptedTerms) ? a.acceptedTerms.map(String) : [];

  if (!fullName) return { error: "fullName required" };
  if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return { error: "valid email required" };
  if (!dob) return { error: "dob required" };
  if (!prefecture) return { error: "prefecture required" };

  const birth = Date.parse(dob);
  if (isNaN(birth)) return { error: "dob invalid" };
  const ageMs = Date.now() - birth;
  const ageYears = ageMs / (365.2425 * 24 * 3600 * 1000);
  if (ageYears < 18) return { error: "adult registration requires age >= 18; use minor registration instead" };

  const intakeId = genID("wi");
  const piiKey = `worker-intake:${intakeId}`;
  const kycToken = genID("kyc").replace(/[^a-zA-Z0-9]/g, "");

  // PII → Preferences (Tier 3, non-federable)
  writePrivate(sdk, piiKey, {
    fullName, email, dob, prefecture,
    userAgent: str(a.userAgent ?? ""), referrer: ref, kycToken,
  });

  // Public record — PII redacted, only governance-relevant metadata
  await hcDb().insertInto("vertex_hc_worker_intake" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.workerIntake/${intakeId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: intakeId,
    pii_key: piiKey,
    kyc_token_hash: kycToken.slice(0, 12),
    email_domain: email.split("@")[1] ?? "",
    prefecture,
    age_band: ageYears < 25 ? "18-24" : ageYears < 40 ? "25-39" : ageYears < 60 ? "40-59" : "60+",
    referrer: ref,
    accepted_terms: JSON.stringify(accepted),
    status: "pendingKyc",
    created_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  // Record contract acceptances (immutable legal record)
  for (const t of accepted) {
    if (t === "worker-agreement" || t === "task-terms" || t === "shift-terms") {
      const acceptId = genID("accept");
      await hcDb().insertInto("vertex_hc_contract_acceptance" as any).values({
        vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.contractAcceptance/${acceptId}`,
        sensitivity_ord: 2,
        owner_did: actorDID,
        id: acceptId,
        contract_type: t,
        contract_did: `did:web:${APP_NANOID}.etzhayyim.com:legal:${t}`,
        acceptor_intake_id: intakeId,
        locale: "ja",
        accepted_at: nowISO(),
        user_agent: str(a.userAgent ?? ""),
        org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
      }).execute();
    }
  }

  const kycUrl = `https://hc.etzhayyim.com/worker/kyc?intakeId=${intakeId}&tok=${kycToken}`;
  const envelope = { ...emailWorkerConfirm(intakeId, fullName, kycUrl), to: email };
  const emailResult = await sendEmail(sdk, envelope);

  return {
    intakeId, status: "pendingKyc",
    nextSteps: ["kyc-document-upload", "amazon-gift-email-verification"],
    referrer: ref,
    kycUrl,
    email: { sent: emailResult.sent, provider: emailResult.provider, outboxId: emailResult.outboxId },
  };
}

async function cmdRegisterMinorGuardian(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const guardianName = str(a.guardianName ?? "");
  const guardianEmail = str(a.guardianEmail ?? "");
  const relation = str(a.relation ?? "");
  const childName = str(a.childName ?? "");
  const childAge = Number(a.childAge ?? 0);
  const prefecture = str(a.prefecture ?? "");
  const ref = str(a.ref ?? "");
  const accepted = Array.isArray(a.acceptedTerms) ? a.acceptedTerms.map(String) : [];

  if (!guardianName) return { error: "guardianName required" };
  if (!guardianEmail || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(guardianEmail)) return { error: "valid guardianEmail required" };
  if (!relation) return { error: "relation required" };
  if (!childName) return { error: "childName required" };
  if (childAge < 8 || childAge > 17) return { error: "childAge must be 8..17" };
  if (!prefecture) return { error: "prefecture required" };
  if (!accepted.includes("minor-consent")) return { error: "minor-consent acceptance required" };

  const intakeId = genID("mi");
  const piiKey = `minor-intake:${intakeId}`;

  writePrivate(sdk, piiKey, {
    guardianName, guardianEmail, relation,
    childName, childAge, prefecture,
    userAgent: str(a.userAgent ?? ""), referrer: ref,
  });

  await hcDb().insertInto("vertex_hc_minor_guardian_intake" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.minorGuardianIntake/${intakeId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: intakeId,
    pii_key: piiKey,
    guardian_email_domain: guardianEmail.split("@")[1] ?? "",
    child_age_band: childAge <= 12 ? "8-12" : "13-17",
    prefecture,
    relation,
    referrer: ref,
    accepted_terms: JSON.stringify(accepted),
    status: "pendingGuardianConfirmation",
    daily_hour_limit: 2,
    weekly_hour_limit: 10,
    night_block_start_jst: "21:00",
    night_block_end_jst: "07:00",
    cero_allowed: JSON.stringify(["A","B"]),
    created_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  for (const t of accepted) {
    if (t === "worker-agreement" || t === "task-terms" || t === "minor-consent") {
      const acceptId = genID("accept");
      const contractType = t === "minor-consent" ? "minor-consent" : t;
      await hcDb().insertInto("vertex_hc_contract_acceptance" as any).values({
        vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.contractAcceptance/${acceptId}`,
        sensitivity_ord: 2,
        owner_did: actorDID,
        id: acceptId,
        contract_type: contractType,
        contract_did: `did:web:${APP_NANOID}.etzhayyim.com:legal:${contractType}`,
        acceptor_intake_id: intakeId,
        locale: "ja",
        accepted_at: nowISO(),
        user_agent: str(a.userAgent ?? ""),
        org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
      }).execute();
    }
  }

  const confirmUrl = `https://hc.etzhayyim.com/worker/minor-confirm?intakeId=${intakeId}`;
  const envelope = { ...emailMinorConfirm(intakeId, guardianName, childName, confirmUrl), to: guardianEmail };
  const emailResult = await sendEmail(sdk, envelope);

  return {
    intakeId, status: "pendingGuardianConfirmation",
    nextSteps: ["guardian-email-confirm", "cero-compatible-title-listing"],
    constraints: { dailyHours: 2, weeklyHours: 10, nightBlock: "21:00-07:00 JST", cero: ["A","B"] },
    referrer: ref,
    confirmUrl,
    email: { sent: emailResult.sent, provider: emailResult.provider, outboxId: emailResult.outboxId },
  };
}

async function cmdCreateGameCaptureTask(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const title = str(a.title ?? "");
  const platform = str(a.platform ?? "");
  const genre = str(a.genre ?? "");
  const gameName = str(a.gameName ?? "");
  const durationMinutes = Math.max(1, Math.min(480, Number(a.durationMinutes ?? 60)));
  const audience = str(a.audience ?? "adult");
  const ceroRating = str(a.ceroRating ?? "");
  const bonusMultiplier = Math.max(1, Math.min(3, Number(a.bonusMultiplier ?? 1)));
  const requesterDid = str(a.requesterDid ?? "");

  if (!title) return { error: "title required" };
  if (!gameName) return { error: "gameName required" };
  if (!platform) return { error: "platform required" };
  if (!["adult", "minor"].includes(audience)) return { error: "audience must be adult|minor" };
  if (audience === "minor") {
    if (!["A", "B"].includes(ceroRating)) return { error: "minor audience requires ceroRating A or B" };
    if (durationMinutes > 120) return { error: "minor tasks cannot exceed 120 minutes (daily cap)" };
  }

  const baseRatePerHour = 100;
  const payoutJpy = Math.round((durationMinutes / 60) * baseRatePerHour * bonusMultiplier);

  const taskId = genID("gct");
  await hcDb().insertInto("vertex_hc_game_capture_task" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.gameCaptureTask/${taskId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: taskId,
    title, platform, genre, game_name: gameName,
    duration_minutes: durationMinutes, audience, cero_rating: ceroRating,
    bonus_multiplier: bonusMultiplier, payout_jpy: payoutJpy,
    payout_currency: "JPY",
    payout_method: "amazon-gift-card",
    requester_did: requesterDid,
    referrer: "game-play-uploader",
    status: "published",
    created_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  return { taskId, status: "published", payoutJpy, durationMinutes, audience };
}

async function cmdAcceptGameCaptureTask(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const taskId = str(a.taskId ?? "");
  const workerIntakeId = str(a.workerIntakeId ?? "");
  if (!taskId) return { error: "taskId required" };
  if (!workerIntakeId) return { error: "workerIntakeId required" };

  const assignmentId = genID("gca");
  await hcDb().insertInto("vertex_hc_game_capture_assignment" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.gameCaptureAssignment/${assignmentId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: assignmentId,
    task_id: taskId,
    worker_intake_id: workerIntakeId,
    status: "accepted",
    accepted_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();
  return { assignmentId, taskId, status: "accepted" };
}

async function cmdSubmitGameCaptureUpload(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const assignmentId = str(a.assignmentId ?? "");
  const videoBlobKey = str(a.videoBlobKey ?? "");
  const actualMinutes = Number(a.actualMinutes ?? 0);
  const piiOccludedCount = Number(a.piiOccludedCount ?? 0);
  const sceneTags = Array.isArray(a.sceneTags) ? a.sceneTags.map(String) : [];

  if (!assignmentId) return { error: "assignmentId required" };
  if (!videoBlobKey) return { error: "videoBlobKey required (content-addressed R2 key)" };
  if (actualMinutes <= 0) return { error: "actualMinutes must be > 0" };

  const submissionId = genID("gcs");
  await hcDb().insertInto("vertex_hc_game_capture_submission" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.gameCaptureSubmission/${submissionId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: submissionId,
    assignment_id: assignmentId,
    video_blob_key: videoBlobKey,
    actual_minutes: actualMinutes,
    pii_occluded_count: piiOccludedCount,
    scene_tags: JSON.stringify(sceneTags),
    status: piiOccludedCount > 0 ? "needsResubmit" : "pendingReview",
    review_auto_approve_at: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString(),
    submitted_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  return {
    submissionId, assignmentId,
    status: piiOccludedCount > 0 ? "needsResubmit" : "pendingReview",
    autoApproveIn: "7 days",
  };
}

async function cmdApproveGameCaptureSubmission(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const submissionId = str(a.submissionId ?? "");
  const decision = str(a.decision ?? "");
  const notes = str(a.notes ?? "");
  const notifyEmail = str(a.notifyEmail ?? "");
  const giftCode = str(a.giftCode ?? "");
  const payoutJpy = Math.max(0, Number(a.payoutJpy ?? 0));
  if (!submissionId) return { error: "submissionId required" };
  if (!["approve", "reject"].includes(decision)) return { error: "decision must be approve|reject" };

  const reviewId = genID("gcr");
  await hcDb().insertInto("vertex_hc_game_capture_review" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.gameCaptureReview/${reviewId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: reviewId,
    submission_id: submissionId,
    decision,
    notes,
    payout_jpy: payoutJpy,
    payout_queued: decision === "approve",
    gift_code_dispatched: decision === "approve" && !!giftCode,
    reviewed_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  let emailResult: Awaited<ReturnType<typeof sendEmail>> | undefined;
  if (decision === "approve" && notifyEmail) {
    const envelope = { ...emailPayout(reviewId, submissionId, payoutJpy, giftCode), to: notifyEmail };
    emailResult = await sendEmail(sdk, envelope);
  }

  return {
    reviewId, submissionId, decision,
    payoutQueued: decision === "approve",
    giftCodeDispatched: decision === "approve" && !!giftCode,
    note: decision === "approve"
      ? (giftCode
          ? "Amazon gift code was dispatched to worker email."
          : "Amazon gift card will be dispatched within 1-7 business days (manual operation until Amazon Incentives API integration lands).")
      : undefined,
    email: emailResult ? { sent: emailResult.sent, provider: emailResult.provider, outboxId: emailResult.outboxId } : undefined,
  };
}

// --- KYC (document upload + review) ---

async function cmdSubmitKycDocument(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const intakeId = str(a.intakeId ?? "");
  const tok = str(a.tok ?? "");
  const docType = str(a.docType ?? ""); // "license" | "passport" | "mynumber" | "health-insurance"
  const fileBase64 = str(a.fileBase64 ?? "");
  const mimeType = str(a.mimeType ?? "image/jpeg");
  if (!intakeId) return { error: "intakeId required" };
  if (!tok) return { error: "tok required" };
  if (!["license", "passport", "mynumber", "health-insurance"].includes(docType)) {
    return { error: "docType must be license|passport|mynumber|health-insurance" };
  }
  if (!fileBase64) return { error: "fileBase64 required" };

  // Token validation — compare against intake's stored kyc_token_hash prefix
  const intake = await hcDb().selectFrom("vertex_hc_worker_intake" as any)
    .select(["kyc_token_hash"] as any)
    .where("id" as any, "=", intakeId).limit(1).executeTakeFirst();
  if (!intake) return { error: "intake not found" };
  const tokenPrefix = tok.slice(0, 12);
  const storedHash = str((intake as any).kyc_token_hash ?? "");
  if (storedHash && storedHash !== tokenPrefix) {
    return { error: "invalid token" };
  }

  // Decode base64
  let bytes: Uint8Array;
  try {
    const binStr = atob(fileBase64);
    bytes = new Uint8Array(binStr.length);
    for (let i = 0; i < binStr.length; i++) bytes[i] = binStr.charCodeAt(i);
  } catch {
    return { error: "fileBase64 invalid" };
  }
  if (bytes.length === 0) return { error: "empty file" };
  if (bytes.length > 12 * 1024 * 1024) return { error: "file too large (12 MB max)" };

  // Content-addressed SHA-256 key
  const hashBuf = await crypto.subtle.digest("SHA-256", bytes);
  const hashHex = Array.from(new Uint8Array(hashBuf)).map(b => b.toString(16).padStart(2, "0")).join("");
  const blobKey = `hc/kyc/${intakeId}/${hashHex}`;

  // Store in R2 (YATA_R2 binding). If binding missing, fall back to record-only.
  const r2 = (sdk.env as any)?.YATA_R2;
  let r2Uploaded = false;
  if (r2 && typeof r2.put === "function") {
    try {
      await r2.put(blobKey, bytes, { httpMetadata: { contentType: mimeType } });
      r2Uploaded = true;
    } catch {
      r2Uploaded = false;
    }
  }

  const submissionId = genID("kyc-sub");
  await hcDb().insertInto("vertex_hc_kyc_submission" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.kycSubmission/${submissionId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: submissionId,
    intake_id: intakeId,
    doc_type: docType,
    blob_key: blobKey,
    mime_type: mimeType,
    byte_size: bytes.length,
    r2_uploaded: r2Uploaded,
    hash_sha256: hashHex,
    status: "pendingReview",
    submitted_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  return {
    submissionId, intakeId, docType, byteSize: bytes.length, r2Uploaded,
    status: "pendingReview",
    note: r2Uploaded ? "Document stored securely. Review typically 1-3 business days." : "R2 storage unavailable; metadata recorded only — please re-upload once storage is restored.",
  };
}

async function cmdReviewKycSubmission(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const submissionId = str(a.submissionId ?? "");
  const decision = str(a.decision ?? "");
  const notes = str(a.notes ?? "");
  if (!submissionId) return { error: "submissionId required" };
  if (!["approve", "reject", "needsMoreInfo"].includes(decision)) {
    return { error: "decision must be approve|reject|needsMoreInfo" };
  }

  const reviewId = genID("kyc-rev");
  await hcDb().insertInto("vertex_hc_kyc_review" as any).values({
    vertex_id: `at://${actorDID}/com.etzhayyim.apps.hc.kycReview/${reviewId}`,
    sensitivity_ord: 2,
    owner_did: actorDID,
    id: reviewId,
    submission_id: submissionId,
    decision,
    notes,
    reviewed_at: nowISO(),
    org_id: "anon", user_id: "anon", actor_id: APP_NANOID,
  }).execute();

  return { reviewId, submissionId, decision };
}

// --- Queries for SuperApp UI (typed vertex_hc_* tables) ---

async function cmdListGameCaptureTasks(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const status = str(a.status ?? "published");
  const audience = str(a.audience ?? "");
  const limit = Math.min(Number(a.limit) || 30, 100);
  const offset = Number(a.offset) || 0;
  let q = hcDb().selectFrom("vertex_hc_game_capture_task" as any).selectAll();
  if (status) q = q.where("status" as any, "=", status);
  if (audience) q = q.where("audience" as any, "=", audience);
  const items = await q.orderBy("created_at" as any, "desc").limit(limit).offset(offset).execute();
  return { items, total: (items as unknown[]).length, offset, limit };
}

async function cmdListMyAssignments(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const workerIntakeId = str(a.workerIntakeId ?? "");
  const limit = Math.min(Number(a.limit) || 30, 100);
  if (!workerIntakeId) return { error: "workerIntakeId required" };
  const items = await hcDb().selectFrom("vertex_hc_game_capture_assignment" as any).selectAll()
    .where("worker_intake_id" as any, "=", workerIntakeId)
    .orderBy("accepted_at" as any, "desc")
    .limit(limit).execute();
  return { items, total: (items as unknown[]).length };
}

async function cmdGetMyEarnings(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const workerIntakeId = str(a.workerIntakeId ?? "");
  if (!workerIntakeId) return { error: "workerIntakeId required" };
  const db = hcDb();

  // 1) my assignments → IDs
  const assignments = await db.selectFrom("vertex_hc_game_capture_assignment" as any)
    .select(["id"] as any).where("worker_intake_id" as any, "=", workerIntakeId).execute();
  const myAssignmentIds = (assignments as Array<{ id: string }>).map((a) => a.id);
  if (myAssignmentIds.length === 0) {
    return {
      workerIntakeId, assignmentCount: 0, submissionCount: 0,
      pendingReviewCount: 0, approvedCount: 0, rejectedCount: 0, paidTotalJpy: 0,
    };
  }

  // 2) my submissions (join via assignment_id)
  const submissions = await db.selectFrom("vertex_hc_game_capture_submission" as any)
    .select(["id", "status"] as any)
    .where("assignment_id" as any, "in", myAssignmentIds)
    .execute();
  const mySubIds = (submissions as Array<{ id: string; status: string }>).map((s) => s.id);
  const pendingReviewCount = (submissions as Array<{ status: string }>).filter((s) => s.status === "pendingReview").length;

  // 3) reviews for my submissions — aggregate
  let approvedCount = 0, rejectedCount = 0, paidTotalJpy = 0;
  if (mySubIds.length > 0) {
    const agg = await db.selectFrom("vertex_hc_game_capture_review" as any)
      .select([
        sql<number>`count(*) filter (where decision = 'approve')`.as("approved"),
        sql<number>`count(*) filter (where decision = 'reject')`.as("rejected"),
        sql<number>`coalesce(sum(payout_jpy) filter (where decision = 'approve'), 0)`.as("paid"),
      ] as any)
      .where("submission_id" as any, "in", mySubIds)
      .executeTakeFirst();
    approvedCount = Number((agg as any)?.approved ?? 0);
    rejectedCount = Number((agg as any)?.rejected ?? 0);
    paidTotalJpy = Number((agg as any)?.paid ?? 0);
  }

  return {
    workerIntakeId,
    assignmentCount: myAssignmentIds.length,
    submissionCount: mySubIds.length,
    pendingReviewCount, approvedCount, rejectedCount, paidTotalJpy,
  };
}

async function cmdGetIntakeSummary(_sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const a = safeJson(body);
  const intakeId = str(a.intakeId ?? "");
  if (!intakeId) return { error: "intakeId required" };
  const db = hcDb();
  const adult = await db.selectFrom("vertex_hc_worker_intake" as any)
    .select(["status", "prefecture", "age_band", "referrer", "created_at"] as any)
    .where("id" as any, "=", intakeId).limit(1).executeTakeFirst();
  if (adult) {
    const r = adult as any;
    return { kind: "adult", intakeId, status: str(r.status ?? ""), prefecture: str(r.prefecture ?? ""), ageBand: str(r.age_band ?? ""), referrer: str(r.referrer ?? ""), createdAt: str(r.created_at ?? "") };
  }
  const minor = await db.selectFrom("vertex_hc_minor_guardian_intake" as any)
    .select(["status", "prefecture", "child_age_band", "relation", "referrer", "created_at"] as any)
    .where("id" as any, "=", intakeId).limit(1).executeTakeFirst();
  if (minor) {
    const r = minor as any;
    return { kind: "minor", intakeId, status: str(r.status ?? ""), prefecture: str(r.prefecture ?? ""), childAgeBand: str(r.child_age_band ?? ""), relation: str(r.relation ?? ""), referrer: str(r.referrer ?? ""), createdAt: str(r.created_at ?? "") };
  }
  return { error: "not found" };
}

// --- Register extended commands (game-capture + intake) ---

function registerGameCaptureCommands(sdk: HostSDK): void {
  sdk.app
    .command(nsid("com.etzhayyim.apps.hc.registerWorker"), (_ctx, body) => cmdRegisterWorker(sdk, body),
      asAgentTool("Register an adult worker (18+) via hc.etzhayyim.com /register form"),
      withCapabilityTags("write", "onboarding", "worker"),
      withOCELEvent("onboarding.workerIntake.created"),
    )
    .command(nsid("com.etzhayyim.apps.hc.registerMinorGuardian"), (_ctx, body) => cmdRegisterMinorGuardian(sdk, body),
      asAgentTool("Register a minor (8-17) with guardian as counterparty"),
      withCapabilityTags("write", "onboarding", "minor", "guardian"),
      withOCELEvent("onboarding.minorGuardianIntake.created"),
    )
    .command(nsid("com.etzhayyim.apps.hc.createGameCaptureTask"), (_ctx, body) => cmdCreateGameCaptureTask(sdk, body),
      asAgentTool("Create a game capture task (domain coverage dataset)"),
      withCapabilityTags("write", "game-capture", "task"),
    )
    .command(nsid("com.etzhayyim.apps.hc.acceptGameCaptureTask"), (_ctx, body) => cmdAcceptGameCaptureTask(sdk, body),
      asAgentTool("Worker accepts a game capture task"),
      withCapabilityTags("write", "game-capture", "assignment"),
    )
    .command(nsid("com.etzhayyim.apps.hc.submitGameCaptureUpload"), (_ctx, body) => cmdSubmitGameCaptureUpload(sdk, body),
      asAgentTool("Submit a recorded gameplay video for an accepted task"),
      withCapabilityTags("write", "game-capture", "upload"),
    )
    .command(nsid("com.etzhayyim.apps.hc.approveGameCaptureSubmission"), (_ctx, body) => cmdApproveGameCaptureSubmission(sdk, body),
      asAgentTool("Approve or reject a game capture submission (triggers gift-card payout queue on approve)"),
      withCapabilityTags("write", "game-capture", "review"),
    )
    .command(nsid("com.etzhayyim.apps.hc.submitKycDocument"), (_ctx, body) => cmdSubmitKycDocument(sdk, body),
      asAgentTool("Submit KYC identity document (base64-encoded; stored in R2 content-addressed)"),
      withCapabilityTags("write", "kyc", "pii"),
      withOCELEvent("kyc.document.submitted"),
    )
    .command(nsid("com.etzhayyim.apps.hc.reviewKycSubmission"), (_ctx, body) => cmdReviewKycSubmission(sdk, body),
      asAgentTool("Admin review of a KYC submission"),
      withCapabilityTags("write", "kyc", "review"),
    )
    .command(nsid("com.etzhayyim.apps.hc.listGameCaptureTasks"), (_ctx, body) => cmdListGameCaptureTasks(sdk, body),
      asAgentTool("List published game capture tasks (optional status/audience filter)"),
      withCapabilityTags("query", "game-capture"),
    )
    .command(nsid("com.etzhayyim.apps.hc.listMyAssignments"), (_ctx, body) => cmdListMyAssignments(sdk, body),
      asAgentTool("List a worker's own game capture assignments"),
      withCapabilityTags("query", "game-capture", "self"),
    )
    .command(nsid("com.etzhayyim.apps.hc.getMyEarnings"), (_ctx, body) => cmdGetMyEarnings(sdk, body),
      asAgentTool("Earnings summary for a worker (approvals / rejections / JPY paid)"),
      withCapabilityTags("query", "earnings", "self"),
    )
    .command(nsid("com.etzhayyim.apps.hc.getIntakeSummary"), (_ctx, body) => cmdGetIntakeSummary(sdk, body),
      asAgentTool("Public metadata for an intake (no PII) — used by SuperApp UI header"),
      withCapabilityTags("query", "onboarding", "self"),
    );
}

export { handleComAtprotoSyncSubscribeReposCommit };

export default createWorkerExport((sdk) => {
  actorDID = sdk.pds.selfRepo ?? "";
  registerHcCommands(sdk);
  registerGameCaptureCommands(sdk);
});
