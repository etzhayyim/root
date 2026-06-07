#!/usr/bin/env npx tsx
/**
 * Register path-based DIDs from ingested domain records.
 *
 * For each domain, creates path-based DIDs via PDS batch-flush
 * (com.atproto.identity.create) so that `etzhayyim coverage` can count them.
 *
 * Usage:
 *   npx tsx scripts/register-dids-from-records.ts [--domain hanrei] [--dry-run]
 */

const PDS_URL = "https://atproto.etzhayyim.com";

// ADR-0023 P4: etzhayyim_TOKEN Bearer replaces spoofable x-kotodama-verified.
const etzhayyim_TOKEN = process.env.etzhayyim_TOKEN;
if (!etzhayyim_TOKEN) {
  throw new Error("etzhayyim_TOKEN env var required — run `export etzhayyim_TOKEN=$(etzhayyim auth token)` first");
}
const AUTH_HEADERS: Record<string, string> = {
  "Content-Type": "application/json",
  "Authorization": `Bearer ${etzhayyim_TOKEN}`,
  "x-etzhayyim-org-id": "anon",
};
const DATA_BASE = "/Volumes/251220/domain-data";
const BATCH_SIZE = 5;
const THROTTLE_MS = 500;

// ── Domain DID definitions ──

interface DIDEntry {
  path: string;
  displayName: string;
  description: string;
}

