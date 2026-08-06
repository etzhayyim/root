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
//
// SEC-2026-002 FIX: EIP-712 signature verification for Council attestations
// (same vulnerability class as ForceAuthorization)

pragma solidity 0.8.27;

import {ECDSA} from "./utils/ECDSA.sol";
import {EIP712} from "./utils/EIP712.sol";

interface IAdherentRegistry {
    function isActive(uint256 tokenId, uint64 windowSecs) external view returns (bool);
    function ownerOfToken(uint256 tokenId) external view returns (address);
}

contract ChartersComplianceRegistry {
    using ECDSA for bytes32;
    using EIP712 for bytes32;

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

    // ─── EIP-712 Domain & Types ───────────────────────────────────────

    /// @notice Domain separator cached at construction (chainId + address immutable).
    bytes32 private immutable _domainSeparator;

    // EIP-712 type hashes
    bytes32 private constant ATTEST_NON_ALIGNED_ADDRESS_TYPEHASH =
        keccak256("AttestNonAlignedAddress(address subject,bytes32 reasonHash,bytes32 evidenceCid)");
    bytes32 private constant ATTEST_NON_ALIGNED_TOKEN_ID_TYPEHASH =
        keccak256("AttestNonAlignedTokenId(uint256 tokenId,bytes32 reasonHash,bytes32 evidenceCid)");
    bytes32 private constant ACCEPT_APPEAL_TYPEHASH =
        keccak256("AcceptAppeal(bytes32 subjectHash,bool isAddress,address subject,uint256 tokenId,bytes32 counterEvidenceCid)");
    bytes32 private constant REHABILITATE_TYPEHASH =
        keccak256("Rehabilitate(bool isAddress,address subject,uint256 tokenId,bytes32 teshuvahCid)");

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
    error InvalidSignature();

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

        // Domain separator: name="ChartersComplianceRegistry", version="1"
        _domainSeparator = EIP712._buildDomainSeparator("ChartersComplianceRegistry", "1");
    }

    /// @notice Get the EIP-712 domain separator for this contract.
    ///         Used by off-chain signers and tests to compute correct digests.
    function domainSeparator() external view returns (bytes32) {
        return _domainSeparator;
    }

    /// @notice Compute the EIP-712 digest for attestNonAlignedAddress (for testing/debugging).
    function computeAttestNonAlignedAddressDigest(
        address subject,
        bytes32 reasonHash,
        bytes32 evidenceCid
    ) external view returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(
            ATTEST_NON_ALIGNED_ADDRESS_TYPEHASH,
            subject,
            reasonHash,
            evidenceCid
        ));
        return EIP712._hashTypedDataV4(_domainSeparator, structHash);
    }

    /// @notice Compute the EIP-712 digest for attestNonAlignedTokenId (for testing/debugging).
    function computeAttestNonAlignedTokenIdDigest(
        uint256 tokenId,
        bytes32 reasonHash,
        bytes32 evidenceCid
    ) external view returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(
            ATTEST_NON_ALIGNED_TOKEN_ID_TYPEHASH,
            tokenId,
            reasonHash,
            evidenceCid
        ));
        return EIP712._hashTypedDataV4(_domainSeparator, structHash);
    }

    /// @notice Compute the EIP-712 digest for acceptAppeal (for testing/debugging).
    function computeAcceptAppealDigest(
        bytes32 subjectHash,
        bool isAddress,
        address subject,
        uint256 tokenId,
        bytes32 counterEvidenceCid
    ) external view returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(
            ACCEPT_APPEAL_TYPEHASH,
            subjectHash,
            isAddress,
            subject,
            tokenId,
            counterEvidenceCid
        ));
        return EIP712._hashTypedDataV4(_domainSeparator, structHash);
    }

    /// @notice Compute the EIP-712 digest for rehabilitate (for testing/debugging).
    function computeRehabilitateDigest(
        bool isAddress,
        address subject,
        uint256 tokenId,
        bytes32 teshuvahCid
    ) external view returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(
            REHABILITATE_TYPEHASH,
            isAddress,
            subject,
            tokenId,
            teshuvahCid
        ));
        return EIP712._hashTypedDataV4(_domainSeparator, structHash);
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
        _verifyAttestNonAlignedAddressSignatures(subject, reasonHash, evidenceCid, councilSigs, councilSigners);

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
        _verifyAttestNonAlignedTokenIdSignatures(tokenId, reasonHash, evidenceCid, councilSigs, councilSigners);

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
        _verifyAcceptAppealSignatures(subjectHash, isAddress, subject, tokenId, counterEvidenceCid, councilSigs, councilSigners);

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
        _verifyRehabilitateSignatures(isAddress, subject, tokenId, teshuvahCid, councilSigs, councilSigners);

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

    // ─── Internal: EIP-712 Signature Verification ─────────────────────

    function _verifyAttestNonAlignedAddressSignatures(
        address subject,
        bytes32 reasonHash,
        bytes32 evidenceCid,
        bytes[] calldata sigs,
        address[] calldata signers
    ) internal view {
        if (sigs.length < MIN_COUNCIL_SIGNERS || signers.length < MIN_COUNCIL_SIGNERS) {
            revert InsufficientSigners(uint8(sigs.length), MIN_COUNCIL_SIGNERS);
        }
        if (sigs.length != signers.length) revert InsufficientSigners(uint8(sigs.length), MIN_COUNCIL_SIGNERS);

        bytes32 structHash = keccak256(abi.encode(
            ATTEST_NON_ALIGNED_ADDRESS_TYPEHASH,
            subject,
            reasonHash,
            evidenceCid
        ));

        bytes32 digest = EIP712._hashTypedDataV4(_domainSeparator, structHash);

        for (uint256 i = 0; i < signers.length; i++) {
            address signer = signers[i];
            if (!isCouncilMember[signer]) revert NotCouncil(signer);
            address recovered = ECDSA.tryRecover(digest, sigs[i]);
            if (recovered == address(0) || recovered != signer) revert InvalidSignature();
        }
    }

    function _verifyAttestNonAlignedTokenIdSignatures(
        uint256 tokenId,
        bytes32 reasonHash,
        bytes32 evidenceCid,
        bytes[] calldata sigs,
        address[] calldata signers
    ) internal view {
        if (sigs.length < MIN_COUNCIL_SIGNERS || signers.length < MIN_COUNCIL_SIGNERS) {
            revert InsufficientSigners(uint8(sigs.length), MIN_COUNCIL_SIGNERS);
        }
        if (sigs.length != signers.length) revert InsufficientSigners(uint8(sigs.length), MIN_COUNCIL_SIGNERS);

        bytes32 structHash = keccak256(abi.encode(
            ATTEST_NON_ALIGNED_TOKEN_ID_TYPEHASH,
            tokenId,
            reasonHash,
            evidenceCid
        ));

        bytes32 digest = EIP712._hashTypedDataV4(_domainSeparator, structHash);

        for (uint256 i = 0; i < signers.length; i++) {
            address signer = signers[i];
            if (!isCouncilMember[signer]) revert NotCouncil(signer);
            address recovered = ECDSA.tryRecover(digest, sigs[i]);
            if (recovered == address(0) || recovered != signer) revert InvalidSignature();
        }
    }

    function _verifyAcceptAppealSignatures(
        bytes32 subjectHash,
        bool isAddress,
        address subject,
        uint256 tokenId,
        bytes32 counterEvidenceCid,
        bytes[] calldata sigs,
        address[] calldata signers
    ) internal view {
        if (sigs.length < MIN_COUNCIL_SIGNERS || signers.length < MIN_COUNCIL_SIGNERS) {
            revert InsufficientSigners(uint8(sigs.length), MIN_COUNCIL_SIGNERS);
        }
        if (sigs.length != signers.length) revert InsufficientSigners(uint8(sigs.length), MIN_COUNCIL_SIGNERS);

        bytes32 structHash = keccak256(abi.encode(
            ACCEPT_APPEAL_TYPEHASH,
            subjectHash,
            isAddress,
            subject,
            tokenId,
            counterEvidenceCid
        ));

        bytes32 digest = EIP712._hashTypedDataV4(_domainSeparator, structHash);

        for (uint256 i = 0; i < signers.length; i++) {
            address signer = signers[i];
            if (!isCouncilMember[signer]) revert NotCouncil(signer);
            address recovered = ECDSA.tryRecover(digest, sigs[i]);
            if (recovered == address(0) || recovered != signer) revert InvalidSignature();
        }
    }

    function _verifyRehabilitateSignatures(
        bool isAddress,
        address subject,
        uint256 tokenId,
        bytes32 teshuvahCid,
        bytes[] calldata sigs,
        address[] calldata signers
    ) internal view {
        if (sigs.length < MIN_COUNCIL_SIGNERS || signers.length < MIN_COUNCIL_SIGNERS) {
            revert InsufficientSigners(uint8(sigs.length), MIN_COUNCIL_SIGNERS);
        }
        if (sigs.length != signers.length) revert InsufficientSigners(uint8(sigs.length), MIN_COUNCIL_SIGNERS);

        bytes32 structHash = keccak256(abi.encode(
            REHABILITATE_TYPEHASH,
            isAddress,
            subject,
            tokenId,
            teshuvahCid
        ));

        bytes32 digest = EIP712._hashTypedDataV4(_domainSeparator, structHash);

        for (uint256 i = 0; i < signers.length; i++) {
            address signer = signers[i];
            if (!isCouncilMember[signer]) revert NotCouncil(signer);
            address recovered = ECDSA.tryRecover(digest, sigs[i]);
            if (recovered == address(0) || recovered != signer) revert InvalidSignature();
        }
    }
}