/**
 * pptx rw-free — presentation-editor record types.
 *
 * Per ADR-2606011400. pptx is a PowerPoint editor (upload / WebGPU edit / OOXML
 * export). This package models the presentation document tree:
 *   presentation → slide → shape → textRun
 * Registry on AT PDS records (replaces the kagami graph). ADR-2605172000 RW-free.
 *
 * AXIS NOTE (ADR-2605172400): axis-clean — presentations/slides/shapes/text are
 * creative document work product (like editor/bim/cad/kami), shareable via the
 * public feed. No personal PII, no settlement, no fulfillment liability. Large
 * blobs (uploaded PPTX, images) referenced by CID.
 *
 * AT-Lexicon: no float. OOXML geometry is integer EMU; font size is integer
 * half-points; slide index is an integer.
 *
 * Identity hierarchy:
 *   did:web:pptx.etzhayyim.com                              — controller
 *   did:web:pptx.etzhayyim.com:pres:{presentationId}        — a presentation
 *   did:web:pptx.etzhayyim.com:slide:{slideId}              — a slide
 *   did:web:pptx.etzhayyim.com:shape:{shapeId}              — a shape
 *   did:web:pptx.etzhayyim.com:run:{runId}                  — a text run
 */

export const PPTX_DID_PREFIX = "did:web:pptx.etzhayyim.com:" as const;

export const PRESENTATION_COLLECTION = "com.etzhayyim.apps.pptx.presentation";
export const SLIDE_COLLECTION = "com.etzhayyim.apps.pptx.slide";
export const SHAPE_COLLECTION = "com.etzhayyim.apps.pptx.shape";
export const TEXTRUN_COLLECTION = "com.etzhayyim.apps.pptx.textRun";

// ─── Presentation ───────────────────────────────────────────────────

export type Visibility = "public" | "private";

export interface PresentationRecord {
  did: string;
  presentationId: string;
  title: string;
  ownerDid: string;
  visibility: Visibility;
  /** IPC/IPFS CID of the source PPTX blob, optional. */
  sourceCid?: string;
  createdAt: string;
}
export interface PresentationView extends PresentationRecord {
  presentationUri: string;
}
export interface CreatePresentationInput {
  presentationId: string;
  title: string;
  ownerDid: string;
  visibility?: Visibility;
  sourceCid?: string;
}
export interface CreatePresentationOutput {
  status: "created" | "alreadyExists" | "rejected";
  presentationUri?: string;
  did?: string;
  presentationId?: string;
  error?: string;
}
export interface GetPresentationInput {
  presentationId: string;
}
export interface GetPresentationOutput {
  presentation?: PresentationView;
  error?: string;
}
export interface ListPresentationsInput {
  ownerDid?: string;
  visibility?: Visibility;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListPresentationsOutput {
  items: PresentationView[];
  cursor?: string;
  total: number;
}

// ─── Slide ──────────────────────────────────────────────────────────

export interface SlideRecord {
  did: string;
  slideId: string;
  /** FK → presentation presentationId. */
  presentationId: string;
  /** 0-based slide index. */
  slideIndex: number;
  layout?: string;
  createdAt: string;
}
export interface SlideView extends SlideRecord {
  slideUri: string;
}
export interface AddSlideInput {
  slideId: string;
  presentationId: string;
  slideIndex: number;
  layout?: string;
}
export interface AddSlideOutput {
  status: "added" | "alreadyExists" | "rejected" | "presentationNotFound";
  slideUri?: string;
  did?: string;
  slideId?: string;
  error?: string;
}
export interface ListSlidesInput {
  presentationId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListSlidesOutput {
  items: SlideView[];
  cursor?: string;
  total: number;
}

// ─── Shape ──────────────────────────────────────────────────────────

export type ShapeType = "text" | "image" | "rectangle" | "ellipse" | "line" | "group" | "table" | "chart" | "other";

export interface ShapeRecord {
  did: string;
  shapeId: string;
  /** FK → slide slideId. */
  slideId: string;
  shapeType: ShapeType;
  /** OOXML geometry, integer EMU. */
  xEmu: number;
  yEmu: number;
  widthEmu: number;
  heightEmu: number;
  /** CID of an image/media blob (image shapes), optional. */
  contentCid?: string;
  createdAt: string;
}
export interface ShapeView extends ShapeRecord {
  shapeUri: string;
}
export interface AddShapeInput {
  shapeId: string;
  slideId: string;
  shapeType: ShapeType;
  xEmu: number;
  yEmu: number;
  widthEmu: number;
  heightEmu: number;
  contentCid?: string;
}
export interface AddShapeOutput {
  status: "added" | "alreadyExists" | "rejected" | "slideNotFound";
  shapeUri?: string;
  did?: string;
  shapeId?: string;
  error?: string;
}
export interface ListShapesInput {
  slideId?: string;
  shapeType?: ShapeType;
  limit?: number;
  cursor?: string;
}
export interface ListShapesOutput {
  items: ShapeView[];
  cursor?: string;
  total: number;
}

// ─── Text run ───────────────────────────────────────────────────────

export interface TextRunRecord {
  did: string;
  runId: string;
  /** FK → shape shapeId. */
  shapeId: string;
  text: string;
  bold: boolean;
  italic: boolean;
  /** Font size, integer half-points (e.g. 36 = 18pt). */
  fontHalfPt?: number;
  createdAt: string;
}
export interface TextRunView extends TextRunRecord {
  runUri: string;
}
export interface AddTextRunInput {
  runId: string;
  shapeId: string;
  text: string;
  bold?: boolean;
  italic?: boolean;
  fontHalfPt?: number;
}
export interface AddTextRunOutput {
  status: "added" | "alreadyExists" | "rejected" | "shapeNotFound";
  runUri?: string;
  did?: string;
  runId?: string;
  error?: string;
}
export interface ListTextRunsInput {
  shapeId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListTextRunsOutput {
  items: TextRunView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  presentationCount?: number;
  slideCount?: number;
  shapeCount?: number;
  textRunCount?: number;
  presentationsByVisibility?: Record<string, number>;
  shapesByType?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export const SHAPE_TYPES: ReadonlySet<string> = new Set(["text", "image", "rectangle", "ellipse", "line", "group", "table", "chart", "other"]);

export function isNonNegInt(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}
export function looksLikeCid(s: string): boolean {
  return /^b[a-z2-7]{20,}$/.test(s) || /^Qm[1-9A-HJ-NP-Za-km-z]{20,}$/.test(s);
}

export function presentationDidFor(id: string): string {
  return `${PPTX_DID_PREFIX}pres:${id.toLowerCase()}`;
}
export function presentationRkey(id: string): string {
  return `pres-${id.toLowerCase()}`;
}
export function slideDidFor(id: string): string {
  return `${PPTX_DID_PREFIX}slide:${id.toLowerCase()}`;
}
export function slideRkey(id: string): string {
  return `slide-${id.toLowerCase()}`;
}
export function shapeDidFor(id: string): string {
  return `${PPTX_DID_PREFIX}shape:${id.toLowerCase()}`;
}
export function shapeRkey(id: string): string {
  return `shape-${id.toLowerCase()}`;
}
export function runDidFor(id: string): string {
  return `${PPTX_DID_PREFIX}run:${id.toLowerCase()}`;
}
export function runRkey(id: string): string {
  return `run-${id.toLowerCase()}`;
}
