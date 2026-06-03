#!/usr/bin/env node
/**
 * ╔══════════════════════════════════════════════════════════════════════╗
 * ║  SUPERSEDED — DO NOT RUN ON THE RELIGIOUS-CORP SUBSTRATE              ║
 * ║                                                                       ║
 * ║  Status: pre-religious-corp commercial-fund era artifact (writes to   ║
 * ║          AT Protocol PDS but uses etzhayyim-side legacy NSID + pre-Charter ║
 * ║          Rider provenance fields).                                    ║
 * ║                                                                       ║
 * ║  Superseded by: ADR-2605263800 (Global corporate-disclosure ingestion ║
 * ║                 via IPFS-pinned DataLad subdatasets) — W1 fetcher:    ║
 * ║                 70-tools/e7m-dataset/src/e7m_dataset/fetchers/        ║
 * ║                 gleif_lei.py                                          ║
 * ║                                                                       ║
 * ║  Why superseded (religious-corp substrate-fit):                       ║
 * ║    - DataLad subdataset + IPFS-pin storage of full GLEIF L1+L2+RepEx  ║
 * ║      concatenated files (NOT per-row PDS createRecord)                ║
 * ║    - com.etzhayyim.corp.leiReference Lexicon record canonical         ║
 * ║      (NOT legacy etzhayyim-side NSID; CC0 1.0 attribution preserved)       ║
 * ║    - LeiSensor Protocol (pymagatama.organism.sensors.corp.lei_sensor) ║
 * ║      acts as the canonical cross-jurisdiction key resolver — other    ║
 * ║      corp sensors look up local registry ID against this pin          ║
 * ║    - Passive-only invariant per ADR-2605262400 §7 (no per-LEI live    ║
 * ║      API lookups; only published concatenated bulk files)             ║
 * ║                                                                       ║
 * ║  Operator action:                                                     ║
 * ║    - For new ingestion: use `e7m-dataset pull gleif-lei` (W1)         ║
 * ║    - Existing PDS records: read ADR-2605263800 §7 W4 migration plan   ║
 * ║                                                                       ║
 * ║  Removal scheduled: ADR-2605263800 W4 deliverable (after sensor       ║
 * ║                     parity is verified at W3).                        ║
 * ╚══════════════════════════════════════════════════════════════════════╝
 *
 * GLEIF Golden Copy CSV → PDS bulk ingest (AT Protocol compliant).
 *
 * Reads the GLEIF LEI-CDF Level 1 Golden Copy CSV (streaming) and writes
 * records to PDS via com.atproto.repo.applyWrites in batches.
 *
 * Download the Golden Copy CSV first:
 *   curl -L -o /tmp/gleif-golden-copy.csv.zip \
 *     "https://goldencopy.gleif.org/storage/golden-copy-files/2026/04/13/1213852/20260413-0800-gleif-goldencopy-lei2-golden-copy.csv.zip"
 *   cd /tmp && unzip gleif-golden-copy.csv.zip
 *
 * Usage:
 *   node 70-tools/scripts/gleif-bulk-ingest.mjs [options]
 *
 * Options:
 *   --csv PATH         Path to unzipped CSV (default: auto-detect in /tmp)
 *   --batch-size N     Records per applyWrites call (default: 100)
 *   --start N          Start at line N (0-based, skip header) for resume (default: 0)
 *   --limit N          Max records to process (default: unlimited)
 *   --delay MS         Delay between batches in ms (default: 5000)
 *   --dry-run          Parse only, no writes
 *   --mode pds|sql     Write mode: pds (XRPC) or sql (RisingWave direct) (default: pds)
 *   --active-only      Only ingest ACTIVE entities (default: true)
 *
 * Auth (PDS mode):
 *   export BEARER_TOKEN=$(etzhayyim auth token)
 *   Or set PDS_HANDLE + PDS_PASSWORD for createSession.
 *
 * Resume:
 *   The script writes progress to /tmp/gleif-ingest-progress.json every batch.
 *   Pass --resume to continue from the last saved position.
 */

