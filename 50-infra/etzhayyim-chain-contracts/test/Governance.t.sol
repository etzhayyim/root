// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {Fixture} from "./_helpers/Fixture.sol";
import {Constitution} from "../src/Constitution.sol";
import {Governance} from "../src/Governance.sol";

contract GovernanceTest is Fixture {
    function setUp() public {
        _deployStack();
    }

    function _makeQuorumOf(uint256 n) internal {
        // Seed `n` adherents (alice, bob, plus more). Each gets an SBT and
        // a fresh attestation. snapshotTotal at vote time will equal n.
        for (uint256 i = 0; i < n; ++i) {
            address holder = address(uint160(0x10000 + i));
            string memory did = string(abi.encodePacked("did:web:", vm.toString(holder)));
            vm.startPrank(officer);
            uint256 id = r.join(holder, did, bytes32(0));
            r.attest(id, EVT_PRAYER, bytes32(0));
            vm.stopPrank();
        }
    }

    function _proposeBaseRateChange(address proposer, uint256 newRate) internal returns (uint256 pid) {
        address[] memory targets = new address[](1);
        bytes[] memory cds = new bytes[](1);
        targets[0] = address(c);
        cds[0] = abi.encodeWithSelector(
            Constitution.setMutable.selector, K_KISHA_BASE, bytes32(newRate)
        );
        vm.prank(proposer);
        pid = gov.propose(targets, cds, keccak256("rationale-cid"));
    }

    function test_propose_requiresAdherent() public {
        address[] memory targets = new address[](1);
        bytes[] memory cds = new bytes[](1);
        targets[0] = address(c);
        cds[0] = abi.encodeWithSelector(Constitution.setMutable.selector, K_KISHA_BASE, bytes32(uint256(2_000_000)));
        vm.expectRevert(Governance.NotAdherent.selector);
        gov.propose(targets, cds, keccak256("r"));
    }

    function test_propose_requiresActive() public {
        // alice has SBT but never attested → inactive
        vm.prank(officer);
        r.join(alice, "did:web:alice.example.com", bytes32(0));
        address[] memory targets = new address[](1);
        bytes[] memory cds = new bytes[](1);
        targets[0] = address(c);
        cds[0] = abi.encodeWithSelector(Constitution.setMutable.selector, K_KISHA_BASE, bytes32(uint256(2_000_000)));
        vm.prank(alice);
        vm.expectRevert(abi.encodeWithSelector(Governance.NotActive.selector, uint256(1)));
        gov.propose(targets, cds, keccak256("r"));
    }

    function test_fullCycle_quorumPass_executesSetMutable() public {
        _makeQuorumOf(10); // tokenIds 1..10
        uint256 pid = _proposeBaseRateChange(address(uint160(0x10000 + 0)), 2_000_000);

        // 33% of 10 = 4 voters needed (forVotes + abstain) — give 6 FOR.
        for (uint256 i = 0; i < 6; ++i) {
            vm.prank(address(uint160(0x10000 + i)));
            gov.castVote(pid, 1);
        }

        // Roll past voting period
        vm.warp(block.timestamp + 4 days);
        assertEq(uint8(gov.state(pid)), uint8(Governance.State.Succeeded));

        gov.queue(pid);
        assertEq(uint8(gov.state(pid)), uint8(Governance.State.Queued));

        // Cannot execute before timelock
        vm.expectRevert(Governance.TimelockNotElapsed.selector);
        gov.execute(pid);

        // Wait for timelock
        vm.warp(block.timestamp + 73 hours);
        gov.execute(pid);

        assertEq(uint8(gov.state(pid)), uint8(Governance.State.Executed));
        assertEq(uint256(c.getMutable(K_KISHA_BASE)), 2_000_000);
    }

    function test_belowQuorum_defeated() public {
        _makeQuorumOf(10);
        uint256 pid = _proposeBaseRateChange(address(uint160(0x10000 + 0)), 2_000_000);

        // Only 2 voters (turnout=2) — quorum 33% of 10 = 4 required; should fail.
        for (uint256 i = 0; i < 2; ++i) {
            vm.prank(address(uint160(0x10000 + i)));
            gov.castVote(pid, 1);
        }

        vm.warp(block.timestamp + 4 days);
        assertEq(uint8(gov.state(pid)), uint8(Governance.State.Defeated));
    }

    function test_doubleVote_reverts() public {
        _makeQuorumOf(3);
        uint256 pid = _proposeBaseRateChange(address(uint160(0x10000 + 0)), 2_000_000);
        vm.prank(address(uint160(0x10000 + 0)));
        gov.castVote(pid, 1);
        vm.prank(address(uint160(0x10000 + 0)));
        vm.expectRevert(abi.encodeWithSelector(Governance.AlreadyVoted.selector, pid, uint256(1)));
        gov.castVote(pid, 1);
    }

    function test_cancel_byProposerBeforeQueue() public {
        _makeQuorumOf(3);
        uint256 pid = _proposeBaseRateChange(address(uint160(0x10000 + 0)), 2_000_000);
        vm.prank(address(uint160(0x10000 + 0)));
        gov.cancel(pid, keccak256("oops"));
        assertEq(uint8(gov.state(pid)), uint8(Governance.State.Canceled));
    }

    function test_expired_afterGracePeriod() public {
        _makeQuorumOf(10);
        uint256 pid = _proposeBaseRateChange(address(uint160(0x10000 + 0)), 2_000_000);
        for (uint256 i = 0; i < 6; ++i) {
            vm.prank(address(uint160(0x10000 + i)));
            gov.castVote(pid, 1);
        }
        vm.warp(block.timestamp + 4 days);
        gov.queue(pid);
        vm.warp(block.timestamp + 73 hours + 15 days);
        assertEq(uint8(gov.state(pid)), uint8(Governance.State.Expired));
    }
}
