// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2605192245 (Global Land Sovereignty) + ADR-2605252315 (Land Trust
// Wave 2 — Multi-ERC Alignment). Deployed on geth-private (chainId 2605) —
// constitutional layer. Soulbound signalling per EIP-5192.

pragma solidity 0.8.27;

import {IERC5192} from "./interfaces/IERC5192.sol";

interface IAdherentRegistry {
    function isActive(uint256 tokenId, uint64 windowSecs) external view returns (bool);
    function ownerOfToken(uint256 tokenId) external view returns (address);
}

/// @notice ChartersComplianceRegistry is the canonical Council Lv6+ membership
/// + non-aligned attestation source (per ADR-2605192230 + ADR-2605192300).
interface IChartersComplianceRegistry {
    function isCouncilMember(address) external view returns (bool);
    function isNonAlignedAddress(address subject) external view returns (bool);
}

contract LandRegistry is IERC5192 {
    enum LandType { Agricultural, Residential, Forest, ReligiousFacility, Other, Ocean, Water, Air, Orbit }
    enum Status { Active, UnderDispute, RehabReversal }

    struct Land {
        bytes32 oathHash;
        bytes32 geojsonCid;
        bytes32 imageryBundleCid;
        bytes32 deedCid;
        bytes32 nationalRegistryRefHash;
        uint256 areaM2;
        LandType landType;
        address steward;
        uint64 donatedAt;
        Status status;
    }

    mapping(uint256 => Land) public lands;
    mapping(address => uint256[]) public stewardLands;
    uint256 public nextLandId = 1;

    IAdherentRegistry public immutable adherentRegistry;
    IChartersComplianceRegistry public immutable charters;

    uint8 public constant MIN_COUNCIL_SIGNERS = 3;

    event Donated(
        uint256 indexed landId,
        address indexed donor,
        bytes32 geojsonCid,
        uint256 areaM2,
        LandType landType
    );
    event StewardChanged(uint256 indexed landId, address oldSteward, address newSteward);
    event DisputeOpened(uint256 indexed landId, bytes32 disputeEvidenceCid);
    event DisputeResolved(uint256 indexed landId, Status resolution);

    error InsufficientCouncilSigners();
    error NotCouncilMember(address signer);
    error LandNotActive(uint256 landId);
    error StewardNotEligible(address steward);
    error LandNotFound(uint256 landId);

    // NOTE: Intentionally absent (constitutional invariants):
    //   - transfer() — donations are inalienable
    //   - burn() / destroy() — permanent record
    //   - setOwner() — only steward role exists
    //   - mint() — only via donate() ritual
    //
    // ERC-5192 (Minimal Soulbound NFTs) signalling, per ADR-2605252315:
    //   - locked(landId) returns true for every donated parcel — forever
    //   - Locked event emitted on donate() — once, never unlocked
    //   - Unlocked event MUST NEVER be emitted (no function path exists)
    //   - supportsInterface(IERC5192) returns true (interface id 0xb45a3c0e)

    constructor(IAdherentRegistry _registry, IChartersComplianceRegistry _charters) {
        adherentRegistry = _registry;
        charters = _charters;
    }

    function donate(
        bytes32 oathHash,
        bytes32 geojsonCid,
        bytes32 imageryBundleCid,
        bytes32 deedCid,
        bytes32 nationalRegistryRefHash,
        uint256 areaM2,
        LandType landType,
        address steward
    ) external returns (uint256 landId) {
        if (charters.isNonAlignedAddress(msg.sender)) revert StewardNotEligible(msg.sender);
        if (charters.isNonAlignedAddress(steward)) revert StewardNotEligible(steward);

        landId = nextLandId++;
        lands[landId] = Land({
            oathHash: oathHash,
            geojsonCid: geojsonCid,
            imageryBundleCid: imageryBundleCid,
            deedCid: deedCid,
            nationalRegistryRefHash: nationalRegistryRefHash,
            areaM2: areaM2,
            landType: landType,
            steward: steward,
            donatedAt: uint64(block.timestamp),
            status: Status.Active
        });
        stewardLands[steward].push(landId);

        emit Donated(landId, msg.sender, geojsonCid, areaM2, landType);
        // ERC-5192: signal soulbound status at donation. Never unlocked.
        emit Locked(landId);
    }

    /// @notice ERC-5192 locked(uint256) — soulbound status of a land record.
    /// @dev CONSTITUTIONAL: always returns true for valid landId. Donated land
    ///      cannot be transferred (no transfer function exists). Per
    ///      ADR-2605192245 §2 + ADR-2605252315 §2.1.
    /// @param landId The land record identifier.
    /// @return True (constant) — reverts LandNotFound for unknown ids.
    function locked(uint256 landId) external view returns (bool) {
        if (lands[landId].donatedAt == 0) revert LandNotFound(landId);
        return true;
    }

    /// @notice ERC-165 supportsInterface — declares ERC-5192 (0xb45a3c0e) + ERC-165 (0x01ffc9a7).
    /// @dev Per ADR-2605252315 §2.5.
    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == type(IERC5192).interfaceId  // 0xb45a3c0e
            || interfaceId == bytes4(0x01ffc9a7);          // ERC-165
    }

    function reassignSteward(
        uint256 landId,
        address newSteward,
        bytes[] calldata councilSigs,
        address[] calldata councilSigners
    ) external {
        _verifyCouncilQuorum(councilSigs, councilSigners);
        Land storage land = lands[landId];
        if (land.status != Status.Active) revert LandNotActive(landId);
        if (charters.isNonAlignedAddress(newSteward)) revert StewardNotEligible(newSteward);

        address old = land.steward;
        land.steward = newSteward;
        stewardLands[newSteward].push(landId);

        emit StewardChanged(landId, old, newSteward);
    }

    function openDispute(uint256 landId, bytes32 disputeEvidenceCid) external {
        Land storage land = lands[landId];
        if (land.status != Status.Active) revert LandNotActive(landId);
        land.status = Status.UnderDispute;
        emit DisputeOpened(landId, disputeEvidenceCid);
    }

    function resolveDispute(
        uint256 landId,
        Status resolution,
        bytes[] calldata councilSigs,
        address[] calldata councilSigners
    ) external {
        _verifyCouncilQuorum(councilSigs, councilSigners);
        Land storage land = lands[landId];
        land.status = resolution;
        emit DisputeResolved(landId, resolution);
    }

    function _verifyCouncilQuorum(bytes[] calldata sigs, address[] calldata signers) internal view {
        if (sigs.length < MIN_COUNCIL_SIGNERS || signers.length < MIN_COUNCIL_SIGNERS) {
            revert InsufficientCouncilSigners();
        }
        for (uint256 i = 0; i < signers.length; i++) {
            if (!charters.isCouncilMember(signers[i])) revert NotCouncilMember(signers[i]);
        }
        // TODO: EIP-712 sig recovery in production
    }
}
