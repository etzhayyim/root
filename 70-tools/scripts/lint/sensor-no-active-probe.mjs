#!/usr/bin/env node
/**
 * sensor-no-active-probe lint — enforce ADR-2605262400 §7 + G8.
 *
 * Pre-commit gate. Scans staged changes under
 * `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/` for
 * forbidden imports + calls that would let a DatasetSensor perform
 * active network probes against third-party hosts.
 *
 * Forbidden imports: socket / dnspython / aiodns / scapy / nmap /
 * paramiko.
 *
 * Forbidden URL hosts in string literals: any HTTP/HTTPS URL whose
 * host is not in the religious-corp allow-list.
 *
 * Allow-list:
 *   - etzhayyim.com (incl. subdomains)
 *   - 127.0.0.1, localhost
 *   - 192.168.1.70 (EVO-X2 LAN — Murakumo fleet)
 *
 * `charter_rider.py` is exempted (it's a content scanner, not a
 * network sensor).
 *
 * Exit code 0 on success, 1 on violation.
 *
 * Authoritative ADR:
 *   90-docs/adr/2605262400-public-data-organism-ipfs-ingestion.md
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const args = process.argv.slice(2);
if (args.length === 0) process.exit(0);

const SENSOR_PREFIX =
  "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/";
const EXEMPT_BASENAMES = new Set([
  "charter_rider.py",
]);

const FORBIDDEN_IMPORTS = [
  [/^\s*import\s+socket\b/m, "import socket"],
  [/^\s*from\s+socket\b/m, "from socket"],
  [/^\s*import\s+dns\b/m, "import dns / dnspython"],
  [/^\s*from\s+dns(\.|\s)/m, "from dns.* / dnspython"],
  [/^\s*import\s+aiodns\b/m, "import aiodns"],
  [/^\s*from\s+aiodns\b/m, "from aiodns"],
  [/^\s*import\s+scapy\b/m, "import scapy"],
  [/^\s*from\s+scapy\b/m, "from scapy"],
  [/^\s*import\s+nmap\b/m, "import nmap / python-nmap"],
  [/^\s*from\s+nmap\b/m, "from nmap / python-nmap"],
  [/^\s*import\s+paramiko\b/m, "import paramiko"],
  [/^\s*from\s+paramiko\b/m, "from paramiko"],
];

const HOST_ALLOWLIST = [
  "etzhayyim.com",
  "127.0.0.1",
  "localhost",
  "192.168.1.70",
];

const URL_LITERAL_RE = /https?:\/\/([^/\s"'`]+)/g;

let violations = 0;

for (const file of args) {
  if (!file.startsWith(SENSOR_PREFIX)) continue;
  const basename = file.split("/").pop() || "";
  if (EXEMPT_BASENAMES.has(basename)) continue;

  const abs = resolve(process.cwd(), file);
  if (!existsSync(abs)) continue;
  let content;
  try {
    content = readFileSync(abs, "utf8");
  } catch {
    continue;
  }

  for (const [re, label] of FORBIDDEN_IMPORTS) {
    if (re.test(content)) {
      console.error(
        `[X] ${file}: forbidden ${label} in DatasetSensor source. ` +
          `Sensors MUST be PASSIVE-ONLY per ADR-2605262400 §7.`,
      );
      violations += 1;
    }
  }

  for (const match of content.matchAll(URL_LITERAL_RE)) {
    const host = match[1] || "";
    const ok = HOST_ALLOWLIST.some((tok) => host.includes(tok));
    if (!ok) {
      console.error(
        `[X] ${file}: URL host '${host}' not on religious-corp ` +
          `allow-list. Sensors MUST NOT contact third-party hosts ` +
          `(ADR-2605262400 §7 / G8).`,
      );
      violations += 1;
    }
  }
}

if (violations > 0) {
  console.error(
    `\n${violations} sensor-no-active-probe violation(s). ` +
      `See ADR-2605262400 §7 for the passive-only invariant.`,
  );
  process.exit(1);
}
process.exit(0);
