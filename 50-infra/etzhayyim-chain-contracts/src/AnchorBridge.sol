// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title AnchorBridge
 * @notice Periodic anchor of geth-private state into Base L2 via the
 *         existing `EtzhayyimAnchor` contract (`50-infra/l2-anchor-contract/`).
 *
 * @dev Per ADR-2605172300 §2.AnchorBridge and §5. Apache-2.0.
 *
 *      The geth-private side cannot directly write to Base. Instead:
 *
 *        1. Officers (or anyone — committing is permissionless) call
 *           {commitRoot} on geth-private with the current MST root or
 *           geth-private state root they want anchored.
 *        2. An off-chain relayer service tails the {RootCommitted} event
 *           and submits a corresponding {EtzhayyimAnchor.anchor} tx on
 *           Base L2.
 *        3. The Base anchor tx's `rootHash` and `ipfsCid` should match
 *           what was committed here, allowing third-party verifiers to
 *           cross-check the two chains.
 *
 *      S1 model: anchoring is fire-and-forget. There is no back-relay
 *      to mark fulfillment on geth-private — the act of issuing the
 *      anchor commitment already creates the audit trail. The Base side
 *      is the canonical timestamp.
 *
 *      Threat model:
 *        - Anyone may commit (no permission gate). If a hostile party
 *          commits garbage roots, the relayer can choose to ignore them
 *          (off-chain policy). Each event is indexed by committer for
 *          easy filtering. There is no on-chain dispute resolution at S1.
 *        - The geth-private chain itself is PoA — only validators
 *          (officers) can produce blocks, so block-level censorship is
 *          a separate concern handled by the validator set.
 */
contract AnchorBridge {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error EmptyRoot();
    error EmptyCid();

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event RootCommitted(
        bytes32 indexed rootHash,
        address indexed committer,
        uint256 indexed committedAt,
        bytes ipfsCid,
        uint64 batchSize,
        bytes32 priorRootHash
    );

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    /// @notice The most recently committed root. Used to chain commits.
    bytes32 public latestRootHash;
    uint256 public latestRootBlockNumber;

    /// @notice rootHash → committer. Idempotent: re-committing the same
    ///         rootHash is a no-op revert.
    mapping(bytes32 => address) public committerOf;

    /// @notice Append-only list of committed root hashes for enumeration.
    bytes32[] public allRoots;

    // -------------------------------------------------------------------
    // Commit
    // -------------------------------------------------------------------

    /**
     * @notice Commit a geth-private state or MST root for anchoring to
     *         Base L2. Permissionless on this side; relayer is the
     *         policy layer.
     *
     * @param rootHash   keccak256 (or sha256) commitment of the state
     *                   to be anchored. The exact hash function is a
     *                   convention shared with the relayer.
     * @param ipfsCid    Raw multibase CID bytes (variable length,
     *                   dag-cbor) referencing the off-chain blob if any.
     * @param batchSize  Informational record count in this batch.
     */
    function commitRoot(
        bytes32 rootHash,
        bytes calldata ipfsCid,
        uint64 batchSize
    ) external {
        if (rootHash == bytes32(0)) revert EmptyRoot();
        if (ipfsCid.length == 0) revert EmptyCid();
        require(committerOf[rootHash] == address(0), "duplicate root");

        bytes32 prior = latestRootHash;
        latestRootHash = rootHash;
        latestRootBlockNumber = block.number;
        committerOf[rootHash] = msg.sender;
        allRoots.push(rootHash);

        emit RootCommitted(
            rootHash,
            msg.sender,
            block.timestamp,
            ipfsCid,
            batchSize,
            prior
        );
    }

    // -------------------------------------------------------------------
    // Reads
    // -------------------------------------------------------------------

    function totalRoots() external view returns (uint256) {
        return allRoots.length;
    }
}
