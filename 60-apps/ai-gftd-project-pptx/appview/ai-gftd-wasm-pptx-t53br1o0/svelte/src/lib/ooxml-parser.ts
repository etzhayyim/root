/**
 * OOXML (.pptx) Parser — decompress ZIP, parse DrawingML XML into typed slide graph.
 *
 * PPTX is a ZIP containing:
 *   [Content_Types].xml
 *   _rels/.rels
 *   ppt/presentation.xml
 *   ppt/slides/slide{N}.xml
 *   ppt/slideLayouts/slideLayout{N}.xml
 *   ppt/slideMasters/slideMaster{N}.xml
 *   ppt/theme/theme{N}.xml
 *   ppt/media/{images}
 *
 * We parse into a flat graph model (PptxPresentation → PptxSlide → PptxShape/PptxImage)
 * suitable for kagami SQL persistence and KAMI Engine rendering.
 */

import { unzipSync, strFromU8 } from "fflate";

// ---------------------------------------------------------------------------
// Types — mirror kagami graph labels
// ---------------------------------------------------------------------------

/** EMU (English Metric Unit) = 1/914400 inch. OOXML native unit. */
export type Emu = number;

export interface PptxPresentation {
  id: string;
  title: string;
  width: Emu;
  height: Emu;
  slides: PptxSlide[];
  theme: PptxTheme | null;
}

export interface PptxSlide {
  id: string;
  order: number;
  layoutRef: string;
  background: string | null;
  shapes: PptxShape[];
  images: PptxImage[];
}

export interface PptxShape {
  id: string;
  slideId: string;
  type: "rect" | "ellipse" | "roundRect" | "triangle" | "arrow" | "line" | "freeform" | "textBox";
  name: string;
  x: Emu;
  y: Emu;
  w: Emu;
  h: Emu;
  rotation: number;
  fill: string | null;
  stroke: string | null;
  strokeWidth: number;
  textBody: PptxTextBody | null;
  /** Whether the shape is visible on the canvas. Default: true. */
  visible?: boolean;
  /** Whether the shape is locked (prevents selection/move). Default: false. */
  locked?: boolean;
  /** Group identifier for grouped shapes. Shapes with the same groupId move together. */
  groupId?: string;
  /** Corner radius for roundRect shapes, in EMU. */
  cornerRadius?: number;
}

export interface PptxTextBody {
  align: "left" | "center" | "right" | "justify";
  verticalAlign: "top" | "middle" | "bottom";
  paragraphs: PptxParagraph[];
}

export interface PptxParagraph {
  level: number;
  spacing: number;
  runs: PptxRun[];
}

export interface PptxRun {
  text: string;
  bold: boolean;
  italic: boolean;
  underline: boolean;
  size: number;
  color: string;
  font: string;
}

export interface PptxImage {
  id: string;
  slideId: string;
  x: Emu;
  y: Emu;
  w: Emu;
  h: Emu;
  /** Blob data (extracted from ppt/media/) */
  blob: Uint8Array | null;
  mime: string;
  rId: string;
}

