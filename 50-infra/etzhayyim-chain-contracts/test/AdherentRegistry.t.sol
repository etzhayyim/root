// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {AdherentRegistry} from "../src/AdherentRegistry.sol";

contract AdherentRegistryTest is Test {
    AdherentRegistry r;

    address constant OFFICER = address(0xA11CE);
    address constant ALICE   = address(0xBEEF);
    address constant BOB     = address(0xC0DE);

    bytes32 constant EVT_PRAYER = keccak256("prayer");

    function setUp() public {
        address[] memory officers = new address[](1);
        officers[0] = OFFICER;
        r = new AdherentRegistry(officers);
    }

    function test_join_mintsMonotonically() public {
        vm.startPrank(OFFICER);
        uint256 t1 = r.join(ALICE, "did:web:alice.example.com", bytes32(uint256(1)));
        uint256 t2 = r.join(BOB,   "did:web:bob.example.com",   bytes32(uint256(2)));
        assertEq(t1, 1);
        assertEq(t2, 2);
        assertEq(r.totalMinted(), 2);
        vm.stopPrank();
    }

    function test_join_rejectsDuplicateDid() public {
        vm.startPrank(OFFICER);
        r.join(ALICE, "did:web:alice.example.com", bytes32(uint256(1)));
        vm.expectRevert(abi.encodeWithSelector(AdherentRegistry.AlreadyJoined.selector, "did:web:alice.example.com"));
        r.join(BOB, "did:web:alice.example.com", bytes32(uint256(2)));
        vm.stopPrank();
    }

    function test_join_rejectsDuplicateWallet() public {
        vm.startPrank(OFFICER);
        r.join(ALICE, "did:web:alice.example.com", bytes32(uint256(1)));
        vm.expectRevert(bytes("wallet already bound"));
        r.join(ALICE, "did:web:alice2.example.com", bytes32(uint256(2)));
        vm.stopPrank();
    }

    function test_join_onlyOfficer() public {
        vm.expectRevert(AdherentRegistry.NotOfficer.selector);
        r.join(ALICE, "did:web:alice.example.com", bytes32(uint256(1)));
    }

    function test_transferFrom_revertsSoulbound() public {
        vm.prank(OFFICER);
        r.join(ALICE, "did:web:alice.example.com", bytes32(uint256(1)));
        vm.expectRevert(AdherentRegistry.Soulbound.selector);
        r.transferFrom(ALICE, BOB, 1);
    }

    function test_locked_alwaysTrue() public {
        vm.prank(OFFICER);
        r.join(ALICE, "did:web:alice.example.com", bytes32(uint256(1)));
        assertTrue(r.locked(1));
    }

    function test_attest_byHolder_setsActive() public {
        vm.prank(OFFICER);
        r.join(ALICE, "did:web:alice.example.com", bytes32(uint256(1)));
        // Not active yet (never attested).
        assertFalse(r.isActive(1, 30 days));
        vm.prank(ALICE);
        r.attest(1, EVT_PRAYER, bytes32(0));
        assertTrue(r.isActive(1, 30 days));
    }

    function test_attest_byOfficer_okAsRelay() public {
        vm.startPrank(OFFICER);
        r.join(ALICE, "did:web:alice.example.com", bytes32(uint256(1)));
        r.attest(1, EVT_PRAYER, bytes32(0));
        vm.stopPrank();
        assertTrue(r.isActive(1, 30 days));
    }

    function test_attest_byStranger_reverts() public {
        vm.prank(OFFICER);
        r.join(ALICE, "did:web:alice.example.com", bytes32(uint256(1)));
        vm.prank(BOB);
        vm.expectRevert(bytes("not adherent or officer"));
        r.attest(1, EVT_PRAYER, bytes32(0));
    }

    function test_revoke_blocksAttest() public {
        vm.startPrank(OFFICER);
        r.join(ALICE, "did:web:alice.example.com", bytes32(uint256(1)));
        r.revoke(1, bytes32(uint256(0xDEAD)));
        vm.stopPrank();
        vm.prank(ALICE);
        vm.expectRevert(abi.encodeWithSelector(AdherentRegistry.TokenRevoked.selector, 1));
        r.attest(1, EVT_PRAYER, bytes32(0));
    }

    function test_isActive_decaysOutsideWindow() public {
        vm.startPrank(OFFICER);
        r.join(ALICE, "did:web:alice.example.com", bytes32(uint256(1)));
        r.attest(1, EVT_PRAYER, bytes32(0));
        vm.stopPrank();
        assertTrue(r.isActive(1, 30 days));
        vm.warp(block.timestamp + 31 days);
        assertFalse(r.isActive(1, 30 days));
    }
}
