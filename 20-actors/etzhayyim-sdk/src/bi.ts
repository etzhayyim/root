/**
 * @etzhayyim/sdk/bi — Basic-income (kisha) + adherent registry helpers.
 *
 * Status: scaffold. Stubs only. See ADR-2605172300 §6.
 *
 * Composition: the SDK speaks to two chains.
 *   - geth-private (ChainID 2605): AdherentRegistry, KishaStream,
 *     AnchorBridge, Constitution, Governance (S3+).
 *   - Base L2:                     KishaPayout, Treasury Safe (USDC).
 *
 * The two-chain plumbing is internal to this module; callers see a
 * single coherent surface: join → attest → status → claim.
 */

import type {PaymentReceipt} from "./pay.js";

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
}

// ─── join ───────────────────────────────────────────────────────────

export interface JoinOpts {
  /** Adherent DID (did:web / did:plc / did:etzhayyim). */
  did: string;

  /**
   * IPFS CID of the creed-acceptance attestation document.
   * The doc must be signed by the DID controller off-chain.
   */
  attestationCid: string;

  /** Adherent's wallet address on geth-private. */
  holder: `0x${string}`;
}

export interface JoinResult {
  /** SBT tokenId minted in AdherentRegistry. */
  tokenId: bigint;

  /** geth-private tx hash of the Joined event. */
  txHash: `0x${string}`;
}

export async function join(_opts: JoinOpts, _cfg: BIConfig): Promise<JoinResult> {
  throw new Error(
    "[etzhayyim-sdk/bi] join() TODO: " +
      "(1) verify creed-acceptance attestation is signed by `did`'s key, " +
      "(2) call AdherentRegistry.join(holder, did, keccak256(attestationCid)) via an officer-relayer tx, " +
      "(3) parse Joined(tokenId, holder, did, attestationCid) event, " +
      "(4) write ai.gftd.apps.adherent.joined AT Record on the adherent's PDS, " +
      "(5) enqueue MST root for next anchor batch."
  );
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

export async function claim(_opts: ClaimOpts, _cfg: BIConfig): Promise<ClaimResult> {
  throw new Error(
    "[etzhayyim-sdk/bi] claim() TODO: " +
      "(1) call KishaStream.claim(tokenId, baseRecipient, maxAmount) on geth-private; " +
      "    paymaster-sponsored if available, otherwise officer-relayed, " +
      "(2) parse ClaimTicketIssued event → ticketId, amount, expiresAt, " +
      "(3) request fulfillment from the relayer service (REST or AT messaging): " +
      "    relayer collects M-of-N officer signatures, submits KishaPayout.fulfill on Base, " +
      "(4) await Fulfilled event on Base, " +
      "(5) create ai.gftd.apps.payment.kisha AT Record citing privateTxHash + base tx, " +
      "(6) anchor enqueue. The `fulfilled` promise resolves with a PaymentReceipt."
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