export interface PptxTheme {
  name: string;
  colors: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Parser
// ---------------------------------------------------------------------------

let idCounter = 0;
function nextId(prefix: string): string {
  return `${prefix}_${++idCounter}_${Date.now().toString(36)}`;
}

/** Parse a .pptx file (ArrayBuffer) into a PptxPresentation graph. */
export function parsePptx(buffer: ArrayBuffer): PptxPresentation {
  idCounter = 0;
  const files = unzipSync(new Uint8Array(buffer));

  const presentation = parsePresentation(files);
  presentation.theme = parseTheme(files);

  const slideRels = discoverSlides(files);
  for (let i = 0; i < slideRels.length; i++) {
    const slideXml = getFileText(files, slideRels[i]);
    if (!slideXml) continue;

    const slideId = nextId("slide");
    const relPath = slideRels[i].replace(/slide\d+\.xml$/, "");
    const relFile = `ppt/slides/_rels/slide${i + 1}.xml.rels`;
    const rels = parseRels(files, relFile);

    const slide = parseSlide(slideXml, slideId, i, rels, files);
    presentation.slides.push(slide);
  }

  return presentation;
}

/** Get text content of a file in the ZIP. */
function getFileText(files: Record<string, Uint8Array>, path: string): string | null {
  const data = files[path];
  if (!data) return null;
  return strFromU8(data);
}

/** Parse ppt/presentation.xml for slide size. */
function parsePresentation(files: Record<string, Uint8Array>): PptxPresentation {
  const xml = getFileText(files, "ppt/presentation.xml") ?? "";
  const cx = extractAttr(xml, "p:sldSz", "cx");
  const cy = extractAttr(xml, "p:sldSz", "cy");

  return {
    id: nextId("pres"),
    title: "Imported Presentation",
    width: cx ? parseInt(cx, 10) : 9144000,
    height: cy ? parseInt(cy, 10) : 6858000,
    slides: [],
    theme: null,
  };
}

/** Discover slide file paths from [Content_Types].xml or directory listing. */
function discoverSlides(files: Record<string, Uint8Array>): string[] {
  const paths: string[] = [];
  for (const key of Object.keys(files)) {
    if (/^ppt\/slides\/slide\d+\.xml$/.test(key)) {
      paths.push(key);
    }
  }
  // Sort by slide number
  paths.sort((a, b) => {
    const na = parseInt(a.match(/slide(\d+)/)?.[1] ?? "0", 10);
    const nb = parseInt(b.match(/slide(\d+)/)?.[1] ?? "0", 10);
    return na - nb;
  });
  return paths;
}

/** Parse relationship file to map rId → target path. */
function parseRels(files: Record<string, Uint8Array>, relPath: string): Map<string, string> {
  const map = new Map<string, string>();
  const xml = getFileText(files, relPath);
  if (!xml) return map;

  const regex = /Id="(rId\d+)"\s+[^>]*Target="([^"]+)"/g;
  let m: RegExpExecArray | null;
  while ((m = regex.exec(xml)) !== null) {
    map.set(m[1], m[2]);
  }
  return map;
}

/** Parse a single slide XML into PptxSlide. */
function parseSlide(
  xml: string,
  slideId: string,
  order: number,
  rels: Map<string, string>,
  files: Record<string, Uint8Array>,
): PptxSlide {
  const slide: PptxSlide = {
    id: slideId,
    order,
    layoutRef: "",
    background: extractBgColor(xml),
    shapes: [],
    images: [],
  };

  // Parse shape tree: <p:sp> elements
  const spBlocks = extractBlocks(xml, "p:sp");
  for (const sp of spBlocks) {
    const shape = parseShape(sp, slideId);
    if (shape) slide.shapes.push(shape);
  }

  // Parse picture elements: <p:pic>
  const picBlocks = extractBlocks(xml, "p:pic");
  for (const pic of picBlocks) {
    const image = parsePicture(pic, slideId, rels, files);
    if (image) slide.images.push(image);
  }

  return slide;
}

/** Parse <p:sp> block into PptxShape. */
function parseShape(xml: string, slideId: string): PptxShape | null {
  const off = extractOffsetExtent(xml);
  if (!off) return null;

  const name = extractAttr(xml, "p:nvSpPr/p:cNvPr", "name")
    ?? extractAttrSimple(xml, "p:cNvPr", "name")
    ?? "";

  const prstGeom = extractAttr(xml, "a:prstGeom", "prst") ?? "rect";
  const shapeType = mapPresetGeometry(prstGeom);

  const rotation = parseInt(extractAttr(xml, "a:xfrm", "rot") ?? "0", 10);
  const fill = extractSolidFill(xml);
  const stroke = extractLineColor(xml);
  const strokeWidth = parseInt(extractAttr(xml, "a:ln", "w") ?? "0", 10);

  const textBody = parseTextBody(xml);

  return {
    id: nextId("shape"),
    slideId,
    type: shapeType,
    name,
    x: off.x,
    y: off.y,
    w: off.w,
    h: off.h,
    rotation: rotation / 60000, // 60000ths of a degree → degrees
    fill,
    stroke,
    strokeWidth,
    textBody,
  };
}

/** Parse <p:pic> block into PptxImage. */
function parsePicture(
  xml: string,
  slideId: string,
  rels: Map<string, string>,
  files: Record<string, Uint8Array>,
): PptxImage | null {
  const off = extractOffsetExtent(xml);
  if (!off) return null;

  // Extract rId from blipFill
  const rId = extractAttr(xml, "a:blip", "r:embed") ?? "";
  const relTarget = rels.get(rId) ?? "";
  const mediaPath = relTarget.startsWith("../")
    ? `ppt/${relTarget.slice(3)}`
    : `ppt/slides/${relTarget}`;

  const blob = files[mediaPath] ?? null;
  const mime = guessMime(mediaPath);

  return {
    id: nextId("img"),
    slideId,
    x: off.x,
    y: off.y,
    w: off.w,
    h: off.h,
    blob,
    mime,
    rId,
  };
}

