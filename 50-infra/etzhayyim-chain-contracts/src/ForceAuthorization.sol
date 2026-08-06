// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2605192315 (Transparent Religious Force) +
// ADR-2605192100 §1.12.B.
// Authorizes religious-corp force operations via 1 SBT = 1 vote with
// HIGHER hurdle than normal governance: 50% quorum + 67% supermajority.
// Normal voting 72h; emergency 24h (requires Council Lv6+ ≥3 emergency
// attestation submitted alongside the proposal).
//
// SEC-2026-002 FIX: EIP-712 signature verification for Council attestations
// (ADR-2605192315 §1.12.B constitutional invariant)

pragma solidity 0.8.27;

import {ECDSA} from "./utils/ECDSA.sol";
import {EIP712} from "./utils/EIP712.sol";

interface IAdherentRegistry {
    function isActive(uint256 tokenId, uint64 windowSecs) external view returns (bool);
    function tokenOf(address) external view returns (uint256);
    function totalMinted() external view returns (uint256);
}

interface IChartersComplianceRegistry {
    function isCouncilMember(address) external view returns (bool);
    function isNonAlignedTokenId(uint256 tokenId) external view returns (bool);
}

contract ForceAuthorization {
    using ECDSA for bytes32;
    using EIP712 for bytes32;

    enum AuthState {
        Proposed, Active, Defeated, Approved, Executed, AfterActionReviewed, Cancelled
    }
    enum Choice { Abstain, For, Against }

    struct Authorization {
        address proposer;
        bytes32 proposalCid;
        bytes32 intendedUseHash;
        bool emergency;
        uint64 proposedAt;
        uint64 votingDeadline;
        AuthState state;
        uint256 forVotes;
        uint256 againstVotes;
        uint256 abstainVotes;
        bytes32 logCid;             // populated after execution
        bytes32 afterActionCid;     // populated after Council ≥3 review
    }

    mapping(bytes32 => Authorization) public authorizations;
    mapping(bytes32 => mapping(uint256 => bool)) public hasVoted;

    IAdherentRegistry public immutable adherent;
    IChartersComplianceRegistry public immutable charters;

    // ─── Constitutional hurdles (higher than normal governance) ────
    uint256 public constant QUORUM_BPS = 5_000;          // 50% of totalMinted
    uint256 public constant SUPERMAJORITY_BPS = 6_700;   // 67% of (for + against)
    uint64 public constant VOTING_PERIOD_NORMAL = 72 hours;
    uint64 public constant VOTING_PERIOD_EMERGENCY = 24 hours;
    uint64 public constant ACTIVE_WINDOW = 30 days;
    uint256 public constant BPS_DENOMINATOR = 10_000;

    uint256 public proposalCounter;

    // ─── EIP-712 Domain & Types ───────────────────────────────────────

    /// @notice Domain separator cached at construction (chainId + address immutable).
    bytes32 private immutable _domainSeparator;

    // EIP-712 type hashes (keccak256 of the type definition)
    bytes32 private constant EMERGENCY_PROPOSE_TYPEHASH =
        keccak256("EmergencyPropose(address proposer,bytes32 proposalCid,bytes32 intendedUseHash,uint256 nonce)");
    bytes32 private constant RECORD_AFTER_ACTION_TYPEHASH =
        keccak256("RecordAfterAction(bytes32 authId,bytes32 afterActionCid)");
    bytes32 private constant CANCEL_TYPEHASH =
        keccak256("Cancel(bytes32 authId,bytes32 reasonCid)");

    event ProposalSubmitted(
        bytes32 indexed authId,
        address indexed proposer,
        bytes32 indexed intendedUseHash,
        bool emergency,
        uint64 votingDeadline
    );
    event Voted(bytes32 indexed authId, uint256 indexed sbtTokenId, Choice choice);
    event ProposalDecided(bytes32 indexed authId, AuthState state);
    event ExecutionRecorded(bytes32 indexed authId, bytes32 logCid);
    event AfterActionReviewed(bytes32 indexed authId, bytes32 afterActionCid);
    event Cancelled(bytes32 indexed authId, bytes32 reasonCid);

    error ZeroProposalCid();
    error ProposerNonAligned();
    error InvalidStateForOperation(AuthState got, AuthState need);
    error VotingNotOver();
    error AlreadyVoted(uint256 sbtTokenId);
    error VoterNotActive(uint256 sbtTokenId);
    error VoterNonAligned(uint256 sbtTokenId);
    error NotVoterOwner();
    error InvalidChoice();
    error EmergencyRequiresCouncilAttestation();
    error InsufficientCouncilSigners();
    error NotCouncilMember(address signer);
    error InvalidSignature();
    error InvalidNonce();

    constructor(IAdherentRegistry _adherent, IChartersComplianceRegistry _charters) {
        adherent = _adherent;
        charters = _charters;
        // Domain separator: name="ForceAuthorization", version="1"
        _domainSeparator = EIP712._buildDomainSeparator("ForceAuthorization", "1");
    }

    /// @notice Get the EIP-712 domain separator for this contract.
    ///         Used by off-chain signers and tests to compute correct digests.
    function domainSeparator() external view returns (bytes32) {
        return _domainSeparator;
    }

    /// @notice Compute the EIP-712 digest for emergency propose (for testing/debugging).
    function computeEmergencyProposeDigest(
        address proposer,
        bytes32 proposalCid,
        bytes32 intendedUseHash,
        uint256 nonce
    ) external view returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(
            EMERGENCY_PROPOSE_TYPEHASH,
            proposer,
            proposalCid,
            intendedUseHash,
            nonce
        ));
        return EIP712._hashTypedDataV4(_domainSeparator, structHash);
    }

    /// @notice Compute the EIP-712 digest for after-action review (for testing/debugging).
    function computeAfterActionDigest(
        bytes32 authId,
        bytes32 afterActionCid
    ) external view returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(
            RECORD_AFTER_ACTION_TYPEHASH,
            authId,
            afterActionCid
        ));
        return EIP712._hashTypedDataV4(_domainSeparator, structHash);
    }

    /// @notice Compute the EIP-712 digest for cancellation (for testing/debugging).
    function computeCancelDigest(
        bytes32 authId,
        bytes32 reasonCid
    ) external view returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(
            CANCEL_TYPEHASH,
            authId,
            reasonCid
        ));
        return EIP712._hashTypedDataV4(_domainSeparator, structHash);
    }

    /// @notice Submit a force-authorization proposal. Normal 72h voting;
    ///         emergency 24h requires Council Lv6+ ≥3 attestation passed
    ///         alongside.
    /// @param emergencyNonce A unique nonce for emergency proposals to prevent
    ///                       signature replay. Must be unique per (proposer, proposalCid).
    function propose(
        bytes32 proposalCid,
        bytes32 intendedUseHash,
        bool emergency,
        bytes[] calldata emergencyCouncilSigs,
        address[] calldata emergencyCouncilSigners,
        uint256 emergencyNonce
    ) external returns (bytes32 authId) {
        if (proposalCid == bytes32(0)) revert ZeroProposalCid();
        uint256 proposerSbt = adherent.tokenOf(msg.sender);
        if (proposerSbt != 0 && charters.isNonAlignedTokenId(proposerSbt)) revert ProposerNonAligned();

        if (emergency) {
            if (emergencyCouncilSigs.length < 3) revert EmergencyRequiresCouncilAttestation();
            // Verify EIP-712 signatures for emergency propose
            _verifyEmergencyProposeSignatures(
                msg.sender,
                proposalCid,
                intendedUseHash,
                emergencyNonce,
                emergencyCouncilSigs,
                emergencyCouncilSigners
            );
        }

        authId = keccak256(abi.encode(msg.sender, proposalCid, ++proposalCounter, block.timestamp));
        Authorization storage a = authorizations[authId];
        a.proposer = msg.sender;
        a.proposalCid = proposalCid;
        a.intendedUseHash = intendedUseHash;
        a.emergency = emergency;
        a.proposedAt = uint64(block.timestamp);
        a.votingDeadline = uint64(block.timestamp) +
            (emergency ? VOTING_PERIOD_EMERGENCY : VOTING_PERIOD_NORMAL);
        a.state = AuthState.Active;

        emit ProposalSubmitted(authId, msg.sender, intendedUseHash, emergency, a.votingDeadline);
    }

    function vote(bytes32 authId, Choice choice) external {
        Authorization storage a = authorizations[authId];
        if (a.state != AuthState.Active) revert InvalidStateForOperation(a.state, AuthState.Active);
        if (block.timestamp > a.votingDeadline) revert VotingNotOver();

        uint256 sbtTokenId = adherent.tokenOf(msg.sender);
        if (sbtTokenId == 0) revert NotVoterOwner();
        if (!adherent.isActive(sbtTokenId, ACTIVE_WINDOW)) revert VoterNotActive(sbtTokenId);
        if (charters.isNonAlignedTokenId(sbtTokenId)) revert VoterNonAligned(sbtTokenId);
        if (hasVoted[authId][sbtTokenId]) revert AlreadyVoted(sbtTokenId);

        hasVoted[authId][sbtTokenId] = true;
        if (choice == Choice.For) a.forVotes++;
        else if (choice == Choice.Against) a.againstVotes++;
        else if (choice == Choice.Abstain) a.abstainVotes++;
        else revert InvalidChoice();

        emit Voted(authId, sbtTokenId, choice);
    }

    /// @notice Resolve a proposal after voting deadline. Anyone may call.
    function resolve(bytes32 authId) external {
        Authorization storage a = authorizations[authId];
        if (a.state != AuthState.Active) revert InvalidStateForOperation(a.state, AuthState.Active);
        if (block.timestamp <= a.votingDeadline) revert VotingNotOver();

        uint256 total = a.forVotes + a.againstVotes + a.abstainVotes;
        uint256 quorum = (adherent.totalMinted() * QUORUM_BPS) / BPS_DENOMINATOR;
        if (total < quorum) {
            a.state = AuthState.Defeated;
            emit ProposalDecided(authId, AuthState.Defeated);
            return;
        }
        uint256 forAgainst = a.forVotes + a.againstVotes;
        if (forAgainst == 0 || (a.forVotes * BPS_DENOMINATOR) / forAgainst < SUPERMAJORITY_BPS) {
            a.state = AuthState.Defeated;
            emit ProposalDecided(authId, AuthState.Defeated);
        } else {
            a.state = AuthState.Approved;
            emit ProposalDecided(authId, AuthState.Approved);
        }
    }

    /// @notice Operating Adherents log the actual force action after
    ///         executing an Approved authorization.
    function recordExecution(bytes32 authId, bytes32 logCid) external {
        Authorization storage a = authorizations[authId];
        if (a.state != AuthState.Approved) revert InvalidStateForOperation(a.state, AuthState.Approved);
        a.state = AuthState.Executed;
        a.logCid = logCid;
        emit ExecutionRecorded(authId, logCid);
    }

    /// @notice Council Lv6+ ≥3 sign off on the after-action review.
    function recordAfterAction(
        bytes32 authId,
        bytes32 afterActionCid,
        bytes[] calldata councilSigs,
        address[] calldata councilSigners
    ) external {
        Authorization storage a = authorizations[authId];
        if (a.state != AuthState.Executed) revert InvalidStateForOperation(a.state, AuthState.Executed);
        _verifyAfterActionSignatures(authId, afterActionCid, councilSigs, councilSigners);
        a.state = AuthState.AfterActionReviewed;
        a.afterActionCid = afterActionCid;
        emit AfterActionReviewed(authId, afterActionCid);
    }

    /// @notice Council Lv6+ ≥3 cancel of a proposal prior to execution.
    function cancel(
        bytes32 authId,
        bytes32 reasonCid,
        bytes[] calldata councilSigs,
        address[] calldata councilSigners
    ) external {
        Authorization storage a = authorizations[authId];
        if (a.state == AuthState.Executed || a.state == AuthState.AfterActionReviewed || a.state == AuthState.Cancelled) {
            revert InvalidStateForOperation(a.state, AuthState.Active);
        }
        _verifyCancelSignatures(authId, reasonCid, councilSigs, councilSigners);
        a.state = AuthState.Cancelled;
        emit Cancelled(authId, reasonCid);
    }

    // ─── Internal: EIP-712 Signature Verification ─────────────────────

    /// @notice Verify EIP-712 signatures for emergency propose.
    ///         Signers sign: proposer, proposalCid, intendedUseHash, nonce
    function _verifyEmergencyProposeSignatures(
        address proposer,
        bytes32 proposalCid,
        bytes32 intendedUseHash,
        uint256 nonce,
        bytes[] calldata sigs,
        address[] calldata signers
    ) internal view {
        if (sigs.length < 3 || signers.length < 3) revert InsufficientCouncilSigners();
        if (sigs.length != signers.length) revert InsufficientCouncilSigners();

        // Hash the struct data
        bytes32 structHash = keccak256(abi.encode(
            EMERGENCY_PROPOSE_TYPEHASH,
            proposer,
            proposalCid,
            intendedUseHash,
            nonce
        ));

        // Final digest = keccak256("\x19\x01" || domainSeparator || structHash)
        bytes32 digest = EIP712._hashTypedDataV4(_domainSeparator, structHash);

        for (uint256 i = 0; i < signers.length; i++) {
            address signer = signers[i];
            if (!charters.isCouncilMember(signer)) revert NotCouncilMember(signer);
            // Recover and verify using tryRecover (returns address(0) on failure)
            address recovered = ECDSA.tryRecover(digest, sigs[i]);
            if (recovered == address(0) || recovered != signer) revert InvalidSignature();
        }
    }

    /// @notice Verify EIP-712 signatures for after-action review.
    ///         Signers sign: authId, afterActionCid
    function _verifyAfterActionSignatures(
        bytes32 authId,
        bytes32 afterActionCid,
        bytes[] calldata sigs,
        address[] calldata signers
    ) internal view {
        if (sigs.length < 3 || signers.length < 3) revert InsufficientCouncilSigners();
        if (sigs.length != signers.length) revert InsufficientCouncilSigners();

        bytes32 structHash = keccak256(abi.encode(
            RECORD_AFTER_ACTION_TYPEHASH,
            authId,
            afterActionCid
        ));

        bytes32 digest = EIP712._hashTypedDataV4(_domainSeparator, structHash);

        for (uint256 i = 0; i < signers.length; i++) {
            address signer = signers[i];
            if (!charters.isCouncilMember(signer)) revert NotCouncilMember(signer);
            address recovered = ECDSA.tryRecover(digest, sigs[i]);
            if (recovered == address(0) || recovered != signer) revert InvalidSignature();
        }
    }

    /// @notice Verify EIP-712 signatures for cancellation.
    ///         Signers sign: authId, reasonCid
    function _verifyCancelSignatures(
        bytes32 authId,
        bytes32 reasonCid,
        bytes[] calldata sigs,
        address[] calldata signers
    ) internal view {
        if (sigs.length < 3 || signers.length < 3) revert InsufficientCouncilSigners();
        if (sigs.length != signers.length) revert InsufficientCouncilSigners();

        bytes32 structHash = keccak256(abi.encode(
            CANCEL_TYPEHASH,
            authId,
            reasonCid
        ));

        bytes32 digest = EIP712._hashTypedDataV4(_domainSeparator, structHash);

        for (uint256 i = 0; i < signers.length; i++) {
            address signer = signers[i];
            if (!charters.isCouncilMember(signer)) revert NotCouncilMember(signer);
            address recovered = ECDSA.tryRecover(digest, sigs[i]);
            if (recovered == address(0) || recovered != signer) revert InvalidSignature();
        }
    }
}