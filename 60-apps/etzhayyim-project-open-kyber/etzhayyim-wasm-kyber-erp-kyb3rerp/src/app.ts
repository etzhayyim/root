// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 etzhayyim Japan株式会社 / etzhayyim. All rights reserved.
// Licensed under the Apache License, Version 2.0 — see LICENSE at repo root.

// kyber.etzhayyim.com — Corporate ERP Intelligence
// TS Native Worker: 28 XRPC commands across Accounting / AP-AR / HR / Procurement / Inventory / Sales / Asset / Governance / Management / Billing
// Design E 3-Tier Write: domain data via com.atproto.repo.createRecord (internal, non-federable)
//
// NOTE: list/read paths currently return empty envelopes — SQL (G()) was deprecated 2026-04-13
// and Kysely read integration for graphar.vertex_* is pending. Commits are recorded via
// handleComAtprotoSyncSubscribeReposCommit so the PDS → RisingWave pipeline still projects writes.

import {
  asAgentTool,
  createCadenceState,
  createInboxBuffer,
  createKyselyDb,
  createWorkerExport,
  decodeJson,
  genID,
  nowISO,
  nsid,
  str,
  withCapabilityTags,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK,
} from "@etzhayyim/magatama-host-sdk";

// ───────────────────────────── shared state ─────────────────────────────

const cadenceState = createCadenceState();
const inbox = createInboxBuffer();
let appId = "";
let actorDID = "";

// Kyber APQC/BPMN projector (cross-project; see ADR-0025)
const APQC_PROJECTOR_DID = "did:web:kyber-projector.etzhayyim.com";
const APQC_PROJECTOR_NANOID = "kyb3proj";

// Department DIDs (multi-DID per app; pre-registered via magatama.jsonld entities)
const DEPT = {
  accounting: "did:web:kyber.etzhayyim.com:dept:accounting",
  hr: "did:web:kyber.etzhayyim.com:dept:hr",
  procurement: "did:web:kyber.etzhayyim.com:dept:procurement",
  inventory: "did:web:kyber.etzhayyim.com:dept:inventory",
  sales: "did:web:kyber.etzhayyim.com:dept:sales",
  asset: "did:web:kyber.etzhayyim.com:dept:asset",
  governance: "did:web:kyber.etzhayyim.com:dept:governance",
} as const;

// IFRS-aligned chart of accounts seed (25 entries)
const CHART_OF_ACCOUNTS_SEED: Array<{ code: string; name: string; type: string }> = [
  { code: "1000", name: "Cash", type: "asset" },
  { code: "1100", name: "Accounts Receivable", type: "asset" },
  { code: "1200", name: "Inventory", type: "asset" },
  { code: "1300", name: "Prepaid Expenses", type: "asset" },
  { code: "1500", name: "Property, Plant & Equipment", type: "asset" },
  { code: "1510", name: "Accumulated Depreciation", type: "contra-asset" },
  { code: "1600", name: "Intangible Assets", type: "asset" },
  { code: "2000", name: "Accounts Payable", type: "liability" },
  { code: "2100", name: "Accrued Expenses", type: "liability" },
  { code: "2200", name: "Short-Term Debt", type: "liability" },
  { code: "2500", name: "Long-Term Debt", type: "liability" },
  { code: "3000", name: "Share Capital", type: "equity" },
  { code: "3100", name: "Retained Earnings", type: "equity" },
  { code: "4000", name: "Sales Revenue", type: "revenue" },
  { code: "4100", name: "Service Revenue", type: "revenue" },
  { code: "5000", name: "Cost of Goods Sold", type: "expense" },
  { code: "5100", name: "Salaries & Wages", type: "expense" },
  { code: "5200", name: "Rent Expense", type: "expense" },
  { code: "5300", name: "Utilities", type: "expense" },
  { code: "5400", name: "Depreciation Expense", type: "expense" },
  { code: "5500", name: "Marketing", type: "expense" },
  { code: "5600", name: "Professional Fees", type: "expense" },
  { code: "5700", name: "Insurance", type: "expense" },
  { code: "5900", name: "Interest Expense", type: "expense" },
  { code: "6000", name: "Income Tax Expense", type: "expense" },
];

// ───────────────────────────── write helpers ─────────────────────────────

function write(sdk: HostSDK, kind: string, rec: Record<string, unknown>, did?: string): void {
  const collection = `com.etzhayyim.apps.kyber.${kind}`;
  const enriched = {
    ...rec,
    createdAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: appId,
  };
  const payload: Record<string, unknown> = {
    collection,
    recordJson: JSON.stringify(enriched),
  };
  if (did) payload.did = did;
  sdk.pds.dispatch({ type: "com.atproto.repo.createRecord", payload });
}

function emptyList<T>(key: string, args: Record<string, unknown>) {
  const limit = Number(args.limit ?? 50);
  const offset = Number(args.offset ?? 0);
  return { ok: true, [key]: [] as T[], total: 0, offset, limit };
}

function parseItems(raw: unknown): Array<Record<string, unknown>> {
  if (Array.isArray(raw)) return raw as Array<Record<string, unknown>>;
  if (typeof raw === "string") {
    try {
      const v = JSON.parse(raw);
      return Array.isArray(v) ? v : [];
    } catch {
      return [];
    }
  }
  return [];
}

function sumItems(items: Array<Record<string, unknown>>): { subtotal: number; tax: number; total: number } {
  let subtotal = 0;
  let tax = 0;
  for (const it of items) {
    const qty = Number(it.quantity ?? 0);
    const price = Number(it.unitPrice ?? 0);
    const rate = Number(it.taxRate ?? 0);
    const line = qty * price;
    subtotal += line;
    tax += line * rate;
  }
  return { subtotal, tax, total: subtotal + tax };
}

function straightLineDepreciationMonthly(asset: Record<string, unknown>): number {
  const cost = Number(asset.cost ?? 0);
  const salvageValue = Number(asset.salvageValue ?? 0);
  const usefulLifeMonths = Number(asset.usefulLifeMonths ?? 0);
  if (usefulLifeMonths <= 0) return 0;
  return Math.max(0, (cost - salvageValue) / usefulLifeMonths);
}

