import {
  tableFromArrays,
  tableToIPC,
  Utf8,
  Float64,
  Int64,
  Field,
  Schema,
} from "apache-arrow";

interface FieldDef {
  name: string;
  type: "string" | "float64" | "int64";
}

interface TableSeed {
  name: string;
  fields: FieldDef[];
  rows: Record<string, unknown>[];
  deleteIDs: string[];
}

const DEFAULT_BASE_URL = "http://127.0.0.1:18084";

async function main(): Promise<void> {
  const baseURL = (process.argv[2] ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
  const now = new Date().toISOString();

  for (const table of buildSeeds(now)) {
    await seedTable(baseURL, table);
  }
}

async function seedTable(baseURL: string, table: TableSeed): Promise<void> {
  for (const id of table.deleteIDs) {
    try {
      await doJSON(
        baseURL + "/v1/table/" + table.name + "/delete",
        { predicate: `_doc_id = '${id}'` },
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      if (!msg.includes("not found")) {
        throw new Error(`delete ${table.name}/${id}: ${msg}`);
      }
    }
  }

  const schema = buildSchema(table.fields);
  const createBody = encodeArrowStream(schema, table.fields, []);
  const createRes = await doArrow(
    baseURL + "/v1/table/" + table.name + "/create",
    createBody,
  );
  if (!createRes.ok && createRes.status !== 409) {
    throw new Error(
      `create ${table.name}: status=${createRes.status} body=${createRes.body}`,
    );
  }

  const mergeBody = encodeArrowStream(schema, table.fields, table.rows);
  const mergeRes = await doArrow(
    baseURL +
      "/v1/table/" +
      table.name +
      "/mergeInsert?on=_doc_id",
    mergeBody,
  );
  if (!mergeRes.ok) {
    throw new Error(
      `mergeInsert ${table.name}: status=${mergeRes.status} body=${mergeRes.body}`,
    );
  }

  const countRes = await doJSON(
    baseURL + "/v1/table/" + table.name + "/countRows",
    {},
  );
  console.log(`${table.name} ${countRes.trim()}`);
}

function buildSchema(fields: FieldDef[]): Schema {
  const arrowFields = fields.map((f) => {
    switch (f.type) {
      case "float64":
        return new Field(f.name, new Float64(), true);
      case "int64":
        return new Field(f.name, new Int64(), true);
      default:
        return new Field(f.name, new Utf8(), true);
    }
  });
  return new Schema(arrowFields);
}

function encodeArrowStream(
  schema: Schema,
  fields: FieldDef[],
  rows: Record<string, unknown>[],
): Uint8Array {
  const columns: Record<string, unknown[]> = {};
  for (const f of fields) {
    columns[f.name] = [];
  }
  for (const row of rows) {
    for (const f of fields) {
      const v = row[f.name];
      if (v === undefined || v === null) {
        columns[f.name].push(null);
      } else if (f.type === "float64") {
        columns[f.name].push(Number(v));
      } else if (f.type === "int64") {
        columns[f.name].push(BigInt(Math.trunc(Number(v))));
      } else {
        columns[f.name].push(String(v));
      }
    }
  }
  const table = tableFromArrays(columns);
  return tableToIPC(table, "stream");
}

async function doArrow(
  url: string,
  body: Uint8Array,
): Promise<{ ok: boolean; status: number; body: string }> {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/vnd.apache.arrow.stream" },
    body,
  });
  const raw = await resp.text();
  return { ok: resp.ok, status: resp.status, body: raw };
}

async function doJSON(url: string, payload: unknown): Promise<string> {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const raw = await resp.text();
  if (!resp.ok) {
    throw new Error(`status=${resp.status} body=${raw}`);
  }
  return raw;
}

function row(
  now: string,
  docID: string,
  extra: Record<string, unknown>,
): Record<string, unknown> {
  return {
    _doc_id: docID,
    'orgId': "anon",
    'userId': "anon",
    'actorId': "sys.yabai-seed",
    'updatedAt': now,
    ...extra,
  };
}

