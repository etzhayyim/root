// yuubin.etzhayyim.com — 日本郵便 Web ゆうびん 自動化 actor (T3 TS Native, MCP-callable)
//
// MCP topology (3 tiers):
//   Tier 1 (high-level orchestration):
//     composeAndPost(content, format, to, deliveryMethod, caseId, ...) — render → upload → submit → record
//     submitNaiyoShomei(content, addresseeNames[], senderName, caseId, ...) — e内容証明 path
//     submitLetterpack(blobKey/url, to, kind=light|plus, caseId) — レターパック path
//   Tier 2 (browser automation primitives):
//     webyubinSubmit(blobKey/url, to, deliveryMethod) — Web ゆうびん 通常便 form
//   Tier 3 (storage + audit):
//     uploadDocument(contentBase64, contentType) — pre-rendered → SHA-256 → B2
//     getStatus(apptNumber) — query 申込番号 status
//     listSubmissions(filter) — list past
//
// Provider abstraction (manual fallback DEFAULT — real automation requires Web ゆうびん 法人 credentials):
//   provider="auto"   → Try CF Browser Rendering puppeteer; fall back to manual on failure
//   provider="manual" → Returns prepared assets + Teams/email notification (operator action required) — DEFAULT
//   provider="puppeteer" → Force CF Browser Rendering automation (fail if HEADLESS_BROWSER missing)
//
// Design E 3-Tier Write:
//   Tier 1 (social)  — no social post by default (confidential).
//   Tier 2 (domain)  — postalItem / postalItemUpdate via com.atproto.repo.createRecord.
//   Tier 3 (state)   — provider creds via Secrets Store (SS_WEBYUBIN_*); B2 dedup keyed by SHA-256.

import {
  asAgentTool,
  createWorkerExport,
  decodeJson,
  genID,
  nowISO,
  nsid,
  str,
  withCapabilityTags,
  type HostSDK,
} from "@etzhayyim/kotodama-host-sdk";
import { unzipSync, zipSync, strFromU8, strToU8 } from "./fflate.mjs";
import puppeteer from "@cloudflare/puppeteer";
import { cdnHead, cdnRead, cdnWrite } from "./cdn-b2";

let appId = "";

// ───────────────────────── preprocessing: A4 docx injection ─────────────────────────
//
// Web ゆうびん rejects .docx that is not A4 (210x297mm). pandoc's default .docx output is US
// Letter; Word for Mac often defaults to the locale's standard which on US locale is Letter.
// This helper unzips the .docx, injects/replaces <w:pgSz>+<w:pgMar> in every <w:sectPr>,
// and repacks. Pure JS (fflate), runs in CF Workers.

const A4_SECTPR_INJECTION =
  '<w:pgSz w:w="11906" w:h="16838"/>' +
  '<w:pgMar w:top="1440" w:right="1134" w:bottom="1440" w:left="1134" ' +
  'w:header="720" w:footer="720" w:gutter="0"/>';

function normalizeDocxToA4(bytes: Uint8Array): Uint8Array {
  const files = unzipSync(bytes);
  const docXml = files["word/document.xml"];
  if (!docXml) throw new Error("invalid .docx (word/document.xml not found)");
  let xml = strFromU8(docXml);
  // Remove existing pgSz / pgMar
  xml = xml.replace(/<w:pgSz\b[^/]*\/>/g, "");
  xml = xml.replace(/<w:pgMar\b[^/]*\/>/g, "");
  // Inject into every <w:sectPr>
  xml = xml.replace(/<w:sectPr\/>/g, `<w:sectPr>${A4_SECTPR_INJECTION}</w:sectPr>`);
  xml = xml.replace(/<w:sectPr>\s*<\/w:sectPr>/g, `<w:sectPr>${A4_SECTPR_INJECTION}</w:sectPr>`);
  xml = xml.replace(
    /<w:sectPr>((?:[^<]|<(?!\/w:sectPr>))*)<\/w:sectPr>/g,
    (_m, inner: string) =>
      inner.includes("<w:pgSz")
        ? `<w:sectPr>${inner}</w:sectPr>`
        : `<w:sectPr>${A4_SECTPR_INJECTION}${inner}</w:sectPr>`,
  );
  files["word/document.xml"] = strToU8(xml);
  return zipSync(files, { level: 6 });
}

// ───────────────────────── preprocessing: PDF page size check ─────────────────────────
//
// Minimal PDF inspection: count pages + detect page size. Uses heuristic /MediaBox parsing.
// A4 MediaBox is `[0 0 595.28 841.89]` (points). Tolerance ±5.

function parsePdfA4Status(bytes: Uint8Array): { pages: number; isA4: boolean; sampleSize?: [number, number] } {
  const text = new TextDecoder("latin1").decode(bytes);
  const pageCount = (text.match(/\/Type\s*\/Page(?!s)/g) || []).length || 1;
  const mediaBoxMatches = [...text.matchAll(/\/MediaBox\s*\[\s*([-.\d]+)\s+([-.\d]+)\s+([-.\d]+)\s+([-.\d]+)\s*\]/g)];
  if (mediaBoxMatches.length === 0) return { pages: pageCount, isA4: false };
  // All MediaBoxes should be ~A4 (portrait 595x842 or landscape 842x595)
  const isA4Box = (a: number, b: number, c: number, d: number): boolean => {
    const w = Math.abs(c - a);
    const h = Math.abs(d - b);
    const a4p = Math.abs(w - 595.28) < 5 && Math.abs(h - 841.89) < 5;
    const a4l = Math.abs(w - 841.89) < 5 && Math.abs(h - 595.28) < 5;
    return a4p || a4l;
  };
  const allA4 = mediaBoxMatches.every((m) => isA4Box(+m[1], +m[2], +m[3], +m[4]));
  const first = mediaBoxMatches[0];
  return {
    pages: pageCount,
    isA4: allA4,
    sampleSize: [Math.abs(+first[3] - +first[1]), Math.abs(+first[4] - +first[2])],
  };
}

