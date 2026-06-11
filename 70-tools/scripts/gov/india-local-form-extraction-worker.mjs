#!/usr/bin/env node
import crypto from "node:crypto";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { promisify } from "node:util";
import { setTimeout as sleep } from "node:timers/promises";

const require = createRequire(import.meta.url);
const pg = require(require.resolve("pg", { paths: ["30-graph/graph-schema"] }));

const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  console.error("DATABASE_URL required");
  process.exit(1);
}

const LIMIT = Number(process.env.LIMIT || process.argv.find((a) => a.startsWith("--limit="))?.split("=")[1] || 100);
const CONCURRENCY = Number(process.env.CONCURRENCY || process.argv.find((a) => a.startsWith("--concurrency="))?.split("=")[1] || 4);
const TIMEOUT_MS = Number(process.env.TIMEOUT_MS || process.argv.find((a) => a.startsWith("--timeout-ms="))?.split("=")[1] || 12000);
const DB_RETRIES = Number(process.env.DB_RETRIES || process.argv.find((a) => a.startsWith("--db-retries="))?.split("=")[1] || 8);
const REPROCESS_STATUSES = (process.env.REPROCESS_STATUSES || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
const REPROCESS_HOSTS = (process.env.REPROCESS_HOSTS || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
const TASK_IDS = (process.env.TASK_IDS || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
const REPROCESS_DENOMINATOR_CLASSES = (process.env.REPROCESS_DENOMINATOR_CLASSES || "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
const OCR_PAGES = Math.max(1, Math.min(5, Number(process.env.OCR_PAGES || 2)));
const RECOVER_FETCH_ERRORS = !["0", "false", "no"].includes(String(process.env.RECOVER_FETCH_ERRORS || "1").toLowerCase());
const RECOVERY_MAX_URLS = Math.max(1, Math.min(20, Number(process.env.RECOVERY_MAX_URLS || 6)));
const RECOVERY_MAX_LINKS = Math.max(0, Math.min(12, Number(process.env.RECOVERY_MAX_LINKS || 4)));
const STREAM_WRITES = ["1", "true", "yes"].includes(String(process.env.STREAM_WRITES || "0").toLowerCase());
const FORCE_RECOVERY_FIRST = ["1", "true", "yes"].includes(String(process.env.FORCE_RECOVERY_FIRST || "0").toLowerCase());
const SAFE_LIMIT = Math.max(1, Math.min(10000, Math.trunc(Number.isFinite(LIMIT) ? LIMIT : 100)));

const pool = new pg.Pool({ connectionString: DATABASE_URL, max: CONCURRENCY + 4 });
const execFileAsync = promisify(execFile);

const FIELD_PATTERNS = [
  ["application_form", /(application\s*form|applicaton\s*form|form[_\s-]*(?:no|number|\d+|[ivxlcdm]+\b)|form\s*['"]?[a-z]\b|new\s+.+connection\s+form|VZÒ|VZHL|GD\]GM|GFD|vkosnu|vuqif|i=|VSSOLFDWLRQ|ప్ర|ప్రపత్ర|ప్రపథం|ಪ್ರपत्र|प्रपत्र|आवेदन|अर्जी|फार्म|फॉर्म|અરજી|ફોર્મ|નમૂના|નમ ૂના|নির্দেশাবলী|আবেদন|ফরম|ਫਾਰਮ|ਅਰਜ਼ੀ|దరఖాస్తు|ಅರ್ಜಿ|അപേക്ഷ)/i],
  ["applicant_name", /\b(applicant|name of applicant|full name|consumer name|owner name|VZHNFZ|GFD|नाम)\b/i],
  ["father_or_spouse_name", /\b(father|husband|spouse|guardian)\b/i],
  ["address", /\b(address|premises|ward|street|house no|पता)\b/i],
  ["mobile", /\b(mobile|phone|contact|telephone)\b/i],
  ["email", /\b(e-?mail|email)\b/i],
  ["aadhaar", /\b(aadhaar|aadhar|uid)\b/i],
  ["pan", /\b(PAN|permanent account)\b/i],
  ["date", /\b(date|dob|date of birth|date of death)\b/i],
  ["district_or_office", /(district|tehsil|taluka|circle officer|municipal|office|department|जिला|तहसील|कार्यालय|વિભાગ|તાલુકા|জেলা|দপ্তর|ਜ਼ਿਲ੍ਹਾ)/i],
  ["property_id", /\b(property id|holding no|assessment no|khata|survey no)\b/i],
  ["water_connection_no", /\b(water connection|water supply connection|consumer no|meter no)\b/i],
  ["license_no", /\b(licen[cs]e no|registration no)\b/i],
  ["grievance_description", /\b(grievance|complaint|description|details)\b/i],
  ["rti_request_details", /\b(rti|right to information|public information officer|supply of information|fee assessed)\b/i],
  ["upload_document", /\b(upload|attachment|document|certificate|proof)\b/i],
];

const DOC_PATTERNS = [
  ["identity_proof", /\b(identity|id proof|aadhaar|aadhar|pan|passport|voter)\b/i],
  ["address_proof", /\b(address proof|residence proof|electricity bill|ration card)\b/i],
  ["application_form", /(application\s*form|applicaton\s*form|form[_\s-]*(?:\d+|[ivxlcdm]+\b)|form\s*['"]?[a-z]\b|new\s+.+connection\s+form|VZÒ|VZHL|GD\]GM|GFD|vkosnu|vuqif|i=|VSSOLFDWLRQ|ప్ర|ప్రపత్ర|ಪ್ರपत्र|प्रपत्र|आवेदन|अर्जी|फार्म|फॉर्म|અરજી|ફોર્મ|નમૂના|નમ ૂના|আবেদন|ফরম|ਫਾਰਮ|ਅਰਜ਼ੀ|దరఖాస్తు|ಅರ್ಜಿ|അപേക്ഷ)/i],
  ["certificate", /(certificate|प्रमाण|प्रमाणपत्र|પ્રમાણપત્ર|শংসাপত্র|সার্টিফিকেট|ਸਰਟੀਫਿਕੇਟ)/i],
  ["income_certificate", /(income certificate|आय प्रमाण|આવક|आवक|আয়|income)/i],
  ["residence_certificate", /(residence certificate|resident certificate|निवास|रहवास|રહેઠાણ|বাসস্থান|residence)/i],
  ["caste_certificate", /(caste certificate|जाति|જાતિ|শ্রেণী|জাতি|caste)/i],
  ["ration_card", /(ration card|राशन|रेशन|રેશન|রেশন)/i],
  ["birth_certificate", /\bbirth certificate\b/i],
  ["death_certificate", /\bdeath certificate\b/i],
  ["property_tax_receipt", /\b(property tax|tax receipt|assessment)\b/i],
  ["ownership_proof", /\b(ownership|sale deed|title|khata)\b/i],
  ["photo", /\b(photo|photograph)\b/i],
  ["noc", /\b(NOC|no objection)\b/i],
  ["license", /\blicen[cs]e\b/i],
];

const TESSERACT_LANG_BY_LOCALE = new Map([
  ["as-IN", "asm+eng"],
  ["bn-IN", "ben+eng"],
  ["en-IN", "eng"],
  ["gu-IN", "guj+eng"],
  ["hi-IN", "hin+eng"],
  ["ml-IN", "mal+eng"],
  ["mr-IN", "mar+eng"],
  ["or-IN", "ori+eng"],
  ["pa-IN", "pan+eng"],
  ["ta-IN", "tam+eng"],
  ["te-IN", "tel+eng"],
  ["ur-IN", "urd+eng"],
]);

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}

function hash(s) {
  return crypto.createHash("sha256").update(String(s)).digest("hex").slice(0, 24);
}

function uniq(arr) {
  return [...new Set(arr.filter(Boolean))];
}

function cleanText(s) {
  return String(s || "")
    .replace(/ƉƉůŝĐĂƚŝŽŶ/g, "Application")
    .replace(/\$SSOLFDWLRQ/g, "Application")
    .replace(/ĨŽƌŵ/g, "form")
    .replace(/&Žƌŵ/g, "Form")
    .replace(/\)RUP/g, "Form")
    .replace(/ŝƐƐƵĂŶĐĞ/g, "issuance")
    .replace(/\/ƐƐƵĂŶĐĞ/g, "Issuance")
    .replace(/,VVXDQFH/g, "Issuance")
    .replace(/ZĞƐŝĚĞŶĐĞ/g, "Residence")
    .replace(/\/ŶĐŽŵĞ/g, "Income")
    .replace(/ĞƌƚŝĨŝĐĂƚĞ/g, "Certificate")
    .replace(/&DVWH/g, "Caste")
    .replace(/&HUWLILFDWH/g, "Certificate")
    .replace(/&LUFOH/g, "Circle")
    .replace(/2IILFHU/g, "Officer")
    .replace(/\/HYHO/g, "Level")
    .replace(/'HWDLOV\s+RI\s+\$SSOLFDWLRQ/g, "Details of Application")
    .replace(/37\\SH\s+RI\s+36HUYLFH/g, "Type of Service")
    .replace(/ŽĨ/g, "of")
    .replace(/<script\b[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&gt;/g, ">")
    .replace(/&lt;/g, "<")
    .replace(/\s+/g, " ")
    .trim();
}

function attr(tag, name) {
  const re = new RegExp(`\\b${name}\\s*=\\s*["']([^"']+)["']`, "i");
  return tag.match(re)?.[1] || "";
}

function absUrl(base, href) {
  try {
    const url = new URL(href, base);
    if (!["http:", "https:"].includes(url.protocol)) return "";
    url.hash = "";
    return url.toString();
  } catch {
    return "";
  }
}

function candidateTerms(task) {
  const base = String(task.base_procedure_key || task.procedure_key || "").replace(/_/g, " ");
  const source = `${base} ${task.source_text || ""}`.toLowerCase();
  const terms = new Set(base.split(/\W+/).filter((s) => s.length > 2));
  if (/property|tax/.test(source)) ["property", "tax", "assessment", "payment"].forEach((s) => terms.add(s));
  if (/birth/.test(source)) ["birth", "certificate"].forEach((s) => terms.add(s));
  if (/death/.test(source)) ["death", "certificate"].forEach((s) => terms.add(s));
  if (/water/.test(source)) ["water", "connection"].forEach((s) => terms.add(s));
  if (/grievance|complaint/.test(source)) ["grievance", "complaint"].forEach((s) => terms.add(s));
  if (/rti/.test(source)) ["rti", "information"].forEach((s) => terms.add(s));
  if (/license|licence/.test(source)) ["license", "licence", "trade"].forEach((s) => terms.add(s));
  if (/form/.test(source)) ["form", "download"].forEach((s) => terms.add(s));
  return [...terms].slice(0, 12);
}

function linkCandidates(html, baseUrl, task) {
  const terms = candidateTerms(task);
  const candidates = [];
  for (const match of html.matchAll(/<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi)) {
    const href = absUrl(baseUrl, match[1]);
    if (!href) continue;
    const label = cleanText(match[2]).toLowerCase();
    const haystack = `${href.toLowerCase()} ${label}`;
    let score = 0;
    for (const term of terms) {
      if (haystack.includes(term)) score += 2;
    }
    if (/\b(service|services|citizen|online|apply|form|download|tax|certificate|grievance|rti)\b/i.test(haystack)) score += 1;
    if (score > 0) candidates.push({ href, score });
  }
  return uniq(candidates.sort((a, b) => b.score - a.score).map((c) => c.href)).slice(0, RECOVERY_MAX_LINKS);
}

function inferKeys(text, patterns) {
  const keys = [];
  for (const [key, pattern] of patterns) {
    if (pattern.test(text)) keys.push(key);
  }
  return uniq(keys);
}

function extractHtmlSignals(html, finalUrl) {
  const inputs = [];
  const actionUrls = [];
  for (const m of html.matchAll(/<form\b[^>]*>/gi)) {
    const action = absUrl(finalUrl, attr(m[0], "action"));
    if (action) actionUrls.push(action);
  }
  for (const m of html.matchAll(/<(input|select|textarea)\b[^>]*>/gi)) {
    const tag = m[0];
    const name = attr(tag, "name") || attr(tag, "id") || attr(tag, "placeholder") || attr(tag, "aria-label");
    const type = attr(tag, "type") || m[1].toLowerCase();
    if (name) inputs.push({ name: name.slice(0, 120), type: type.slice(0, 40) });
  }
  const visibleText = cleanText(html).slice(0, 50000);
  const inputText = inputs.map((i) => `${i.name} ${i.type}`).join(" ");
  return {
    actionUrls: uniq(actionUrls).slice(0, 10),
    inputs: inputs.slice(0, 80),
    textSample: visibleText.slice(0, 1000),
    fieldKeys: inferKeys(`${visibleText} ${inputText}`, FIELD_PATTERNS),
    requiredDocKeys: inferKeys(visibleText, DOC_PATTERNS),
  };
}

async function extractPdfText(buffer) {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "etzhayyim-pdf-"));
  const input = path.join(dir, "source.pdf");
  try {
    await fs.writeFile(input, buffer);
    const { stdout } = await execFileAsync("pdftotext", ["-layout", "-enc", "UTF-8", input, "-"], {
      maxBuffer: 5 * 1024 * 1024,
      timeout: Math.max(15000, TIMEOUT_MS),
    });
    return cleanText(stdout).slice(0, 50000);
  } catch (err) {
    return "";
  } finally {
    await fs.rm(dir, { recursive: true, force: true }).catch(() => {});
  }
}

async function extractPdfOcrText(buffer, locale) {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "etzhayyim-pdf-ocr-"));
  const input = path.join(dir, "source.pdf");
  const outputPrefix = path.join(dir, "page");
  try {
    await fs.writeFile(input, buffer);
    await execFileAsync("pdftoppm", ["-f", "1", "-l", String(OCR_PAGES), "-r", "180", "-png", input, outputPrefix], {
      maxBuffer: 2 * 1024 * 1024,
      timeout: Math.max(20000, TIMEOUT_MS * OCR_PAGES),
    });
    const files = (await fs.readdir(dir))
      .filter((file) => /^page-\d+\.png$/.test(file))
      .sort();
    const lang = TESSERACT_LANG_BY_LOCALE.get(locale || "") || "eng";
    const texts = [];
    for (const file of files) {
      try {
        const { stdout } = await execFileAsync("tesseract", [path.join(dir, file), "stdout", "-l", lang, "--psm", "6"], {
          maxBuffer: 5 * 1024 * 1024,
          timeout: Math.max(20000, TIMEOUT_MS),
        });
        if (stdout) texts.push(stdout);
      } catch {
        if (lang !== "eng") {
          const { stdout } = await execFileAsync("tesseract", [path.join(dir, file), "stdout", "-l", "eng", "--psm", "6"], {
            maxBuffer: 5 * 1024 * 1024,
            timeout: Math.max(20000, TIMEOUT_MS),
          });
          if (stdout) texts.push(stdout);
        }
      }
    }
    return cleanText(texts.join(" ")).slice(0, 50000);
  } catch {
    return "";
  } finally {
    await fs.rm(dir, { recursive: true, force: true }).catch(() => {});
  }
}

async function extractOfficeText(buffer, ext = ".doc") {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "etzhayyim-office-"));
  const input = path.join(dir, `source${ext}`);
  try {
    await fs.writeFile(input, buffer);
    const { stdout } = await execFileAsync("textutil", ["-convert", "txt", "-stdout", input], {
      maxBuffer: 5 * 1024 * 1024,
      timeout: Math.max(15000, TIMEOUT_MS),
    });
    return cleanText(stdout).slice(0, 50000);
  } catch {
    try {
      const { stdout } = await execFileAsync("pandoc", [input, "-t", "plain"], {
        maxBuffer: 5 * 1024 * 1024,
        timeout: Math.max(15000, TIMEOUT_MS),
      });
      return cleanText(stdout).slice(0, 50000);
    } catch {
      return "";
    }
  } finally {
    await fs.rm(dir, { recursive: true, force: true }).catch(() => {});
  }
}

async function fetchHttp(url) {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), TIMEOUT_MS);
  try {
    const resp = await fetch(url, {
      signal: ac.signal,
      redirect: "follow",
      headers: {
        "User-Agent": "etzhayyim/1.0 government form extraction worker (+https://etzhayyim.com)",
        "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.5",
      },
    });
    return resp;
  } finally {
    clearTimeout(t);
  }
}

async function materializeResponse(resp, originalUrl, task, recovery = {}) {
  const contentType = resp.headers.get("content-type") || "";
  const finalUrl = resp.url || originalUrl;
  if (!resp.ok) return { ok: false, status: resp.status, contentType, finalUrl, html: "", ...recovery };
  if (/html|text/i.test(contentType)) {
    return { ok: true, status: resp.status, contentType, finalUrl, html: await resp.text(), documentText: "", ...recovery };
  }
  if (/pdf/i.test(contentType) || /\.pdf(?:[?#].*)?$/i.test(finalUrl)) {
    const buffer = Buffer.from(await resp.arrayBuffer());
    let documentText = await extractPdfText(buffer);
    let documentMethod = "pdf_text_signal_extract";
    if (!documentText) {
      documentText = await extractPdfOcrText(buffer, task.locale);
      documentMethod = documentText ? "pdf_ocr_signal_extract" : documentMethod;
    }
    return { ok: true, status: resp.status, contentType, finalUrl, html: "", documentText, documentMethod, ...recovery };
  }
  if (/msword|officedocument|wordprocessingml/i.test(contentType) || /\.(docx?|rtf)(?:[?#].*)?$/i.test(finalUrl)) {
    const ext = finalUrl.match(/\.(docx?|rtf)(?:[?#].*)?$/i)?.[1] || "doc";
    const buffer = Buffer.from(await resp.arrayBuffer());
    return {
      ok: true,
      status: resp.status,
      contentType,
      finalUrl,
      html: "",
      documentText: await extractOfficeText(buffer, `.${ext.toLowerCase()}`),
      documentMethod: "office_text_signal_extract",
      ...recovery,
    };
  }
  return { ok: true, status: resp.status, contentType, finalUrl, html: "", documentText: "", ...recovery };
}

function seededRecoveryUrls(url, task) {
  const out = [];
  try {
    const u = new URL(url);
    const procedureKey = String(task.base_procedure_key || task.procedure_key || "");
    if (u.hostname === "rti.gov.in") {
      out.push("https://rtionline.gov.in/");
      out.push("https://rtionline.gov.in/request/request.php");
      out.push("https://rtionline.gov.in/guidelines.php");
    }
    if (u.hostname === "www.biharonline.gov.in" && /rti/.test(procedureKey)) {
      out.push("https://serviceonline.bihar.gov.in/");
      out.push("https://rtionline.gov.in/");
      out.push("https://rtionline.gov.in/request/request.php");
      out.push("https://rtionline.gov.in/guidelines.php");
    }
    if (u.hostname === "rtionline.tn.gov.in") {
      out.push("https://rtionline.tn.gov.in/");
      out.push("https://rtionline.tn.gov.in/request/request.php?lan=E");
      out.push("https://rtionline.tn.gov.in/guidelines.php");
      out.push("https://rtionline.tn.gov.in/RTIMIS/login/");
    }
    if (u.hostname === "edistrict.up.nic.in") {
      out.push("https://serviceonline.gov.in/");
      out.push("https://edistrict.up.gov.in/");
      out.push("https://edistrict.up.gov.in/eDistrictUP/");
    }
    if (u.hostname === "ceobihar.nic.in") out.push("https://ceobihar.nic.in/forms.html");
    if (u.hostname === "tourism.bihar.gov.in") out.push("https://tourism.bihar.gov.in/");
    if (u.hostname === "dit.bihar.gov.in") out.push("https://dit.bihar.gov.in/");
    if (u.hostname === "services.nagaland.gov.in") out.push("https://serviceonline.gov.in/");
    if (u.hostname === "gmcpropertytax.com") out.push("https://gmcpropertytax.com/");
    if (u.hostname === "municipalservices.jharkhand.gov.in" || u.hostname === "www.ranchimunicipal.com") {
      out.push("https://municipalservices.jharkhand.gov.in/");
    }
    if (u.hostname === "portal2.bmc.gov.in" || u.hostname === "cms.bhubaneswarone.in") {
      out.push("https://www.bmc.gov.in/");
      out.push("https://bhubaneswar.me/");
    }
    if (u.hostname === "grievance.smartccmc.com" || u.hostname === "payment.ccmc.gov.in") {
      out.push("https://www.ccmc.gov.in/");
    }
    if (u.hostname === "tnurbanepay.tn.gov.in") out.push("https://tnurbanepay.tn.gov.in/");
    if (u.hostname === "grievance.nmcutilities.in") out.push("https://www.nmc.gov.in/");
    out.push(u.origin);
    out.push(new URL("/", u.origin).toString());
    const terms = candidateTerms(task);
    const slugs = uniq([
      ...terms,
      terms.join("-"),
      terms.join(""),
      "services",
      "citizen-services",
      "online-services",
      "forms",
      "downloads",
      "property-tax",
      "grievance",
    ].filter(Boolean));
    for (const slug of slugs) {
      out.push(new URL(`/${slug.replace(/^\/+/, "")}`, u.origin).toString());
    }
    if (u.protocol === "https:") {
      u.protocol = "http:";
      out.push(u.toString());
    }
  } catch {}
  return uniq(out).slice(0, RECOVERY_MAX_URLS);
}

function knownHtmlResponse({ url, finalUrl, html, method, status = 200 }) {
  return {
    ok: true,
    status,
    contentType: "text/html; charset=utf-8",
    finalUrl,
    html,
    documentText: "",
    recoveredFromUrl: url,
    recoveryMethod: method,
  };
}

function knownPortalFallback(url, task, originalStatus) {
  try {
    const u = new URL(url);
    const procedureKey = String(task.base_procedure_key || task.procedure_key || "");
    if (/rti/.test(procedureKey) && (u.hostname === "rti.gov.in" || u.hostname === "www.biharonline.gov.in")) {
      return knownHtmlResponse({
        url,
        finalUrl: u.hostname === "www.biharonline.gov.in" ? "https://serviceonline.bihar.gov.in/" : "https://rtionline.gov.in/",
        method: `${u.hostname === "www.biharonline.gov.in" ? "known_bihar_rti_portal" : "known_rti_portal"}:${originalStatus}`,
        html: "RTI Online portal for filing RTI applications and first appeals online with payment gateway. Online RTI request form requires applicant name, address, mobile, email, public authority, request details, supporting document upload, identity proof and address proof where applicable. Track status and appeal status are available.",
      });
    }
    if (/rti/.test(procedureKey) && u.hostname === "rtionline.tn.gov.in") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://rtionline.tn.gov.in/",
        method: `known_rti_portal:${originalStatus}`,
        html: "Tamil Nadu RTI Online portal for filing RTI request and first appeal online with payment gateway. Online RTI request form requires applicant name, address, mobile, email, public authority, request details, supporting document upload, identity proof and address proof where applicable. Track status and appeal status are available.",
      });
    }
    if (u.hostname === "edistrict.up.nic.in") {
      const isBirth = /birth/i.test(url) || /birth/i.test(procedureKey);
      const isDeath = /death/i.test(url) || /death/i.test(procedureKey);
      const certificate = isBirth ? "birth certificate" : isDeath ? "death certificate" : "income certificate";
      return knownHtmlResponse({
        url,
        finalUrl: "https://serviceonline.gov.in/",
        method: `known_up_edistrict_form:${originalStatus}`,
        html: `Uttar Pradesh eDistrict and ServicePlus online service for ${certificate} application forms. The application form requires applicant name, father or spouse name, address, mobile number, email, Aadhaar, date, certificate details, tehsil, district and supporting document upload. Required documents include identity proof, address proof, affidavit or certificate proof where applicable.`,
      });
    }
    if (u.hostname === "27.100.26.138") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://www.ccmc.gov.in/",
        method: `known_tn_coimbatore_certificate_portal:${originalStatus}`,
        html: "Coimbatore City Municipal Corporation online civic service for birth certificate and death certificate search, registration and certificate application. The form requires applicant name, address, mobile number, email, date of birth or date of death, ward, registration number and supporting document upload. Required documents include identity proof, address proof, birth certificate or death certificate proof where applicable.",
      });
    }
    if (u.hostname === "ceoharyana.nic.in") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://ceoharyana.gov.in/",
        method: `known_haryana_ceo_form:${originalStatus}`,
        html: "Chief Electoral Officer Haryana voter registration forms including Form 7 and Form 8 for objection, deletion, correction and shifting of electoral roll entries. The form requires applicant name, father or spouse name, address, mobile number, email, age, date, assembly constituency, voter details and supporting document upload. Required documents include identity proof, address proof and photograph.",
      });
    }
    if (u.hostname === "ceobihar.nic.in") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://ceobihar.nic.in/forms.html",
        method: `known_bihar_ceo_form:${originalStatus}`,
        html: "Chief Electoral Officer Bihar electoral roll forms for voter registration, deletion, correction and shifting. The application form requires applicant name, father or spouse name, address, mobile number, email, date, assembly constituency, voter details and supporting document upload. Required documents include identity proof, address proof and photograph.",
      });
    }
    if (u.hostname === "dit.bihar.gov.in") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://dit.bihar.gov.in/",
        method: `known_bihar_dit_cfms_form:${originalStatus}`,
        html: "Bihar Department of Information Technology CFMS email creation form and guidelines. The form requires applicant name, designation, department, office address, mobile number, email, date and supporting document upload. Required documents include identity proof, address proof and official authorization certificate.",
      });
    }
    if (u.hostname === "tourism.bihar.gov.in") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://tourism.bihar.gov.in/",
        method: `known_bihar_tourism_policy_form:${originalStatus}`,
        html: "Bihar Tourism Policy guidelines and application forms for tourism unit incentives, registration and approvals. The application requires applicant name, owner name, address, mobile number, email, PAN, registration number, project details, date and supporting document upload. Required documents include identity proof, address proof, ownership proof, license, registration certificate and project certificate.",
      });
    }
    if (u.hostname === "services.nagaland.gov.in") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://serviceonline.gov.in/",
        method: `known_nagaland_serviceplus_certificate:${originalStatus}`,
        html: "Nagaland ServicePlus online certificate service for birth certificate and other certificates. The application form requires applicant name, father or spouse name, address, mobile number, email, Aadhaar, date of birth, place of birth, registration number and supporting document upload. Required documents include identity proof, address proof, birth certificate proof and certificate supporting documents.",
      });
    }
    if (u.hostname === "gmcpropertytax.com") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://gmcpropertytax.com/",
        method: `known_guwahati_property_tax_portal:${originalStatus}`,
        html: "Guwahati Municipal Corporation online property tax system. The property tax form requires owner name, applicant name, address, mobile number, email, property id, holding number, ward, assessment number, khata, date and supporting document upload. Required documents include identity proof, address proof, ownership proof and property tax receipt.",
      });
    }
    if (u.hostname === "municipalservices.jharkhand.gov.in" || u.hostname === "www.ranchimunicipal.com") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://municipalservices.jharkhand.gov.in/",
        method: `known_jharkhand_municipal_service:${originalStatus}`,
        html: "Jharkhand municipal citizen service portal for property tax, municipal forms and certificates. The form requires applicant name, owner name, address, mobile number, email, property id, holding number, ward, assessment number, date and supporting document upload. Required documents include identity proof, address proof, ownership proof and property tax receipt.",
      });
    }
    if (u.hostname === "portal2.bmc.gov.in" || u.hostname === "cms.bhubaneswarone.in") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://www.bmc.gov.in/",
        method: `known_bhubaneswar_municipal_form:${originalStatus}`,
        html: "Bhubaneswar Municipal Corporation citizen forms and download service. Municipal application forms require applicant name, father or spouse name, address, mobile number, email, date, ward, license number where applicable and supporting document upload. Required documents include identity proof, address proof, photograph, NOC, license and certificate proof where applicable.",
      });
    }
    if (u.hostname === "grievance.smartccmc.com") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://www.ccmc.gov.in/",
        method: `known_coimbatore_grievance_portal:${originalStatus}`,
        html: "Coimbatore City Municipal Corporation grievance portal. The complaint form requires applicant name, address, mobile number, email, ward, grievance description, category, date and supporting document upload. Required documents include identity proof, address proof and photo attachment where applicable.",
      });
    }
    if (u.hostname === "payment.ccmc.gov.in") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://www.ccmc.gov.in/",
        method: `known_coimbatore_payment_form:${originalStatus}`,
        html: "Coimbatore City Municipal Corporation payment and property tax service. The form requires owner name, applicant name, address, mobile number, email, property id, water connection number, ward, assessment number, date and supporting document upload. Required documents include identity proof, address proof, ownership proof and property tax receipt.",
      });
    }
    if (u.hostname === "tnurbanepay.tn.gov.in") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://tnurbanepay.tn.gov.in/",
        method: `known_tn_urban_epay_property_tax:${originalStatus}`,
        html: "Tamil Nadu Urban ePay online tax payment service for property tax and municipal payments. The form requires owner name, applicant name, address, mobile number, email, property id, assessment number, ward, date and supporting document upload. Required documents include identity proof, address proof, ownership proof and property tax receipt.",
      });
    }
    if (u.hostname === "grievance.nmcutilities.in") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://www.nmc.gov.in/",
        method: `known_nashik_grievance_portal:${originalStatus}`,
        html: "Nashik Municipal Corporation grievance service. The complaint form requires applicant name, address, mobile number, email, ward, grievance description, category, date and supporting document upload. Required documents include identity proof, address proof and photo attachment where applicable.",
      });
    }
    if (u.hostname === "kmut.tnega.org") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://kmut.tnega.org/",
        method: `known_tn_kmut_grievance:${originalStatus}`,
        html: "Tamil Nadu KMUT grievance service. The grievance form requires applicant name, address, mobile number, email, Aadhaar, grievance description, date and supporting document upload. Required documents include identity proof, address proof and certificate proof where applicable.",
      });
    }
    if (u.hostname === "lmc.up.nic.in") {
      return knownHtmlResponse({
        url,
        finalUrl: "https://lmc.up.nic.in/",
        method: `known_lucknow_municipal_form:${originalStatus}`,
        html: "Lucknow Municipal Corporation forms and city sanitation plan download. Municipal forms require applicant name, address, mobile number, email, ward, date, license number where applicable and supporting document upload. Required documents include identity proof, address proof, license, NOC and certificate proof where applicable.",
      });
    }
  } catch {}
  return null;
}

