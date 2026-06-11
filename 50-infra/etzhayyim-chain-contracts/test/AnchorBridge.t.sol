// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {AnchorBridge} from "../src/AnchorBridge.sol";

contract AnchorBridgeTest is Test {
    AnchorBridge ab;

    function setUp() public {
        ab = new AnchorBridge();
    }

    function test_commitRoot_storesAndEnumerates() public {
        bytes32 root = keccak256("root-1");
        ab.commitRoot(root, hex"01020304", 100);
        assertEq(ab.latestRootHash(), root);
        assertEq(ab.totalRoots(), 1);
        assertEq(ab.allRoots(0), root);
        assertEq(ab.committerOf(root), address(this));
    }

    function test_commitRoot_chainsPrior() public {
        bytes32 r1 = keccak256("root-1");
        bytes32 r2 = keccak256("root-2");
        ab.commitRoot(r1, hex"01", 1);
        ab.commitRoot(r2, hex"02", 2);
        assertEq(ab.latestRootHash(), r2);
        assertEq(ab.allRoots(0), r1);
        assertEq(ab.allRoots(1), r2);
    }

    function test_commitRoot_rejectsDuplicate() public {
        bytes32 root = keccak256("root-1");
        ab.commitRoot(root, hex"01", 1);
        vm.expectRevert(bytes("duplicate root"));
        ab.commitRoot(root, hex"02", 2);
    }

    function test_commitRoot_emptyRootReverts() public {
        vm.expectRevert(AnchorBridge.EmptyRoot.selector);
        ab.commitRoot(bytes32(0), hex"01", 1);
    }

    function test_commitRoot_emptyCidReverts() public {
        vm.expectRevert(AnchorBridge.EmptyCid.selector);
        ab.commitRoot(keccak256("r"), hex"", 1);
    }
}