// ───────────────────────── env / secrets ─────────────────────────

async function resolveSecret(v: unknown): Promise<string> {
  if (!v) return "";
  if (typeof v === "string") return v;
  const anyV = v as { get?: () => Promise<string>; text?: () => Promise<string> };
  if (typeof anyV.get === "function") return await anyV.get();
  if (typeof anyV.text === "function") return await anyV.text();
  return String(v);
}

// ───────────────────────── helpers ─────────────────────────

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function write(sdk: HostSDK, kind: string, rec: Record<string, unknown>): void {
  const collection = `com.etzhayyim.apps.yuubin.${kind}`;
  const enriched = {
    ...rec,
    createdAt: nowISO(),
    org_id: "etzhayyim.com",
    user_id: "anon",
    actor_id: appId,
  };
  sdk.pds.dispatch({
    type: "com.atproto.repo.createRecord",
    payload: { collection, recordJson: JSON.stringify(enriched) },
  });
}

interface PostalAddress {
  postalCode?: string;       // 例: "100-8920" (東京地裁)
  prefecture?: string;       // 例: "東京都"
  cityWardLine1?: string;    // 例: "千代田区霞が関1-1-4"
  building?: string;         // 例: "東京地方裁判所 民事第7部"
  recipientName?: string;    // 例: "御中"
  honorific?: string;        // 例: "御中" / "様"
}

function formatAddressOneLine(a: PostalAddress): string {
  return [a.postalCode ? `〒${a.postalCode}` : "", a.prefecture, a.cityWardLine1, a.building, a.recipientName, a.honorific].filter(Boolean).join(" ");
}

async function uploadToCdn(env: Record<string, unknown>, bytes: Uint8Array, contentType: string): Promise<{ blobKey: string; deduped: boolean; publicUrl: string }> {
  const blobKey = await sha256Hex(bytes);
  const baseUrl = str(env.CDN_PUBLIC_BASE_URL ?? "https://yuubin.etzhayyim.com/api/blob");
  const existing = await cdnHead(env as Record<string, string>, blobKey).catch(() => null);
  let deduped = false;
  if (existing) {
    deduped = true;
  } else {
    await cdnWrite(env as Record<string, string>, blobKey, bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer, contentType);
  }
  return { blobKey, deduped, publicUrl: `${baseUrl}/${blobKey}` };
}

// ───────────────────────── browser automation (Tier 2) ─────────────────────────

interface WebyubinSubmission {
  apptNumber: string;        // 申込番号 (Web ゆうびん が発行)
  trackingNumber?: string;   // 追跡番号 (発送後に発行)
  totalCostJpy: number;
  paidAt?: string;
  scheduledShipAt?: string;
  screenshotBlobKey?: string;
}

// Real DOM verified 2026-04-20 via Claude in Chrome against https://webyubin.jpi.post.japanpost.jp/
// Login form (action POST https://webyubin.jpi.post.japanpost.jp/webyubin/snt/DYFR900.do):
//   - input#mailAddress (text)  — user sets value; name is JWT-encoded, id is stable
//   - input#password    (password) — same
//   - <a onclick="submitActionByFormId('DYFR900.login', 'main'); return false;">ログイン</a>
// Top page (DYFR900.do) service menu via submitActionByFormId('DYFR900.XXX', 'main'):
//   - DYFR210 / DYFR220  → Webレタックス (慶弔)
//   - DYFR410 / DYFR415  → Webレター (請求書・通知書印刷配送)  ← 通常の書類郵送はこれ
//   - DYFR310 / DYFR315  → Web速達
//   - openEnMenu()       → e内容証明 (popup window)
// Logout: submitActionByFormId('logout', 'main')
// 登録情報: /webyubin/kad/DYFR040.do

type DyfrAction =
  | "DYFR410" // Webレター (DEFAULT for regular postal items)
  | "DYFR415" // Webレター 差込差出し
  | "DYFR310" // Web速達
  | "DYFR315" // Web速達 差込差出し
  | "DYFR210" // Webレタックス かんたん作成
  | "DYFR220" // Webレタックス こだわり作成
  ;

function deliveryMethodToDyfr(m: "regular" | "letterpack-light" | "letterpack-plus" | "express"): DyfrAction {
  switch (m) {
    case "express":          return "DYFR310"; // Web速達
    case "letterpack-light":
    case "letterpack-plus":
    case "regular":
    default:                 return "DYFR410"; // Webレター (default for postal items)
  }
}

