/**
 * @etzhayyim/sdk/bi — Basic-income (kisha) + adherent registry helpers.
 *
 * Status: scaffold. Stubs only — except `join()`, which now implements
 * the full two-chain atomic ritual per ADR-2605172700 (cross-substrate
 * link between 信者 / EtzhayyimMembership on Base and Adherent /
 * AdherentRegistry on geth-private).
 *
 * Composition: the SDK speaks to two chains.
 *   - geth-private (ChainID 2605): AdherentRegistry, KishaStream,
 *     AnchorBridge, Constitution, Governance (S3+).
 *   - Base L2:                     EtzhayyimMembership (per ADR-2605172600),
 *                                  KishaPayout, Treasury Safe (USDC).
 *
 * The two-chain plumbing is internal to this module; callers see a
 * single coherent surface: join → attest → status → claim.
 */

import {
  createPublicClient,
  http,
  decodeEventLog,
  parseAbiItem,
  type Address,
  type Hash,
  type PublicClient,
  type WalletClient,
} from "viem";
import {AtpAgent} from "@atproto/api";

import {
  ETZHAYYIM_MEMBERSHIP_ABI,
  KISHA_STREAM_ABI,
  OATH_RECORD_NSID,
} from "./abi.js";
import type {PaymentReceipt} from "./pay.js";

// Parsed once at module load; used by claim() fulfillment polling.
const FULFILLED_EVENT = parseAbiItem(
  "event Fulfilled(bytes32 indexed ticketId, uint256 indexed tokenId, address indexed baseRecipient, uint256 amount, uint64 fulfilledAt)"
);

// ─── Constants ──────────────────────────────────────────────────────

/** geth-private ChainID per ADR-2605172300 §1. */
export const ETZHAYYIM_PRIVATE_CHAIN_ID = 2605 as const;

/** Default chain RPC for geth-private. SDK consumer SHOULD override. */
export const ETZHAYYIM_PRIVATE_RPC_DEFAULT =
  "https://chain.etzhayyim.com" as const;

/** Reserved attestation event types. Extensible via Constitution. */
export type AttestationEventType =
  | "prayer"
  | "study"
  | "service"
  | "donation";

// ─── Configuration ──────────────────────────────────────────────────

export interface BIConfig {
  /** geth-private RPC URL. */
  privateRpcUrl?: string;

  /** Constitution.sol address on geth-private. */
  constitutionAddress?: `0x${string}`;

  /** AdherentRegistry.sol address on geth-private. */
  registryAddress?: `0x${string}`;

  /** KishaStream.sol address on geth-private. */
  kishaStreamAddress?: `0x${string}`;

  /** AnchorBridge.sol address on geth-private. */
  anchorBridgeAddress?: `0x${string}`;

  /** KishaPayout.sol address on Base L2. */
  kishaPayoutAddress?: `0x${string}`;

  /** Treasury Safe address on Base L2 (info only; SDK doesn't write here). */
  treasurySafeAddress?: `0x${string}`;

  /** Phenotype.sol address on geth-private (S2+). Optional — when unset,
   *  the SDK reports a neutral 10_000 bps multiplier. */
  phenotypeAddress?: `0x${string}`;

  /** EtzhayyimMembership.sol address on Base L2 (per ADR-2605172600).
   *  Used by `join()` to perform the 信者 ritual leg. */
  membershipAddress?: `0x${string}`;

  /** Base L2 RPC URL. Default: `https://mainnet.base.org`. */
  baseRpcUrl?: string;

  /**
   * Officer-relayer endpoint that submits the geth-private
   * `AdherentRegistry.join` tx on behalf of the adherent (officer-only
   * call). Required when `BIConfig.officerRelayer` is unset — without
   * one, `join()` stops after the 信者 leg and reports the partial
   * state for human follow-up.
   *
   * Convention: HTTPS endpoint that accepts a JSON body
   *   { holder, did, attestationCid, membershipTxHash, baseChainId,
   *     githubCommitSha } and returns { tokenId, txHash }.
   * Out-of-band signed by an officer multisig.
   */
  officerRelayer?: {
    url: string;
    bearerToken?: string;
  };

