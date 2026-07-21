// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {PublicLandRegistry, IERC721Minimal, IERC721MetadataMinimal} from "../src/PublicLandRegistry.sol";
import {IERC5192} from "../src/interfaces/IERC5192.sol";

/// @dev First test coverage for PublicLandRegistry.sol (ADR-2605252315), the Base L2
///      ERC-721/ERC-5192 mirror of donated land. It's an R0 scaffold — every state-mutating
///      function reverts NotYetActivated() until a Council activation ADR — but that revert
///      boundary IS the constitutional invariant (donated land can never be transferred, even
///      by accident, before real activation logic exists), plus name/symbol/supportsInterface
///      are genuinely live. None of it had any assertions.
contract PublicLandRegistryTest is Test {
    PublicLandRegistry registry;
    address constant CHARTERS = address(0xC4A47E7);

    function setUp() public {
        registry = new PublicLandRegistry(CHARTERS);
    }

    function test_constructor_setsChartersAndStartsUnactivated() public view {
        assertEq(registry.charters(), CHARTERS);
        assertFalse(registry.activated());
        assertEq(registry.anchorBridge(), address(0));
    }

    function test_metadata_nameAndSymbolAreLive() public view {
        assertEq(registry.name(), "etzhayyim Public Land Registry");
        assertEq(registry.symbol(), "EZ-LAND");
    }

    function test_supportsInterface_recognizesImplementedInterfaces() public view {
        assertTrue(registry.supportsInterface(type(IERC721Minimal).interfaceId));
        assertTrue(registry.supportsInterface(type(IERC721MetadataMinimal).interfaceId));
        assertTrue(registry.supportsInterface(type(IERC5192).interfaceId));
        assertTrue(registry.supportsInterface(bytes4(0x01ffc9a7))); // ERC-165 itself
    }

    function test_supportsInterface_rejectsUnknownInterface() public view {
        assertFalse(registry.supportsInterface(bytes4(0xffffffff)));
        assertFalse(registry.supportsInterface(bytes4(0xdeadbeef)));
    }

    // ── ERC-721 views: all revert pre-activation ────────────────────────────

    function test_balanceOf_revertsNotYetActivated() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.balanceOf(address(this));
    }

    function test_ownerOf_revertsNotYetActivated() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.ownerOf(1);
    }

    function test_tokenURI_revertsNotYetActivated() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.tokenURI(1);
    }

    function test_getApproved_revertsNotYetActivated() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.getApproved(1);
    }

    function test_isApprovedForAll_revertsNotYetActivated() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.isApprovedForAll(address(this), address(0xB0B));
    }

    // ── ERC-721 mutators: constitutionally rejected, all revert ─────────────

    function test_safeTransferFrom3Arg_revertsNotYetActivated() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.safeTransferFrom(address(this), address(0xB0B), 1);
    }

    function test_safeTransferFrom4Arg_revertsNotYetActivated() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.safeTransferFrom(address(this), address(0xB0B), 1, "");
    }

    function test_transferFrom_revertsNotYetActivated() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.transferFrom(address(this), address(0xB0B), 1);
    }

    function test_approve_revertsNotYetActivated() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.approve(address(0xB0B), 1);
    }

    function test_setApprovalForAll_revertsNotYetActivated() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.setApprovalForAll(address(0xB0B), true);
    }

    // ── soulbound + mirror flow + activation: all revert pre-activation ─────

    function test_locked_revertsNotYetActivatedSinceActivatedCanNeverFlipInR0() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.locked(1);
    }

    function test_mintFromAnchor_revertsNotYetActivated() public {
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.mintFromAnchor(1, address(this), "ipfs://cid");
    }

    function test_activate_revertsNotYetActivated() public {
        bytes[] memory sigs = new bytes[](0);
        address[] memory signers = new address[](0);
        vm.expectRevert(PublicLandRegistry.NotYetActivated.selector);
        registry.activate(address(0xB0B), sigs, signers);
    }
}
