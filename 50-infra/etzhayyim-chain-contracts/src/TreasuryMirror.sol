// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {Constitution} from "./Constitution.sol";

/**
 * @title TreasuryMirror
 * @notice On-chain (geth-private) accounting mirror of the off-chain
 *         Treasury Safe on Base. Stores per-tier NAV updates supplied
 *         by registered oracles, and computes the constitutional kisha
 *         envelope from the reserve-tier 3-year rolling average × κ.
 *         Per ADR-2605172300 §2.TreasuryMirror + §4. Apache-2.0.
 *
 * @dev The Base Safe is the canonical custody. This contract is purely
 *      a witness: an oracle posts signed NAV samples here so geth-
 *      private contracts (governance proposals, KishaStream policy)
 *      can read NAV without depending on a Base RPC.
 *
 *      Tiers (ADR-2605172300 §4):
 *        0 = 流動 (liquid)   — USDC, payout source
 *        1 = 準備 (reserve)  — yield-bearing (USDY / sDAI / aUSDC),
 *                              feeds the kisha envelope
 *        2 = 本財 (corpus)   — RWA SBT wrappers, untouchable principal
 *
 *      Spending rule:
 *        annualEnvelope = trailing3yrAvg(reserveNAV) × κ_bps / 10_000
 *        monthlyEnvelope = annualEnvelope / 12
 *
 *        κ floor and ceiling are constitutional constants
 *        (kappa_floor_bps / kappa_ceiling_bps); the current κ
 *        (kappa_bps) is governance-mutable within the band.
 *
 *      Sample retention:
 *        - Each tier keeps a circular buffer of weekly samples
 *          (52 × 3 = 156 slots) for the 3-yr rolling average. Older
 *          samples are overwritten.
 *
 *      Trust model:
 *        - Oracle set is governance-managed (registered via this
 *          contract from a Governance-executed call).
 *        - Each sample is EIP-191 signed by the oracle EOA. Per-oracle
 *          nonces prevent replay.
 *        - Even a hostile oracle cannot exceed the κ ceiling because
 *          the envelope is `min(envelope, hardCeiling)` at read time.
 */