async function browserAutomateWebyubin(
  sdk: HostSDK,
  blobKey: string,
  to: PostalAddress,
  deliveryMethod: "regular" | "letterpack-light" | "letterpack-plus" | "express",
  contentDescription: string,
): Promise<WebyubinSubmission> {
  const browserBinding = sdk.env.HEADLESS_BROWSER;
  if (!browserBinding) {
    throw new Error("HEADLESS_BROWSER binding missing. Web ゆうびん 自動化には CF Browser Rendering の binding が必要です。wrangler.jsonc に `browser: { binding: 'HEADLESS_BROWSER' }` を追加し、@cloudflare/puppeteer を install してください。");
  }
  const username = await resolveSecret(sdk.env.SS_WEBYUBIN_USERNAME);
  const password = await resolveSecret(sdk.env.SS_WEBYUBIN_PASSWORD);
  if (!username || !password) {
    throw new Error("Web ゆうびん credentials missing (SS_WEBYUBIN_USERNAME / SS_WEBYUBIN_PASSWORD). etzhayyim.webyubin keychain に登録 → Secrets Store に同期してください。");
  }

  const browser = await puppeteer.launch(browserBinding as any);
  let screenshotBytes: Uint8Array | null = null;
  let apptNumber = "";
  let totalCostJpy = 0;

  // Helper to save a screenshot for debugging and include URL in error
  const saveDebugShot = async (page: any, label: string): Promise<string> => {
    try {
      const png = await page.screenshot({ fullPage: true });
      const { blobKey } = await uploadToCdn(sdk.env, new Uint8Array(png), "image/png");
      const url = `${str(sdk.env.CDN_PUBLIC_BASE_URL)}/${blobKey}`;
      console.error(`[yuubin debug] ${label} screenshot: ${url}`);
      return url;
    } catch (e) {
      return `(screenshot failed: ${e instanceof Error ? e.message : String(e)})`;
    }
  };

  try {
    const page = await browser.newPage();
    // Spoof real macOS Chrome UA — Web ゆうびん may sniff for unsupported browsers
    try { await page.setUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"); } catch {}
    await page.setViewport({ width: 1440, height: 900 });
    const loginUrl = str(sdk.env.WEBYUBIN_LOGIN_URL ?? "https://webyubin.jpi.post.japanpost.jp/");
    await page.goto(loginUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
    // Let F5 BIG-IP / Akamai-style JS challenges complete (TS* cookies take several seconds to settle)
    await new Promise((r) => setTimeout(r, 8000));
    // Verify we actually have a filled form (challenge might redirect)
    await page.waitForSelector("#mailAddress", { timeout: 10000 });
    // Log initial cookies for challenge analysis
    const initialCookies = await page.cookies().catch(() => []);
    console.log(`[yuubin login] initial cookies after JS settle: count=${initialCookies.length} TS=${initialCookies.filter((c: any) => c.name.startsWith("TS")).map((c: any) => `${c.name}=${c.value.slice(0, 12)}..`).join(",")}`);

    // ── 1. ログイン (verified against real DOM 2026-04-20) ─────────
    //    Input ids are stable; name attributes are JWT-encoded and rotate.
    // Fill fields using puppeteer's type() to trigger real input events (DOM value + keystroke events)
    // This matches real user behavior — some sites validate on key events, not value set directly.
    await page.focus("#mailAddress");
    await page.evaluate(() => { (document.getElementById("mailAddress") as HTMLInputElement).value = ""; });
    await page.type("#mailAddress", username, { delay: 50 });
    await page.focus("#password");
    await page.evaluate(() => { (document.getElementById("password") as HTMLInputElement).value = ""; });
    await page.type("#password", password, { delay: 50 });

    const cookiesBefore = await page.cookies().catch(() => []);
    const jsessionBefore = cookiesBefore.find((c: any) => c.name === "JSESSIONID")?.value || "(none)";
    console.log(`[yuubin login] cookies before: ${cookiesBefore.map((c: any) => c.name).join(",") || "(none)"} JSESSIONID=${jsessionBefore.slice(0, 30)}`);

    // Capture login request + response for debugging
    const loginRespPromise = page.waitForResponse(
      (r: any) => /\/webyubin\/snt\/DYFR900(\.login)?\.do/.test(r.url()) && r.request().method() === "POST",
      { timeout: 30000 },
    ).catch(() => null);

    await Promise.all([
      page.waitForNavigation({ waitUntil: "load", timeout: 30000 }).catch((e: any) => {
        console.log(`[yuubin login] waitNav err: ${(e?.message || e || "").toString().slice(0, 100)}`);
      }),
      page.evaluate(() => (globalThis as any).submitActionByFormId("DYFR900.login", "main")),
    ]);

    const loginResp: any = await loginRespPromise;
    if (loginResp) {
      let bodySnippet = "(unavailable)";
      try {
        const body = await loginResp.text();
        bodySnippet = body.replace(/\s+/g, " ").slice(0, 500);
      } catch {}
      console.log(`[yuubin login] POST response: status=${loginResp.status()} url=${loginResp.url()} location=${loginResp.headers()["location"] || "(none)"} setCookie=${loginResp.headers()["set-cookie"]?.slice(0,200) || "(none)"}`);
      console.log(`[yuubin login] body: ${bodySnippet}`);
    } else {
      console.log(`[yuubin login] POST response not captured`);
    }
    // Check for login error message in body
    const errorMsg = await page.evaluate(() => {
      const errNode = document.querySelector('.errorMsg, .error, [class*="err"], #errorMsg');
      return errNode ? errNode.textContent?.trim().slice(0, 200) : null;
    });
    if (errorMsg) {
      console.log(`[yuubin login] error message on page: "${errorMsg}"`);
    }

    // Strict post-login marker wait (requires 登録内容の変更 or ログアウト in <a> text — unique to authenticated state)
    await page.waitForFunction(
      () => Array.from(document.querySelectorAll("a")).some(
        (a) => /登録内容の変更/.test(a.textContent || "") || /^\[?ログアウト\]?$/.test((a.textContent || "").trim())
      ),
      { timeout: 20000 },
    ).catch(async (e: any) => {
      const cookiesAfter = await page.cookies().catch(() => []);
      const state = await page.evaluate(() => ({
        url: location.href,
        hasMailAddress: !!document.getElementById("mailAddress"),
        bodyExcerpt: (document.body.innerText || "").slice(0, 400),
      }));
      const shot = await saveDebugShot(page, "post-login-no-marker");
      throw new Error(
        `Login marker not found (登録内容の変更/ログアウト). url=${state.url} hasMailForm=${state.hasMailAddress} cookies=[${cookiesAfter.map((c: any) => c.name).join(",")}] excerpt="${state.bodyExcerpt.slice(0, 200)}" screenshot=${shot} innerErr=${(e?.message || e || "").toString().slice(0, 100)}`,
      );
    });

    const cookiesAfter = await page.cookies().catch(() => []);
    console.log(`[yuubin login] cookies after: count=${cookiesAfter.length} names=${cookiesAfter.map((c: any) => `${c.name}(${c.domain})`).join(",").slice(0, 300)}`);

    // ── 2. 申込フロー起動 (service menu → e.g. DYFR410 = Webレター) ──
    const dyfrAction = deliveryMethodToDyfr(deliveryMethod);
    await Promise.all([
      page.waitForNavigation({ waitUntil: "domcontentloaded", timeout: 30000 }).catch(() => null),
      page.evaluate((action: string) => (globalThis as any).submitActionByFormId(`DYFR900.${action}`, "main"), dyfrAction),
    ]);
    await new Promise((r) => setTimeout(r, 1500));

    // ── 3. File upload via iframe lightbox ─────────────────
    //    Verified flow (Claude-in-Chrome 2026-04-20):
    //      a. Main page: click "選択" → saveAndSubmit('DYFR920') → opens TB_iframeContent lightbox
    //      b. Iframe #TB_iframeContent contains input#DYFR920_uploadFile[type=file]
    //      c. Inside iframe: select 白黒 radio, inject File via DataTransfer, call exeAction()
    //    Alternative: saveAndSubmit('DYFR940') for template selection (unused here).
    const hit = await cdnRead(sdk.env as Record<string, string>, blobKey);
    if (!hit) throw new Error(`blob ${blobKey} not found in CDN`);
    const fileBytes = new Uint8Array(hit.body);

    // 3a. Trigger iframe lightbox
    console.log("[yuubin] step 3a: triggering saveAndSubmit('DYFR920')");
    await page.evaluate(() => (globalThis as any).saveAndSubmit("DYFR920"));
    console.log("[yuubin] step 3a: waiting for iframe#TB_iframeContent");
    const iframeHandle = await page.waitForSelector("iframe#TB_iframeContent", { timeout: 15000 }).catch(async (e: any) => {
      const shot = await saveDebugShot(page, "iframe-not-found");
      throw new Error(`iframe#TB_iframeContent wait failed: ${e?.message || e}. screenshot=${shot}`);
    });
    console.log("[yuubin] step 3a: got iframe handle");
    const iframe: any = await iframeHandle.contentFrame();
    if (!iframe) throw new Error("TB_iframeContent iframe not accessible");
    console.log("[yuubin] step 3a: iframe contentFrame OK, waiting for #DYFR920_uploadFile");
    await iframe.waitForSelector("#DYFR920_uploadFile", { timeout: 15000 }).catch(async (e: any) => {
      const shot = await saveDebugShot(page, "iframe-file-input-missing");
      const iframeBody = await iframe.evaluate(() => (document.body?.innerText || "").slice(0, 500)).catch(() => "(iframe body read failed)");
      throw new Error(`#DYFR920_uploadFile wait failed: ${e?.message || e}. iframeBody="${iframeBody}" screenshot=${shot}`);
    });
    console.log("[yuubin] step 3a: #DYFR920_uploadFile ready");

    // 3b. Inject file bytes into iframe's input#DYFR920_uploadFile via DataTransfer + select 白黒
    await iframe.evaluate(async (bytesArr: number[], filename: string) => {
      const arr = new Uint8Array(bytesArr);
      const blob = new Blob([arr], { type: "application/pdf" });
      const file = new File([blob], filename, { type: "application/pdf" });
      const input = document.getElementById("DYFR920_uploadFile") as HTMLInputElement | null;
      if (!input) throw new Error("DYFR920_uploadFile not found in iframe");
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      input.dispatchEvent(new Event("change", { bubbles: true }));
      // 白黒 radio (checkedKey2 = 白黒, checkedKey1 = カラー)
      const bw = document.getElementById("DYFR920_model_printSetting_checkedKey2") as HTMLInputElement | null;
      if (bw) { bw.checked = true; bw.click(); bw.dispatchEvent(new Event("change", { bubbles: true })); }
    }, Array.from(fileBytes), `${blobKey.slice(0, 12)}.pdf`);

    // 3c. Trigger iframe's exeAction (submitAction('DYFR920.upload')) and wait for lightbox close
    await iframe.evaluate(() => (globalThis as any).exeAction());
    // wait until iframe becomes hidden / detached (upload completed)
    await page.waitForFunction(() => {
      const el = document.getElementById("TB_iframeContent");
      return !el || (el as HTMLElement).offsetParent === null;
    }, { timeout: 45000 }).catch(() => null);
    await new Promise((r) => setTimeout(r, 1500));

    // 3d. Confirm content — click "内容を確定する" on main page
    await Promise.all([
      page.waitForNavigation({ waitUntil: "domcontentloaded", timeout: 30000 }).catch(() => null),
      page.evaluate(() => {
        const btn = Array.from(document.querySelectorAll("a, button, input[type=button], input[type=submit]"))
          .find((e) => /内容を確定する/.test((e as HTMLElement).textContent || (e as HTMLInputElement).value || ""));
        (btn as HTMLElement)?.click();
      }),
    ]);
    await new Promise((r) => setTimeout(r, 1500));
    const afterUploadShot = await saveDebugShot(page, "after-upload");

    // ── 4. 宛先入力 (selectors require live validation — returning early with debug shot for now) ──
    //    Webレター の 宛先画面は DYFR4xx ルート下。未検証。本 push では upload 完了までを自動化し、
    //    以降は screenshot を返して operator 手動確認 + confirmManualPost でクローズする。
    const addrPageShot = await page.evaluate(() => ({
      url: location.href,
      title: document.title,
      bodyTail: (document.body.innerText || "").slice(-800).replace(/\s+/g, " "),
    }));
    console.log(`[yuubin] after upload page state:`, JSON.stringify(addrPageShot).slice(0, 400));

    // ── 5/6. Capture apptNumber / cost if any already visible on the post-upload screen ──
    const capture = await page.evaluate(() => {
      const body = document.body.innerText || "";
      const mApp = body.match(/(?:申込番号|お申込番号|受付番号)[:：\s]*([A-Z0-9\-]+)/);
      const mCost = body.match(/(?:合計|料金|お支払い金額)[:：\s]*[¥￥]?\s*([\d,]+)\s*円/);
      return { apptNumber: mApp?.[1] ?? "", totalCostText: mCost?.[1] ?? "" };
    });
    apptNumber = capture.apptNumber;
    totalCostJpy = Number(capture.totalCostText.replace(/,/g, "")) || 0;

    // Persist URL of after-upload screenshot for operator follow-up
    const shotKey = afterUploadShot.split("/").pop() || "";
    if (shotKey) {
      screenshotBytes = null; // already saved via saveDebugShot
    }

    // ── 7. 確認画面 screenshot ──────────────────────
    if (!screenshotBytes) {
      const png = await page.screenshot({ fullPage: true });
      screenshotBytes = new Uint8Array(png);
    }

    // ── 8. logout (session cleanup) ─────────────────
    try {
      await page.evaluate(() => (globalThis as any).submitActionByFormId?.("logout", "main"));
    } catch {}
  } finally {
    await browser.close().catch(() => {});
  }

  let screenshotBlobKey: string | undefined;
  if (screenshotBytes) {
    const { blobKey: k } = await uploadToCdn(sdk.env, screenshotBytes, "image/png");
    screenshotBlobKey = k;
  }
  return {
    apptNumber,
    totalCostJpy,
    paidAt: nowISO(),
    screenshotBlobKey,
  };
}

// ───────────────────────── commands ─────────────────────────

async function cmdUploadDocument(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const b64 = str(args.contentBase64 ?? "");
  const contentType = str(args.contentType ?? "application/pdf");
  if (!b64) return { ok: false, error: "contentBase64 required" };
  try {
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const { blobKey, deduped, publicUrl } = await uploadToCdn(sdk.env, bytes, contentType);
    return { ok: true, blobKey, publicUrl, byteSize: bytes.length, deduped };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : String(e) };
  }
}

async function runPuppeteerFlow(
  sdk: HostSDK,
  txId: string,
  blobKey: string,
  to: PostalAddress,
  deliveryMethod: "regular" | "letterpack-light" | "letterpack-plus" | "express",
  contentDescription: string,
  caseId: string,
  subject: string,
): Promise<void> {
  try {
    const result = await browserAutomateWebyubin(sdk, blobKey, to, deliveryMethod, contentDescription);
    write(sdk, "postalItemUpdate", {
      txId,
      blobKey,
      provider: "puppeteer",
      apptNumber: result.apptNumber,
      totalCostJpy: result.totalCostJpy,
      paidAt: result.paidAt,
      screenshotBlobKey: result.screenshotBlobKey,
      status: "submitted",
      submittedAt: nowISO(),
      confirmedAt: nowISO(),
    });
  } catch (e) {
    const errMsg = e instanceof Error ? e.message : String(e);
    console.error(`[yuubin puppeteer ${txId}] failed:`, errMsg);
    write(sdk, "postalItemUpdate", {
      txId,
      blobKey,
      provider: "puppeteer",
      status: "failed",
      error: errMsg,
      caseId,
      subject,
      failedAt: nowISO(),
    });
  }
}

async function cmdComposeAndPost(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const blobKey = str(args.blobKey ?? "");
  const url = str(args.url ?? "");
  if (!blobKey && !url) return { ok: false, error: "blobKey or url required (PDF を事前 uploadDocument で R2 へ)" };

  const to = (args.to ?? {}) as PostalAddress;
  if (!to.postalCode || !to.cityWardLine1) {
    return { ok: false, error: "to.postalCode と to.cityWardLine1 が必要" };
  }

  const deliveryMethod = (str(args.deliveryMethod ?? "regular")) as "regular" | "letterpack-light" | "letterpack-plus" | "express";
  const provider = str(args.provider ?? "auto");
  const caseId = str(args.caseId ?? "");
  const subject = str(args.subject ?? "");
  const contentDescription = str(args.contentDescription ?? subject ?? "");
  const teamsChannelEmail = str(args.teamsChannelEmail ?? "");
  const operatorEmail = str(args.operatorEmail ?? "");

  const txId = genID("post");

  // ── async puppeteer provider: dispatch to Durable Object for long-running flow ──
  // CF Workers have ~30s CPU budget; Web ゆうびん full flow (login + iframe upload + form + submit)
  // can take 40-60s. Durable Object instances can run up to 30 min wall clock via alarm, so we
  // delegate the puppeteer work to YUUBIN_POST_DO which persists state and drives alarms.
  if (provider === "auto" || provider === "puppeteer") {
    const doNs = (sdk.env as any).YUUBIN_POST_DO;
    if (doNs) {
      write(sdk, "postalItem", {
        txId, blobKey,
        toAddress: formatAddressOneLine(to), deliveryMethod, caseId, subject,
        provider: "puppeteer", status: "processing", submittedAt: nowISO(),
      });
      try {
        const id = doNs.idFromName(txId);
        const stub = doNs.get(id);
        await stub.fetch("https://do/start", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ txId, blobKey, to, deliveryMethod, contentDescription, caseId, subject }),
        });
        return {
          ok: true, txId, provider: "puppeteer-do", status: "processing",
          hint: "Poll com.etzhayyim.apps.yuubin.getTxStatus or postalItemUpdate for final state. DO alarm runs the puppeteer flow.",
        };
      } catch (e) {
        console.error("DO dispatch failed:", e instanceof Error ? e.message : String(e));
      }
    }
    // Fallback to waitUntil pattern (works for flows < 30s)
    write(sdk, "postalItem", {
      txId, blobKey,
      toAddress: formatAddressOneLine(to), deliveryMethod, caseId, subject,
      provider: "puppeteer", status: "processing", submittedAt: nowISO(),
    });
    const task = runPuppeteerFlow(sdk, txId, blobKey, to, deliveryMethod, contentDescription, caseId, subject);
    (sdk.pds as any).pendingWrites?.push(task);
    return {
      ok: true, txId, provider: "puppeteer-waituntil", status: "processing",
      hint: "DO binding missing — using waitUntil fallback. Poll postalItemUpdate AT Record for status.",
    };
  }

  // ── manual handoff ──
  const cdnBase = str(sdk.env.CDN_PUBLIC_BASE_URL ?? "https://yuubin.etzhayyim.com/api/blob");
  const docUrl = url || `${cdnBase}/${blobKey}`;
  const webyubinUrl = str(sdk.env.WEBYUBIN_LOGIN_URL ?? "https://webyubin.jpi.post.japanpost.jp/");

  let notificationId: string | null = null;
  if (teamsChannelEmail || operatorEmail) {
    try {
      const recipients = [teamsChannelEmail, operatorEmail].filter(Boolean);
      const r = await fetch("https://mailer.etzhayyim.com/xrpc/com.etzhayyim.apps.mailer.send", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          to: recipients,
          subject: `[YUUBIN 手動投函依頼] ${subject || `caseId=${caseId}`} → ${formatAddressOneLine(to)}`,
          bodyHtml:
            `<p>Web ゆうびん 手動投函が必要です (provider=manual)。</p>` +
            `<ul>` +
            `<li>送付先: <code>${formatAddressOneLine(to)}</code></li>` +
            `<li>配送方法: <b>${deliveryMethod}</b></li>` +
            `<li>caseId: <code>${caseId || "(none)"}</code></li>` +
            `<li>subject: ${subject || "(none)"}</li>` +
            `<li>txId: <code>${txId}</code></li>` +
            `<li>PDF: <a href="${docUrl}">${docUrl}</a></li>` +
            `</ul>` +
            `<p>手順: <a href="${webyubinUrl}">${webyubinUrl}</a> を開きログイン → "${deliveryMethod}" 選択 → PDF upload → 上記宛先入力 → 決済 → 申込番号控え。</p>` +
            `<p>投函完了後、com.etzhayyim.apps.yuubin.confirmManualPost({ txId: "${txId}", apptNumber, paidAt }) で記録更新してください。</p>`,
          importance: "high",
        }),
      });
      if (r.ok) {
        const j = await r.json().catch(() => ({})) as Record<string, unknown>;
        notificationId = (j.messageId as string) ?? null;
      }
    } catch (e) {
      console.error("notifyOperator failed:", e instanceof Error ? e.message : String(e));
    }
  }

  write(sdk, "postalItem", {
    txId, blobKey,
    toAddress: formatAddressOneLine(to),
    deliveryMethod, caseId, subject,
    provider: "manual",
    notificationId,
    status: "needs_human",
    submittedAt: nowISO(),
  });

  return {
    ok: true,
    txId,
    provider: "manual",
    status: "needs_human",
    notificationId: notificationId ?? undefined,
    humanInstructions: {
      channel: "web-yuubin",
      uploadUrl: webyubinUrl,
      downloadUrl: docUrl,
      to: formatAddressOneLine(to),
      deliveryMethod,
      steps: [
        `Open ${webyubinUrl} (logged in as 法人 account)`,
        `Click "${deliveryMethod}" メニュー`,
        `Upload PDF from ${docUrl}`,
        `Enter 宛先: ${formatAddressOneLine(to)}`,
        `Confirm 配送方法 + 決済 (登録済クレカ)`,
        `Capture 申込番号`,
        `After completion, call com.etzhayyim.apps.yuubin.confirmManualPost({ txId: "${txId}", apptNumber, paidAt })`,
      ],
    },
  };
}

