// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2605252315 (Land Trust Wave 2 — Multi-ERC Alignment).
//
// LandClassRegistry — ERC-1155 SUPPLEMENTARY aggregate accounting for land
// classes (Agricultural / Residential / Forest / ReligiousFacility / Other /
// Ocean / Water / Air / Orbit). Token IDs are constants matching the
// LandRegistry.LandType enum.
//
// IMPORTANT — NOT A FUNGIBLE ECONOMIC TOKEN:
//   - "balance" = area-m² accounting hash, NOT transferable value
//   - All transfers revert (soulbound at the class layer)
//   - Class assignment is fixed at land donation time (mirrored from LandRegistry)
//   - Aggregate accounting only — for "how much agricultural land in trust" queries
//
// STATUS: R0 SCAFFOLD — all state-mutating functions revert NotYetActivated().

pragma solidity 0.8.27;

/// @dev Minimal ERC-1155 interface (only what we expose).
interface IERC1155Minimal {
    event TransferSingle(
        address indexed operator,
        address indexed from,
        address indexed to,
        uint256 id,
        uint256 value
    );
    event TransferBatch(
        address indexed operator,
        address indexed from,
        address indexed to,
        uint256[] ids,
        uint256[] values
    );
    event ApprovalForAll(address indexed account, address indexed operator, bool approved);
    event URI(string value, uint256 indexed id);

    function balanceOf(address account, uint256 id) external view returns (uint256);
    function balanceOfBatch(address[] calldata accounts, uint256[] calldata ids)
        external view returns (uint256[] memory);
    function setApprovalForAll(address operator, bool approved) external;
    function isApprovedForAll(address account, address operator) external view returns (bool);
    function safeTransferFrom(address from, address to, uint256 id, uint256 amount, bytes calldata data) external;
    function safeBatchTransferFrom(
        address from,
        address to,
        uint256[] calldata ids,
        uint256[] calldata amounts,
        bytes calldata data
    ) external;
}

interface IERC1155MetadataURIMinimal {
    function uri(uint256 id) external view returns (string memory);
}

contract LandClassRegistry is IERC1155Minimal, IERC1155MetadataURIMinimal {
    // Token IDs MUST match LandRegistry.LandType enum order — constitutional invariant.
    uint256 public constant CLASS_AGRICULTURAL    = 0;
    uint256 public constant CLASS_RESIDENTIAL     = 1;
    uint256 public constant CLASS_FOREST          = 2;
    uint256 public constant CLASS_RELIGIOUS_FAC   = 3;
    uint256 public constant CLASS_OTHER           = 4;
    uint256 public constant CLASS_OCEAN           = 5;
    uint256 public constant CLASS_WATER           = 6;
    uint256 public constant CLASS_AIR             = 7;
    uint256 public constant CLASS_ORBIT           = 8;

    error NotYetActivated();
    error LandClassSoulbound();
    error OnlyAnchorBridge();
    error InvalidClass(uint256 classId);

    bool public activated;
    address public anchorBridge;
    address public publicLandRegistry;
    address public charters;

    constructor(address _charters) {
        charters = _charters;
    }

    // ─── ERC-1155 view (R0 stubs) ──────────────────────────────────────────

    function balanceOf(address, uint256) external pure returns (uint256) {
        revert NotYetActivated();
    }

    function balanceOfBatch(address[] calldata, uint256[] calldata)
        external pure returns (uint256[] memory)
    {
        revert NotYetActivated();
    }

    function isApprovedForAll(address, address) external pure returns (bool) {
        revert NotYetActivated();
    }

    function uri(uint256) external pure returns (string memory) {
        revert NotYetActivated();
    }

    // ─── ERC-1155 mutators — CONSTITUTIONALLY DISABLED ─────────────────────

    /// @dev Soulbound. ERC-1155 transfers are not permitted for land classes.
    function safeTransferFrom(address, address, uint256, uint256, bytes calldata) external pure {
        revert LandClassSoulbound();
    }

    function safeBatchTransferFrom(address, address, uint256[] calldata, uint256[] calldata, bytes calldata) external pure {
        revert LandClassSoulbound();
    }

    function setApprovalForAll(address, bool) external pure {
        revert LandClassSoulbound();
    }

    // ─── Aggregate views (R0 stubs) ────────────────────────────────────────

    /// @notice Total area-in-trust by land class (m²).
    function totalAreaByClass(uint256) external pure returns (uint256) {
        revert NotYetActivated();
    }

    /// @notice List of parcels (PublicLandRegistry tokenIds) of a given class.
    function parcelsByClass(uint256, uint256 /*offset*/, uint256 /*limit*/)
        external pure returns (uint256[] memory)
    {
        revert NotYetActivated();
    }

    // ─── Mirror flow (called by AnchorBridge on donation) ──────────────────

    /// @notice Records a parcel's class membership. Called by AnchorBridge only.
    /// @dev R0: reverts NotYetActivated.
    function recordClassFromAnchor(
        uint256 /*landTokenId*/,
        uint256 /*classId*/,
        uint256 /*areaM2*/
    ) external pure {
        revert NotYetActivated();
    }

    // ─── ERC-165 ───────────────────────────────────────────────────────────

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == type(IERC1155Minimal).interfaceId    // 0xd9b67a26
            || interfaceId == type(IERC1155MetadataURIMinimal).interfaceId // 0x0e89341c
            || interfaceId == bytes4(0x01ffc9a7);                  // ERC-165
    }

    // ─── Activation ────────────────────────────────────────────────────────

    function activate(
        address, /*_publicLandRegistry*/
        address, /*_anchorBridge*/
        bytes[] calldata, /*councilSigs*/
        address[] calldata /*councilSigners*/
    ) external pure {
        revert NotYetActivated();
    }
}
