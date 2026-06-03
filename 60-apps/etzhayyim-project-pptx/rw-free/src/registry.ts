/**
 * pptx rw-free — presentation + slide + shape + textRun registries + coverage.
 * AT PDS records (no RW). Document tree FK-validates down: slide→presentation,
 * shape→slide, textRun→shape. Creative document data; blobs by CID.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  PRESENTATION_COLLECTION,
  SHAPE_COLLECTION,
  SHAPE_TYPES,
  SLIDE_COLLECTION,
  TEXTRUN_COLLECTION,
  isNonNegInt,
  looksLikeCid,
  presentationDidFor,
  presentationRkey,
  runDidFor,
  runRkey,
  shapeDidFor,
  shapeRkey,
  slideDidFor,
  slideRkey,
  type AddShapeInput,
  type AddShapeOutput,
  type AddSlideInput,
  type AddSlideOutput,
  type AddTextRunInput,
  type AddTextRunOutput,
  type CoverageInput,
  type CoverageOutput,
  type CreatePresentationInput,
  type CreatePresentationOutput,
  type GetPresentationInput,
  type GetPresentationOutput,
  type ListPresentationsInput,
  type ListPresentationsOutput,
  type ListShapesInput,
  type ListShapesOutput,
  type ListSlidesInput,
  type ListSlidesOutput,
  type ListTextRunsInput,
  type ListTextRunsOutput,
  type PresentationRecord,
  type PresentationView,
  type ShapeRecord,
  type ShapeView,
  type SlideRecord,
  type SlideView,
  type TextRunRecord,
  type TextRunView,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

async function exists(e: Etzhayyim, collection: string, rkey: string): Promise<boolean> {
  const resp = await e.read({ collection, rkey }).catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

async function scanAll<T>(e: Etzhayyim, collection: string, maxScan: number, onRow: (v: T) => void): Promise<number> {
  let cursor: string | undefined;
  let scanned = 0;
  while (scanned < maxScan) {
    const page = await e.read<T>({ collection, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      if (scanned >= maxScan) break;
      onRow(r.value);
      scanned += 1;
    }
    if (scanned >= maxScan || !page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return scanned;
}

// ─── Presentation ───────────────────────────────────────────────────

export async function createPresentation(e: Etzhayyim, input: CreatePresentationInput): Promise<CreatePresentationOutput> {
  if (!input.presentationId || !input.title || !input.ownerDid) return { status: "rejected", error: "missingRequiredFields" };
  if (!input.ownerDid.startsWith("did:")) return { status: "rejected", error: "invalidOwnerDid" };
  if (input.sourceCid && !looksLikeCid(input.sourceCid)) return { status: "rejected", error: "invalidSourceCid" };
  const rkey = presentationRkey(input.presentationId);
  const existing = await e.read<PresentationRecord>({ collection: PRESENTATION_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", presentationUri: existing.records[0].uri, did: existing.records[0].value.did, presentationId: input.presentationId };
  }
  const did = presentationDidFor(input.presentationId);
  const record: PresentationRecord = {
    did,
    presentationId: input.presentationId,
    title: input.title,
    ownerDid: input.ownerDid,
    visibility: input.visibility ?? "private",
    sourceCid: input.sourceCid,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: PRESENTATION_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "created", presentationUri: receipt.uri, did, presentationId: input.presentationId };
}

export async function getPresentation(e: Etzhayyim, input: GetPresentationInput): Promise<GetPresentationOutput> {
  if (!input.presentationId) return { error: "invalidPresentationId" };
  const resp = await e.read<PresentationRecord>({ collection: PRESENTATION_COLLECTION, rkey: presentationRkey(input.presentationId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { presentation: { ...r.value, presentationUri: r.uri } };
}

export async function listPresentations(e: Etzhayyim, input: ListPresentationsInput = {}): Promise<ListPresentationsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<PresentationRecord>({ collection: PRESENTATION_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: PresentationView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.ownerDid && v.ownerDid !== input.ownerDid) return false;
      if (input.visibility && v.visibility !== input.visibility) return false;
      if (q && !v.title.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, presentationUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Slide ──────────────────────────────────────────────────────────

export async function addSlide(e: Etzhayyim, input: AddSlideInput): Promise<AddSlideOutput> {
  if (!input.slideId || !input.presentationId) return { status: "rejected", error: "missingRequiredFields" };
  if (!isNonNegInt(input.slideIndex)) return { status: "rejected", error: "slideIndexMustBeNonNegInt" };
  if (!(await exists(e, PRESENTATION_COLLECTION, presentationRkey(input.presentationId)))) {
    return { status: "presentationNotFound", error: `presentationNotFound:${input.presentationId}` };
  }
  const rkey = slideRkey(input.slideId);
  const existing = await e.read<SlideRecord>({ collection: SLIDE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", slideUri: existing.records[0].uri, did: existing.records[0].value.did, slideId: input.slideId };
  }
  const did = slideDidFor(input.slideId);
  const record: SlideRecord = {
    did,
    slideId: input.slideId,
    presentationId: input.presentationId,
    slideIndex: input.slideIndex,
    layout: input.layout,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: SLIDE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", slideUri: receipt.uri, did, slideId: input.slideId };
}

export async function listSlides(e: Etzhayyim, input: ListSlidesInput = {}): Promise<ListSlidesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<SlideRecord>({ collection: SLIDE_COLLECTION, cursor: input.cursor, limit });
  const items: SlideView[] = resp.records
    .filter((r) => (input.presentationId ? r.value.presentationId === input.presentationId : true))
    .map((r) => ({ ...r.value, slideUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Shape ──────────────────────────────────────────────────────────

export async function addShape(e: Etzhayyim, input: AddShapeInput): Promise<AddShapeOutput> {
  if (!input.shapeId || !input.slideId) return { status: "rejected", error: "missingRequiredFields" };
  if (!SHAPE_TYPES.has(input.shapeType)) return { status: "rejected", error: "invalidShapeType" };
  for (const v of [input.xEmu, input.yEmu, input.widthEmu, input.heightEmu]) {
    if (!isNonNegInt(v)) return { status: "rejected", error: "geometryMustBeNonNegIntEmu" };
  }
  if (input.contentCid && !looksLikeCid(input.contentCid)) return { status: "rejected", error: "invalidContentCid" };
  if (!(await exists(e, SLIDE_COLLECTION, slideRkey(input.slideId)))) {
    return { status: "slideNotFound", error: `slideNotFound:${input.slideId}` };
  }
  const rkey = shapeRkey(input.shapeId);
  const existing = await e.read<ShapeRecord>({ collection: SHAPE_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", shapeUri: existing.records[0].uri, did: existing.records[0].value.did, shapeId: input.shapeId };
  }
  const did = shapeDidFor(input.shapeId);
  const record: ShapeRecord = {
    did,
    shapeId: input.shapeId,
    slideId: input.slideId,
    shapeType: input.shapeType,
    xEmu: input.xEmu,
    yEmu: input.yEmu,
    widthEmu: input.widthEmu,
    heightEmu: input.heightEmu,
    contentCid: input.contentCid,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: SHAPE_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", shapeUri: receipt.uri, did, shapeId: input.shapeId };
}

export async function listShapes(e: Etzhayyim, input: ListShapesInput = {}): Promise<ListShapesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ShapeRecord>({ collection: SHAPE_COLLECTION, cursor: input.cursor, limit });
  const items: ShapeView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.slideId && v.slideId !== input.slideId) return false;
      if (input.shapeType && v.shapeType !== input.shapeType) return false;
      return true;
    })
    .map((r) => ({ ...r.value, shapeUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Text run ───────────────────────────────────────────────────────

export async function addTextRun(e: Etzhayyim, input: AddTextRunInput): Promise<AddTextRunOutput> {
  if (!input.runId || !input.shapeId || input.text == null) return { status: "rejected", error: "missingRequiredFields" };
  if (input.fontHalfPt != null && !isNonNegInt(input.fontHalfPt)) return { status: "rejected", error: "fontHalfPtMustBeNonNegInt" };
  if (!(await exists(e, SHAPE_COLLECTION, shapeRkey(input.shapeId)))) {
    return { status: "shapeNotFound", error: `shapeNotFound:${input.shapeId}` };
  }
  const rkey = runRkey(input.runId);
  const existing = await e.read<TextRunRecord>({ collection: TEXTRUN_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", runUri: existing.records[0].uri, did: existing.records[0].value.did, runId: input.runId };
  }
  const did = runDidFor(input.runId);
  const record: TextRunRecord = {
    did,
    runId: input.runId,
    shapeId: input.shapeId,
    text: input.text,
    bold: Boolean(input.bold),
    italic: Boolean(input.italic),
    fontHalfPt: input.fontHalfPt,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: TEXTRUN_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "added", runUri: receipt.uri, did, runId: input.runId };
}

export async function listTextRuns(e: Etzhayyim, input: ListTextRunsInput = {}): Promise<ListTextRunsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<TextRunRecord>({ collection: TEXTRUN_COLLECTION, cursor: input.cursor, limit });
  const items: TextRunView[] = resp.records
    .filter((r) => (input.shapeId ? r.value.shapeId === input.shapeId : true))
    .map((r) => ({ ...r.value, runUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const presentationsByVisibility: Record<string, number> = {};
  const presentationCount = await scanAll<PresentationRecord>(e, PRESENTATION_COLLECTION, maxScan, (v) => {
    presentationsByVisibility[v.visibility] = (presentationsByVisibility[v.visibility] ?? 0) + 1;
  });
  const slideCount = await scanAll<SlideRecord>(e, SLIDE_COLLECTION, maxScan, () => {});
  const shapesByType: Record<string, number> = {};
  const shapeCount = await scanAll<ShapeRecord>(e, SHAPE_COLLECTION, maxScan, (v) => {
    shapesByType[v.shapeType] = (shapesByType[v.shapeType] ?? 0) + 1;
  });
  const textRunCount = await scanAll<TextRunRecord>(e, TEXTRUN_COLLECTION, maxScan, () => {});
  return {
    presentationCount,
    slideCount,
    shapeCount,
    textRunCount,
    presentationsByVisibility,
    shapesByType,
    truncated: presentationCount >= maxScan || slideCount >= maxScan || shapeCount >= maxScan || textRunCount >= maxScan,
  };
}
