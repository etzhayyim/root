// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {AdherentRegistry} from "./AdherentRegistry.sol";
import {Constitution} from "./Constitution.sol";

/**
 * @title Governance
 * @notice On-chain governance for the etzhayyim religious voluntary
 *         association. Minimal custom Governor (not OZ-imported) so the
 *         deployment has zero external dependencies. Per ADR-2605172300
 *         §8. Apache-2.0.
 *
 * @dev Constitutional invariants enforced here:
 *
 *        - **1 SBT = 1 vote.** Voting weight is binary per active SBT,
 *          not weighted by holding size or token balance. There is no
 *          transferable share token; that is locked by
 *          Constitution.getConstant("no_transferable_share").
 *
 *        - **Active-voter requirement.** A vote may be cast only if
 *          AdherentRegistry.isActive(tokenId, active_window_secs) at
 *          the moment of voting. Members who have not attested in the
 *          window are not eligible to vote on this proposal.
 *
 *        - **Quorum.** A proposal passes only if `forVotes` reach a
 *          fraction (Constitution.getMutable("quorum_bps")) of the
 *          AdherentRegistry total minted (less revoked) AT THE TIME OF
 *          SNAPSHOT (voteStart). Quorum may not fall below
 *          Constitution.getConstant("quorum_floor_bps") (constitutional
 *          floor) — even if governance proposes a lower mutable value,
 *          this contract rejects vote tallies against the floor.
 *
 *        - **Timelock.** A passed proposal cannot execute until after
 *          Constitution.getMutable("timelock_secs") have elapsed since
 *          {queue}. Anyone may then call {execute}; the calls in the
 *          proposal are dispatched to their targets.
 *
 *      Constitution binding:
 *        Constitution.bindGovernance(<this contract>) MUST be called
 *        before {execute} can change constitutional parameters. The
 *        same address acts as `governance` for KishaStream / Phenotype
 *        / TreasuryMirror governance-gated setters.
 *
 *      What this contract intentionally lacks (vs. OZ Governor):
 *        - extensible voting modules (it is a single hard-coded module);
 *        - delegation (1 SBT = 1 vote rules it out);
 *        - on-chain proposal description text (only an IPFS CID hash
 *          is stored; the rationale lives off-chain);
 *        - off-chain signature voting (S3 votes are direct tx; passkey
 *          + paymaster relayer in S3.1).
 */