  /**
   * viem WalletClient bound to the adherent's wallet on Base. Required
   * for `join()` Stage 1 (EtzhayyimMembership.join) and `claim()`
   * fulfillment polling. EOA wallet acceptable for v0; a future
   * upgrade swaps this for an ERC-4337 SmartAccountClient with a
   * paymaster (ADR-2605172100 §"Account model").
   */
  baseWalletClient?: WalletClient;

  /**
   * viem WalletClient bound to the adherent's wallet on geth-private.
   * Required for `claim()` Stage 1 (KishaStream.claim, holder-only).
   */
  privateWalletClient?: WalletClient;

  /**
   * @atproto/api AtpAgent bound to the adherent's PDS, with an active
   * session. Required for `join()` Stage 2 (oath AT Record write) and
   * `claim()` Stage 5 (payment.kisha AT Record write).
   */
  pdsAgent?: AtpAgent;
}

// ─── join — two-chain atomic ritual (ADR-2605172700) ────────────────

export interface JoinOpts {
  /** Adherent DID (did:web / did:plc / did:etzhayyim). */
  did: string;

  /**
   * Adherent's wallet address. Same address controls both chains
   * (ERC-4337 Smart Account derived from the DID's passkey per
   * ADR-2605172100). On geth-private it appears as the SBT holder.
   */
  holder: `0x${string}`;

  /**
   * keccak256 of the canonical oath text. The text itself is fixed by
   * ADR-2605172600's lexicon (`ai.gftd.apps.etzhayyim.oath`). The
   * adherent's signature over the text is carried inside the AT Record
   * written in Stage 2; only the hash goes on-chain.
   */
  oathHash: `0x${string}`;

  /**
   * Optional github username for the dual-permanent (Base + MEMBERS.md)
   * record. Per ADR-2605172600 the field is informational; empty string
   * accepted on-chain.
   */
  githubUsername?: string;

  /**
   * Optional reference to the MEMBERS.md PR or merged commit SHA that
   * the adherent will (or has) opened against `etzhayyim/root`. Included
   * verbatim in the AT Record body so a single document indexes both
   * chains and the github commit.
   */
  githubCommitSha?: string;
}

export interface JoinResult {
  /** SBT tokenId minted on geth-private. */
  tokenId: bigint;

  /** Base L2 tx hash of the `EtzhayyimMembership.Joined` event (信者). */
  membershipTxHash: `0x${string}`;

  /** geth-private tx hash of the `AdherentRegistry.Joined` event. */
  adherentTxHash: `0x${string}`;

  /** AT URI of the `ai.gftd.apps.etzhayyim.oath` record that bridges
   *  both chains + the github commit. */
  oathRecordUri: string;

  /** True if both chain legs landed; false if only the Base 信者 leg
   *  succeeded and the geth-private leg was skipped/failed (no officer
   *  relayer wired). */
  fullyEnrolled: boolean;
}

