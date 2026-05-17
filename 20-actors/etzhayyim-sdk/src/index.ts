/**
 * @etzhayyim/sdk
 *
 * RW-free substrate SDK for etzhayyim open religious-corp apps.
 * Per ADR-2605172000 — apps under etzhayyim/root MUST NOT depend on
 * RisingWave or any centralized off-chain DB. This SDK wraps the
 * primary substrate (AT MST + IPFS + Base L2 anchor) as one API.
 *
 * Status: scaffold v0.0.0. All implementations are TODO stubs.
 */

import type { AtpAgent } from "@atproto/api";

// ─── Configuration ──────────────────────────────────────────────────

export interface EtzhayyimConfig {
  /** The actor's DID. Must resolve to a PDS endpoint. */
  did: string;

  /** PDS HTTP endpoint. Default: from DID document `service[type=AtprotoPersonalDataServer]`. */
  pdsUrl?: string;

  /** IPFS HTTP gateway for blob fetch. Default: `https://ipfs.etzhayyim.com`. */
  ipfsGateway?: string;

  /** IPFS HTTP API for pin. Required for write operations with blobs. */
  ipfsApiUrl?: string;

  /** Base L2 RPC URL. Default: `https://mainnet.base.org`. */
  l2RpcUrl?: string;

  /** Address of the anchor contract on Base L2 (ADR-2605171800 Stage 5). */
  anchorContract?: `0x${string}`;

  /** Signer for both PDS writes and L2 anchor txns. Pre-bound to `did`. */
  signer?: Signer;
}

export interface Signer {
  signMessage(msg: Uint8Array): Promise<Uint8Array>;
  publicKeyMultibase: string;
}

// ─── Write API (replaces SQL INSERT) ────────────────────────────────

export interface WriteOpts<T extends Record<string, unknown>> {
  /** Lexicon NSID. e.g. `ai.gftd.apps.openIsco.occupation`. */
  collection: string;

  /** Record body. Validated against the resolved lexicon shape. */
  record: T;

  /**
   * Optional record key. If omitted, the SDK generates a TID
   * (timestamp-based; AT Protocol convention).
   */
  rkey?: string;

  /**
   * Optional blobs to pin to IPFS. Keys become CID references inside
   * the record body via the lexicon's $type=blob refs.
   */
  blobs?: Map<string, Blob>;

  /**
   * If true, anchor this record's MST root to Base L2 immediately
   * (synchronous). Default false — anchoring is batched per the
   * SDK's anchor scheduler (every N records or T seconds).
   */
  anchorNow?: boolean;
}

export interface WriteReceipt {
  /** AT URI of the created record. `at://<did>/<collection>/<rkey>`. */
  uri: string;

  /** Content CID of the record. */
  cid: string;

  /** CIDs of any pinned blobs, keyed by the lexicon field name. */
  blobCids: Record<string, string>;

  /**
   * L2 batch sequence number this record will land in. The actual
   * on-chain anchor tx is async unless `anchorNow: true` was set.
   */
  pendingAnchor: bigint;
}

// ─── Read API (replaces SQL SELECT) ─────────────────────────────────

export interface ReadOpts {
  /** Lexicon NSID. */
  collection: string;

  /** Specific record key. If set, returns single record. */
  rkey?: string;

  /** Key-prefix filter for MST traversal. */
  prefix?: string;

  /** Pagination cursor (from previous response). */
  cursor?: string;

  /** Page size. Default 50, max 100. */
  limit?: number;

  /** If false, skip blob fetch (return only CID refs). Default true. */
  fetchBlobs?: boolean;
}

export interface ReadResponse<T> {
  records: Array<{
    uri: string;
    cid: string;
    value: T;
    blobs?: Record<string, Blob>;
  }>;
  cursor?: string;
}

// ─── Verify API (replaces audit trail) ──────────────────────────────

export interface VerifyResult {
  /** True if the record is included in an anchored MST root. */
  included: boolean;

  /** L2 anchor tx that finalized the MST root containing this record. */
  anchoredAt?: {
    txHash: `0x${string}`;
    blockNumber: bigint;
    rootCid: string;
  };