import { createReadStream } from "node:fs";
import { stat, writeFile, readFile } from "node:fs/promises";
import { createInterface } from "node:readline";
import { createUnzip } from "node:zlib";
import { basename } from "node:path";
import { execSync } from "node:child_process";

// ── Config ──────────────────────────────────────────────────────────────────

const PDS_URL = "https://atproto.etzhayyim.com";
const COLLECTOR_DID = "did:web:legal-entity.etzhayyim.com";
const COLLECTION = "com.etzhayyim.apps.legalEntity.legalEntity";
const PROGRESS_FILE = "/tmp/gleif-ingest-progress.json";
const RW_CONN = "REDACTED_USE_DATABASE_URL_ENV?sslmode=disable";

// ── CLI args ────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
function getArg(name, fallback) {
  const idx = args.indexOf(`--${name}`);
  if (idx === -1) return fallback;
  return args[idx + 1] ?? fallback;
}
function hasFlag(name) {
  return args.includes(`--${name}`);
}

const CSV_PATH = getArg("csv", "");
const BATCH_SIZE = Number(getArg("batch-size", "100"));
const START_LINE = Number(getArg("start", "0"));
const LIMIT = Number(getArg("limit", "0")) || Infinity;
const DELAY_MS = Number(getArg("delay", "5000"));
const DRY_RUN = hasFlag("dry-run");
const RESUME = hasFlag("resume");
const ACTIVE_ONLY = !hasFlag("all-statuses"); // default: active only
const MODE = getArg("mode", "pds"); // pds | sql

// ── CSV discovery ───────────────────────────────────────────────────────────

async function findCsvPath() {
  if (CSV_PATH) return CSV_PATH;
  // Auto-detect in /tmp
  const candidates = [
    "/tmp/20260413-0800-gleif-goldencopy-lei2-golden-copy.csv",
  ];
  // Also try glob
  try {
    const found = execSync("ls /tmp/*gleif*golden*copy*.csv 2>/dev/null", { encoding: "utf8" }).trim().split("\n");
    candidates.push(...found.filter(Boolean));
  } catch { /* ignore */ }
  for (const p of candidates) {
    try {
      await stat(p);
      return p;
    } catch { /* skip */ }
  }
  throw new Error(
    "CSV not found. Download with:\n" +
    '  curl -L -o /tmp/gleif-golden-copy.csv.zip "https://goldencopy.gleif.org/storage/golden-copy-files/2026/04/13/1213852/20260413-0800-gleif-goldencopy-lei2-golden-copy.csv.zip"\n' +
    "  cd /tmp && unzip gleif-golden-copy.csv.zip"
  );
}

// ── CSV parsing (RFC 4180 aware — handles quoted fields with commas) ───────

function parseCSVLine(line) {
  const fields = [];
  let i = 0;
  while (i < line.length) {
    if (line[i] === '"') {
      // Quoted field
      let j = i + 1;
      let val = "";
      while (j < line.length) {
        if (line[j] === '"') {
          if (j + 1 < line.length && line[j + 1] === '"') {
            val += '"';
            j += 2;
          } else {
            j++; // closing quote
            break;
          }
        } else {
          val += line[j];
          j++;
        }
      }
      fields.push(val);
      i = j + 1; // skip comma
    } else {
      // Unquoted field
      const comma = line.indexOf(",", i);
      if (comma === -1) {
        fields.push(line.slice(i));
        break;
      }
      fields.push(line.slice(i, comma));
      i = comma + 1;
    }
  }
  return fields;
}

// ── Column index map ────────────────────────────────────────────────────────