/**
 * Perform the two-chain membership ritual per ADR-2605172700.
 *
 *   Stage 1 — Base L2: call `EtzhayyimMembership.join(oathHash, githubUsername)`
 *             (anyone-callable, paymaster-sponsored gas). On success the
 *             adherent is a 信者; the commitment is permanently on Base
 *             and (after Stage 3 PR merges) also on github.
 *
 *   Stage 2 — PDS: write a signed `ai.gftd.apps.etzhayyim.oath` record
 *             carrying the full oath text, the DID signature, the Base
 *             chainId + Joined tx hash, the github commit SHA, and the
 *             joinedAt timestamp. The record's CID is the
 *             `attestationCid` consumed by Stage 4.
 *
 *   Stage 3 — Github: out-of-band, the adherent opens a PR to
 *             `MEMBERS.md`. This SDK does not drive the PR (it requires
 *             github auth); it returns the commit SHA placeholder for
 *             the caller to fill in before the AT Record is finalized.
 *
 *   Stage 4 — geth-private: officer-relayed call to
 *             `AdherentRegistry.join(holder, did, keccak256(oathRecordCid))`.
 *             This is the only step that needs officer privilege; the
 *             relayer is consulted via `cfg.officerRelayer` if set,
 *             otherwise the call returns `fullyEnrolled=false` with the
 *             Stage 1+2 receipts so a human can complete the enrollment
 *             through the standard officer flow.
 *
 * If Stage 1 succeeds and Stage 4 fails (network / officer down / etc.),
 * the 信者 state on Base is *not* rolled back — that's the intended
 * semantic per ADR-2605172600 (信者 is permanent and self-sovereign;
 * Adherent is a later additive layer). Re-running `join()` is
 * idempotent: Stage 1 will revert `AlreadyMember`, Stage 2 dedupes
 * by content, Stage 4 retries the officer-relayer call.
 */
export async function join(opts: JoinOpts, cfg: BIConfig): Promise<JoinResult> {
  // ─── precondition checks (kept as runtime errors so the SDK fails
  //     loudly rather than producing partial state silently) ─────────
  if (!cfg.membershipAddress) {
    throw new Error("[etzhayyim-sdk/bi] join: cfg.membershipAddress required (Base L2)");
  }
  if (!cfg.registryAddress) {
    throw new Error("[etzhayyim-sdk/bi] join: cfg.registryAddress required (geth-private)");
  }
  if (!opts.holder || !/^0x[0-9a-fA-F]{40}$/.test(opts.holder)) {
    throw new Error("[etzhayyim-sdk/bi] join: holder must be a 0x-prefixed address");
  }
  if (!opts.oathHash || !/^0x[0-9a-fA-F]{64}$/.test(opts.oathHash)) {
    throw new Error("[etzhayyim-sdk/bi] join: oathHash must be a 0x-prefixed 32-byte hex");
  }

  // ─── Stage 1: Base L2 EtzhayyimMembership.join ──────────────────────
  //   Reuses the same paymaster-sponsored ERC-4337 path as pay.ts.
  //   See pay.ts `pay()` for the eventual viem wiring; here we delegate
  //   to a future low-level helper.
  const baseRpc = cfg.baseRpcUrl ?? "https://mainnet.base.org";
  const baseChainId = cfg.baseWalletClient?.chain?.id ?? 8453;
  const membershipTxHash = await _baseJoin(
    {
      membership: cfg.membershipAddress,
      rpcUrl: baseRpc,
      holder: opts.holder,
      oathHash: opts.oathHash,
      githubUsername: opts.githubUsername ?? "",
    },
    cfg
  );

  // ─── Stage 2: AT Record (ai.gftd.apps.etzhayyim.oath) ──────────────
  const {recordUri, recordCid} = await _writeOathRecord(
    {
      did: opts.did,
      holder: opts.holder,
      oathHash: opts.oathHash,
      baseChainId,
      membershipTxHash,
      githubUsername: opts.githubUsername ?? "",
      githubCommitSha: opts.githubCommitSha ?? "",
    },
    cfg
  );
  const attestationCid = recordCid;

  // ─── Stage 3: Github MEMBERS.md PR — out-of-band, caller's responsibility ─
  //   We do not drive the PR. The Stage 2 record carries
  //   `githubCommitSha` (which may be empty pre-merge); after the user
  //   opens the PR, they can re-call `join` to update the record. For
  //   the canonical reading of "fully enrolled", the github leg can be
  //   verified by an auditor reading the AT Record.

  // ─── Stage 4: officer-relayed AdherentRegistry.join ─────────────────
  if (!cfg.officerRelayer) {
    return {
      tokenId: 0n,
      membershipTxHash,
      adherentTxHash: "0x0000000000000000000000000000000000000000000000000000000000000000",
      oathRecordUri: recordUri,
      fullyEnrolled: false,
    };
  }
  const {tokenId, txHash: adherentTxHash} = await _officerRelayJoin({
    relayer: cfg.officerRelayer,
    registry: cfg.registryAddress,
    holder: opts.holder,
    did: opts.did,
    attestationCid,
    membershipTxHash,
    baseChainId,
    githubCommitSha: opts.githubCommitSha ?? "",
  });

  return {
    tokenId,
    membershipTxHash,
    adherentTxHash,
    oathRecordUri: recordUri,
    fullyEnrolled: true,
  };
}

