/**
 * ipfs-pinner — MST CAR → IPFS pinning service.
 *
 * Stage 4 of ADR-2605171800. Phase 1 implementation:
 *   - Pinning targets arrive on disk: mst-projector writes
 *     `<dataDir>/<urlencoded shardKey>/<rootCid>.car` at flush.
 *   - The pinner polls `<dataDir>` (default 10 s) and pins any `.car`
 *     it has not seen yet to the configured providers, then emits an
 *     `com.etzhayyim.substrate.ipfsPin` AT Record under the pinner's
 *     DID.
 *   - Idempotency: in-memory dedup by `<shardKey>/<rootCid>`. The
 *     content-addressed pin itself is idempotent at the provider, so
 *     restart-replay is safe.
 *
 * Production invariant (per README): replication factor ≥ 2 distinct
 * providers. Override with `ETZ_PINNER_MIN_PROVIDERS=1` for Kubo-only
 * dev loops.
 *
 * Firehose-driven mode (subscribe to `com.etzhayyim.substrate.shardSnapshot`
 * to time pins to the projector's emission) is intentionally deferred —
 * the on-disk path is simpler, has fewer moving parts, and gives the
 * same end-to-end guarantee.
 */

import { readdir, stat } from "node:fs/promises";
import { join } from "node:path";

import { pinata } from "./providers/pinata.js";
import { web3storage } from "./providers/web3storage.js";
import { filecoin } from "./providers/filecoin.js";
import { kubo } from "./providers/kubo.js";
import { kotobase } from "./providers/kotobase.js";
import { emitPinRecord } from "./emit.js";

export interface PinnerConfig {
  providers: string[];
  minProviders: number;
  dataDir: string;
  did: string;
  pdsUrl: string;
  pollIntervalMs: number;
  session?: {
    did: string;
    handle: string;
    accessJwt: string;
    refreshJwt: string;
  };
  auth?: { handle: string; password: string };
}

type ProviderFn = (carPath: string) => Promise<{ cid: string; receipt: unknown }>;

const REGISTRY: Record<string, ProviderFn> = {
  pinata: pinata as ProviderFn,
  web3storage: web3storage as ProviderFn,
  filecoin: filecoin as ProviderFn,
  kubo: kubo as ProviderFn,
  kotobase: kotobase as ProviderFn,
};

function loadConfig(): PinnerConfig {
  const session = process.env.ETZ_PINNER_PDS_SESSION
    ? (JSON.parse(process.env.ETZ_PINNER_PDS_SESSION) as PinnerConfig["session"])
    : undefined;
  const auth = !session && process.env.ETZ_PINNER_PDS_AUTH
    ? (JSON.parse(process.env.ETZ_PINNER_PDS_AUTH) as PinnerConfig["auth"])
    : undefined;
  const providers = (process.env.ETZ_PINNER_PROVIDERS ?? "kubo")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  return {
    providers,
    minProviders: Number(
      process.env.ETZ_PINNER_MIN_PROVIDERS ?? Math.min(providers.length, 2),
    ),
    dataDir: process.env.ETZ_PINNER_DATA_DIR ?? "/data/mst-projector",
    did: process.env.ETZ_PINNER_DID ?? "did:web:pinner.etzhayyim.com",
    pdsUrl: process.env.ETZ_PINNER_PDS_URL ?? "https://pds.etzhayyim.com",
    pollIntervalMs: Number(process.env.ETZ_PINNER_POLL_MS ?? 10_000),
    session,
    auth,
  };
}

interface CarTarget {
  shardKey: string;
  rootCid: string;
  carPath: string;
  byteSize: number;
}

/**
 * Walk `<dataDir>` and enumerate every `.car` file with its decoded
 * `<shardKey, rootCid>` derived from the path layout that
 * mst-projector Phase 2 writes: `<dataDir>/<encodeURIComponent(shardKey)>/<rootCid>.car`.
 */
