// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

/**
 * @title EtzhayyimAuthz
 * @notice Root identity registry for etzhayyim per ADR-2605212030.
 *
 *         Each `root` is (dwebHandleHash, activeKey, optional vendor predecessor).
 *         The public DID surface is `did:web:<handle>.etzhayyim.com`; the
 *         on-chain authority is `did:erc725:base:<this-contract>#<rootIdHex>`.
 *         The two are bound via `dwebHandleHash` (keccak256 of the handle).
 *
 * @dev Phase α (this deployment): Council multisig owns provisioning and
 *      vendor-root mirroring. Key rotation is permissionless but requires
 *      a signature from the current active key. Permissionless self-
 *      provisioning via ERC-4337 is deferred to a follow-up ADR.
 *
 *      No proxy. No upgrade. Council can deactivate roots; deactivation is
 *      irreversible (must be re-provisioned under a new rootId if needed).
 */
contract EtzhayyimAuthz {
    // ─── Storage ────────────────────────────────────────────────────────

    address public owner;

    struct Root {
        bytes32 dwebHandleHash;             // keccak256(bytes("<handle>.etzhayyim.com"))
        address activeKey;                  // current signing key (EOA / smart-wallet-recovered)
        address predecessorVendorAddr;      // vendor-side wallet for migrated roots; 0 for greenfield
        bytes32 predecessorVendorRootHash;  // hash of vendor did:erc725:etzhayyim:260425:* DID; 0 for greenfield
        uint96 createdBlock;
        uint96 lastRotatedBlock;
        bool active;
    }

    mapping(bytes32 => Root) public roots;
    mapping(bytes32 => bytes32) public dwebToRoot;

    // ─── Events ─────────────────────────────────────────────────────────

    event OwnerChanged(address indexed previousOwner, address indexed newOwner);
    event RootProvisioned(bytes32 indexed rootId, bytes32 indexed dwebHandleHash, address activeKey);
    event VendorRootMirrored(
        bytes32 indexed rootId,
        bytes32 indexed predecessorVendorRootHash,
        address predecessorVendorAddr
    );
    event RootKeyRotated(bytes32 indexed rootId, address oldKey, address newKey);
    event RootDeactivated(bytes32 indexed rootId);

    // ─── Errors ─────────────────────────────────────────────────────────

    error NotOwner();
    error ZeroAddress();
    error InvalidArgument();
    error DwebTaken();
    error RootExists();
    error RootNotFound();
    error RootInactive();
    error NotActiveKey();
    error InvalidSignature();

    // ─── Construction ───────────────────────────────────────────────────

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

    // ─── Provisioning ───────────────────────────────────────────────────

    /// @notice Mint a new greenfield etzhayyim root identity.
    function provisionRoot(bytes32 dwebHandleHash, address activeKey)
        external
        onlyOwner
        returns (bytes32 rootId)
    {
        if (dwebHandleHash == bytes32(0)) revert InvalidArgument();
        if (activeKey == address(0)) revert ZeroAddress();
        if (dwebToRoot[dwebHandleHash] != bytes32(0)) revert DwebTaken();

        rootId = keccak256(
            abi.encode("etzhayyim-authz-root", dwebHandleHash, activeKey, block.number, block.chainid)
        );
        if (roots[rootId].createdBlock != 0) revert RootExists();

        roots[rootId] = Root({
            dwebHandleHash: dwebHandleHash,
            activeKey: activeKey,
            predecessorVendorAddr: address(0),
            predecessorVendorRootHash: bytes32(0),
            createdBlock: uint96(block.number),
            lastRotatedBlock: uint96(block.number),
            active: true
        });
        dwebToRoot[dwebHandleHash] = rootId;
        emit RootProvisioned(rootId, dwebHandleHash, activeKey);
    }

    /// @notice Mint an etzhayyim root that mirrors an existing vendor-issued ERC725 root.
    /// @dev Vendor continuity proof is recorded as data; on-chain signature
    ///      verification of the vendor key is intentionally NOT enforced here —
    ///      Council (owner) is expected to verify the proof off-chain before
    ///      calling this function. The recorded fields make the link auditable.
    function mirrorVendorRoot(
        bytes32 dwebHandleHash,
        address newActiveKey,
        bytes32 predecessorVendorRootHash,
        address predecessorVendorAddr
    ) external onlyOwner returns (bytes32 rootId) {
        if (dwebHandleHash == bytes32(0)) revert InvalidArgument();
        if (newActiveKey == address(0)) revert ZeroAddress();
        if (predecessorVendorRootHash == bytes32(0)) revert InvalidArgument();
        if (predecessorVendorAddr == address(0)) revert ZeroAddress();
        if (dwebToRoot[dwebHandleHash] != bytes32(0)) revert DwebTaken();

        rootId = keccak256(
            abi.encode(
                "etzhayyim-authz-mirror",
                dwebHandleHash,
                newActiveKey,
                predecessorVendorRootHash,
                block.number,
                block.chainid
            )
        );
        if (roots[rootId].createdBlock != 0) revert RootExists();

        roots[rootId] = Root({
            dwebHandleHash: dwebHandleHash,
            activeKey: newActiveKey,
            predecessorVendorAddr: predecessorVendorAddr,
            predecessorVendorRootHash: predecessorVendorRootHash,
            createdBlock: uint96(block.number),
            lastRotatedBlock: uint96(block.number),
            active: true
        });
        dwebToRoot[dwebHandleHash] = rootId;
        emit RootProvisioned(rootId, dwebHandleHash, newActiveKey);
        emit VendorRootMirrored(rootId, predecessorVendorRootHash, predecessorVendorAddr);
    }

    // ─── Key rotation ───────────────────────────────────────────────────

    /// @notice Rotate the active signing key of a root. Caller must produce
    ///         a signature from the current active key over the rotation
    ///         digest. Rotation is permissionless w.r.t. msg.sender; the
    ///         signature is the gating authority.
    function rotateKey(bytes32 rootId, address newKey, bytes calldata sigOldKey) external {
        Root storage r = roots[rootId];
        if (r.createdBlock == 0) revert RootNotFound();
        if (!r.active) revert RootInactive();
        if (newKey == address(0)) revert ZeroAddress();

        bytes32 inner = keccak256(
            abi.encode(
                "etzhayyim-authz-rotate",
                address(this),
                block.chainid,
                rootId,
                newKey,
                r.lastRotatedBlock
            )
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", inner));
        address recovered = _recover(digest, sigOldKey);
        if (recovered == address(0)) revert InvalidSignature();
        if (recovered != r.activeKey) revert NotActiveKey();

        address old = r.activeKey;
        r.activeKey = newKey;
        r.lastRotatedBlock = uint96(block.number);
        emit RootKeyRotated(rootId, old, newKey);
    }

    // ─── Deactivation ──────────────────────────────────────────────────

    function deactivateRoot(bytes32 rootId) external onlyOwner {
        Root storage r = roots[rootId];
        if (r.createdBlock == 0) revert RootNotFound();
        if (!r.active) revert RootInactive();
        r.active = false;
        emit RootDeactivated(rootId);
    }

    // ─── Read accessors ────────────────────────────────────────────────

    function resolveDwebHandle(bytes32 dwebHandleHash) external view returns (bytes32 rootId, Root memory data) {
        rootId = dwebToRoot[dwebHandleHash];
        if (rootId != bytes32(0)) {
            data = roots[rootId];
        }
    }

    function isActive(bytes32 rootId) external view returns (bool) {
        Root storage r = roots[rootId];
        return r.createdBlock != 0 && r.active;
    }

    function getProvenance(bytes32 rootId) external view returns (Root memory) {
        return roots[rootId];
    }

    // ─── Internal: ECDSA recover ───────────────────────────────────────

    function _recover(bytes32 digest, bytes calldata sig) internal pure returns (address) {
        if (sig.length != 65) return address(0);
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly {
            r := calldataload(sig.offset)
            s := calldataload(add(sig.offset, 32))
            v := byte(0, calldataload(add(sig.offset, 64)))
        }
        if (v < 27) v += 27;
        if (v != 27 && v != 28) return address(0);
        // EIP-2 low-s requirement
        if (uint256(s) > 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0) return address(0);
        return ecrecover(digest, v, r, s);
    }
}
