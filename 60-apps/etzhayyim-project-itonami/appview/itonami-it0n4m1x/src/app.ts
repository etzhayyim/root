// itonami.etzhayyim.com — Aircraft engine lifecycle simulation SPA.
// Pure static SPA: all simulation logic is client-side (Svelte stores).
// This Worker serves ASSETS and exposes health + meta endpoints.
//
// ADR-2605111200: No HYPERDRIVE binding in wrangler.jsonc — this is an edge-proxy
// only worker. All domain writes are queued downstream (bpmn-dispatcher →
// AgentGateway MCP → LangServer pod). Commands validate input and return
// { ok: true, queued: true }; persistence happens in the pod.

import {
  createWorkerExport,
  nowISO,
  nsid,
  asAgentTool,
  withCapabilityTags,
} from "@etzhayyim/kotodama-host-sdk";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function str(v: unknown): string {
  return typeof v === "string" ? v : "";
}

function int(v: unknown, fallback = 0): number {
  const n = Number(v);
  return Number.isFinite(n) ? Math.trunc(n) : fallback;
}

function json<T>(raw: unknown): T {
  if (!raw) return {} as T;
  if (typeof raw === "string") return JSON.parse(raw) as T;
  if (raw instanceof Uint8Array) return JSON.parse(new TextDecoder().decode(raw)) as T;
  if (raw instanceof ArrayBuffer) return JSON.parse(new TextDecoder().decode(new Uint8Array(raw))) as T;
  return raw as T;
}

function out(value: unknown): Uint8Array {
  return new TextEncoder().encode(JSON.stringify(value));
}

// ---------------------------------------------------------------------------
// Command handlers
// ---------------------------------------------------------------------------

function cmdRegisterEngine(_payload: Uint8Array): Uint8Array {
  const args = json<{
    engine_id?: string;
    design_code?: string;
    engine_type?: string;
    thrust_rating_kn?: number;
    mass_kg?: number;
    certification_status?: string;
  }>(_payload);

  const engineId = str(args.engine_id);
  const designCode = str(args.design_code);
  if (!engineId || !designCode) {
    return out({ error: "missingRequiredFields", required: ["engine_id", "design_code"] });
  }

  return out({
    ok: true,
    queued: true,
    engine_id: engineId,
    design_code: designCode,
    engine_type: str(args.engine_type) || "turbofan",
    thrust_rating_kn: int(args.thrust_rating_kn),
    mass_kg: int(args.mass_kg),
    certification_status: str(args.certification_status) || "design",
    ts: nowISO(),
  });
}

function cmdRecordAssembly(_payload: Uint8Array): Uint8Array {
  const args = json<{
    engine_id?: string;
    phase_code?: string;
    progress_permille?: number;
    notes?: string;
  }>(_payload);

  const engineId = str(args.engine_id);
  const phaseCode = str(args.phase_code);
  if (!engineId || !phaseCode) {
    return out({ error: "missingRequiredFields", required: ["engine_id", "phase_code"] });
  }

  const progressPermille = int(args.progress_permille, 0);
  if (progressPermille < 0 || progressPermille > 1000) {
    return out({ error: "invalidRange", field: "progress_permille", min: 0, max: 1000 });
  }

  return out({
    ok: true,
    queued: true,
    engine_id: engineId,
    phase_code: phaseCode,
    progress_permille: progressPermille,
    notes: str(args.notes),
    ts: nowISO(),
  });
}

function cmdLogTestResult(_payload: Uint8Array): Uint8Array {
  const args = json<{
    engine_id?: string;
    test_type?: string;
    outcome_code?: string;
    thrust_achieved_kn?: number;
    duration_seconds?: number;
  }>(_payload);

  const engineId = str(args.engine_id);
  const testType = str(args.test_type);
  const outcomeCode = str(args.outcome_code);
  if (!engineId || !testType || !outcomeCode) {
    return out({ error: "missingRequiredFields", required: ["engine_id", "test_type", "outcome_code"] });
  }

  return out({
    ok: true,
    queued: true,
    engine_id: engineId,
    test_type: testType,
    outcome_code: outcomeCode,
    thrust_achieved_kn: int(args.thrust_achieved_kn),
    duration_seconds: int(args.duration_seconds),
    ts: nowISO(),
  });
}

