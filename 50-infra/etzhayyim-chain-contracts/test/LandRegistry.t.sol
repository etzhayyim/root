// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {
    LandRegistry,
    IAdherentRegistry as ILandAdherentRegistry,
    IChartersComplianceRegistry as ILandCharters
} from "../src/LandRegistry.sol";
import {IERC5192} from "../src/interfaces/IERC5192.sol";
import {AdherentRegistry} from "../src/AdherentRegistry.sol";
import {ChartersComplianceRegistry, IAdherentRegistry as ICharterAdherentRegistry} from "../src/ChartersComplianceRegistry.sol";

/// @dev First test coverage for LandRegistry.sol (ADR-2605192245 + ADR-2605252315).
///      Land donation is constitutionally inalienable — this suite exists to verify
///      that invariant holds in code, not just in comments, before any real donation
///      is ever recorded (LANDS.md is still "awaiting first donation" as of writing).
contract LandRegistryTest is Test {
    LandRegistry land;
    AdherentRegistry adherents;
    ChartersComplianceRegistry charters;

    address constant DONOR   = address(0xD0707);
    address constant STEWARD = address(0x57EEA7D);
    address constant OUTSIDER = address(0x0075);

    // ChartersComplianceRegistry requires exactly 5 bootstrap council seats.
    uint256[5] councilKeys = [uint256(1), uint256(2), uint256(3), uint256(4), uint256(5)];
    address[5] council;

    bytes32 constant OATH = keccak256("oath");
    bytes32 constant GEOJSON = keccak256("geojson");
    bytes32 constant IMAGERY = keccak256("imagery");
    bytes32 constant DEED = keccak256("deed");
    bytes32 constant NATIONAL_REF = keccak256("national-ref");
    uint256 constant AREA_M2 = 10_000;

    function setUp() public {
        for (uint256 i = 0; i < 5; i++) {
            council[i] = vm.addr(councilKeys[i]);
        }
        address[] memory officers = new address[](1);
        officers[0] = address(this);
        adherents = new AdherentRegistry(officers);

        address[] memory bootstrap = new address[](5);
        for (uint256 i = 0; i < 5; i++) bootstrap[i] = council[i];
        charters = new ChartersComplianceRegistry(ICharterAdherentRegistry(address(adherents)), bootstrap);

        land = new LandRegistry(
            ILandAdherentRegistry(address(adherents)),
            ILandCharters(address(charters))
        );
    }

    function _donate() internal returns (uint256 landId) {
        vm.prank(DONOR);
        landId = land.donate(OATH, GEOJSON, IMAGERY, DEED, NATIONAL_REF, AREA_M2, LandRegistry.LandType.Agricultural, STEWARD);
    }

    /// Marks `subject` non-aligned via a real Council-quorum attestation + finalize
    /// (the only path that can make isNonAlignedAddress() return true).
    function _makeNonAligned(address subject) internal {
        bytes[] memory sigs = new bytes[](3);
        address[] memory signers = new address[](3);
        for (uint256 i = 0; i < 3; i++) { sigs[i] = ""; signers[i] = council[i]; }
        charters.attestNonAlignedAddress(subject, keccak256("reason"), keccak256("evidence"), sigs, signers);
        vm.warp(block.timestamp + charters.APPEAL_WINDOW() + 1);
        charters.finalize(true, subject, 0);
        assertTrue(charters.isNonAlignedAddress(subject));
    }

    // ── donate() ──────────────────────────────────────────────────────────

    function test_donate_mintsSequentiallyAndStoresRecord() public {
        uint256 id1 = _donate();
        assertEq(id1, 1);

        (
            bytes32 oathHash, bytes32 geojsonCid, bytes32 imageryBundleCid, bytes32 deedCid,
            bytes32 nationalRegistryRefHash, uint256 areaM2, LandRegistry.LandType landType,
            address steward, uint64 donatedAt, LandRegistry.Status status
        ) = land.lands(id1);
        assertEq(oathHash, OATH);
        assertEq(geojsonCid, GEOJSON);
        assertEq(imageryBundleCid, IMAGERY);
        assertEq(deedCid, DEED);
        assertEq(nationalRegistryRefHash, NATIONAL_REF);
        assertEq(areaM2, AREA_M2);
        assertEq(uint8(landType), uint8(LandRegistry.LandType.Agricultural));
        assertEq(steward, STEWARD);
        assertEq(donatedAt, uint64(block.timestamp));
        assertEq(uint8(status), uint8(LandRegistry.Status.Active));

        vm.prank(DONOR);
        uint256 id2 = land.donate(OATH, GEOJSON, IMAGERY, DEED, NATIONAL_REF, AREA_M2, LandRegistry.LandType.Forest, STEWARD);
        assertEq(id2, 2);
        assertEq(land.nextLandId(), 3);
    }

    function test_donate_emitsDonatedAndLocked() public {
        vm.expectEmit(true, true, false, true);
        emit LandRegistry.Donated(1, DONOR, GEOJSON, AREA_M2, LandRegistry.LandType.Agricultural);
        vm.expectEmit(true, false, false, false);
        emit IERC5192.Locked(1);
        _donate();
    }

    function test_donate_tracksStewardLands() public {
        uint256 id1 = _donate();
        vm.prank(DONOR);
        uint256 id2 = land.donate(OATH, GEOJSON, IMAGERY, DEED, NATIONAL_REF, AREA_M2, LandRegistry.LandType.Water, STEWARD);
        assertEq(land.stewardLands(STEWARD, 0), id1);
        assertEq(land.stewardLands(STEWARD, 1), id2);
    }

    function test_donate_revertsForNonAlignedDonor() public {
        _makeNonAligned(DONOR);
        vm.prank(DONOR);
        vm.expectRevert(abi.encodeWithSelector(LandRegistry.StewardNotEligible.selector, DONOR));
        land.donate(OATH, GEOJSON, IMAGERY, DEED, NATIONAL_REF, AREA_M2, LandRegistry.LandType.Agricultural, STEWARD);
    }

    function test_donate_revertsForNonAlignedSteward() public {
        _makeNonAligned(STEWARD);
        vm.prank(DONOR);
        vm.expectRevert(abi.encodeWithSelector(LandRegistry.StewardNotEligible.selector, STEWARD));
        land.donate(OATH, GEOJSON, IMAGERY, DEED, NATIONAL_REF, AREA_M2, LandRegistry.LandType.Agricultural, STEWARD);
    }

    // ── ERC-5192 soulbound signalling ───────────────────────────────────────

    function test_locked_alwaysTrueForDonatedLand() public {
        uint256 id = _donate();
        assertTrue(land.locked(id));
    }

    function test_locked_revertsForUnknownLandId() public {
        vm.expectRevert(abi.encodeWithSelector(LandRegistry.LandNotFound.selector, 999));
        land.locked(999);
    }

    function test_supportsInterface_erc5192AndErc165Only() public view {
        assertTrue(land.supportsInterface(0xb45a3c0e)); // ERC-5192
        assertTrue(land.supportsInterface(0x01ffc9a7)); // ERC-165
        assertFalse(land.supportsInterface(0x80ac58cd)); // ERC-721 — NOT supported (no transfer)
    }

    // ── reassignSteward() — Council Lv6+ >=3 quorum ─────────────────────────

    function test_reassignSteward_requiresMinimumSignerCount() public {
        uint256 id = _donate();
        bytes[] memory sigs = new bytes[](2);
        address[] memory signers = new address[](2);
        signers[0] = council[0]; signers[1] = council[1];
        vm.expectRevert(LandRegistry.InsufficientCouncilSigners.selector);
        land.reassignSteward(id, OUTSIDER, sigs, signers);
    }

    function test_reassignSteward_rejectsNonCouncilSigner() public {
        uint256 id = _donate();
        bytes[] memory sigs = new bytes[](3);
        address[] memory signers = new address[](3);
        signers[0] = council[0]; signers[1] = council[1]; signers[2] = OUTSIDER;
        vm.expectRevert(abi.encodeWithSelector(LandRegistry.NotCouncilMember.selector, OUTSIDER));
        land.reassignSteward(id, OUTSIDER, sigs, signers);
    }

    function test_reassignSteward_happyPath() public {
        uint256 id = _donate();
        bytes[] memory sigs = new bytes[](3);
        address[] memory signers = new address[](3);
        for (uint256 i = 0; i < 3; i++) { sigs[i] = ""; signers[i] = council[i]; }

        vm.expectEmit(true, false, false, true);
        emit LandRegistry.StewardChanged(id, STEWARD, OUTSIDER);
        land.reassignSteward(id, OUTSIDER, sigs, signers);

        (, , , , , , , address steward, ,) = land.lands(id);
        assertEq(steward, OUTSIDER);
    }

    function test_reassignSteward_revertsIfNotActive() public {
        uint256 id = _donate();
        land.openDispute(id, keccak256("evidence"));

        bytes[] memory sigs = new bytes[](3);
        address[] memory signers = new address[](3);
        for (uint256 i = 0; i < 3; i++) { sigs[i] = ""; signers[i] = council[i]; }
        vm.expectRevert(abi.encodeWithSelector(LandRegistry.LandNotActive.selector, id));
        land.reassignSteward(id, OUTSIDER, sigs, signers);
    }

    function test_reassignSteward_revertsForNonAlignedNewSteward() public {
        uint256 id = _donate();
        _makeNonAligned(OUTSIDER);
        bytes[] memory sigs = new bytes[](3);
        address[] memory signers = new address[](3);
        for (uint256 i = 0; i < 3; i++) { sigs[i] = ""; signers[i] = council[i]; }
        vm.expectRevert(abi.encodeWithSelector(LandRegistry.StewardNotEligible.selector, OUTSIDER));
        land.reassignSteward(id, OUTSIDER, sigs, signers);
    }

    // ── dispute lifecycle ───────────────────────────────────────────────────

    function test_openDispute_setsUnderDisputeAndEmits() public {
        uint256 id = _donate();
        vm.expectEmit(true, false, false, true);
        emit LandRegistry.DisputeOpened(id, keccak256("evidence"));
        land.openDispute(id, keccak256("evidence"));
        (, , , , , , , , , LandRegistry.Status status) = land.lands(id);
        assertEq(uint8(status), uint8(LandRegistry.Status.UnderDispute));
    }

    function test_openDispute_revertsIfAlreadyDisputed() public {
        uint256 id = _donate();
        land.openDispute(id, keccak256("evidence"));
        vm.expectRevert(abi.encodeWithSelector(LandRegistry.LandNotActive.selector, id));
        land.openDispute(id, keccak256("evidence-2"));
    }

    function test_resolveDispute_requiresCouncilQuorum() public {
        uint256 id = _donate();
        land.openDispute(id, keccak256("evidence"));
        bytes[] memory sigs = new bytes[](2);
        address[] memory signers = new address[](2);
        signers[0] = council[0]; signers[1] = council[1];
        vm.expectRevert(LandRegistry.InsufficientCouncilSigners.selector);
        land.resolveDispute(id, LandRegistry.Status.Active, sigs, signers);
    }

    function test_resolveDispute_happyPathRestoresActive() public {
        uint256 id = _donate();
        land.openDispute(id, keccak256("evidence"));

        bytes[] memory sigs = new bytes[](3);
        address[] memory signers = new address[](3);
        for (uint256 i = 0; i < 3; i++) { sigs[i] = ""; signers[i] = council[i]; }

        vm.expectEmit(true, false, false, true);
        emit LandRegistry.DisputeResolved(id, LandRegistry.Status.Active);
        land.resolveDispute(id, LandRegistry.Status.Active, sigs, signers);

        (, , , , , , , , , LandRegistry.Status status) = land.lands(id);
        assertEq(uint8(status), uint8(LandRegistry.Status.Active));
    }

    // ── constitutional invariant: no transfer/burn/setOwner surface exists ──
    // (Solidity has no function to call that doesn't exist; this documents the
    // invariant the same way ChartersComplianceRegistry's own tests do — by
    // asserting the only two ways `steward` or `status` can change are the
    // Council-gated paths already covered above.)
    function test_donate_isTheOnlyMintPath() public {
        // nextLandId only advances via donate(); no other function increments it.
        assertEq(land.nextLandId(), 1);
        _donate();
        assertEq(land.nextLandId(), 2);
    }
}
