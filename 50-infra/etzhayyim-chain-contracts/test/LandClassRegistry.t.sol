// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {LandClassRegistry, IERC1155Minimal, IERC1155MetadataURIMinimal} from "../src/LandClassRegistry.sol";
import {LandRegistry} from "../src/LandRegistry.sol";

/// @dev First test coverage for LandClassRegistry.sol (ADR-2605252315), the ERC-1155
///      aggregate accounting layer for donated land classes (Agricultural/Residential/
///      Forest/.../Orbit). It's an R0 scaffold — view/aggregate/mirror functions revert
///      NotYetActivated() and transfers are permanently rejected via LandClassSoulbound()
///      — but the CLASS_* token-id constants are LIVE and carry a real cross-contract
///      invariant ("Token IDs MUST match LandRegistry.LandType enum order") that had never
///      actually been checked against LandRegistry.LandType itself.
contract LandClassRegistryTest is Test {
    LandClassRegistry classes;
    address constant CHARTERS = address(0xC4A47E7);

    function setUp() public {
        classes = new LandClassRegistry(CHARTERS);
    }

    function test_constructor_setsChartersAndStartsUnactivated() public view {
        assertEq(classes.charters(), CHARTERS);
        assertFalse(classes.activated());
        assertEq(classes.anchorBridge(), address(0));
        assertEq(classes.publicLandRegistry(), address(0));
    }

    // ── drift guard: CLASS_* constants MUST match LandRegistry.LandType enum order ──

    function test_classConstants_matchLandRegistryLandTypeEnumOrder() public view {
        assertEq(classes.CLASS_AGRICULTURAL(), uint256(LandRegistry.LandType.Agricultural));
        assertEq(classes.CLASS_RESIDENTIAL(), uint256(LandRegistry.LandType.Residential));
        assertEq(classes.CLASS_FOREST(), uint256(LandRegistry.LandType.Forest));
        assertEq(classes.CLASS_RELIGIOUS_FAC(), uint256(LandRegistry.LandType.ReligiousFacility));
        assertEq(classes.CLASS_OTHER(), uint256(LandRegistry.LandType.Other));
        assertEq(classes.CLASS_OCEAN(), uint256(LandRegistry.LandType.Ocean));
        assertEq(classes.CLASS_WATER(), uint256(LandRegistry.LandType.Water));
        assertEq(classes.CLASS_AIR(), uint256(LandRegistry.LandType.Air));
        assertEq(classes.CLASS_ORBIT(), uint256(LandRegistry.LandType.Orbit));
    }

    function test_supportsInterface_recognizesImplementedInterfaces() public view {
        assertTrue(classes.supportsInterface(type(IERC1155Minimal).interfaceId));
        assertTrue(classes.supportsInterface(type(IERC1155MetadataURIMinimal).interfaceId));
        assertTrue(classes.supportsInterface(bytes4(0x01ffc9a7))); // ERC-165 itself
    }

    function test_supportsInterface_rejectsUnknownInterface() public view {
        assertFalse(classes.supportsInterface(bytes4(0xffffffff)));
    }

    // ── ERC-1155 views: all revert pre-activation ────────────────────────────

    function test_balanceOf_revertsNotYetActivated() public {
        vm.expectRevert(LandClassRegistry.NotYetActivated.selector);
        classes.balanceOf(address(this), 0);
    }

    function test_balanceOfBatch_revertsNotYetActivated() public {
        address[] memory accounts = new address[](1);
        accounts[0] = address(this);
        uint256[] memory ids = new uint256[](1);
        ids[0] = 0;
        vm.expectRevert(LandClassRegistry.NotYetActivated.selector);
        classes.balanceOfBatch(accounts, ids);
    }

    function test_isApprovedForAll_revertsNotYetActivated() public {
        vm.expectRevert(LandClassRegistry.NotYetActivated.selector);
        classes.isApprovedForAll(address(this), address(0xB0B));
    }

    function test_uri_revertsNotYetActivated() public {
        vm.expectRevert(LandClassRegistry.NotYetActivated.selector);
        classes.uri(0);
    }

    // ── ERC-1155 mutators: permanently soulbound, never NotYetActivated ──────

    function test_safeTransferFrom_revertsLandClassSoulbound() public {
        vm.expectRevert(LandClassRegistry.LandClassSoulbound.selector);
        classes.safeTransferFrom(address(this), address(0xB0B), 0, 1, "");
    }

    function test_safeBatchTransferFrom_revertsLandClassSoulbound() public {
        uint256[] memory ids = new uint256[](1);
        ids[0] = 0;
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = 1;
        vm.expectRevert(LandClassRegistry.LandClassSoulbound.selector);
        classes.safeBatchTransferFrom(address(this), address(0xB0B), ids, amounts, "");
    }

    function test_setApprovalForAll_revertsLandClassSoulbound() public {
        vm.expectRevert(LandClassRegistry.LandClassSoulbound.selector);
        classes.setApprovalForAll(address(0xB0B), true);
    }

    // ── aggregate views + mirror flow + activation: all revert pre-activation ──

    function test_totalAreaByClass_revertsNotYetActivated() public {
        vm.expectRevert(LandClassRegistry.NotYetActivated.selector);
        classes.totalAreaByClass(0);
    }

    function test_parcelsByClass_revertsNotYetActivated() public {
        vm.expectRevert(LandClassRegistry.NotYetActivated.selector);
        classes.parcelsByClass(0, 0, 10);
    }

    function test_recordClassFromAnchor_revertsNotYetActivated() public {
        vm.expectRevert(LandClassRegistry.NotYetActivated.selector);
        classes.recordClassFromAnchor(1, 0, 1000);
    }

    function test_activate_revertsNotYetActivated() public {
        bytes[] memory sigs = new bytes[](0);
        address[] memory signers = new address[](0);
        vm.expectRevert(LandClassRegistry.NotYetActivated.selector);
        classes.activate(address(0xB0B), address(0xCA5C), sigs, signers);
    }
}
