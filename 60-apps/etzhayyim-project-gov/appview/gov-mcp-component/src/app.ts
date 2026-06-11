// SUBSTRATE-PORT (ADR-2605212100 follow-up, 2026-05-24):
// - Kysely + HyperDrive Postgres writes replaced by @etzhayyim/sdk MST PUT (ADR-2605172000).
// - Lexicon `com.etzhayyim.apps.gov.*` → `com.etzhayyim.gov.*`.
// - ACTOR_DID `did:web:gov.etzhayyim.com` → `did:web:etzhayyim.com:gov`.
// - Package import `@etzhayyim/kotodama-host-sdk` PRESERVED — atomic cutover to `@etzhayyim/kotodama-host-sdk`
//   deferred to ADR-2605214000 wave.

import {
  asAgentTool,
  createKyselyDb,
  createWorkerExport,
  nowISO,
  nsid,
  parseLexiconInput,
  withCapabilityTags,
  type HostSDK,
} from "@etzhayyim/kotodama-host-sdk";
import type { Database } from "@etzhayyim/graph-schema";
import { Etzhayyim } from "@etzhayyim/sdk";

const ACTOR_DID = "did:web:etzhayyim.com:gov";

// --- Helper: SDK instance ---

function etzhayyim(sdk: HostSDK): Etzhayyim {
  const env = sdk.env as any;
  return new Etzhayyim({
    did: ACTOR_DID,
    pdsUrl: env.PDS_URL ?? "https://pds.etzhayyim.com",
    ipfsGateway: env.IPFS_GATEWAY,
    ipfsApiUrl: env.IPFS_API_URL,
    l2RpcUrl: env.L2_RPC_URL,
    anchorContract: env.ANCHOR_CONTRACT,
    signer: env.SIGNER,
  });
}

// --- Register Agency ---

async function cmdRegisterAgency(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.gov.registerAgency", body);
  const {
    name, nameLocal, jurisdiction, branch, level, cofog,
    parentAgencyDid, establishedAt, legalBasis, websiteUri,
  } = args;

  const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40);
  const path = `${jurisdiction?.toLowerCase() ?? "xx"}:${cofog ?? "00"}:${slug}`;
  const did = `${ACTOR_DID}:${path}`;
  const rkey = slug + "-" + Date.now().toString(36);
  const now = nowISO();

  const e = etzhayyim(sdk);
  const receipt = await e.write({
    collection: "com.etzhayyim.gov.agency",
    record: {
      name,
      nameLocal: nameLocal ?? undefined,
      jurisdiction: jurisdiction ?? "",
      branch: branch ?? undefined,
      level: level ?? undefined,
      cofog: cofog ?? undefined,
      parentAgencyDid: parentAgencyDid ?? undefined,
      establishedAt: establishedAt ?? undefined,
      legalBasis: legalBasis ?? undefined,
      websiteUri: websiteUri ?? undefined,
      agencyDid: did,
      createdAt: now,
      updatedAt: now,
    },
  });

  return { did, uri: receipt.uri };
}

// --- Record Official ---

async function cmdRecordOfficial(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.gov.recordOfficial", body);
  const {
    agencyDid, personDid, role, appointedAt,
    termEndsAt, appointedByDid, confirmationProcess,
  } = args;

  const rkey = role.toLowerCase().replace(/[^a-z0-9]+/g, "-") + "-" + Date.now().toString(36);
  const now = nowISO();

  const e = etzhayyim(sdk);
  const receipt = await e.write({
    collection: "com.etzhayyim.gov.official",
    record: {
      agencyDid: agencyDid ?? "",
      personDid: personDid ?? undefined,
      role: role ?? "",
      appointedAt: appointedAt ?? "",
      termEndsAt: termEndsAt ?? undefined,
      appointedByDid: appointedByDid ?? undefined,
      confirmationProcess: confirmationProcess ?? undefined,
      createdAt: now,
      updatedAt: now,
    },
  });

  return { uri: receipt.uri };
}