// ───────────────────────────── Accounting (5) ─────────────────────────────

async function cmdCreateJournalEntry(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const lines = parseItems(args.lines);
  if (lines.length < 2) return { ok: false, error: "journal requires at least 2 lines (debit + credit)" };
  let debit = 0;
  let credit = 0;
  for (const l of lines) {
    debit += Number(l.debit ?? 0);
    credit += Number(l.credit ?? 0);
  }
  if (Math.abs(debit - credit) > 0.005) {
    return { ok: false, error: `unbalanced journal: debit=${debit} credit=${credit}` };
  }
  const journalId = genID("je");
  const date = str(args.date ?? nowISO().slice(0, 10));
  const debitAccount = str(lines.find((l) => Number(l.debit ?? 0) > 0)?.account ?? "");
  const creditAccount = str(lines.find((l) => Number(l.credit ?? 0) > 0)?.account ?? "");
  const now = nowISO();
  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db.insertInto("vertex_kyber_journal_entry" as never).values({
      vertex_id: `at://${DEPT.accounting}/com.etzhayyim.apps.kyber.journalEntry/${journalId}`,
      entry_id: journalId,
      org_did: "anon",
      actor_did: DEPT.accounting,
      date,
      description: str(args.memo ?? ""),
      debit_account: debitAccount,
      credit_account: creditAccount,
      amount: debit,
      currency: str(args.currency ?? "JPY"),
      reference: "",
      period: date.slice(0, 7),
      created_at: now,
    } as never).execute());
  } catch (err) {
    return { ok: false, error: "JournalEntryFailed", detail: String(err) };
  }
  return { ok: true, journalId, debitTotal: debit, creditTotal: credit };
}

function cmdListJournalEntries(_sdk: HostSDK, body: Uint8Array) {
  return emptyList("journalEntries", decodeJson(body, {}) as Record<string, unknown>);
}

function cmdGetTrialBalance(_sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  return {
    ok: true,
    asOf: str(args.asOf ?? nowISO().slice(0, 10)),
    currency: str(args.currency ?? "JPY"),
    accounts: [] as Array<Record<string, unknown>>,
    totals: { debit: 0, credit: 0 },
  };
}

async function cmdCreateAccount(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const code = str(args.code ?? "");
  const name = str(args.name ?? "");
  const type = str(args.type ?? "asset");
  if (!code || !name) return { ok: false, error: "code and name required" };
  const accountId = genID("acc");
  const now = nowISO();
  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db.insertInto("vertex_kyber_account" as never).values({
      vertex_id: `at://${DEPT.accounting}/com.etzhayyim.apps.kyber.account/${accountId}`,
      account_id: accountId,
      org_did: "anon",
      actor_did: DEPT.accounting,
      code,
      name,
      account_type: type,
      seed: false,
      created_at: now,
    } as never).execute());
  } catch (err) {
    return { ok: false, error: "CreateAccountFailed", detail: String(err) };
  }
  return { ok: true, accountId, code, name, type };
}

async function cmdSeedChartOfAccounts(sdk: HostSDK, _body: Uint8Array) {
  const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
  const now = nowISO();
  for (const a of CHART_OF_ACCOUNTS_SEED) {
    const accountId = genID("acc");
    try {
      await (db.insertInto("vertex_kyber_account" as never).values({
        vertex_id: `at://${DEPT.accounting}/com.etzhayyim.apps.kyber.account/${accountId}`,
        account_id: accountId,
        org_did: "anon",
        actor_did: DEPT.accounting,
        code: a.code,
        name: a.name,
        account_type: a.type,
        seed: true,
        created_at: now,
      } as never).execute());
    } catch {} // skip duplicates on re-seed
  }
  return { ok: true, seeded: CHART_OF_ACCOUNTS_SEED.length };
}

// ───────────────────────────── AP / AR (2) ─────────────────────────────

async function cmdCreateInvoice(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const direction = str(args.direction ?? "receivable");
  const counterparty = str(args.counterparty ?? "");
  const items = parseItems(args.items);
  if (!counterparty || items.length === 0) {
    return { ok: false, error: "counterparty and items required" };
  }
  const { subtotal, tax, total } = sumItems(items);
  const invoiceId = genID("inv");
  const now = nowISO();
  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db.insertInto("vertex_kyber_invoice" as never).values({
      vertex_id: `at://${DEPT.accounting}/com.etzhayyim.apps.kyber.invoice/${invoiceId}`,
      invoice_id: invoiceId,
      org_did: "anon",
      actor_did: DEPT.accounting,
      invoice_number: invoiceId,
      invoice_type: direction,
      party_did: "",
      party_name: counterparty,
      issue_date: now.slice(0, 10),
      due_date: str(args.dueDate ?? ""),
      subtotal,
      tax,
      total,
      currency: str(args.currency ?? "JPY"),
      status: "draft",
      items_json: JSON.stringify(items),
      created_at: now,
    } as never).execute());
  } catch (err) {
    return { ok: false, error: "CreateInvoiceFailed", detail: String(err) };
  }
  return { ok: true, invoiceId, direction, counterparty, subtotal, tax, total };
}

function cmdListInvoices(_sdk: HostSDK, body: Uint8Array) {
  return emptyList("invoices", decodeJson(body, {}) as Record<string, unknown>);
}

// ───────────────────────────── HR (2) ─────────────────────────────

async function cmdRegisterEmployee(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const name = str(args.name ?? "");
  const department = str(args.department ?? "");
  if (!name || !department) return { ok: false, error: "name and department required" };
  const employeeId = genID("emp");
  const nameParts = name.split(" ");
  const firstName = nameParts[0] ?? name;
  const lastName = nameParts.slice(1).join(" ") || "";
  const now = nowISO();
  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db.insertInto("vertex_kyber_employee" as never).values({
      vertex_id: `at://${DEPT.hr}/com.etzhayyim.apps.kyber.employee/${employeeId}`,
      employee_id: employeeId,
      org_did: "anon",
      actor_did: DEPT.hr,
      employee_number: employeeId,
      first_name: firstName,
      last_name: lastName,
      email: str(args.email ?? ""),
      department,
      position: str(args.position ?? ""),
      employment_type: str(args.employmentType ?? "full-time"),
      hire_date: now.slice(0, 10),
      status: "active",
      created_at: now,
    } as never).execute());
  } catch (err) {
    return { ok: false, error: "RegisterEmployeeFailed", detail: String(err) };
  }
  return { ok: true, employeeId, name, department };
}

