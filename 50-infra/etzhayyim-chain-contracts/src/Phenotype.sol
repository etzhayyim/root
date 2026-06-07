// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {Constitution} from "./Constitution.sol";

/**
 * @title Phenotype
 * @notice Per-adherent kisha multiplier in basis points. Bounded by the
 *         constitutional floor / ceiling read from {Constitution}.
 *         Populated by the off-chain Pregel `EligibilityCell` (see
 *         `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/eligibility/`) which
 *         signs each update with a registered cell key.
 *
 * @dev Per ADR-2605172300 §2 and §3.1. Apache-2.0.
 *
 *      Trust model:
 *        - Cell keys are added / removed only by `Constitution.governance()`
 *          so a hostile / leaked cell key can be rotated out via the same
 *          governance process that touches kisha rate.
 *        - Each {setMultiplier} call requires a fresh signature over the
 *          payload (epoch, tokenId, bps, nonce, expiry). Replay is
 *          prevented by a per-cell nonce; signature is EIP-191
 *          personal_sign (matched with `KishaPayout` for S1 simplicity;
 *          EIP-712 typed-data is a candidate for S3).
 *        - Multiplier is clamped on write to
 *          [Constitution.phenotype_min_bps, phenotype_max_bps]. Even a
 *          buggy or compromised cell cannot exceed the constitutional
 *          band.
 *
 *      What this contract does NOT do:
 *        - It does not own the kisha rate. It only exposes a multiplier.
 *          {KishaStream} composes the two at read time.
 *        - It does not enforce eligibility (active-window, revoke, etc.).
 *          Those are AdherentRegistry's responsibility.
 *        - It does not store *why* the multiplier was set. Rationale
 *          lives off-chain in an IPFS-pinned attestation referenced by
 *          `evidenceHash`.
 */