// --- Submit Consult ---

async function cmdSubmitConsult(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.gov.submitConsult", body);
  const { requesterDid, domain, category, query, municipalityCode, priority } = args;

  const rkey = domain + "-" + Date.now().toString(36);
  const now = nowISO();

  const e = etzhayyim(sdk);
  const receipt = await e.write({
    collection: "com.etzhayyim.gov.consult",
    record: {
      requesterDid: requesterDid ?? "",
      domain: domain ?? "",
      category: category ?? undefined,
      query: query ?? "",
      municipalityCode: municipalityCode ?? undefined,
      priority: priority ?? "normal",
      status: "open",
      createdAt: now,
      updatedAt: now,
    },
  });

  return { id: rkey, status: "open" };
}

// --- List Agencies ---

async function cmdListAgencies(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.gov.listAgencies", body);
  const { jurisdiction, branch, level, cofog, parentAgencyDid } = args;
  const limit = Math.min(Number(args.limit) || 50, 200);
  const cursor = args.cursor as string | undefined;

  const e = etzhayyim(sdk);
  const { records, cursor: nextCursor } = await e.read<Record<string, unknown>>({
    collection: "com.etzhayyim.gov.agency",
    limit,
    cursor,
  });

  // MST has no native WHERE — filter in memory after read.
  const filtered = records.map((r) => r.value).filter((r: any) => {
    if (jurisdiction && r.jurisdiction !== jurisdiction) return false;
    if (branch && r.branch !== branch) return false;
    if (level && r.level !== level) return false;
    if (cofog && r.cofog !== cofog) return false;
    if (parentAgencyDid && r.parentAgencyDid !== parentAgencyDid) return false;
    return true;
  });

  const agencies = filtered.map((r: any) => ({
    did: `${ACTOR_DID}:${r.jurisdiction}:${r.cofog}:${r.name?.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40)}`,
    name: r.name,
    nameLocal: r.nameLocal,
    jurisdiction: r.jurisdiction,
    branch: r.branch,
    cofog: r.cofog,
  }));

  return { agencies, cursor: nextCursor };
}

// --- Get Agency ---

async function cmdGetAgency(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const { id } = parseLexiconInput("com.etzhayyim.gov.getAgency", body);

  const e = etzhayyim(sdk);
  const { records } = await e.read<Record<string, unknown>>({
    collection: "com.etzhayyim.gov.agency",
    rkey: id,
  });

  if (records.length === 0) return { agency: null, officials: [] };

  const agency = records[0]?.value as any;
  if (!agency) return { agency: null, officials: [] };

  // Get officials for this agency.
  const { records: officialRecords } = await e.read<Record<string, unknown>>({
    collection: "com.etzhayyim.gov.official",
    limit: 50,
  });

  const agencyDid = `${ACTOR_DID}:${agency.jurisdiction}:${agency.cofog}:${id}`;
  const officials = officialRecords
    .map((r) => r.value as any)
    .filter((o: any) => o.agencyDid === agencyDid)
    .map((o: any) => ({
      personDid: o.personDid,
      role: o.role,
      appointedAt: o.appointedAt,
      termEndsAt: o.termEndsAt,
    }));

  return { agency, officials };
}

// --- List Officials ---

async function cmdListOfficials(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.gov.listOfficials", body);
  const { agencyDid, role } = args;
  const limit = Math.min(Number(args.limit) || 50, 200);
  const cursor = args.cursor as string | undefined;

  const e = etzhayyim(sdk);
  const { records, cursor: nextCursor } = await e.read<Record<string, unknown>>({
    collection: "com.etzhayyim.gov.official",
    limit,
    cursor,
  });

  // MST has no native WHERE — filter in memory after read.
  const filtered = records.map((r) => r.value).filter((o: any) => {
    if (agencyDid && o.agencyDid !== agencyDid) return false;
    if (role && o.role !== role) return false;
    return true;
  });

  return { officials: filtered, cursor: nextCursor };
}

