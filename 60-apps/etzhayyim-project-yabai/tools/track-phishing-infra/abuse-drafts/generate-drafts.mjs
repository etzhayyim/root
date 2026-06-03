#!/usr/bin/env node
// Generate .eml abuse-report drafts from vertex_yabai_infra_track.
// Drafts only — never sends. Review, then hand-submit.
//
// Usage: PGPASSWORD=... node generate-drafts.mjs

import { spawn } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PG = ["-h", process.env.RW_HOST ?? "45.32.79.245", "-p", process.env.RW_PORT ?? "4566",
            "-U", process.env.RW_USER ?? "root", "-d", process.env.RW_DB ?? "dev"];
const FROM = process.env.ABUSE_FROM ?? "abuse-liaison@etzhayyim.com";
const REPLY_TO = process.env.ABUSE_REPLY_TO ?? "jun@etzhayyim.com";

const ABUSE_TARGETS = {
  asn: {
    135377: { name: "UCLOUD HK", to: "abuse@ucloud.cn", cc: [] },
    152194: { name: "CTG Server Limited HK", to: "abuse@ctgserver.com", cc: [] },
    45102:  { name: "Alibaba Cloud SG", to: "abuse@alibabacloud.com", cc: [] },
    47583:  { name: "Hostinger", to: "abuse@hostinger.com", cc: [] },
  },
  registrar: {
    "Dynadot Inc":          { to: "abuse@dynadot.com" },
    "Dynadot LLC":          { to: "abuse@dynadot.com" },
    "NameSilo, LLC":        { to: "abuse@namesilo.com" },
    "Gname.com Pte. Ltd.":  { to: "abuse@gname.com" },
    "GMO Internet Group, Inc. d/b/a Onamae.com": { to: "abuse@onamae.com" },
    "Metaregistrar BV":     { to: "abuse@metaregistrar.com" },
  },
};

function psql(sql) {
  return new Promise((resolve, reject) => {
    const p = spawn("psql", [...PG, "-tA", "-F", "\t", "-c", sql]);
    let out = "", err = "";
    p.stdout.on("data", (b) => (out += b));
    p.stderr.on("data", (b) => (err += b));
    p.on("close", (c) => c === 0 ? resolve(out.trim()) : reject(new Error(err)));
  });
}

function eml({ to, subject, body }) {
  const date = new Date().toUTCString();
  return [
    `From: ${FROM}`,
    `To: ${to}`,
    `Reply-To: ${REPLY_TO}`,
    `Subject: ${subject}`,
    `Date: ${date}`,
    `Content-Type: text/plain; charset=utf-8`,
    ``,
    body,
  ].join("\r\n");
}

const legalBoilerplate = `
We identified the following domains as active phishing / typosquat
infrastructure impersonating WhatsApp, LINE, Mastercard, Apple, and SMBC.
Classification source: etzhayyim Yabai intel pipeline (com.etzhayyim.apps.yabai,
evidence category PhishingInfrastructure, confidence >=0.95). Probe
method: DNS + WHOIS + Team Cymru ASN lookup + crt.sh CT log (2026-04-19).

Request: please investigate and take appropriate action (suspend /
null-route / revoke registration) in accordance with your AUP and
applicable ICANN / local law obligations.

We can provide additional evidence (original phishing SMS/email payload,
victim reports, timeline) on request. Please reply to ${REPLY_TO}.

— etzhayyim Security Intel, https://yabai.etzhayyim.com
`.trim();

async function hostingDrafts() {
  const rows = (await psql(`
    SELECT asn, asn_org, asn_country,
           COUNT(DISTINCT domain) AS cnt,
           STRING_AGG(DISTINCT domain || ' => ' || COALESCE(resolved_ip,'-'), '||' ORDER BY domain || ' => ' || COALESCE(resolved_ip,'-'))
    FROM vertex_yabai_infra_track
    WHERE asn IS NOT NULL
    GROUP BY asn, asn_org, asn_country
    ORDER BY cnt DESC;
  `)).split("\n").filter(Boolean);

  for (const row of rows) {
    const [asn, asnOrg, country, cnt, list] = row.split("\t");
    const tgt = ABUSE_TARGETS.asn[Number(asn)];
    if (!tgt) continue;
    const body = [
      `Hello ${tgt.name} abuse team,`,
      ``,
      `We are reporting ${cnt} domains currently resolving to your network`,
      `(${asnOrg}, AS${asn}, ${country}). Full list below (domain => ip):`,
      ``,
      list.split("||").join("\n"),
      ``,
      legalBoilerplate,
    ].join("\n");
    const subject = `[Abuse][AS${asn}] ${cnt} phishing domains on your network (etzhayyim Yabai)`;
    const file = join(__dirname, `hosting-AS${asn}.eml`);
    writeFileSync(file, eml({ to: tgt.to, subject, body }));
    console.log(`wrote ${file} → ${tgt.to} (${cnt} domains)`);
  }
}

async function registrarDrafts() {
  const rows = (await psql(`
    SELECT registrar, COUNT(DISTINCT domain) AS cnt,
           STRING_AGG(DISTINCT domain, '||' ORDER BY domain)
    FROM vertex_yabai_infra_track
    WHERE registrar IS NOT NULL
    GROUP BY registrar
    ORDER BY cnt DESC;
  `)).split("\n").filter(Boolean);

  for (const row of rows) {
    const [registrar, cnt, list] = row.split("\t");
    const tgt = ABUSE_TARGETS.registrar[registrar];
    if (!tgt) { console.log(`SKIP registrar with no abuse contact: ${registrar}`); continue; }
    const body = [
      `Hello ${registrar} abuse team,`,
      ``,
      `We are reporting ${cnt} domains registered through ${registrar}`,
      `that resolve to active phishing / typosquat infrastructure.`,
      ``,
      `Domains:`,
      list.split("||").join("\n"),
      ``,
      legalBoilerplate,
    ].join("\n");
    const subject = `[Abuse][Registrar] ${cnt} phishing domains registered via ${registrar}`;
    const safe = registrar.replace(/[^A-Za-z0-9]+/g, "-").replace(/-+$/, "");
    const file = join(__dirname, `registrar-${safe}.eml`);
    writeFileSync(file, eml({ to: tgt.to, subject, body }));
    console.log(`wrote ${file} → ${tgt.to} (${cnt} domains)`);
  }
}

mkdirSync(__dirname, { recursive: true });
await hostingDrafts();
await registrarDrafts();
console.log("done — review .eml files before sending");
