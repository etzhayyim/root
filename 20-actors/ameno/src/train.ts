/**
 * @etzhayyim/ameno/train — Browser-side LoRA-only training for baien.
 *
 * Scaffold v0.1.0. Implements the L2 layer of ADR-2605242600. The
 * full WebGPU autograd path, OPFS-backed Adam state, DP clip + Gaussian
 * noise, and ES256 passkey signing land in R1; today this module
 * exposes the public type surface and stubs that throw on use so the
 * ameno appview compiles and a future "Train" UI panel can render
 * without runtime errors as long as the user does not start a round.
 *
 * Constitutional invariants (enforced at runtime once R1 lands):
 *   - Trunk + modality encoders frozen (ADR-2605241900 G1).
 *   - Only LoRA A (in×r) / B (r×out) over q/k/v/o_proj are trainable
 *     (ADR-2605242600 G2).
 *   - charter_rider.scan() runs on the shard BEFORE the first step
 *     (G6); rounds with >5% drop are aborted device-side.
 *   - DP clip + Gaussian noise applied on-device, NOT at the aggregator
 *     (server-side DP would require trusting the aggregator with raw
 *     gradients; ADR-2605242600 §2 L2 step 6).
 *   - Delta is signed with the member's passkey-derived ES256 key
 *     (ADR-2605231525); no server-issued token is ever accepted.
 */

export type TrainDeviceClass = "ios" | "android" | "wasm-desktop";

/** LoRA training hyperparameters. Defaults mirror ADR-2605231300 §LoRA. */
export interface LoraTrainConfig {
  rank: number;
  alpha: number;
  dropout: number;
  /** Adam learning rate. */
  learningRate: number;
  /** Number of micro-batch=1 steps to run this round. */
  stepCount: number;
  /** L2 clip threshold τ for differential privacy. */
  dpClipTau: number;
  /** Gaussian noise σ added after clipping. */
  dpNoiseSigma: number;
  /** Target modules — fixed to q/k/v/o_proj per G2; included for visibility. */
  targetModules: readonly string[];
}

export const TRAIN_DEFAULTS: LoraTrainConfig = {
  rank: 16,
  alpha: 32,
  dropout: 0.05,
  learningRate: 2e-4,
  stepCount: 50,
  dpClipTau: 1.0,
  dpNoiseSigma: 0.01,
  targetModules: ["q_proj", "k_proj", "v_proj", "o_proj"],
} as const;

/** Per-device step-count budget (ADR-2605242600 §2 L2 step 4). */
export const DEVICE_STEP_BUDGET: Record<TrainDeviceClass, number> = {
  ios: 50,
  android: 30,
  "wasm-desktop": 500,
} as const;

export interface TrainShardRef {
  /** IPFS CID of the dataset shard (resolved via app.etzhayyim.substrate.datasetPin). */
  datasetShardCid: string;
  /** Size in bytes; informational. */
  sizeBytes: number;
}

export interface RoundContext {
  /** IPFS CID of the frozen trunk + encoders for this round (round-frozen per G10). */
  baseModelCid: string;
  /** IPFS CID of the adapter the device starts from. Empty-adapter CID for iter=0. */
  prevAdapterCid: string;
  /** Monotonic round counter per (actorDid, baseModelCid). */
  iter: number;
  /** Caller DID (Adherent SBT holder per G7); used only for receipt/manifest. */
  actorDid: string;
  /** Detected device class for the step-count budget + receipt deviceClass field. */
  deviceClass: TrainDeviceClass;
}

export interface CharterRiderScanResult {
  /** Total rows in the shard. */
  totalRows: number;
  /** Rows the scanner rejected (per ADR-2605192200 §2(a)..(h)). */
  rejectedRows: number;
  /** True iff (rejectedRows / totalRows) <= 0.05. */
  passed: boolean;
  /** Sample of rejected row evidence (truncated to keep the manifest small). */
  evidenceSample: ReadonlyArray<{ category: string; evidence: string }>;
}

