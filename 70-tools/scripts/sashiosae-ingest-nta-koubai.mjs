#!/usr/bin/env node
/**
 * Sashiosae — 国税庁公売公告 (NTA public auction) ingest (ADR-0032 Phase 1 MVP).
 *
 * Strategy (Follow-based input, project rule):
 *   site.etzhayyim.com crawler が既に www.koubai.nta.go.jp を ingest して
 *   vertex_page (com.etzhayyim.apps.site.page) に格納している。本 script は
 *   それら page を読み、public-auction 情報 (auctionId / scheduledAt /
 *   propertyType / estimatedValue / venueUrl) を抽出し、
 *   com.etzhayyim.apps.sashiosae.recordKankaResult XRPC を呼ぶ。
 *
 * Phase 1 scope: 国税庁 (did:web:jpn-state.etzhayyim.com:mof:nta:choushuu:kanka) のみ。
 * Phase 2 で 47 都道府県 + 指定都市の独自公売システムを追加。
 *
 * Auth: authority Service Auth JWT (lxm=com.etzhayyim.apps.sashiosae.recordKankaResult)
 *   env etzhayyim_AUTHORITY_JWT で渡す (60s TTL、etzhayyim agent-token --lxm で取得)。
 *
 * Tier rule (ADR-0032): auctionId / scheduledAt / estimatedValue / venueUrl は
 *   Tier 1 public (政府公開情報)。落札者 / 正確落札額 は取得対象外 (Tier 3)。
 *
 * Usage:
 *   export etzhayyim_AUTHORITY_JWT=$(etzhayyim agent-token --lxm com.etzhayyim.apps.sashiosae.recordKankaResult --did did:web:jpn-state.etzhayyim.com:mof:nta:choushuu:kanka)
 *   node sashiosae-ingest-nta-koubai.mjs [--dry-run] [--limit 50]
 */
import { readFile } from "node:fs/promises";

const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const JWT = process.env.etzhayyim_AUTHORITY_JWT ?? "";
const XRPC_HOST = process.env.XRPC_HOST ?? "https://atproto.etzhayyim.com";
const AUTHORITY_DID = "did:web:jpn-state.etzhayyim.com:mof:nta:choushuu:kanka";
const NTA_HOST = "www.koubai.nta.go.jp";
const UA = "etzhayyim-sashiosae-ingest/0.1 (https://jpn-state.etzhayyim.com; adr-0032)";

const args = process.argv.slice(2);
const DRY_RUN = args.includes("--dry-run");
const LIMIT = Number(args[args.indexOf("--limit") + 1]) || 50;

let _pgPool = null;
async function pool() {
  if (_pgPool) return _pgPool;
  const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");
  _pgPool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 60000 });
  return _pgPool;
}

async function fetchKoubaiPages() {
  const p = await pool();
  const res = await p.query(
    `SELECT vertex_id, url, html, fetched_at
       FROM vertex_page
      WHERE url LIKE $1
        AND (extracted_for_sashiosae IS NULL OR extracted_for_sashiosae < fetched_at)
      ORDER BY fetched_at DESC
      LIMIT $2`,
    [`%://${NTA_HOST}/%`, LIMIT]
  );
  return res.rows;
}

/**
 * Parse 公売公告 detail page.
 * NTA koubai pages are structured HTML tables with labeled fields.
 * Field extraction via regex (no LLM required for Phase 1 MVP).
 */