contract Governance {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error NotAdherent();
    error NotActive(uint256 tokenId);
    error AlreadyVoted(uint256 proposalId, uint256 tokenId);
    error UnknownProposal(uint256 proposalId);
    error InvalidState(uint8 expected, uint8 actual);
    error VoteWindowClosed();
    error VoteWindowOpen();
    error NotQueueable();
    error NotExecutable();
    error TimelockNotElapsed();
    error TargetsCalldatasMismatch();
    error EmptyTargets();
    error ExecutionFailed(uint256 index, bytes returndata);
    error QuorumBelowFloor();

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event ProposalCreated(
        uint256 indexed proposalId,
        address indexed proposer,
        uint256 indexed proposerTokenId,
        address[] targets,
        bytes[] calldatas,
        bytes32 descCid,
        uint64 voteStart,
        uint64 voteEnd
    );
    event VoteCast(
        uint256 indexed proposalId,
        uint256 indexed tokenId,
        uint8 choice, // 0 against, 1 for, 2 abstain
        address voter
    );
    event ProposalQueued(uint256 indexed proposalId, uint64 eta);
    event ProposalExecuted(uint256 indexed proposalId);
    event ProposalCanceled(uint256 indexed proposalId, bytes32 reasonCid);

    // -------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------

    enum State {
        Pending,    // 0 — not used: voteStart is set to block.timestamp so proposals are immediately Active
        Active,     // 1 — voting in progress
        Defeated,   // 2 — voting ended, did not pass
        Succeeded,  // 3 — voting ended, passed; not yet queued
        Queued,     // 4 — queued, timelock running
        Executed,   // 5 — executed
        Canceled,   // 6 — canceled by proposer or governance
        Expired     // 7 — queued but grace period passed without execution
    }

    struct Proposal {
        address proposer;
        uint256 proposerTokenId;
        address[] targets;
        bytes[] calldatas;
        bytes32 descCid;
        uint64 voteStart;
        uint64 voteEnd;
        uint64 eta;          // earliest execution time after queue (0 until queued)
        uint64 snapshotTotal; // total adherent count at voteStart (denominator)
        uint64 forVotes;
        uint64 againstVotes;
        uint64 abstainVotes;
        bool executed;
        bool canceled;
        bool queued;
    }

    // -------------------------------------------------------------------
    // Immutable wiring
    // -------------------------------------------------------------------

    AdherentRegistry public immutable registry;
    Constitution     public immutable constitution;

    /// @notice Voting period (seconds). Hardcoded; future S3.1 may move
    ///         to constitution as a mutable parameter.
    uint64 public constant VOTING_PERIOD_SECS = 3 days;

    /// @notice Grace period after eta during which the proposal may be
    ///         executed. After it elapses, the proposal Expires.
    uint64 public constant EXECUTION_GRACE_SECS = 14 days;

    // Canonical mutable keys read at vote-tally time.
    bytes32 private constant K_QUORUM_BPS         = keccak256("quorum_bps");
    bytes32 private constant K_TIMELOCK_SECS      = keccak256("timelock_secs");
    bytes32 private constant K_ACTIVE_WINDOW_SECS = keccak256("active_window_secs");
    bytes32 private constant K_QUORUM_FLOOR_BPS   = keccak256("quorum_floor_bps");

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    uint256 public proposalCount;
    mapping(uint256 => Proposal) private _proposals;
    /// @notice (proposalId, tokenId) → voted? Prevents double-vote per
    ///         SBT even if the wallet rotates.
    mapping(uint256 => mapping(uint256 => bool)) public hasVoted;

    // -------------------------------------------------------------------
    // Construction
    // -------------------------------------------------------------------

    constructor(AdherentRegistry registry_, Constitution constitution_) {
        registry = registry_;
        constitution = constitution_;
    }

    // -------------------------------------------------------------------
    // Proposal lifecycle
    // -------------------------------------------------------------------

    /**
     * @notice Submit a new proposal. Caller must be an adherent and
     *         must be active in the trailing window.
     *
     * @dev voteStart is set to ``block.timestamp`` (no voting delay);
     *      voteEnd is ``voteStart + VOTING_PERIOD_SECS``.
     */
    function propose(
        address[] calldata targets,
        bytes[] calldata calldatas,
        bytes32 descCid
    ) external returns (uint256 proposalId) {
        if (targets.length == 0) revert EmptyTargets();
        if (targets.length != calldatas.length) revert TargetsCalldatasMismatch();

        uint256 tokenId = registry.tokenOf(msg.sender);
        if (tokenId == 0) revert NotAdherent();
        uint64 window = uint64(uint256(constitution.getMutable(K_ACTIVE_WINDOW_SECS)));
        if (!registry.isActive(tokenId, window)) revert NotActive(tokenId);

        proposalId = ++proposalCount;
        uint64 voteStart = uint64(block.timestamp);
        uint64 voteEnd = voteStart + VOTING_PERIOD_SECS;

        Proposal storage p = _proposals[proposalId];
        p.proposer = msg.sender;
        p.proposerTokenId = tokenId;
        // Deep copy targets/calldatas to storage. The loop is bounded
        // by the size of the proposal — gas is the proposer's problem.
        for (uint256 i = 0; i < targets.length; ++i) {
            p.targets.push(targets[i]);
            p.calldatas.push(calldatas[i]);
        }
        p.descCid = descCid;
        p.voteStart = voteStart;
        p.voteEnd = voteEnd;
        p.snapshotTotal = uint64(registry.totalMinted());

        emit ProposalCreated(
            proposalId, msg.sender, tokenId, targets, calldatas, descCid, voteStart, voteEnd
        );
    }

    /**
     * @notice Cast a vote. Choice: 0 = against, 1 = for, 2 = abstain.
     *         Caller must be the holder of an active SBT and not have
     *         voted on this proposal yet.
     */
    function castVote(uint256 proposalId, uint8 choice) external {
        Proposal storage p = _proposals[proposalId];
        if (p.voteStart == 0) revert UnknownProposal(proposalId);
        if (block.timestamp < p.voteStart) revert VoteWindowClosed();
        if (block.timestamp > p.voteEnd) revert VoteWindowClosed();

        uint256 tokenId = registry.tokenOf(msg.sender);
        if (tokenId == 0) revert NotAdherent();
        uint64 window = uint64(uint256(constitution.getMutable(K_ACTIVE_WINDOW_SECS)));
        if (!registry.isActive(tokenId, window)) revert NotActive(tokenId);
        if (hasVoted[proposalId][tokenId]) revert AlreadyVoted(proposalId, tokenId);

        hasVoted[proposalId][tokenId] = true;
        if (choice == 0) {
            p.againstVotes += 1;
        } else if (choice == 1) {
            p.forVotes += 1;
        } else if (choice == 2) {
            p.abstainVotes += 1;
        } else {
            revert InvalidState(0, choice);
        }

        emit VoteCast(proposalId, tokenId, choice, msg.sender);
    }

    /**
     * @notice Queue a Succeeded proposal for timelocked execution.
     *         Anyone may call (the proposer is not privileged).
     */
    function queue(uint256 proposalId) external {
        Proposal storage p = _proposals[proposalId];
        if (p.voteStart == 0) revert UnknownProposal(proposalId);
        if (state(proposalId) != State.Succeeded) revert NotQueueable();
        uint64 tl = uint64(uint256(constitution.getMutable(K_TIMELOCK_SECS)));
        p.queued = true;
        p.eta = uint64(block.timestamp) + tl;
        emit ProposalQueued(proposalId, p.eta);
    }

    /**
     * @notice Execute a Queued proposal whose eta has elapsed and whose
     *         grace period has not. Dispatches each (target, calldata)
     *         pair via low-level call.
     */
    function execute(uint256 proposalId) external payable {
        Proposal storage p = _proposals[proposalId];
        if (p.voteStart == 0) revert UnknownProposal(proposalId);
        State st = state(proposalId);
        if (st != State.Queued) revert NotExecutable();
        if (block.timestamp < p.eta) revert TimelockNotElapsed();

        p.executed = true;
        for (uint256 i = 0; i < p.targets.length; ++i) {
            (bool ok, bytes memory ret) = p.targets[i].call(p.calldatas[i]);
            if (!ok) revert ExecutionFailed(i, ret);
        }
        emit ProposalExecuted(proposalId);
    }

    /**
     * @notice Cancel a proposal. The proposer may cancel before queuing;
     *         after queueing the proposal can only be canceled by a
     *         separate governance vote (i.e., a new proposal calling
     *         {cancel} on this contract — there is no other path).
     */
    function cancel(uint256 proposalId, bytes32 reasonCid) external {
        Proposal storage p = _proposals[proposalId];
        if (p.voteStart == 0) revert UnknownProposal(proposalId);
        State st = state(proposalId);
        if (st == State.Executed || st == State.Canceled) revert NotQueueable();
        if (msg.sender == address(this)) {
            // self-call via governance: always allowed
            p.canceled = true;
        } else if (msg.sender == p.proposer && !p.queued) {
            p.canceled = true;
        } else {
            revert NotQueueable();
        }
        emit ProposalCanceled(proposalId, reasonCid);
    }

    // -------------------------------------------------------------------
    // Reads
    // -------------------------------------------------------------------

    function state(uint256 proposalId) public view returns (State) {
        Proposal storage p = _proposals[proposalId];
        if (p.voteStart == 0) revert UnknownProposal(proposalId);
        if (p.canceled) return State.Canceled;
        if (p.executed) return State.Executed;
        if (p.queued) {
            if (block.timestamp > p.eta + EXECUTION_GRACE_SECS) return State.Expired;
            return State.Queued;
        }
        if (block.timestamp <= p.voteEnd) return State.Active;

        // Voting concluded. Apply quorum + majority.
        uint16 quorumBps = uint16(uint256(constitution.getMutable(K_QUORUM_BPS)));
        uint16 floor_ = uint16(uint256(constitution.getConstant(K_QUORUM_FLOOR_BPS)));
        if (quorumBps < floor_) {
            // Treat under-floor quorum as if at floor — protects against
            // a governance proposal that sets quorum_bps below the
            // constitutional floor accidentally.
            quorumBps = floor_;
        }
        uint256 denom = uint256(p.snapshotTotal);
        if (denom == 0) return State.Defeated;
        // Quorum applies to total cast votes (for + abstain),
        // not just `for`. Matches OZ Governor default.
        uint256 turnout = uint256(p.forVotes) + uint256(p.abstainVotes);
        if (turnout * 10_000 < denom * quorumBps) return State.Defeated;
        if (uint256(p.forVotes) <= uint256(p.againstVotes)) return State.Defeated;
        return State.Succeeded;
    }

    function getProposal(uint256 proposalId) external view returns (Proposal memory) {
        Proposal storage p = _proposals[proposalId];
        if (p.voteStart == 0) revert UnknownProposal(proposalId);
        return p;
    }
}