interface DomainDIDConfig {
  nanoid: string;
  appDid: string;
  /** Static DIDs (from app definition) */
  staticDIDs: DIDEntry[];
  /** Dynamic DID generator from seed/raw data */
  dynamicDIDs?: (limit: number) => DIDEntry[];
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ── Load seed data ──

function loadSeed(path: string): any[] {
  const fs = require("fs");
  const p = require("path");
  const filePath = p.join(DATA_BASE, path);
  if (!fs.existsSync(filePath)) return [];
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

function loadCsv(path: string, limit: number): string[][] {
  const fs = require("fs");
  const p = require("path");
  const filePath = p.join(DATA_BASE, path);
  if (!fs.existsSync(filePath)) return [];
  return fs.readFileSync(filePath, "utf-8").trim().split("\n").slice(0, limit).map((l: string) => l.split(","));
}

// ── Domain configs ──

const DOMAINS: Record<string, DomainDIDConfig> = {
  hanrei: {
    nanoid: "h4nr31jp",
    appDid: "did:web:h4nr31jp.etzhayyim.com",
    staticDIDs: [
      { path: "court:supreme", displayName: "最高裁判所", description: "Supreme Court of Japan" },
      { path: "court:ipHigh", displayName: "知的財産高等裁判所", description: "IP High Court" },
      { path: "court:high", displayName: "高等裁判所", description: "High Courts" },
      { path: "court:district", displayName: "地方裁判所", description: "District Courts" },
      { path: "court:family", displayName: "家庭裁判所", description: "Family Courts" },
      { path: "court:summaryCourt", displayName: "簡易裁判所", description: "Summary Courts" },
      { path: "source:kanpo", displayName: "官報", description: "Official Gazette" },
      { path: "source:egov", displayName: "e-Gov法令検索", description: "e-Gov legislation database (CC BY 4.0)" },
      { path: "source:wikidata", displayName: "Wikidata", description: "Wikidata SPARQL (CC0)" },
    ],
    dynamicDIDs: (limit) => {
      // Jurisdictions from hanrei app (75 national + 8 international)
      const jurisdictions = [
        { iso3: "jpn", name: "Japan", localName: "日本" },
        { iso3: "kor", name: "South Korea", localName: "대한민국" },
        { iso3: "chn", name: "China", localName: "中华人民共和国" },
        { iso3: "twn", name: "Taiwan", localName: "中華民國" },
        { iso3: "hkg", name: "Hong Kong", localName: "香港" },
        { iso3: "sgp", name: "Singapore", localName: "Singapore" },
        { iso3: "tha", name: "Thailand", localName: "ไทย" },
        { iso3: "mys", name: "Malaysia", localName: "Malaysia" },
        { iso3: "idn", name: "Indonesia", localName: "Indonesia" },
        { iso3: "phl", name: "Philippines", localName: "Pilipinas" },
        { iso3: "vnm", name: "Vietnam", localName: "Việt Nam" },
        { iso3: "ind", name: "India", localName: "भारत" },
        { iso3: "pak", name: "Pakistan", localName: "پاکستان" },
        { iso3: "aus", name: "Australia", localName: "Australia" },
        { iso3: "nzl", name: "New Zealand", localName: "New Zealand" },
        { iso3: "usa", name: "United States", localName: "United States" },
        { iso3: "can", name: "Canada", localName: "Canada" },
        { iso3: "mex", name: "Mexico", localName: "México" },
        { iso3: "bra", name: "Brazil", localName: "Brasil" },
        { iso3: "arg", name: "Argentina", localName: "Argentina" },
        { iso3: "col", name: "Colombia", localName: "Colombia" },
        { iso3: "chl", name: "Chile", localName: "Chile" },
        { iso3: "per", name: "Peru", localName: "Perú" },
        { iso3: "gbr", name: "United Kingdom", localName: "United Kingdom" },
        { iso3: "fra", name: "France", localName: "France" },
        { iso3: "deu", name: "Germany", localName: "Deutschland" },
        { iso3: "ita", name: "Italy", localName: "Italia" },
        { iso3: "esp", name: "Spain", localName: "España" },
        { iso3: "nld", name: "Netherlands", localName: "Nederland" },
        { iso3: "bel", name: "Belgium", localName: "België" },
        { iso3: "che", name: "Switzerland", localName: "Schweiz" },
        { iso3: "aut", name: "Austria", localName: "Österreich" },
        { iso3: "prt", name: "Portugal", localName: "Portugal" },
        { iso3: "irl", name: "Ireland", localName: "Ireland" },
        { iso3: "swe", name: "Sweden", localName: "Sverige" },
        { iso3: "nor", name: "Norway", localName: "Norge" },
        { iso3: "dnk", name: "Denmark", localName: "Danmark" },
        { iso3: "fin", name: "Finland", localName: "Suomi" },
        { iso3: "isl", name: "Iceland", localName: "Ísland" },
        { iso3: "pol", name: "Poland", localName: "Polska" },
        { iso3: "cze", name: "Czech Republic", localName: "Česko" },
        { iso3: "svk", name: "Slovakia", localName: "Slovensko" },
        { iso3: "hun", name: "Hungary", localName: "Magyarország" },
        { iso3: "rou", name: "Romania", localName: "România" },
        { iso3: "bgr", name: "Bulgaria", localName: "България" },
        { iso3: "hrv", name: "Croatia", localName: "Hrvatska" },
        { iso3: "svn", name: "Slovenia", localName: "Slovenija" },
        { iso3: "est", name: "Estonia", localName: "Eesti" },
        { iso3: "lva", name: "Latvia", localName: "Latvija" },
        { iso3: "ltu", name: "Lithuania", localName: "Lietuva" },
        { iso3: "grc", name: "Greece", localName: "Ελλάδα" },
        { iso3: "tur", name: "Turkey", localName: "Türkiye" },
        { iso3: "rus", name: "Russia", localName: "Россия" },
        { iso3: "ukr", name: "Ukraine", localName: "Україна" },
        { iso3: "blr", name: "Belarus", localName: "Беларусь" },
        { iso3: "geo", name: "Georgia", localName: "საქართველო" },
        { iso3: "isr", name: "Israel", localName: "ישראל" },
        { iso3: "sau", name: "Saudi Arabia", localName: "السعودية" },
        { iso3: "are", name: "UAE", localName: "الإمارات" },
        { iso3: "qat", name: "Qatar", localName: "قطر" },
        { iso3: "kwt", name: "Kuwait", localName: "الكويت" },
        { iso3: "zaf", name: "South Africa", localName: "South Africa" },
        { iso3: "nga", name: "Nigeria", localName: "Nigeria" },
        { iso3: "ken", name: "Kenya", localName: "Kenya" },
        { iso3: "gha", name: "Ghana", localName: "Ghana" },
        { iso3: "egy", name: "Egypt", localName: "مصر" },
        { iso3: "mar", name: "Morocco", localName: "المغرب" },
        { iso3: "tun", name: "Tunisia", localName: "تونس" },
        // International courts
        { iso3: "icj", name: "International Court of Justice", localName: "ICJ" },
        { iso3: "icc", name: "International Criminal Court", localName: "ICC" },
        { iso3: "echr", name: "European Court of Human Rights", localName: "ECHR" },
        { iso3: "cjeu", name: "Court of Justice of the EU", localName: "CJEU" },
        { iso3: "iachr", name: "Inter-American Court of Human Rights", localName: "IACHR" },
        { iso3: "achpr", name: "African Court on Human Rights", localName: "ACHPR" },
        { iso3: "itlos", name: "International Tribunal for the Law of the Sea", localName: "ITLOS" },
        { iso3: "wtoAb", name: "WTO Appellate Body", localName: "WTO AB" },
      ];
      return jurisdictions.slice(0, limit).map(j => ({
        path: `jurisdiction:${j.iso3}`,
        displayName: `${j.localName} (${j.name})`,
        description: `Jurisdiction: ${j.name} — case law, legislation, gazette`,
      }));
    },
  },

  dns: {
    nanoid: "scndu0rf",
    appDid: "did:web:scndu0rf.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const rows = loadCsv("dns/top-1m.csv", Math.min(limit, 1000));
      return rows.map(r => ({
        path: `zone:${(r[1] || "").replace(/\./g, "_")}`,
        displayName: r[1] || "",
        description: `DNS zone: ${r[1]} (rank #${r[0]})`,
      }));
    },
  },

  legalEntity: {
    nanoid: "le01corp0",
    appDid: "did:web:le01corp0.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/legalEntity/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `registry:${(s.jurisdiction || "").toLowerCase()}`,
        displayName: s.name || "",
        description: `Legal entity registry: ${s.jurisdiction} — ${s.entityCount?.toLocaleString()} entities`,
      }));
    },
  },

  autorace: {
    nanoid: "zcv937fk",
    appDid: "did:web:zcv937fk.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/autorace/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `venue:${s.venueId || s.nameEn?.toLowerCase() || ""}`,
        displayName: s.name || s.nameEn || "",
        description: `Autorace venue: ${s.name || ""} (${s.prefecture || ""})`,
      }));
    },
  },

  keirin: {
    nanoid: "zub804qz",
    appDid: "did:web:zub804qz.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/keirin/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `velodrome:${s.venueId || ""}`,
        displayName: s.name || "",
        description: `Keirin velodrome: ${s.name || ""} (${s.prefecture || ""})`,
      }));
    },
  },

  kyotei: {
    nanoid: "qv8yed1k",
    appDid: "did:web:qv8yed1k.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/kyotei/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `venue:${s.venueId || ""}`,
        displayName: s.name || "",
        description: `Kyotei boat race venue: ${s.name || ""} (${s.prefecture || ""})`,
      }));
    },
  },

  pachinko: {
    nanoid: "k3rn5la4",
    appDid: "did:web:k3rn5la4.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/pachinko/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `prefecture:${(s.prefecture || "").toLowerCase().replace(/\s+/g, "_")}`,
        displayName: `${s.prefecture || ""} パチンコ`,
        description: `Pachinko stores: ${s.prefecture || ""} — ${s.storeCount || 0} stores`,
      }));
    },
  },

  blockchain: {
    nanoid: "blkchn01",
    appDid: "did:web:blkchn01.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/blockchain/seed.json");
      const fs = require("fs");
      const path = require("path");
      let coins: any[] = [];
      const coinPath = path.join(DATA_BASE, "blockchain/coingeckoCoinList.json");
      if (fs.existsSync(coinPath)) {
        coins = JSON.parse(fs.readFileSync(coinPath, "utf-8"));
      }
      const chainDIDs = seed.slice(0, Math.min(limit, 10)).map((s: any) => ({
        path: `chain:${s.chainId || s.name?.toLowerCase().replace(/\s+/g, "_") || ""}`,
        displayName: s.name || "",
        description: `Blockchain: ${s.name || ""} (${s.type || ""}, ${s.consensus || ""})`,
      }));
      const coinDIDs = coins.slice(0, Math.min(limit - chainDIDs.length, 500)).map((c: any) => ({
        path: `coin:${c.id || ""}`,
        displayName: `${c.name || ""} (${(c.symbol || "").toUpperCase()})`,
        description: `Cryptocurrency: ${c.name || ""} — ${c.id || ""}`,
      }));
      return [...chainDIDs, ...coinDIDs];
    },
  },

  isin: {
    nanoid: "is1n8k2x",
    appDid: "did:web:is1n8k2x.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/isin/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `nna:${(s.country || "").toLowerCase()}`,
        displayName: s.nna || "",
        description: `ISIN National Numbering Agency: ${s.country || ""} — ${s.isinCount?.toLocaleString() || 0} securities`,
      }));
    },
  },

  gtin: {
    nanoid: "gt1n4k7m",
    appDid: "did:web:gt1n4k7m.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/gtin/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `prefix:${s.prefixRange || ""}`,
        displayName: `GS1 ${s.country || ""}`,
        description: `GTIN prefix: ${s.prefixRange || ""} — ${s.country || ""} (${s.gs1_org || ""})`,
      }));
    },
  },

  isbn: {
    nanoid: "bn7k2m4x",
    appDid: "did:web:bn7k2m4x.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/isbn/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `group:${s.group || ""}`,
        displayName: `ISBN ${s.country || ""}`,
        description: `ISBN registration group: ${s.group || ""} — ${s.country || ""} (${s.agency || ""})`,
      }));
    },
  },

  ndc: {
    nanoid: "nd7c3k9m",
    appDid: "did:web:nd7c3k9m.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/ndc/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `atc:${(s.atcLevel1 || "").toLowerCase()}`,
        displayName: s.name || "",
        description: `ATC Level 1: ${s.atcLevel1 || ""} ${s.name || ""} — ${s.drugCount || 0} drugs`,
      }));
    },
  },

  cas: {
    nanoid: "cs4r7n2k",
    appDid: "did:web:cs4r7n2k.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/cas/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `substance:${(s.casNumber || s.name || "").replace(/[\s-]/g, "_").toLowerCase()}`,
        displayName: s.name || "",
        description: `CAS substance: ${s.name || ""}`,
      }));
    },
  },

  maps: {
    nanoid: "v1m9k2q8",
    appDid: "did:web:v1m9k2q8.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/maps/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `country:${(s.country || "").toLowerCase().replace(/\s+/g, "_")}`,
        displayName: s.country || "",
        description: `Map coverage: ${s.country || ""} — ${s.addressCount?.toLocaleString() || 0} addresses`,
      }));
    },
  },

  anima: {
    nanoid: "czj1f6yv",
    appDid: "did:web:czj1f6yv.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/anima/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `kingdom:${(s.kingdom || "").toLowerCase()}`,
        displayName: s.kingdom || "",
        description: `Animal kingdom: ${s.kingdom || ""} — ${s.describedSpecies?.toLocaleString() || 0} species`,
      }));
    },
  },

  treaty: {
    nanoid: "tr3aty01",
    appDid: "did:web:tr3aty01.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/treaty/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `chapter:${(s.chapter || "").replace(/\s+/g, "_").toLowerCase()}`,
        displayName: s.name || "",
        description: `Treaty chapter: ${s.chapter || ""} — ${s.treatyCount || 0} treaties`,
      }));
    },
  },

  chotatsu: {
    nanoid: "ch0t4ts1",
    appDid: "did:web:ch0t4ts1.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/chotatsu/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `source:${(s.sourceId || s.name || "").replace(/[\s/]/g, "_").toLowerCase()}`,
        displayName: s.name || "",
        description: `Procurement source: ${s.name || ""}`,
      }));
    },
  },

  isco: {
    nanoid: "wfc8k3n1",
    appDid: "did:web:wfc8k3n1.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/isco/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `major:${s.code || ""}`,
        displayName: s.name || "",
        description: `ISCO Major Group ${s.code || ""}: ${s.name || ""} — ${s.subMajorGroups || 0} sub-groups`,
      }));
    },
  },

  isic: {
    nanoid: "1s1c5c0a",
    appDid: "did:web:1s1c5c0a.etzhayyim.com",
    staticDIDs: [],
    dynamicDIDs: (limit) => {
      const seed = loadSeed("domains/isic/seed.json");
      return seed.slice(0, limit).map((s: any) => ({
        path: `section:${(s.section || "").toLowerCase()}`,
        displayName: s.name || "",
        description: `ISIC Section ${s.section || ""}: ${s.name || ""} — ${s.divisions || 0} divisions`,
      }));
    },
  },
};

