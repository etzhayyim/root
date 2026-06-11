/**
 * PPTX Exporter — rebuild OOXML DrawingML XML from slide graph, ZIP, and download.
 *
 * Generates a valid .pptx (Office Open XML) from the in-memory PptxPresentation.
 * Uses fflate for ZIP compression.
 */

import { zipSync, strToU8 } from "fflate";
import type {
  PptxPresentation,
  PptxSlide,
  PptxShape,
  PptxImage,
  PptxTextBody,
  PptxParagraph,
  PptxRun,
  PptxTheme,
} from "./ooxml-parser";

/** Export a PptxPresentation to a .pptx Blob for download. */
export function exportPptx(pres: PptxPresentation): Blob {
  const files: Record<string, Uint8Array> = {};

  files["[Content_Types].xml"] = strToU8(buildContentTypes(pres));
  files["_rels/.rels"] = strToU8(buildRootRels());
  files["ppt/presentation.xml"] = strToU8(buildPresentationXml(pres));
  files["ppt/_rels/presentation.xml.rels"] = strToU8(buildPresentationRels(pres));

  // Theme is always required (slideMaster references it)
  files["ppt/theme/theme1.xml"] = strToU8(
    pres.theme ? buildThemeXml(pres.theme) : buildDefaultThemeXml(),
  );

  // docProps required by Keynote and some readers
  files["docProps/app.xml"] = strToU8(buildAppXml());
  files["docProps/core.xml"] = strToU8(buildCoreXml(pres.title));

  // Slide layouts + masters (minimal stubs for valid PPTX)
  files["ppt/slideLayouts/slideLayout1.xml"] = strToU8(buildSlideLayout());
  files["ppt/slideLayouts/_rels/slideLayout1.xml.rels"] = strToU8(buildSlideLayoutRels());
  files["ppt/slideMasters/slideMaster1.xml"] = strToU8(buildSlideMaster());
  files["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = strToU8(buildSlideMasterRels());

  let mediaIdx = 0;
  for (let i = 0; i < pres.slides.length; i++) {
    const slide = pres.slides[i];
    const slideNum = i + 1;
    const imageRefs: { rId: string; mediaFile: string }[] = [];

    // Collect images and write media files
    for (const img of slide.images) {
      mediaIdx++;
      const ext = img.mime.split("/")[1] ?? "png";
      const mediaFile = `image${mediaIdx}.${ext}`;
      if (img.blob) {
        files[`ppt/media/${mediaFile}`] = img.blob;
      }
      imageRefs.push({ rId: `rId${100 + mediaIdx}`, mediaFile });
    }

    files[`ppt/slides/slide${slideNum}.xml`] = strToU8(
      buildSlideXml(slide, pres, imageRefs),
    );
    files[`ppt/slides/_rels/slide${slideNum}.xml.rels`] = strToU8(
      buildSlideRels(imageRefs),
    );
  }

  const zipped = zipSync(files, { level: 6 });
  // Use slice to get exact bytes (buffer may be larger than the actual data)
  const exactBuffer = zipped.buffer.slice(zipped.byteOffset, zipped.byteOffset + zipped.byteLength);
  return new Blob([exactBuffer], { type: "application/vnd.openxmlformats-officedocument.presentationml.presentation" });
}

/** Trigger browser download of a Blob. */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// XML Builders
// ---------------------------------------------------------------------------

function xmlHeader(): string {
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`;
}

function buildContentTypes(pres: PptxPresentation): string {
  let slides = "";
  for (let i = 0; i < pres.slides.length; i++) {
    slides += `<Override PartName="/ppt/slides/slide${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>`;
  }
  return `${xmlHeader()}
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="jpeg" ContentType="image/jpeg"/>
  <Default Extension="jpg" ContentType="image/jpeg"/>
  <Default Extension="gif" ContentType="image/gif"/>
  <Default Extension="webp" ContentType="image/webp"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  ${slides}
</Types>`;
}

function buildRootRels(): string {
  return `${xmlHeader()}
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>`;
}