function parseKoubaiPage(html, url) {
  const pick = (label) => {
    const m = html.match(new RegExp(`${label}[^<]*</[^>]+>\\s*<[^>]+>([^<]+)`, "i"));
    return m ? m[1].trim() : "";
  };
  const auctionId = pick("公売番号") || pick("物件番号") || url.split("/").pop()?.replace(/\\.[a-z]+$/, "") || "";
  const propertyLabel = pick("財産の種類") || pick("物件種別") || "";
  const scheduledJp = pick("公売期日") || pick("開始日時") || "";
  const estimatedJp = pick("見積価額") || pick("最低公売価額") || "";
  const kankaMethodJp = pick("公売方法") || pick("売却方法") || "";

  const propertyType = (() => {
    if (/不動産|土地|建物|マンション/.test(propertyLabel)) return "realEstate";
    if (/自動車|動産|家財/.test(propertyLabel)) return "movable";
    if (/預金|預貯金/.test(propertyLabel)) return "deposit";
    if (/有価証券|株式/.test(propertyLabel)) return "securities";
    if (/債権|売掛/.test(propertyLabel)) return "receivable";
    return "other";
  })();

  const kankaMethod = /入札/.test(kankaMethodJp) ? "bid-auction"
    : /期間入札/.test(kankaMethodJp) ? "public-auction"
    : /随意/.test(kankaMethodJp) ? "private-contract"
    : "public-auction";

  const scheduledAt = (() => {
    const m = scheduledJp.match(/(\\d{4})[\\-/年](\\d{1,2})[\\-/月](\\d{1,2})/);
    if (!m) return "";
    return new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]), 0, 0, 0)).toISOString();
  })();

  const estimatedValue = (() => {
    const digits = estimatedJp.replace(/[^\\d]/g, "");
    return digits ? Number(digits) : 0;
  })();

  if (!auctionId || !scheduledAt) return null;

  return {
    authorityDid: AUTHORITY_DID,
    auctionId,
    kankaMethod,
    propertyType,
    estimatedValue,
    scheduledAt,
    venueUrl: url,
    status: new Date(scheduledAt) > new Date() ? "scheduled" : "closed",
    // noticeId は NTA 公開データから導出不能 (債務者情報が紐付かない)。
    // Phase 1 MVP では auctionId を placeholder として空文字列で格納。
    noticeId: "",
  };
}

async function postKankaResult(payload) {
  if (DRY_RUN) {
    console.log("[dry-run] would POST", JSON.stringify(payload));
    return { kankaId: "dry-run", uri: "" };
  }
  if (!JWT) throw new Error("etzhayyim_AUTHORITY_JWT env required (etzhayyim agent-token --lxm com.etzhayyim.apps.sashiosae.recordKankaResult)");
  const res = await fetch(`${XRPC_HOST}/xrpc/com.etzhayyim.apps.sashiosae.recordKankaResult`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${JWT}`,
      "User-Agent": UA,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`XRPC HTTP ${res.status}: ${(await res.text()).slice(0, 400)}`);
  return res.json();
}

async function markExtracted(vertexIds) {
  if (DRY_RUN || vertexIds.length === 0) return;
  const p = await pool();
  await p.query(
    `UPDATE vertex_page SET extracted_for_sashiosae = NOW() WHERE vertex_id = ANY($1::varchar[])`,
    [vertexIds]
  );
}

async function main() {
  console.log(`[nta-koubai] fetching vertex_page WHERE host=${NTA_HOST} limit=${LIMIT} dry-run=${DRY_RUN}`);
  const pages = await fetchKoubaiPages();
  console.log(`[nta-koubai] candidate pages: ${pages.length}`);

  let ok = 0, skip = 0, fail = 0;
  const processed = [];
  for (const row of pages) {
    try {
      const payload = parseKoubaiPage(String(row.html ?? ""), String(row.url ?? ""));
      if (!payload) { skip++; continue; }
      await postKankaResult(payload);
      ok++;
      processed.push(row.vertex_id);
    } catch (err) {
      fail++;
      console.error(`[nta-koubai] fail ${row.url}: ${err.message}`);
    }
  }
  await markExtracted(processed);
  console.log(`[nta-koubai] done: ok=${ok} skip=${skip} fail=${fail}`);
  await (await pool()).end();
}

main().catch((err) => { console.error(err); process.exit(1); });
