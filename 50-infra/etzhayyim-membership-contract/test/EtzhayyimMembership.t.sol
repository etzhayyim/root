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
        (bytes32 storedOath, string memory gh, uint64 joined, uint64 revoked, ) = reg.members(alice);
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

        (, , uint64 joined, uint64 revoked, ) = reg.members(alice);
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

    function test_join_starts_at_level_1() public {
        vm.prank(alice);
        reg.join(oath, "alice");
        assertEq(reg.levelOf(alice), 1);
    }

    function test_advance_sequential() public {
        vm.prank(alice);
        reg.join(oath, "alice");
        vm.prank(alice);
        reg.advance(2, keccak256("at://alice/practice"), "first practice");
        assertEq(reg.levelOf(alice), 2);
        vm.prank(alice);
        reg.advance(3, keccak256("github:etzhayyim/root@abc"), "first PR");
        assertEq(reg.levelOf(alice), 3);
    }

    function test_advance_reverts_on_skip() public {
        vm.prank(alice);
        reg.join(oath, "alice");
        vm.expectRevert(abi.encodeWithSelector(EtzhayyimMembership.LevelNotSequential.selector, uint8(3), uint8(1)));
        vm.prank(alice);
        reg.advance(3, keccak256("skip"), "skipping");
    }

    function test_advance_reverts_on_invalid_level() public {
        vm.prank(alice);
        reg.join(oath, "alice");
        vm.expectRevert(abi.encodeWithSelector(EtzhayyimMembership.InvalidLevel.selector, uint8(8)));
        vm.prank(alice);
        reg.advance(8, keccak256("over"), "too high");
    }

    function test_advance_reverts_on_empty_evidence() public {
        vm.prank(alice);
        reg.join(oath, "alice");
        vm.expectRevert(EtzhayyimMembership.EmptyEvidence.selector);
        vm.prank(alice);
        reg.advance(2, bytes32(0), "no evidence");
    }

    function test_revoked_member_cannot_advance() public {
        vm.prank(alice);
        reg.join(oath, "alice");
        vm.prank(alice);
        reg.revoke();
        vm.expectRevert(abi.encodeWithSelector(EtzhayyimMembership.NotMember.selector, alice));
        vm.prank(alice);
        reg.advance(2, keccak256("after revoke"), "");
    }

    function test_advance_to_level_7_full_path() public {
        vm.startPrank(alice);
        reg.join(oath, "alice");
        for (uint8 lv = 2; lv <= 7; lv++) {
            reg.advance(lv, keccak256(abi.encode(lv)), "");
        }
        vm.stopPrank();
        assertEq(reg.levelOf(alice), 7);
        // Level 7 is the cap; advancing further reverts on InvalidLevel
        vm.expectRevert(abi.encodeWithSelector(EtzhayyimMembership.InvalidLevel.selector, uint8(8)));
        vm.prank(alice);
        reg.advance(8, keccak256("over"), "");
    }
}