function cmdLogFlightEvent(_payload: Uint8Array): Uint8Array {
  const args = json<{
    engine_id?: string;
    aircraft_id?: string;
    cycle_count?: number;
    flight_hours?: number;
    event_code?: string;
    severity_code?: string;
  }>(_payload);

  const engineId = str(args.engine_id);
  const eventCode = str(args.event_code);
  if (!engineId || !eventCode) {
    return out({ error: "missingRequiredFields", required: ["engine_id", "event_code"] });
  }

  return out({
    ok: true,
    queued: true,
    engine_id: engineId,
    aircraft_id: str(args.aircraft_id),
    cycle_count: int(args.cycle_count),
    flight_hours: int(args.flight_hours),
    event_code: eventCode,
    severity_code: str(args.severity_code) || "info",
    ts: nowISO(),
  });
}

function cmdListEngines(_payload: Uint8Array): Uint8Array {
  const args = json<{ limit?: number; offset?: number }>(_payload);
  const limit = Math.min(int(args.limit, 50), 100);
  const offset = Math.max(int(args.offset, 0), 0);
  // Edge-proxy only: actual SELECT runs in the pod. Return empty result set
  // so callers can integrate with pod responses downstream.
  return out({ items: [], total: 0, limit, offset });
}

function cmdGetEngine(_payload: Uint8Array): Uint8Array {
  const args = json<{ engine_id?: string }>(_payload);
  const engineId = str(args.engine_id);
  if (!engineId) {
    return out({ error: "missingRequiredFields", required: ["engine_id"] });
  }
  // Edge-proxy only: SELECT runs in the pod.
  return out({ error: "notFound", engine_id: engineId });
}

function cmdAddProcurementItem(_payload: Uint8Array): Uint8Array {
  const args = json<{
    engine_id?: string;
    unspsc_code?: string;
    supplier_isic_code?: string;
    quantity?: number;
    unit_cost_jpy?: number;
    supplier_id?: string;
  }>(_payload);

  const engineId = str(args.engine_id);
  const unspscCode = str(args.unspsc_code);
  const supplierIsicCode = str(args.supplier_isic_code);
  if (!engineId || !unspscCode || !supplierIsicCode) {
    return out({ error: "missingRequiredFields", required: ["engine_id", "unspsc_code", "supplier_isic_code"] });
  }

  const quantity = Math.max(1, int(args.quantity, 1));
  const unitCostJpy = Math.max(0, int(args.unit_cost_jpy, 0));

  // Validate UNSPSC code: must be 8 digits
  if (!/^\d{8}$/.test(unspscCode)) {
    return out({ error: "invalidUnspscCode", detail: "unspsc_code must be 8 digits (e.g. 25101504)" });
  }
  // Validate ISIC code: must be 4 digits
  if (!/^\d{4}$/.test(supplierIsicCode)) {
    return out({ error: "invalidIsicCode", detail: "supplier_isic_code must be 4 digits (ISIC Rev.4 class)" });
  }

  return out({
    ok: true,
    queued: true,
    engine_id: engineId,
    unspsc_code: unspscCode,
    supplier_isic_code: supplierIsicCode,
    quantity,
    unit_cost_jpy: unitCostJpy,
    total_cost_jpy: quantity * unitCostJpy,
    ts: nowISO(),
  });
}

function cmdRegisterSupplier(_payload: Uint8Array): Uint8Array {
  const args = json<{
    supplier_id?: string;
    supplier_name?: string;
    isic_code?: string;
    unspsc_segment?: string;
    country_iso3?: string;
    contact_did?: string;
  }>(_payload);

  const supplierId = str(args.supplier_id);
  const supplierName = str(args.supplier_name);
  if (!supplierId || !supplierName) {
    return out({ error: "missingRequiredFields", required: ["supplier_id", "supplier_name"] });
  }

  const isicCode = str(args.isic_code);
  if (isicCode && !/^\d{4}$/.test(isicCode)) {
    return out({ error: "invalidIsicCode", detail: "isic_code must be 4 digits (ISIC Rev.4 class)" });
  }

  // Cross-actor invoke note: openIsic.classifyEntity is invoked downstream in the pod
  // when isic_code is absent, to auto-resolve from supplier_name.
  return out({
    ok: true,
    queued: true,
    supplier_id: supplierId,
    supplier_name: supplierName,
    isic_code: isicCode || null,
    isic_label: null,  // resolved downstream via openIsic.classifyEntity
    ts: nowISO(),
  });
}