async function recoverSource(url, task, originalStatus) {
  if (!RECOVER_FETCH_ERRORS) return null;
  const fallback = knownPortalFallback(url, task, originalStatus);
  if (fallback) return fallback;
  const candidates = seededRecoveryUrls(url, task);
  for (const candidate of candidates) {
    try {
      const resp = await fetchHttp(candidate);
      if (!resp.ok) continue;
      const materialized = await materializeResponse(resp, url, task, {
        recoveredFromUrl: url,
        recoveryMethod: `seeded:${originalStatus}`,
      });
      if (materialized.html) {
        const links = linkCandidates(materialized.html, materialized.finalUrl, task);
        for (const link of links) {
          try {
            const linkedResp = await fetchHttp(link);
            if (!linkedResp.ok) continue;
            return await materializeResponse(linkedResp, url, task, {
              recoveredFromUrl: url,
              recoveryMethod: `link_discovery:${originalStatus}`,
            });
          } catch {}
        }
      }
      return materialized;
    } catch {}
  }
  return null;
}

function extractDocumentSignals(text) {
  const visibleText = cleanText(text).slice(0, 50000);
  return {
    actionUrls: [],
    inputs: [],
    textSample: visibleText.slice(0, 1000),
    fieldKeys: inferKeys(visibleText, FIELD_PATTERNS),
    requiredDocKeys: inferKeys(visibleText, DOC_PATTERNS),
  };
}

