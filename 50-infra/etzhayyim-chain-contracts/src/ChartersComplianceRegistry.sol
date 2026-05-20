// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2605192230 (Three-Tier Enforcement Implementation).
// Single source of truth for Council Lv6+ attestations under Charter Rider §2.
//
// Council membership is bootstrapped per ADR-2605192300 (5 founder-proposed
// + 30-day public objection seats). Phase 2 expansion to formal 1 SBT = 1
// vote election is handled via Governance proposal that calls
// `setCouncilMember(addr, true/false)`.

pragma solidity 0.8.27;

interface IAdherentRegistry {
    function isActive(uint256 tokenId, uint64 windowSecs) external view returns (bool);
    function ownerOfToken(uint256 tokenId) external view returns (address);
}

contract ChartersComplianceRegistry {
    enum Status { Aligned, NonAligned, UnderReview, Rehabilitated }

    struct Attestation {
        Status status;
        bytes32 reasonHash;       // keccak256 of canonical reason (e.g., "rider.section_2g")
        bytes32 evidenceCid;      // IPFS CID of evidence bundle
        uint64 effectiveAt;
        uint64 appealDeadline;
        address[] councilSigners;
        bool finalized;
    }

    mapping(address => Attestation) public attestationsByAddress;
    mapping(uint256 => Attestation) public attestationsByTokenId;

    /// @notice Council Lv6+ membership. Bootstrapped from constructor list
    ///         (5 seats per ADR-2605192300). Mutable only via {governance}
    ///         after Phase 2 formal-council transition.
    mapping(address => bool) public isCouncilMember;
    uint256 public councilMemberCount;

    IAdherentRegistry public immutable adherentRegistry;

    /// @notice Governance contract authorized to call {setCouncilMember}.
    ///         Bound once via {bindGovernance}. Until bound, only the
    ///         constructor-seeded bootstrap set is recognised.
    address public governance;

    uint64 public constant APPEAL_WINDOW = 30 days;
    uint8 public constant MIN_COUNCIL_SIGNERS = 3;
    uint8 public constant BOOTSTRAP_COUNCIL_SIZE = 5;

    event AttestationCreated(
        bytes32 indexed subjectHash,
        bool isAddress,
        address subjectAddress,
        uint256 subjectTokenId,
        Status status,
        bytes32 reasonHash,
        bytes32 evidenceCid,
        uint64 effectiveAt,
        address[] councilSigners
    );

    event AppealAccepted(bytes32 indexed subjectHash, bytes32 newEvidenceCid);
    event Rehabilitated(bytes32 indexed subjectHash, uint64 effectiveAt);
    event Finalized(bytes32 indexed subjectHash);
    event GovernanceBound(address indexed governance);
    event CouncilMemberSet(address indexed member, bool isMember);

    error NotCouncil(address signer);
    error InsufficientSigners(uint8 got, uint8 need);
    error AlreadyFinalized();
    error AppealWindowOpen();
    error NotGovernance();
    error GovernanceAlreadyBound();
    error BootstrapSizeMismatch();
    error DuplicateBootstrapMember();

    constructor(IAdherentRegistry _adherentRegistry, address[] memory _bootstrapCouncil) {
        adherentRegistry = _adherentRegistry;
        if (_bootstrapCouncil.length != BOOTSTRAP_COUNCIL_SIZE) revert BootstrapSizeMismatch();
        for (uint256 i = 0; i < BOOTSTRAP_COUNCIL_SIZE; i++) {
            address m = _bootstrapCouncil[i];
            if (isCouncilMember[m]) revert DuplicateBootstrapMember();
            isCouncilMember[m] = true;
            emit CouncilMemberSet(m, true);
        }
        councilMemberCount = BOOTSTRAP_COUNCIL_SIZE;
    }

    function bindGovernance(address governance_) external {
        if (governance != address(0)) revert GovernanceAlreadyBound();
        governance = governance_;
        emit GovernanceBound(governance_);
    }

    /// @notice Phase 2 Council membership mutation. Governance-gated.
    function setCouncilMember(address member, bool isMember) external {
        if (msg.sender != governance) revert NotGovernance();
        bool was = isCouncilMember[member];
        if (was == isMember) return;
        isCouncilMember[member] = isMember;
        if (isMember) {
            councilMemberCount++;
        } else {
            councilMemberCount--;
        }
        emit CouncilMemberSet(member, isMember);
    }

    function attestNonAlignedAddress(
        address subject,
        bytes32 reasonHash,
        bytes32 evidenceCid,
        bytes[] calldata councilSigs,
        address[] calldata councilSigners
    ) external {
        _verifyCouncilQuorum(councilSigs, councilSigners);

        Attestation storage a = attestationsByAddress[subject];
        a.status = Status.UnderReview;
        a.reasonHash = reasonHash;
        a.evidenceCid = evidenceCid;
        a.effectiveAt = uint64(block.timestamp);
        a.appealDeadline = uint64(block.timestamp + APPEAL_WINDOW);
        a.councilSigners = councilSigners;
        a.finalized = false;

        bytes32 h = keccak256(abi.encode(subject, true));
        emit AttestationCreated(
            h, true, subject, 0,
            Status.UnderReview, reasonHash, evidenceCid, a.effectiveAt, councilSigners
        );
    }

    function attestNonAlignedTokenId(
        uint256 tokenId,
        bytes32 reasonHash,
        bytes32 evidenceCid,
        bytes[] calldata councilSigs,
        address[] calldata councilSigners
    ) external {
        _verifyCouncilQuorum(councilSigs, councilSigners);

        Attestation storage a = attestationsByTokenId[tokenId];
        a.status = Status.UnderReview;
        a.reasonHash = reasonHash;
        a.evidenceCid = evidenceCid;
        a.effectiveAt = uint64(block.timestamp);
        a.appealDeadline = uint64(block.timestamp + APPEAL_WINDOW);
        a.councilSigners = councilSigners;
        a.finalized = false;

        bytes32 h = keccak256(abi.encode(tokenId, false));
        emit AttestationCreated(
            h, false, address(0), tokenId,
            Status.UnderReview, reasonHash, evidenceCid, a.effectiveAt, councilSigners
        );
    }

    function acceptAppeal(
        bytes32 subjectHash,
        bool isAddress,
        address subject,
        uint256 tokenId,
        bytes32 counterEvidenceCid,
        bytes[] calldata councilSigs,
        address[] calldata councilSigners
    ) external {
        _verifyCouncilQuorum(councilSigs, councilSigners);
        Attestation storage a = isAddress ? attestationsByAddress[subject] : attestationsByTokenId[tokenId];
        if (a.finalized) revert AlreadyFinalized();
        a.status = Status.Aligned;
        a.evidenceCid = counterEvidenceCid;
        emit AppealAccepted(subjectHash, counterEvidenceCid);
    }

    function rehabilitate(
        bool isAddress,
        address subject,
        uint256 tokenId,
        bytes32 teshuvahCid,
        bytes[] calldata councilSigs,
        address[] calldata councilSigners
    ) external {
        _verifyCouncilQuorum(councilSigs, councilSigners);
        Attestation storage a = isAddress ? attestationsByAddress[subject] : attestationsByTokenId[tokenId];
        a.status = Status.Rehabilitated;
        a.evidenceCid = teshuvahCid;
        a.effectiveAt = uint64(block.timestamp);
        a.finalized = true;
        bytes32 h = keccak256(abi.encode(isAddress ? uint256(uint160(subject)) : tokenId, isAddress));
        emit Rehabilitated(h, a.effectiveAt);
    }

    function finalize(bool isAddress, address subject, uint256 tokenId) external {
        Attestation storage a = isAddress ? attestationsByAddress[subject] : attestationsByTokenId[tokenId];
        if (block.timestamp < a.appealDeadline) revert AppealWindowOpen();
        if (a.finalized) revert AlreadyFinalized();
        if (a.status == Status.UnderReview) {
            a.status = Status.NonAligned;
        }
        a.finalized = true;
        bytes32 h = keccak256(abi.encode(isAddress ? uint256(uint160(subject)) : tokenId, isAddress));
        emit Finalized(h);
    }

    function isNonAlignedAddress(address subject) public view returns (bool) {
        Attestation storage a = attestationsByAddress[subject];
        return a.status == Status.NonAligned && a.finalized && block.timestamp >= a.effectiveAt;
    }

    function isNonAlignedTokenId(uint256 tokenId) public view returns (bool) {
        Attestation storage a = attestationsByTokenId[tokenId];
        return a.status == Status.NonAligned && a.finalized && block.timestamp >= a.effectiveAt;
    }

    function _verifyCouncilQuorum(bytes[] calldata sigs, address[] calldata signers) internal view {
        if (sigs.length < MIN_COUNCIL_SIGNERS || signers.length < MIN_COUNCIL_SIGNERS) {
            revert InsufficientSigners(uint8(sigs.length), MIN_COUNCIL_SIGNERS);
        }
        for (uint256 i = 0; i < signers.length; i++) {
            if (!isCouncilMember[signers[i]]) revert NotCouncil(signers[i]);
        }
        // TODO: EIP-712 sig recovery against canonical message digest in production.
        //       v0 scaffold trusts the multisig submission (Council members
        //       coordinate off-chain attestation Lexicons + the Pregel
        //       CouncilDeliberationCell collects ≥3 signed votes).
    }
}
