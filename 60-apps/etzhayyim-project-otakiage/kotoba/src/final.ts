/**
 * otakiage kotoba — final tier (slice 3, +5 → 13/10, 10/10 canonical ✓).
 *
 *   issueCertificate  — issue a Certificate record for a ritualized item
 *                       (rkey=certificate-{certId-slug}, idempotent)
 *   anchorCertificate — anchor a certificate to L2/L1 (records the anchor txid)
 *   scheduleMatsuri   — schedule a seasonal matsuri (rkey=matsuri-{matsuriId})
 *   coverage          — coverage report (item counts by status / mode / month)
 *   agentChat         — LLM chat persistence stub (LangServer pod-side LLM call)
 *
 * Closes otakiage at canonical 10/10 + 3 transition helpers = 13 total.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import { ritualize } from "./transitions.js";
import {
  idSlug,
  OTAKIAGE_DID_PREFIX,
  type AgentChatInput,
  type AgentChatOutput,
  type AgentChatRecord,
  type AnchorCertificateInput,
  type AnchorCertificateOutput,
  type CertificateRecord,
  type CoverageInput,
  type CoverageOutput,
  type IssueCertificateInput,
  type IssueCertificateOutput,
  type ItemRecord,
  type MatsuriRecord,
  type ScheduleMatsuriInput,
  type ScheduleMatsuriOutput,
  type ItemMode,
  type ItemStatus,
} from "./types.js";

const ITEM_COLLECTION = "com.etzhayyim.otakiage.item";
const CERTIFICATE_COLLECTION = "com.etzhayyim.otakiage.certificate";
const MATSURI_COLLECTION = "com.etzhayyim.otakiage.matsuri";
const AGENT_CHAT_COLLECTION = "com.etzhayyim.otakiage.agentChat";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

function certRkey(certId: string): string {
  return `certificate-${idSlug(certId)}`;
}

function certDid(certId: string): string {
  return `${OTAKIAGE_DID_PREFIX}certificate:${idSlug(certId)}`;
}

function matsuriRkey(matsuriId: string): string {
  return `matsuri-${idSlug(matsuriId)}`;
}

function matsuriDid(matsuriId: string): string {
  return `${OTAKIAGE_DID_PREFIX}matsuri:${idSlug(matsuriId)}`;
}

function agentChatRkey(chatId: string): string {
  return `agentchat-${idSlug(chatId)}`;
}

// ─── issueCertificate ───────────────────────────────────────────────

export async function issueCertificate(
  e: Etzhayyim,
  input: IssueCertificateInput
): Promise<IssueCertificateOutput> {
  if (!input.certId || !input.itemId || !input.issuerDid) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = certRkey(input.certId);
  const existing = await e
    .read<CertificateRecord>({ collection: CERTIFICATE_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      certificateUri: existing.records[0].uri,
      certId: input.certId,
    };
  }
  const did = certDid(input.certId);
  const now = new Date().toISOString();
  const record: CertificateRecord = {
    did,
    certId: input.certId,
    itemId: input.itemId,
    issuerDid: input.issuerDid,
    matsuriDid: input.matsuriDid,
    title: input.title,
    body: input.body,
    languages: input.languages,
    pdfCid: input.pdfCid,
    qrCid: input.qrCid,
    issuedAt: now,
    createdAt: now,
  };
  const receipt = await e.write({
    collection: CERTIFICATE_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });

  // Auto-ritualize the item if it's still in ritual_pending.
  if (input.autoRitualize !== false) {
    await ritualize(e, { itemId: input.itemId, certificateUri: receipt.uri }).catch(
      () => undefined
    );
  }

  return {
    status: "issued",
    certificateUri: receipt.uri,
    certId: input.certId,
    did,
  };
}

// ─── anchorCertificate ──────────────────────────────────────────────

export async function anchorCertificate(
  e: Etzhayyim,
  input: AnchorCertificateInput
): Promise<AnchorCertificateOutput> {
  if (!input.certId || !input.anchorTxHash || !input.anchorChain) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = certRkey(input.certId);
  const resp = await e
    .read<CertificateRecord>({ collection: CERTIFICATE_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  const existing = resp.records[0]?.value;
  if (!existing) {
    return { status: "rejected", error: "certificateNotFound" };
  }
  if (existing.anchorTxHash) {
    return {
      status: "alreadyAnchored",
      certificateUri: resp.records[0].uri,
      certId: input.certId,
      anchorTxHash: existing.anchorTxHash,
      anchorChain: existing.anchorChain,
    };
  }
  const merged: CertificateRecord = {
    ...existing,
    anchorTxHash: input.anchorTxHash,
    anchorChain: input.anchorChain,
    anchoredAt: new Date().toISOString(),
  };
  const receipt = await e.write({
    collection: CERTIFICATE_COLLECTION,
    record: merged as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "anchored",
    certificateUri: receipt.uri,
    certId: input.certId,
    anchorTxHash: input.anchorTxHash,
    anchorChain: input.anchorChain,
  };
}

// ─── scheduleMatsuri ────────────────────────────────────────────────

export async function scheduleMatsuri(
  e: Etzhayyim,
  input: ScheduleMatsuriInput
): Promise<ScheduleMatsuriOutput> {
  if (!input.matsuriId || !input.scheduledAt) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = matsuriRkey(input.matsuriId);
  const existing = await e
    .read<MatsuriRecord>({ collection: MATSURI_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      matsuriUri: existing.records[0].uri,
      matsuriId: input.matsuriId,
    };
  }
  const did = matsuriDid(input.matsuriId);
  const now = new Date().toISOString();
  const record: MatsuriRecord = {
    did,
    matsuriId: input.matsuriId,
    name: input.name,
    nameLocal: input.nameLocal,
    scheduledAt: input.scheduledAt,
    locationHint: input.locationHint,
    capacityItems: input.capacityItems,
    description: input.description,
    organizerDid: input.organizerDid,
    createdAt: now,
  };
  const receipt = await e.write({
    collection: MATSURI_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "scheduled",
    matsuriUri: receipt.uri,
    matsuriId: input.matsuriId,
    did,
  };
}

// ─── coverage ───────────────────────────────────────────────────────

export async function coverage(
  e: Etzhayyim,
  input: CoverageInput = {}
): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  let cursor: string | undefined;
  let scanned = 0;
  const byStatus: Record<ItemStatus, number> = {
    submitted: 0,
    reuse_open: 0,
    handed_over: 0,
    reuse_expired: 0,
    ritual_pending: 0,
    ritualized: 0,
  };
  const byMode: Record<ItemMode, number> = {
    reuse_only: 0,
    ritual_only: 0,
    reuse_then_ritual: 0,
  };
  const byMonth: Record<string, number> = {};
  while (scanned < maxScan) {
    const page = await e.read<ItemRecord>({
      collection: ITEM_COLLECTION,
      cursor,
      limit: PAGE_LIMIT,
    });
    for (const r of page.records) {
      const v = r.value;
      if (input.ownerDid && v.ownerDid !== input.ownerDid) continue;
      byStatus[v.status] = (byStatus[v.status] ?? 0) + 1;
      byMode[v.mode] = (byMode[v.mode] ?? 0) + 1;
      const month = v.submittedAt.slice(0, 7); // YYYY-MM
      byMonth[month] = (byMonth[month] ?? 0) + 1;
    }
    scanned += page.records.length;
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return {
    total: scanned,
    byStatus,
    byMode,
    byMonth,
    truncated: scanned >= maxScan,
  };
}

// ─── agentChat ──────────────────────────────────────────────────────

export async function agentChat(
  e: Etzhayyim,
  input: AgentChatInput
): Promise<AgentChatOutput> {
  if (!input.chatId || !input.userDid || !input.userMessage) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = agentChatRkey(input.chatId);
  const existing = await e
    .read<AgentChatRecord>({ collection: AGENT_CHAT_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      chatUri: existing.records[0].uri,
      chatId: input.chatId,
    };
  }
  // Note: agentChat is a thin persistence layer. The actual LLM call
  // lives in the LangServer pod (per ADR-2605111200). The pod computes
  // assistantReply + intent + suggestedAction, then invokes this
  // function with the result already in hand.
  const now = new Date().toISOString();
  const record: AgentChatRecord = {
    chatId: input.chatId,
    userDid: input.userDid,
    userMessage: input.userMessage,
    assistantReply: input.assistantReply,
    intent: input.intent,
    suggestedAction: input.suggestedAction,
    referencedItemIds: input.referencedItemIds,
    model: input.model,
    occurredAt: now,
    createdAt: now,
  };
  const receipt = await e.write({
    collection: AGENT_CHAT_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "registered",
    chatUri: receipt.uri,
    chatId: input.chatId,
  };
}