export interface TrainRoundResult {
  /** Mean eval-microbench loss BEFORE the training step. Scaled by 1_000_000 to match the lexicon (integer-only) on the wire. */
  lossBefore: number;
  /** Mean eval-microbench loss AFTER the training step. Same scaling as lossBefore. */
  lossAfter: number;
  /** L2 norm of the on-device DP-clipped delta. Scaled by 1_000_000 to match the lexicon. */
  gradNormL2: number;
  /** IPFS CID of the safetensors blob containing the delta. */
  deltaCid: string;
  /** Steps actually performed (may be < config.stepCount if thermal-throttled). */
  stepsCompleted: number;
  /** Scanner result for the shard. */
  scanner: CharterRiderScanResult;
}

export interface SignedDeltaManifest {
  v: 1;
  actorDid: string;
  baseModelCid: string;
  datasetShardCid: string;
  prevAdapterCid: string;
  deltaCid: string;
  iter: number;
  stepCount: number;
  deviceClass: TrainDeviceClass;
  /** Scaled by 1_000_000 ('micro-loss' units); the lexicon forbids floats. */
  lossBefore: number;
  /** Scaled by 1_000_000 ('micro-loss' units); same units as lossBefore. */
  lossAfter: number;
  /** Scaled by 1_000_000 ('micro-norm' units); the lexicon forbids floats. */
  gradNormL2: number;
  scannerPass: boolean;
  trainedAt: string;
  /** ES256 signature over canonical JSON of the preceding fields. */
  sig: string;
}

/**
 * Run a single federated training round for baien on this device.
 *
 * Order of operations (mirrors ADR-2605242600 §2 L2):
 *   1. Pull `shard.datasetShardCid` from IPFS into OPFS.
 *   2. `charter_rider.scan()` — abort the round if >5% rows are rejected.
 *   3. Pre-eval pass → `lossBefore`.
 *   4. WebGPU LoRA-only autograd, `stepCount` micro-batch=1 steps.
 *   5. Post-eval pass → `lossAfter`.
 *   6. DP clip + Gaussian noise on the in-memory delta.
 *   7. Serialise delta to safetensors; pin to IPFS; record `deltaCid`.
 *
 * NOTE: R0 scaffold — throws. Real implementation lands in R1
 * after iPhone 12 WebGPU backward-pass numerics are validated.
 */
export async function runFederatedRound(
  _ctx: RoundContext,
  _shard: TrainShardRef,
  _config: LoraTrainConfig = TRAIN_DEFAULTS,
): Promise<TrainRoundResult> {
  throw new Error(
    "runFederatedRound: not yet implemented in 0.1.0 scaffold; activates in R1 (ADR-2605242600)",
  );
}

/**
 * Sign the round's manifest with the member's passkey-derived ES256
 * key (ADR-2605231525). The platform MUST hold the private key; this
 * function is only the canonicalisation + WebAuthn `sign` wrapper.
 *
 * NOTE: R0 scaffold — throws. Real implementation lands in R1.
 */
export async function signDeltaManifest(
  _manifest: Omit<SignedDeltaManifest, "sig">,
): Promise<SignedDeltaManifest> {
  throw new Error(
    "signDeltaManifest: not yet implemented in 0.1.0 scaffold; activates in R1 (ADR-2605242600)",
  );
}

/**
 * Publish the signed delta record to the contributor's AT repo under
 * the lexicon `app.etzhayyim.baien.distributedTrainDelta`. The
 * aggregator subscribes to the firehose and picks it up from there.
 *
 * NOTE: R0 scaffold — throws. Real implementation lands in R1.
 */
export async function publishDeltaRecord(
  _signed: SignedDeltaManifest,
): Promise<{ uri: string; cid: string }> {
  throw new Error(
    "publishDeltaRecord: not yet implemented in 0.1.0 scaffold; activates in R1 (ADR-2605242600)",
  );
}

/**
 * Probe the running environment and return the device class. Defaults
 * to `wasm-desktop` for non-mobile WebGPU contexts. The probe runs
 * before any training-step budget decision.
 *
 * NOTE: R0 scaffold — throws. Real implementation lands in R1.
 */
export function detectDeviceClass(): TrainDeviceClass {
  throw new Error(
    "detectDeviceClass: not yet implemented in 0.1.0 scaffold; activates in R1 (ADR-2605242600)",
  );
}
