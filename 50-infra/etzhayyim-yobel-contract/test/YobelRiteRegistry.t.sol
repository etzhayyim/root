// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {YobelRiteRegistry} from "../src/YobelRiteRegistry.sol";

contract YobelRiteRegistryTest is Test {
    YobelRiteRegistry reg;

    address constant DECLARER = address(0xD1);
    address constant ANYONE = address(0xA1);

    bytes32 constant RITE_ID = keccak256("shmita-5786");
    bytes32 constant DOCTRINAL = keccak256("Lev 25:1-7 / Deut 15:1-2");
    bytes32 constant SCOPE = keccak256("etzhayyim community small monetary debts");
    bytes32 constant ISSUER = keccak256("did:web:etzhayyim.com:steward-shmita-5786");
    uint64 constant EFFECTIVE = 1_758_551_400;  // 2025-09-22T18:00:00Z
    uint64 constant EXPIRY = 1_789_142_400;     // 2026-09-11T18:00:00Z

    function setUp() public {
        reg = new YobelRiteRegistry();
    }

    // ─── Happy path ─────────────────────────────────────────────────

    function test_declareRite_creates_record() public {
        vm.prank(DECLARER);
        reg.declareRite(
            RITE_ID,
            YobelRiteRegistry.RiteType.Shmita7yr,
            DOCTRINAL,
            SCOPE,
            EFFECTIVE,
            EXPIRY,
            ISSUER
        );
        YobelRiteRegistry.Rite memory r = reg.getRite(RITE_ID);
        assertEq(uint8(r.status), uint8(YobelRiteRegistry.Status.Declared));
        assertEq(r.declarer, DECLARER);
        assertEq(r.doctrinalBasisHash, DOCTRINAL);
        assertEq(r.ratifierCount, 0);
        assertEq(reg.riteCount(), 1);
    }

    function test_ratifyRite_transitions_to_active() public {
        _declareShmita();
        bytes32 ratHash = keccak256("council-sig-set-canonical-hash");
        vm.prank(ANYONE);
        reg.ratifyRite(RITE_ID, ratHash, 5);
        YobelRiteRegistry.Rite memory r = reg.getRite(RITE_ID);
        assertEq(uint8(r.status), uint8(YobelRiteRegistry.Status.Active));
        assertEq(r.ratificationHash, ratHash);
        assertEq(r.ratifierCount, 5);
        assertTrue(reg.isActive(RITE_ID));
    }

    function test_completeRite_after_expiry() public {
        _declareShmita();
        reg.ratifyRite(RITE_ID, keccak256("rat"), 4);
        vm.warp(EXPIRY + 1);
        reg.completeRite(RITE_ID);
        YobelRiteRegistry.Rite memory r = reg.getRite(RITE_ID);
        assertEq(uint8(r.status), uint8(YobelRiteRegistry.Status.Completed));
    }

    function test_cancelRite_by_declarer_before_ratification() public {
        _declareShmita();
        vm.prank(DECLARER);
        reg.cancelRite(RITE_ID, keccak256("declarer withdrew"));
        YobelRiteRegistry.Rite memory r = reg.getRite(RITE_ID);
        assertEq(uint8(r.status), uint8(YobelRiteRegistry.Status.Cancelled));
    }

    function test_supersedeRite_marks_status_and_link() public {
        _declareShmita();
        reg.ratifyRite(RITE_ID, keccak256("rat"), 4);
        bytes32 newer = keccak256("shmita-5786-corrected");
        reg.supersedeRite(RITE_ID, newer, keccak256("audit-tampering-detected"));
        YobelRiteRegistry.Rite memory r = reg.getRite(RITE_ID);
        assertEq(uint8(r.status), uint8(YobelRiteRegistry.Status.Superseded));
        assertEq(r.supersededByRiteId, newer);
    }

    // ─── Invariants & gates ─────────────────────────────────────────

    function test_declareRite_rejects_duplicate() public {
        _declareShmita();
        vm.expectRevert(abi.encodeWithSelector(YobelRiteRegistry.RiteAlreadyExists.selector, RITE_ID));
        reg.declareRite(RITE_ID, YobelRiteRegistry.RiteType.Shmita7yr, DOCTRINAL, SCOPE, EFFECTIVE, EXPIRY, ISSUER);
    }

    function test_declareRite_rejects_empty_doctrinal_basis() public {
        vm.expectRevert(YobelRiteRegistry.EmptyDoctrinalBasisHash.selector);
        reg.declareRite(RITE_ID, YobelRiteRegistry.RiteType.Shmita7yr, bytes32(0), SCOPE, EFFECTIVE, EXPIRY, ISSUER);
    }

    function test_declareRite_rejects_expiry_before_effective() public {
        vm.expectRevert(
            abi.encodeWithSelector(
                YobelRiteRegistry.ExpiryBeforeEffective.selector, EFFECTIVE, EFFECTIVE - 1
            )
        );
        reg.declareRite(
            RITE_ID, YobelRiteRegistry.RiteType.Shmita7yr, DOCTRINAL, SCOPE, EFFECTIVE, EFFECTIVE - 1, ISSUER
        );
    }

    function test_declareRite_accepts_perpetual_expiry_zero() public {
        reg.declareRite(RITE_ID, YobelRiteRegistry.RiteType.PoliticalAmnesty, DOCTRINAL, SCOPE, EFFECTIVE, 0, ISSUER);
        YobelRiteRegistry.Rite memory r = reg.getRite(RITE_ID);
        assertEq(r.expiryDate, 0);
    }

    function test_ratifyRite_rejects_below_floor() public {
        _declareShmita();
        vm.expectRevert(
            abi.encodeWithSelector(YobelRiteRegistry.RatifierCountTooLow.selector, 3, 4)
        );
        reg.ratifyRite(RITE_ID, keccak256("rat"), 3);
    }

    function test_ratifyRite_rejects_empty_hash() public {
        _declareShmita();
        vm.expectRevert(YobelRiteRegistry.EmptyRatificationHash.selector);
        reg.ratifyRite(RITE_ID, bytes32(0), 4);
    }

    function test_ratifyRite_rejects_non_declared_status() public {
        _declareShmita();
        reg.ratifyRite(RITE_ID, keccak256("rat"), 4);
        vm.expectRevert(
            abi.encodeWithSelector(
                YobelRiteRegistry.InvalidStatusTransition.selector,
                RITE_ID,
                YobelRiteRegistry.Status.Active,
                YobelRiteRegistry.Status.Active
            )
        );
        reg.ratifyRite(RITE_ID, keccak256("rat2"), 4);
    }

    function test_completeRite_rejects_before_expiry() public {
        _declareShmita();
        reg.ratifyRite(RITE_ID, keccak256("rat"), 4);
        vm.warp(EXPIRY - 1);
        vm.expectRevert(
            abi.encodeWithSelector(YobelRiteRegistry.ExpiryNotReached.selector, EXPIRY, EXPIRY - 1)
        );
        reg.completeRite(RITE_ID);
    }

    function test_completeRite_rejects_perpetual() public {
        reg.declareRite(RITE_ID, YobelRiteRegistry.RiteType.PoliticalAmnesty, DOCTRINAL, SCOPE, EFFECTIVE, 0, ISSUER);
        reg.ratifyRite(RITE_ID, keccak256("rat"), 4);
        vm.expectRevert(
            abi.encodeWithSelector(YobelRiteRegistry.ExpiryNotReached.selector, 0, block.timestamp)
        );
        reg.completeRite(RITE_ID);
    }

    function test_cancelRite_only_by_declarer() public {
        _declareShmita();
        vm.prank(ANYONE);
        vm.expectRevert(
            abi.encodeWithSelector(YobelRiteRegistry.NotDeclarer.selector, ANYONE, DECLARER)
        );
        reg.cancelRite(RITE_ID, keccak256("forbidden"));
    }

    function test_supersedeRite_rejects_non_active() public {
        _declareShmita();
        // Status is Declared, not Active
        vm.expectRevert(
            abi.encodeWithSelector(
                YobelRiteRegistry.InvalidStatusTransition.selector,
                RITE_ID,
                YobelRiteRegistry.Status.Declared,
                YobelRiteRegistry.Status.Superseded
            )
        );
        reg.supersedeRite(RITE_ID, keccak256("newer"), keccak256("reason"));
    }

    // ─── Multi-rite enumeration ─────────────────────────────────────

    function test_multiple_rites_enumerable() public {
        _declareShmita();
        reg.declareRite(
            keccak256("yobel-2074"),
            YobelRiteRegistry.RiteType.Yobel50yr,
            DOCTRINAL,
            SCOPE,
            EFFECTIVE,
            EXPIRY,
            ISSUER
        );
        assertEq(reg.riteCount(), 2);
    }

    // ─── Helpers ────────────────────────────────────────────────────

    function _declareShmita() internal {
        vm.prank(DECLARER);
        reg.declareRite(
            RITE_ID,
            YobelRiteRegistry.RiteType.Shmita7yr,
            DOCTRINAL,
            SCOPE,
            EFFECTIVE,
            EXPIRY,
            ISSUER
        );
    }
}