/** Parse <p:txBody> into PptxTextBody. */
function parseTextBody(xml: string): PptxTextBody | null {
  const txBody = extractBlock(xml, "p:txBody");
  if (!txBody) return null;

  const align = (extractAttr(txBody, "a:pPr", "algn") ?? "l") as string;
  const alignMap: Record<string, PptxTextBody["align"]> = {
    l: "left", ctr: "center", r: "right", just: "justify",
  };

  const paragraphs: PptxParagraph[] = [];
  const paraBlocks = extractBlocks(txBody, "a:p");

  for (const paraXml of paraBlocks) {
    const level = parseInt(extractAttr(paraXml, "a:pPr", "lvl") ?? "0", 10);
    const runs: PptxRun[] = [];

    const runBlocks = extractBlocks(paraXml, "a:r");
    for (const runXml of runBlocks) {
      const text = extractInnerText(runXml, "a:t");
      if (!text) continue;

      const bold = extractAttr(runXml, "a:rPr", "b") === "1";
      const italic = extractAttr(runXml, "a:rPr", "i") === "1";
      const underline = extractAttr(runXml, "a:rPr", "u") === "sng";
      const size = parseInt(extractAttr(runXml, "a:rPr", "sz") ?? "1800", 10);
      const color = extractRunColor(runXml) ?? "000000";
      const font = extractAttrDeep(runXml, "a:latin", "typeface") ?? "Calibri";

      runs.push({ text, bold, italic, underline, size, color, font });
    }

    if (runs.length > 0) {
      paragraphs.push({ level, spacing: 0, runs });
    }
  }

  if (paragraphs.length === 0) return null;

  return {
    align: alignMap[align] ?? "left",
    verticalAlign: "top",
    paragraphs,
  };
}

/** Parse theme colors from ppt/theme/theme1.xml. */
function parseTheme(files: Record<string, Uint8Array>): PptxTheme | null {
  const xml = getFileText(files, "ppt/theme/theme1.xml");
  if (!xml) return null;

  const name = extractAttr(xml, "a:theme", "name") ?? "Default";
  const colors: Record<string, string> = {};

  const colorNames = ["dk1", "dk2", "lt1", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];
  for (const cn of colorNames) {
    const block = extractBlock(xml, `a:${cn}`);
    if (!block) continue;
    const val = extractAttr(block, "a:srgbClr", "val") ?? extractAttr(block, "a:sysClr", "lastClr");
    if (val) colors[cn] = val;
  }

  return { name, colors };
}

// ---------------------------------------------------------------------------
// XML extraction helpers (lightweight, no DOM parser needed)
// ---------------------------------------------------------------------------

/** Extract a single attribute value from a tag. */
function extractAttr(xml: string, tag: string, attr: string): string | null {
  const simpleName = tag.includes("/") ? tag.split("/").pop()! : tag;
  const regex = new RegExp(`<${simpleName}[^>]*\\s${attr}="([^"]*)"`, "i");
  const m = xml.match(regex);
  return m ? m[1] : null;
}

function extractAttrSimple(xml: string, tag: string, attr: string): string | null {
  return extractAttr(xml, tag, attr);
}

function extractAttrDeep(xml: string, tag: string, attr: string): string | null {
  return extractAttr(xml, tag, attr);
}

/** Extract inner text of a tag: <tag>text</tag>. */
function extractInnerText(xml: string, tag: string): string | null {
  const regex = new RegExp(`<${tag}[^>]*>([^<]*)</${tag}>`, "i");
  const m = xml.match(regex);
  return m ? m[1] : null;
}

/** Extract a block: <tag ...>...</tag> (greedy for first occurrence). */
function extractBlock(xml: string, tag: string): string | null {
  const openIdx = xml.indexOf(`<${tag}`);
  if (openIdx === -1) return null;

  const closeTag = `</${tag}>`;
  const closeIdx = xml.indexOf(closeTag, openIdx);
  if (closeIdx === -1) return null;

  return xml.slice(openIdx, closeIdx + closeTag.length);
}

