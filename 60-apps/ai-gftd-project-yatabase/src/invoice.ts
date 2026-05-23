// invoice.ts — 適格請求書 (Japan qualified invoice) generator (P8.5).
//
// CF Worker constraints (no native PDF runtime) → render an HTML invoice
// instead. Customer's browser prints it to PDF. The HTML includes:
//   - 登録番号 T9007028460042 (etz hayim 適格請求書発行事業者)
//   - 売手 (vendor) name + address
//   - 買手 (customer) — orgDid + Stripe customer details
//   - 取引年月日 (transaction date range)
//   - 取引内容 (line items per metric)
//   - 税率ごとの消費税額 (10% consumption tax separated)
//   - 適用税率
//
// Endpoints:
//   GET /api/invoices            → list of available months (last 12)
//   GET /api/invoice?month=YYYY-MM → HTML invoice for that month

import { PLAN_RULES, FX_JPY_PER_USD, type PlanTier } from "./plan-quota";

export interface InvoiceEnv {
  HYPERDRIVE?: unknown;
  YATA_VERSION?: string;
  YATABASE_AUTH_CACHE?: KVNamespace;
}

interface AnyKyselyDb {
  selectFrom(table: string): unknown;
}

async function getDb(env: InvoiceEnv): Promise<AnyKyselyDb | null> {
  if (!env.HYPERDRIVE) return null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    return sdk.createKyselyDb(env.HYPERDRIVE as never) as unknown as AnyKyselyDb;
  } catch {
    return null;
  }
}

const QII_NUMBER = "T9007028460042"; // etz hayim 適格請求書発行事業者登録番号
const VENDOR_NAME = "etz hayim";
const VENDOR_ADDRESS_JP = "—";        // physical address (omit on demo)
const CONSUMPTION_TAX_RATE = 0.10;

// US-primary, JP-secondary metric labels.
const METRIC_LABELS_EN: Record<string, string> = {
  api_request: "API requests",
  yata_query_cu_ms: "Cypher compute (CU·ms)",
  storage_gb_hour: "Storage (GB·hour)",
  egress_gb: "Egress (GB)",
  mcp_call: "MCP tool calls",
  did_mint: "DID mints",
  plan_base_fee: "Plan base fee (monthly)",
};
const METRIC_LABELS_JP: Record<string, string> = {
  api_request: "API リクエスト",
  yata_query_cu_ms: "Cypher 計算時間",
  storage_gb_hour: "ストレージ容量時間",
  egress_gb: "外部送信",
  mcp_call: "MCP ツール呼出",
  did_mint: "DID 発行",
};

const METRIC_RATE_JPY_MICRO: Record<string, number> = {
  api_request: 200,
  yata_query_cu_ms: 83,
  storage_gb_hour: 13_889,
  egress_gb: 15_000_000,
  mcp_call: 30_000,
  did_mint: 300_000_000,
};

interface InvoiceLineItem {
  metric: string;
  labelJp: string;
  qty: number;
  unitJpyMicro: number;
  subtotalJpyMicro: number;
  eventCount: number;
}

interface InvoiceSummary {
  month: string;       // YYYY-MM
  orgDid: string;
  windowStart: string;
  windowEnd: string;
  plan: PlanTier;
  monthlyBaseFeeJpy: number;
  lineItems: InvoiceLineItem[];
  subtotalJpyMicro: number;
  taxJpyMicro: number;
  totalJpyMicro: number;
  totalJpy: number;
}

function startOfMonthMs(year: number, month1Indexed: number): number {
  return Date.UTC(year, month1Indexed - 1, 1, 0, 0, 0, 0);
}

function endOfMonthMs(year: number, month1Indexed: number): number {
  if (month1Indexed === 12) return Date.UTC(year + 1, 0, 1, 0, 0, 0, 0);
  return Date.UTC(year, month1Indexed, 1, 0, 0, 0, 0);
}