// ── PDS batch-flush DID registration ──

/** Register DIDs via direct XRPC createRecord (one at a time, more reliable than batch-flush) */
async function registerDIDsBatch(
  appDid: string,
  dids: DIDEntry[],
  dryRun: boolean,
  nanoid: string,
): Promise<number> {
  let registered = 0;

  for (let i = 0; i < dids.length; i++) {
    const d = dids[i];
    const did = `did:web:${nanoid}.etzhayyim.com:${d.path}`;

    if (dryRun) {
      registered++;
      continue;
    }

    // Write DID document record
    const didRecord = {
      did,
      controller: appDid,
      status: "active",
      displayName: d.displayName,
      description: d.description,
      document: JSON.stringify({ id: did, controller: appDid }),
      orgId: "anon",
      userId: "anon",
      actorId: appDid,
      createdAt: new Date().toISOString(),
    };

    try {
      const resp = await fetch(`${PDS_URL}/xrpc/com.atproto.repo.createRecord`, {
        method: "POST",
        headers: AUTH_HEADERS,
        body: JSON.stringify({
          repo: appDid,
          collection: "com.etzhayyim.wproto.did",
          record: didRecord,
        }),
      });

      if (!resp.ok) {
        const text = await resp.text().catch((error) => {
          console.warn("    [pds] failed to read error response body:", (error as Error).message?.slice(0, 80));
          return "";
        });
        if (resp.status === 429) {
          await sleep(2000);
          i--; // retry
          continue;
        }
        if (i < 3) console.warn(`    [pds] ${resp.status}: ${text.slice(0, 80)}`);
        continue;
      }
      registered++;

      // Also write Profile record for this DID
      const handle = did.replace("did:web:", "").replace(/:/g, ".");
      await fetch(`${PDS_URL}/xrpc/com.atproto.repo.createRecord`, {
        method: "POST",
        headers: AUTH_HEADERS,
        body: JSON.stringify({
          repo: appDid,
          collection: "app.bsky.actor.profile",
          record: {
            did,
            displayName: d.displayName,
            description: d.description,
            handle,
            sensitivity: "public",
            controller: appDid,
            orgId: "anon",
            userId: "anon",
            actorId: appDid,
            createdAt: new Date().toISOString(),
          },
        }),
      }).catch((error) => {
        if (i < 3) {
          console.warn("    [profile] failed to create profile record:", (error as Error).message?.slice(0, 80));
        }
      });
    } catch (err) {
      if (i < 3) console.warn(`    [error] ${(err as Error).message?.slice(0, 80)}`);
    }

    if (THROTTLE_MS > 0 && i % BATCH_SIZE === 0) await sleep(THROTTLE_MS);
    if (i > 0 && i % 50 === 0) process.stdout.write(`  ${i}/${dids.length}...`);
  }

  return registered;
}