export async function discoverCars(dataDir: string): Promise<CarTarget[]> {
  const out: CarTarget[] = [];
  let shardDirs: string[];
  try {
    shardDirs = await readdir(dataDir);
  } catch {
    return out;
  }
  for (const shardDir of shardDirs) {
    const shardKey = decodeURIComponent(shardDir);
    const full = join(dataDir, shardDir);
    let entries: string[];
    try {
      entries = await readdir(full);
    } catch {
      continue;
    }
    for (const entry of entries) {
      if (!entry.endsWith(".car")) continue;
      const rootCid = entry.slice(0, -".car".length);
      const carPath = join(full, entry);
      let byteSize = 0;
      try {
        byteSize = (await stat(carPath)).size;
      } catch {
        continue;
      }
      out.push({ shardKey, rootCid, carPath, byteSize });
    }
  }
  return out;
}

export async function pinOne(
  config: PinnerConfig,
  target: CarTarget,
): Promise<{ uri: string; cid: string; providers: string[] }> {
  const results: Array<{ provider: string; cid: string; receipt: unknown }> = [];
  for (const name of config.providers) {
    const fn = REGISTRY[name];
    if (!fn) throw new Error(`unknown provider: ${name}`);
    const { cid, receipt } = await fn(target.carPath);
    results.push({ provider: name, cid, receipt });
    console.log(
      `[ipfs-pinner] ${name} pinned ${target.carPath} → ${cid}`,
    );
  }
  if (results.length < config.minProviders) {
    throw new Error(
      `[ipfs-pinner] replication factor ${results.length} < min ${config.minProviders}`,
    );
  }
  const cids = new Set(results.map((r) => r.cid));
  if (cids.size > 1) {
    throw new Error(
      `[ipfs-pinner] CID mismatch across providers: ${[...cids].join(", ")}`,
    );
  }
  const carCid = results[0].cid;
  if (carCid !== target.rootCid) {
    throw new Error(
      `[ipfs-pinner] provider CID ${carCid} does not match expected rootCid ${target.rootCid}`,
    );
  }
  const emit = await emitPinRecord({
    did: config.did,
    pdsUrl: config.pdsUrl,
    session: config.session,
    auth: config.auth,
    shardKey: target.shardKey,
    rootCid: target.rootCid,
    carCid,
    providers: results.map((r) => r.provider),
    byteSize: target.byteSize,
    pinnedAt: new Date().toISOString(),
  });
  return { uri: emit.uri, cid: emit.cid, providers: results.map((r) => r.provider) };
}

async function pollLoop(config: PinnerConfig): Promise<void> {
  const seen = new Set<string>();
  for (;;) {
    let targets: CarTarget[];
    try {
      targets = await discoverCars(config.dataDir);
    } catch (err) {
      console.warn("[ipfs-pinner] discover failed:", err);
      targets = [];
    }
    for (const t of targets) {
      const key = `${t.shardKey}/${t.rootCid}`;
      if (seen.has(key)) continue;
      try {
        const out = await pinOne(config, t);
        console.log(
          `[ipfs-pinner] pinned ${key} via [${out.providers.join(",")}] uri=${out.uri}`,
        );
        seen.add(key);
      } catch (err) {
        console.error(`[ipfs-pinner] pin failed for ${key}:`, err);
      }
    }
    await new Promise((r) => setTimeout(r, config.pollIntervalMs));
  }
}

async function main() {
  const config = loadConfig();
  console.log("[ipfs-pinner] starting", {
    providers: config.providers,
    minProviders: config.minProviders,
    dataDir: config.dataDir,
    did: config.did,
    pdsUrl: config.pdsUrl,
    pollIntervalMs: config.pollIntervalMs,
    authMode: config.session ? "session" : config.auth ? "password" : "none",
  });
  if (config.providers.length === 0) {
    throw new Error(
      "[ipfs-pinner] ETZ_PINNER_PROVIDERS is empty; nothing to do",
    );
  }
  await pollLoop(config);
}

// Only run main() when this module is executed directly (not when
// imported by tests).
const isMainModule =
  import.meta.url.startsWith("file:") &&
  process.argv[1] &&
  import.meta.url.endsWith(process.argv[1].replace(/\\/g, "/"));
if (isMainModule) {
  main().catch((err) => {
    console.error("[ipfs-pinner] fatal:", err);
    process.exit(2);
  });
}
