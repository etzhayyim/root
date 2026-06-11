// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Minimal IERC7401 nestable NFT interface (EIP-7401 — Parent-Governed Nestable NFTs).
// Used by etzhayyim StewardTenureRegistry to nest steward-tenure child NFTs
// under PublicLandRegistry parent (land) NFTs.
// Per ADR-2605252315 (Land Trust Wave 2 — Multi-ERC Alignment).
//
// EIP-7401 Interface ID (minimal subset): 0x42b0e56f
//
// This is a MINIMAL subset of EIP-7401, including only the functions needed
// for the steward-tenure semantics. Full RMRK / EIP-7401 implementation
// (including child management, equippable patterns, etc.) is intentionally
// out of scope for R0 — see ADR-2605252315 §6.

pragma solidity 0.8.27;

/// @title IERC7401 (minimal) — Parent-Governed Nestable NFTs
/// @dev EIP-7401 minimal subset. We include only:
///   - directOwnerOf — returns (parentContract, parentTokenId, isNft)
///   - addChild — parent receives child
///   - acceptChild — parent confirms child
/// Sufficient for steward-tenure (child) ↔ land (parent) semantics.
interface IERC7401 {
    /// @notice Used to notify listeners that the token is being transferred from one parent to another.
    /// @param tokenId ID of the token being moved
    /// @param fromParentContract Address of the previous parent contract (0 if first parent)
    /// @param fromParentTokenId ID of the previous parent token (0 if first parent)
    /// @param toParentContract Address of the new parent contract
    /// @param toParentTokenId ID of the new parent token
    event NestTransfer(
        uint256 indexed tokenId,
        address fromParentContract,
        uint256 fromParentTokenId,
        address toParentContract,
        uint256 toParentTokenId
    );

    /// @notice Emitted when a child is added to a parent NFT.
    event ChildAdded(
        uint256 indexed tokenId,
        uint256 indexed childIndex,
        address indexed childAddress,
        uint256 childId
    );

    /// @notice Emitted when a child is accepted by the parent NFT.
    event ChildAccepted(
        uint256 indexed tokenId,
        uint256 childIndex,
        address indexed childAddress,
        uint256 childId
    );

    /// @notice Used to retrieve the direct owner of an NFT.
    /// @dev If the immediate owner is another NFT, the function MUST return the address
    ///      of that NFT contract, the tokenId of that NFT, and true. Otherwise the
    ///      function MUST return the EOA / contract owner, 0, and false.
    /// @param tokenId ID of the token for which the direct owner is being retrieved
    /// @return parentContract Address of the parent (NFT contract or EOA)
    /// @return parentTokenId Token ID of the parent (0 if not nested)
    /// @return isNft Whether the parent is an NFT (true) or an EOA / contract (false)
    function directOwnerOf(uint256 tokenId)
        external
        view
        returns (address parentContract, uint256 parentTokenId, bool isNft);

    /// @notice Used to add a child NFT to a parent NFT.
    /// @dev Used by the child NFT contract to add itself under a parent.
    /// @param parentId ID of the parent NFT to which the child is being added
    /// @param childId ID of the child NFT being added
    /// @param data Optional data passed during the add operation
    function addChild(uint256 parentId, uint256 childId, bytes calldata data) external;

    /// @notice Used to accept a pending child NFT under a parent.
    /// @dev MUST be called by the parent NFT owner (or its approved address).
    /// @param parentId ID of the parent NFT
    /// @param childIndex Index of the child in the pending children array
    /// @param childAddress Address of the child NFT contract (sanity check)
    /// @param childId ID of the child NFT being accepted (sanity check)
    function acceptChild(
        uint256 parentId,
        uint256 childIndex,
        address childAddress,
        uint256 childId
    ) external;
}