  /** Merkle proof from record CID up to the anchored root. */
  merklePath?: string[];

  /** If !included, the reason. */
  reason?: "not-yet-anchored" | "record-not-found" | "anchor-mismatch";
}

// ─── Subscribe API (replaces streaming MV) ──────────────────────────

export interface SubscribeOpts {
  /** Lexicon NSID(s) to filter the firehose. */
  collections: string[];

  /** Cursor to resume from. Default: now. */
  cursor?: string;
}

export interface SubscribeEvent<T> {
  uri: string;
  cid: string;
  value: T;
  op: "create" | "update" | "delete";
  seq: bigint;
}

// ─── Main SDK class ─────────────────────────────────────────────────

export class Etzhayyim {
  readonly config: Required<
    Omit<EtzhayyimConfig, "signer" | "pdsUrl" | "ipfsApiUrl" | "anchorContract">
  > &
    Pick<
      EtzhayyimConfig,
      "signer" | "pdsUrl" | "ipfsApiUrl" | "anchorContract"
    >;

  #pds?: AtpAgent;

  constructor(config: EtzhayyimConfig) {
    this.config = {
      did: config.did,
      pdsUrl: config.pdsUrl,
      ipfsGateway: config.ipfsGateway ?? "https://ipfs.etzhayyim.com",
      ipfsApiUrl: config.ipfsApiUrl,
      l2RpcUrl: config.l2RpcUrl ?? "https://mainnet.base.org",
      anchorContract: config.anchorContract,
      signer: config.signer,
    };
  }

