// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/// @title AgentRuntimeLeaseEscrow
///
/// @notice GCC bond escrow for ADR-2604301200 Web4-style autonomous agent
///         runtime leases. A lease represents an offchain CPU/memory/GPU/
///         storage/network reservation. The contract does not provision k8s
///         resources; it only locks the resource bond, records the policy hash,
///         supports renewal/hibernation, and gives the owner/governance slasher
///         a bounded penalty path.
///
/// @dev    Lease details are stored as compact hashes. The public details live
///         in ERC-8004 agentURI, atproto records, RisingWave operational rows,
///         and IPFS/B2 policy documents. Slashing applies only to the locked
///         lease bond, not to arbitrary balances.
contract AgentRuntimeLeaseEscrow {
    IERC20 public immutable gcc;

    address public owner;
    address public treasury;

    uint256 public constant MIN_LEASE_PERIOD = 1 hours;
    uint256 public constant MAX_LEASE_PERIOD = 365 days;

    enum LeaseStatus {
        None,
        Active,
        Hibernated,
        Released,
        Slashed
    }

    struct Lease {
        address lessee;
        bytes32 agentDidHash;
        bytes32 resourceHash;
        bytes32 policyHash;
        uint256 bond;
        uint64 startsAt;
        uint64 expiresAt;
        LeaseStatus status;
    }

    mapping(bytes32 leaseId => Lease) internal _leases;

    event LeaseReserved(
        bytes32 indexed leaseId,
        address indexed lessee,
        bytes32 indexed agentDidHash,
        bytes32 resourceHash,
        bytes32 policyHash,
        uint256 bond,
        uint64 startsAt,
        uint64 expiresAt
    );
    event LeaseRenewed(bytes32 indexed leaseId, uint256 addedBond, uint64 newExpiresAt, uint256 totalBond);
    event LeaseHibernated(bytes32 indexed leaseId, address indexed lessee, uint256 refundAmount);
    event LeaseReleased(bytes32 indexed leaseId, address indexed lessee, uint256 refundAmount);
    event LeaseSlashed(
        bytes32 indexed leaseId,
        bytes32 indexed reasonHash,
        address indexed beneficiary,
        uint256 amount,
        uint256 remainingBond
    );
    event TreasuryUpdated(address indexed oldTreasury, address indexed newTreasury);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    error NotOwner();
    error NotAuthorized();
    error ZeroAddress();
    error EmptyLeaseId();
    error EmptyHash();
    error InvalidLeasePeriod();
    error LeaseAlreadyExists();
    error LeaseNotFound();
    error LeaseNotActive();
    error LeaseNotExpired();
    error InsufficientBond(uint256 requested, uint256 available);
    error TransferFailed();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(IERC20 gcc_, address treasury_, address owner_) {
        if (address(gcc_) == address(0) || treasury_ == address(0)) revert ZeroAddress();
        gcc = gcc_;
        treasury = treasury_;
        owner = owner_ == address(0) ? msg.sender : owner_;
        emit OwnershipTransferred(address(0), owner);
        emit TreasuryUpdated(address(0), treasury_);
    }

    /// @notice Reserve a runtime lease by locking `bond` GCC. Caller must have
    ///         approved this contract first. `resourceHash` should commit to
    ///         CPU/memory/GPU/storage/network limits. `policyHash` should commit
    ///         to the slash policy and hibernation rules.
    function reserveLease(
        bytes32 leaseId,
        bytes32 agentDidHash,
        bytes32 resourceHash,
        bytes32 policyHash,
        uint256 bond,
        uint64 leasePeriodSec
    ) external {
        if (leaseId == bytes32(0)) revert EmptyLeaseId();
        if (agentDidHash == bytes32(0) || resourceHash == bytes32(0) || policyHash == bytes32(0)) {
            revert EmptyHash();
        }
        if (leasePeriodSec < MIN_LEASE_PERIOD || leasePeriodSec > MAX_LEASE_PERIOD) {
            revert InvalidLeasePeriod();
        }
        if (_leases[leaseId].status != LeaseStatus.None) revert LeaseAlreadyExists();

        bool ok = gcc.transferFrom(msg.sender, address(this), bond);
        if (!ok) revert TransferFailed();

        uint64 startsAt = uint64(block.timestamp);
        uint64 expiresAt = startsAt + leasePeriodSec;
        _leases[leaseId] = Lease({
            lessee: msg.sender,
            agentDidHash: agentDidHash,
            resourceHash: resourceHash,
            policyHash: policyHash,
            bond: bond,
            startsAt: startsAt,
            expiresAt: expiresAt,
            status: LeaseStatus.Active
        });

        emit LeaseReserved(leaseId, msg.sender, agentDidHash, resourceHash, policyHash, bond, startsAt, expiresAt);
    }

    /// @notice Extend an active lease. `additionalBond` can be zero when only
    ///         extending time under a policy that permits it.
    function renewLease(bytes32 leaseId, uint256 additionalBond, uint64 extendSec) external {
        Lease storage lease = _activeLease(leaseId);
        if (msg.sender != lease.lessee && msg.sender != owner) revert NotAuthorized();
        if (extendSec == 0 || extendSec > MAX_LEASE_PERIOD) revert InvalidLeasePeriod();

        if (additionalBond > 0) {
            bool ok = gcc.transferFrom(msg.sender, address(this), additionalBond);
            if (!ok) revert TransferFailed();
            lease.bond += additionalBond;
        }

        uint256 newExpiresAt = uint256(lease.expiresAt) + extendSec;
        if (newExpiresAt > type(uint64).max) revert InvalidLeasePeriod();
        // forge-lint: disable-next-line(unsafe-typecast)
        lease.expiresAt = uint64(newExpiresAt);

        emit LeaseRenewed(leaseId, additionalBond, lease.expiresAt, lease.bond);
    }

    /// @notice Graceful shutdown path. Use when the agent cannot renew but has
    ///         no outstanding accepted jobs. This is not a penalty.
    function hibernate(bytes32 leaseId) external {
        Lease storage lease = _activeLease(leaseId);
        if (msg.sender != lease.lessee && msg.sender != owner) revert NotAuthorized();

        uint256 refund = lease.bond;
        address lessee = lease.lessee;
        lease.bond = 0;
        lease.status = LeaseStatus.Hibernated;

        if (refund > 0 && !gcc.transfer(lessee, refund)) revert TransferFailed();
        emit LeaseHibernated(leaseId, lessee, refund);
    }

    /// @notice Release an expired lease and refund remaining bond. Anyone can
    ///         submit the transaction; funds always return to the lessee.
    function releaseExpired(bytes32 leaseId) external {
        Lease storage lease = _activeLease(leaseId);
        if (block.timestamp < lease.expiresAt) revert LeaseNotExpired();

        uint256 refund = lease.bond;
        address lessee = lease.lessee;
        lease.bond = 0;
        lease.status = LeaseStatus.Released;

        if (refund > 0 && !gcc.transfer(lessee, refund)) revert TransferFailed();
        emit LeaseReleased(leaseId, lessee, refund);
    }

    /// @notice Slash an active lease for runtime no-show, false receipt,
    ///         resource overuse, social spam, child-org abuse, or similar
    ///         policy violation. If beneficiary is zero, treasury receives it.
    function slashLease(bytes32 leaseId, uint256 amount, address beneficiary, bytes32 reasonHash) external onlyOwner {
        Lease storage lease = _activeLease(leaseId);
        if (amount > lease.bond) revert InsufficientBond(amount, lease.bond);

        address receiver = beneficiary == address(0) ? treasury : beneficiary;
        lease.bond -= amount;
        if (lease.bond == 0) {
            lease.status = LeaseStatus.Slashed;
        }

        if (amount > 0 && !gcc.transfer(receiver, amount)) revert TransferFailed();
        emit LeaseSlashed(leaseId, reasonHash, receiver, amount, lease.bond);
    }

    function setTreasury(address newTreasury) external onlyOwner {
        if (newTreasury == address(0)) revert ZeroAddress();
        emit TreasuryUpdated(treasury, newTreasury);
        treasury = newTreasury;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroAddress();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function leases(bytes32 leaseId) external view returns (Lease memory) {
        return _leases[leaseId];
    }

    function _activeLease(bytes32 leaseId) internal view returns (Lease storage lease) {
        lease = _leases[leaseId];
        if (lease.status == LeaseStatus.None) revert LeaseNotFound();
        if (lease.status != LeaseStatus.Active) revert LeaseNotActive();
    }
}
