// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {StewardTenureRegistry} from "../src/StewardTenureRegistry.sol";
import {IERC7401} from "../src/interfaces/IERC7401.sol";
import {IERC5192} from "../src/interfaces/IERC5192.sol";

/// @dev First test coverage for StewardTenureRegistry.sol (ADR-2605252315 + ADR-2605192345),
///      the ERC-7401 nestable-NFT registry for steward tenures on donated land parcels. Last
///      of the 4 previously-untested R0 land-cluster scaffolds (DisplacementDividend,
///      PublicLandRegistry, LandClassRegistry already covered this loop). Every state-mutating
///      function reverts NotYetActivated() pre-activation -- the invariant this locks in is
///      that no tenure NFT can be minted/nested/terminated by anyone (not even Council) until
///      real activation logic lands, plus MIN_COUNCIL_SIGNERS and supportsInterface are live.
contract StewardTenureRegistryTest is Test {
    StewardTenureRegistry registry;
    address constant CHARTERS = address(0xC4A47E7);

    function setUp() public {
        registry = new StewardTenureRegistry(CHARTERS);
    }

    function test_constructor_setsChartersAndStartsUnactivated() public view {
        assertEq(registry.charters(), CHARTERS);
        assertFalse(registry.activated());
        assertEq(registry.publicLandRegistry(), address(0));
    }

    function test_minCouncilSigners_isThree() public view {
        assertEq(registry.MIN_COUNCIL_SIGNERS(), 3);
    }

    function test_supportsInterface_recognizesImplementedInterfaces() public view {
        assertTrue(registry.supportsInterface(type(IERC7401).interfaceId));
        assertTrue(registry.supportsInterface(type(IERC5192).interfaceId));
        assertTrue(registry.supportsInterface(bytes4(0x01ffc9a7))); // ERC-165 itself
    }

    function test_supportsInterface_rejectsUnknownInterface() public view {
        assertFalse(registry.supportsInterface(bytes4(0xffffffff)));
    }

    // ── ERC-7401 nestable views: all revert pre-activation ──────────────────

    function test_directOwnerOf_revertsNotYetActivated() public {
        vm.expectRevert(StewardTenureRegistry.NotYetActivated.selector);
        registry.directOwnerOf(1);
    }

    function test_addChild_revertsNotYetActivated() public {
        vm.expectRevert(StewardTenureRegistry.NotYetActivated.selector);
        registry.addChild(1, 1, "");
    }

    function test_acceptChild_revertsNotYetActivated() public {
        vm.expectRevert(StewardTenureRegistry.NotYetActivated.selector);
        registry.acceptChild(1, 0, address(this), 1);
    }

    // ── ERC-5192 soulbound-while-active: activated can never flip in R0 ──────

    function test_locked_revertsNotYetActivatedSinceActivatedCanNeverFlipInR0() public {
        vm.expectRevert(StewardTenureRegistry.NotYetActivated.selector);
        registry.locked(1);
    }

    // ── tenure lifecycle + views + activation: all revert pre-activation ─────

    function test_nestNew_revertsNotYetActivated() public {
        bytes[] memory sigs = new bytes[](0);
        address[] memory signers = new address[](0);
        vm.expectRevert(StewardTenureRegistry.NotYetActivated.selector);
        registry.nestNew(1, 1, StewardTenureRegistry.TenureType.Founder, uint64(block.timestamp + 365 days), bytes32("evidence"), sigs, signers);
    }

    function test_terminate_revertsNotYetActivated() public {
        bytes[] memory sigs = new bytes[](0);
        address[] memory signers = new address[](0);
        vm.expectRevert(StewardTenureRegistry.NotYetActivated.selector);
        registry.terminate(1, bytes32("reason"), sigs, signers);
    }

    function test_activeTenureOf_revertsNotYetActivated() public {
        vm.expectRevert(StewardTenureRegistry.NotYetActivated.selector);
        registry.activeTenureOf(1);
    }

    function test_tenureHistoryOf_revertsNotYetActivated() public {
        vm.expectRevert(StewardTenureRegistry.NotYetActivated.selector);
        registry.tenureHistoryOf(1);
    }

    function test_activate_revertsNotYetActivated() public {
        bytes[] memory sigs = new bytes[](0);
        address[] memory signers = new address[](0);
        vm.expectRevert(StewardTenureRegistry.NotYetActivated.selector);
        registry.activate(address(0xB0B), sigs, signers);
    }
}