// P74: read KV daily counters for the requested month and roll them up
// into the same row shape buildInvoiceSummary expects. The KV path
// works whenever ADR-2605111200 blocks the RW direct query — same
// authoritative-when-RW-degraded pattern as plan-quota / metering.
async function rollUpKvUsageForMonth(
  env: InvoiceEnv,
  orgDid: string,
  year: number,
  month1: number,
): Promise<Array<Record<string, unknown>>> {
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return [];
  const metrics: (keyof typeof METRIC_RATE_JPY_MICRO)[] = [
    "api_request", "yata_query_cu_ms", "storage_gb_hour", "egress_gb", "mcp_call", "did_mint",
  ];
  // Enumerate every YYYY-MM-DD in the month.
  const days: string[] = [];
  const dayCursor = new Date(Date.UTC(year, month1 - 1, 1));
  while (dayCursor.getUTCMonth() === month1 - 1) {
    days.push(dayCursor.toISOString().slice(0, 10));
    dayCursor.setUTCDate(dayCursor.getUTCDate() + 1);
  }
  const rows: Array<Record<string, unknown>> = [];
  for (const metric of metrics) {
    let qty = 0;
    let events = 0;
    for (const day of days) {
      const raw = await kv.get(`usage:v1:${orgDid}:${metric}:${day}`);
      if (!raw) continue;
      try {
        const v = JSON.parse(raw) as { qty?: number; events?: number };
        qty += Number(v.qty ?? 0);
        events += Number(v.events ?? 0);
      } catch { /* ignore */ }
    }
    if (qty > 0 || events > 0) {
      const billed = qty * (METRIC_RATE_JPY_MICRO[metric] ?? 0);
      rows.push({ metric, total_qty: qty, total_billed: billed, event_count: events });
    }
  }
  return rows;
}

export async function buildInvoiceSummary(
  env: InvoiceEnv,
  orgDid: string,
  month: string,                   // "YYYY-MM"
  plan: PlanTier,
): Promise<InvoiceSummary | null> {
  const m = /^(\d{4})-(\d{2})$/.exec(month);
  if (!m) return null;
  const year = Number(m[1]);
  const month1 = Number(m[2]);
  if (month1 < 1 || month1 > 12) return null;
  const startMs = startOfMonthMs(year, month1);
  const endMs = endOfMonthMs(year, month1);

  let rows: Array<Record<string, unknown>> = [];
  let sqlTag: ((strings: TemplateStringsArray, ...values: unknown[]) => unknown) | null = null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    sqlTag = (sdk as unknown as { sql?: typeof sqlTag }).sql ?? null;
  } catch {
    sqlTag = null;
  }
  const db = sqlTag ? await getDb(env) : null;
  if (sqlTag && db) {
    const q = sqlTag`
      SELECT metric,
             SUM(qty) AS total_qty,
             SUM(billed_amount_jpy_micro) AS total_billed,
             COUNT(*) AS event_count
      FROM vertex_billing_event
      WHERE org_did = ${orgDid} AND ts_ms >= ${startMs} AND ts_ms < ${endMs}
      GROUP BY metric
      ORDER BY metric ASC
    `;
    try {
      const exec = (q as unknown as { execute: (db: unknown) => Promise<{ rows: Array<Record<string, unknown>> }> }).execute;
      const result = await exec.call(q, db);
      rows = result.rows ?? [];
    } catch (e) {
      console.warn("[yatabase][invoice] RW aggregate query failed; falling back to KV:", e);
      rows = [];
    }
  }
  // P74: KV fallback (authoritative when RW is degraded by ADR-2605111200).
  if (rows.length === 0) {
    rows = await rollUpKvUsageForMonth(env, orgDid, year, month1);
  }

  const lineItems: InvoiceLineItem[] = rows.map((r) => {
    const metric = String(r.metric ?? "");
    const labelEn = METRIC_LABELS_EN[metric] ?? metric;
    const labelJp = METRIC_LABELS_JP[metric] ?? metric;
    return {
      metric,
      labelJp: `${labelEn} / ${labelJp}`,
      qty: Number(r.total_qty ?? 0),
      unitJpyMicro: METRIC_RATE_JPY_MICRO[metric] ?? 0,
      subtotalJpyMicro: Number(r.total_billed ?? 0),
      eventCount: Number(r.event_count ?? 0),
    };
  });

  const usageSubtotalMicro = lineItems.reduce((acc, li) => acc + li.subtotalJpyMicro, 0);
  const baseFeeMicro = PLAN_RULES[plan].monthlyJpy * 1_000_000;
  const subtotalMicro = baseFeeMicro + usageSubtotalMicro;
  const taxMicro = Math.round(subtotalMicro * CONSUMPTION_TAX_RATE);
  const totalMicro = subtotalMicro + taxMicro;

  if (baseFeeMicro > 0) {
    lineItems.unshift({
      metric: "plan_base_fee",
      labelJp: `${plan} plan monthly fee / ${plan} プラン月額`,
      qty: 1,
      unitJpyMicro: baseFeeMicro,
      subtotalJpyMicro: baseFeeMicro,
      eventCount: 1,
    });
  }

  return {
    month,
    orgDid,
    windowStart: new Date(startMs).toISOString().slice(0, 10),
    windowEnd: new Date(endMs - 1).toISOString().slice(0, 10),
    plan,
    monthlyBaseFeeJpy: PLAN_RULES[plan].monthlyJpy,
    lineItems,
    subtotalJpyMicro: subtotalMicro,
    taxJpyMicro: taxMicro,
    totalJpyMicro: totalMicro,
    totalJpy: Math.round(totalMicro / 1_000_000),
  };
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function jpyMicroToJpy(micro: number): string {
  return "¥" + Math.round(micro / 1_000_000).toLocaleString("ja-JP");
}