function cmdListEmployees(_sdk: HostSDK, body: Uint8Array) {
  return emptyList("employees", decodeJson(body, {}) as Record<string, unknown>);
}

// ───────────────────────────── Procurement (2) ─────────────────────────────

async function cmdCreatePurchaseOrder(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const vendor = str(args.vendor ?? "");
  const items = parseItems(args.items);
  if (!vendor || items.length === 0) return { ok: false, error: "vendor and items required" };
  const { subtotal, tax, total } = sumItems(items);
  const purchaseOrderId = genID("po");
  const now = nowISO();
  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db.insertInto("vertex_kyber_purchase_order" as never).values({
      vertex_id: `at://${DEPT.procurement}/com.etzhayyim.apps.kyber.purchaseOrder/${purchaseOrderId}`,
      po_id: purchaseOrderId,
      org_did: "anon",
      actor_did: DEPT.procurement,
      po_number: purchaseOrderId,
      vendor_did: "",
      vendor_name: vendor,
      order_date: now.slice(0, 10),
      expected_delivery: str(args.deliveryDate ?? ""),
      subtotal,
      tax,
      total,
      currency: str(args.currency ?? "JPY"),
      status: "draft",
      items_json: JSON.stringify(items),
      created_at: now,
    } as never).execute());
  } catch (err) {
    return { ok: false, error: "CreatePurchaseOrderFailed", detail: String(err) };
  }
  return { ok: true, purchaseOrderId, vendor, subtotal, tax, total };
}

function cmdListPurchaseOrders(_sdk: HostSDK, body: Uint8Array) {
  return emptyList("purchaseOrders", decodeJson(body, {}) as Record<string, unknown>);
}

// ───────────────────────────── Inventory (2) ─────────────────────────────

async function cmdRegisterInventoryItem(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const sku = str(args.sku ?? "");
  const name = str(args.name ?? "");
  if (!sku || !name) return { ok: false, error: "sku and name required" };
  const inventoryItemId = genID("inv");
  const now = nowISO();
  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db.insertInto("vertex_kyber_inventory_item" as never).values({
      vertex_id: `at://${DEPT.inventory}/com.etzhayyim.apps.kyber.inventoryItem/${inventoryItemId}`,
      item_id: inventoryItemId,
      org_did: "anon",
      actor_did: DEPT.inventory,
      sku,
      name,
      description: "",
      category: str(args.category ?? ""),
      quantity_on_hand: Number(args.quantity ?? 0),
      unit_cost: Number(args.unitCost ?? 0),
      reorder_point: Number(args.reorderPoint ?? 0),
      warehouse: str(args.warehouse ?? "default"),
      created_at: now,
    } as never).execute());
  } catch (err) {
    return { ok: false, error: "RegisterInventoryItemFailed", detail: String(err) };
  }
  return { ok: true, inventoryItemId, sku, name };
}

function cmdListInventory(_sdk: HostSDK, body: Uint8Array) {
  return emptyList("items", decodeJson(body, {}) as Record<string, unknown>);
}

// ───────────────────────────── Sales (2) ─────────────────────────────

async function cmdCreateSalesOrder(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const customer = str(args.customer ?? "");
  const items = parseItems(args.items);
  if (!customer || items.length === 0) return { ok: false, error: "customer and items required" };
  const { subtotal, tax, total } = sumItems(items);
  const shipping = Number(args.shipping ?? 0);
  const grandTotal = total + shipping;
  const salesOrderId = genID("so");
  const now = nowISO();
  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db.insertInto("vertex_kyber_sales_order" as never).values({
      vertex_id: `at://${DEPT.sales}/com.etzhayyim.apps.kyber.salesOrder/${salesOrderId}`,
      order_id: salesOrderId,
      org_did: "anon",
      actor_did: DEPT.sales,
      order_number: salesOrderId,
      customer_did: "",
      customer_name: customer,
      order_date: now.slice(0, 10),
      expected_delivery: "",
      subtotal,
      tax,
      total: grandTotal,
      currency: str(args.currency ?? "JPY"),
      status: "draft",
      items_json: JSON.stringify(items),
      created_at: now,
    } as never).execute());
  } catch (err) {
    return { ok: false, error: "CreateSalesOrderFailed", detail: String(err) };
  }
  return { ok: true, salesOrderId, customer, subtotal, tax, shipping, total: grandTotal };
}

function cmdListSalesOrders(_sdk: HostSDK, body: Uint8Array) {
  return emptyList("salesOrders", decodeJson(body, {}) as Record<string, unknown>);
}

// ───────────────────────────── Asset (3) ─────────────────────────────

async function cmdRegisterFixedAsset(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const assetTag = str(args.assetTag ?? "");
  const name = str(args.name ?? "");
  if (!assetTag || !name) return { ok: false, error: "assetTag and name required" };

  const fixedAssetId = genID("fa");
  const cost = Number(args.cost ?? 0);
  const salvageValue = Number(args.salvageValue ?? 0);
  const usefulLifeMonths = Number(args.usefulLifeMonths ?? 60);
  const usefulLifeYears = Math.max(1, Math.ceil(usefulLifeMonths / 12));
  const acquisitionDate = str(args.acquisitionDate ?? nowISO().slice(0, 10));
  const now = nowISO();

  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db.insertInto("vertex_kyber_fixed_asset" as never).values({
      vertex_id: `at://${DEPT.asset}/com.etzhayyim.apps.kyber.fixedAsset/${fixedAssetId}`,
      asset_id: fixedAssetId,
      org_did: "anon",
      actor_did: DEPT.asset,
      asset_number: assetTag,
      name,
      category: str(args.category ?? ""),
      acquisition_date: acquisitionDate,
      acquisition_cost: cost,
      useful_life_years: usefulLifeYears,
      depreciation_method: str(args.depreciationMethod ?? "straight-line"),
      salvage_value: salvageValue,
      accumulated_depreciation: 0,
      net_book_value: cost - salvageValue,
      location: "",
      status: str(args.status ?? "active"),
      created_at: now,
    } as never).execute());
  } catch (err) {
    return { ok: false, error: "RegisterFixedAssetFailed", detail: String(err) };
  }

  return { ok: true, fixedAssetId, assetTag, name, cost, usefulLifeMonths };
}

