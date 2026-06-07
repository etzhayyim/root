// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

/// @title DeployRegistry
/// @notice On-chain provenance ledger for `etzhayyim deploy` (ADR-0074 Phase 2-A).
///         Each `recordDeploy` call writes an immutable receipt for one app
///         deployment: who deployed, what version of which app nanoid, and
///         the SHA-256 of the build artifacts + kotodama.jsonld manifest.
/// @dev    State is intentionally minimal. The authoritative payload lives in
///         the `Deployed` event (free in calldata, indexed by nanoid for cheap
///         filtering). The on-chain mapping just exposes the latest version
///         per nanoid for synchronous `getLatest()` reads from Workers and
///         `etzhayyim deploy` itself when validating an upgrade.
///
///         Authorization model for now: a single `deployer` role (== sealer).
///         Org multisig (ADR-0074 §"Authority Multisig") will replace this
///         with a per-app `requiredApprovers` list in Phase 3 — at which
///         point `recordDeploy` becomes a contract-only call from the
///         multisig proxy. Until then we trust whichever key signs the tx.
contract DeployRegistry {
    struct DeployRecord {
        bytes32 nanoid;        // app nanoid (8-char alpha-start, padded right with 0x00)
        bytes32 contentHash;   // sha256(kotodama.jsonld + build artifacts), 32 bytes
        bytes32 commitSha;     // git commit (40-char ascii, right-padded)
        uint64  deployedAt;    // block.timestamp
        uint32  versionSeq;    // monotonic per nanoid (1, 2, 3, …)
        address deployer;      // tx.origin / wallet that signed recordDeploy
        bytes16 kotodamaCid;   // optional CID v1 truncated; bytes16(0) = none
        // 11 bytes free in this struct's last slot for future fields
    }

    address public owner;
    bool public openDeploy;    // false = only `deployer`/owner; true = any caller can record

    /// @dev Latest record per nanoid (nanoid → DeployRecord). New records
    /// don't overwrite history — that lives in the `Deployed` event log.
    mapping(bytes32 => DeployRecord) public latest;
    mapping(bytes32 => uint32)        public versionCount;

    event Deployed(
        bytes32 indexed nanoid,
        uint32  indexed versionSeq,
        address indexed deployer,
        bytes32 contentHash,
        bytes32 commitSha,
        bytes16 kotodamaCid,
        uint64  deployedAt
    );

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event OpenDeploySet(bool openDeploy);

    error NotOwner();
    error NotAuthorized();
    error EmptyNanoid();
    error EmptyContentHash();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(address owner_) {
        owner = owner_ == address(0) ? msg.sender : owner_;
        emit OwnershipTransferred(address(0), owner);
    }

    /// @notice Record a new deploy receipt. Caller must be the owner unless
    ///         `openDeploy` is true (Phase 3 will swap this for a multisig
    ///         requirement; do NOT enable openDeploy in production yet).
    function recordDeploy(
        bytes32 nanoid,
        bytes32 contentHash,
        bytes32 commitSha,
        bytes16 kotodamaCid
    ) external returns (uint32 versionSeq) {
        if (!openDeploy && msg.sender != owner) revert NotAuthorized();
        if (nanoid == bytes32(0)) revert EmptyNanoid();
        if (contentHash == bytes32(0)) revert EmptyContentHash();

        versionSeq = ++versionCount[nanoid];
        DeployRecord memory rec = DeployRecord({
            nanoid: nanoid,
            contentHash: contentHash,
            commitSha: commitSha,
            deployedAt: uint64(block.timestamp),
            versionSeq: versionSeq,
            deployer: msg.sender,
            kotodamaCid: kotodamaCid
        });
        latest[nanoid] = rec;

        emit Deployed(nanoid, versionSeq, msg.sender, contentHash, commitSha, kotodamaCid, rec.deployedAt);
    }

    /// @notice Read the most recent deploy receipt for an app. Reverts in
    ///         the caller's frame if the app has never been recorded
    ///         (versionCount == 0) so workers can distinguish "no record"
    ///         from "record exists with zero hash".
    function getLatest(bytes32 nanoid) external view returns (DeployRecord memory) {
        if (versionCount[nanoid] == 0) revert EmptyNanoid();
        return latest[nanoid];
    }

    function setOpenDeploy(bool open) external onlyOwner {
        openDeploy = open;
        emit OpenDeploySet(open);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert NotOwner();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}