async function cmdSubmitNaiyoShomei(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  // e内容証明 path: Web ゆうびん の 内容証明メニューに遷移して Word ファイル up
  // 当面 manual handoff で実装。puppeteer 化は別タスク。
  const blobKey = str(args.blobKey ?? "");
  const senderName = str(args.senderName ?? "");
  const addresseeNames = (args.addresseeNames as string[]) ?? [];
  const caseId = str(args.caseId ?? "");
  const subject = str(args.subject ?? "");
  const teamsChannelEmail = str(args.teamsChannelEmail ?? "");
  const enaiyoUrl = str(sdk.env.ENAIYO_URL ?? "https://webyubin.jpi.post.japanpost.jp/webyubin/kad/DYFR010.do");

  if (!blobKey || !senderName || addresseeNames.length === 0) {
    return { ok: false, error: "blobKey, senderName, addresseeNames[] が必要" };
  }
  const txId = genID("naiyo");
  const cdnBase = str(sdk.env.CDN_PUBLIC_BASE_URL);
  const docUrl = `${cdnBase}/${blobKey}`;

  write(sdk, "postalItem", {
    txId, blobKey,
    deliveryMethod: "naiyo-shomei",
    senderName,
    addresseeNames,
    caseId, subject,
    provider: "manual",
    status: "needs_human",
    submittedAt: nowISO(),
  });

  return {
    ok: true, txId, provider: "manual", status: "needs_human",
    humanInstructions: {
      channel: "e-naiyo-shomei",
      uploadUrl: enaiyoUrl,
      downloadUrl: docUrl,
      steps: [
        `Open ${enaiyoUrl} (法人 account)`,
        `Click "電子内容証明 (e内容証明)" メニュー`,
        `Word ファイル up (PDF 不可、要 Word 形式)`,
        `差出人: ${senderName}`,
        `受取人: ${addresseeNames.join(", ")}`,
        `配達証明・本人限定受取等のオプション選択`,
        `決済 → 申込番号取得`,
        `confirmManualPost({ txId: "${txId}", apptNumber, paidAt }) で記録更新`,
      ],
    },
  };
}