contract TreasuryMirror {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error NotGovernance();
    error UnknownOracle(address oracle);
    error AlreadyRegistered(address oracle);
    error InvalidTier(uint8 tier);
    error ExpiredSignature();
    error InvalidSignature();
    error BadNonce(uint64 expected, uint64 given);

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event OracleRegistered(address indexed oracle, bytes32 indexed labelHash);
    event OracleRevoked(address indexed oracle, bytes32 reasonCid);
    event NavUpdated(
        uint8 indexed tier,
        uint256 amountUsdc,   // 6-decimal USDC base units
        address indexed oracle,
        uint64 sampleEpoch,
        uint16 slot           // current ring-buffer slot
    );

    // -------------------------------------------------------------------
    // Tiers + ring buffer
    // -------------------------------------------------------------------

    uint8 public constant TIER_LIQUID  = 0;
    uint8 public constant TIER_RESERVE = 1;
    uint8 public constant TIER_CORPUS  = 2;
    uint8 public constant TIER_COUNT   = 3;

    /// @notice 3-year rolling average sample count (weekly cadence target).
    uint16 public constant SAMPLE_SLOTS = 156;

    // -------------------------------------------------------------------
    // Constitutional keys
    // -------------------------------------------------------------------

    bytes32 private constant K_KAPPA_BPS         = keccak256("kappa_bps");
    bytes32 private constant K_KAPPA_FLOOR_BPS   = keccak256("kappa_floor_bps");
    bytes32 private constant K_KAPPA_CEILING_BPS = keccak256("kappa_ceiling_bps");

    // -------------------------------------------------------------------
    // Immutable wiring
    // -------------------------------------------------------------------

    Constitution public immutable constitution;

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    mapping(address => bool)   public isOracle;
    mapping(address => uint64) public oracleNonce;

    struct TierState {
        uint256 latest;             // most recent posted amount
        uint64  lastUpdatedAt;
        uint16  slot;               // next ring-buffer write slot
        uint16  filled;             // count of slots filled (≤ SAMPLE_SLOTS)
    }

    mapping(uint8 => TierState) private _tier;
    mapping(uint8 => uint256[SAMPLE_SLOTS]) private _samples;

    // -------------------------------------------------------------------
    // Construction
    // -------------------------------------------------------------------

    constructor(Constitution constitution_) {
        constitution = constitution_;
    }

    // -------------------------------------------------------------------
    // Oracle-set management (governance-only)
    // -------------------------------------------------------------------

    modifier onlyGovernance() {
        if (msg.sender != constitution.governance()) revert NotGovernance();
        _;
    }

    function registerOracle(address oracle, bytes32 labelHash) external onlyGovernance {
        if (isOracle[oracle]) revert AlreadyRegistered(oracle);
        isOracle[oracle] = true;
        emit OracleRegistered(oracle, labelHash);
    }

    function revokeOracle(address oracle, bytes32 reasonCid) external onlyGovernance {
        if (!isOracle[oracle]) revert UnknownOracle(oracle);
        isOracle[oracle] = false;
        emit OracleRevoked(oracle, reasonCid);
    }

    // -------------------------------------------------------------------
    // NAV update — oracle-signed, EIP-191
    // -------------------------------------------------------------------

    function updateNAV(
        uint8 tier,
        uint256 amountUsdc,
        uint64 sampleEpoch,
        uint64 nonce,
        uint64 expiresAt,
        address oracle,
        bytes calldata sig
    ) external {
        if (tier >= TIER_COUNT) revert InvalidTier(tier);
        if (!isOracle[oracle]) revert UnknownOracle(oracle);
        if (block.timestamp > expiresAt) revert ExpiredSignature();
        if (oracleNonce[oracle] != nonce) revert BadNonce(oracleNonce[oracle], nonce);

        bytes32 h = payloadHash(tier, amountUsdc, sampleEpoch, nonce, expiresAt, oracle);
        bytes32 envelope = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", h));
        if (!_verify(envelope, sig, oracle)) revert InvalidSignature();

        TierState storage t = _tier[tier];
        _samples[tier][t.slot] = amountUsdc;
        t.latest = amountUsdc;
        t.lastUpdatedAt = uint64(block.timestamp);
        uint16 newSlot = (t.slot + 1) % SAMPLE_SLOTS;
        if (t.filled < SAMPLE_SLOTS) {
            unchecked { t.filled += 1; }
        }
        t.slot = newSlot;

        unchecked { oracleNonce[oracle] = nonce + 1; }

        emit NavUpdated(tier, amountUsdc, oracle, sampleEpoch, newSlot);
    }

    // -------------------------------------------------------------------
    // Reads
    // -------------------------------------------------------------------

    function tierLatest(uint8 tier) external view returns (uint256) {
        if (tier >= TIER_COUNT) revert InvalidTier(tier);
        return _tier[tier].latest;
    }

    function tierFilledSamples(uint8 tier) external view returns (uint16) {
        if (tier >= TIER_COUNT) revert InvalidTier(tier);
        return _tier[tier].filled;
    }

    function reserveAverage() public view returns (uint256) {
        TierState storage t = _tier[TIER_RESERVE];
        if (t.filled == 0) return 0;
        uint256 sum = 0;
        for (uint16 i = 0; i < t.filled; ++i) {
            sum += _samples[TIER_RESERVE][i];
        }
        return sum / uint256(t.filled);
    }

    /// @notice Constitutional kisha envelope in USDC base units per month.
    ///         Clamped to the kappa band.
    function monthlyEnvelopeUsdc() external view returns (uint256) {
        uint16 kappa  = uint16(uint256(constitution.getMutable(K_KAPPA_BPS)));
        uint16 floor_ = uint16(uint256(constitution.getConstant(K_KAPPA_FLOOR_BPS)));
        uint16 ceil_  = uint16(uint256(constitution.getConstant(K_KAPPA_CEILING_BPS)));
        if (kappa < floor_) kappa = floor_;
        if (kappa > ceil_)  kappa = ceil_;
        uint256 avg = reserveAverage();
        // annual = avg × kappa / 10_000 ; monthly = annual / 12
        return (avg * uint256(kappa)) / (10_000 * 12);
    }

    function payloadHash(
        uint8 tier,
        uint256 amountUsdc,
        uint64 sampleEpoch,
        uint64 nonce,
        uint64 expiresAt,
        address oracle
    ) public view returns (bytes32) {
        return keccak256(abi.encode(
            address(this),
            block.chainid,
            tier,
            amountUsdc,
            sampleEpoch,
            nonce,
            expiresAt,
            oracle
        ));
    }

    // -------------------------------------------------------------------
    // Signature verification (same envelope as KishaPayout / Phenotype)
    // -------------------------------------------------------------------

    function _verify(bytes32 hash, bytes calldata sig, address expected) internal pure returns (bool) {
        if (sig.length != 65) return false;
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly ("memory-safe") {
            r := calldataload(sig.offset)
            s := calldataload(add(sig.offset, 32))
            v := byte(0, calldataload(add(sig.offset, 64)))
        }
        if (v < 27) v += 27;
        if (v != 27 && v != 28) return false;
        if (uint256(s) > 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0) {
            return false;
        }
        address recovered = ecrecover(hash, v, r, s);
        return recovered != address(0) && recovered == expected;
    }
}
