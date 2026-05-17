// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {EtzhayyimAnchor} from "../src/EtzhayyimAnchor.sol";

contract EtzhayyimAnchorTest is Test {
    EtzhayyimAnchor anchorC;

    function setUp() public {
        anchorC = new EtzhayyimAnchor();
    }

    function test_anchor_emits_event_and_stores_entry() public {
        bytes32 root = keccak256(abi.encodePacked("root-1"));
        bytes memory cid = bytes("bafyreidemo...");
        vm.expectEmit(true, true, false, true);
        emit EtzhayyimAnchor.Anchored(root, address(this), cid, block.number, 100);
        anchorC.anchor(root, cid, 100);
        assertEq(anchorC.rootCount(), 1);
    }

    function test_anchor_reverts_on_duplicate() public {
        bytes32 root = keccak256(abi.encodePacked("root-1"));
        bytes memory cid = bytes("bafyreidemo...");
        anchorC.anchor(root, cid, 100);
        vm.expectRevert(abi.encodeWithSelector(EtzhayyimAnchor.AlreadyAnchored.selector, root));
        anchorC.anchor(root, cid, 100);
    }

    function test_anchor_reverts_on_empty_cid() public {
        bytes32 root = keccak256(abi.encodePacked("root-1"));
        vm.expectRevert(EtzhayyimAnchor.EmptyIpfsCid.selector);
        anchorC.anchor(root, bytes(""), 100);
    }

    function test_listRoots_paginates() public {
        for (uint256 i = 0; i < 5; i++) {
            anchorC.anchor(keccak256(abi.encode(i)), bytes("bafy..."), 1);
        }
        bytes32[] memory page = anchorC.listRoots(1, 2);
        assertEq(page.length, 2);
    }
}