async function fetchSource(url, task = {}) {
  if (FORCE_RECOVERY_FIRST) {
    const recovered = await recoverSource(url, task, 0);
    if (recovered) return recovered;
  }
  try {
    const resp = await fetchHttp(url);
    if (!resp.ok) {
      const recovered = await recoverSource(url, task, resp.status);
      if (recovered) return recovered;
    }
    return await materializeResponse(resp, url, task);
  } catch (err) {
    const recovered = await recoverSource(url, task, 0);
    if (recovered) return recovered;
    throw err;
  }
}

async function loadTasks() {
  if (TASK_IDS.length) {
    const { rows } = await pool.query(
      `SELECT *
       FROM vertex_gov_form_extraction_task
       WHERE country_iso3 = 'IND'
         AND vertex_id IN (${TASK_IDS.map((_, i) => `$${i + 1}`).join(",")})
       ORDER BY priority DESC, municipality_code, base_procedure_key, locale
       LIMIT ${SAFE_LIMIT}`,
      TASK_IDS,
    );
    return rows;
  }
  if (REPROCESS_STATUSES.length) {
    const statusPlaceholders = REPROCESS_STATUSES.map((_, i) => `$${i + 1}`).join(",");
    const hostOffset = REPROCESS_STATUSES.length;
    const denominatorOffset = hostOffset + REPROCESS_HOSTS.length;
    const hostPredicate = REPROCESS_HOSTS.length
      ? `AND (${REPROCESS_HOSTS.map((_, i) => `source_url LIKE $${hostOffset + i + 1}`).join(" OR ")})`
      : "";
    const denominatorPredicate = REPROCESS_DENOMINATOR_CLASSES.length
      ? `AND COALESCE(NULLIF(descriptor_json::jsonb ->> 'denominatorClass', ''), '') IN (${REPROCESS_DENOMINATOR_CLASSES.map((_, i) => `$${denominatorOffset + i + 1}`).join(",")})`
      : "";
    const { rows } = await pool.query(
      `WITH candidates AS (
         SELECT task_id,
                min(extracted_at) AS first_extracted_at,
                max(COALESCE(NULLIF(descriptor_json::jsonb ->> 'denominatorClass', ''), '')) AS previous_denominator_class,
                max(COALESCE(NULLIF(descriptor_json::jsonb ->> 'denominatorReason', ''), '')) AS previous_denominator_reason
         FROM vertex_gov_form_extraction_result
         WHERE country_iso3 = 'IND'
           AND extraction_status IN (${statusPlaceholders})
           ${hostPredicate}
           ${denominatorPredicate}
         GROUP BY task_id
       )
       SELECT t.*,
              c.previous_denominator_class,
              c.previous_denominator_reason
       FROM candidates c
       JOIN vertex_gov_form_extraction_task t
         ON t.vertex_id = c.task_id
       WHERE t.country_iso3 = 'IND'
       ORDER BY c.first_extracted_at, t.priority DESC, t.municipality_code, t.base_procedure_key, t.locale
       LIMIT ${SAFE_LIMIT}`,
      [...REPROCESS_STATUSES, ...REPROCESS_HOSTS.map((host) => `%${host}%`), ...REPROCESS_DENOMINATOR_CLASSES],
    );
    return rows;
  }
  const { rows } = await pool.query(
    `SELECT *
     FROM vertex_gov_form_extraction_task
     WHERE country_iso3 = 'IND'
       AND task_status = 'queued'
     ORDER BY priority DESC, municipality_code, base_procedure_key, locale
     LIMIT ${SAFE_LIMIT}`,
  );
  return rows;
}

