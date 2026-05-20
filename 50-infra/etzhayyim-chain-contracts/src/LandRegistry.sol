// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2605192245 (Global Land Sovereignty).
// Deployed on geth-private (chainId 2605) — constitutional layer.

pragma solidity 0.8.27;

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

contract LandRegistry {
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

    // NOTE: Intentionally absent (constitutional invariants):
    //   - transfer() — donations are inalienable
    //   - burn() / destroy() — permanent record
    //   - setOwner() — only steward role exists
    //   - mint() — only via donate() ritual

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
