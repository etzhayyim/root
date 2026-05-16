// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

// ERC-1271: allows contract signers (e.g. Gnosis Safe) as arbiter.
interface IERC1271 {
    function isValidSignature(bytes32 hash, bytes memory signature) external view returns (bytes4);
}
bytes4 constant ERC1271_MAGIC_VALUE = 0x1626ba7e;

/// @title ClaimStakeEscrow — claim-level "正しいと得・嘘で損" primitive.
///
/// @notice ADR-2604261717 Phase 1. Each claim flows through:
///
///         1. `postClaim` — claimant deposits `bond` GCC; the claim enters
///            Pending and a `challengePeriod` window opens.
///         2a. No challenge is filed before the window closes →
///             `claimUnchallenged` returns the bond to the claimant.
///         2b. Anyone files `challenge` with `counterBond ≥ bond * minCounterBondBps /
///             10_000`; the claim moves to Challenged and an arbiter
///             resolution window opens.
///         3a. `settle` is called with an arbiter ECDSA signature over
///             `keccak256(claimId, claimWins, address(this), chainid)`. The
///             contract distributes per the 85 / 10 / 5 split:
///               - Upheld   →  claimant += bond + counter * 0.85
///                            treasury += counter * 0.10
///                            reward   += counter * 0.05
///               - Slashed  →  challenger += counter + bond * 0.85
///                            treasury   += bond * 0.10
///                            reward     += bond * 0.05
///         3b. `noShow` — arbiter doesn't sign within `arbiterTimeout`;
///             both sides refunded, treasury / reward get nothing.
///
/// @dev    Game theory: with `bond = b`, challenge probability `P > 0`,
///         and an honest arbiter, EV(lie) = -P * b < 0 < EV(truth) once
///         the reward subsidy `r` makes EV(truth) ≥ ε.
///
/// @dev    Mirrors the MurakumoEscrow shape (ADR-0074 Phase 2-A) but
///         scopes a different escrow lifecycle. CEI strict, no
///         ReentrancyGuard needed (single-token, no external callbacks
///         on success path; failed transfers revert immediately).
contract ClaimStakeEscrow {
    IERC20 public immutable gcc;

    address public owner;
    address public arbiter;
    address public treasury;
    address public rewardPool;

    /// 7 days. Hard cap (90 days) enforced on `postClaim`.
    uint64 public constant DEFAULT_CHALLENGE_PERIOD = 7 days;
    uint64 public constant MAX_CHALLENGE_PERIOD     = 90 days;
    uint64 public constant MIN_CHALLENGE_PERIOD     = 60;

    /// After a claim is challenged the arbiter has this many seconds to
    /// sign an outcome before either side can `noShow` to a full refund.
    uint64 public constant ARBITER_TIMEOUT = 14 days;

    uint16 public constant BPS_DENOMINATOR = 10_000;

    /// Default 50% — keeps frivolous challenges from being free.
    uint16 public minCounterBondBps;
    /// 85 / 10 / 5 (winner / treasury / reward).
    uint16 public winnerBps;
    uint16 public treasuryBps;
    uint16 public rewardBps;
    uint256 public minBond;

    enum State { None, Pending, Challenged, Upheld, Slashed, Refunded }

    struct Claim {
        bytes32 claimId;
        bytes32 didHash;
        bytes32 atRecordCid;
        uint256 bond;
        uint64  postedAt;
        uint64  challengePeriod;
        address claimant;
        State   state;
    }
    struct Challenge {
        bytes32 challengerDidHash;
        uint256 counterBond;
        uint64  postedAt;
        address challenger;
    }

    mapping(bytes32 claimId => Claim) internal _claims;
    mapping(bytes32 claimId => Challenge) internal _challenges;

    event ClaimPosted(
        bytes32 indexed claimId,
        address indexed claimant,
        bytes32 indexed didHash,
        bytes32 atRecordCid,
        uint256 bond,
        uint64  challengePeriod
    );
    event ClaimChallenged(
        bytes32 indexed claimId,
        address indexed challenger,
        bytes32 indexed challengerDidHash,
        uint256 counterBond
    );
    event ClaimUpheld(
        bytes32 indexed claimId,
        uint256 claimantPayout,
        uint256 treasuryAmount,
        uint256 rewardAmount
    );
    event ClaimSlashed(
        bytes32 indexed claimId,
        uint256 challengerPayout,
        uint256 treasuryAmount,
        uint256 rewardAmount
    );
    event ClaimRefunded(bytes32 indexed claimId, uint256 claimantAmount, uint256 challengerAmount);
    event ArbiterUpdated(address indexed oldArbiter, address indexed newArbiter);
    event TreasuryUpdated(address indexed oldTreasury, address indexed newTreasury);
    event RewardPoolUpdated(address indexed oldRewardPool, address indexed newRewardPool);
    event SplitPolicyUpdated(uint16 winnerBps, uint16 treasuryBps, uint16 rewardBps, uint16 minCounterBondBps, uint256 minBond);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    error NotOwner();
    error ZeroAddress();
    error ZeroId();
    error ClaimAlreadyExists();
    error ClaimNotFound();
    error InvalidState();
    error ChallengeWindowClosed();
    error ChallengeWindowOpen();
    error ArbiterTimeoutNotReached();
    error ArbiterStillResponsive();
    error InvalidArbiterSignature();
    error InvalidSplitPolicy();
    error InvalidChallengePeriod();
    error BondTooSmall();
    error CounterBondTooSmall();
    error TransferFailed();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(
        IERC20 gcc_,
        address arbiter_,
        address treasury_,
        address rewardPool_,
        address owner_
    ) {
        if (arbiter_ == address(0) || treasury_ == address(0) || rewardPool_ == address(0)) revert ZeroAddress();
        gcc = gcc_;
        arbiter = arbiter_;
        treasury = treasury_;
        rewardPool = rewardPool_;
        owner = owner_ == address(0) ? msg.sender : owner_;

        winnerBps   = 8_500;
        treasuryBps = 1_000;
        rewardBps   = 500;
        minCounterBondBps = 5_000; // 50%
        minBond = 1 ether;          // 1 GCC

        emit OwnershipTransferred(address(0), owner);
        emit ArbiterUpdated(address(0), arbiter_);
        emit TreasuryUpdated(address(0), treasury_);
        emit RewardPoolUpdated(address(0), rewardPool_);
        emit SplitPolicyUpdated(winnerBps, treasuryBps, rewardBps, minCounterBondBps, minBond);
    }

    // ── Claimant path ────────────────────────────────────────────────────────

    /// @notice Lock `bond` GCC against `claimId`. Caller must
    ///         `gcc.approve(escrow, bond)` first.
    function postClaim(
        bytes32 claimId,
        bytes32 didHash,
        bytes32 atRecordCid,
        uint256 bond,
        uint64 challengePeriod
    ) external {
        if (claimId == bytes32(0)) revert ZeroId();
        if (_claims[claimId].state != State.None) revert ClaimAlreadyExists();
        if (bond < minBond) revert BondTooSmall();
        if (challengePeriod == 0) challengePeriod = DEFAULT_CHALLENGE_PERIOD;
        if (challengePeriod < MIN_CHALLENGE_PERIOD || challengePeriod > MAX_CHALLENGE_PERIOD) revert InvalidChallengePeriod();

        bool ok = gcc.transferFrom(msg.sender, address(this), bond);
        if (!ok) revert TransferFailed();

        _claims[claimId] = Claim({
            claimId: claimId,
            didHash: didHash,
            atRecordCid: atRecordCid,
            bond: bond,
            postedAt: uint64(block.timestamp),
            challengePeriod: challengePeriod,
            claimant: msg.sender,
            state: State.Pending
        });

        emit ClaimPosted(claimId, msg.sender, didHash, atRecordCid, bond, challengePeriod);
    }

    // ── Challenger path ──────────────────────────────────────────────────────

    /// @notice Lock `counterBond` against `claimId`. Caller must
    ///         `gcc.approve(escrow, counterBond)` first.
    function challenge(
        bytes32 claimId,
        bytes32 challengerDidHash,
        uint256 counterBond
    ) external {
        Claim storage c = _claims[claimId];
        if (c.state == State.None) revert ClaimNotFound();
        if (c.state != State.Pending) revert InvalidState();
        if (block.timestamp >= uint256(c.postedAt) + uint256(c.challengePeriod)) revert ChallengeWindowClosed();

        uint256 minCounter = (c.bond * minCounterBondBps) / BPS_DENOMINATOR;
        if (counterBond < minCounter) revert CounterBondTooSmall();

        bool ok = gcc.transferFrom(msg.sender, address(this), counterBond);
        if (!ok) revert TransferFailed();

        c.state = State.Challenged;
        _challenges[claimId] = Challenge({
            challengerDidHash: challengerDidHash,
            counterBond: counterBond,
            postedAt: uint64(block.timestamp),
            challenger: msg.sender
        });

        emit ClaimChallenged(claimId, msg.sender, challengerDidHash, counterBond);
    }

    // ── Settlement paths ─────────────────────────────────────────────────────

    /// @notice Path A: no challenge filed within window → return bond.
    function claimUnchallenged(bytes32 claimId) external {
        Claim storage c = _claims[claimId];
        if (c.state == State.None) revert ClaimNotFound();
        if (c.state != State.Pending) revert InvalidState();
        if (block.timestamp < uint256(c.postedAt) + uint256(c.challengePeriod)) revert ChallengeWindowOpen();

        c.state = State.Refunded;
        uint256 bond = c.bond;
        if (!gcc.transfer(c.claimant, bond)) revert TransferFailed();

        emit ClaimRefunded(claimId, bond, 0);
    }

    /// @notice Path B: arbiter has ruled. `arbiterSig` is an ECDSA over
    ///         `keccak256(claimId, claimWins, address(this), chainid)`
    ///         using `\x19Ethereum Signed Message:\n32`.
    function settle(bytes32 claimId, bool claimWins, bytes calldata arbiterSig) external {
        Claim storage c = _claims[claimId];
        if (c.state == State.None) revert ClaimNotFound();
        if (c.state != State.Challenged) revert InvalidState();

        bytes32 payloadHash = keccak256(abi.encode(claimId, claimWins, address(this), block.chainid));
        bytes32 ethSignedHash = ECDSA.toEthSignedMessageHash(payloadHash);
        if (!_isValidArbiterSig(payloadHash, ethSignedHash, arbiterSig)) revert InvalidArbiterSignature();

        Challenge storage ch = _challenges[claimId];
        uint256 bond = c.bond;
        uint256 counter = ch.counterBond;

        if (claimWins) {
            uint256 winnerSlice   = (counter * winnerBps)   / BPS_DENOMINATOR;
            uint256 treasurySlice = (counter * treasuryBps) / BPS_DENOMINATOR;
            uint256 rewardSlice   = counter - winnerSlice - treasurySlice; // exact, sums to counter
            uint256 claimantPayout = bond + winnerSlice;

            c.state = State.Upheld;

            if (!gcc.transfer(c.claimant, claimantPayout)) revert TransferFailed();
            if (treasurySlice > 0 && !gcc.transfer(treasury, treasurySlice)) revert TransferFailed();
            if (rewardSlice   > 0 && !gcc.transfer(rewardPool, rewardSlice)) revert TransferFailed();

            emit ClaimUpheld(claimId, claimantPayout, treasurySlice, rewardSlice);
        } else {
            uint256 winnerSlice   = (bond * winnerBps)   / BPS_DENOMINATOR;
            uint256 treasurySlice = (bond * treasuryBps) / BPS_DENOMINATOR;
            uint256 rewardSlice   = bond - winnerSlice - treasurySlice;
            uint256 challengerPayout = counter + winnerSlice;

            c.state = State.Slashed;

            if (!gcc.transfer(ch.challenger, challengerPayout)) revert TransferFailed();
            if (treasurySlice > 0 && !gcc.transfer(treasury, treasurySlice)) revert TransferFailed();
            if (rewardSlice   > 0 && !gcc.transfer(rewardPool, rewardSlice)) revert TransferFailed();

            emit ClaimSlashed(claimId, challengerPayout, treasurySlice, rewardSlice);
        }
    }

    /// @notice Path C: arbiter didn't sign in time → both sides refunded.
    ///         Either party may invoke after the timeout elapses.
    function noShow(bytes32 claimId) external {
        Claim storage c = _claims[claimId];
        if (c.state == State.None) revert ClaimNotFound();
        if (c.state != State.Challenged) revert InvalidState();

        Challenge storage ch = _challenges[claimId];
        if (block.timestamp < uint256(ch.postedAt) + uint256(ARBITER_TIMEOUT)) revert ArbiterStillResponsive();

        c.state = State.Refunded;
        uint256 bond = c.bond;
        uint256 counter = ch.counterBond;

        if (!gcc.transfer(c.claimant, bond)) revert TransferFailed();
        if (counter > 0 && !gcc.transfer(ch.challenger, counter)) revert TransferFailed();

        emit ClaimRefunded(claimId, bond, counter);
    }

    // ── Signature verification ───────────────────────────────────────────────

    /// @dev EOA path: ECDSA.recover over eth-signed hash (backward compat with
    ///      bot-signed settlements). Contract path: ERC-1271 isValidSignature
    ///      over the raw payloadHash (Safe applies its own EIP-712 domain).
    function _isValidArbiterSig(
        bytes32 payloadHash,
        bytes32 ethSignedHash,
        bytes calldata sig
    ) internal view returns (bool) {
        // EOA path: non-reverting recovery so short/malformed sigs fall through.
        bytes memory sigMem = sig; // copy calldata → memory for tryRecover overload
        (address recovered, ECDSA.RecoverError err) = ECDSA.tryRecover(ethSignedHash, sigMem);
        if (err == ECDSA.RecoverError.NoError && recovered == arbiter) return true;
        // ERC-1271 path: arbiter is a contract (e.g. Gnosis Safe).
        if (arbiter.code.length == 0) return false;
        (bool ok, bytes memory ret) = arbiter.staticcall(
            abi.encodeWithSelector(IERC1271.isValidSignature.selector, payloadHash, sig)
        );
        return ok && ret.length >= 32 && abi.decode(ret, (bytes4)) == ERC1271_MAGIC_VALUE;
    }

    // ── Admin ────────────────────────────────────────────────────────────────

    function setSplitPolicy(uint16 newWinnerBps, uint16 newTreasuryBps, uint16 newRewardBps, uint16 newMinCounterBondBps, uint256 newMinBond) external onlyOwner {
        if (uint256(newWinnerBps) + newTreasuryBps + newRewardBps != BPS_DENOMINATOR) revert InvalidSplitPolicy();
        if (newMinCounterBondBps == 0 || newMinCounterBondBps > BPS_DENOMINATOR) revert InvalidSplitPolicy();
        winnerBps = newWinnerBps;
        treasuryBps = newTreasuryBps;
        rewardBps = newRewardBps;
        minCounterBondBps = newMinCounterBondBps;
        minBond = newMinBond;
        emit SplitPolicyUpdated(newWinnerBps, newTreasuryBps, newRewardBps, newMinCounterBondBps, newMinBond);
    }

    function setArbiter(address newArbiter) external onlyOwner {
        if (newArbiter == address(0)) revert ZeroAddress();
        emit ArbiterUpdated(arbiter, newArbiter);
        arbiter = newArbiter;
    }

    function setTreasury(address newTreasury) external onlyOwner {
        if (newTreasury == address(0)) revert ZeroAddress();
        emit TreasuryUpdated(treasury, newTreasury);
        treasury = newTreasury;
    }

    function setRewardPool(address newRewardPool) external onlyOwner {
        if (newRewardPool == address(0)) revert ZeroAddress();
        emit RewardPoolUpdated(rewardPool, newRewardPool);
        rewardPool = newRewardPool;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert NotOwner();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    // ── Views ────────────────────────────────────────────────────────────────

    function claims(bytes32 claimId) external view returns (Claim memory) {
        return _claims[claimId];
    }

    function challenges(bytes32 claimId) external view returns (Challenge memory) {
        return _challenges[claimId];
    }
}