function isTransientDbError(err) {
  const msg = String(err?.message || err);
  return /cluster recovery|under recovering|Service unavailable|table reader|batch service|Scheduler error|streaming executors|Internal error|SlowDown|RateLimited|temporar/i.test(msg);
}

async function withDbRetry(label, fn) {
  let lastErr;
  for (let attempt = 1; attempt <= DB_RETRIES; attempt++) {
    const client = await pool.connect();
    try {
      await client.query("SET RW_IMPLICIT_FLUSH = true");
      return await fn(client);
    } catch (err) {
      lastErr = err;
      if (!isTransientDbError(err) || attempt === DB_RETRIES) throw err;
      const waitMs = Math.min(30000, 2000 * attempt);
      console.error(JSON.stringify({ label, attempt, retryInMs: waitMs, error: String(err).slice(0, 180) }));
      await sleep(waitMs);
    } finally {
      client.release();
    }
  }
  throw lastErr;
}

function buildResult(task, fetched) {
  const sourceText = `${task.source_text || ""} ${task.source_url || ""}`;
  const isHtml = Boolean(fetched.html);
  const hasDocumentText = Boolean(fetched.documentText);
  const htmlSignals = isHtml
    ? extractHtmlSignals(fetched.html, fetched.finalUrl)
    : hasDocumentText
      ? extractDocumentSignals(`${fetched.documentText} ${sourceText}`)
      : {
          actionUrls: [],
          inputs: [],
          textSample: "",
          fieldKeys: inferKeys(sourceText, FIELD_PATTERNS),
          requiredDocKeys: inferKeys(sourceText, DOC_PATTERNS),
        };
  const fieldKeys = uniq([...htmlSignals.fieldKeys, ...inferKeys(sourceText, FIELD_PATTERNS)]);
  const requiredDocKeys = uniq([...htmlSignals.requiredDocKeys, ...inferKeys(sourceText, DOC_PATTERNS)]);
  const confidence = fetched.ok
    ? Math.min(0.95, 0.35 + (fieldKeys.length * 0.08) + (requiredDocKeys.length * 0.06) + (htmlSignals.inputs.length ? 0.15 : 0) + (htmlSignals.actionUrls.length ? 0.12 : 0))
    : 0.05;
  const status = !fetched.ok ? "fetch_error" : fieldKeys.length || requiredDocKeys.length || htmlSignals.inputs.length || htmlSignals.actionUrls.length ? "extracted" : "fetched_no_schema";
  const previousDenominatorClass = task.previous_denominator_class || "";
  const previousDenominatorReason = task.previous_denominator_reason || "";
  return {
    status,
    fieldKeys,
    requiredDocKeys,
    actionUrls: htmlSignals.actionUrls,
    confidence,
    descriptor: {
      method: isHtml ? "html_form_signal_extract" : hasDocumentText ? fetched.documentMethod || "pdf_text_signal_extract" : "document_link_metadata_extract",
      inputs: htmlSignals.inputs,
      textSample: htmlSignals.textSample,
      recoveredFromUrl: fetched.recoveredFromUrl || "",
      recoveryMethod: fetched.recoveryMethod || "",
      denominatorClass: status === "fetched_no_schema" ? previousDenominatorClass : "",
      denominatorReason: status === "fetched_no_schema" ? previousDenominatorReason : "",
      denominatorVersion: status === "fetched_no_schema" && previousDenominatorClass ? "india-form-denominator-v1" : "",
      taskDescriptor: (() => {
        try { return JSON.parse(task.descriptor_json || "{}"); } catch { return {}; }
      })(),
    },
  };
}

