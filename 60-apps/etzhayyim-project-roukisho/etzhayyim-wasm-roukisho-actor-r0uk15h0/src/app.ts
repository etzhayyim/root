// roukisho.etzhayyim.com — 労働基準監督署 (Labor Standards Inspection Office) registry
// TS Native Worker: 4 XRPC (listOffices / getOffice / recordCommunication / listCommunications)
// Directory seed is static (entities[] in kotodama.jsonld mirror). Graph reads via Kysely pending.

import {
  asAgentTool,
  createWorkerExport,
  decodeJson,
  genID,
  nowISO,
  nsid,
  str,
  withCapabilityTags,
  type HostSDK,
} from "@etzhayyim/kotodama-host-sdk";

let appId = "";

// ───────────────────────── seed directory ─────────────────────────
// Minimal seed for known offices. Full 320-office directory to be backfilled
// from jsite.mhlw.go.jp via a follow-based ingest worker (future work).

type OfficeSeed = {
  officeId: string;
  did: string;
  name: string;
  prefecture: string;
  bureau: string;
  postalCode: string;
  address: string;
  tel: string;
  fax: string;
  url: string;
  jurisdiction: string[];
  divisions: Array<{ number: number; focus: string }>;
};

const OFFICES_SEED: OfficeSeed[] = [
  {
    officeId: "jp-tokyo-chuo",
    did: "did:web:roukisho.etzhayyim.com:tokyo:chuo",
    name: "中央労働基準監督署",
    prefecture: "JP-13",
    bureau: "東京労働局",
    postalCode: "112-8573",
    address: "東京都文京区後楽1-9-20 飯田橋合同庁舎6・7階",
    tel: "+81358037381",
    fax: "+81338188411",
    url: "https://jsite.mhlw.go.jp/tokyo-roudoukyoku/",
    jurisdiction: ["千代田区", "中央区", "文京区", "島しょ"],
    divisions: [
      { number: 1, focus: "監督" },
      { number: 2, focus: "監督" },
      { number: 3, focus: "安全衛生" },
      { number: 4, focus: "労災" },
    ],
  },
];

// ───────────────────────── write helper ─────────────────────────

function write(sdk: HostSDK, kind: string, rec: Record<string, unknown>): void {
  const collection = `com.etzhayyim.apps.roukisho.${kind}`;
  const enriched = {
    ...rec,
    createdAt: nowISO(),
    org_id: "etzhayyim.com",
    user_id: "anon",
    actor_id: appId,
  };
  sdk.pds.dispatch({
    type: "com.atproto.repo.createRecord",
    payload: { collection, recordJson: JSON.stringify(enriched) },
  });
}

function officeMatches(o: OfficeSeed, prefecture?: string, bureau?: string): boolean {
  if (prefecture && o.prefecture !== prefecture && !o.prefecture.includes(prefecture)) return false;
  if (bureau && !o.bureau.includes(bureau)) return false;
  return true;
}

// ───────────────────────── commands ─────────────────────────

async function cmdListOffices(_sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const prefecture = str(args.prefecture ?? "");
  const bureau = str(args.bureau ?? "");
  const limit = Number(args.limit ?? 100);
  const offset = Number(args.offset ?? 0);
  const filtered = OFFICES_SEED.filter((o) => officeMatches(o, prefecture || undefined, bureau || undefined));
  const page = filtered.slice(offset, offset + limit);
  return { ok: true, offices: page, total: filtered.length, offset, limit };
}

async function cmdGetOffice(_sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const officeId = str(args.officeId ?? "");
  const did = str(args.did ?? "");
  if (!officeId && !did) return { ok: false, error: "officeId or did required" };
  const office = OFFICES_SEED.find((o) => (officeId && o.officeId === officeId) || (did && o.did === did));
  if (!office) return { ok: false, error: "office not found" };
  return { ok: true, office };
}

async function cmdRecordCommunication(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const direction = str(args.direction ?? "");
  const channel = str(args.channel ?? "");
  const officeId = str(args.officeId ?? "");
  if (!direction || !channel || !officeId) return { ok: false, error: "direction, channel, officeId required" };
  const recordId = genID("comm");
  const officeDid = str(args.officeDid ?? `did:web:roukisho.etzhayyim.com:${officeId.replace(/^jp-/, "").replace(/-/g, ":")}`);
  write(sdk, "communication", {
    recordId,
    direction,
    channel,
    officeId,
    officeDid,
    divisionNumber: Number(args.divisionNumber ?? 0),
    inspector: str(args.inspector ?? ""),
    caseId: str(args.caseId ?? ""),
    subject: str(args.subject ?? ""),
    summary: str(args.summary ?? ""),
    documentBlobKey: str(args.documentBlobKey ?? ""),
    faxTxId: str(args.faxTxId ?? ""),
    occurredAt: str(args.occurredAt ?? nowISO()),
  });
  return { ok: true, recordId };
}

async function cmdListCommunications(_sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const limit = Number(args.limit ?? 50);
  const offset = Number(args.offset ?? 0);
  return { ok: true, communications: [] as Array<Record<string, unknown>>, total: 0, offset, limit };
}

// ───────────────────────── Worker export ─────────────────────────

export default createWorkerExport((sdk) => {
  appId = sdk.pds.selfNanoid ?? "r0uk15h0";

  sdk.app
    .query(nsid("com.etzhayyim.apps.roukisho.listOffices"), async (_c, b) => cmdListOffices(sdk, b))
    .query(nsid("com.etzhayyim.apps.roukisho.getOffice"), async (_c, b) => cmdGetOffice(sdk, b))
    .command(nsid("com.etzhayyim.apps.roukisho.recordCommunication"), async (_c, b) => cmdRecordCommunication(sdk, b),
      asAgentTool("Record inbound/outbound communication (phone/fax/mail/visit) with a 労基署. Scoped by caseId."),
      withCapabilityTags("roukisho", "communication", "audit"))
    .query(nsid("com.etzhayyim.apps.roukisho.listCommunications"), async (_c, b) => cmdListCommunications(sdk, b));
});