// Key columns from GLEIF LEI-CDF Level 1 CSV (0-indexed after header parse)
const COL = {
  LEI: 0,
  LegalName: 1,
  LegalAddressCountry: 43, // Entity.LegalAddress.Country
  LegalAddressRegion: 42,  // Entity.LegalAddress.Region
  LegalAddressCity: 41,    // Entity.LegalAddress.City
  RegistrationAuthorityEntityID: 189, // Entity.RegistrationAuthority.RegistrationAuthorityEntityID
  LegalJurisdiction: 190,  // Entity.LegalJurisdiction
  EntityCategory: 191,     // Entity.EntityCategory
  LegalFormCode: 193,      // Entity.LegalForm.EntityLegalFormCode
  EntityStatus: 199,       // Entity.EntityStatus
  EntityCreationDate: 200,  // Entity.EntityCreationDate
  InitialRegistrationDate: 313, // Registration.InitialRegistrationDate
  RegistrationStatus: 315,      // Registration.RegistrationStatus
};

// ── Build column index dynamically from header row ──────────────────────────

function buildColumnIndex(headerFields) {
  const idx = {};
  const wanted = {
    '"LEI"': "LEI",
    "LEI": "LEI",
    '"Entity.LegalName"': "LegalName",
    "Entity.LegalName": "LegalName",
    '"Entity.LegalAddress.Country"': "LegalAddressCountry",
    "Entity.LegalAddress.Country": "LegalAddressCountry",
    '"Entity.LegalAddress.Region"': "LegalAddressRegion",
    "Entity.LegalAddress.Region": "LegalAddressRegion",
    '"Entity.LegalAddress.City"': "LegalAddressCity",
    "Entity.LegalAddress.City": "LegalAddressCity",
    '"Entity.RegistrationAuthority.RegistrationAuthorityEntityID"': "RegistrationAuthorityEntityID",
    "Entity.RegistrationAuthority.RegistrationAuthorityEntityID": "RegistrationAuthorityEntityID",
    '"Entity.LegalJurisdiction"': "LegalJurisdiction",
    "Entity.LegalJurisdiction": "LegalJurisdiction",
    '"Entity.EntityCategory"': "EntityCategory",
    "Entity.EntityCategory": "EntityCategory",
    '"Entity.LegalForm.EntityLegalFormCode"': "LegalFormCode",
    "Entity.LegalForm.EntityLegalFormCode": "LegalFormCode",
    '"Entity.EntityStatus"': "EntityStatus",
    "Entity.EntityStatus": "EntityStatus",
    '"Entity.EntityCreationDate"': "EntityCreationDate",
    "Entity.EntityCreationDate": "EntityCreationDate",
    '"Registration.InitialRegistrationDate"': "InitialRegistrationDate",
    "Registration.InitialRegistrationDate": "InitialRegistrationDate",
    '"Registration.RegistrationStatus"': "RegistrationStatus",
    "Registration.RegistrationStatus": "RegistrationStatus",
  };
  for (let i = 0; i < headerFields.length; i++) {
    const raw = headerFields[i].trim();
    const key = wanted[raw];
    if (key) idx[key] = i;
  }
  return idx;
}

// ── CSV row → AT Protocol record ───────────────────────────────────────────

function csvRowToRecord(fields, colIdx) {
  const get = (key) => (fields[colIdx[key]] ?? "").trim();
  const lei = get("LEI");
  if (!lei || lei.length !== 20) return null;

  const status = get("EntityStatus");
  if (ACTIVE_ONLY && status && status !== "ACTIVE") return null;

  const name = get("LegalName");
  if (!name) return null;

  const jurisdiction = get("LegalJurisdiction");
  const country = get("LegalAddressCountry");

  return {
    $type: COLLECTION,
    name,
    displayName: name,
    description: `LEI ${lei} — ${jurisdiction}`,
    entityType: get("EntityCategory"),
    registrationNumber: get("RegistrationAuthorityEntityID"),
    jurisdiction,
    country,
    entityStatus: status || "ACTIVE",
    lei,
    industryCode: get("LegalFormCode"),
    incorporationDate: get("EntityCreationDate"),
    sourceDid: COLLECTOR_DID,
    createdAt: new Date().toISOString(),
  };
}

// ── Auth ────────────────────────────────────────────────────────────────────