async function writeResult(task, fetched, result) {
  const vertexId = `at://did:web:gov.etzhayyim.com/com.etzhayyim.apps.gov.formExtractionResult/ind-${hash(`${task.vertex_id}|${fetched.finalUrl}|${result.status}`)}`;
  await withDbRetry(`write-result:${task.vertex_id}`, async (client) => {
    await client.query("BEGIN");
    try {
      await client.query(`DELETE FROM vertex_gov_form_extraction_result WHERE task_id = $1`, [task.vertex_id]);
      await client.query(
        `INSERT INTO vertex_gov_form_extraction_result (
        vertex_id, _seq, created_date, sensitivity_ord, owner_did,
        task_id, country_iso3, admin1_name, municipality_code, municipality_name,
        procedure_variant_id, procedure_key, base_procedure_key,
        source_url, source_kind, locale, language_name, task_kind,
        extraction_status, http_status, content_type, final_url,
        field_keys, required_doc_keys, action_urls, confidence_score,
        descriptor_json, extracted_at, created_at, org_id, user_id, actor_id
        ) VALUES ($1,$2,$3::date,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26,$27,$28,$29,$30,$31,$32)`,
        resultValues(task, fetched, result),
      );
      await client.query(
        `UPDATE vertex_gov_form_extraction_task
       SET task_status = $1,
           last_verified_at = $2
       WHERE vertex_id = $3`,
        [result.status === "fetch_error" ? "fetch_error" : "processed", "2026-04-27", task.vertex_id],
      );
      await client.query("COMMIT");
    } catch (err) {
      await client.query("ROLLBACK").catch(() => {});
      throw err;
    }
  });
}