contract Phenotype {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error NotGovernance();
    error UnknownCell(address cell);
    error AlreadyRegistered(address cell);
    error ExpiredSignature();
    error InvalidSignature();
    error BadNonce(uint64 expected, uint64 given);
    error OutOfBand(uint16 given, uint16 floor, uint16 ceiling);

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event CellRegistered(address indexed cell, bytes32 indexed labelHash);
    event CellRevoked(address indexed cell, bytes32 reasonCid);
    event MultiplierSet(
        uint256 indexed tokenId,
        address indexed cell,
        uint16 oldBps,
        uint16 newBps,
        uint64 epoch,
        bytes32 evidenceHash
    );

    // -------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------

    struct MultiplierRecord {
        uint16 bps;             // current multiplier in basis points (10_000 = 1.0×)
        uint64 lastUpdatedAt;   // block.timestamp of latest setMultiplier
        uint64 lastEpoch;       // cell-supplied epoch of latest update
        address lastCell;       // cell that wrote the latest value
    }

    // -------------------------------------------------------------------
    // Immutable wiring
    // -------------------------------------------------------------------

    Constitution public immutable constitution;

    // Canonical constitutional keys (also documented in Constitution.sol).
    bytes32 private constant K_PHENOTYPE_MIN_BPS = keccak256("phenotype_min_bps");
    bytes32 private constant K_PHENOTYPE_MAX_BPS = keccak256("phenotype_max_bps");

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    /// @notice cell address → registered flag. Cells are EOAs (or contracts)
    ///         whose private key is held by the Pregel runtime.
    mapping(address => bool) public isCell;

    /// @notice Per-cell monotonic nonce used to bind each setMultiplier
    ///         call to a single signature.
    mapping(address => uint64) public cellNonce;

    /// @notice tokenId → multiplier record.
    mapping(uint256 => MultiplierRecord) private _records;

    // -------------------------------------------------------------------
    // Construction
    // -------------------------------------------------------------------

    constructor(Constitution constitution_) {
        constitution = constitution_;
    }

    // -------------------------------------------------------------------
    // Cell-set management (governance-only)
    // -------------------------------------------------------------------

    modifier onlyGovernance() {
        if (msg.sender != constitution.governance()) revert NotGovernance();
        _;
    }

    function registerCell(address cell, bytes32 labelHash) external onlyGovernance {
        if (isCell[cell]) revert AlreadyRegistered(cell);
        isCell[cell] = true;
        emit CellRegistered(cell, labelHash);
    }

    function revokeCell(address cell, bytes32 reasonCid) external onlyGovernance {
        if (!isCell[cell]) revert UnknownCell(cell);
        isCell[cell] = false;
        emit CellRevoked(cell, reasonCid);
    }

    // -------------------------------------------------------------------
    // Multiplier update — cell-signed, EIP-191
    // -------------------------------------------------------------------

    /**
     * @notice Set the multiplier for `tokenId`. Caller may be anyone;
     *         security comes from the cell signature.
     *
     * @param tokenId       Adherent SBT id.
     * @param newBps        New multiplier in basis points.
     * @param epoch         Cell-supplied epoch (Pregel super-step number).
     * @param nonce         Expected cellNonce[cell] before the call.
     *                      Use the contract's current value via
     *                      {expectedNonce}.
     * @param expiresAt     Signature expiry (unix seconds).
     * @param evidenceHash  Optional IPFS CID hash of the evidence record;
     *                      pass bytes32(0) if none.
     * @param cell          Cell address (must be registered).
     * @param sig           65-byte EIP-191 signature by `cell` over
     *                      `keccak256(\x19Ethereum Signed Message:\n32 || h)`
     *                      where `h` is the keccak256 of the payload
     *                      computed by {payloadHash}.
     */
    function setMultiplier(
        uint256 tokenId,
        uint16 newBps,
        uint64 epoch,
        uint64 nonce,
        uint64 expiresAt,
        bytes32 evidenceHash,
        address cell,
        bytes calldata sig
    ) external {
        if (!isCell[cell]) revert UnknownCell(cell);
        if (block.timestamp > expiresAt) revert ExpiredSignature();
        if (cellNonce[cell] != nonce) revert BadNonce(cellNonce[cell], nonce);

        uint16 floorBps = uint16(uint256(constitution.getConstant(K_PHENOTYPE_MIN_BPS)));
        uint16 ceilBps  = uint16(uint256(constitution.getConstant(K_PHENOTYPE_MAX_BPS)));
        if (newBps < floorBps || newBps > ceilBps) {
            revert OutOfBand(newBps, floorBps, ceilBps);
        }

        bytes32 h = payloadHash(tokenId, newBps, epoch, nonce, expiresAt, evidenceHash, cell);
        bytes32 envelope = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", h));
        if (!_verify(envelope, sig, cell)) revert InvalidSignature();

        MultiplierRecord storage r = _records[tokenId];
        uint16 oldBps = r.bps;
        r.bps = newBps;
        r.lastUpdatedAt = uint64(block.timestamp);
        r.lastEpoch = epoch;
        r.lastCell = cell;

        unchecked { cellNonce[cell] = nonce + 1; }

        emit MultiplierSet(tokenId, cell, oldBps, newBps, epoch, evidenceHash);
    }

    // -------------------------------------------------------------------
    // Reads
    // -------------------------------------------------------------------

    /**
     * @notice Current multiplier in bps. Returns 10_000 (= 1.0×) if no
     *         value has been set yet — KishaStream therefore treats an
     *         un-evaluated adherent as multiplier-neutral, not zero-rate.
     */
    function getMultiplierBps(uint256 tokenId) external view returns (uint16) {
        uint16 bps = _records[tokenId].bps;
        return bps == 0 ? 10_000 : bps;
    }

    function getRecord(uint256 tokenId) external view returns (MultiplierRecord memory) {
        return _records[tokenId];
    }

    function expectedNonce(address cell) external view returns (uint64) {
        return cellNonce[cell];
    }

    function payloadHash(
        uint256 tokenId,
        uint16 newBps,
        uint64 epoch,
        uint64 nonce,
        uint64 expiresAt,
        bytes32 evidenceHash,
        address cell
    ) public view returns (bytes32) {
        return keccak256(abi.encode(
            address(this),
            block.chainid,
            tokenId,
            newBps,
            epoch,
            nonce,
            expiresAt,
            evidenceHash,
            cell
        ));
    }

    // -------------------------------------------------------------------
    // Signature verification (same envelope as KishaPayout)
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