function cmdListFixedAssets(_sdk: HostSDK, body: Uint8Array) {
  return emptyList("fixedAssets", decodeJson(body, {}) as Record<string, unknown>);
}

async function cmdRunDepreciation(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const period = str(args.period ?? nowISO().slice(0, 7));
  const assets = parseItems(args.assets);
  const totalAmount = assets.reduce((sum, a) => sum + straightLineDepreciationMonthly(a), 0);

  const depreciationRunId = genID("depr");
  const now = nowISO();
  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db.insertInto("vertex_kyber_depreciation_run" as never).values({
      vertex_id: `at://${DEPT.asset}/com.etzhayyim.apps.kyber.depreciationRun/${depreciationRunId}`,
      run_id: depreciationRunId,
      org_did: "anon",
      actor_did: DEPT.asset,
      period,
      total_depreciation: totalAmount,
      asset_count: assets.length,
      status: "completed",
      created_at: now,
    } as never).execute());
  } catch (err) {
    return { ok: false, error: "RunDepreciationFailed", detail: String(err) };
  }

  return { ok: true, depreciationRunId, period, assetCount: assets.length, totalAmount };
}

// ───────────────────────────── Governance (3) ─────────────────────────────

async function cmdRegisterPolicyControl(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const controlCode = str(args.controlCode ?? "");
  const title = str(args.title ?? "");
  if (!controlCode || !title) return { ok: false, error: "controlCode and title required" };

  const policyControlId = genID("ctl");
  const now = nowISO();
  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db.insertInto("vertex_kyber_policy_control" as never).values({
      vertex_id: `at://${DEPT.governance}/com.etzhayyim.apps.kyber.policyControl/${policyControlId}`,
      control_id: policyControlId,
      org_did: "anon",
      actor_did: DEPT.governance,
      control_code: controlCode,
      name: title,
      description: str(args.description ?? ""),
      framework: str(args.framework ?? "iso-27001"),
      category: str(args.category ?? ""),
      status: str(args.status ?? "active"),
      owner_did: str(args.owner ?? ""),
      review_date: "",
      created_at: now,
    } as never).execute());
  } catch (err) {
    return { ok: false, error: "RegisterPolicyControlFailed", detail: String(err) };
  }

  return { ok: true, policyControlId, controlCode, title };
}

async function cmdRecordRiskIssue(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const riskTitle = str(args.riskTitle ?? "");
  if (!riskTitle) return { ok: false, error: "riskTitle required" };

  const riskIssueId = genID("risk");
  const likelihood = str(args.likelihood ?? "medium");
  const severity = str(args.severity ?? "medium");
  const now = nowISO();
  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db.insertInto("vertex_kyber_risk_issue" as never).values({
      vertex_id: `at://${DEPT.governance}/com.etzhayyim.apps.kyber.riskIssue/${riskIssueId}`,
      issue_id: riskIssueId,
      org_did: "anon",
      actor_did: DEPT.governance,
      title: riskTitle,
      description: str(args.mitigationPlan ?? ""),
      category: str(args.category ?? "operational"),
      likelihood,
      impact: severity,
      risk_score: null,
      status: str(args.status ?? "open"),
      owner_did: str(args.owner ?? ""),
      due_date: str(args.dueDate ?? ""),
      created_at: now,
    } as never).execute());
  } catch (err) {
    return { ok: false, error: "RecordRiskIssueFailed", detail: String(err) };
  }

  return { ok: true, riskIssueId, riskTitle };
}

function cmdListRiskIssues(_sdk: HostSDK, body: Uint8Array) {
  return emptyList("riskIssues", decodeJson(body, {}) as Record<string, unknown>);
}

// ───────────────────── Billing / Tenant (4) — ADR-2605072300 ─────────────────────────────

const BILLING_DID = "did:web:kyber.etzhayyim.com:dept:billing";

function nowMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

function planLimits(planId: string): { maxUsers: number; maxMonthlyTxns: number } {
  switch (planId) {
    case "starter": return { maxUsers: 5,      maxMonthlyTxns: 5000 };
    case "growth":  return { maxUsers: 20,     maxMonthlyTxns: 50000 };
    case "scale":   return { maxUsers: 999999, maxMonthlyTxns: 999999 };
    default:        return { maxUsers: 1,      maxMonthlyTxns: 100 };
  }
}

// Stripe integration is REMOVED from the canonical etzhayyim repo per
// Charter Rider §1.3 + ADR-2605192115 + ADR-2605211900 §"Constitutional
// invariants" (no fiat payment processors / no `subscription` purpose
// on external substrate calls). Downstream commercial forks (e.g.
// kyber.etzhayyim.com) that operate as for-profit ERP tenancies are expected
// to patch in their own stripePost implementation locally.
//
// This stub keeps the call sites in cmdProvisionTenant + cmdReportUsage
// type-correct without re-introducing the api.stripe.com URL into the
// canonical source tree. Calls degrade silently: provision continues
// without a customer id, usage reporting reports zero. The deployed
// kyber.etzhayyim.com instance ships a separate billing-non-religious-corp
// module that re-exports a real stripePost. See
// 90-docs/adr/2605212100-stripe-removed-from-religious-corp-canonical.md.
async function stripePost(
  _path: string,
  _params: Record<string, string>,
  _stripeKey: string,
): Promise<{ ok: boolean; id?: string; errorMessage?: string }> {
  return {
    ok: false,
    errorMessage:
      "Stripe disabled in canonical etzhayyim repo (Charter Rider §1.3). " +
      "Patch your downstream commercial fork to re-implement stripePost.",
  };
}

