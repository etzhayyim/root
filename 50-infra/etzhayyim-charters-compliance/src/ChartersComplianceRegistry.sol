// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2605192230 (Three-Tier Enforcement Implementation).
// Single source of truth for Council Lv6+ attestations under Charter Rider §2.

pragma solidity ^0.8.24;

interface IAdherentRegistry {
    function isActive(uint256 tokenId, uint64 windowSec) external view returns (bool);
    function ownerOf(uint256 tokenId) external view returns (address);
}

interface ICouncil {
    /// @notice Returns true if signer is a Council Lv6+ member (per ADR-2605192300)
    function isCouncil(address signer) external view returns (bool);
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

    ICouncil public immutable council;
    IAdherentRegistry public immutable adherentRegistry;

    uint64 public constant APPEAL_WINDOW = 30 days;
    uint8 public constant MIN_COUNCIL_SIGNERS = 3;

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

    error NotCouncil(address signer);
    error InsufficientSigners(uint8 got, uint8 need);
    error AlreadyFinalized();
    error AppealWindowOpen();
    error InvalidSignature();

    constructor(ICouncil _council, IAdherentRegistry _adherentRegistry) {
        council = _council;
        adherentRegistry = _adherentRegistry;
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

    /// @notice Accept appeal (Council determines counter-evidence is sufficient)
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
            if (!council.isCouncil(signers[i])) revert NotCouncil(signers[i]);
        }
        // TODO: cryptographic verification of sigs against a canonical message digest
        //       (current scaffold trusts caller; production deploy adds EIP-712 sig recovery)
    }
}
