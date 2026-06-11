/**
 * Operational smoke — runs anchor-cron's real submit.ts code path
 * against a locally-deployed EtzhayyimAnchor on Anvil. No PDS, no IPFS;
 * those are exercised at the unit-test layer already. This smoke
 * confirms that an MST rootCid (Phase 2 output of mst-projector) flows
 * cleanly through `submit.ts → EtzhayyimAnchor.anchor() → Anchored event`
 * on a real EVM.
 *
 * Pre-reqs (the test fails-fast otherwise):
 *   - `anvil --port 8546` running in the background
 *   - `forge script Deploy.s.sol --rpc-url http://127.0.0.1:8546 --broadcast`
 *     has been executed (contract address printed below).
 *
 * Run:
 *   cd 50-infra/anchor-cron
 *   pnpm exec tsx smoke/substrate-anvil-smoke.ts
 */

import {createPublicClient, http, parseEventLogs} from "viem";
import {privateKeyToAccount} from "viem/accounts";

import {submitAnchor, ETZHAYYIM_ANCHOR_ABI} from "../src/submit.js";
import {ipfsPinToPendingRoot} from "../src/pendingFromPds.js";

// submit.ts deliberately keeps its ABI minimal (only the call surface
// it uses). The smoke needs the Anchored event for log parsing, so we
// extend the production ABI here.
const SMOKE_ABI = [
  ...ETZHAYYIM_ANCHOR_ABI,
  {
    type: "event",
    name: "Anchored",
    anonymous: false,
    inputs: [
      {name: "rootHash", type: "bytes32", indexed: true},
      {name: "anchorer", type: "address", indexed: true},
      {name: "ipfsCid", type: "bytes", indexed: false},
      {name: "blockNumber", type: "uint256", indexed: false},
      {name: "batchSize", type: "uint64", indexed: false},
    ],
  },
] as const;

const RPC_URL = process.env.ETZ_SMOKE_RPC ?? "http://127.0.0.1:8546";
const CONTRACT =
  (process.env.ETZ_SMOKE_CONTRACT as `0x${string}`) ??
  "0x5fbdb2315678afecb367f032d93f642f64180aa3";
const SIGNER_KEY =
  (process.env.ETZ_SMOKE_KEY as `0x${string}`) ??
  "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";

// A real CID that mst-projector's MST round-trip test produces for the
// two-record fixture (see 50-infra/mst-projector/src/mst.test.ts).
// Any valid v1-dag-cbor CID would work; this one is checked in.
const FIXTURE = {
  uri: "at://did:web:pinner.etzhayyim.com/com.etzhayyim.substrate.ipfsPin/3a",
  shardKey: "com.etzhayyim.apps.threads.post",
  rootCid: "bafyreigh2akiscaildc7obb6q3vbiqd5gukvvr44e7lsdgowf2c5sb6e44",
  carCid: "bafyreigh2akiscaildc7obb6q3vbiqd5gukvvr44e7lsdgowf2c5sb6e44",
  byteSize: 4096,
  blockCount: 3,
  pinnedAt: "2026-05-21T12:00:00.000Z",
};

async function main(): Promise<void> {
  console.log("[smoke] EtzhayyimAnchor =", CONTRACT, "rpc =", RPC_URL);

  const {pending} = ipfsPinToPendingRoot(FIXTURE);
  console.log(
    "[smoke] fixture rootCid =",
    FIXTURE.rootCid,
    "→ rootHash =",
    pending.rootHash,
  );

  const submit = await submitAnchor({
    contract: CONTRACT,
    rpcUrl: RPC_URL,
    signerKey: SIGNER_KEY,
    confirmations: 1,
    pending,
  });
  console.log(
    "[smoke] submitAnchor returned:",
    JSON.stringify({
      txHash: submit.txHash,
      blockNumber: submit.blockNumber,
      logIndex: submit.logIndex,
      alreadyAnchored: submit.alreadyAnchored,
    }),
  );

  if (submit.alreadyAnchored) {
    console.log(
      "[smoke] (idempotency path — anchor pre-existed; you can re-run after `anvil --reset` for a fresh tx)",
    );
  }

  // Verify on-chain Anchored event + anchors() mapping read.
  const publicClient = createPublicClient({transport: http(RPC_URL)});
  const onChain = (await publicClient.readContract({
    address: CONTRACT,
    abi: ETZHAYYIM_ANCHOR_ABI,
    functionName: "anchors",
    args: [pending.rootHash],
  })) as readonly [`0x${string}`, `0x${string}`, bigint, `0x${string}`, bigint, bigint];
  const [rootHash, ipfsCidHex, blockNumber, anchorer, batchSize] = onChain;
  console.log("[smoke] on-chain anchors() entry:");
  console.log("  rootHash    =", rootHash);
  console.log("  blockNumber =", blockNumber.toString());
  console.log("  anchorer    =", anchorer);
  console.log("  batchSize   =", batchSize.toString());
  console.log("  ipfsCid len =", (ipfsCidHex.length - 2) / 2, "bytes");

  if (rootHash.toLowerCase() !== pending.rootHash.toLowerCase()) {
    throw new Error(
      `[smoke] FAIL: on-chain rootHash ${rootHash} != expected ${pending.rootHash}`,
    );
  }
  if (blockNumber === 0n) {
    throw new Error("[smoke] FAIL: blockNumber == 0 (not anchored)");
  }
  const expectedAnchorer = privateKeyToAccount(SIGNER_KEY).address;
  if (anchorer.toLowerCase() !== expectedAnchorer.toLowerCase()) {
    throw new Error(
      `[smoke] FAIL: anchorer ${anchorer} != signer ${expectedAnchorer}`,
    );
  }
  const ipfsCidBytes = new Uint8Array(
    Buffer.from(ipfsCidHex.slice(2), "hex"),
  );
  const ipfsCidString = new TextDecoder().decode(ipfsCidBytes);
  if (ipfsCidString !== FIXTURE.rootCid) {
    throw new Error(
      `[smoke] FAIL: on-chain ipfsCid "${ipfsCidString}" != expected "${FIXTURE.rootCid}"`,
    );
  }
  console.log("[smoke] on-chain ipfsCid decoded =", ipfsCidString, "(✓ matches fixture)");

  // For fresh anchors (non-idempotency path), additionally check the
  // Anchored event in the receipt.
  if (!submit.alreadyAnchored) {
    const receipt = await publicClient.getTransactionReceipt({hash: submit.txHash});
    const events = parseEventLogs({
      abi: SMOKE_ABI,
      logs: receipt.logs,
      eventName: "Anchored",
    });
    if (events.length !== 1) {
      throw new Error(
        `[smoke] FAIL: expected 1 Anchored event, got ${events.length}`,
      );
    }
    const ev = events[0] as unknown as {
      args: {rootHash: `0x${string}`; anchorer: `0x${string}`};
    };
    if (ev.args.rootHash.toLowerCase() !== pending.rootHash.toLowerCase()) {
      throw new Error(
        `[smoke] FAIL: event rootHash ${ev.args.rootHash} != expected ${pending.rootHash}`,
      );
    }
    console.log("[smoke] Anchored event verified: rootHash + anchorer match");
  }

  console.log("[smoke] ✓ substrate pipeline operational smoke PASSED");
}

main().catch((err) => {
  console.error("[smoke] fatal:", err);
  process.exit(1);
});