// --- List Municipalities ---

async function cmdListMunicipalities(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.gov.listMunicipalities", body);
  const { prefecture } = args;
  const limit = Math.min(Number(args.limit) || 50, 200);
  const cursor = args.cursor as string | undefined;

  const e = etzhayyim(sdk);
  const { records, cursor: nextCursor } = await e.read<Record<string, unknown>>({
    collection: "com.etzhayyim.gov.municipality",
    limit,
    cursor,
  });

  // MST has no native WHERE — filter in memory after read.
  const filtered = records.map((r) => r.value).filter((m: any) => {
    if (prefecture && m.prefecture !== prefecture) return false;
    return true;
  });

  return { municipalities: filtered, cursor: nextCursor };
}

// --- List Consults ---

async function cmdListConsults(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.gov.listConsults", body);
  const { requesterDid, domain, status } = args;
  const limit = Math.min(Number(args.limit) || 50, 200);
  const cursor = args.cursor as string | undefined;

  const e = etzhayyim(sdk);
  const { records, cursor: nextCursor } = await e.read<Record<string, unknown>>({
    collection: "com.etzhayyim.gov.consult",
    limit,
    cursor,
  });

  // MST has no native WHERE — filter in memory after read.
  const filtered = records.map((r) => r.value).filter((c: any) => {
    if (requesterDid && c.requesterDid !== requesterDid) return false;
    if (domain && c.domain !== domain) return false;
    if (status && c.status !== status) return false;
    return true;
  });

  return { consults: filtered, cursor: nextCursor };
}

// --- Export ---

export default createWorkerExport((sdk) => {
  sdk.app
    .command(nsid("com.etzhayyim.gov.registerAgency"), (ctx, body) => cmdRegisterAgency(sdk, body),
      asAgentTool("Register a government agency with jurisdiction, branch, and COFOG classification"),
      withCapabilityTags("gov", "agency", "public-services"),
    )
    .command(nsid("com.etzhayyim.gov.recordOfficial"), (ctx, body) => cmdRecordOfficial(sdk, body),
      asAgentTool("Record a public official appointment to a government agency role"),
      withCapabilityTags("gov", "official", "public-services"),
    )
    .command(nsid("com.etzhayyim.gov.submitConsult"), (ctx, body) => cmdSubmitConsult(sdk, body),
      asAgentTool("Submit a public services consultation (healthcare, welfare, education, housing, employment)"),
      withCapabilityTags("gov", "consult", "public-services"),
    )
    .query(nsid("com.etzhayyim.gov.listAgencies"), (ctx, body) => cmdListAgencies(sdk, body),
      asAgentTool("List government agencies with jurisdiction/branch/COFOG filters"),
      withCapabilityTags("gov", "agency", "public-services"),
    )
    .query(nsid("com.etzhayyim.gov.getAgency"), (ctx, body) => cmdGetAgency(sdk, body),
      asAgentTool("Get a government agency by ID including current officials"),
      withCapabilityTags("gov", "agency", "public-services"),
    )
    .query(nsid("com.etzhayyim.gov.listOfficials"), (ctx, body) => cmdListOfficials(sdk, body),
      asAgentTool("List public officials for a government agency"),
      withCapabilityTags("gov", "official", "public-services"),
    )
    .query(nsid("com.etzhayyim.gov.listMunicipalities"), (ctx, body) => cmdListMunicipalities(sdk, body),
      asAgentTool("List municipalities with optional prefecture filter"),
      withCapabilityTags("gov", "municipality", "public-services"),
    )
    .query(nsid("com.etzhayyim.gov.listConsults"), (ctx, body) => cmdListConsults(sdk, body),
      asAgentTool("List public services consultations for a requester"),
      withCapabilityTags("gov", "consult", "public-services"),
    );
});
