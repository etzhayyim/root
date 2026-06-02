import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed vertex_bpmn_process_def + vertex_bpmn_lexicon_binding for the
// airline operations cluster (10 actors, 80 BPMN processes).
// Actors: air-sched / air-book / air-yield / air-dcs / air-ops /
//         air-crew / air-mro / air-sms / air-cargo / air-ffp
// BPMN files that already exist on disk are read and embedded verbatim.
// Missing files receive a minimal stub XML so the migration is idempotent
// regardless of BPMN authoring progress; the F5 watcher skips deploy for stubs.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-05-07T12:00:00Z";
const ACTOR_ID = "sys.bpmn.seed.airline";

const snake = (s: string) => s.replace(/([A-Z])/g, "_$1").toLowerCase();
const slug = (s: string) => s.replace(/([A-Z])/g, "-$1").toLowerCase();

function readBpmn(relPath: string): string {
  const abs = path.resolve(repoRoot, relPath);
  if (existsSync(abs)) return readFileSync(abs, "utf8");
  // Minimal stub — F5 watcher skips Zeebe deploy when status='stub'
  const processId = path.basename(relPath, ".bpmn");
  return `<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="${processId}" targetNamespace="http://etzhayyim.com"><bpmn:process id="${processId}" isExecutable="false"/></bpmn:definitions>`;
}

type ActorEntry = {
  actor: string;          // e.g. "air-sched"
  actorDid: string;       // e.g. "did:web:air-sched.etzhayyim.com"
  procs: string[];        // camelCase method names
};

const ACTORS: ActorEntry[] = [
  {
    actor: "air-sched",
    actorDid: "did:web:air-sched.etzhayyim.com",
    procs: [
      "registerSchedule", "requestSlot", "allocateSlot", "assignFleet",
      "publishSchedule", "assignGate", "changeFrequency", "registerCodeshare",
    ],
  },
  {
    actor: "air-book",
    actorDid: "did:web:air-book.etzhayyim.com",
    procs: [
      "createPnr", "confirmBooking", "issueTicket", "assignSeat",
      "addAncillary", "cancelBooking", "reprotectPassenger", "settleBsp",
    ],
  },
  {
    actor: "air-yield",
    actorDid: "did:web:air-yield.etzhayyim.com",
    procs: [
      "publishFareClass", "adjustInventory", "fileFare", "setOverbooking",
      "processGroupBooking", "applyDynamicPrice", "generateRevenueReport", "forecastDemand",
    ],
  },
  {
    actor: "air-dcs",
    actorDid: "did:web:air-dcs.etzhayyim.com",
    procs: [
      "processCheckIn", "processBoardingPass", "acceptBaggage", "reconcileBaggage",
      "computeLoadSheet", "transmitApis", "trackTurnaround", "issueDepartureControl",
    ],
  },
  {
    actor: "air-ops",
    actorDid: "did:web:air-ops.etzhayyim.com",
    procs: [
      "fileFlightPlan", "createDispatchBrief", "fetchNotam", "fetchWeatherBrief",
      "recordTechLog", "orderFuel", "submitPirep", "monitorFlight",
    ],
  },
  {
    actor: "air-crew",
    actorDid: "did:web:air-crew.etzhayyim.com",
    procs: [
      "publishRoster", "buildPairing", "trackQualification", "assessFatigue",
      "assignCrew", "bookCrewTravel", "recordDutyTime", "notifyCrew",
    ],
  },
  {
    actor: "air-mro",
    actorDid: "did:web:air-mro.etzhayyim.com",
    procs: [
      "createWorkOrder", "trackComponent", "checkAirworthiness", "reportTechOccurrence",
      "scheduleMaintenance", "reportReliability", "orderSparePart", "recordGroundEquipment",
    ],
  },
  {
    actor: "air-sms",
    actorDid: "did:web:air-sms.etzhayyim.com",
    procs: [
      "submitSafetyReport", "assessRisk", "recordIosaFinding", "fileRegulatoryReport",
      "reportOccurrence", "distributeSafetyBulletin", "screenDangerousGoods", "handleSecurityAlert",
    ],
  },
  {
    actor: "air-cargo",
    actorDid: "did:web:air-cargo.etzhayyim.com",
    procs: [
      "createCargoBooking", "issueAirWaybill", "acceptCargo", "assignUld",
      "trackShipment", "processClaim", "settleCargoAccount", "reportCargoSecurity",
    ],
  },
  {
    actor: "air-ffp",
    actorDid: "did:web:air-ffp.etzhayyim.com",
    procs: [
      "enrollMember", "accruePoints", "redeemReward", "updateTier",
      "transferMiles", "processPurchase", "expireMiles", "reconcilePartner",
    ],
  },
];

type Row = {
  processVid: string;
  bindingVid: string;
  bpmnProcessId: string;
  nsid: string;
  sourcePath: string;
  ownerDid: string;
};

function buildRows(): Row[] {
  const rows: Row[] = [];
  for (const a of ACTORS) {
    for (const proc of a.procs) {
      const bpmnProcessId = `${a.actor.replace(/-/g, "_")}_${snake(proc)}`;
      const procSlug = `${a.actor}-${slug(proc)}`;
      rows.push({
        processVid: `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${procSlug}-v1`,
        bindingVid: `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${procSlug}-v1`,
        bpmnProcessId,
        nsid: `com.etzhayyim.apps.${a.actor.replace(/-([a-z])/g, (_, c) => c.toUpperCase())}.${proc}`,
        sourcePath: `00-contracts/bpmn/com/etzhayyim/${a.actor}/${proc}.bpmn`,
        ownerDid: a.actorDid,
      });
    }
  }
  return rows;
}

export async function up(db: Kysely<unknown>): Promise<void> {
  const rows = buildRows();
  for (const r of rows) {
    const xml = readBpmn(r.sourcePath);
    const xmlByteSize = Buffer.byteLength(xml, "utf8");
    const isStub = !existsSync(path.resolve(repoRoot, r.sourcePath));
    const status = isStub ? "stub" : "active";

    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord,
        org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${r.processVid}, ${r.ownerDid}, ${r.bpmnProcessId}, 1,
        ${xml}, ${sql.raw(String(xmlByteSize))}, ${r.sourcePath}, ${status},
        ${CREATED_AT}, 100, ${r.ownerDid}, ${r.ownerDid}, ${ACTOR_ID},
        ${r.ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${r.processVid}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, status, created_at, sensitivity_ord,
        org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${r.bindingVid}, ${r.ownerDid}, ${r.nsid}, ${r.bpmnProcessId}, 1,
        15000, ${status}, ${CREATED_AT}, 100,
        ${r.ownerDid}, ${r.ownerDid}, ${ACTOR_ID},
        ${r.ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${r.bindingVid}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  const rows = buildRows();
  for (const r of rows) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${r.bindingVid}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${r.processVid}`.execute(db);
  }
}