async function getAuthToken() {
  // 1. Env var
  if (process.env.BEARER_TOKEN) return process.env.BEARER_TOKEN;

  // 2. createSession
  if (process.env.PDS_HANDLE && process.env.PDS_PASSWORD) {
    const resp = await fetch(`${PDS_URL}/xrpc/com.atproto.server.createSession`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier: process.env.PDS_HANDLE,
        password: process.env.PDS_PASSWORD,
      }),
    });
    if (resp.ok) {
      const data = await resp.json();
      return data.accessJwt;
    }
    throw new Error(`createSession failed: ${resp.status} ${await resp.text()}`);
  }

  return null; // PDS may accept unauthenticated writes for known repos
}

// ── PDS batch write ─────────────────────────────────────────────────────────

async function writeBatchPDS(records, token) {
  const writes = records.map((rec) => ({
    $type: "com.atproto.repo.applyWrites#create",
    action: "create",
    collection: COLLECTION,
    value: rec,
  }));

  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const body = JSON.stringify({
    repo: COLLECTOR_DID,
    writes,
  });

  const resp = await fetch(`${PDS_URL}/xrpc/com.atproto.repo.applyWrites`, {
    method: "POST",
    headers,
    body,
    signal: AbortSignal.timeout(60_000),
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    // Retry-able errors
    if (resp.status === 429 || resp.status >= 500) {
      throw new RetryableError(`PDS ${resp.status}: ${text.slice(0, 200)}`);
    }
    throw new Error(`PDS ${resp.status}: ${text.slice(0, 200)}`);
  }

  return resp.json();
}

class RetryableError extends Error {
  constructor(msg) { super(msg); this.name = "RetryableError"; }
}

// ── RisingWave SQL batch write (direct) ─────────────────────────────────────

let _pgPool = null;

async function getRwPool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");
  _pgPool = new pg.Pool({ connectionString: RW_CONN, max: 2 });
  return _pgPool;
}

async function writeBatchSQL(records) {
  const pool = await getRwPool();
  const now = new Date().toISOString();

  // Build bulk INSERT
  const cols = [
    "vertex_id", "rkey", "repo", "collection", "name", "display_name",
    "description", "entity_type", "registration_number", "jurisdiction",
    "country", "status", "lei", "industry_code", "incorporation_date",
    "source_did", "owner_did", "source", "label", "sensitivity_ord",
  ];
  const placeholders = [];
  const values = [];
  let paramIdx = 1;

  for (const rec of records) {
    // AT-native vertex_id matches the existing 190M-row convention
    // (`at://${repo}/${collection}/${rkey}`). Rkey = LEI for deterministic
    // upsert keying — the LEI is globally unique by design.
    const vertexId = `at://${COLLECTOR_DID}/${COLLECTION}/${rec.lei}`;
    const row = [
      vertexId, rec.lei, COLLECTOR_DID, COLLECTION,
      rec.name, rec.displayName, rec.description, rec.entityType,
      rec.registrationNumber, rec.jurisdiction, rec.country,
      rec.entityStatus, rec.lei, rec.industryCode, rec.incorporationDate,
      COLLECTOR_DID, COLLECTOR_DID,
      "gleif", "LegalEntity", 300,
    ];
    const ph = row.map(() => `$${paramIdx++}`);
    placeholders.push(`(${ph.join(",")})`);
    values.push(...row);
  }

  const sql = `INSERT INTO vertex_legal_entity (${cols.join(",")})
VALUES ${placeholders.join(",\n")}`;

  // RW on B2 has transient write windows: a B2 connection hiccup puts the
  // streaming graph into 5-15s recovery and DML rejects with "table reader
  // closed" / "DML during cluster recovery". Retry these with backoff so a
  // long-running ingest doesn't lose batches over single-flap blips.
  const isTransient = (msg) =>
    /table reader closed|cluster recovery|connection closed before message|connection terminated|gRPC.*Internal error|Scheduler error/i.test(msg);
  let attempt = 0;
  const maxAttempts = 6;
  while (true) {
    try {
      await pool.query(sql, values);
      return;
    } catch (e) {
      attempt++;
      const msg = String(e?.message || e);
      if (attempt >= maxAttempts || !isTransient(msg)) {
        throw e;
      }
      const backoffMs = Math.min(15000, 1000 * 2 ** (attempt - 1)); // 1s,2s,4s,8s,15s,15s
      console.warn(`[gleif-ingest] transient SQL write fail (attempt ${attempt}/${maxAttempts}, retrying in ${backoffMs}ms): ${msg.slice(0, 200)}`);
      await new Promise((r) => setTimeout(r, backoffMs));
    }
  }
}