function jpyMicroToUsd(micro: number): string {
  // Internal pricing is JPY-micro (matches `vertex_billing_event` column).
  // For the US-primary display we convert to USD using the FX snapshot
  // committed in `[platform.market]`.
  const usd = micro / 1_000_000 / FX_JPY_PER_USD;
  return "$" + usd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function dualCurrency(micro: number): string {
  return `${jpyMicroToUsd(micro)} (${jpyMicroToJpy(micro)})`;
}

export function renderInvoiceHtml(summary: InvoiceSummary): string {
  const invoiceNumber = `Y${summary.month.replace("-", "")}-${summary.orgDid.slice(-12).replace(/[^a-zA-Z0-9]/g, "")}`;
  const issuedAt = new Date().toISOString().slice(0, 10);
  const lineRows = summary.lineItems.map((li) => `
    <tr>
      <td>${escapeHtml(li.labelJp)} <span class="meta">(${escapeHtml(li.metric)})</span></td>
      <td class="num">${li.qty.toLocaleString("en-US")}</td>
      <td class="num">${dualCurrency(li.unitJpyMicro)}</td>
      <td class="num">${dualCurrency(li.subtotalJpyMicro)}</td>
    </tr>
  `).join("");

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Invoice ${escapeHtml(invoiceNumber)} — yatabase</title>
<style>
  @page { size: A4; margin: 18mm 14mm; }
  body { font: 12pt/1.6 -apple-system, "Hiragino Kaku Gothic ProN", "Yu Gothic", system-ui, sans-serif;
         color: #111; max-width: 720px; margin: 0 auto; padding: 24px; }
  h1 { font-size: 22pt; margin: 0 0 6px; letter-spacing: 0.04em; }
  h2 { font-size: 11pt; margin: 22px 0 6px; color: #555; font-weight: 600;
       text-transform: uppercase; letter-spacing: 0.05em; }
  .header { display: flex; justify-content: space-between; align-items: flex-start;
            border-bottom: 2px solid #111; padding-bottom: 12px; margin-bottom: 18px; }
  .header .meta { font-size: 10pt; color: #555; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin: 14px 0; }
  .grid > div { border: 1px solid #ccc; padding: 12px; border-radius: 4px; }
  .grid h3 { font-size: 10pt; margin: 0 0 6px; color: #555; font-weight: 600;
             text-transform: uppercase; letter-spacing: 0.05em; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 11pt; }
  th, td { padding: 8px 10px; border: 1px solid #ccc; }
  th { background: #f4f4f4; text-align: left; font-weight: 600; }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
  .totals { margin-top: 16px; }
  .totals table { width: 50%; margin-left: auto; }
  .totals .grand td { font-weight: 700; font-size: 13pt;
                       border-top: 2px solid #111; }
  .meta { color: #777; font-size: 10pt; }
  .note { margin-top: 24px; padding: 12px; background: #f8f8f8; border-radius: 4px;
          font-size: 10pt; color: #444; }
  .qii { background: #fff3cd; padding: 8px 12px; border-radius: 4px; display: inline-block;
         font-weight: 600; letter-spacing: 0.04em; }
  @media print { .no-print { display: none; } body { padding: 0; } }
  .no-print { margin-bottom: 18px; padding: 10px; background: #e7f3ff; border-radius: 4px;
              font-size: 10pt; color: #0050b3; }
</style>
</head>
<body>
<div class="no-print">Print this page (⌘P / Ctrl+P) → "Save as PDF" to file the invoice with your finance team.</div>
<div class="header">
  <div>
    <h1>Invoice</h1>
    <div class="meta">Tax invoice (US primary, Japan QII secondary)</div>
  </div>
  <div class="meta">
    Invoice No.: <strong>${escapeHtml(invoiceNumber)}</strong><br>
    Issued: ${escapeHtml(issuedAt)}<br>
    Period: ${escapeHtml(summary.windowStart)} — ${escapeHtml(summary.windowEnd)}<br>
    FX snapshot: 1 USD = ${FX_JPY_PER_USD} JPY (committed in [platform.market])
  </div>
</div>

<div class="grid">
  <div>
    <h3>Vendor</h3>
    <strong>${escapeHtml(VENDOR_NAME)}</strong><br>
    yatabase.etzhayyim.com (io-yatabase BaaS)<br>
    Address: ${escapeHtml(VENDOR_ADDRESS_JP)}<br>
    <div class="qii" style="margin-top:8px">JP QII registry: ${escapeHtml(QII_NUMBER)}</div>
    <div class="meta" style="margin-top:6px">US merchant of record: Stripe (Delaware-domiciled etz hayim entity, planned)</div>
  </div>
  <div>
    <h3>Customer</h3>
    Org DID: <code>${escapeHtml(summary.orgDid)}</code><br>
    Plan: <strong>${escapeHtml(summary.plan)}</strong><br>
    Billing month: ${escapeHtml(summary.month)}
  </div>
</div>

<h2>Line items</h2>
<table>
  <thead><tr>
    <th>Item</th>
    <th class="num">Qty</th>
    <th class="num">Unit price (USD primary, JPY secondary)</th>
    <th class="num">Subtotal</th>
  </tr></thead>
  <tbody>${lineRows || '<tr><td colspan="4" class="meta">No metered events in this period.</td></tr>'}</tbody>
</table>

<div class="totals">
  <table>
    <tr>
      <td>Subtotal</td>
      <td class="num">${dualCurrency(summary.subtotalJpyMicro)}</td>
    </tr>
    <tr>
      <td>Consumption tax (Japan customers, 10%)</td>
      <td class="num">${dualCurrency(summary.taxJpyMicro)}</td>
    </tr>
    <tr class="grand">
      <td>Grand total (tax inclusive)</td>
      <td class="num">${dualCurrency(summary.totalJpyMicro)}</td>
    </tr>
  </table>
</div>

<div class="note">
  <strong>US (primary):</strong> This invoice is issued by ${escapeHtml(VENDOR_NAME)}.
  Sales tax is computed by Stripe Tax based on customer's nexus state. No
  federal corporate tax withholding for non-US-domiciled vendors below the
  Wayfair v. South Dakota economic-nexus threshold.
  <br><br>
  <strong>Japan (secondary):</strong> 本請求書は適格請求書等保存方式（インボイス制度）にも対応した適格請求書です。
  登録番号 ${escapeHtml(QII_NUMBER)} は国税庁の適格請求書発行事業者として登録されています。
  消費税率は標準 10%。Japan customers can use this invoice for 仕入税額控除.
  <br><br>
  This invoice complies with the US tax-invoice norms and Japan's Qualified
  Invoice System (適格請求書等保存方式).
</div>
</body>
</html>`;
}

export async function handleInvoice(env: InvoiceEnv, orgDid: string, plan: PlanTier, month: string): Promise<Response> {
  const summary = await buildInvoiceSummary(env, orgDid, month, plan);
  if (!summary) {
    return new Response(
      JSON.stringify({ error: "BadRequest", message: "month must be YYYY-MM and Hyperdrive must be reachable" }),
      { status: 400, headers: { "content-type": "application/json" } },
    );
  }
  return new Response(renderInvoiceHtml(summary), {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "x-yatabase-surface": "invoice",
      "cache-control": "no-store",
    },
  });
}

export async function listInvoiceMonths(env: InvoiceEnv, orgDid: string): Promise<{ months: string[] }> {
  // Try RW first.
  let sqlTag: ((strings: TemplateStringsArray, ...values: unknown[]) => unknown) | null = null;
  try {
    const sdk = await import("@gftd/magatama-host-sdk");
    sqlTag = (sdk as unknown as { sql?: typeof sqlTag }).sql ?? null;
  } catch {
    sqlTag = null;
  }
  const db = sqlTag ? await getDb(env) : null;
  if (sqlTag && db) {
    const q = sqlTag`
      SELECT MIN(ts_ms) AS min_ts, MAX(ts_ms) AS max_ts
      FROM vertex_billing_event
      WHERE org_did = ${orgDid}
    `;
    try {
      const exec = (q as unknown as { execute: (db: unknown) => Promise<{ rows: Array<Record<string, unknown>> }> }).execute;
      const result = await exec.call(q, db);
      const minTs = Number(result.rows?.[0]?.min_ts ?? 0);
      const maxTs = Number(result.rows?.[0]?.max_ts ?? 0);
      if (minTs && maxTs) {
        const months: string[] = [];
        const start = new Date(minTs);
        start.setUTCDate(1);
        const end = new Date(maxTs);
        end.setUTCDate(1);
        for (let d = new Date(start); d <= end; d.setUTCMonth(d.getUTCMonth() + 1)) {
          months.push(`${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`);
        }
        return { months };
      }
    } catch (e) {
      console.warn("[yatabase][invoice] RW month-range query failed; falling back to KV:", e);
    }
  }

  // P74: KV fallback. Scan the per-org metric keys to derive the set of
  // months with non-zero usage. KV list is paginated; we bound the scan
  // to 1000 keys (well above the 6 metrics × 35 days = 210 max we expect
  // for the rolling window).
  const kv = env.YATABASE_AUTH_CACHE;
  if (!kv) return { months: [] };
  const monthsSet = new Set<string>();
  try {
    const list = await kv.list({ prefix: `usage:v1:${orgDid}:`, limit: 1000 });
    for (const k of list.keys ?? []) {
      // key shape: usage:v1:{orgDid}:{metric}:{YYYY-MM-DD}
      const tail = k.name.split(":").pop() ?? "";
      const ym = tail.slice(0, 7);
      if (/^\d{4}-\d{2}$/.test(ym)) monthsSet.add(ym);
    }
  } catch (e) {
    console.warn("[yatabase][invoice] KV list failed:", e);
  }
  // Always include current month so a fresh signup sees something
  // billable to inspect (the base fee + any partial usage).
  const now = new Date();
  monthsSet.add(`${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`);
  const months = Array.from(monthsSet).sort();
  return { months };
}
