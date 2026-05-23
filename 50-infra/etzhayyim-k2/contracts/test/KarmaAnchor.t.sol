// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {KarmaAnchor} from "../src/KarmaAnchor.sol";

contract KarmaAnchorTest is Test {
    KarmaAnchor internal anchor;
    address internal council = makeAddr("council");
    address internal stranger = makeAddr("stranger");

    function setUp() public {
        anchor = new KarmaAnchor(council);
    }

    function test_constructorSetsOwner() public view {
        assertEq(anchor.owner(), council);
    }

    function test_constructorRevertsOnZeroOwner() public {
        vm.expectRevert(KarmaAnchor.ZeroAddress.selector);
        new KarmaAnchor(address(0));
    }

    function test_submitAnchor_happyPath() public {
        bytes32 root = keccak256("root");
        bytes32 cid = keccak256("cid");
        vm.prank(council);
        anchor.submitAnchor(20260521, root, cid);
        KarmaAnchor.Anchor memory a = anchor.getAnchor(20260521);
        assertEq(a.merkleRoot, root);
        assertEq(a.ipfsCidHash, cid);
        assertTrue(a.present);
    }

    function test_submitAnchor_revertsNotOwner() public {
        vm.prank(stranger);
        vm.expectRevert(KarmaAnchor.NotOwner.selector);
        anchor.submitAnchor(20260521, keccak256("r"), keccak256("c"));
    }

    function test_submitAnchor_revertsZeroRoot() public {
        vm.prank(council);
        vm.expectRevert(KarmaAnchor.InvalidArgument.selector);
        anchor.submitAnchor(20260521, bytes32(0), keccak256("c"));
    }

    function test_submitAnchor_revertsZeroCid() public {
        vm.prank(council);
        vm.expectRevert(KarmaAnchor.InvalidArgument.selector);
        anchor.submitAnchor(20260521, keccak256("r"), bytes32(0));
    }

    function test_submitAnchor_revertsDoubleSubmit() public {
        vm.prank(council);
        anchor.submitAnchor(20260521, keccak256("r"), keccak256("c"));
        vm.prank(council);
        vm.expectRevert(KarmaAnchor.AnchorAlreadyExists.selector);
        anchor.submitAnchor(20260521, keccak256("r2"), keccak256("c2"));
    }

    function test_verifyLeaf_validProof_4leafTree() public {
        // Build a small Merkle tree of 4 leaves with sorted-pair hashing.
        bytes32 leafA = keccak256("a");
        bytes32 leafB = keccak256("b");
        bytes32 leafC = keccak256("c");
        bytes32 leafD = keccak256("d");

        bytes32 ab = leafA < leafB
            ? keccak256(abi.encodePacked(leafA, leafB))
            : keccak256(abi.encodePacked(leafB, leafA));
        bytes32 cd = leafC < leafD
            ? keccak256(abi.encodePacked(leafC, leafD))
            : keccak256(abi.encodePacked(leafD, leafC));
        bytes32 root = ab < cd
            ? keccak256(abi.encodePacked(ab, cd))
            : keccak256(abi.encodePacked(cd, ab));

        vm.prank(council);
        anchor.submitAnchor(1, root, keccak256("cid"));

        // Proof for leafA: sibling leafB, then sibling cd.
        bytes32[] memory proof = new bytes32[](2);
        proof[0] = leafB;
        proof[1] = cd;
        assertTrue(anchor.verifyLeaf(1, leafA, proof));

        // Wrong leaf must fail.
        assertFalse(anchor.verifyLeaf(1, keccak256("x"), proof));

        // No anchor for unrelated epoch.
        assertFalse(anchor.verifyLeaf(999, leafA, proof));
    }

    function test_setOwner_happyPath() public {
        address newCouncil = makeAddr("newCouncil");
        vm.prank(council);
        anchor.setOwner(newCouncil);
        assertEq(anchor.owner(), newCouncil);
    }

    function test_setOwner_revertsNotOwner() public {
        vm.prank(stranger);
        vm.expectRevert(KarmaAnchor.NotOwner.selector);
        anchor.setOwner(stranger);
    }
}
