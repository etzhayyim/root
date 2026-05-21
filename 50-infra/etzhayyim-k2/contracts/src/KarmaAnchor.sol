// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

/**
 * @title KarmaAnchor
 * @notice Daily Merkle-root anchor of cohort-internal events to Base L2
 *         per ADR-2605212040 §D1. Owner (Council 5-of-7 Safe) submits
 *         one anchor per epoch; readers verify cohort-internal events
 *         off-chain by checking their leaf against the on-chain root.
 *
 * @dev    Each anchor binds:
 *           - merkleRoot:  32-byte Merkle root over the epoch's event log
 *           - ipfsCidHash: keccak256 of the IPFS CID of the full event log
 *
 *         No upgrade, no pause. An incorrect anchor cannot be retracted;
 *         the next-epoch anchor takes precedence for future verification.
 *         Historic events stand on their original anchor.
 */
contract KarmaAnchor {
    address public owner;

    struct Anchor {
        bytes32 merkleRoot;
        bytes32 ipfsCidHash;
        uint96 submittedBlock;
        bool present;
    }

    /// @dev epoch is caller-defined (typically unix day = block.timestamp / 86400).
    mapping(uint256 => Anchor) public anchors;

    event OwnerChanged(address indexed previousOwner, address indexed newOwner);
    event AnchorSubmitted(
        uint256 indexed epoch,
        bytes32 merkleRoot,
        bytes32 ipfsCidHash,
        uint256 submittedBlock
    );

    error NotOwner();
    error ZeroAddress();
    error InvalidArgument();
    error AnchorAlreadyExists();

    constructor(address initialOwner) {
        if (initialOwner == address(0)) revert ZeroAddress();
        owner = initialOwner;
        emit OwnerChanged(address(0), initialOwner);
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    function setOwner(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroAddress();
        emit OwnerChanged(owner, newOwner);
        owner = newOwner;
    }

    /// @notice Submit the anchor for `epoch`. Each epoch can be anchored
    ///         exactly once.
    function submitAnchor(uint256 epoch, bytes32 merkleRoot, bytes32 ipfsCidHash) external onlyOwner {
        if (merkleRoot == bytes32(0)) revert InvalidArgument();
        if (ipfsCidHash == bytes32(0)) revert InvalidArgument();
        if (anchors[epoch].present) revert AnchorAlreadyExists();
        anchors[epoch] = Anchor({
            merkleRoot: merkleRoot,
            ipfsCidHash: ipfsCidHash,
            submittedBlock: uint96(block.number),
            present: true
        });
        emit AnchorSubmitted(epoch, merkleRoot, ipfsCidHash, block.number);
    }

    /// @notice Verify a Merkle proof against the anchor for `epoch`.
    /// @dev Standard sorted-pair OpenZeppelin-compatible proof verification.
    function verifyLeaf(uint256 epoch, bytes32 leaf, bytes32[] calldata proof)
        external
        view
        returns (bool)
    {
        Anchor storage a = anchors[epoch];
        if (!a.present) return false;
        bytes32 computed = leaf;
        for (uint256 i = 0; i < proof.length; i++) {
            bytes32 sibling = proof[i];
            computed = computed < sibling
                ? keccak256(abi.encodePacked(computed, sibling))
                : keccak256(abi.encodePacked(sibling, computed));
        }
        return computed == a.merkleRoot;
    }

    function getAnchor(uint256 epoch) external view returns (Anchor memory) {
        return anchors[epoch];
    }
}