// ─── Low-level helpers for join() — viem wiring intentionally deferred
//     to a follow-up so the SDK stays compilable without viem providers
//     bound. The shape pins the contract; production glue plugs in here.

interface _BaseJoinIn {
  membership: `0x${string}`;
  rpcUrl: string;
  holder: `0x${string}`;
  oathHash: `0x${string}`;
  githubUsername: string;
}

async function _baseJoin(args: _BaseJoinIn, cfg: BIConfig): Promise<`0x${string}`> {
  if (!cfg.baseWalletClient) {
    throw new Error(
      "[etzhayyim-sdk/bi] _baseJoin: cfg.baseWalletClient required " +
        "(a viem WalletClient bound to the adherent's Base wallet). " +
        "Future upgrade: ERC-4337 SmartAccountClient + paymaster."
    );
  }
  if (!cfg.baseWalletClient.account) {
    throw new Error("[etzhayyim-sdk/bi] _baseJoin: walletClient has no account");
  }
  const pub = createPublicClient({transport: http(args.rpcUrl)});
  // EtzhayyimMembership.join writes msg.sender's slot, so the wallet
  // account MUST equal the adherent's holder address. Sanity-check.
  const sender = cfg.baseWalletClient.account.address.toLowerCase();
  if (sender !== args.holder.toLowerCase()) {
    throw new Error(
      `[etzhayyim-sdk/bi] _baseJoin: walletClient account ${sender} ` +
        `does not match opts.holder ${args.holder.toLowerCase()}; ` +
        "EtzhayyimMembership.join binds msg.sender = member."
    );
  }
  const hash = await cfg.baseWalletClient.writeContract({
    account: cfg.baseWalletClient.account,
    chain: cfg.baseWalletClient.chain ?? null,
    address: args.membership,
    abi: ETZHAYYIM_MEMBERSHIP_ABI,
    functionName: "join",
    args: [args.oathHash, args.githubUsername],
  });
  const receipt = await pub.waitForTransactionReceipt({hash});
  if (receipt.status !== "success") {
    throw new Error(
      `[etzhayyim-sdk/bi] _baseJoin: tx ${hash} reverted; check that the ` +
        "wallet is not already a 信者 (EtzhayyimMembership.AlreadyMember)"
    );
  }
  return hash;
}

interface _OathRecordIn {
  did: string;
  holder: `0x${string}`;
  oathHash: `0x${string}`;
  baseChainId: number;
  membershipTxHash: `0x${string}`;
  githubUsername: string;
  githubCommitSha: string;
}

/** Canonical oath text per ADR-2605172600 (both languages equivalent). */
export const CANONICAL_OATH_TEXT = [
  "我、etzhayyim の信者として、生命の樹 (עץ חיים) の支柱の一として、自らの行いと意思を、永続的な公開記録 (blockchain と github) として残すことを誓う。",
  "",
  "I, as a 信者 (follower) of etzhayyim, as one of the pillars of the Tree of Life (עץ חיים), swear to leave my acts and intentions as a permanent public record (blockchain and github).",
].join("\n");

