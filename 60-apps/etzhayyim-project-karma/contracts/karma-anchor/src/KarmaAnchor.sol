// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title KarmaAnchor
 * @notice Append-only commitment registry for Karma Hegemon Layer-4 persistence.
 *
 * Each call to `anchor` records:
 *   - the Merkle root of all karma edge IPFS CIDs emitted within the window
 *   - the window time bounds
 *   - the count of edges covered
 *
 * The contract is intentionally minimal:
 *   - no upgrade mechanism (immutable verifier)
 *   - no removal / mutation (append-only)
 *   - no privileged read (everything is public)
 *   - small gas profile suitable for L2 daily commits
 *
 * Authoritative axioms: 90-docs/proof/Karma.lean
 *   - karma_5_layer_persistence  →  one record per (window) is required
 *   - karma_survives_quad_failure →  blockchain is one of 5 surviving locations
 *
 * Owner is expected to be the karma actor's did:erc725 wallet
 * (ADR-0074/0095 unified identity); writes are gated by `onlyOwner`.
 */
contract KarmaAnchor {
    // ──────────────────────────────────────────────
    // Storage
    // ──────────────────────────────────────────────

    address public owner;

    /// @notice Single anchor commitment.
    struct Commitment {
        bytes32 merkleRoot;       // sha256(merkle tree of edge ipfs cids)
        uint64  windowStartMs;    // inclusive ms epoch
        uint64  windowEndMs;      // exclusive ms epoch
        uint32  edgeCount;        // number of edges covered
        uint32  blockTimestamp;   // truncated block.timestamp at anchor
    }

    /// @notice Append-only ledger of commitments. Index = anchor sequence.
    Commitment[] public commitments;

    /// @notice Lookup: windowEndMs → commitment index + 1 (0 = absent).
    mapping(uint64 => uint256) public windowIndexPlusOne;

    // ──────────────────────────────────────────────
    // Events
    // ──────────────────────────────────────────────

    event Anchored(
        uint256 indexed anchorIndex,
        bytes32 indexed merkleRoot,
        uint64 windowStartMs,
        uint64 windowEndMs,
        uint32 edgeCount
    );

    event OwnershipTransferred(address indexed prevOwner, address indexed newOwner);

    // ──────────────────────────────────────────────
    // Modifiers
    // ──────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "KarmaAnchor: not owner");
        _;
    }

    // ──────────────────────────────────────────────
    // Constructor
    // ──────────────────────────────────────────────

    constructor(address initialOwner) {
        require(initialOwner != address(0), "KarmaAnchor: owner zero");
        owner = initialOwner;
        emit OwnershipTransferred(address(0), initialOwner);
    }

    // ──────────────────────────────────────────────
    // Anchor (write)
    // ──────────────────────────────────────────────

    /**
     * @notice Append a new Merkle root commitment for a karma window.
     *         Reverts if a commitment for the same windowEndMs already exists
     *         (idempotency: each window's daily run produces exactly one anchor).
     *
     * @param merkleRoot      Root of the Merkle tree over edge IPFS CIDs.
     * @param windowStartMs   Inclusive lower bound of the time window (ms epoch).
     * @param windowEndMs     Exclusive upper bound of the time window (ms epoch).
     * @param edgeCount       Number of edges covered (informational).
     */
    function anchor(
        bytes32 merkleRoot,
        uint64 windowStartMs,
        uint64 windowEndMs,
        uint32 edgeCount
    ) external onlyOwner returns (uint256 anchorIndex) {
        require(merkleRoot != bytes32(0), "KarmaAnchor: empty root");
        require(windowEndMs > windowStartMs, "KarmaAnchor: bad window");
        require(edgeCount > 0, "KarmaAnchor: empty window");
        require(windowIndexPlusOne[windowEndMs] == 0, "KarmaAnchor: window exists");

        Commitment memory c = Commitment({
            merkleRoot: merkleRoot,
            windowStartMs: windowStartMs,
            windowEndMs: windowEndMs,
            edgeCount: edgeCount,
            blockTimestamp: uint32(block.timestamp)
        });

        commitments.push(c);
        anchorIndex = commitments.length - 1;
        windowIndexPlusOne[windowEndMs] = anchorIndex + 1;

        emit Anchored(anchorIndex, merkleRoot, windowStartMs, windowEndMs, edgeCount);
    }

    // ──────────────────────────────────────────────
    // Read
    // ──────────────────────────────────────────────

    function commitmentCount() external view returns (uint256) {
        return commitments.length;
    }

    function getCommitment(uint256 index) external view returns (Commitment memory) {
        require(index < commitments.length, "KarmaAnchor: out of range");
        return commitments[index];
    }

    /// @notice Returns (found, commitment) for a given windowEndMs.
    function findByWindow(uint64 windowEndMs) external view returns (bool found, Commitment memory c) {
        uint256 plusOne = windowIndexPlusOne[windowEndMs];
        if (plusOne == 0) {
            return (false, c);
        }
        c = commitments[plusOne - 1];
        return (true, c);
    }

    // ──────────────────────────────────────────────
    // Owner transfer
    // ──────────────────────────────────────────────

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "KarmaAnchor: owner zero");
        address prev = owner;
        owner = newOwner;
        emit OwnershipTransferred(prev, newOwner);
    }
}
