// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title EtzhayyimAnchor
 * @notice Immutable append-only log of MST root anchors for the etzhayyim
 *         open religious-corp activity ecosystem. Per ADR-2605171800 Stage 5.
 *
 * @dev Design rules (from ADR-2605172000 + ADR-2605172100):
 *      - NO admin function. NO upgrade path. NO pause. The contract code is
 *        the only governance — to change behavior, deploy a new contract.
 *      - Anyone can call anchor(...). The on-chain record of who anchored
 *        (msg.sender + their on-chain identity, resolvable to a DID via
 *        attestation) is the audit trail. There is no whitelist; the
 *        anchorer's reputation is established off-chain via their DID.
 *      - Emits Anchored(...) event so reorgs / indexer rebuilds work.
 */
contract EtzhayyimAnchor {
    /// @dev One anchored MST root entry.
    struct AnchorEntry {
        bytes32 rootHash;        // sha256 of the MST root CID bytes
        bytes ipfsCid;           // raw multibase CID (variable length, dag-cbor)
        uint256 blockNumber;     // L2 block when anchored
        address anchorer;        // msg.sender at anchor time
        uint64 batchSize;        // record count in this batch (informational)
        uint64 anchoredAt;       // block.timestamp at anchor time
    }

    /// @dev rootHash → entry. Anchoring the same root twice is idempotent
    ///      (second call is a no-op revert).
    mapping(bytes32 => AnchorEntry) public anchors;

    /// @dev Append-only list of all anchored rootHashes for enumeration.
    bytes32[] public allRoots;

    /// @notice Emitted on each successful anchor.
    event Anchored(
        bytes32 indexed rootHash,
        address indexed anchorer,
        bytes ipfsCid,
        uint256 blockNumber,
        uint64 batchSize
    );

    error AlreadyAnchored(bytes32 rootHash);
    error EmptyIpfsCid();

    /**
     * @notice Anchor an MST root.
     * @param rootHash sha256 of the canonical MST root CID bytes.
     * @param ipfsCid the multibase-encoded CID of the MST root in IPFS.
     * @param batchSize record count in this batch (informational, not enforced).
     */
    function anchor(bytes32 rootHash, bytes calldata ipfsCid, uint64 batchSize) external {
        if (anchors[rootHash].blockNumber != 0) revert AlreadyAnchored(rootHash);
        if (ipfsCid.length == 0) revert EmptyIpfsCid();

        anchors[rootHash] = AnchorEntry({
            rootHash: rootHash,
            ipfsCid: ipfsCid,
            blockNumber: block.number,
            anchorer: msg.sender,
            batchSize: batchSize,
            anchoredAt: uint64(block.timestamp)
        });
        allRoots.push(rootHash);

        emit Anchored(rootHash, msg.sender, ipfsCid, block.number, batchSize);
    }

    /// @notice Number of distinct roots anchored so far.
    function rootCount() external view returns (uint256) {
        return allRoots.length;
    }

    /// @notice Paginated read of anchored roots.
    function listRoots(uint256 offset, uint256 limit) external view returns (bytes32[] memory page) {
        uint256 total = allRoots.length;
        if (offset >= total) return new bytes32[](0);
        uint256 end = offset + limit;
        if (end > total) end = total;
        page = new bytes32[](end - offset);
        for (uint256 i = 0; i < page.length; i++) {
            page[i] = allRoots[offset + i];
        }
    }
}