// ── Main ──

async function main() {
  const args = process.argv.slice(2);
  const domainFilter = args.includes("--domain") ? args[args.indexOf("--domain") + 1] : null;
  const limit = args.includes("--limit") ? parseInt(args[args.indexOf("--limit") + 1]) : 10000;
  const dryRun = args.includes("--dry-run");

  console.log("═══════════════════════════════════════════════════");
  console.log("  DID Registration from Domain Records");
  console.log("  PDS:", PDS_URL);
  console.log("  Limit:", limit);
  console.log("  Dry run:", dryRun);
  console.log("  Domain filter:", domainFilter ?? "all");
  console.log("═══════════════════════════════════════════════════\n");

  let grandTotal = 0;
  const results: { domain: string; registered: number; total: number }[] = [];

  for (const [name, config] of Object.entries(DOMAINS)) {
    if (domainFilter && domainFilter !== name) continue;

    console.log(`── ${name} (${config.appDid}) ──`);

    // Collect all DIDs
    const allDIDs: DIDEntry[] = [...config.staticDIDs];
    if (config.dynamicDIDs) {
      const dynamic = config.dynamicDIDs(limit);
      allDIDs.push(...dynamic);
    }

    if (allDIDs.length === 0) {
      console.log(`  [skip] no DIDs to register`);
      continue;
    }

    console.log(`  ${allDIDs.length} DIDs to register (${config.staticDIDs.length} static + ${allDIDs.length - config.staticDIDs.length} dynamic)`);

    if (dryRun) {
      for (const d of allDIDs.slice(0, 5)) {
        console.log(`    did:web:${config.nanoid}.etzhayyim.com:${d.path} → ${d.displayName}`);
      }
      if (allDIDs.length > 5) console.log(`    ... and ${allDIDs.length - 5} more`);
      results.push({ domain: name, registered: allDIDs.length, total: allDIDs.length });
      grandTotal += allDIDs.length;
      continue;
    }

    const registered = await registerDIDsBatch(config.appDid, allDIDs, dryRun, config.nanoid);
    console.log(`  -> registered ${registered}/${allDIDs.length} DIDs`);
    results.push({ domain: name, registered, total: allDIDs.length });
    grandTotal += registered;
  }

  console.log("\n═══════════════════════════════════════════════════");
  console.log("  DID REGISTRATION SUMMARY");
  console.log("═══════════════════════════════════════════════════");
  for (const r of results) {
    console.log(`  ${r.domain}: ${r.registered}/${r.total}`);
  }
  console.log("───────────────────────────────────────────────────");
  console.log(`  Total DIDs registered: ${grandTotal}`);
  console.log("═══════════════════════════════════════════════════");
}

main().catch(err => {
  console.error("Fatal:", err);
  process.exit(1);
});
