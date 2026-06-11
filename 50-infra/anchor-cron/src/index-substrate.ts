/**
 * anchor-cron — substrate mode (firehose-driven).
 *
 * Stage 5b of ADR-2605171800. Reads `com.etzhayyim.substrate.ipfsPin`
 * records from a PDS, submits the rootHash to EtzhayyimAnchor on Base
 * L2, and writes `com.etzhayyim.substrate.l2Anchor` receipts back.
 *
 * Sidecar mode (cell checkpoints) remains in `src/index.ts`. The two
 * entrypoints share submit.ts + solvency.ts but otherwise stand alone
 * so the sidecar test suite is unaffected.
 *
 * Required env (substrate mode):
 *   ETZ_ANCHOR_CONTRACT                  EtzhayyimAnchor on the target chain
 *   ETZ_ANCHOR_RPC_URL                   JSON-RPC endpoint (default Base mainnet)
 *   ETZ_ANCHOR_SIGNER_KEY                0x-hex 32-byte private key
 *   ETZ_ANCHOR_CHAIN_ID                  EIP-155 chain id (8453 / 84532)
 *   ETZ_ANCHOR_PDS_URL                   PDS service for both reads + writes
 *   ETZ_ANCHOR_PDS_SESSION | _PDS_AUTH   resumable session OR handle+password
 *   ETZ_ANCHOR_PINNER_REPO               DID hosting com.etzhayyim.substrate.ipfsPin
 *   ETZ_ANCHOR_ANCHORER_REPO             DID under which l2Anchor records are written
 *   ETZ_ANCHOR_CONFIRMATIONS             default 3
 *   ETZ_ANCHOR_BATCH_MAX                 default 10
 *   ETZ_ANCHOR_WARN_BALANCE_WEI          solvency floor (wei). 0 = off.
 */

import process from "node:process";
import {AtpAgent} from "@atproto/api";
import {privateKeyToAccount} from "viem/accounts";

import {runTickSubstrate, type SubstrateCronConfig} from "./cron-substrate.js";
import {readPendingFromPds} from "./pendingFromPds.js";
import {commitL2Anchor} from "./commitToPds.js";
import {submitAnchor} from "./submit.js";
import {checkSolvency, emitSolvencyWarning} from "./solvency.js";

function envOrThrow(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`anchor-cron substrate: ${name} is required`);
  return v;
}

function envBigIntOrZero(name: string): bigint {
  const raw = process.env[name];
  if (!raw) return 0n;
  try {
    return BigInt(raw);
  } catch {
    throw new Error(
      `anchor-cron substrate: ${name} must be a base-10 integer (wei)`,
    );
  }
}

async function buildAuthenticatedAgent(pdsUrl: string): Promise<AtpAgent> {
  const agent = new AtpAgent({service: pdsUrl});
  const sessionEnv = process.env.ETZ_ANCHOR_PDS_SESSION;
  const authEnv = process.env.ETZ_ANCHOR_PDS_AUTH;
  if (sessionEnv) {
    const s = JSON.parse(sessionEnv) as {
      did: string;
      handle: string;
      accessJwt: string;
      refreshJwt: string;
    };
    await agent.resumeSession({...s, active: true});
    return agent;
  }
  if (authEnv) {
    const a = JSON.parse(authEnv) as {handle: string; password: string};
    await agent.login({identifier: a.handle, password: a.password});
    return agent;
  }
  throw new Error(
    "anchor-cron substrate: ETZ_ANCHOR_PDS_SESSION or ETZ_ANCHOR_PDS_AUTH required",
  );
}

const CONFIG: SubstrateCronConfig = {
  contract: envOrThrow("ETZ_ANCHOR_CONTRACT") as `0x${string}`,
  rpcUrl: process.env.ETZ_ANCHOR_RPC_URL ?? "https://mainnet.base.org",
  signerKey: envOrThrow("ETZ_ANCHOR_SIGNER_KEY") as `0x${string}`,
  chainId: Number(process.env.ETZ_ANCHOR_CHAIN_ID ?? 8453),
  pdsUrl: process.env.ETZ_ANCHOR_PDS_URL ?? "https://pds.etzhayyim.com",
  pinnerRepo: envOrThrow("ETZ_ANCHOR_PINNER_REPO"),
  anchorerRepo: envOrThrow("ETZ_ANCHOR_ANCHORER_REPO"),
  confirmations: Number(process.env.ETZ_ANCHOR_CONFIRMATIONS ?? 3),
  batchMax: Number(process.env.ETZ_ANCHOR_BATCH_MAX ?? 10),
  warnBalanceWei: envBigIntOrZero("ETZ_ANCHOR_WARN_BALANCE_WEI"),
};

async function main(): Promise<void> {
  const agent = await buildAuthenticatedAgent(CONFIG.pdsUrl);
  const anchorerAddress = privateKeyToAccount(CONFIG.signerKey).address;

  await runTickSubstrate(CONFIG, {
    readPending: async ({limit}) =>
      readPendingFromPds({
        agent,
        pinnerRepo: CONFIG.pinnerRepo,
        anchorerRepo: CONFIG.anchorerRepo,
        limit,
      }),
    submitAnchor,
    commitL2Anchor: async (input) =>
      commitL2Anchor({
        agent,
        repo: CONFIG.anchorerRepo,
        ...input,
      }),
    resolveAnchorerAddress: async () => anchorerAddress,
    checkSolvency,
    emitSolvencyWarning,
    log: (msg) => console.log(msg),
  });
}

main().catch((cause) => {
  console.error("[anchor-cron substrate] fatal:", cause);
  process.exit(2);
});