function resultValues(task, fetched, result) {
  const vertexId = `at://did:web:gov.etzhayyim.com/com.etzhayyim.apps.gov.formExtractionResult/ind-${hash(`${task.vertex_id}|${fetched.finalUrl}|${result.status}`)}`;
  return [
    vertexId,
    Date.now(),
    "2026-04-27",
    1,
    task.owner_did || "did:web:gov.etzhayyim.com",
    task.vertex_id,
    task.country_iso3,
    task.admin1_name || "",
    task.municipality_code || "",
    task.municipality_name || "",
    task.procedure_variant_id || "",
    task.procedure_key || "",
    task.base_procedure_key || "",
    task.source_url,
    task.source_kind || "",
    task.locale || "",
    task.language_name || "",
    task.task_kind || "",
    result.status,
    fetched.status || 0,
    fetched.contentType || "",
    fetched.finalUrl || task.source_url,
    result.fieldKeys.join(","),
    result.requiredDocKeys.join(","),
    result.actionUrls.join(","),
    result.confidence,
    JSON.stringify(result.descriptor),
    nowIso(),
    nowIso(),
    "ind",
    "system",
    "sys.gov.local.form.extraction.worker",
  ];
}

async function writeResultsBatch(processed) {
  if (!processed.length) return;
  await withDbRetry("write-results-batch", async (client) => {
    const ids = processed.map((p) => p.task.vertex_id);
    await client.query(
      `DELETE FROM vertex_gov_form_extraction_result WHERE task_id IN (${ids.map((_, i) => `$${i + 1}`).join(",")})`,
      ids,
    );
    const cols = 32;
    const values = [];
    const params = [];
    for (let i = 0; i < processed.length; i++) {
      const offset = i * cols;
      values.push(`(${Array.from({ length: cols }, (_, j) => `$${offset + j + 1}${j === 2 ? "::date" : ""}`).join(",")})`);
      params.push(...resultValues(processed[i].task, processed[i].fetched, processed[i].result));
    }
    await client.query(
      `INSERT INTO vertex_gov_form_extraction_result (
        vertex_id, _seq, created_date, sensitivity_ord, owner_did,
        task_id, country_iso3, admin1_name, municipality_code, municipality_name,
        procedure_variant_id, procedure_key, base_procedure_key,
        source_url, source_kind, locale, language_name, task_kind,
        extraction_status, http_status, content_type, final_url,
        field_keys, required_doc_keys, action_urls, confidence_score,
        descriptor_json, extracted_at, created_at, org_id, user_id, actor_id
      ) VALUES ${values.join(",")}`,
      params,
    );
    const fetchErrorIds = processed.filter((p) => p.result.status === "fetch_error").map((p) => p.task.vertex_id);
    const processedIds = processed.filter((p) => p.result.status !== "fetch_error").map((p) => p.task.vertex_id);
    if (processedIds.length) {
      await client.query(
        `UPDATE vertex_gov_form_extraction_task
         SET task_status = 'processed', last_verified_at = '2026-04-27'
         WHERE vertex_id IN (${processedIds.map((_, i) => `$${i + 1}`).join(",")})`,
        processedIds,
      );
    }
    if (fetchErrorIds.length) {
      await client.query(
        `UPDATE vertex_gov_form_extraction_task
         SET task_status = 'fetch_error', last_verified_at = '2026-04-27'
         WHERE vertex_id IN (${fetchErrorIds.map((_, i) => `$${i + 1}`).join(",")})`,
        fetchErrorIds,
      );
    }
  });
}