function buildPresentationXml(pres: PptxPresentation): string {
  let slideList = "";
  for (let i = 0; i < pres.slides.length; i++) {
    slideList += `<p:sldId id="${256 + i}" r:id="rId${i + 2}"/>`;
  }

  return `${xmlHeader()}
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
  saveSubsetFonts="1">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>${slideList}</p:sldIdLst>
  <p:sldSz cx="${pres.width}" cy="${pres.height}" type="custom"/>
  <p:notesSz cx="${pres.height}" cy="${pres.width}"/>
</p:presentation>`;
}

function buildPresentationRels(pres: PptxPresentation): string {
  let rels = `<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>`;

  for (let i = 0; i < pres.slides.length; i++) {
    rels += `<Relationship Id="rId${i + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide${i + 1}.xml"/>`;
  }

  const themeId = pres.slides.length + 2;
  rels += `<Relationship Id="rId${themeId}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>`;

  return `${xmlHeader()}
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  ${rels}
</Relationships>`;
}

function buildSlideXml(
  slide: PptxSlide,
  pres: PptxPresentation,
  imageRefs: { rId: string; mediaFile: string }[],
): string {
  let spTree = "";

  for (let si = 0; si < slide.shapes.length; si++) {
    spTree += buildShapeXml(slide.shapes[si], si + 2);
  }

  for (let i = 0; i < slide.images.length; i++) {
    const img = slide.images[i];
    const ref = imageRefs[i];
    if (ref) {
      spTree += buildPictureXml(img, ref.rId, slide.shapes.length + 2 + i);
    }
  }

  const bgXml = slide.background
    ? `<p:bg><p:bgPr><a:solidFill><a:srgbClr val="${escXml(slide.background)}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>`
    : "";

  return `${xmlHeader()}
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>${bgXml}<p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr/>
    ${spTree}
  </p:spTree></p:cSld>
</p:sld>`;
}

function buildShapeXml(shape: PptxShape, shapeId: number): string {
  const prst = reverseMapGeometry(shape.type);
  const rot = Math.round(shape.rotation * 60000);
  const fillXml = shape.fill
    ? `<a:solidFill><a:srgbClr val="${escXml(shape.fill)}"/></a:solidFill>`
    : `<a:noFill/>`;
  const lnXml = shape.stroke
    ? `<a:ln w="${shape.strokeWidth || 12700}"><a:solidFill><a:srgbClr val="${escXml(shape.stroke)}"/></a:solidFill></a:ln>`
    : `<a:ln><a:noFill/></a:ln>`;
  const txBody = shape.textBody ? buildTextBodyXml(shape.textBody) : `<p:txBody><a:bodyPr rtlCol="0"/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody>`;

  return `<p:sp>
  <p:nvSpPr><p:cNvPr id="${shapeId}" name="${escXml(shape.name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm rot="${rot}"><a:off x="${shape.x}" y="${shape.y}"/><a:ext cx="${shape.w}" cy="${shape.h}"/></a:xfrm>
    <a:prstGeom prst="${prst}"><a:avLst/></a:prstGeom>
    ${fillXml}${lnXml}
  </p:spPr>
  ${txBody}
</p:sp>`;
}

function buildTextBodyXml(tb: PptxTextBody): string {
  const alignMap: Record<string, string> = { left: "l", center: "ctr", right: "r", justify: "just" };
  const anchor = tb.verticalAlign === "middle" ? "ctr" : tb.verticalAlign === "bottom" ? "b" : "t";
  let paras = "";

  for (const p of tb.paragraphs) {
    let runs = "";
    for (const r of p.runs) {
      const bAttr = r.bold ? ` b="1"` : "";
      const iAttr = r.italic ? ` i="1"` : "";
      const uAttr = r.underline ? ` u="sng"` : "";
      runs += `<a:r><a:rPr lang="en-US" sz="${r.size}" dirty="0"${bAttr}${iAttr}${uAttr}><a:solidFill><a:srgbClr val="${escXml(r.color)}"/></a:solidFill><a:latin typeface="${escXml(r.font)}"/></a:rPr><a:t>${escXml(r.text)}</a:t></a:r>`;
    }
    paras += `<a:p><a:pPr algn="${alignMap[tb.align] ?? "l"}" lvl="${p.level}"/>${runs}</a:p>`;
  }

  return `<p:txBody><a:bodyPr rtlCol="0" anchor="${anchor}"/><a:lstStyle/>${paras}</p:txBody>`;
}

