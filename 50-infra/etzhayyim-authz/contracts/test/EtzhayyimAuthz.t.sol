// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {EtzhayyimAuthz} from "../src/EtzhayyimAuthz.sol";

contract EtzhayyimAuthzTest is Test {
    EtzhayyimAuthz internal authz;

    address internal council = makeAddr("council");
    uint256 internal aliceKeyPk = 0xA11CE;
    address internal aliceKey;
    uint256 internal bobKeyPk = 0xB0B;
    address internal bobKey;
    address internal stranger = makeAddr("stranger");

    bytes32 internal aliceDwebHash = keccak256(bytes("alice.etzhayyim.com"));
    bytes32 internal bobDwebHash = keccak256(bytes("bob.etzhayyim.com"));

    function setUp() public {
        aliceKey = vm.addr(aliceKeyPk);
        bobKey = vm.addr(bobKeyPk);
        authz = new EtzhayyimAuthz(council);
    }

    // ─── Construction ──────────────────────────────────────────────────

    function test_constructorSetsOwner() public view {
        assertEq(authz.owner(), council);
    }

    function test_constructorRevertsOnZeroOwner() public {
        vm.expectRevert(EtzhayyimAuthz.ZeroAddress.selector);
        new EtzhayyimAuthz(address(0));
    }

    // ─── provisionRoot ─────────────────────────────────────────────────

    function test_provisionRoot_happyPath() public {
        vm.prank(council);
        bytes32 rootId = authz.provisionRoot(aliceDwebHash, aliceKey);
        assertTrue(rootId != bytes32(0));

        (bytes32 resolvedRootId, EtzhayyimAuthz.Root memory data) = authz.resolveDwebHandle(aliceDwebHash);
        assertEq(resolvedRootId, rootId);
        assertEq(data.activeKey, aliceKey);
        assertTrue(data.active);
        assertEq(data.predecessorVendorAddr, address(0));
        assertEq(data.predecessorVendorRootHash, bytes32(0));
        assertTrue(authz.isActive(rootId));
    }

    function test_provisionRoot_revertsNotOwner() public {
        vm.prank(stranger);
        vm.expectRevert(EtzhayyimAuthz.NotOwner.selector);
        authz.provisionRoot(aliceDwebHash, aliceKey);
    }

    function test_provisionRoot_revertsZeroKey() public {
        vm.prank(council);
        vm.expectRevert(EtzhayyimAuthz.ZeroAddress.selector);
        authz.provisionRoot(aliceDwebHash, address(0));
    }

    function test_provisionRoot_revertsZeroDweb() public {
        vm.prank(council);
        vm.expectRevert(EtzhayyimAuthz.InvalidArgument.selector);
        authz.provisionRoot(bytes32(0), aliceKey);
    }

    function test_provisionRoot_revertsDwebTaken() public {
        vm.prank(council);
        authz.provisionRoot(aliceDwebHash, aliceKey);
        vm.prank(council);
        vm.expectRevert(EtzhayyimAuthz.DwebTaken.selector);
        authz.provisionRoot(aliceDwebHash, bobKey);
    }

    // ─── mirrorVendorRoot ─────────────────────────────────────────────

    function test_mirrorVendorRoot_happyPath() public {
        bytes32 vendorRootHash = keccak256("did:erc725:etzhayyim:260425:0xVENDOR");
        address vendorAddr = makeAddr("vendorWallet");

        vm.prank(council);
        bytes32 rootId = authz.mirrorVendorRoot(aliceDwebHash, aliceKey, vendorRootHash, vendorAddr);

        EtzhayyimAuthz.Root memory data = authz.getProvenance(rootId);
        assertEq(data.activeKey, aliceKey);
        assertEq(data.predecessorVendorAddr, vendorAddr);
        assertEq(data.predecessorVendorRootHash, vendorRootHash);
        assertTrue(data.active);
    }

    function test_mirrorVendorRoot_revertsZeroVendorHash() public {
        vm.prank(council);
        vm.expectRevert(EtzhayyimAuthz.InvalidArgument.selector);
        authz.mirrorVendorRoot(aliceDwebHash, aliceKey, bytes32(0), makeAddr("vendorWallet"));
    }

    function test_mirrorVendorRoot_revertsZeroVendorAddr() public {
        vm.prank(council);
        vm.expectRevert(EtzhayyimAuthz.ZeroAddress.selector);
        authz.mirrorVendorRoot(aliceDwebHash, aliceKey, keccak256("v"), address(0));
    }

    // ─── rotateKey ────────────────────────────────────────────────────

    function test_rotateKey_happyPath() public {
        vm.prank(council);
        bytes32 rootId = authz.provisionRoot(aliceDwebHash, aliceKey);

        uint96 createdBlock = authz.getProvenance(rootId).lastRotatedBlock;

        bytes32 inner = keccak256(
            abi.encode(
                "etzhayyim-authz-rotate",
                address(authz),
                block.chainid,
                rootId,
                bobKey,
                createdBlock
            )
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", inner));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(aliceKeyPk, digest);
        bytes memory sig = abi.encodePacked(r, s, v);

        // Move forward 1 block so lastRotatedBlock changes
        vm.roll(block.number + 1);
        vm.prank(stranger);
        authz.rotateKey(rootId, bobKey, sig);

        assertEq(authz.getProvenance(rootId).activeKey, bobKey);
    }

    function test_rotateKey_revertsWrongSigner() public {
        vm.prank(council);
        bytes32 rootId = authz.provisionRoot(aliceDwebHash, aliceKey);

        uint96 createdBlock = authz.getProvenance(rootId).lastRotatedBlock;
        bytes32 inner = keccak256(
            abi.encode(
                "etzhayyim-authz-rotate",
                address(authz),
                block.chainid,
                rootId,
                bobKey,
                createdBlock
            )
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", inner));
        // Wrong signer: bob signs instead of alice (current active key)
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(bobKeyPk, digest);
        bytes memory sig = abi.encodePacked(r, s, v);

        vm.expectRevert(EtzhayyimAuthz.NotActiveKey.selector);
        authz.rotateKey(rootId, bobKey, sig);
    }

    function test_rotateKey_revertsRootNotFound() public {
        bytes32 fakeRoot = keccak256("nope");
        bytes memory sig = new bytes(65);
        vm.expectRevert(EtzhayyimAuthz.RootNotFound.selector);
        authz.rotateKey(fakeRoot, bobKey, sig);
    }

    // ─── deactivateRoot ──────────────────────────────────────────────

    function test_deactivateRoot_happyPath() public {
        vm.prank(council);
        bytes32 rootId = authz.provisionRoot(aliceDwebHash, aliceKey);

        assertTrue(authz.isActive(rootId));
        vm.prank(council);
        authz.deactivateRoot(rootId);
        assertFalse(authz.isActive(rootId));
    }

    function test_deactivateRoot_revertsNotOwner() public {
        vm.prank(council);
        bytes32 rootId = authz.provisionRoot(aliceDwebHash, aliceKey);
        vm.prank(stranger);
        vm.expectRevert(EtzhayyimAuthz.NotOwner.selector);
        authz.deactivateRoot(rootId);
    }

    // ─── setOwner ─────────────────────────────────────────────────────

    function test_setOwner_happyPath() public {
        address newCouncil = makeAddr("newCouncil");
        vm.prank(council);
        authz.setOwner(newCouncil);
        assertEq(authz.owner(), newCouncil);
    }

    function test_setOwner_revertsNotOwner() public {
        vm.prank(stranger);
        vm.expectRevert(EtzhayyimAuthz.NotOwner.selector);
        authz.setOwner(stranger);
    }
}