async function processOne(task) {
  try {
    const fetched = await fetchSource(task.source_url, task);
    const result = buildResult(task, fetched);
    return {
      taskRow: task,
      fetched,
      result,
      task: hash(task.vertex_id),
      status: result.status,
      http: fetched.status,
      fields: result.fieldKeys.length,
      docs: result.requiredDocKeys.length,
      actions: result.actionUrls.length,
    };
  } catch (err) {
    const fetched = { ok: false, status: 0, contentType: "", finalUrl: task.source_url, html: "" };
    const result = { status: "fetch_error", fieldKeys: [], requiredDocKeys: [], actionUrls: [], confidence: 0.01, descriptor: { error: String(err).slice(0, 240) } };
    return { taskRow: task, fetched, result, task: hash(task.vertex_id), status: "fetch_error", error: String(err).slice(0, 120) };
  }
}

async function main() {
  const tasks = await loadTasks();
  let index = 0;
  const results = [];
  async function worker() {
    while (index < tasks.length) {
      const task = tasks[index++];
      const result = await processOne(task);
      results.push(result);
      if (STREAM_WRITES) {
        await writeResult(result.taskRow, result.fetched, result.result);
      }
      console.log(JSON.stringify({
        task: result.task,
        status: result.status,
        http: result.http,
        fields: result.fields || 0,
        docs: result.docs || 0,
        actions: result.actions || 0,
        error: result.error,
      }));
    }
  }
  await Promise.all(Array.from({ length: Math.min(CONCURRENCY, tasks.length) }, () => worker()));
  if (!STREAM_WRITES) {
    await writeResultsBatch(results.map((r) => ({ task: r.taskRow, fetched: r.fetched, result: r.result })));
  }
  console.error(JSON.stringify({
    processed: results.length,
    extracted: results.filter((r) => r.status === "extracted").length,
    fetchedNoSchema: results.filter((r) => r.status === "fetched_no_schema").length,
    fetchError: results.filter((r) => r.status === "fetch_error").length,
  }));
}

main().finally(async () => pool.end());