async function cmdProvisionTenant(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const orgDid = str(args.orgDid ?? "");
  const orgName = str(args.orgName ?? "");
  const email = str(args.email ?? "");
  const planId = str(args.planId ?? "free");

  if (!orgDid || !orgName) return { ok: false, error: "orgDid and orgName required" };

  const env = sdk.env as Record<string, unknown>;
  const stripeKey = str(env.STRIPE_SECRET_KEY ?? "");
  const db = createKyselyDb(env.HYPERDRIVE as never);

  // Idempotency check via Hyperdrive read
  try {
    const existing = await (db
      .selectFrom("vertex_kyber_billing_tenant" as never)
      .select(["tenant_id" as never, "plan_id" as never, "status" as never, "stripe_customer_id" as never])
      .where("org_did" as never, "=" as never, orgDid as never)
      .orderBy("created_at" as never, "asc" as never)
      .limit(1)
      .executeTakeFirst() as Promise<Record<string, unknown> | undefined>);
    if (existing) {
      return {
        ok: true,
        tenantId: str(existing.tenant_id ?? ""),
        planId: str(existing.plan_id ?? planId),
        status: str(existing.status ?? "active"),
        stripeCustomerId: str(existing.stripe_customer_id ?? ""),
        alreadyExisted: true,
      };
    }
  } catch (_) { /* table not ready — fall through */ }

  const tenantId = genID("tenant");
  let stripeCustomerId = "";
  if (stripeKey && planId !== "free") {
    const res = await stripePost("customers", {
      name: orgName,
      email,
      "metadata[orgDid]": orgDid,
      "metadata[tenantId]": tenantId,
      "metadata[planId]": planId,
    }, stripeKey);
    if (res.ok && res.id) stripeCustomerId = res.id;
  }

  const limits = planLimits(planId);
  const now = nowISO();
  const vertexId = `at://${BILLING_DID}/com.etzhayyim.apps.kyber.billingTenant/${tenantId}`;

  // ADR-0036: Hyperdrive direct write → RisingWave (T2 Domain)
  try {
    await (db
      .insertInto("vertex_kyber_billing_tenant" as never)
      .values({
        vertex_id: vertexId,
        tenant_id: tenantId,
        org_did: orgDid,
        actor_did: BILLING_DID,
        plan_id: planId,
        stripe_customer_id: stripeCustomerId,
        plan_activated_at: now,
        status: "active",
        max_users: limits.maxUsers,
        max_monthly_txns: limits.maxMonthlyTxns,
        created_at: now,
        updated_at: now,
      } as never)
      .execute());
  } catch (err) {
    return { ok: false, error: "ProvisionFailed", detail: String(err) };
  }

  return { ok: true, tenantId, planId, status: "active", stripeCustomerId, alreadyExisted: false };
}

async function cmdGetTenantPlan(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const orgDid = str(args.orgDid ?? "");
  if (!orgDid) return { ok: false, error: "orgDid required" };

  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    const tenant = await (db
      .selectFrom("vertex_kyber_billing_tenant" as never)
      .selectAll()
      .where("org_did" as never, "=" as never, orgDid as never)
      .orderBy("created_at" as never, "asc" as never)
      .limit(1)
      .executeTakeFirst() as Promise<Record<string, unknown> | undefined>);

    if (!tenant) return { ok: false, error: "TenantNotFound" };

    const usage = await (db
      .selectFrom("mv_kyber_monthly_usage" as never)
      .selectAll()
      .where("org_did" as never, "=" as never, orgDid as never)
      .where("period_month" as never, "=" as never, nowMonth() as never)
      .execute() as Promise<Array<Record<string, unknown>>>);

    const usageMap: Record<string, number> = {};
    for (const row of usage) {
      usageMap[str(row.meter_type ?? "")] = Number(row.total_count ?? 0);
    }

    return {
      ok: true,
      tenantId: str(tenant.tenant_id ?? ""),
      orgDid: str(tenant.org_did ?? ""),
      planId: str(tenant.plan_id ?? "free"),
      status: str(tenant.status ?? "active"),
      maxUsers: Number(tenant.max_users ?? 1),
      maxMonthlyTxns: Number(tenant.max_monthly_txns ?? 100),
      stripeCustomerId: str(tenant.stripe_customer_id ?? ""),
      planActivatedAt: str(tenant.plan_activated_at ?? ""),
      usage: {
        xrpcRequests: usageMap.xrpc_request ?? 0,
        rwRows: usageMap.rw_row ?? 0,
        llmTokens: usageMap.llm_token ?? 0,
        langserverInvocations: usageMap.langserver_invocation ?? 0,
        pdsBytes: usageMap.pds_byte ?? 0,
      },
    };
  } catch (err) {
    return { ok: false, error: "ReadError", detail: String(err) };
  }
}

async function cmdRecordUsage(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const orgDid = str(args.orgDid ?? "");
  const meterType = str(args.meterType ?? "");
  const deltaCount = Number(args.deltaCount ?? 1);
  const periodMonth = str(args.periodMonth ?? nowMonth());

  if (!orgDid || !meterType) return { ok: false, error: "orgDid and meterType required" };
  if (deltaCount <= 0) return { ok: false, error: "deltaCount must be > 0" };

  const meterId = genID("meter");
  const now = nowISO();
  const vertexId = `at://${BILLING_DID}/com.etzhayyim.apps.kyber.usageMeter/${meterId}`;

  // ADR-0036: Hyperdrive direct write → RisingWave (T2 Domain)
  try {
    const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
    await (db
      .insertInto("vertex_kyber_usage_meter" as never)
      .values({
        vertex_id: vertexId,
        meter_id: meterId,
        org_did: orgDid,
        actor_did: BILLING_DID,
        meter_type: meterType,
        period_month: periodMonth,
        delta_count: deltaCount,
        reported_to_stripe: false,
        created_at: now,
      } as never)
      .execute());
  } catch (err) {
    return { ok: false, error: "RecordUsageFailed", detail: String(err) };
  }

  return { ok: true, meterId };
}

