/**
 * Kubo provider — pin a CAR to a local (or LAN-reachable) Kubo node.
 *
 * Religious-corp default. No API key, no centralized service, no
 * deal-based archival. The pin lives as long as the Kubo node runs.
 * Pair with at least one durable provider (Filecoin via Storacha) in
 * production per ADR-2605171800 Stage 4 replication-factor invariant.
 *
 * Kubo HTTP API used:
 *   - POST /api/v0/dag/import   (multipart CAR upload, returns roots[])
 *   - POST /api/v0/pin/add?arg=<cid>  (idempotent recursive pin)
 *
 * Endpoint: `ETZ_KUBO_API` (default `http://127.0.0.1:5001`).
 *
 * The function MUST be called with a CAR file produced by mst-projector
 * Phase 2; the single CAR root CID is returned + verified against the
 * /dag/import response.
 */

import { readFile } from "node:fs/promises";

export interface KuboPinResult {
  cid: string;
  receipt: {
    provider: "kubo";
    apiUrl: string;
    rootsReported: string[];
    pinAddOk: boolean;
  };
}

interface DagImportLine {
  Root?: { Cid?: { "/"?: string } };
  Stats?: unknown;
}

interface PinAddResponse {
  Pins?: string[];
}

const DEFAULT_API = "http://127.0.0.1:5001";

function trimApi(url: string): string {
  return url.replace(/\/+$/, "");
}

async function postCarToDagImport(
  apiUrl: string,
  carBytes: Uint8Array,
): Promise<string[]> {
  const form = new FormData();
  const blob = new Blob([carBytes as BlobPart], {
    type: "application/vnd.ipld.car",
  });
  form.append("file", blob, "shard.car");
  const res = await fetch(`${trimApi(apiUrl)}/api/v0/dag/import?pin-roots=true`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    throw new Error(
      `[ipfs-pinner/kubo] dag/import failed: ${res.status} ${await res.text()}`,
    );
  }
  // Kubo streams NDJSON; each line is a JSON object. Collect Root.Cid["/"]
  // entries — typically one per CAR.
  const text = await res.text();
  const roots: string[] = [];
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    let parsed: DagImportLine;
    try {
      parsed = JSON.parse(trimmed) as DagImportLine;
    } catch {
      continue;
    }
    const cid = parsed.Root?.Cid?.["/"];
    if (typeof cid === "string") roots.push(cid);
  }
  if (roots.length === 0) {
    throw new Error("[ipfs-pinner/kubo] dag/import returned no roots");
  }
  return roots;
}

async function pinAddRecursive(apiUrl: string, cid: string): Promise<boolean> {
  const url = `${trimApi(apiUrl)}/api/v0/pin/add?arg=${encodeURIComponent(cid)}&recursive=true`;
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) {
    throw new Error(
      `[ipfs-pinner/kubo] pin/add failed: ${res.status} ${await res.text()}`,
    );
  }
  const body = (await res.json()) as PinAddResponse;
  return Array.isArray(body.Pins) && body.Pins.includes(cid);
}

export async function kubo(carPath: string): Promise<KuboPinResult> {
  const apiUrl = process.env.ETZ_KUBO_API ?? DEFAULT_API;
  const carBytes = await readFile(carPath);
  const roots = await postCarToDagImport(apiUrl, new Uint8Array(carBytes));
  if (roots.length > 1) {
    // mst-projector CARs always have exactly one root; defensive guard
    // against an upstream change that would silently mis-pin.
    throw new Error(
      `[ipfs-pinner/kubo] expected single root, got ${roots.length}: ${roots.join(", ")}`,
    );
  }
  const cid = roots[0];
  const pinAddOk = await pinAddRecursive(apiUrl, cid);
  return {
    cid,
    receipt: {
      provider: "kubo",
      apiUrl,
      rootsReported: roots,
      pinAddOk,
    },
  };
}

/**
 * Test seam — exposes internals for unit tests that inject a fake
 * `fetch`. Production code uses {@link kubo} above.
 */
export const __testing = {
  postCarToDagImport,
  pinAddRecursive,
};