async function _writeOathRecord(
  args: _OathRecordIn,
  cfg: BIConfig
): Promise<{recordUri: string; recordCid: string}> {
  if (!cfg.pdsAgent) {
    throw new Error(
      "[etzhayyim-sdk/bi] _writeOathRecord: cfg.pdsAgent required " +
        "(AtpAgent with an active session bound to the adherent's DID)"
    );
  }
  const session = cfg.pdsAgent.session;
  if (!session || session.did !== args.did) {
    throw new Error(
      "[etzhayyim-sdk/bi] _writeOathRecord: pdsAgent session DID " +
        `(${session?.did ?? "none"}) does not match opts.did ${args.did}`
    );
  }
  // The record body is the lexicon-defined shape. The lexicon itself
  // lives at 00-contracts/lexicons/ai/gftd/apps/etzhayyim/oath.json
  // (per ADR-2605172600 § Phase 1).
  const record = {
    $type: OATH_RECORD_NSID,
    oathText: CANONICAL_OATH_TEXT,
    oathHash: args.oathHash,
    holder: args.holder,
    baseChainId: args.baseChainId,
    membershipTxHash: args.membershipTxHash,
    githubUsername: args.githubUsername,
    githubCommitSha: args.githubCommitSha,
    joinedAt: new Date().toISOString(),
  };
  const created = await cfg.pdsAgent.com.atproto.repo.createRecord({
    repo: args.did,
    collection: OATH_RECORD_NSID,
    record,
  });
  return {recordUri: created.data.uri, recordCid: created.data.cid};
}

interface _OfficerRelayIn {
  relayer: {url: string; bearerToken?: string};
  registry: `0x${string}`;
  holder: `0x${string}`;
  did: string;
  attestationCid: string;
  membershipTxHash: `0x${string}`;
  baseChainId: number;
  githubCommitSha: string;
}

async function _officerRelayJoin(
  args: _OfficerRelayIn
): Promise<{tokenId: bigint; txHash: `0x${string}`}> {
  // The officer relayer is an HTTPS endpoint; the SDK posts the payload
  // and the relayer signs + submits the AdherentRegistry.join tx on
  // geth-private. The contract checks `msg.sender == isOfficer` on the
  // chain side; the relayer's authority is its officer-multisig
  // signing key.
  const body = {
    holder: args.holder,
    did: args.did,
    attestationCid: args.attestationCid,
    registry: args.registry,
    membershipTxHash: args.membershipTxHash,
    baseChainId: args.baseChainId,
    githubCommitSha: args.githubCommitSha,
  };
  const res = await fetch(args.relayer.url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(args.relayer.bearerToken
        ? {Authorization: `Bearer ${args.relayer.bearerToken}`}
        : {}),
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(
      `[etzhayyim-sdk/bi] officer relayer ${args.relayer.url} returned ${res.status}: ${text}`
    );
  }
  const out = (await res.json()) as {tokenId: string; txHash: `0x${string}`};
  return {tokenId: BigInt(out.tokenId), txHash: out.txHash};
}

// ─── attest ─────────────────────────────────────────────────────────

export interface AttestOpts {
  tokenId: bigint;
  eventType: AttestationEventType;
  /** Optional IPFS CID of evidence (encrypted-to-passkey by default). */
  evidenceCid?: string;
}

export interface AttestResult {
  txHash: `0x${string}`;
  /** AT URI of the corresponding event record on the adherent's PDS. */
  recordUri: string;
}

export async function attest(_opts: AttestOpts, _cfg: BIConfig): Promise<AttestResult> {
  throw new Error(
    "[etzhayyim-sdk/bi] attest() TODO: " +
      "(1) create com.etzhayyim.event.<eventType> AT Record (encrypt evidence if private), " +
      "(2) call AdherentRegistry.attest(tokenId, keccak256(eventType), keccak256(evidenceCid)) — " +
      "    paymaster-sponsored if available, otherwise officer-relayed, " +
      "(3) MST commit + anchor enqueue."
  );
}

// ─── status ─────────────────────────────────────────────────────────