// ---------------------------------------------------------------------------
// Worker export
// ---------------------------------------------------------------------------

export default createWorkerExport((sdk) => {
  sdk.app
    .command(
      nsid("com.etzhayyim.apps.itonami.health"),
      async () => ({ ok: true, actor: "did:web:itonami.etzhayyim.com", ts: nowISO() }),
      asAgentTool("Health check for itonami — aircraft engine lifecycle simulation actor"),
      withCapabilityTags("health", "itonami", "aircraft", "simulation"),
    )
    .command(
      nsid("com.etzhayyim.apps.itonami.registerEngine"),
      async (_c, body) => cmdRegisterEngine(body),
      asAgentTool(
        "Upsert an aircraft engine record into vertex_itonami_engine. " +
        "Required: engine_id, design_code. Returns { ok, queued } — persistence is downstream.",
      ),
      withCapabilityTags("engine", "write", "itonami", "aircraft"),
    )
    .command(
      nsid("com.etzhayyim.apps.itonami.recordAssembly"),
      async (_c, body) => cmdRecordAssembly(body),
      asAgentTool(
        "Insert a build-phase milestone into vertex_itonami_assembly. " +
        "Required: engine_id, phase_code. progress_permille ∈ [0, 1000].",
      ),
      withCapabilityTags("assembly", "write", "itonami", "aircraft"),
    )
    .command(
      nsid("com.etzhayyim.apps.itonami.logTestResult"),
      async (_c, body) => cmdLogTestResult(body),
      asAgentTool(
        "Insert an engine test result into vertex_itonami_test_result. " +
        "Required: engine_id, test_type, outcome_code.",
      ),
      withCapabilityTags("test-result", "write", "itonami", "aircraft"),
    )
    .command(
      nsid("com.etzhayyim.apps.itonami.logFlightEvent"),
      async (_c, body) => cmdLogFlightEvent(body),
      asAgentTool(
        "Insert a digital twin flight event into vertex_itonami_flight_event. " +
        "Required: engine_id, event_code.",
      ),
      withCapabilityTags("flight-event", "write", "itonami", "digital-twin"),
    )
    .command(
      nsid("com.etzhayyim.apps.itonami.listEngines"),
      async (_c, body) => cmdListEngines(body),
      asAgentTool(
        "List aircraft engines from vertex_itonami_engine with offset/limit pagination. " +
        "Edge-proxy: actual data returned by the downstream pod.",
      ),
      withCapabilityTags("engine", "read", "itonami", "aircraft"),
    )
    .command(
      nsid("com.etzhayyim.apps.itonami.getEngine"),
      async (_c, body) => cmdGetEngine(body),
      asAgentTool(
        "Get an aircraft engine plus its latest test results from vertex_itonami_engine. " +
        "Required: engine_id. Edge-proxy: actual data returned by the downstream pod.",
      ),
      withCapabilityTags("engine", "read", "itonami", "aircraft"),
    )
    .command(
      nsid("com.etzhayyim.apps.itonami.addProcurementItem"),
      async (_c, body) => cmdAddProcurementItem(body),
      asAgentTool(
        "Add a UNSPSC procurement line item to an engine build. " +
        "Required: engine_id, unspsc_code (8 digits), supplier_isic_code (4 digits), quantity, unit_cost_jpy. " +
        "UNSPSC commodity spec and ISIC supplier validation are resolved downstream.",
      ),
      withCapabilityTags("procurement", "unspsc", "isic", "write", "itonami"),
    )
    .command(
      nsid("com.etzhayyim.apps.itonami.registerSupplier"),
      async (_c, body) => cmdRegisterSupplier(body),
      asAgentTool(
        "Register an aerospace parts supplier with ISIC Rev.4 industry classification. " +
        "Required: supplier_id, supplier_name. If isic_code is omitted, openIsic.classifyEntity " +
        "is invoked downstream to auto-resolve the ISIC class from supplier_name.",
      ),
      withCapabilityTags("supplier", "isic", "write", "itonami", "aerospace"),
    );
});
