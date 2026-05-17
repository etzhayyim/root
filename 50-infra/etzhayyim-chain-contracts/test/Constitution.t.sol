// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {Constitution} from "../src/Constitution.sol";

contract ConstitutionTest is Test {
    Constitution c;

    bytes32 constant K_ONE_SBT_ONE_VOTE   = keccak256("one_sbt_one_vote");
    bytes32 constant K_PHENOTYPE_MIN      = keccak256("phenotype_min_bps");
    bytes32 constant K_PHENOTYPE_MAX      = keccak256("phenotype_max_bps");
    bytes32 constant K_KISHA_BASE         = keccak256("kisha_base_rate");
    bytes32 constant K_KAPPA              = keccak256("kappa_bps");
    bytes32 constant K_QUORUM             = keccak256("quorum_bps");
    bytes32 constant K_ACTIVE_WINDOW      = keccak256("active_window_secs");
    bytes32 constant K_TIMELOCK           = keccak256("timelock_secs");
    bytes32 constant K_KAPPA_FLOOR        = keccak256("kappa_floor_bps");
    bytes32 constant K_KAPPA_CEILING      = keccak256("kappa_ceiling_bps");
    bytes32 constant K_QUORUM_FLOOR       = keccak256("quorum_floor_bps");

    address constant GOV    = address(0xA11CE);
    address constant ALICE  = address(0xBEEF);

    function setUp() public {
        bytes32[] memory cKeys = new bytes32[](6);
        bytes32[] memory cVals = new bytes32[](6);
        cKeys[0] = K_ONE_SBT_ONE_VOTE;     cVals[0] = bytes32(uint256(1));
        cKeys[1] = K_PHENOTYPE_MIN;         cVals[1] = bytes32(uint256(5_000));
        cKeys[2] = K_PHENOTYPE_MAX;         cVals[2] = bytes32(uint256(20_000));
        cKeys[3] = K_KAPPA_FLOOR;           cVals[3] = bytes32(uint256(100));
        cKeys[4] = K_KAPPA_CEILING;         cVals[4] = bytes32(uint256(500));
        cKeys[5] = K_QUORUM_FLOOR;          cVals[5] = bytes32(uint256(2_000));

        bytes32[] memory mKeys = new bytes32[](5);
        bytes32[] memory mVals = new bytes32[](5);
        mKeys[0] = K_KISHA_BASE;     mVals[0] = bytes32(uint256(1_000_000));   // 1 USDC/day
        mKeys[1] = K_KAPPA;           mVals[1] = bytes32(uint256(300));
        mKeys[2] = K_QUORUM;          mVals[2] = bytes32(uint256(3_300));
        mKeys[3] = K_ACTIVE_WINDOW;   mVals[3] = bytes32(uint256(30 days));
        mKeys[4] = K_TIMELOCK;        mVals[4] = bytes32(uint256(72 hours));

        c = new Constitution(cKeys, cVals, mKeys, mVals);
    }

    function test_constants_set() public view {
        assertEq(c.getConstant(K_ONE_SBT_ONE_VOTE), bytes32(uint256(1)));
        assertEq(c.getConstant(K_PHENOTYPE_MIN), bytes32(uint256(5_000)));
        assertEq(c.getConstant(K_PHENOTYPE_MAX), bytes32(uint256(20_000)));
        assertTrue(c.isConstant(K_KAPPA_FLOOR));
    }

    function test_unknownConstant_reverts() public {
        vm.expectRevert(abi.encodeWithSelector(Constitution.UnknownConstant.selector, keccak256("nope")));
        c.getConstant(keccak256("nope"));
    }

    function test_mutables_initial() public view {
        assertEq(c.getMutable(K_KISHA_BASE), bytes32(uint256(1_000_000)));
        assertEq(c.getMutable(K_KAPPA),       bytes32(uint256(300)));
    }

    function test_bindGovernance_oneShot() public {
        c.bindGovernance(GOV);
        assertEq(c.governance(), GOV);
        vm.expectRevert(Constitution.GovernanceAlreadyBound.selector);
        c.bindGovernance(ALICE);
    }

    function test_setMutable_onlyGovernance() public {
        c.bindGovernance(GOV);
        vm.expectRevert(Constitution.NotGovernance.selector);
        c.setMutable(K_KAPPA, bytes32(uint256(400)));
    }

    function test_setMutable_succeeds_fromGovernance() public {
        c.bindGovernance(GOV);
        vm.prank(GOV);
        c.setMutable(K_KAPPA, bytes32(uint256(400)));
        assertEq(c.getMutable(K_KAPPA), bytes32(uint256(400)));
    }

    function test_setMutable_refusesConstantKey() public {
        c.bindGovernance(GOV);
        vm.prank(GOV);
        vm.expectRevert(abi.encodeWithSelector(Constitution.ImmutableKey.selector, K_PHENOTYPE_MIN));
        c.setMutable(K_PHENOTYPE_MIN, bytes32(uint256(9_999)));
    }
}