function buildPictureXml(img: PptxImage, rId: string, picId: number): string {
  return `<p:pic>
  <p:nvPicPr><p:cNvPr id="${picId}" name="Image"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
  <p:blipFill><a:blip r:embed="${rId}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
  <p:spPr><a:xfrm><a:off x="${img.x}" y="${img.y}"/><a:ext cx="${img.w}" cy="${img.h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
</p:pic>`;
}

function buildSlideRels(imageRefs: { rId: string; mediaFile: string }[]): string {
  let rels = `<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>`;
  for (const ref of imageRefs) {
    rels += `<Relationship Id="${ref.rId}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/${ref.mediaFile}"/>`;
  }
  return `${xmlHeader()}
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  ${rels}
</Relationships>`;
}

function buildThemeXml(theme: PptxTheme): string {
  const colorEntries = Object.entries(theme.colors);
  let scheme = "";
  for (const [name, val] of colorEntries) {
    scheme += `<a:${name}><a:srgbClr val="${escXml(val)}"/></a:${name}>`;
  }

  return `${xmlHeader()}
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="${escXml(theme.name)}">
  <a:themeElements>
    <a:clrScheme name="Custom">${scheme}</a:clrScheme>
    <a:fontScheme name="Custom"><a:majorFont><a:latin typeface="Calibri"/></a:majorFont><a:minorFont><a:latin typeface="Calibri"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Custom"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>`;
}

function buildSlideLayout(): string {
  return `${xmlHeader()}
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
</p:sldLayout>`;
}

function buildSlideLayoutRels(): string {
  return `${xmlHeader()}
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>`;
}

function buildSlideMaster(): string {
  return `${xmlHeader()}
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
</p:sldMaster>`;
}

function buildSlideMasterRels(): string {
  return `${xmlHeader()}
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>`;
}

/** Default theme XML when no theme is loaded from a parsed PPTX. */
function buildDefaultThemeXml(): string {
  return `${xmlHeader()}
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="44546A"/></a:dk2>
      <a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
      <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
      <a:accent2><a:srgbClr val="ED7D31"/></a:accent2>
      <a:accent3><a:srgbClr val="A5A5A5"/></a:accent3>
      <a:accent4><a:srgbClr val="FFC000"/></a:accent4>
      <a:accent5><a:srgbClr val="5B9BD5"/></a:accent5>
      <a:accent6><a:srgbClr val="70AD47"/></a:accent6>
      <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
      <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont><a:latin typeface="Calibri Light"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
      <a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/>
  <a:extraClrSchemeLst/>
</a:theme>`;
}

/** App properties (required by Keynote). */
function buildAppXml(): string {
  return `${xmlHeader()}
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>pptx.etzhayyim.com</Application>
  <Slides>1</Slides>
  <ScaleCrop>false</ScaleCrop>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
</Properties>`;
}

/** Core properties (required by Keynote). */
function buildCoreXml(title: string): string {
  const now = new Date().toISOString();
  return `${xmlHeader()}
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>${escXml(title)}</dc:title>
  <dc:creator>pptx.etzhayyim.com</dc:creator>
  <dcterms:created xsi:type="dcterms:W3CDTF">${now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">${now}</dcterms:modified>
</cp:coreProperties>`;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function reverseMapGeometry(type: PptxShape["type"]): string {
  const map: Record<string, string> = {
    rect: "rect",
    ellipse: "ellipse",
    roundRect: "roundRect",
    triangle: "triangle",
    arrow: "rightArrow",
    line: "line",
    freeform: "rect",
    textBox: "rect",
  };
  return map[type] ?? "rect";
}

function escXml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}
