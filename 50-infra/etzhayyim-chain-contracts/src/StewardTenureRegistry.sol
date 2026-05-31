// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2605252315 (Land Trust Wave 2 — Multi-ERC Alignment).
// Per ADR-2605192345 (Steward Succession — multisig-mediated).
//
// StewardTenureRegistry — ERC-7401 (Parent-Governed Nestable NFTs) for
// steward-tenure child NFTs nested under PublicLandRegistry land NFTs.
//
//   parent NFT = PublicLandRegistry tokenId  (a land parcel — permanent)
//   child NFT  = tenure NFT                  (a steward's tenure on that parcel)
//
// Each parcel may have multiple historical tenure children (one active + N
// terminated). Active tenure is soulbound while active (cannot transfer);
// succession is always Council ≥3 multisig burn-and-mint of the child.
//
// STATUS: R0 SCAFFOLD — all state-mutating functions revert NotYetActivated()
// until separate post-Bootstrap-Council activation ADR enables them.

pragma solidity 0.8.27;

import {IERC7401} from "./interfaces/IERC7401.sol";
import {IERC5192} from "./interfaces/IERC5192.sol";

contract StewardTenureRegistry is IERC7401, IERC5192 {
    enum TenureType { Founder, Successor, Interim, CouncilAppointed }

    struct Tenure {
        uint256 landTokenId;
        uint256 stewardSbtId;
        address stewardAddr;
        uint64 startedAt;
        uint64 expectedEndAt;
        uint64 actualEndAt; // 0 = active
        TenureType tenureType;
        bytes32 successionEvidenceCid;
    }

    error NotYetActivated();
    error TenureNotFound(uint256 tenureId);
    error NotActiveTenure(uint256 tenureId);
    error InsufficientCouncilSigners();
    error TenureSoulbound(uint256 tenureId);

    bool public activated;
    address public publicLandRegistry; // parent contract, set at activation
    address public charters;            // ChartersComplianceRegistry

    uint8 public constant MIN_COUNCIL_SIGNERS = 3;

    // Events (active in R1; emit nothing in R0)
    event TenureStarted(
        uint256 indexed tenureId,
        uint256 indexed landTokenId,
        uint256 indexed stewardSbtId,
        TenureType tenureType
    );
    event TenureTerminated(uint256 indexed tenureId, bytes32 reasonCid);

    constructor(address _charters) {
        charters = _charters;
    }

    // ─── ERC-7401 nestable (R0 stubs) ──────────────────────────────────────

    function directOwnerOf(uint256) external pure returns (address, uint256, bool) {
        revert NotYetActivated();
    }

    function addChild(uint256, uint256, bytes calldata) external pure {
        revert NotYetActivated();
    }

    function acceptChild(uint256, uint256, address, uint256) external pure {
        revert NotYetActivated();
    }

    // ─── ERC-5192 (soulbound-while-active) ─────────────────────────────────

    /// @dev R0: always reverts. R1: returns true iff tenure.actualEndAt == 0.
    function locked(uint256) external view returns (bool) {
        if (!activated) revert NotYetActivated();
        return true; // simplified; R1 will return tenures[id].actualEndAt == 0
    }

    // ─── ERC-165 ───────────────────────────────────────────────────────────

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == type(IERC7401).interfaceId
            || interfaceId == type(IERC5192).interfaceId
            || interfaceId == bytes4(0x01ffc9a7); // ERC-165
    }

    // ─── Tenure lifecycle (R0 stubs) ───────────────────────────────────────

    /// @notice Mint a new tenure NFT as child of a land NFT.
    /// @dev Council ≥3 multisig only. R0: reverts NotYetActivated.
    function nestNew(
        uint256, /*landTokenId*/
        uint256, /*successorStewardSbt*/
        TenureType,
        uint64, /*expectedEndAt*/
        bytes32, /*successionEvidenceCid*/
        bytes[] calldata, /*councilSigs*/
        address[] calldata /*councilSigners*/
    ) external pure returns (uint256) {
        revert NotYetActivated();
    }

    /// @notice Terminate an active tenure (burn child NFT).
    /// @dev Council ≥3 multisig only. R0: reverts NotYetActivated.
    function terminate(
        uint256, /*tenureId*/
        bytes32, /*reasonCid*/
        bytes[] calldata, /*councilSigs*/
        address[] calldata /*councilSigners*/
    ) external pure {
        revert NotYetActivated();
    }

    // ─── View helpers (R0 stubs) ───────────────────────────────────────────

    function activeTenureOf(uint256) external pure returns (uint256) {
        revert NotYetActivated();
    }

    function tenureHistoryOf(uint256) external pure returns (uint256[] memory) {
        revert NotYetActivated();
    }

    // ─── Activation ────────────────────────────────────────────────────────

    function activate(
        address, /*_publicLandRegistry*/
        bytes[] calldata, /*councilSigs*/
        address[] calldata /*councilSigners*/
    ) external pure {
        revert NotYetActivated();
    }
}
