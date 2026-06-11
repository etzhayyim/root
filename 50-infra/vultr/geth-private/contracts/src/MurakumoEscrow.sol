// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

import {MurakumoRegistry} from "./MurakumoRegistry.sol";

// ERC-1271: allows contract signers (e.g. Gnosis Safe) as oracle.
interface IERC1271 {
    function isValidSignature(bytes32 hash, bytes memory signature) external view returns (bytes4);
}
bytes4 constant ERC1271_MAGIC_VALUE = 0x1626ba7e;

/// @title MurakumoEscrow
///
/// @notice Per-job GCC escrow + signed settlement for Murakumo inference
///         (ADR-0074 Phase 2-A). Each request goes through three steps:
///
///         1. `submitJob` — caller deposits GCC for a specific operator.
///         2. `settleJob` — etzhayyim routing-gateway oracle signs the actual
///            cost; the escrow splits between operator (70%) / treasury
///            (25%) / referrer (5%) and refunds the remainder.
///         3. `refund` — if no settle within `SETTLEMENT_TIMEOUT`, the
///            caller can claw back the deposit themselves.
///
/// @dev    The split policy is parameter-controlled (`setSplitPolicy`)
///         but defaults to 70/25/5. If the caller doesn't designate a
///         `referrer`, the referrer slice rolls up into treasury.
///
///         The signed settlement payload is
///           `keccak256(jobId, actualCost, address(this), block.chainid)`
///         passed through the standard "\x19Ethereum Signed Message:\n32"
///         prefix so any wallet can produce it. The signing key (`oracle`)
///         is rotated independently from `owner` — Phase 3 multisig will
///         replace `oracle` with an aggregator while keeping `owner` as
///         a separate emergency-pause authority.
contract MurakumoEscrow {
    IERC20 public immutable gcc;
    MurakumoRegistry public immutable registry;

    address public owner;
    address public oracle;
    address public treasury;

    uint256 public constant SETTLEMENT_TIMEOUT = 5 minutes;
    uint16 public constant BPS_DENOMINATOR = 10_000;

    uint16 public operatorBps;
    uint16 public treasuryBps;
    uint16 public referrerBps;

    struct Job {
        address client;
        bytes32 operatorDid;
        bytes32 modelId;
        uint256 deposit;
        // 0x0 = no referrer; treasury then absorbs the referrer slice.
        address referrer;
        uint64 submittedAt;
        bool settled;
        bool refunded;
    }

    mapping(bytes32 jobId => Job) internal _jobs;

    event JobSubmitted(
        bytes32 indexed jobId,
        address indexed client,
        bytes32 indexed operatorDid,
        bytes32 modelId,
        uint256 deposit,
        address referrer
    );
    event JobSettled(
        bytes32 indexed jobId,
        bytes32 indexed operatorDid,
        uint256 actualCost,
        uint256 operatorAmount,
        uint256 treasuryAmount,
        uint256 referrerAmount,
        uint256 refundAmount
    );
    event JobRefunded(bytes32 indexed jobId, address indexed client, uint256 amount);
    event SplitPolicyUpdated(uint16 operatorBps, uint16 treasuryBps, uint16 referrerBps);
    event OracleUpdated(address indexed oldOracle, address indexed newOracle);
    event TreasuryUpdated(address indexed oldTreasury, address indexed newTreasury);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    error NotOwner();
    error JobAlreadyExists();
    error JobNotFound();
    error JobAlreadySettled();
    error JobAlreadyRefunded();
    error TimeoutNotReached();
    error InvalidOracleSignature();
    error InvalidSplitPolicy();
    error CostExceedsDeposit();
    error TransferFailed();
    error ZeroAddress();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(
        IERC20 gcc_,
        MurakumoRegistry registry_,
        address oracle_,
        address treasury_,
        address owner_
    ) {
        if (oracle_ == address(0) || treasury_ == address(0)) revert ZeroAddress();
        gcc = gcc_;
        registry = registry_;
        oracle = oracle_;
        treasury = treasury_;
        owner = owner_ == address(0) ? msg.sender : owner_;
        operatorBps = 7_000;
        treasuryBps = 2_500;
        referrerBps = 500;
        emit OwnershipTransferred(address(0), owner);
        emit OracleUpdated(address(0), oracle_);
        emit TreasuryUpdated(address(0), treasury_);
        emit SplitPolicyUpdated(operatorBps, treasuryBps, referrerBps);
    }

    /// @notice Deposit `deposit` GCC into escrow for `jobId`. Caller must
    ///         have called `gcc.approve(escrow, deposit)` first.
    function submitJob(
        bytes32 jobId,
        bytes32 operatorDid,
        bytes32 modelId,
        uint256 deposit,
        address referrer
    ) external {
        if (jobId == bytes32(0)) revert JobNotFound();
        if (_jobs[jobId].submittedAt != 0) revert JobAlreadyExists();

        bool ok = gcc.transferFrom(msg.sender, address(this), deposit);
        if (!ok) revert TransferFailed();

        _jobs[jobId] = Job({
            client: msg.sender,
            operatorDid: operatorDid,
            modelId: modelId,
            deposit: deposit,
            referrer: referrer,
            submittedAt: uint64(block.timestamp),
            settled: false,
            refunded: false
        });
        emit JobSubmitted(jobId, msg.sender, operatorDid, modelId, deposit, referrer);
    }

    /// @notice Settle job with oracle-signed actual cost. Anyone can
    ///         submit the tx as long as the signature is valid — the
    ///         oracle key is the trust anchor, not the caller.
    function settleJob(bytes32 jobId, uint256 actualCost, bytes calldata oracleSig) external {
        Job storage job = _jobs[jobId];
        if (job.submittedAt == 0) revert JobNotFound();
        if (job.settled) revert JobAlreadySettled();
        if (job.refunded) revert JobAlreadyRefunded();
        if (actualCost > job.deposit) revert CostExceedsDeposit();

        // Verify the oracle's signature over (jobId, actualCost, escrow,
        // chainId). Including the contract address + chainId rules out
        // cross-instance and cross-chain replay.
        bytes32 payloadHash = keccak256(abi.encode(jobId, actualCost, address(this), block.chainid));
        bytes32 ethSignedHash = ECDSA.toEthSignedMessageHash(payloadHash);
        if (!_isValidOracleSig(payloadHash, ethSignedHash, oracleSig)) revert InvalidOracleSignature();

        // Pay out from the deposit. Refund (deposit - actualCost) to the
        // client; split actualCost three ways. If referrer is unset, its
        // slice rolls into treasury so totals always sum to actualCost.
        address operatorPayout = registry.payoutAddressOf(job.operatorDid);
        uint256 operatorAmount = (actualCost * operatorBps) / BPS_DENOMINATOR;
        uint256 referrerAmount = job.referrer == address(0) ? 0 : (actualCost * referrerBps) / BPS_DENOMINATOR;
        uint256 treasuryAmount = actualCost - operatorAmount - referrerAmount;
        uint256 refundAmount = job.deposit - actualCost;

        job.settled = true;

        if (operatorAmount > 0) {
            if (!gcc.transfer(operatorPayout, operatorAmount)) revert TransferFailed();
        }
        if (treasuryAmount > 0) {
            if (!gcc.transfer(treasury, treasuryAmount)) revert TransferFailed();
        }
        if (referrerAmount > 0) {
            if (!gcc.transfer(job.referrer, referrerAmount)) revert TransferFailed();
        }
        if (refundAmount > 0) {
            if (!gcc.transfer(job.client, refundAmount)) revert TransferFailed();
        }

        emit JobSettled(jobId, job.operatorDid, actualCost, operatorAmount, treasuryAmount, referrerAmount, refundAmount);
    }

    /// @notice Caller-initiated refund after the settlement window. No
    ///         oracle signature required — the timeout itself is the
    ///         consent. Anyone can submit the tx; the funds always
    ///         return to the original client.
    function refund(bytes32 jobId) external {
        Job storage job = _jobs[jobId];
        if (job.submittedAt == 0) revert JobNotFound();
        if (job.settled) revert JobAlreadySettled();
        if (job.refunded) revert JobAlreadyRefunded();
        if (block.timestamp < uint256(job.submittedAt) + SETTLEMENT_TIMEOUT) revert TimeoutNotReached();

        job.refunded = true;
        if (!gcc.transfer(job.client, job.deposit)) revert TransferFailed();
        emit JobRefunded(jobId, job.client, job.deposit);
    }

    // ── Signature verification ───────────────────────────────────────────────

    /// @dev EOA path: ECDSA.recover over eth-signed hash (backward compat with
    ///      bot-signed settlements). Contract path: ERC-1271 isValidSignature
    ///      over the raw payloadHash (Safe applies its own EIP-712 domain).
    function _isValidOracleSig(
        bytes32 payloadHash,
        bytes32 ethSignedHash,
        bytes calldata sig
    ) internal view returns (bool) {
        // EOA path: non-reverting recovery so short/malformed sigs fall through.
        bytes memory sigMem = sig; // copy calldata → memory for tryRecover overload
        (address recovered, ECDSA.RecoverError err) = ECDSA.tryRecover(ethSignedHash, sigMem);
        if (err == ECDSA.RecoverError.NoError && recovered == oracle) return true;
        // ERC-1271 path: oracle is a contract (e.g. Gnosis Safe).
        if (oracle.code.length == 0) return false;
        (bool ok, bytes memory ret) = oracle.staticcall(
            abi.encodeWithSelector(IERC1271.isValidSignature.selector, payloadHash, sig)
        );
        return ok && ret.length >= 32 && abi.decode(ret, (bytes4)) == ERC1271_MAGIC_VALUE;
    }

    function setSplitPolicy(uint16 newOperatorBps, uint16 newTreasuryBps, uint16 newReferrerBps) external onlyOwner {
        if (uint256(newOperatorBps) + newTreasuryBps + newReferrerBps != BPS_DENOMINATOR) revert InvalidSplitPolicy();
        operatorBps = newOperatorBps;
        treasuryBps = newTreasuryBps;
        referrerBps = newReferrerBps;
        emit SplitPolicyUpdated(newOperatorBps, newTreasuryBps, newReferrerBps);
    }

    function setOracle(address newOracle) external onlyOwner {
        if (newOracle == address(0)) revert ZeroAddress();
        emit OracleUpdated(oracle, newOracle);
        oracle = newOracle;
    }

    function setTreasury(address newTreasury) external onlyOwner {
        if (newTreasury == address(0)) revert ZeroAddress();
        emit TreasuryUpdated(treasury, newTreasury);
        treasury = newTreasury;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert NotOwner();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function jobs(bytes32 jobId) external view returns (Job memory) {
        return _jobs[jobId];
    }
}
