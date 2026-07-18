// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

/**
 * @title CohortLifecycle
 * @notice K2 cohort lifecycle state machine on Base L2 per ADR-2605212040 §D5.
 *
 *         K2 is the technical primitive; yobel (`orgs/etzhayyim/com-etzhayyim-yobel/`) is one
 *         scriptural consumer that binds the 50-year cohort to scriptural
 *         release semantics. This contract makes no assumptions about
 *         cohort cadence — yobel and other consumers manage their own
 *         timers off-chain and call into the lifecycle transitions here.
 *
 * @dev State machine:
 *
 *      Genesis ──┬──> Active ───┬──> Fissioned (one cohort splits into N children)
 *                │              │
 *                │              └──> Decommissioned
 *                │
 *                └──> (rejected before Active — Decommissioned with reason="rejected")
 *
 *      Resume is a special transition: Fissioned or Decommissioned can
 *      return to Active under Council governance vote. The state machine
 *      records every transition with its block number so off-chain history
 *      is reconstructable from logs.
 *
 *      Council 5-of-7 Safe owns all transitions. No upgrade, no pause.
 */
contract CohortLifecycle {
    address public owner;

    enum Status {
        Unknown,         // 0 — not present
        Genesis,         // 1 — created, not yet activated
        Active,          // 2 — running
        Fissioned,       // 3 — split into child cohorts; parent retired
        Decommissioned,  // 4 — terminal (until resumed)
        Resumed          // 5 — special transitional flag back to Active
    }

    struct Cohort {
        bytes32 slugHash;            // keccak256 of the cohort handle (e.g. "yobel-cycle-5786")
        Status status;
        uint96 genesisBlock;
        uint96 lastTransitionBlock;
        bytes32 reasonHash;          // keccak256 of free-text reason for last transition; 0 if none
    }

    mapping(bytes32 => Cohort) public cohorts;       // cohortId => Cohort
    mapping(bytes32 => bytes32) public slugToCohort; // slugHash => cohortId

    /// @dev fission edges: parent cohortId => array of child cohortIds.
    mapping(bytes32 => bytes32[]) private _fissionChildren;
    /// @dev reverse edge: child cohortId => parent cohortId (0 if not fission-born).
    mapping(bytes32 => bytes32) public fissionParent;

    event OwnerChanged(address indexed previousOwner, address indexed newOwner);
    event CohortStarted(bytes32 indexed cohortId, bytes32 indexed slugHash);
    event CohortActivated(bytes32 indexed cohortId);
    event CohortFissioned(bytes32 indexed parentId, bytes32[] childIds);
    event CohortDecommissioned(bytes32 indexed cohortId, bytes32 reasonHash);
    event CohortResumed(bytes32 indexed cohortId, Status fromStatus);

    error NotOwner();
    error ZeroAddress();
    error InvalidArgument();
    error CohortExists();
    error CohortNotFound();
    error InvalidTransition(Status from, Status to);
    error SlugTaken();

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

    // ─── Transitions ───────────────────────────────────────────────────

    /// @notice Genesis transition — create a new cohort in `Genesis` status.
    function startGenesis(bytes32 slugHash) external onlyOwner returns (bytes32 cohortId) {
        if (slugHash == bytes32(0)) revert InvalidArgument();
        if (slugToCohort[slugHash] != bytes32(0)) revert SlugTaken();
        cohortId = keccak256(abi.encode("k2-cohort", slugHash, block.number, block.chainid));
        if (cohorts[cohortId].status != Status.Unknown) revert CohortExists();
        cohorts[cohortId] = Cohort({
            slugHash: slugHash,
            status: Status.Genesis,
            genesisBlock: uint96(block.number),
            lastTransitionBlock: uint96(block.number),
            reasonHash: bytes32(0)
        });
        slugToCohort[slugHash] = cohortId;
        emit CohortStarted(cohortId, slugHash);
    }

    /// @notice Genesis → Active.
    function activate(bytes32 cohortId) external onlyOwner {
        Cohort storage c = cohorts[cohortId];
        if (c.status == Status.Unknown) revert CohortNotFound();
        if (c.status != Status.Genesis && c.status != Status.Resumed) {
            revert InvalidTransition(c.status, Status.Active);
        }
        c.status = Status.Active;
        c.lastTransitionBlock = uint96(block.number);
        emit CohortActivated(cohortId);
    }

    /// @notice Active → Fissioned. The parent retires; children are
    ///         created in Genesis status (the operator subsequently
    ///         calls activate() per child).
    function fission(bytes32 parentId, bytes32[] calldata childSlugHashes)
        external
        onlyOwner
        returns (bytes32[] memory childIds)
    {
        Cohort storage p = cohorts[parentId];
        if (p.status == Status.Unknown) revert CohortNotFound();
        if (p.status != Status.Active) revert InvalidTransition(p.status, Status.Fissioned);
        if (childSlugHashes.length == 0) revert InvalidArgument();

        childIds = new bytes32[](childSlugHashes.length);
        for (uint256 i = 0; i < childSlugHashes.length; i++) {
            bytes32 slug = childSlugHashes[i];
            if (slug == bytes32(0)) revert InvalidArgument();
            if (slugToCohort[slug] != bytes32(0)) revert SlugTaken();
            bytes32 childId = keccak256(
                abi.encode("k2-cohort-fission", parentId, slug, i, block.number, block.chainid)
            );
            cohorts[childId] = Cohort({
                slugHash: slug,
                status: Status.Genesis,
                genesisBlock: uint96(block.number),
                lastTransitionBlock: uint96(block.number),
                reasonHash: bytes32(0)
            });
            slugToCohort[slug] = childId;
            fissionParent[childId] = parentId;
            childIds[i] = childId;
        }
        _fissionChildren[parentId] = childIds;
        p.status = Status.Fissioned;
        p.lastTransitionBlock = uint96(block.number);
        emit CohortFissioned(parentId, childIds);
    }

    /// @notice Active or Genesis → Decommissioned. Terminal until resume().
    function decommission(bytes32 cohortId, bytes32 reasonHash) external onlyOwner {
        Cohort storage c = cohorts[cohortId];
        if (c.status == Status.Unknown) revert CohortNotFound();
        if (c.status != Status.Active && c.status != Status.Genesis) {
            revert InvalidTransition(c.status, Status.Decommissioned);
        }
        c.status = Status.Decommissioned;
        c.lastTransitionBlock = uint96(block.number);
        c.reasonHash = reasonHash;
        emit CohortDecommissioned(cohortId, reasonHash);
    }

    /// @notice Decommissioned or Fissioned → Resumed (then activate() to reach Active).
    function resume(bytes32 cohortId) external onlyOwner {
        Cohort storage c = cohorts[cohortId];
        if (c.status == Status.Unknown) revert CohortNotFound();
        Status from = c.status;
        if (from != Status.Decommissioned && from != Status.Fissioned) {
            revert InvalidTransition(from, Status.Resumed);
        }
        c.status = Status.Resumed;
        c.lastTransitionBlock = uint96(block.number);
        emit CohortResumed(cohortId, from);
    }

    // ─── Read accessors ────────────────────────────────────────────────

    function getCohort(bytes32 cohortId) external view returns (Cohort memory) {
        return cohorts[cohortId];
    }

    function resolveSlug(bytes32 slugHash) external view returns (bytes32) {
        return slugToCohort[slugHash];
    }

    function getFissionChildren(bytes32 parentId) external view returns (bytes32[] memory) {
        return _fissionChildren[parentId];
    }
}