/** Extract all blocks for a tag (non-nested). */
function extractBlocks(xml: string, tag: string): string[] {
  const blocks: string[] = [];
  const openTag = `<${tag}`;
  const closeTag = `</${tag}>`;
  let searchFrom = 0;

  while (true) {
    const openIdx = xml.indexOf(openTag, searchFrom);
    if (openIdx === -1) break;

    // Handle self-closing tags
    const nextClose = xml.indexOf(">", openIdx);
    if (nextClose === -1) break;

    if (xml[nextClose - 1] === "/") {
      blocks.push(xml.slice(openIdx, nextClose + 1));
      searchFrom = nextClose + 1;
      continue;
    }

    // Find matching close, handling nesting
    let depth = 1;
    let pos = nextClose + 1;
    while (depth > 0 && pos < xml.length) {
      const nextOpen = xml.indexOf(openTag, pos);
      const nextEnd = xml.indexOf(closeTag, pos);

      if (nextEnd === -1) break;

      if (nextOpen !== -1 && nextOpen < nextEnd) {
        // Check if self-closing
        const gt = xml.indexOf(">", nextOpen);
        if (gt !== -1 && xml[gt - 1] === "/") {
          pos = gt + 1;
        } else {
          depth++;
          pos = nextOpen + openTag.length;
        }
      } else {
        depth--;
        if (depth === 0) {
          blocks.push(xml.slice(openIdx, nextEnd + closeTag.length));
        }
        pos = nextEnd + closeTag.length;
      }
    }

    searchFrom = pos;
  }

  return blocks;
}

/** Extract offset + extent from <a:off x="" y=""/> <a:ext cx="" cy=""/>. */
function extractOffsetExtent(xml: string): { x: Emu; y: Emu; w: Emu; h: Emu } | null {
  const x = extractAttr(xml, "a:off", "x");
  const y = extractAttr(xml, "a:off", "y");
  const cx = extractAttr(xml, "a:ext", "cx");
  const cy = extractAttr(xml, "a:ext", "cy");

  if (!x || !y || !cx || !cy) return null;

  return {
    x: parseInt(x, 10),
    y: parseInt(y, 10),
    w: parseInt(cx, 10),
    h: parseInt(cy, 10),
  };
}

/** Extract solid fill color from <a:solidFill><a:srgbClr val="RRGGBB"/></a:solidFill>. */
function extractSolidFill(xml: string): string | null {
  const block = extractBlock(xml, "a:solidFill");
  if (!block) return null;
  return extractAttr(block, "a:srgbClr", "val");
}

/** Extract line color. */
function extractLineColor(xml: string): string | null {
  const ln = extractBlock(xml, "a:ln");
  if (!ln) return null;
  return extractSolidFill(ln);
}

/** Extract run text color from <a:rPr>...<a:solidFill><a:srgbClr val="..."/>. */
function extractRunColor(xml: string): string | null {
  const rPr = extractBlock(xml, "a:rPr");
  if (!rPr) return null;
  return extractSolidFill(rPr);
}

/** Extract background color. */
function extractBgColor(xml: string): string | null {
  const bg = extractBlock(xml, "p:bg");
  if (!bg) return null;
  return extractSolidFill(bg);
}

/** Map OOXML preset geometry name to our shape type. */
function mapPresetGeometry(prst: string): PptxShape["type"] {
  const map: Record<string, PptxShape["type"]> = {
    rect: "rect",
    ellipse: "ellipse",
    roundRect: "roundRect",
    triangle: "triangle",
    rightArrow: "arrow",
    leftArrow: "arrow",
    upArrow: "arrow",
    downArrow: "arrow",
    line: "line",
    straightConnector1: "line",
    bentConnector2: "line",
    bentConnector3: "line",
    curvedConnector3: "line",
  };
  return map[prst] ?? "rect";
}

/** Guess MIME type from file extension. */
function guessMime(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() ?? "";
  const mimes: Record<string, string> = {
    png: "image/png",
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    gif: "image/gif",
    svg: "image/svg+xml",
    webp: "image/webp",
    emf: "image/x-emf",
    wmf: "image/x-wmf",
    tiff: "image/tiff",
    tif: "image/tiff",
  };
  return mimes[ext] ?? "application/octet-stream";
}