function buildSeeds(now: string): TableSeed[] {
  const s = "string" as const;
  const f = "float64" as const;
  const i = "int64" as const;

  const entitiesFields: FieldDef[] = [
    { name: "_doc_id", type: s },
    { name: "orgId", type: s },
    { name: "userId", type: s },
    { name: "actorId", type: s },
    { name: "entityId", type: s },
    { name: "entityType", type: s },
    { name: "contactKind", type: s },
    { name: "normalizedValue", type: s },
    { name: "canonicalName", type: s },
    { name: "aliasesJson", type: s },
    { name: "contactsJson", type: s },
    { name: "websitesJson", type: s },
    { name: "contextUrl", type: s },
    { name: "updatedAt", type: s },
  ];
  const evidencesFields: FieldDef[] = [
    { name: "_doc_id", type: s },
    { name: "orgId", type: s },
    { name: "userId", type: s },
    { name: "actorId", type: s },
    { name: "evidenceId", type: s },
    { name: "entityId", type: s },
    { name: "category", type: s },
    { name: "source", type: s },
    { name: "sourceReliability", type: s },
    { name: "occurredAt", type: s },
    { name: "confidence", type: f },
    { name: "severity", type: i },
    { name: "probability", type: f },
    { name: "jurisdiction", type: s },
    { name: "summary", type: s },
    { name: "updatedAt", type: s },
  ];
  const risksFields: FieldDef[] = [
    { name: "_doc_id", type: s },
    { name: "orgId", type: s },
    { name: "userId", type: s },
    { name: "actorId", type: s },
    { name: "entityId", type: s },
    { name: "wellBecomingScore", type: f },
    { name: "penaltyScore", type: f },
    { name: "yabaiRiskScore", type: f },
    { name: "infoRisk", type: f },
    { name: "scoredAt", type: s },
    { name: "updatedAt", type: s },
  ];
  const watchlistFields: FieldDef[] = [
    { name: "_doc_id", type: s },
    { name: "orgId", type: s },
    { name: "userId", type: s },
    { name: "actorId", type: s },
    { name: "signalId", type: s },
    { name: "entityType", type: s },
    { name: "matchKind", type: s },
    { name: "matchMode", type: s },
    { name: "matchValue", type: s },
    { name: "value", type: s },
    { name: "category", type: s },
    { name: "source", type: s },
    { name: "confidence", type: f },
    { name: "severity", type: i },
    { name: "probability", type: f },
    { name: "jurisdiction", type: s },
    { name: "updatedAt", type: s },
  ];
  const sourcesFields: FieldDef[] = [
    { name: "_doc_id", type: s },
    { name: "orgId", type: s },
    { name: "userId", type: s },
    { name: "actorId", type: s },
    { name: "sourceId", type: s },
    { name: "sourceType", type: s },
    { name: "name", type: s },
    { name: "url", type: s },
    { name: "note", type: s },
    { name: "updatedAt", type: s },
  ];

  const deleteEntityIDs = [
    "ent-1525c83cc9df", "ent-2b83ca523824", "ent-2c02ded7260a", "ent-b01070e33474", "ent-00b91cfeda09",
    "ent-407333bba1fb", "ent-418b48610118", "ent-71619516eca8", "ent-9a0bfc43c0ab", "ent-de5f7f7990df",
    "ent-ph01-050999", "ent-ph02-0120xx", "ent-ph03-intl44", "ent-em01-prize", "ent-em02-ceo", "ent-em03-support",
    "ent-ws01-bank", "ent-ws02-crypto", "ent-ws03-govt", "ent-ws04-delivery",
  ];
  const deleteEvidenceIDs = [
    "evidence-0d39e63d50b91a25", "evidence-bec4acde4969ce1e", "evidence-9a92aaef6fdc5ab6", "evidence-780cc32b8557a61d",
    "evidence-ph01-spam-call", "evidence-ph02-robo", "evidence-ph03-vishing", "evidence-em01-lottery", "evidence-em02-bec",
    "evidence-em03-bank", "evidence-ws01-phish", "evidence-ws02-crypto", "evidence-ws03-govt", "evidence-ws04-delivery",
  ];
  const deleteWatchlistIDs = ["wl-001", "wl-002", "wl-003", "wl-004", "wl-005", "wl-006", "wl-007", "wl-008"];
  const deleteSourceIDs = ["resources-crawl", "resources-legal", "operator-watchlist", "yabai-design"];

  const entities: Record<string, unknown>[] = [
    row(now, "ent-crypto-braden-karony", { 'entityId': "ent-crypto-braden-karony", 'entityType': "Person", 'canonicalName': "Braden John Karony", 'aliasesJson': '["Braden Karony"]', 'contextUrl': "https://www.justice.gov/usao-edny/pr/founder-and-key-employees-safemoon-charged-multi-million-dollar-international-fraud" }),
    row(now, "ent-crypto-safemoon-llc", { 'entityId': "ent-crypto-safemoon-llc", 'entityType': "Organization", 'canonicalName': "SafeMoon US LLC", 'aliasesJson': '["SafeMoon"]', 'contextUrl': "https://www.justice.gov/usao-edny/pr/founder-and-key-employees-safemoon-charged-multi-million-dollar-international-fraud" }),
    row(now, "ent-crypto-safemoon-token", { 'entityId': "ent-crypto-safemoon-token", 'entityType': "Product", 'canonicalName': "SafeMoon (SFM)", 'aliasesJson': '["SFM","SafeMoon Token"]', 'contextUrl': "https://www.justice.gov/usao-edny/pr/founder-and-key-employees-safemoon-charged-multi-million-dollar-international-fraud" }),
    row(now, "ent-crypto-do-kwon", { 'entityId': "ent-crypto-do-kwon", 'entityType': "Person", 'canonicalName': "Do Hyeong Kwon", 'aliasesJson': '["Do Kwon"]', 'contextUrl': "https://www.justice.gov/opa/pr/do-hyeong-kwon-extradited-united-states-face-fraud-charges-related-collapse-terraform" }),
    row(now, "ent-crypto-terraform", { 'entityId': "ent-crypto-terraform", 'entityType': "Organization", 'canonicalName': "Terraform Labs PTE. Ltd.", 'aliasesJson': '["Terraform Labs"]', 'contextUrl': "https://www.sec.gov/newsroom/press-releases/2024-73" }),
    row(now, "ent-crypto-ust", { 'entityId': "ent-crypto-ust", 'entityType': "Product", 'canonicalName': "TerraUSD (UST)", 'aliasesJson': '["UST","TerraUSD"]', 'contextUrl': "https://www.sec.gov/newsroom/press-releases/2024-73" }),
    row(now, "ent-crypto-luna", { 'entityId': "ent-crypto-luna", 'entityType': "Product", 'canonicalName': "LUNA", 'aliasesJson': '["Terra (LUNA)"]', 'contextUrl': "https://www.sec.gov/newsroom/press-releases/2024-73" }),
    row(now, "ent-crypto-karl-greenwood", { 'entityId': "ent-crypto-karl-greenwood", 'entityType': "Person", 'canonicalName': "Karl Sebastian Greenwood", 'aliasesJson': '["Karl Greenwood"]', 'contextUrl': "https://www.justice.gov/usao-sdny/pr/co-founder-onecoin-sentenced-20-years-prison-fraud-and-money-laundering-schemes" }),
    row(now, "ent-crypto-ruja-ignatova", { 'entityId': "ent-crypto-ruja-ignatova", 'entityType': "Person", 'canonicalName': "Ruja Ignatova", 'aliasesJson': '["Cryptoqueen"]', 'contextUrl': "https://www.justice.gov/usao-sdny/pr/co-founder-onecoin-sentenced-20-years-prison-fraud-and-money-laundering-schemes" }),
    row(now, "ent-crypto-onecoin", { 'entityId': "ent-crypto-onecoin", 'entityType': "Product", 'canonicalName': "OneCoin", 'aliasesJson': '["OneCoin Token"]', 'contextUrl': "https://www.justice.gov/usao-sdny/pr/co-founder-onecoin-sentenced-20-years-prison-fraud-and-money-laundering-schemes" }),
    row(now, "ent-crypto-bitconnect", { 'entityId': "ent-crypto-bitconnect", 'entityType': "Organization", 'canonicalName': "BitConnect", 'aliasesJson': '["BitConnect Lending Program"]', 'contextUrl': "https://www.sec.gov/newsroom/press-releases/2021-172" }),
    row(now, "ent-crypto-satish-kumbhani", { 'entityId': "ent-crypto-satish-kumbhani", 'entityType': "Person", 'canonicalName': "Satish Kumbhani", 'aliasesJson': '["BitConnect founder"]', 'contextUrl': "https://www.sec.gov/newsroom/press-releases/2021-172" }),
    row(now, "ent-crypto-bcc", { 'entityId': "ent-crypto-bcc", 'entityType': "Product", 'canonicalName': "BitConnect Coin (BCC)", 'aliasesJson': '["BCC"]', 'contextUrl': "https://www.sec.gov/newsroom/press-releases/2021-172" }),
    row(now, "ent-crypto-tornado-cash", { 'entityId': "ent-crypto-tornado-cash", 'entityType': "Organization", 'canonicalName': "Tornado Cash", 'aliasesJson': '["Tornado Cash mixer"]', 'contextUrl': "https://ofac.treasury.gov/recent-actions/20220808" }),
    row(now, "ent-crypto-roman-semenov", { 'entityId': "ent-crypto-roman-semenov", 'entityType': "Person", 'canonicalName': "Roman Semenov", 'aliasesJson': '["Tornado Cash co-founder"]', 'contextUrl': "https://ofac.treasury.gov/recent-actions/20250321" }),
  ];

  const evidences: Record<string, unknown>[] = [
    row(now, "ev-crypto-safemoon-karony", { 'evidenceId': "ev-crypto-safemoon-karony", 'entityId': "ent-crypto-braden-karony", category: "CriminalEvidence", source: "justice/usao-edny/safemoon-2023-11-01", 'sourceReliability': "A", 'occurredAt': "2023-11-01T00:00:00Z", confidence: 0.97, severity: 5, probability: 0.01, jurisdiction: "US", summary: "DOJ announced fraud and securities-fraud conspiracy charges tied to SafeMoon." }),
    row(now, "ev-crypto-safemoon-llc", { 'evidenceId': "ev-crypto-safemoon-llc", 'entityId': "ent-crypto-safemoon-llc", category: "CriminalEvidence", source: "justice/usao-edny/safemoon-2023-11-01", 'sourceReliability': "A", 'occurredAt': "2023-11-01T00:00:00Z", confidence: 0.95, severity: 5, probability: 0.01, jurisdiction: "US", summary: "SafeMoon operating entity appeared in the DOJ SafeMoon fraud case." }),
    row(now, "ev-crypto-safemoon-token", { 'evidenceId': "ev-crypto-safemoon-token", 'entityId': "ent-crypto-safemoon-token", category: "FraudSignal", source: "justice/usao-edny/safemoon-2023-11-01", 'sourceReliability': "A", 'occurredAt': "2023-11-01T00:00:00Z", confidence: 0.93, severity: 5, probability: 0.02, jurisdiction: "US", summary: "SafeMoon token linked to alleged misappropriation and misleading statements." }),
    row(now, "ev-crypto-do-kwon-doj", { 'evidenceId': "ev-crypto-do-kwon-doj", 'entityId': "ent-crypto-do-kwon", category: "CriminalEvidence", source: "justice/criminal-vns/do-kwon-2024-12-31", 'sourceReliability': "A", 'occurredAt': "2024-12-31T00:00:00Z", confidence: 0.97, severity: 5, probability: 0.01, jurisdiction: "US", summary: "DOJ announced Do Kwon extradition to face fraud charges related to Terraform collapse." }),
    row(now, "ev-crypto-terraform-sec", { 'evidenceId': "ev-crypto-terraform-sec", 'entityId': "ent-crypto-terraform", category: "FraudSignal", source: "sec/terraform-2024-06-13", 'sourceReliability': "A", 'occurredAt': "2024-06-13T00:00:00Z", confidence: 0.95, severity: 5, probability: 0.02, jurisdiction: "US", summary: "SEC announced settlement after Terraform and Kwon were found liable for fraud." }),
    row(now, "ev-crypto-ust-sec", { 'evidenceId': "ev-crypto-ust-sec", 'entityId': "ent-crypto-ust", category: "FraudSignal", source: "sec/terraform-2024-06-13", 'sourceReliability': "A", 'occurredAt': "2024-06-13T00:00:00Z", confidence: 0.94, severity: 5, probability: 0.02, jurisdiction: "US", summary: "UST collapse formed part of the SEC Terraform fraud case." }),
    row(now, "ev-crypto-luna-sec", { 'evidenceId': "ev-crypto-luna-sec", 'entityId': "ent-crypto-luna", category: "FraudSignal", source: "sec/terraform-2024-06-13", 'sourceReliability': "A", 'occurredAt': "2024-06-13T00:00:00Z", confidence: 0.94, severity: 5, probability: 0.02, jurisdiction: "US", summary: "LUNA collapse formed part of the SEC Terraform fraud case." }),
    row(now, "ev-crypto-greenwood", { 'evidenceId': "ev-crypto-greenwood", 'entityId': "ent-crypto-karl-greenwood", category: "CriminalEvidence", source: "justice/usao-sdny/onecoin-2023-09-12", 'sourceReliability': "A", 'occurredAt': "2023-09-12T00:00:00Z", confidence: 0.96, severity: 5, probability: 0.01, jurisdiction: "US", summary: "DOJ announced sentencing of OneCoin co-founder Karl Greenwood for fraud and money laundering." }),
    row(now, "ev-crypto-ignatova", { 'evidenceId': "ev-crypto-ignatova", 'entityId': "ent-crypto-ruja-ignatova", category: "CriminalEvidence", source: "justice/usao-sdny/onecoin-2023-09-12", 'sourceReliability': "A", 'occurredAt': "2023-09-12T00:00:00Z", confidence: 0.92, severity: 5, probability: 0.02, jurisdiction: "US", summary: "OneCoin prosecution identified Ruja Ignatova as a central actor in the scheme." }),
    row(now, "ev-crypto-onecoin", { 'evidenceId': "ev-crypto-onecoin", 'entityId': "ent-crypto-onecoin", category: "CriminalEvidence", source: "justice/usao-sdny/onecoin-2023-09-12", 'sourceReliability': "A", 'occurredAt': "2023-09-12T00:00:00Z", confidence: 0.95, severity: 5, probability: 0.01, jurisdiction: "US", summary: "OneCoin was described by DOJ as a multi-billion-dollar fraud scheme." }),
    row(now, "ev-crypto-bitconnect-org", { 'evidenceId': "ev-crypto-bitconnect-org", 'entityId': "ent-crypto-bitconnect", category: "FraudSignal", source: "sec/bitconnect-2021-09-01", 'sourceReliability': "A", 'occurredAt': "2021-09-01T00:00:00Z", confidence: 0.94, severity: 5, probability: 0.02, jurisdiction: "US", summary: "SEC charged BitConnect over an alleged unregistered offering and promoter network." }),
    row(now, "ev-crypto-bitconnect-satish", { 'evidenceId': "ev-crypto-bitconnect-satish", 'entityId': "ent-crypto-satish-kumbhani", category: "FraudSignal", source: "sec/bitconnect-2021-09-01", 'sourceReliability': "A", 'occurredAt': "2021-09-01T00:00:00Z", confidence: 0.94, severity: 5, probability: 0.02, jurisdiction: "US", summary: "SEC named Satish Kumbhani in the BitConnect enforcement action." }),
    row(now, "ev-crypto-bitconnect-bcc", { 'evidenceId': "ev-crypto-bitconnect-bcc", 'entityId': "ent-crypto-bcc", category: "FraudSignal", source: "sec/bitconnect-2021-09-01", 'sourceReliability': "A", 'occurredAt': "2021-09-01T00:00:00Z", confidence: 0.93, severity: 5, probability: 0.02, jurisdiction: "US", summary: "BCC token was promoted in the BitConnect program flagged by the SEC." }),
    row(now, "ev-crypto-tornado-ofac", { 'evidenceId': "ev-crypto-tornado-ofac", 'entityId': "ent-crypto-tornado-cash", category: "SanctionHit", source: "ofac/tornado-cash-2022-08-08", 'sourceReliability': "A", 'occurredAt': "2022-08-08T00:00:00Z", confidence: 0.98, severity: 5, probability: 0.005, jurisdiction: "US", summary: "OFAC designated Tornado Cash under U.S. sanctions." }),
    row(now, "ev-crypto-tornado-aml", { 'evidenceId': "ev-crypto-tornado-aml", 'entityId': "ent-crypto-tornado-cash", category: "AMLPattern", source: "ofac/roman-semenov-2025-03-21", 'sourceReliability': "A", 'occurredAt': "2025-03-21T00:00:00Z", confidence: 0.97, severity: 5, probability: 0.01, jurisdiction: "US", summary: "OFAC maintained sanctions context around Tornado Cash and laundering concerns." }),
    row(now, "ev-crypto-roman", { 'evidenceId': "ev-crypto-roman", 'entityId': "ent-crypto-roman-semenov", category: "SanctionHit", source: "ofac/roman-semenov-2025-03-21", 'sourceReliability': "A", 'occurredAt': "2025-03-21T00:00:00Z", confidence: 0.98, severity: 5, probability: 0.005, jurisdiction: "US", summary: "OFAC updated sanctions-related designation context tied to Roman Semenov." }),
  ];

  const risks: Record<string, unknown>[] = [
    row(now, "ent-crypto-braden-karony", { 'entityId': "ent-crypto-braden-karony", 'wellBecomingScore': 8.0, 'penaltyScore': 50.0, 'yabaiRiskScore': 99.0, 'infoRisk': 8.9, 'scoredAt': now }),
    row(now, "ent-crypto-safemoon-llc", { 'entityId': "ent-crypto-safemoon-llc", 'wellBecomingScore': 10.0, 'penaltyScore': 49.0, 'yabaiRiskScore': 97.2, 'infoRisk': 8.6, 'scoredAt': now }),
    row(now, "ent-crypto-safemoon-token", { 'entityId': "ent-crypto-safemoon-token", 'wellBecomingScore': 13.0, 'penaltyScore': 47.0, 'yabaiRiskScore': 94.6, 'infoRisk': 8.1, 'scoredAt': now }),
    row(now, "ent-crypto-do-kwon", { 'entityId': "ent-crypto-do-kwon", 'wellBecomingScore': 7.0, 'penaltyScore': 50.0, 'yabaiRiskScore': 99.0, 'infoRisk': 9.0, 'scoredAt': now }),
    row(now, "ent-crypto-terraform", { 'entityId': "ent-crypto-terraform", 'wellBecomingScore': 12.0, 'penaltyScore': 48.0, 'yabaiRiskScore': 96.4, 'infoRisk': 8.3, 'scoredAt': now }),
    row(now, "ent-crypto-ust", { 'entityId': "ent-crypto-ust", 'wellBecomingScore': 11.0, 'penaltyScore': 48.0, 'yabaiRiskScore': 97.4, 'infoRisk': 8.4, 'scoredAt': now }),
    row(now, "ent-crypto-luna", { 'entityId': "ent-crypto-luna", 'wellBecomingScore': 11.0, 'penaltyScore': 48.0, 'yabaiRiskScore': 97.4, 'infoRisk': 8.4, 'scoredAt': now }),
    row(now, "ent-crypto-karl-greenwood", { 'entityId': "ent-crypto-karl-greenwood", 'wellBecomingScore': 9.0, 'penaltyScore': 49.0, 'yabaiRiskScore': 97.8, 'infoRisk': 8.7, 'scoredAt': now }),
    row(now, "ent-crypto-ruja-ignatova", { 'entityId': "ent-crypto-ruja-ignatova", 'wellBecomingScore': 12.0, 'penaltyScore': 47.0, 'yabaiRiskScore': 95.6, 'infoRisk': 8.0, 'scoredAt': now }),
    row(now, "ent-crypto-onecoin", { 'entityId': "ent-crypto-onecoin", 'wellBecomingScore': 8.0, 'penaltyScore': 50.0, 'yabaiRiskScore': 99.0, 'infoRisk': 8.9, 'scoredAt': now }),
    row(now, "ent-crypto-bitconnect", { 'entityId': "ent-crypto-bitconnect", 'wellBecomingScore': 14.0, 'penaltyScore': 46.0, 'yabaiRiskScore': 92.8, 'infoRisk': 7.8, 'scoredAt': now }),
    row(now, "ent-crypto-satish-kumbhani", { 'entityId': "ent-crypto-satish-kumbhani", 'wellBecomingScore': 14.0, 'penaltyScore': 46.0, 'yabaiRiskScore': 92.8, 'infoRisk': 7.8, 'scoredAt': now }),
    row(now, "ent-crypto-bcc", { 'entityId': "ent-crypto-bcc", 'wellBecomingScore': 15.0, 'penaltyScore': 45.0, 'yabaiRiskScore': 91.0, 'infoRisk': 7.5, 'scoredAt': now }),
    row(now, "ent-crypto-tornado-cash", { 'entityId': "ent-crypto-tornado-cash", 'wellBecomingScore': 4.0, 'penaltyScore': 50.0, 'yabaiRiskScore': 100.0, 'infoRisk': 9.5, 'scoredAt': now }),
    row(now, "ent-crypto-roman-semenov", { 'entityId': "ent-crypto-roman-semenov", 'wellBecomingScore': 5.0, 'penaltyScore': 50.0, 'yabaiRiskScore': 99.0, 'infoRisk': 9.2, 'scoredAt': now }),
  ];

  const watchlist: Record<string, unknown>[] = [
    row(now, "wl-crypto-braden-karony", { 'signalId': "wl-crypto-braden-karony", 'entityType': "Person", value: "Braden John Karony", category: "CriminalEvidence", source: "justice/usao-edny/safemoon-2023-11-01", confidence: 0.97, severity: 5, probability: 0.01, jurisdiction: "US" }),
    row(now, "wl-crypto-safemoon-llc", { 'signalId': "wl-crypto-safemoon-llc", 'entityType': "Organization", value: "SafeMoon US LLC", category: "CriminalEvidence", source: "justice/usao-edny/safemoon-2023-11-01", confidence: 0.95, severity: 5, probability: 0.01, jurisdiction: "US" }),
    row(now, "wl-crypto-safemoon", { 'signalId': "wl-crypto-safemoon", 'entityType': "Product", value: "SafeMoon (SFM)", category: "FraudSignal", source: "justice/usao-edny/safemoon-2023-11-01", confidence: 0.93, severity: 5, probability: 0.02, jurisdiction: "US" }),
    row(now, "wl-crypto-do-kwon", { 'signalId': "wl-crypto-do-kwon", 'entityType': "Person", value: "Do Hyeong Kwon", category: "CriminalEvidence", source: "justice/criminal-vns/do-kwon-2024-12-31", confidence: 0.97, severity: 5, probability: 0.01, jurisdiction: "US" }),
    row(now, "wl-crypto-terraform", { 'signalId': "wl-crypto-terraform", 'entityType': "Organization", value: "Terraform Labs PTE. Ltd.", category: "FraudSignal", source: "sec/terraform-2024-06-13", confidence: 0.95, severity: 5, probability: 0.02, jurisdiction: "US" }),
    row(now, "wl-crypto-ust", { 'signalId': "wl-crypto-ust", 'entityType': "Product", value: "TerraUSD (UST)", category: "FraudSignal", source: "sec/terraform-2024-06-13", confidence: 0.94, severity: 5, probability: 0.02, jurisdiction: "US" }),
    row(now, "wl-crypto-luna", { 'signalId': "wl-crypto-luna", 'entityType': "Product", value: "LUNA", category: "FraudSignal", source: "sec/terraform-2024-06-13", confidence: 0.94, severity: 5, probability: 0.02, jurisdiction: "US" }),
    row(now, "wl-crypto-karl-greenwood", { 'signalId': "wl-crypto-karl-greenwood", 'entityType': "Person", value: "Karl Sebastian Greenwood", category: "CriminalEvidence", source: "justice/usao-sdny/onecoin-2023-09-12", confidence: 0.96, severity: 5, probability: 0.01, jurisdiction: "US" }),
    row(now, "wl-crypto-ruja-ignatova", { 'signalId': "wl-crypto-ruja-ignatova", 'entityType': "Person", value: "Ruja Ignatova", category: "CriminalEvidence", source: "justice/usao-sdny/onecoin-2023-09-12", confidence: 0.92, severity: 5, probability: 0.02, jurisdiction: "US" }),
    row(now, "wl-crypto-onecoin", { 'signalId': "wl-crypto-onecoin", 'entityType': "Product", value: "OneCoin", category: "CriminalEvidence", source: "justice/usao-sdny/onecoin-2023-09-12", confidence: 0.95, severity: 5, probability: 0.01, jurisdiction: "US" }),
    row(now, "wl-crypto-bitconnect", { 'signalId': "wl-crypto-bitconnect", 'entityType': "Organization", value: "BitConnect", category: "FraudSignal", source: "sec/bitconnect-2021-09-01", confidence: 0.94, severity: 5, probability: 0.02, jurisdiction: "US" }),
    row(now, "wl-crypto-satish-kumbhani", { 'signalId': "wl-crypto-satish-kumbhani", 'entityType': "Person", value: "Satish Kumbhani", category: "FraudSignal", source: "sec/bitconnect-2021-09-01", confidence: 0.94, severity: 5, probability: 0.02, jurisdiction: "US" }),
    row(now, "wl-crypto-bcc", { 'signalId': "wl-crypto-bcc", 'entityType': "Product", value: "BitConnect Coin (BCC)", category: "FraudSignal", source: "sec/bitconnect-2021-09-01", confidence: 0.93, severity: 5, probability: 0.02, jurisdiction: "US" }),
    row(now, "wl-crypto-tornado", { 'signalId': "wl-crypto-tornado", 'entityType': "Organization", value: "Tornado Cash", category: "SanctionHit", source: "ofac/tornado-cash-2022-08-08", confidence: 0.98, severity: 5, probability: 0.005, jurisdiction: "US" }),
    row(now, "wl-crypto-roman-semenov", { 'signalId': "wl-crypto-roman-semenov", 'entityType': "Person", value: "Roman Semenov", category: "SanctionHit", source: "ofac/roman-semenov-2025-03-21", confidence: 0.98, severity: 5, probability: 0.005, jurisdiction: "US" }),
    row(now, "wl-crypto-tornado-aml", { 'signalId': "wl-crypto-tornado-aml", 'entityType': "Organization", value: "Tornado Cash", category: "AMLPattern", source: "ofac/roman-semenov-2025-03-21", confidence: 0.97, severity: 5, probability: 0.01, jurisdiction: "US" }),
  ];

  const sources: Record<string, unknown>[] = [
    row(now, "doj-safemoon", { 'sourceId': "doj-safemoon", 'sourceType': "CreativeWork", name: "U.S. DOJ: SafeMoon founder charged", url: "https://www.justice.gov/usao-edny/pr/founder-and-key-employees-safemoon-charged-multi-million-dollar-international-fraud", note: "EDNY release dated 2023-11-01 on SafeMoon fraud charges." }),
    row(now, "sec-terraform", { 'sourceId': "sec-terraform", 'sourceType': "CreativeWork", name: "U.S. SEC: Terraform and Do Kwon settlement", url: "https://www.sec.gov/newsroom/press-releases/2024-73", note: "SEC release dated 2024-06-13 after Terraform fraud verdict." }),
    row(now, "doj-do-kwon", { 'sourceId': "doj-do-kwon", 'sourceType': "CreativeWork", name: "U.S. DOJ: Do Kwon extradition", url: "https://www.justice.gov/opa/pr/do-hyeong-kwon-extradited-united-states-face-fraud-charges-related-collapse-terraform", note: "DOJ release dated 2024-12-31 on Do Kwon extradition." }),
    row(now, "doj-onecoin", { 'sourceId': "doj-onecoin", 'sourceType': "CreativeWork", name: "U.S. DOJ: OneCoin sentencing", url: "https://www.justice.gov/usao-sdny/pr/co-founder-onecoin-sentenced-20-years-prison-fraud-and-money-laundering-schemes", note: "SDNY release dated 2023-09-12 on Karl Greenwood and OneCoin." }),
    row(now, "sec-bitconnect", { 'sourceId': "sec-bitconnect", 'sourceType': "CreativeWork", name: "U.S. SEC: BitConnect action", url: "https://www.sec.gov/newsroom/press-releases/2021-172", note: "SEC release dated 2021-09-01 on BitConnect." }),
    row(now, "ofac-tornado", { 'sourceId': "ofac-tornado", 'sourceType': "CreativeWork", name: "U.S. Treasury OFAC: Tornado Cash sanctions", url: "https://ofac.treasury.gov/recent-actions/20220808", note: "OFAC action dated 2022-08-08 designating Tornado Cash." }),
    row(now, "ofac-semenov", { 'sourceId': "ofac-semenov", 'sourceType': "CreativeWork", name: "U.S. Treasury OFAC: Roman Semenov update", url: "https://ofac.treasury.gov/recent-actions/20250321", note: "OFAC action dated 2025-03-21 tied to Roman Semenov and Tornado Cash." }),
  ];

  return [
    { name: "yabaiEntities", fields: entitiesFields, rows: entities, deleteIDs: deleteEntityIDs },
    { name: "yabaiEvidences", fields: evidencesFields, rows: evidences, deleteIDs: deleteEvidenceIDs },
    { name: "yabaiRisks", fields: risksFields, rows: risks, deleteIDs: [...deleteEntityIDs] },
    { name: "yabaiWatchlistSignals", fields: watchlistFields, rows: watchlist, deleteIDs: deleteWatchlistIDs },
    { name: "yabaiSources", fields: sourcesFields, rows: sources, deleteIDs: deleteSourceIDs },
  ];
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
