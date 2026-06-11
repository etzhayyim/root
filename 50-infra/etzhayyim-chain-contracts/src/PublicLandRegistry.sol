// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2605252315 (Land Trust Wave 2 — Multi-ERC Alignment).
// Per ADR-2605252300 (Charter §0 Preamble — Kingdom of God on Blockchain).
//
// PublicLandRegistry — Base L2 (chainId 8453) ERC-721 + ERC-5192 mirror of the
// geth-private constitutional LandRegistry. Public, anyone-readable, soulbound.
//
// STATUS: R0 SCAFFOLD — all state-mutating functions revert NotYetActivated()
// until a separate post-Bootstrap-Council activation ADR enables them.
// Council ratify gate: post-2026-06-19 (Bootstrap Council RFP closure).
//
// CONSTITUTIONAL INVARIANTS (re-asserted at code level):
//   - No transfer of land NFT (soulbound, EIP-5192 locked() = true forever)
//   - No burn of land NFT (donations permanent)
//   - No "owner" semantics outside ERC-721 metadata compliance — semantically
//     "ownerOf(landId)" returns the steward address; this is the active steward
//     per LandRegistry.lands[landId].steward
//   - Only AnchorBridge can mint (observed donate() event from geth-private)
//
// NOTE: Once activated, this contract becomes the Base L2 half of the 4-layer
// land record (Preamble §0.3). Until then, all functions revert.

pragma solidity 0.8.27;

import {IERC5192} from "./interfaces/IERC5192.sol";

/// @dev Minimal ERC-721 + ERC-721 Metadata interface signatures we expose.
///      We don't inherit OpenZeppelin in R0 to keep the scaffold dependency-free;
///      activation ADR will inherit OZ ERC721 properly.
interface IERC721Minimal {
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    function balanceOf(address owner) external view returns (uint256);
    function ownerOf(uint256 tokenId) external view returns (address);
    function safeTransferFrom(address from, address to, uint256 tokenId, bytes calldata data) external;
    function safeTransferFrom(address from, address to, uint256 tokenId) external;
    function transferFrom(address from, address to, uint256 tokenId) external; // implementations revert/disallow
    function approve(address to, uint256 tokenId) external;
    function setApprovalForAll(address operator, bool approved) external;
    function getApproved(uint256 tokenId) external view returns (address);
    function isApprovedForAll(address owner, address operator) external view returns (bool);
}

interface IERC721MetadataMinimal {
    function name() external view returns (string memory);
    function symbol() external view returns (string memory);
    function tokenURI(uint256 tokenId) external view returns (string memory);
}

contract PublicLandRegistry is IERC721Minimal, IERC721MetadataMinimal, IERC5192 {
    error NotYetActivated();
    error LandSoulbound(uint256 tokenId);
    error LandPermanent(uint256 tokenId);
    error OnlyAnchorBridge();
    error NotCouncilMultisig();
    error ERC721NonexistentToken(uint256 tokenId);

    // Activation gate. False in R0; Council ≥3 multisig flips via activate().
    bool public activated;

    // AnchorBridge address (set by Council multisig at activation).
    address public anchorBridge;

    // ChartersComplianceRegistry (for Council Lv6+ ≥3 multisig check at activation).
    address public charters;

    // Constitutional metadata
    string private constant _NAME = "etzhayyim Public Land Registry";
    string private constant _SYMBOL = "EZ-LAND";

    constructor(address _charters) {
        charters = _charters;
        // activated stays false; anchorBridge stays 0 until activate() called
    }

    // ─── ERC-721 view stubs (always revert in R0) ──────────────────────────

    function balanceOf(address) external pure returns (uint256) {
        revert NotYetActivated();
    }

    function ownerOf(uint256) external pure returns (address) {
        revert NotYetActivated();
    }

    function name() external pure returns (string memory) {
        return _NAME;
    }

    function symbol() external pure returns (string memory) {
        return _SYMBOL;
    }

    function tokenURI(uint256) external pure returns (string memory) {
        revert NotYetActivated();
    }

    function getApproved(uint256) external pure returns (address) {
        revert NotYetActivated();
    }

    function isApprovedForAll(address, address) external pure returns (bool) {
        revert NotYetActivated();
    }

    // ─── ERC-721 mutators — ALL revert in R0 + constitutionally rejected ───

    function safeTransferFrom(address, address, uint256, bytes calldata) external pure {
        revert NotYetActivated();
    }

    function safeTransferFrom(address, address, uint256) external pure {
        revert NotYetActivated();
    }

    function transferFrom(address, address, uint256) external pure {
        revert NotYetActivated();
    }

    function approve(address, uint256) external pure {
        revert NotYetActivated();
    }

    function setApprovalForAll(address, bool) external pure {
        revert NotYetActivated();
    }

    // ─── ERC-5192 ──────────────────────────────────────────────────────────

    /// @dev CONSTITUTIONAL: returns true once activated; in R0 reverts NotYetActivated.
    function locked(uint256) external view returns (bool) {
        if (!activated) revert NotYetActivated();
        return true;
    }

    // ─── ERC-165 ───────────────────────────────────────────────────────────

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == type(IERC721Minimal).interfaceId
            || interfaceId == type(IERC721MetadataMinimal).interfaceId
            || interfaceId == type(IERC5192).interfaceId   // 0xb45a3c0e
            || interfaceId == bytes4(0x01ffc9a7);          // ERC-165
    }

    // ─── Mirror flow (R0 stub) ─────────────────────────────────────────────

    /// @notice Called by AnchorBridge to mint a Base L2 mirror of a geth-private donation.
    /// @dev R0: reverts NotYetActivated. Activation ADR will wire to AnchorBridge.
    function mintFromAnchor(
        uint256,
        address,
        string calldata
    ) external pure {
        revert NotYetActivated();
    }

    // ─── Activation (Council multisig-gated, R0 stub) ──────────────────────

    /// @notice Council Lv6+ ≥3 multisig calls this to flip activated = true.
    /// @dev R0: reverts NotYetActivated. Future activation ADR will implement
    ///      with proper multisig signature verification.
    function activate(address /*_anchorBridge*/, bytes[] calldata /*councilSigs*/, address[] calldata /*councilSigners*/) external pure {
        revert NotYetActivated();
    }
}