async function cmdReportUsageToStripe(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const dryRun = Boolean(args.dryRun ?? false);
  const periodMonth = str(args.periodMonth ?? nowMonth());
  const env = sdk.env as Record<string, unknown>;
  const stripeKey = str(env.STRIPE_SECRET_KEY ?? "");

  if (!stripeKey) return { ok: false, reported: 0, skipped: 0, errors: ["STRIPE_SECRET_KEY not configured"] };

  let reported = 0;
  let skipped = 0;
  const errors: string[] = [];

  try {
    const db = createKyselyDb(env.HYPERDRIVE as never);

    // Fetch paid tenants with usage this month
    const rows = await (db
      .selectFrom("mv_kyber_monthly_usage" as never)
      .innerJoin(
        "vertex_kyber_billing_tenant" as never,
        "vertex_kyber_billing_tenant.tenant_id" as never,
        "mv_kyber_monthly_usage.tenant_id" as never,
      )
      .select([
        "mv_kyber_monthly_usage.tenant_id" as never,
        "mv_kyber_monthly_usage.org_did" as never,
        "mv_kyber_monthly_usage.meter_type" as never,
        "mv_kyber_monthly_usage.total_count" as never,
        "vertex_kyber_billing_tenant.plan_id" as never,
        "vertex_kyber_billing_tenant.stripe_customer_id" as never,
      ])
      .where("mv_kyber_monthly_usage.period_month" as never, "=" as never, periodMonth as never)
      .where("vertex_kyber_billing_tenant.plan_id" as never, "!=" as never, "free" as never)
      .execute() as Promise<Array<Record<string, unknown>>>);

    if (dryRun) return { ok: true, reported: 0, skipped: rows.length, errors: [], dryRun: true, periodMonth };

    for (const row of rows) {
      const tenantId = str(row.tenant_id ?? "");
      const meterType = str(row.meter_type ?? "");
      const totalCount = Number(row.total_count ?? 0);
      const stripeCustomerId = str(row.stripe_customer_id ?? "");

      if (!stripeCustomerId || totalCount === 0) { skipped++; continue; }

      // Stripe Meter API (https://docs.stripe.com/api/billing/meter-event/create)
      const res = await stripePost("billing/meter_events", {
        event_name: `kyber_${meterType}`,
        payload: JSON.stringify({ stripe_customer_id: stripeCustomerId, value: String(totalCount) }),
        identifier: `${tenantId}:${periodMonth}:${meterType}`,
      }, stripeKey);

      if (res.ok) {
        reported++;
        // ADR-0036: record stripe report via Hyperdrive direct write (idempotency)
        const reportId = genID("srpt");
        const reportAt = nowISO();
        try {
          await (db
            .insertInto("vertex_kyber_stripe_report" as never)
            .values({
              vertex_id: `at://${BILLING_DID}/com.etzhayyim.apps.kyber.kyberStripeReport/${reportId}`,
              report_id: reportId,
              tenant_id: tenantId,
              org_did: str(row.org_did ?? ""),
              actor_did: BILLING_DID,
              period_month: periodMonth,
              meter_type: meterType,
              total_count: totalCount,
              stripe_event_id: res.id ?? "",
              status: "reported",
              reported_at: reportAt,
              created_at: reportAt,
            } as never)
            .execute());
        } catch {} // non-fatal: Stripe event already sent
      } else {
        errors.push(`${tenantId}/${meterType}: ${res.errorMessage}`);
      }
    }
  } catch (err) {
    errors.push(String(err));
  }

  return { ok: errors.length === 0, reported, skipped, errors, periodMonth };
}

// ───────────────────────────── Management / Integration (5) ─────────────────────────────

async function cmdRegisterDepartments(sdk: HostSDK, _body: Uint8Array) {
  const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
  const now = nowISO();
  const entries: Array<{ role: string; did: string; departmentId: string }> = [];
  for (const [role, did] of Object.entries(DEPT)) {
    const departmentId = genID("dept");
    try {
      await (db.insertInto("vertex_kyber_department" as never).values({
        vertex_id: `at://${did}/com.etzhayyim.apps.kyber.department/${departmentId}`,
        department_id: departmentId,
        org_did: "anon",
        actor_did: did,
        role,
        dept_did: did,
        created_at: now,
      } as never).execute());
    } catch {} // idempotent: skip if already registered
    entries.push({ role, did, departmentId });
  }
  return { ok: true, departments: entries };
}

function cmdDashboard(_sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const period = str(args.period ?? nowISO().slice(0, 7));
  return {
    ok: true,
    period,
    modules: {
      accounting: { journalEntries: 0, trialBalance: { debit: 0, credit: 0 } },
      apAr: { receivableOpen: 0, payableOpen: 0, currency: "JPY" },
      hr: { activeEmployees: 0, departments: Object.keys(DEPT).length },
      procurement: { openPOs: 0 },
      inventory: { skus: 0, lowStock: 0 },
      sales: { openOrders: 0 },
      asset: { activeAssets: 0, depreciationRuns: 0 },
      governance: { activeControls: 0, openRiskIssues: 0 },
    },
    departments: Object.keys(DEPT),
    note: "dashboard metrics are stubs; reads re-enable after graphar.vertex_* Kysely wiring",
  };
}

// ───── Bonus: integration catalog (referenced from UI) ─────

const INTEGRATION_CATALOG = [
  { id: "mailer", name: "com.etzhayyim.apps.mailer", kind: "messaging", status: "available" },
  { id: "calendar", name: "com.etzhayyim.apps.calendar", kind: "scheduling", status: "available" },
  { id: "projector", name: "com.etzhayyim.projector", kind: "pm", status: "available" },
  { id: "drive", name: "com.etzhayyim.apps.drive", kind: "storage", status: "available" },
  { id: "apqc", name: "com.etzhayyim.apps.apqc", kind: "process-framework", status: "available" },
];