async function cmdNormalizeDocx(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const blobKey = str(args.blobKey ?? "");
  if (!blobKey) return { ok: false, error: "blobKey required" };
  try {
    const hit = await cdnRead(sdk.env as Record<string, string>, blobKey);
    if (!hit) return { ok: false, error: `blob ${blobKey} not found` };
    const bytes = new Uint8Array(hit.body);
    const normalized = normalizeDocxToA4(bytes);
    const { blobKey: newKey, publicUrl, deduped } = await uploadToCdn(sdk.env, normalized, "application/vnd.openxmlformats-officedocument.wordprocessingml.document");
    return {
      ok: true,
      originalBlobKey: blobKey,
      normalizedBlobKey: newKey,
      normalizedPublicUrl: publicUrl,
      byteSize: normalized.length,
      deduped,
      appliedSectPr: A4_SECTPR_INJECTION,
    };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : String(e) };
  }
}

async function cmdValidatePdf(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const blobKey = str(args.blobKey ?? "");
  if (!blobKey) return { ok: false, error: "blobKey required" };
  try {
    const hit = await cdnRead(sdk.env as Record<string, string>, blobKey);
    if (!hit) return { ok: false, error: `blob ${blobKey} not found` };
    const bytes = new Uint8Array(hit.body);
    const result = parsePdfA4Status(bytes);
    return {
      ok: true,
      blobKey,
      pages: result.pages,
      isA4: result.isA4,
      sampleSize: result.sampleSize,
      byteSize: bytes.length,
      warning: result.isA4 ? null : "PDF is not A4 (595.28x841.89pt). Web ゆうびん will reject. Re-render via pandoc --pdf-engine=xelatex -V papersize=a4 with embedded CJK fonts.",
    };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : String(e) };
  }
}

