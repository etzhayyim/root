// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {EtzhayyimMembership} from "../src/EtzhayyimMembership.sol";

contract EtzhayyimMembershipTest is Test {
    EtzhayyimMembership reg;
    address alice = address(0xA1);
    address bob = address(0xB0B);
    bytes32 oath = keccak256("I, as a follower of etzhayyim, ...");

    function setUp() public {
        reg = new EtzhayyimMembership();
    }

    function test_join_emits_event_and_stores() public {
        vm.prank(alice);
        vm.expectEmit(true, true, false, true);
        emit EtzhayyimMembership.Joined(alice, oath, "alice-github", uint64(block.timestamp));
        reg.join(oath, "alice-github");

        assertEq(reg.memberCount(), 1);
        (bytes32 storedOath, string memory gh, uint64 joined, uint64 revoked) = reg.members(alice);
        assertEq(storedOath, oath);
        assertEq(gh, "alice-github");
        assertGt(joined, 0);
        assertEq(revoked, 0);
        assertTrue(reg.isActiveMember(alice));
    }

    function test_join_reverts_on_duplicate() public {
        vm.prank(alice);
        reg.join(oath, "alice");
        vm.expectRevert(abi.encodeWithSelector(EtzhayyimMembership.AlreadyMember.selector, alice));
        vm.prank(alice);
        reg.join(oath, "alice2");
    }

    function test_join_reverts_on_empty_oath() public {
        vm.expectRevert(EtzhayyimMembership.EmptyOathHash.selector);
        vm.prank(alice);
        reg.join(bytes32(0), "alice");
    }

    function test_revoke_keeps_history() public {
        vm.prank(alice);
        reg.join(oath, "alice");

        vm.prank(alice);
        reg.revoke();

        (, , uint64 joined, uint64 revoked) = reg.members(alice);
        assertGt(joined, 0);
        assertGt(revoked, 0);
        assertFalse(reg.isActiveMember(alice));
        // memberCount still 1 — revoked doesn't remove
        assertEq(reg.memberCount(), 1);
    }

    function test_revoke_reverts_on_non_member() public {
        vm.expectRevert(abi.encodeWithSelector(EtzhayyimMembership.NotMember.selector, bob));
        vm.prank(bob);
        reg.revoke();
    }

    function test_listMembers_paginates() public {
        for (uint160 i = 1; i <= 5; i++) {
            vm.prank(address(i));
            reg.join(keccak256(abi.encode(i)), "");
        }
        address[] memory page = reg.listMembers(1, 2);
        assertEq(page.length, 2);
        assertEq(page[0], address(2));
        assertEq(page[1], address(3));
    }
}