function cmdListIntegrationCatalog(_sdk: HostSDK, _body: Uint8Array) {
  return { ok: true, integrations: INTEGRATION_CATALOG, total: INTEGRATION_CATALOG.length };
}

async function cmdSyncIntegrationCatalog(sdk: HostSDK, _body: Uint8Array) {
  const db = createKyselyDb((sdk.env as Record<string, unknown>).HYPERDRIVE as never);
  const now = nowISO();
  for (const i of INTEGRATION_CATALOG) {
    const bindingId = genID("bind");
    try {
      await (db.insertInto("vertex_kyber_integration_binding" as never).values({
        vertex_id: `at://${actorDID || "did:web:kyber.etzhayyim.com"}/com.etzhayyim.apps.kyber.integrationBinding/${bindingId}`,
        binding_id: bindingId,
        org_did: "anon",
        actor_did: actorDID || "did:web:kyber.etzhayyim.com",
        integration_id: i.id,
        name: i.name,
        description: i.kind,
        category: i.kind,
        xrpc_method: "",
        synced_at: now,
        created_at: now,
      } as never).execute());
    } catch {} // skip duplicates on re-sync
  }
  return { ok: true, synced: INTEGRATION_CATALOG.length };
}

// ───────────────────────────── Reactive input ─────────────────────────────

export function handleComAtprotoSyncSubscribeReposCommit(
  _sdk: HostSDK,
  commit: ComAtprotoSyncSubscribeReposCommit,
): { ok: true; detail: string } {
  if (commit.action !== "create") return { ok: true, detail: "skip non-create" };
  const collection = str(commit.collection ?? "");
  inbox.inboundCommits.push({ collection, action: "create", ts: Date.now() });
  return { ok: true, detail: `accepted ${collection}` };
}

// ───────────────────────────── APQC projector bootstrap ─────────────────────────────

function cmdInitApqcProjector(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const projectorDid = str(args.projectorDid ?? APQC_PROJECTOR_DID);
  const projectorNanoid = str(args.projectorNanoid ?? APQC_PROJECTOR_NANOID);
  const scope = str(args.scope ?? "all");

  // 1. Follow projector so its subscribeRepos delivers kyber commits.
  sdk.pds.dispatch({
    type: "app.bsky.graph.follow",
    payload: { nanoid: projectorNanoid, subject: projectorDid },
  });

  // 2. Emit bootstrap record — projector onCommit detects this and auto-registers
  //    the 13 APQC L1 DIDs + 28 BPMN bindings (idempotent).
  const bootstrapRkey = genID("boot");
  sdk.pds.dispatch({
    type: "com.atproto.repo.createRecord",
    payload: {
      collection: "com.etzhayyim.apps.kyber.apqcBootstrap",
      recordJson: JSON.stringify({
        projectorDid,
        scope,
        requestedAt: nowISO(),
        org_id: "anon",
        user_id: "anon",
        actor_id: appId,
      }),
    },
  });

  return { ok: true, projectorDid, followed: true, bootstrapRkey, scope };
}

// ───────────────────────────── Command wiring ─────────────────────────────

