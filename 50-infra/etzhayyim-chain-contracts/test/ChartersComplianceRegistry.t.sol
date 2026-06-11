// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {ChartersComplianceRegistry, IAdherentRegistry} from "../src/ChartersComplianceRegistry.sol";

/// @dev Minimal mock for AdherentRegistry — the Registry only needs
/// isActive + ownerOfToken, neither of which charter-compliance reads
/// in the current implementation. Kept stub to satisfy the constructor.
contract MockAdherentRegistry is IAdherentRegistry {
    function isActive(uint256, uint64) external pure returns (bool) { return true; }
    function ownerOfToken(uint256) external pure returns (address) { return address(0); }
}

contract ChartersComplianceRegistryTest is Test {
    ChartersComplianceRegistry internal reg;
    MockAdherentRegistry internal adh;

    address internal constant COUNCIL_1 = address(0xC001);
    address internal constant COUNCIL_2 = address(0xC002);
    address internal constant COUNCIL_3 = address(0xC003);
    address internal constant COUNCIL_4 = address(0xC004);
    address internal constant COUNCIL_5 = address(0xC005);
    address internal constant OUTSIDER = address(0xBEEF);
    address internal constant SUBJECT = address(0xACE);

    bytes32 internal constant REASON_2G = keccak256("rider.section_2g");
    bytes32 internal constant EVIDENCE_CID = bytes32("ipfs://QmEvidence...");

    function setUp() public {
        adh = new MockAdherentRegistry();
        address[] memory bootstrap = new address[](5);
        bootstrap[0] = COUNCIL_1;
        bootstrap[1] = COUNCIL_2;
        bootstrap[2] = COUNCIL_3;
        bootstrap[3] = COUNCIL_4;
        bootstrap[4] = COUNCIL_5;
        reg = new ChartersComplianceRegistry(adh, bootstrap);
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

    function _signers3() internal pure returns (bytes[] memory sigs, address[] memory signers) {
        signers = new address[](3);
        signers[0] = COUNCIL_1;
        signers[1] = COUNCIL_2;
        signers[2] = COUNCIL_3;
        sigs = new bytes[](3);
        sigs[0] = abi.encodePacked("sig1");
        sigs[1] = abi.encodePacked("sig2");
        sigs[2] = abi.encodePacked("sig3");
    }

    function test_attestNonAlignedAddress_sets_UnderReview() public {
        (bytes[] memory sigs, address[] memory signers) = _signers3();
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
        sigs[0] = bytes("s1"); sigs[1] = bytes("s2"); sigs[2] = bytes("s3");
        vm.expectRevert(
            abi.encodeWithSelector(ChartersComplianceRegistry.NotCouncil.selector, OUTSIDER)
        );
        reg.attestNonAlignedAddress(SUBJECT, REASON_2G, EVIDENCE_CID, sigs, signers);
    }

    function test_finalize_after_appeal_window() public {
        (bytes[] memory sigs, address[] memory signers) = _signers3();
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
        (bytes[] memory sigs, address[] memory signers) = _signers3();
        reg.attestNonAlignedAddress(SUBJECT, REASON_2G, EVIDENCE_CID, sigs, signers);

        bytes32 newEvidence = bytes32("ipfs://QmCounterEvidence...");
        bytes32 subjectHash = keccak256(abi.encode(SUBJECT, true));
        reg.acceptAppeal(subjectHash, true, SUBJECT, 0, newEvidence, sigs, signers);

        // Status = Aligned, no longer triggers enforcement
        assertFalse(reg.isNonAlignedAddress(SUBJECT));
    }

    function test_rehabilitate_path() public {
        (bytes[] memory sigs, address[] memory signers) = _signers3();
        reg.attestNonAlignedAddress(SUBJECT, REASON_2G, EVIDENCE_CID, sigs, signers);

        skip(30 days + 1);
        reg.finalize(true, SUBJECT, 0);
        assertTrue(reg.isNonAlignedAddress(SUBJECT));

        // Subject submits teshuvah + 3 council sign
        bytes32 teshuvahCid = bytes32("ipfs://QmTeshuvah...");
        reg.rehabilitate(true, SUBJECT, 0, teshuvahCid, sigs, signers);

        // Enforcement gates lifted, but status remains Rehabilitated (permanent record)
        assertFalse(reg.isNonAlignedAddress(SUBJECT));
    }

    // ─── Token ID variant ──────────────────────────────────────────

    function test_attestNonAlignedTokenId() public {
        (bytes[] memory sigs, address[] memory signers) = _signers3();
        uint256 tokenId = 42;
        reg.attestNonAlignedTokenId(tokenId, REASON_2G, EVIDENCE_CID, sigs, signers);

        assertFalse(reg.isNonAlignedTokenId(tokenId));  // appeal window open
        skip(30 days + 1);
        reg.finalize(false, address(0), tokenId);
        assertTrue(reg.isNonAlignedTokenId(tokenId));
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