  /** Resolve DID → PDS URL if not set in config. Lazy initialization. */
  async pds(): Promise<AtpAgent> {
    if (this.#pds) return this.#pds;
    throw new Error(
      "[etzhayyim-sdk] pds() not yet implemented. " +
        "TODO: lazy-resolve DID document, instantiate AtpAgent with " +
        "service=AtprotoPersonalDataServer endpoint, attach DID-bound signer."
    );
  }

  async write<T extends Record<string, unknown>>(
    _opts: WriteOpts<T>
  ): Promise<WriteReceipt> {
    throw new Error(
      "[etzhayyim-sdk] write() not yet implemented. " +
        "TODO: (1) pin blobs to IPFS via ipfsApiUrl, (2) substitute blob " +
        "fields in record body with CID refs per lexicon $type=blob shape, " +
        "(3) call pds.com.atproto.repo.createRecord, (4) enqueue MST root " +
        "for next L2 anchor batch unless anchorNow:true."
    );
  }

  async read<T>(_opts: ReadOpts): Promise<ReadResponse<T>> {
    throw new Error(
      "[etzhayyim-sdk] read() not yet implemented. " +
        "TODO: (1) resolve PDS, (2) call pds.com.atproto.repo.listRecords " +
        "with collection/cursor/limit, (3) optionally MST-prefix-filter, " +
        "(4) if fetchBlobs, GET each blob CID from ipfsGateway."
    );
  }

  async verify(_recordUri: string): Promise<VerifyResult> {
    throw new Error(
      "[etzhayyim-sdk] verify() not yet implemented. " +
        "TODO: (1) parse AT URI → DID/collection/rkey, (2) fetch record CID " +
        "from PDS, (3) traverse MST upward to the root, (4) query anchor " +
        "contract on Base L2 for the latest root containing this MST entry, " +
        "(5) return Merkle proof + on-chain anchor tx ref."
    );
  }

  async *subscribe<T>(_opts: SubscribeOpts): AsyncGenerator<SubscribeEvent<T>> {
    throw new Error(
      "[etzhayyim-sdk] subscribe() not yet implemented. " +
        "TODO: open WebSocket to pds /xrpc/com.atproto.sync.subscribeRepos, " +
        "filter ops by opts.collections, yield events."
    );
  }

  // ─── Payment surface (ADR-2605172100) ────────────────────────────

  /** One-shot USDC payment on Base L2. See ./pay.ts for full opts. */
  async pay(opts: import("./pay.js").PayOpts) {
    const { pay } = await import("./pay.js");
    return pay(opts);
  }

  /** Open a Superfluid streaming payment. */
  async payStream(opts: import("./pay.js").PayStreamOpts) {
    const { payStream } = await import("./pay.js");
    return payStream(opts);
  }

  /** Close a Superfluid streaming payment. */
  async payStreamStop(streamId: `0x${string}`) {
    const { payStreamStop } = await import("./pay.js");
    return payStreamStop(streamId);
  }

  /** Open a Gnosis-Safe-backed escrow (2-of-3: user/recipient/arbiter). */
  async escrowOpen(opts: import("./pay.js").EscrowOpenOpts) {
    const { escrowOpen } = await import("./pay.js");
    return escrowOpen(opts);
  }

  /** Release or refund an open escrow. */
  async escrowRelease(safeAddress: `0x${string}`, to: "recipient" | "user") {
    const { escrowRelease } = await import("./pay.js");
    return escrowRelease(safeAddress, to);
  }

  /** Distribute USDC through an immutable 0xSplits contract. */
  async splitDistribute(opts: import("./pay.js").SplitDistributeOpts) {
    const { splitDistribute } = await import("./pay.js");
    return splitDistribute(opts);
  }

  // ─── Basic-income / adherent surface (ADR-2605172300) ─────────────

  /** Optional BI module config. Set per-instance when BI is in use. */
  biConfig?: import("./bi.js").BIConfig;

  /** Mint adherent SBT on geth-private. */
  async biJoin(opts: import("./bi.js").JoinOpts) {
    const { join } = await import("./bi.js");
    return join(opts, this.biConfig ?? {});
  }

  /** Record a participation event. */
  async biAttest(opts: import("./bi.js").AttestOpts) {
    const { attest } = await import("./bi.js");
    return attest(opts, this.biConfig ?? {});
  }

  /** Read accrual + status snapshot for an adherent. */
  async biStatus(tokenId: bigint) {
    const { status } = await import("./bi.js");
    return status(tokenId, this.biConfig ?? {});
  }

  /** Claim accrued kisha. Returns immediately on geth-private issue;
   *  the returned `fulfilled` promise resolves once Base settlement lands. */
  async biClaim(opts: import("./bi.js").ClaimOpts) {
    const { claim } = await import("./bi.js");
    return claim(opts, this.biConfig ?? {});
  }

  /** Submit a cell-signed phenotype multiplier update (S2). Requires a
   *  signer registered as a cell in Phenotype.sol. Normally invoked
   *  from the Python EligibilityCell; exposed in TS for test rigs. */
  async biSetPhenotype(input: import("./bi.js").PhenotypeUpdateInput) {
    const { setPhenotype } = await import("./bi.js");
    return setPhenotype(input, this.biConfig ?? {});
  }

  /** Submit a governance proposal that adjusts one constitutional mutable. */
  async biPropose(opts: import("./bi.js").ProposeOpts) {
    const { propose } = await import("./bi.js");
    return propose(opts, this.biConfig ?? {});
  }

  /** Cast a vote on an active governance proposal. */
  async biVote(proposalId: bigint, choice: "for" | "against" | "abstain") {
    const { vote } = await import("./bi.js");
    return vote(proposalId, choice, this.biConfig ?? {});
  }

  /** Read the current state of a governance proposal. */
  async biProposalState(proposalId: bigint) {
    const { proposalState } = await import("./bi.js");
    return proposalState(proposalId, this.biConfig ?? {});
  }
}

// ─── Re-exports ─────────────────────────────────────────────────────

export * as pds from "./pds.js";
export * as ipfs from "./ipfs.js";
export * as l2 from "./l2.js";
export * as pay from "./pay.js";
export * as bi from "./bi.js";
export * as paymaster from "./paymaster.js";
export { parseUsdc, parseUsdcPerSecond, USDC_BASE } from "./pay.js";
export {
  ETZHAYYIM_PRIVATE_CHAIN_ID,
  ETZHAYYIM_PRIVATE_RPC_DEFAULT,
} from "./bi.js";
export { sponsoredWriteContract, type SponsoredBundle } from "./paymaster.js";