function configureApp(sdk: HostSDK): void {
  const app = sdk.app;
  app
    // Accounting (5)
    .command(nsid("com.etzhayyim.apps.kyber.createJournalEntry"), async (_c, b) => cmdCreateJournalEntry(sdk, b),
      asAgentTool("Create a double-entry journal (debit/credit balance required)"),
      withCapabilityTags("accounting", "gl"))
    .command(nsid("com.etzhayyim.apps.kyber.listJournalEntries"), async (_c, b) => cmdListJournalEntries(sdk, b),
      asAgentTool("List journal entries (date/account filter)"),
      withCapabilityTags("accounting", "query"))
    .command(nsid("com.etzhayyim.apps.kyber.getTrialBalance"), async (_c, b) => cmdGetTrialBalance(sdk, b),
      asAgentTool("Trial balance as of date"),
      withCapabilityTags("accounting", "report"))
    .command(nsid("com.etzhayyim.apps.kyber.createAccount"), async (_c, b) => cmdCreateAccount(sdk, b),
      asAgentTool("Add a chart-of-accounts entry"),
      withCapabilityTags("accounting", "coa"))
    .command(nsid("com.etzhayyim.apps.kyber.seedChartOfAccounts"), async (_c, b) => cmdSeedChartOfAccounts(sdk, b),
      asAgentTool("Seed 25 IFRS-aligned default accounts"),
      withCapabilityTags("accounting", "coa", "seed"))
    // AP/AR (2)
    .command(nsid("com.etzhayyim.apps.kyber.createInvoice"), async (_c, b) => cmdCreateInvoice(sdk, b),
      asAgentTool("Create invoice (AP or AR; multi-line items; tax)"),
      withCapabilityTags("finance", "invoice"))
    .command(nsid("com.etzhayyim.apps.kyber.listInvoices"), async (_c, b) => cmdListInvoices(sdk, b),
      asAgentTool("List invoices (direction/status filter)"),
      withCapabilityTags("finance", "query"))
    // HR (2)
    .command(nsid("com.etzhayyim.apps.kyber.registerEmployee"), async (_c, b) => cmdRegisterEmployee(sdk, b),
      asAgentTool("Register employee with department/position/salary"),
      withCapabilityTags("hr", "employee"))
    .command(nsid("com.etzhayyim.apps.kyber.listEmployees"), async (_c, b) => cmdListEmployees(sdk, b),
      asAgentTool("List employees (department/status filter)"),
      withCapabilityTags("hr", "query"))
    // Procurement (2)
    .command(nsid("com.etzhayyim.apps.kyber.createPurchaseOrder"), async (_c, b) => cmdCreatePurchaseOrder(sdk, b),
      asAgentTool("Create purchase order (vendor / items / delivery)"),
      withCapabilityTags("procurement", "po"))
    .command(nsid("com.etzhayyim.apps.kyber.listPurchaseOrders"), async (_c, b) => cmdListPurchaseOrders(sdk, b),
      asAgentTool("List purchase orders (vendor/status filter)"),
      withCapabilityTags("procurement", "query"))
    // Inventory (2)
    .command(nsid("com.etzhayyim.apps.kyber.registerInventoryItem"), async (_c, b) => cmdRegisterInventoryItem(sdk, b),
      asAgentTool("Register inventory item (SKU / warehouse / reorder)"),
      withCapabilityTags("inventory", "sku"))
    .command(nsid("com.etzhayyim.apps.kyber.listInventory"), async (_c, b) => cmdListInventory(sdk, b),
      asAgentTool("List inventory (category / warehouse / low-stock filter)"),
      withCapabilityTags("inventory", "query"))
    // Sales (2)
    .command(nsid("com.etzhayyim.apps.kyber.createSalesOrder"), async (_c, b) => cmdCreateSalesOrder(sdk, b),
      asAgentTool("Create sales order (customer / items / tax / shipping)"),
      withCapabilityTags("sales", "so"))
    .command(nsid("com.etzhayyim.apps.kyber.listSalesOrders"), async (_c, b) => cmdListSalesOrders(sdk, b),
      asAgentTool("List sales orders (customer/status filter)"),
      withCapabilityTags("sales", "query"))
    // Asset (3)
    .command(nsid("com.etzhayyim.apps.kyber.registerFixedAsset"), async (_c, b) => cmdRegisterFixedAsset(sdk, b),
      asAgentTool("Register fixed asset for capitalization and depreciation"),
      withCapabilityTags("asset", "fixed-asset"))
    .command(nsid("com.etzhayyim.apps.kyber.listFixedAssets"), async (_c, b) => cmdListFixedAssets(sdk, b),
      asAgentTool("List fixed assets (category/status/owner filter)"),
      withCapabilityTags("asset", "query"))
    .command(nsid("com.etzhayyim.apps.kyber.runDepreciation"), async (_c, b) => cmdRunDepreciation(sdk, b),
      asAgentTool("Run period depreciation (straight-line) and post summary"),
      withCapabilityTags("asset", "depreciation", "accounting"))
    // Governance (3)
    .command(nsid("com.etzhayyim.apps.kyber.registerPolicyControl"), async (_c, b) => cmdRegisterPolicyControl(sdk, b),
      asAgentTool("Register policy/control item for governance and compliance"),
      withCapabilityTags("governance", "compliance", "control"))
    .command(nsid("com.etzhayyim.apps.kyber.recordRiskIssue"), async (_c, b) => cmdRecordRiskIssue(sdk, b),
      asAgentTool("Record enterprise risk issue with severity and mitigation plan"),
      withCapabilityTags("governance", "risk", "issue"))
    .command(nsid("com.etzhayyim.apps.kyber.listRiskIssues"), async (_c, b) => cmdListRiskIssues(sdk, b),
      asAgentTool("List risk issues (severity/status/owner filter)"),
      withCapabilityTags("governance", "risk", "query"))
    // Management (5 incl. integrations)
    .command(nsid("com.etzhayyim.apps.kyber.registerDepartments"), async (_c, b) => cmdRegisterDepartments(sdk, b),
      asAgentTool("Register the 7 department DIDs"),
      withCapabilityTags("management", "did"))
    .command(nsid("com.etzhayyim.apps.kyber.dashboard"), async (_c, b) => cmdDashboard(sdk, b),
      asAgentTool("ERP dashboard — period summary across 8 modules"),
      withCapabilityTags("management", "dashboard"))
    .command(nsid("com.etzhayyim.apps.kyber.listIntegrationCatalog"), async (_c, b) => cmdListIntegrationCatalog(sdk, b),
      asAgentTool("List available cross-app integrations"),
      withCapabilityTags("integration", "catalog"))
    .command(nsid("com.etzhayyim.apps.kyber.syncIntegrationCatalog"), async (_c, b) => cmdSyncIntegrationCatalog(sdk, b),
      asAgentTool("Sync integration catalog into integrationBinding records"),
      withCapabilityTags("integration", "sync"))
    // APQC/BPMN projector bootstrap (cross-project; ADR-0025)
    .command(nsid("com.etzhayyim.apps.kyber.initApqcProjector"), async (_c, b) => cmdInitApqcProjector(sdk, b),
      asAgentTool("Bootstrap kyber-projector: follow + emit apqcBootstrap record"),
      withCapabilityTags("apqc", "bpmn", "bootstrap", "cross-project"))
    // Billing (4) — ADR-2605072300
    .command(nsid("com.etzhayyim.apps.kyber.provisionTenant"), async (_c, b) => cmdProvisionTenant(sdk, b),
      asAgentTool("Provision a kyber tenant (idempotent by orgDid). Called by yoro.etzhayyim.com signup flow."),
      withCapabilityTags("billing", "tenant", "signup"))
    .command(nsid("com.etzhayyim.apps.kyber.getTenantPlan"), async (_c, b) => cmdGetTenantPlan(sdk, b),
      asAgentTool("Return current plan, usage counters, and limits for a tenant"),
      withCapabilityTags("billing", "plan", "query"))
    .command(nsid("com.etzhayyim.apps.kyber.recordUsage"), async (_c, b) => cmdRecordUsage(sdk, b),
      asAgentTool("Append a usage delta to the usage meter (xrpc_request / rw_row / llm_token / langserver_invocation / pds_byte)"),
      withCapabilityTags("billing", "meter"))
    .command(nsid("com.etzhayyim.apps.kyber.reportUsageToStripe"), async (_c, b) => cmdReportUsageToStripe(sdk, b),
      asAgentTool("Flush monthly usage for paid tenants to Stripe Meter API (scheduled monthly)"),
      withCapabilityTags("billing", "stripe", "scheduled"));
}

// ───────────────────────────── Worker export ─────────────────────────────

export default createWorkerExport((sdk) => {
  appId = sdk.pds.selfNanoid ?? "kyb3rerp";
  actorDID = sdk.pds.selfRepo ?? "did:web:kyber.etzhayyim.com";
  void actorDID;
  void cadenceState;
  configureApp(sdk);
});