// ── Progress tracking ───────────────────────────────────────────────────────

async function loadProgress() {
  try {
    const data = JSON.parse(await readFile(PROGRESS_FILE, "utf8"));
    return data;
  } catch {
    return { lastLine: 0, totalWritten: 0, totalSkipped: 0, totalErrors: 0 };
  }
}

async function saveProgress(state) {
  await writeFile(PROGRESS_FILE, JSON.stringify(state, null, 2));
}

// ── Stats display ───────────────────────────────────────────────────────────

function formatRate(count, elapsedMs) {
  const rps = (count / (elapsedMs / 1000)).toFixed(1);
  return `${rps} rec/s`;
}

function formatETA(remaining, ratePerSec) {
  if (ratePerSec <= 0) return "unknown";
  const secs = remaining / ratePerSec;
  if (secs < 60) return `${Math.ceil(secs)}s`;
  if (secs < 3600) return `${Math.ceil(secs / 60)}m`;
  return `${(secs / 3600).toFixed(1)}h`;
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const csvPath = await findCsvPath();
  const csvStat = await stat(csvPath);
  console.log(`[gleif-ingest] CSV: ${basename(csvPath)} (${(csvStat.size / 1e9).toFixed(2)} GB)`);
  console.log(`[gleif-ingest] Mode: ${MODE} | Batch: ${BATCH_SIZE} | Delay: ${DELAY_MS}ms | Active-only: ${ACTIVE_ONLY}`);

  // Determine start line
  let startLine = START_LINE;
  let progress = { lastLine: 0, totalWritten: 0, totalSkipped: 0, totalErrors: 0 };
  if (RESUME) {
    progress = await loadProgress();
    startLine = progress.lastLine;
    console.log(`[gleif-ingest] Resuming from line ${startLine} (${progress.totalWritten} written, ${progress.totalSkipped} skipped)`);
  }

  // Auth (PDS mode)
  let token = null;
  if (MODE === "pds" && !DRY_RUN) {
    token = await getAuthToken();
    if (token) {
      console.log(`[gleif-ingest] Auth: Bearer token (${token.length} chars)`);
    } else {
      console.log(`[gleif-ingest] Auth: none (unauthenticated — may fail for writes)`);
    }
  }

  // Open CSV stream
  const stream = createReadStream(csvPath, { encoding: "utf8" });
  const rl = createInterface({ input: stream, crlfDelay: Infinity });

  let lineNum = 0;
  let colIdx = null;
  let batch = [];
  let totalWritten = progress.totalWritten;
  let totalSkipped = progress.totalSkipped;
  let totalErrors = progress.totalErrors;
  let totalParsed = 0;
  let processedInSession = 0;
  const startTime = Date.now();

  for await (const line of rl) {
    if (lineNum === 0) {
      // Parse header
      const headerFields = parseCSVLine(line);
      colIdx = buildColumnIndex(headerFields);
      const found = Object.keys(colIdx).length;
      console.log(`[gleif-ingest] Header parsed: ${headerFields.length} columns, ${found} mapped`);
      if (found < 8) {
        console.error(`[gleif-ingest] ERROR: Only ${found} columns mapped. Check CSV format.`);
        console.error("[gleif-ingest] Mapped:", colIdx);
        process.exit(1);
      }
      lineNum++;
      continue;
    }

    // Skip to start position
    if (lineNum < startLine + 1) { // +1 for header
      lineNum++;
      continue;
    }

    // Limit check
    if (processedInSession >= LIMIT) break;

    // Parse row
    const fields = parseCSVLine(line);
    const record = csvRowToRecord(fields, colIdx);
    if (record) {
      batch.push(record);
      totalParsed++;
    } else {
      totalSkipped++;
    }

    // Flush batch
    if (batch.length >= BATCH_SIZE) {
      if (!DRY_RUN) {
        let retries = 0;
        const maxRetries = 3;
        while (retries < maxRetries) {
          try {
            if (MODE === "sql") {
              await writeBatchSQL(batch);
            } else {
              await writeBatchPDS(batch, token);
            }
            totalWritten += batch.length;
            break;
          } catch (e) {
            if (e instanceof RetryableError && retries < maxRetries - 1) {
              retries++;
              const backoff = DELAY_MS * Math.pow(2, retries);
              console.warn(`[gleif-ingest] Retry ${retries}/${maxRetries} after ${backoff}ms: ${e.message}`);
              await sleep(backoff);
            } else {
              console.error(`[gleif-ingest] ERROR at line ${lineNum}: ${e.message}`);
              totalErrors++;
              break;
            }
          }
        }
      } else {
        totalWritten += batch.length;
      }

      processedInSession += batch.length;
      batch = [];

      // Progress report
      const elapsed = Date.now() - startTime;
      const rps = totalParsed / (elapsed / 1000);
      const estimatedTotal = 3_032_611; // GLEIF active LEI count
      const remaining = estimatedTotal - totalWritten;
      const eta = formatETA(remaining, rps);

      // Update progress file
      const progressState = { lastLine: lineNum, totalWritten, totalSkipped, totalErrors, timestamp: new Date().toISOString() };
      await saveProgress(progressState);

      process.stdout.write(
        `\r[gleif-ingest] Line ${lineNum.toLocaleString()} | ` +
        `Written: ${totalWritten.toLocaleString()} | ` +
        `Skipped: ${totalSkipped.toLocaleString()} | ` +
        `Errors: ${totalErrors} | ` +
        `${formatRate(totalParsed, elapsed)} | ` +
        `ETA: ${eta}   `
      );

      // Rate limit
      if (!DRY_RUN && DELAY_MS > 0) {
        await sleep(DELAY_MS);
      }
    }

    lineNum++;
  }

  // Flush remaining
  if (batch.length > 0) {
    if (!DRY_RUN) {
      try {
        if (MODE === "sql") {
          await writeBatchSQL(batch);
        } else {
          await writeBatchPDS(batch, token);
        }
        totalWritten += batch.length;
      } catch (e) {
        console.error(`\n[gleif-ingest] ERROR (final batch): ${e.message}`);
        totalErrors++;
      }
    } else {
      totalWritten += batch.length;
    }
    processedInSession += batch.length;
  }

  // Final report
  const elapsed = Date.now() - startTime;
  console.log(`\n\n[gleif-ingest] === COMPLETE ===`);
  console.log(`[gleif-ingest] CSV lines scanned: ${lineNum.toLocaleString()}`);
  console.log(`[gleif-ingest] Records written:   ${totalWritten.toLocaleString()}`);
  console.log(`[gleif-ingest] Records skipped:   ${totalSkipped.toLocaleString()} (inactive/invalid)`);
  console.log(`[gleif-ingest] Errors:            ${totalErrors}`);
  console.log(`[gleif-ingest] Elapsed:           ${(elapsed / 1000).toFixed(1)}s`);
  console.log(`[gleif-ingest] Rate:              ${formatRate(processedInSession, elapsed)}`);
  console.log(`[gleif-ingest] Progress saved to: ${PROGRESS_FILE}`);

  if (MODE === "sql" && _pgPool) {
    await _pgPool.end();
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

main().catch((e) => {
  console.error(`\n[gleif-ingest] FATAL: ${e.message}`);
  process.exit(1);
});