export interface KishaStatus {
  /** SBT tokenId. */
  tokenId: bigint;
  /** Unix seconds of join. */
  adherentSince: bigint;
  /** Most recent attest call (0 if never). */
  lastAttestedAt: bigint;
  /** True if attested within Constitution.active_window_secs. */
  isActive: boolean;
  /** Current base rate in USDC base units (6 decimals) per day. */
  baseRatePerDay: bigint;
  /** Phenotype multiplier (S2+). 10_000 = 1.0×; 5_000 = 0.5×. */
  phenotypeMultiplierBps: number;
  /** Currently claimable amount in USDC base units. */
  claimable: bigint;
  /** Total kisha claimed historically in USDC base units. */
  claimedTotal: bigint;
}

export async function status(_tokenId: bigint, _cfg: BIConfig): Promise<KishaStatus> {
  throw new Error(
    "[etzhayyim-sdk/bi] status() TODO: " +
      "(1) read AdherentRegistry.getRecord(tokenId), " +
      "(2) read KishaStream.baseRatePerDay + .accruedNow(tokenId), " +
      "(3) (S2) if cfg.phenotypeAddress set, read Phenotype.getMultiplierBps(tokenId); " +
      "    else default to 10_000, " +
      "(4) aggregate Fulfilled(ticketId, tokenId, ...) events from KishaPayout for claimedTotal, " +
      "(5) assemble KishaStatus."
  );
}

// ─── Phenotype — cell-signed multiplier update (S2) ─────────────────

export interface PhenotypeUpdateInput {
  tokenId: bigint;
  /** Multiplier in basis points, bounded by Constitution band (5000..20000). */
  bps: number;
  /** Cell-supplied epoch (Pregel super-step number). */
  epoch: bigint;
  /** Optional IPFS CID hash of the evidence record (32-byte). */
  evidenceHash?: `0x${string}`;
  /** Signature TTL from now, in seconds. Default 600. */
  ttlSecs?: number;
}

export interface PhenotypeUpdateResult {
  txHash: `0x${string}`;
  oldBps: number;
  newBps: number;
}

/**
 * Submit a cell-signed phenotype update. Caller MUST be running with
 * a signer registered as a cell in `Phenotype.sol` (registered via
 * `Phenotype.registerCell` by governance).
 *
 * In typical operation this is NOT called by app code — the Pregel
 * `EligibilityCell` (Python, at
 * `20-actors/magatama/py/src/pymagatama/eligibility/cell.py`)
 * computes the multiplier and submits it directly via web3.py. This
 * SDK function exists for TypeScript-side test rigs and dashboard
 * tooling that want to issue cell updates from the same process that
 * holds the cell key.
 */
export async function setPhenotype(
  _input: PhenotypeUpdateInput,
  _cfg: BIConfig
): Promise<PhenotypeUpdateResult> {
  throw new Error(
    "[etzhayyim-sdk/bi] setPhenotype() TODO: " +
      "(1) read Phenotype.expectedNonce(cell) on geth-private, " +
      "(2) build payloadHash matching Phenotype.payloadHash, " +
      "(3) sign EIP-191 envelope with the cell key, " +
      "(4) submit Phenotype.setMultiplier(tokenId, bps, epoch, nonce, expiresAt, evidenceHash, cell, sig), " +
      "(5) parse MultiplierSet(tokenId, cell, oldBps, newBps, epoch, ...) event."
  );
}

// ─── claim ──────────────────────────────────────────────────────────

export interface ClaimOpts {
  tokenId: bigint;
  /** Base L2 address that will receive USDC. Defaults to adherent's Smart Wallet. */
  baseRecipient?: `0x${string}`;
  /** Optional cap on amount in USDC base units. 0 = claim full accrued. */
  maxAmount?: bigint;
}

export interface ClaimResult {
  /** Ticket id emitted by KishaStream on geth-private. */
  ticketId: `0x${string}`;
  /** geth-private tx hash for the claim() call. */
  privateTxHash: `0x${string}`;
  /** Amount issued by KishaStream (≤ accrued, ≤ maxAmount). */
  amount: bigint;
  /** Promise that resolves once Base KishaPayout.Fulfilled is observed. */
  fulfilled: Promise<PaymentReceipt>;
}

