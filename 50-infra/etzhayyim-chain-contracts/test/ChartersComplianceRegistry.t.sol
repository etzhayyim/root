// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {ECDSA} from "../src/utils/ECDSA.sol";
import {EIP712} from "../src/utils/EIP712.sol";
import {ChartersComplianceRegistry, IAdherentRegistry} from "../src/ChartersComplianceRegistry.sol";

/// @dev Minimal mock for AdherentRegistry — the Registry only needs
/// isActive + ownerOfToken, neither of which charter-compliance reads
/// in the current implementation. Kept stub to satisfy the constructor.
contract MockAdherentRegistry is IAdherentRegistry {
    function isActive(uint256, uint64) external pure returns (bool) { return true; }
    function ownerOfToken(uint256) external pure returns (address) { return address(0); }
}

contract ChartersComplianceRegistryTest is Test {
    using ECDSA for bytes32;

    ChartersComplianceRegistry internal reg;
    MockAdherentRegistry internal adh;

    // Council private keys and their derived addresses
    uint256 constant COUNCIL_1_PK = 0x1111111111111111111111111111111111111111111111111111111111111111;
    uint256 constant COUNCIL_2_PK = 0x2222222222222222222222222222222222222222222222222222222222222222;
    uint256 constant COUNCIL_3_PK = 0x3333333333333333333333333333333333333333333333333333333333333333;
    uint256 constant COUNCIL_4_PK = 0x4444444444444444444444444444444444444444444444444444444444444444;
    uint256 constant COUNCIL_5_PK = 0x5555555555555555555555555555555555555555555555555555555555555555;
    uint256 constant OUTSIDER_PK = 0x6666666666666666666666666666666666666666666666666666666666666666;

    address COUNCIL_1;
    address COUNCIL_2;
    address COUNCIL_3;
    address COUNCIL_4;
    address COUNCIL_5;
    address OUTSIDER;
    address SUBJECT = address(0xACE);

    bytes32 REASON_2G;
    bytes32 EVIDENCE_CID;

    function setUp() public {
        COUNCIL_1 = vm.addr(COUNCIL_1_PK);
        COUNCIL_2 = vm.addr(COUNCIL_2_PK);
        COUNCIL_3 = vm.addr(COUNCIL_3_PK);
        COUNCIL_4 = vm.addr(COUNCIL_4_PK);
        COUNCIL_5 = vm.addr(COUNCIL_5_PK);
        OUTSIDER = vm.addr(OUTSIDER_PK);

        REASON_2G = keccak256("rider.section_2g");
        EVIDENCE_CID = bytes32("ipfs://QmEvidence...");

        adh = new MockAdherentRegistry();
        address[] memory bootstrap = new address[](5);
        bootstrap[0] = COUNCIL_1;
        bootstrap[1] = COUNCIL_2;
        bootstrap[2] = COUNCIL_3;
        bootstrap[3] = COUNCIL_4;
        bootstrap[4] = COUNCIL_5;
        reg = new ChartersComplianceRegistry(adh, bootstrap);
    }

    function _signUsingContractDigest(bytes32 digest, uint256 pk) internal view returns (bytes memory) {
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, digest);
        return abi.encodePacked(r, s, v);
    }

    function _councilSigsAttestAddress(
        address subject,
        bytes32 reasonHash,
        bytes32 evidenceCid
    ) internal view returns (bytes[] memory sigs, address[] memory signers) {
        signers = new address[](3);
        signers[0] = COUNCIL_1; signers[1] = COUNCIL_2; signers[2] = COUNCIL_3;
        sigs = new bytes[](3);
        bytes32 digest = reg.computeAttestNonAlignedAddressDigest(subject, reasonHash, evidenceCid);
        sigs[0] = _signUsingContractDigest(digest, COUNCIL_1_PK);
        sigs[1] = _signUsingContractDigest(digest, COUNCIL_2_PK);
        sigs[2] = _signUsingContractDigest(digest, COUNCIL_3_PK);
    }

    function _councilSigsAttestTokenId(
        uint256 tokenId,
        bytes32 reasonHash,
        bytes32 evidenceCid
    ) internal view returns (bytes[] memory sigs, address[] memory signers) {
        signers = new address[](3);
        signers[0] = COUNCIL_1; signers[1] = COUNCIL_2; signers[2] = COUNCIL_3;
        sigs = new bytes[](3);
        bytes32 digest = reg.computeAttestNonAlignedTokenIdDigest(tokenId, reasonHash, evidenceCid);
        sigs[0] = _signUsingContractDigest(digest, COUNCIL_1_PK);
        sigs[1] = _signUsingContractDigest(digest, COUNCIL_2_PK);
        sigs[2] = _signUsingContractDigest(digest, COUNCIL_3_PK);
    }

    function _councilSigsAcceptAppeal(
        bytes32 subjectHash,
        bool isAddress,
        address subject,
        uint256 tokenId,
        bytes32 counterEvidenceCid
    ) internal view returns (bytes[] memory sigs, address[] memory signers) {
        signers = new address[](3);
        signers[0] = COUNCIL_1; signers[1] = COUNCIL_2; signers[2] = COUNCIL_3;
        sigs = new bytes[](3);
        bytes32 digest = reg.computeAcceptAppealDigest(subjectHash, isAddress, subject, tokenId, counterEvidenceCid);
        sigs[0] = _signUsingContractDigest(digest, COUNCIL_1_PK);
        sigs[1] = _signUsingContractDigest(digest, COUNCIL_2_PK);
        sigs[2] = _signUsingContractDigest(digest, COUNCIL_3_PK);
    }

    function _councilSigsRehabilitate(
        bool isAddress,
        address subject,
        uint256 tokenId,
        bytes32 teshuvahCid
    ) internal view returns (bytes[] memory sigs, address[] memory signers) {
        signers = new address[](3);
        signers[0] = COUNCIL_1; signers[1] = COUNCIL_2; signers[2] = COUNCIL_3;
        sigs = new bytes[](3);
        bytes32 digest = reg.computeRehabilitateDigest(isAddress, subject, tokenId, teshuvahCid);
        sigs[0] = _signUsingContractDigest(digest, COUNCIL_1_PK);
        sigs[1] = _signUsingContractDigest(digest, COUNCIL_2_PK);
        sigs[2] = _signUsingContractDigest(digest, COUNCIL_3_PK);
    }

    // ─── Bootstrap Council ─────────────────────────────────────────

    function test_bootstrap_council_set() public view {
        assertTrue(reg.isCouncilMember(COUNCIL_1));
        assertTrue(reg.isCouncilMember(COUNCIL_5));
        assertFalse(reg.isCouncilMember(OUTSIDER));
        assertEq(reg.councilMemberCount(), 5);
    }

    function test_bootstrap_size_mismatch_reverts() public {
        address[] memory shortList = new address[](3);
        shortList[0] = COUNCIL_1;
        shortList[1] = COUNCIL_2;
        shortList[2] = COUNCIL_3;
        vm.expectRevert(ChartersComplianceRegistry.BootstrapSizeMismatch.selector);
        new ChartersComplianceRegistry(adh, shortList);
    }

    function test_bootstrap_duplicate_reverts() public {
        address[] memory dup = new address[](5);
        dup[0] = COUNCIL_1;
        dup[1] = COUNCIL_2;
        dup[2] = COUNCIL_3;
        dup[3] = COUNCIL_1;
        dup[4] = COUNCIL_5;
        vm.expectRevert(ChartersComplianceRegistry.DuplicateBootstrapMember.selector);
        new ChartersComplianceRegistry(adh, dup);
    }

    // ─── Attestation flow ──────────────────────────────────────────

    function test_attestNonAlignedAddress_sets_UnderReview() public {
        (bytes[] memory sigs, address[] memory signers) = _councilSigsAttestAddress(SUBJECT, REASON_2G, EVIDENCE_CID);
        reg.attestNonAlignedAddress(SUBJECT, REASON_2G, EVIDENCE_CID, sigs, signers);

        (
            ChartersComplianceRegistry.Status status,
            bytes32 reasonHash,
            bytes32 evidenceCid,
            uint64 effectiveAt,
            uint64 appealDeadline,
            bool finalized
        ) = reg.attestationsByAddress(SUBJECT);

        assertEq(uint8(status), uint8(ChartersComplianceRegistry.Status.UnderReview));
        assertEq(reasonHash, REASON_2G);
        assertEq(evidenceCid, EVIDENCE_CID);
        assertGt(effectiveAt, 0);
        assertEq(appealDeadline, effectiveAt + 30 days);
        assertFalse(finalized);
        // Not non-aligned during appeal window
        assertFalse(reg.isNonAlignedAddress(SUBJECT));
    }

    function test_attest_insufficient_signers_reverts() public {
        address[] memory signers = new address[](2);
        signers[0] = COUNCIL_1;
        signers[1] = COUNCIL_2;
        bytes[] memory sigs = new bytes[](2);
        sigs[0] = bytes("s1");
        sigs[1] = bytes("s2");
        vm.expectRevert(
            abi.encodeWithSelector(ChartersComplianceRegistry.InsufficientSigners.selector, 2, 3)
        );
        reg.attestNonAlignedAddress(SUBJECT, REASON_2G, EVIDENCE_CID, sigs, signers);
    }

    function test_attest_outsider_in_signers_reverts() public {
        address[] memory signers = new address[](3);
        signers[0] = COUNCIL_1;
        signers[1] = COUNCIL_2;
        signers[2] = OUTSIDER;  // not council
        bytes[] memory sigs = new bytes[](3);
        bytes32 digest = reg.computeAttestNonAlignedAddressDigest(SUBJECT, REASON_2G, EVIDENCE_CID);
        sigs[0] = _signUsingContractDigest(digest, COUNCIL_1_PK);
        sigs[1] = _signUsingContractDigest(digest, COUNCIL_2_PK);
        sigs[2] = _signUsingContractDigest(digest, OUTSIDER_PK);
        vm.expectRevert(
            abi.encodeWithSelector(ChartersComplianceRegistry.NotCouncil.selector, OUTSIDER)
        );
        reg.attestNonAlignedAddress(SUBJECT, REASON_2G, EVIDENCE_CID, sigs, signers);
    }

    function test_finalize_after_appeal_window() public {
        (bytes[] memory sigs, address[] memory signers) = _councilSigsAttestAddress(SUBJECT, REASON_2G, EVIDENCE_CID);
        reg.attestNonAlignedAddress(SUBJECT, REASON_2G, EVIDENCE_CID, sigs, signers);

        // Still under review
        assertFalse(reg.isNonAlignedAddress(SUBJECT));

        // Cannot finalize before window
        vm.expectRevert(ChartersComplianceRegistry.AppealWindowOpen.selector);
        reg.finalize(true, SUBJECT, 0);

        // Pass appeal window
        skip(30 days + 1);
        reg.finalize(true, SUBJECT, 0);

        // Now non-aligned (L1+L2+L3 enforcement active)
        assertTrue(reg.isNonAlignedAddress(SUBJECT));

        // Cannot finalize twice
        vm.expectRevert(ChartersComplianceRegistry.AlreadyFinalized.selector);
        reg.finalize(true, SUBJECT, 0);
    }

    function test_acceptAppeal_clears_status() public {
        (bytes[] memory sigs, address[] memory signers) = _councilSigsAttestAddress(SUBJECT, REASON_2G, EVIDENCE_CID);
        reg.attestNonAlignedAddress(SUBJECT, REASON_2G, EVIDENCE_CID, sigs, signers);

        bytes32 newEvidence = bytes32("ipfs://QmCounterEvidence...");
        bytes32 subjectHash = keccak256(abi.encode(SUBJECT, true));
        (bytes[] memory appealSigs, address[] memory appealSigners) = _councilSigsAcceptAppeal(subjectHash, true, SUBJECT, 0, newEvidence);
        reg.acceptAppeal(subjectHash, true, SUBJECT, 0, newEvidence, appealSigs, appealSigners);

        // Status = Aligned, no longer triggers enforcement
        assertFalse(reg.isNonAlignedAddress(SUBJECT));
    }

    function test_rehabilitate_path() public {
        (bytes[] memory sigs, address[] memory signers) = _councilSigsAttestAddress(SUBJECT, REASON_2G, EVIDENCE_CID);
        reg.attestNonAlignedAddress(SUBJECT, REASON_2G, EVIDENCE_CID, sigs, signers);

        skip(30 days + 1);
        reg.finalize(true, SUBJECT, 0);
        assertTrue(reg.isNonAlignedAddress(SUBJECT));

        // Subject submits teshuvah + 3 council sign
        bytes32 teshuvahCid = bytes32("ipfs://QmTeshuvah...");
        (bytes[] memory rehabSigs, address[] memory rehabSigners) = _councilSigsRehabilitate(true, SUBJECT, 0, teshuvahCid);
        reg.rehabilitate(true, SUBJECT, 0, teshuvahCid, rehabSigs, rehabSigners);

        // Enforcement gates lifted, but status remains Rehabilitated (permanent record)
        assertFalse(reg.isNonAlignedAddress(SUBJECT));
    }

    // ─── Token ID variant ──────────────────────────────────────────

    function test_attestNonAlignedTokenId() public {
        (bytes[] memory sigs, address[] memory signers) = _councilSigsAttestTokenId(42, REASON_2G, EVIDENCE_CID);
        reg.attestNonAlignedTokenId(42, REASON_2G, EVIDENCE_CID, sigs, signers);

        assertFalse(reg.isNonAlignedTokenId(42));  // appeal window open
        skip(30 days + 1);
        reg.finalize(false, address(0), 42);
        assertTrue(reg.isNonAlignedTokenId(42));
    }

    // ─── Governance binding ────────────────────────────────────────

    function test_bindGovernance_oneShot() public {
        assertEq(reg.governance(), address(0));
        reg.bindGovernance(address(0x60110));
        assertEq(reg.governance(), address(0x60110));
        vm.expectRevert(ChartersComplianceRegistry.GovernanceAlreadyBound.selector);
        reg.bindGovernance(address(0xABCDEF));
    }

    function test_setCouncilMember_only_governance() public {
        reg.bindGovernance(address(0x60110));

        // Non-governance cannot set
        vm.expectRevert(ChartersComplianceRegistry.NotGovernance.selector);
        reg.setCouncilMember(OUTSIDER, true);

        // Governance can add a 6th member
        vm.prank(address(0x60110));
        reg.setCouncilMember(OUTSIDER, true);
        assertTrue(reg.isCouncilMember(OUTSIDER));
        assertEq(reg.councilMemberCount(), 6);

        // And remove one
        vm.prank(address(0x60110));
        reg.setCouncilMember(COUNCIL_5, false);
        assertFalse(reg.isCouncilMember(COUNCIL_5));
        assertEq(reg.councilMemberCount(), 5);
    }
}