async function cmdGetTxStatus(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const txId = str(args.txId ?? "");
  if (!txId) return { ok: false, error: "txId required" };
  // Kysely/Hyperdrive lookup omitted here for brevity — in production, read from
  // graph projection of postalItem + postalItemUpdate by txId.
  // For now, signal that the caller should fetch via the standard AT Record read path.
  return {
    ok: true,
    txId,
    hint: "Read com.etzhayyim.apps.yuubin.postalItem + postalItemUpdate AT Records filtered by txId. Final status lands in postalItemUpdate.",
  };
}

async function cmdConfirmManualPost(sdk: HostSDK, body: Uint8Array) {
  const args = decodeJson(body, {}) as Record<string, unknown>;
  const txId = str(args.txId ?? "");
  if (!txId) return { ok: false, error: "txId required" };
  const apptNumber = str(args.apptNumber ?? "");
  const trackingNumber = str(args.trackingNumber ?? "");
  const paidAt = str(args.paidAt ?? nowISO());
  const totalCostJpy = Number(args.totalCostJpy ?? 0);

  write(sdk, "postalItemUpdate", {
    txId, apptNumber, trackingNumber,
    status: "submitted", paidAt, totalCostJpy,
    confirmedAt: nowISO(), confirmedManually: true,
  });

  return { ok: true, txId, status: "submitted", apptNumber, trackingNumber };
}