export async function claim(opts: ClaimOpts, cfg: BIConfig): Promise<ClaimResult> {
  // ─── Precondition checks ───────────────────────────────────────────
  if (!cfg.privateWalletClient) {
    throw new Error("[etzhayyim-sdk/bi] claim: cfg.privateWalletClient required (geth-private wallet)");
  }
  if (!cfg.privateWalletClient.account) {
    throw new Error("[etzhayyim-sdk/bi] claim: privateWalletClient has no account");
  }
  if (!cfg.kishaStreamAddress) {
    throw new Error("[etzhayyim-sdk/bi] claim: cfg.kishaStreamAddress required");
  }
  if (!cfg.kishaPayoutAddress) {
    throw new Error("[etzhayyim-sdk/bi] claim: cfg.kishaPayoutAddress required (for fulfillment polling)");
  }
  if (!cfg.privateRpcUrl) {
    throw new Error("[etzhayyim-sdk/bi] claim: cfg.privateRpcUrl required");
  }

  const privateWallet = cfg.privateWalletClient;
  const account = privateWallet.account!;
  const baseRecipient: Address = opts.baseRecipient ?? (account.address as Address);
  const maxAmount: bigint = opts.maxAmount ?? 0n;

  const privatePub: PublicClient = createPublicClient({transport: http(cfg.privateRpcUrl)});

  // ─── Stage 1: KishaStream.claim on geth-private ────────────────────
  const privateTxHash: Hash = await privateWallet.writeContract({
    account,
    chain: privateWallet.chain ?? null,
    address: cfg.kishaStreamAddress,
    abi: KISHA_STREAM_ABI,
    functionName: "claim",
    args: [opts.tokenId, baseRecipient, maxAmount],
  });
  const privateReceipt = await privatePub.waitForTransactionReceipt({hash: privateTxHash});
  if (privateReceipt.status !== "success") {
    throw new Error(
      `[etzhayyim-sdk/bi] claim: KishaStream.claim tx ${privateTxHash} reverted; ` +
        "likely NotHolder / TokenRevoked / NotActive / NothingAccrued — see KISHA_STREAM_ABI for typed errors"
    );
  }

  // ─── Stage 2: decode ClaimTicketIssued ─────────────────────────────
  const ticketLog = privateReceipt.logs.find(
    (l) => l.address.toLowerCase() === cfg.kishaStreamAddress!.toLowerCase()
  );
  if (!ticketLog) {
    throw new Error("[etzhayyim-sdk/bi] claim: ClaimTicketIssued log missing from receipt");
  }
  const decoded = decodeEventLog({
    abi: KISHA_STREAM_ABI,
    eventName: "ClaimTicketIssued",
    data: ticketLog.data,
    topics: ticketLog.topics,
  });
  const eventArgs = decoded.args as {
    ticketId: `0x${string}`;
    tokenId: bigint;
    holder: Address;
    baseRecipient: Address;
    amount: bigint;
    claimSeq: bigint;
    issuedAt: bigint;
    expiresAt: bigint;
  };
  const ticketId = eventArgs.ticketId;
  const amount = eventArgs.amount;
  const expiresAt = Number(eventArgs.expiresAt);

  // ─── Stage 3: fulfillment Promise ──────────────────────────────────
  // The relayer is off-chain and out of this SDK's control. We watch
  // Base for the matching `Fulfilled(ticketId, ...)` event and resolve
  // once it lands. Caller awaits at their convenience.
  const fulfilled: Promise<PaymentReceipt> = _waitForFulfillment({
    cfg,
    ticketId,
    expiresAt,
    privateTxHash,
  });

  return {ticketId, privateTxHash, amount, fulfilled};
}

// ─── claim() fulfillment helper ─────────────────────────────────────

interface _WaitForFulfillmentIn {
  cfg: BIConfig;
  ticketId: `0x${string}`;
  expiresAt: number; // unix seconds
  privateTxHash: Hash;
}

