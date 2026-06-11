// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {CohortLifecycle} from "../src/CohortLifecycle.sol";

contract CohortLifecycleTest is Test {
    CohortLifecycle internal lifecycle;
    address internal council = makeAddr("council");
    address internal stranger = makeAddr("stranger");

    bytes32 internal slugA = keccak256(bytes("yobel-cycle-5786"));
    bytes32 internal slugB = keccak256(bytes("cohort-fission-2"));
    bytes32 internal slugC = keccak256(bytes("cohort-fission-3"));

    function setUp() public {
        lifecycle = new CohortLifecycle(council);
    }

    function test_constructor() public view {
        assertEq(lifecycle.owner(), council);
    }

    function test_startGenesis_happyPath() public {
        vm.prank(council);
        bytes32 cohortId = lifecycle.startGenesis(slugA);
        CohortLifecycle.Cohort memory c = lifecycle.getCohort(cohortId);
        assertEq(uint256(c.status), uint256(CohortLifecycle.Status.Genesis));
        assertEq(c.slugHash, slugA);
        assertEq(lifecycle.resolveSlug(slugA), cohortId);
    }

    function test_startGenesis_revertsSlugTaken() public {
        vm.prank(council);
        lifecycle.startGenesis(slugA);
        vm.prank(council);
        vm.expectRevert(CohortLifecycle.SlugTaken.selector);
        lifecycle.startGenesis(slugA);
    }

    function test_activate_happyPath() public {
        vm.prank(council);
        bytes32 cohortId = lifecycle.startGenesis(slugA);
        vm.prank(council);
        lifecycle.activate(cohortId);
        assertEq(uint256(lifecycle.getCohort(cohortId).status), uint256(CohortLifecycle.Status.Active));
    }

    function test_activate_revertsBadStatus() public {
        vm.prank(council);
        bytes32 cohortId = lifecycle.startGenesis(slugA);
        vm.prank(council);
        lifecycle.activate(cohortId);
        // Trying to activate an already-Active cohort fails.
        vm.prank(council);
        vm.expectRevert();
        lifecycle.activate(cohortId);
    }

    function test_fission_happyPath() public {
        vm.prank(council);
        bytes32 parent = lifecycle.startGenesis(slugA);
        vm.prank(council);
        lifecycle.activate(parent);

        bytes32[] memory childSlugs = new bytes32[](2);
        childSlugs[0] = slugB;
        childSlugs[1] = slugC;
        vm.prank(council);
        bytes32[] memory children = lifecycle.fission(parent, childSlugs);

        assertEq(children.length, 2);
        assertEq(uint256(lifecycle.getCohort(parent).status), uint256(CohortLifecycle.Status.Fissioned));
        assertEq(uint256(lifecycle.getCohort(children[0]).status), uint256(CohortLifecycle.Status.Genesis));
        assertEq(lifecycle.fissionParent(children[0]), parent);
        assertEq(lifecycle.getFissionChildren(parent).length, 2);
    }

    function test_fission_revertsParentNotActive() public {
        vm.prank(council);
        bytes32 parent = lifecycle.startGenesis(slugA);
        bytes32[] memory childSlugs = new bytes32[](1);
        childSlugs[0] = slugB;
        vm.prank(council);
        vm.expectRevert();
        lifecycle.fission(parent, childSlugs);
    }

    function test_decommission_fromActive() public {
        vm.prank(council);
        bytes32 cohortId = lifecycle.startGenesis(slugA);
        vm.prank(council);
        lifecycle.activate(cohortId);
        vm.prank(council);
        lifecycle.decommission(cohortId, keccak256("disbanded"));
        assertEq(uint256(lifecycle.getCohort(cohortId).status), uint256(CohortLifecycle.Status.Decommissioned));
        assertEq(lifecycle.getCohort(cohortId).reasonHash, keccak256("disbanded"));
    }

    function test_decommission_fromGenesis() public {
        vm.prank(council);
        bytes32 cohortId = lifecycle.startGenesis(slugA);
        vm.prank(council);
        lifecycle.decommission(cohortId, keccak256("rejected"));
        assertEq(uint256(lifecycle.getCohort(cohortId).status), uint256(CohortLifecycle.Status.Decommissioned));
    }

    function test_resume_fromDecommissioned() public {
        vm.prank(council);
        bytes32 cohortId = lifecycle.startGenesis(slugA);
        vm.prank(council);
        lifecycle.activate(cohortId);
        vm.prank(council);
        lifecycle.decommission(cohortId, keccak256("disbanded"));

        vm.prank(council);
        lifecycle.resume(cohortId);
        assertEq(uint256(lifecycle.getCohort(cohortId).status), uint256(CohortLifecycle.Status.Resumed));

        vm.prank(council);
        lifecycle.activate(cohortId);
        assertEq(uint256(lifecycle.getCohort(cohortId).status), uint256(CohortLifecycle.Status.Active));
    }

    function test_resume_revertsFromGenesis() public {
        vm.prank(council);
        bytes32 cohortId = lifecycle.startGenesis(slugA);
        vm.prank(council);
        vm.expectRevert();
        lifecycle.resume(cohortId);
    }

    function test_onlyOwner_modifiers() public {
        vm.startPrank(stranger);
        vm.expectRevert(CohortLifecycle.NotOwner.selector);
        lifecycle.startGenesis(slugA);

        vm.expectRevert(CohortLifecycle.NotOwner.selector);
        lifecycle.activate(bytes32(0));

        bytes32[] memory childSlugs = new bytes32[](1);
        childSlugs[0] = slugB;
        vm.expectRevert(CohortLifecycle.NotOwner.selector);
        lifecycle.fission(bytes32(0), childSlugs);

        vm.expectRevert(CohortLifecycle.NotOwner.selector);
        lifecycle.decommission(bytes32(0), bytes32(0));

        vm.expectRevert(CohortLifecycle.NotOwner.selector);
        lifecycle.resume(bytes32(0));
        vm.stopPrank();
    }
}