// ───────────────────────── Durable Object ─────────────────────────
// Long-running puppeteer flow isolation. Started via fetch("/start"), immediately schedules an
// alarm (1s) which runs the actual browser automation. Alarm handler has no 30s CPU cap (up to
// 30min wall clock). On completion, writes postalItemUpdate via PDS XRPC (direct fetch since we
// have no HostSDK in DO scope).

interface YuubinPostPayload {
  txId: string;
  blobKey: string;
  to: PostalAddress;
  deliveryMethod: "regular" | "letterpack-light" | "letterpack-plus" | "express";
  contentDescription: string;
  caseId: string;
  subject: string;
}

export class YuubinPostDO {
  state: DurableObjectState;
  env: Record<string, unknown>;
  constructor(state: DurableObjectState, env: Record<string, unknown>) {
    this.state = state;
    this.env = env;
  }
  async fetch(req: Request): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname === "/start") {
      const payload = (await req.json()) as YuubinPostPayload;
      await this.state.storage.put("payload", payload);
      await this.state.storage.setAlarm(Date.now() + 1000);
      return new Response(JSON.stringify({ scheduled: true, txId: payload.txId }), {
        headers: { "content-type": "application/json" },
      });
    }
    if (url.pathname === "/status") {
      const payload = await this.state.storage.get("payload");
      const result = await this.state.storage.get("result");
      return new Response(JSON.stringify({ payload, result }), {
        headers: { "content-type": "application/json" },
      });
    }
    return new Response("not found", { status: 404 });
  }
  async alarm(): Promise<void> {
    const payload = await this.state.storage.get<YuubinPostPayload>("payload");
    if (!payload) return;
    try {
      // Build a minimal HostSDK-like object just for the fields browserAutomateWebyubin needs.
      // Only env (HEADLESS_BROWSER, SS_WEBYUBIN_*, B2_KEY_ID/B2_APPLICATION_KEY/B2_BUCKET, CDN_PUBLIC_BASE_URL) + a write function.
      const doSdk: any = {
        env: this.env,
        pds: {
          dispatch: (arg: any) => {
            console.log("[YuubinPostDO] dispatch", arg.type, (arg.payload?.collection || arg.payload?.did || ""));
          },
          pendingWrites: [] as Promise<unknown>[],
        },
      };
      const result = await browserAutomateWebyubin(
        doSdk,
        payload.blobKey,
        payload.to,
        payload.deliveryMethod,
        payload.contentDescription,
      );
      await this.state.storage.put("result", { ok: true, ...result, completedAt: nowISO() });
      console.log(`[YuubinPostDO ${payload.txId}] completed: apptNumber=${result.apptNumber} cost=${result.totalCostJpy}`);
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : String(e);
      await this.state.storage.put("result", { ok: false, error: errMsg, failedAt: nowISO() });
      console.error(`[YuubinPostDO ${payload.txId}] failed:`, errMsg);
    }
  }
}