async function _waitForFulfillment(args: _WaitForFulfillmentIn): Promise<PaymentReceipt> {
  const cfg = args.cfg;
  if (!cfg.kishaPayoutAddress) {
    throw new Error("[etzhayyim-sdk/bi] _waitForFulfillment: cfg.kishaPayoutAddress required");
  }
  const baseRpc = cfg.baseRpcUrl ?? "https://mainnet.base.org";
  const basePub: PublicClient = createPublicClient({transport: http(baseRpc)});

  // Poll for the Fulfilled event keyed on ticketId. Short-circuit if
  // the ticket TTL has already lapsed; in that case the relayer is
  // either down or the ticket was never submitted, and the caller can
  // call `claim()` again to mint a fresh ticket.
  const pollIntervalMs = 5_000;
  const deadlineMs = Date.now() + Math.max(0, args.expiresAt - Math.floor(Date.now() / 1000)) * 1000;
  while (Date.now() < deadlineMs) {
    const logs = await basePub.getLogs({
      address: cfg.kishaPayoutAddress,
      event: FULFILLED_EVENT,
      args: {ticketId: args.ticketId},
      fromBlock: "earliest",
      toBlock: "latest",
    });
    if (logs.length > 0) {
      const hit = logs[0];
      // Optional Stage 5: write ai.gftd.apps.payment.kisha record if the
      // SDK has a PDS agent. Skipped silently when no agent is bound —
      // the public audit record then comes only from the on-chain
      // Fulfilled event.
      let recordUri = "";
      if (cfg.pdsAgent && cfg.pdsAgent.session) {
        try {
          const created = await cfg.pdsAgent.com.atproto.repo.createRecord({
            repo: cfg.pdsAgent.session.did,
            collection: "ai.gftd.apps.payment.kisha",
            record: {
              $type: "ai.gftd.apps.payment.kisha",
              ticketId: args.ticketId,
              privateTxHash: args.privateTxHash,
              baseTxHash: hit.transactionHash,
              baseBlockNumber: Number(hit.blockNumber ?? 0),
              fulfilledAt: new Date().toISOString(),
            },
          });
          recordUri = created.data.uri;
        } catch {
          // Audit record is best-effort; on-chain Fulfilled remains canonical.
        }
      }
      return {
        txHash: hit.transactionHash as `0x${string}`,
        blockNumber: hit.blockNumber ?? 0n,
        recordUri,
        atomicBatch: false,
      };
    }
    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
  }
  throw new Error(
    `[etzhayyim-sdk/bi] claim: fulfillment for ticket ${args.ticketId} did not land before expiry. ` +
      "Relayer is either down, throttled, or the ticket was rejected. " +
      "Re-call claim() to mint a fresh ticket."
  );
}

// ─── propose / vote (S3, stubbed for shape) ─────────────────────────

export type ConstitutionalChange =
  | "kisha_base_rate"
  | "kappa_bps"
  | "tier_liquid_bps"
  | "tier_reserve_bps"
  | "tier_corpus_bps"
  | "quorum_bps"
  | "active_window_secs"
  | "timelock_secs";

export interface ProposeOpts {
  change: ConstitutionalChange;
  from: bigint;
  to: bigint;
  rationale: string;
}

export async function propose(_opts: ProposeOpts, _cfg: BIConfig): Promise<bigint> {
  throw new Error(
    "[etzhayyim-sdk/bi] propose() TODO (S3): " +
      "encode Constitution.setMutable(<keccak(change)>, bytes32(to)) as a Governance proposal, " +
      "submit Governance.propose(...), return proposalId."
  );
}

export async function vote(_proposalId: bigint, _choice: "for" | "against" | "abstain", _cfg: BIConfig): Promise<void> {
  throw new Error(
    "[etzhayyim-sdk/bi] vote() TODO (S3): call Governance.castVote(proposalId, choice)."
  );
}
