// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2605192145 (Public Fund Architecture).
// 1 SBT = 1 vote governance over the Public Fund Safe (5-of-7 Gnosis Safe).
// Quorum 20% of total minted SBTs, approval 50% of cast (for+against) votes,
// 7-day voting period, 48-hour timelock.

pragma solidity 0.8.27;

interface IAdherentRegistry {
    function isActive(uint256 tokenId, uint64 windowSecs) external view returns (bool);
    function tokenOf(address) external view returns (uint256);
    function totalMinted() external view returns (uint256);
}

interface IChartersComplianceRegistry {
    function isCouncilMember(address) external view returns (bool);
    function isNonAlignedAddress(address subject) external view returns (bool);
    function isNonAlignedTokenId(uint256 tokenId) external view returns (bool);
}

contract PublicFundGovernance {
    enum ProposalState { Pending, Active, Defeated, Succeeded, Queued, Executed, Cancelled }
    enum Choice { Abstain, For, Against }

    struct Grant {
        address proposer;
        bytes32 missionAxisHash;
        bytes32 evidenceCid;
        uint64 proposedAt;
        uint64 votingDeadline;
        uint64 timelockEnd;
        ProposalState state;
        uint256 forVotes;
        uint256 againstVotes;
        uint256 abstainVotes;
        // Stored in mapping below to avoid struct-with-arrays gas hit:
        //   recipients[proposalId]
        //   amounts[proposalId]
    }

    mapping(bytes32 => Grant) public grants;
    mapping(bytes32 => address[]) public recipients;
    mapping(bytes32 => uint256[]) public amounts;
    mapping(bytes32 => mapping(uint256 => bool)) public hasVoted;  // proposalId -> sbtTokenId -> voted

    IAdherentRegistry public immutable adherent;
    IChartersComplianceRegistry public immutable charters;
    address public immutable publicFundSafe;

    uint256 public constant QUORUM_BPS = 2_000;      // 20% of totalMinted
    uint256 public constant APPROVAL_BPS = 5_000;    // 50% of (for + against)
    uint64 public constant VOTING_PERIOD = 7 days;
    uint64 public constant TIMELOCK = 48 hours;
    uint64 public constant ACTIVE_WINDOW = 30 days;
    uint256 public constant BPS_DENOMINATOR = 10_000;

    uint256 public proposalCounter;

    event Proposed(
        bytes32 indexed proposalId,
        address indexed proposer,
        bytes32 indexed missionAxisHash,
        address[] recipients,
        uint256[] amounts,
        bytes32 evidenceCid,
        uint64 votingDeadline
    );
    event Voted(bytes32 indexed proposalId, uint256 indexed sbtTokenId, Choice choice);
    event Queued(bytes32 indexed proposalId, uint64 timelockEnd);
    event Executed(bytes32 indexed proposalId);
    event Cancelled(bytes32 indexed proposalId, bytes32 reasonCid);

    error EmptyRecipients();
    error LengthMismatch();
    error ZeroAmount();
    error RecipientNonAligned(address recipient);
    error ProposerNonAligned();
    error AlreadyVoted(uint256 sbtTokenId);
    error VoterNotActive(uint256 sbtTokenId);
    error VoterNonAligned(uint256 sbtTokenId);
    error NotVoterOwner();
    error InvalidChoice();
    error InvalidStateForOperation(ProposalState got, ProposalState need);
    error VotingNotOver();
    error TimelockNotElapsed();
    error InsufficientCouncilSigners();
    error NotCouncilMember(address signer);

    constructor(
        IAdherentRegistry _adherent,
        IChartersComplianceRegistry _charters,
        address _publicFundSafe
    ) {
        require(_publicFundSafe != address(0), "publicFundSafe=0");
        adherent = _adherent;
        charters = _charters;
        publicFundSafe = _publicFundSafe;
    }

    // ─── Proposal lifecycle ─────────────────────────────────────────

    function propose(
        address[] calldata _recipients,
        uint256[] calldata _amounts,
        bytes32 missionAxisHash,
        bytes32 evidenceCid
    ) external returns (bytes32 proposalId) {
        if (_recipients.length == 0) revert EmptyRecipients();
        if (_recipients.length != _amounts.length) revert LengthMismatch();
        if (charters.isNonAlignedAddress(msg.sender)) revert ProposerNonAligned();
        for (uint256 i = 0; i < _recipients.length; i++) {
            if (_amounts[i] == 0) revert ZeroAmount();
            if (charters.isNonAlignedAddress(_recipients[i])) revert RecipientNonAligned(_recipients[i]);
        }

        proposalId = keccak256(abi.encode(
            msg.sender, missionAxisHash, evidenceCid, ++proposalCounter, block.timestamp
        ));

        Grant storage g = grants[proposalId];
        g.proposer = msg.sender;
        g.missionAxisHash = missionAxisHash;
        g.evidenceCid = evidenceCid;
        g.proposedAt = uint64(block.timestamp);
        g.votingDeadline = uint64(block.timestamp) + VOTING_PERIOD;
        g.state = ProposalState.Active;

        // Copy recipients + amounts to storage (calldata→storage copy)
        for (uint256 i = 0; i < _recipients.length; i++) {
            recipients[proposalId].push(_recipients[i]);
            amounts[proposalId].push(_amounts[i]);
        }

        emit Proposed(proposalId, msg.sender, missionAxisHash, _recipients, _amounts, evidenceCid, g.votingDeadline);
    }

    function vote(bytes32 proposalId, Choice choice) external {
        Grant storage g = grants[proposalId];
        if (g.state != ProposalState.Active) revert InvalidStateForOperation(g.state, ProposalState.Active);
        if (block.timestamp > g.votingDeadline) {
            // Auto-advance state on first attempted post-deadline op
            _tallyAndAdvance(proposalId);
            revert VotingNotOver();  // re-revert in case state didn't change to Succeeded
        }

        uint256 sbtTokenId = adherent.tokenOf(msg.sender);
        if (sbtTokenId == 0) revert NotVoterOwner();
        if (!adherent.isActive(sbtTokenId, ACTIVE_WINDOW)) revert VoterNotActive(sbtTokenId);
        if (charters.isNonAlignedTokenId(sbtTokenId)) revert VoterNonAligned(sbtTokenId);
        if (hasVoted[proposalId][sbtTokenId]) revert AlreadyVoted(sbtTokenId);

        hasVoted[proposalId][sbtTokenId] = true;
        if (choice == Choice.For) g.forVotes++;
        else if (choice == Choice.Against) g.againstVotes++;
        else if (choice == Choice.Abstain) g.abstainVotes++;
        else revert InvalidChoice();

        emit Voted(proposalId, sbtTokenId, choice);
    }

    function queue(bytes32 proposalId) external {
        Grant storage g = grants[proposalId];
        if (block.timestamp <= g.votingDeadline) revert VotingNotOver();
        if (g.state == ProposalState.Active) _tallyAndAdvance(proposalId);
        if (g.state != ProposalState.Succeeded) revert InvalidStateForOperation(g.state, ProposalState.Succeeded);

        g.state = ProposalState.Queued;
        g.timelockEnd = uint64(block.timestamp) + TIMELOCK;
        emit Queued(proposalId, g.timelockEnd);
    }

    function execute(bytes32 proposalId) external {
        Grant storage g = grants[proposalId];
        if (g.state != ProposalState.Queued) revert InvalidStateForOperation(g.state, ProposalState.Queued);
        if (block.timestamp < g.timelockEnd) revert TimelockNotElapsed();

        g.state = ProposalState.Executed;

        // NOTE: The Safe (5-of-7) is the asset custody. PublicFundGovernance
        // does NOT directly transfer; it emits the Executed event so the
        // Safe operator can sign + submit the disbursement Safe-tx in a
        // single batch. Alternatively, the Safe can be configured with a
        // module that triggers on Executed events (out of scope for v0).

        emit Executed(proposalId);
    }

    /// @notice Council Lv6+ ≥3 multisig may cancel a proposal at any stage
    ///         prior to execution. Used for Charter Compliance discovery
    ///         post-proposal or for emergency mission-incompatibility.
    function cancel(
        bytes32 proposalId,
        bytes32 reasonCid,
        bytes[] calldata councilSigs,
        address[] calldata councilSigners
    ) external {
        Grant storage g = grants[proposalId];
        if (g.state == ProposalState.Executed || g.state == ProposalState.Cancelled) {
            revert InvalidStateForOperation(g.state, ProposalState.Active);
        }
        _verifyCouncilQuorum(councilSigs, councilSigners);
        g.state = ProposalState.Cancelled;
        emit Cancelled(proposalId, reasonCid);
    }

    // ─── Views ──────────────────────────────────────────────────────

    function getRecipients(bytes32 proposalId) external view returns (address[] memory) {
        return recipients[proposalId];
    }

    function getAmounts(bytes32 proposalId) external view returns (uint256[] memory) {
        return amounts[proposalId];
    }

    function quorumThreshold() public view returns (uint256) {
        return (adherent.totalMinted() * QUORUM_BPS) / BPS_DENOMINATOR;
    }

    function stateOf(bytes32 proposalId) external view returns (ProposalState) {
        return grants[proposalId].state;
    }

    // ─── Internal ───────────────────────────────────────────────────

    function _tallyAndAdvance(bytes32 proposalId) internal {
        Grant storage g = grants[proposalId];
        uint256 total = g.forVotes + g.againstVotes + g.abstainVotes;
        uint256 quorum = quorumThreshold();
        if (total < quorum) {
            g.state = ProposalState.Defeated;
            return;
        }
        uint256 forAgainst = g.forVotes + g.againstVotes;
        if (forAgainst == 0) {
            g.state = ProposalState.Defeated;
            return;
        }
        // Approval = forVotes / (for + against) >= 50%
        if ((g.forVotes * BPS_DENOMINATOR) / forAgainst >= APPROVAL_BPS) {
            g.state = ProposalState.Succeeded;
        } else {
            g.state = ProposalState.Defeated;
        }
    }

    function _verifyCouncilQuorum(bytes[] calldata sigs, address[] calldata signers) internal view {
        if (sigs.length < 3 || signers.length < 3) revert InsufficientCouncilSigners();
        for (uint256 i = 0; i < signers.length; i++) {
            if (!charters.isCouncilMember(signers[i])) revert NotCouncilMember(signers[i]);
        }
        // TODO: EIP-712 sig recovery in production
    }
}