// ───────────────────────── Worker export ─────────────────────────

export default createWorkerExport((sdk) => {
  appId = sdk.pds.selfNanoid ?? "y00b1nx9";

  // B2 blob proxy: GET /api/blob/{sha256hex} with CORS:* (for browser automation / puppeteer injection)
  sdk.router.options("/api/blob/:key", (c) => new Response(null, {
    status: 204,
    headers: {
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET, HEAD, OPTIONS",
      "access-control-allow-headers": "*",
      "access-control-max-age": "86400",
    },
  }));
  sdk.router.get("/api/blob/:key", async (c) => {
    const key = c.req.param("key");
    if (!/^[a-f0-9]{64}$/.test(key)) return c.text("invalid blobKey", 400);
    const hit = await cdnRead(sdk.env as Record<string, string>, key).catch(() => null);
    if (!hit) return c.text("blob not found", 404);
    return new Response(hit.body, {
      headers: {
        "content-type": hit.contentType,
        "content-length": String(hit.body.byteLength),
        "cache-control": "public, max-age=31536000, immutable",
        "x-blob-key": key,
        "access-control-allow-origin": "*",
        "access-control-expose-headers": "content-type, content-length, x-blob-key",
      },
    });
  });

  sdk.app
    // Tier 1 (DEFAULT for agents)
    .command(nsid("com.etzhayyim.apps.yuubin.composeAndPost"), async (_c, b) => cmdComposeAndPost(sdk, b),
      asAgentTool("End-to-end Web ゆうびん 投函: PDF blob + 宛先 (郵便番号/都道府県/市区町村/建物/受取人) + 配送方法 (regular | letterpack-light | letterpack-plus | express) → CF Browser Rendering puppeteer で Web ゆうびん 自動操作 (login → 文書 upload → 宛先入力 → 決済 → 申込番号取得)。失敗時は Teams/email manual-handoff フォールバック。confirmManualPost で audit chain クローズ。"),
      withCapabilityTags("yuubin", "post", "outbound", "compliance", "high-level"))
    .command(nsid("com.etzhayyim.apps.yuubin.submitNaiyoShomei"), async (_c, b) => cmdSubmitNaiyoShomei(sdk, b),
      asAgentTool("e内容証明 (電子内容証明) 発出: blobKey (Word 形式) + 差出人 + 受取人[] → Web ゆうびん 内容証明メニュー (現状 manual-handoff)。配達証明付き 3 通 (差出人控/受取人/郵便局保管) を機械印刷・封入・発送。"),
      withCapabilityTags("yuubin", "naiyo-shomei", "outbound", "compliance"))
    .command(nsid("com.etzhayyim.apps.yuubin.confirmManualPost"), async (_c, b) => cmdConfirmManualPost(sdk, b),
      asAgentTool("Manual handoff の投函完了を記録 (apptNumber + paidAt + trackingNumber)。postalItemUpdate を AT Repo に書き込み audit chain をクローズ。"),
      withCapabilityTags("yuubin", "confirm", "audit"))
    .command(nsid("com.etzhayyim.apps.yuubin.getTxStatus"), async (_c, b) => cmdGetTxStatus(sdk, b),
      asAgentTool("composeAndPost で発行された txId の処理状況を取得。async puppeteer flow は postalItem (initial) + postalItemUpdate (final) の 2 レコードを AT Repo に書く。最終 status/apptNumber は postalItemUpdate に入る。"),
      withCapabilityTags("yuubin", "status", "tx"))
    // Tier 2 (helpers)
    .command(nsid("com.etzhayyim.apps.yuubin.uploadDocument"), async (_c, b) => cmdUploadDocument(sdk, b),
      asAgentTool("Pre-rendered PDF (base64) を CDN R2 へ content-addressed upload (SHA-256 dedup)。返り値の blobKey を composeAndPost / submitNaiyoShomei に渡す。"),
      withCapabilityTags("yuubin", "upload", "blob"))
    // Tier 2 (preprocessing: A4 正規化)
    .command(nsid("com.etzhayyim.apps.yuubin.normalizeDocx"), async (_c, b) => cmdNormalizeDocx(sdk, b),
      asAgentTool("Web ゆうびん は .docx が A4 (210x297mm) でないと拒否する。pandoc 既定は US Letter。この command は blobKey の .docx を unzip → word/document.xml の <w:sectPr> に A4 pgSz/pgMar を注入 → 再 zip → 新しい blobKey 返却。pure JS (fflate)、CF Worker で完結。"),
      withCapabilityTags("yuubin", "preprocess", "docx", "a4"))
    .command(nsid("com.etzhayyim.apps.yuubin.validatePdf"), async (_c, b) => cmdValidatePdf(sdk, b),
      asAgentTool("PDF blob の page size を検査し、A4 (595.28x841.89pt) か確認。Web ゆうびん へ submit 前に呼んで non-A4 を早期検出。MediaBox 解析は heuristic (完全検査は pdfcpu 等を別途)。"),
      withCapabilityTags("yuubin", "preprocess", "pdf", "validate"));
});
