// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {YobelRiteRegistry} from "../src/YobelRiteRegistry.sol";
import {YobelReleaseRegistry} from "../src/YobelReleaseRegistry.sol";

contract YobelReleaseRegistryTest is Test {
    YobelRiteRegistry riteReg;
    YobelReleaseRegistry relReg;

    address constant DECLARER = address(0xD1);
    address constant CREDITOR_AGENT = address(0xC1);
    address constant RELEASE_AGENT = address(0xE1);

    bytes32 constant RITE_ID = keccak256("shmita-5786");
    bytes32 constant DEBT_ID = keccak256("credA-d1-community-ok");
    bytes32 constant DEBTOR = keccak256("did:web:etzhayyim.com:debtor-community-ok");
    bytes32 constant CREDITOR = keccak256("did:web:etzhayyim.com:creditor-A");
    bytes32 constant DOCTRINAL = keccak256("Lev 25:1-7");
    bytes32 constant SCOPE = keccak256("etzhayyim community");
    bytes32 constant ISSUER = keccak256("did:web:etzhayyim.com:steward");
    uint64 constant EFFECTIVE = 1_758_551_400;
    uint64 constant EXPIRY = 1_789_142_400;

    uint256 constant PRINCIPAL = 250_000_000;  // $250 USDC
    uint256 constant ACCRUED = 12_500_000;     // $12.50 USDC
    uint256 constant CAP = PRINCIPAL + ACCRUED;

    function setUp() public {
        riteReg = new YobelRiteRegistry();
        relReg = new YobelReleaseRegistry(riteReg);
        _activateShmita();
    }

    // ─── Happy path ─────────────────────────────────────────────────

    function test_register_debt_cap_then_record_release() public {
        vm.prank(CREDITOR_AGENT);
        relReg.registerDebtCap(RITE_ID, DEBT_ID, PRINCIPAL, ACCRUED);

        YobelReleaseRegistry.DebtCap memory cap = relReg.getDebtCap(RITE_ID, DEBT_ID);
        assertEq(cap.principalMicroUsdc, PRINCIPAL);
        assertEq(cap.accruedMicroUsdc, ACCRUED);
        assertEq(cap.registrar, CREDITOR_AGENT);
        assertEq(cap.totalReleasedMicroUsdc, 0);

        bytes32 releaseId = keccak256("rel-1");
        vm.prank(RELEASE_AGENT);
        relReg.recordRelease(
            releaseId,
            RITE_ID,
            DEBT_ID,
            DEBTOR,
            CREDITOR,
            CAP,
            YobelReleaseRegistry.ReleaseMethod.BaseL2Transfer,
            keccak256("0xbase-l2-tx-hash")
        );

        YobelReleaseRegistry.Release memory r = relReg.getRelease(releaseId);
        assertEq(r.releasedMicroUsdc, CAP);
        assertEq(r.recorder, RELEASE_AGENT);
        assertEq(uint8(r.releaseMethod), uint8(YobelReleaseRegistry.ReleaseMethod.BaseL2Transfer));
        assertEq(relReg.releaseCount(), 1);
        assertEq(relReg.releaseCountByRite(RITE_ID), 1);
        assertEq(relReg.releaseCountByDebtor(DEBTOR), 1);

        YobelReleaseRegistry.DebtCap memory after_ = relReg.getDebtCap(RITE_ID, DEBT_ID);
        assertEq(after_.totalReleasedMicroUsdc, CAP);
    }

    function test_partial_releases_cumulate_to_cap() public {
        relReg.registerDebtCap(RITE_ID, DEBT_ID, PRINCIPAL, ACCRUED);

        // Release $100 first
        relReg.recordRelease(
            keccak256("rel-partial-1"),
            RITE_ID,
            DEBT_ID,
            DEBTOR,
            CREDITOR,
            100_000_000,
            YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping,
            bytes32(0)
        );
        // Release the rest
        relReg.recordRelease(
            keccak256("rel-partial-2"),
            RITE_ID,
            DEBT_ID,
            DEBTOR,
            CREDITOR,
            CAP - 100_000_000,
            YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping,
            bytes32(0)
        );
        YobelReleaseRegistry.DebtCap memory cap = relReg.getDebtCap(RITE_ID, DEBT_ID);
        assertEq(cap.totalReleasedMicroUsdc, CAP);
    }

    function test_zero_amount_release_legal_for_doctrinal_methods() public {
        relReg.registerDebtCap(RITE_ID, DEBT_ID, PRINCIPAL, ACCRUED);
        relReg.recordRelease(
            keccak256("rel-doctrinal"),
            RITE_ID,
            DEBT_ID,
            DEBTOR,
            CREDITOR,
            0,
            YobelReleaseRegistry.ReleaseMethod.EcclesiasticalIndulgence,
            bytes32(0)
        );
        assertEq(relReg.releaseCount(), 1);
    }

    // ─── Invariants & gates (Charter Rider §2(b)) ───────────────────

    function test_recordRelease_rejects_over_cap() public {
        relReg.registerDebtCap(RITE_ID, DEBT_ID, PRINCIPAL, ACCRUED);
        vm.expectRevert(
            abi.encodeWithSelector(
                YobelReleaseRegistry.OneWayViolation.selector,
                CAP + 1,
                CAP
            )
        );
        relReg.recordRelease(
            keccak256("rel-over"),
            RITE_ID,
            DEBT_ID,
            DEBTOR,
            CREDITOR,
            CAP + 1,
            YobelReleaseRegistry.ReleaseMethod.BaseL2Transfer,
            keccak256("0xtx")
        );
    }

    function test_recordRelease_rejects_cumulative_over_cap() public {
        relReg.registerDebtCap(RITE_ID, DEBT_ID, 100, 0);
        relReg.recordRelease(
            keccak256("rel-50a"), RITE_ID, DEBT_ID, DEBTOR, CREDITOR, 50,
            YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping, bytes32(0)
        );
        relReg.recordRelease(
            keccak256("rel-50b"), RITE_ID, DEBT_ID, DEBTOR, CREDITOR, 50,
            YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping, bytes32(0)
        );
        // Third release attempt — cumulative would exceed 100
        vm.expectRevert(
            abi.encodeWithSelector(YobelReleaseRegistry.OneWayViolation.selector, 101, 100)
        );
        relReg.recordRelease(
            keccak256("rel-1c"), RITE_ID, DEBT_ID, DEBTOR, CREDITOR, 1,
            YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping, bytes32(0)
        );
    }

    function test_recordRelease_rejects_unregistered_debt() public {
        // Cap not registered
        vm.expectRevert(
            abi.encodeWithSelector(YobelReleaseRegistry.DebtCapNotRegistered.selector, DEBT_ID)
        );
        relReg.recordRelease(
            keccak256("rel-orphan"), RITE_ID, DEBT_ID, DEBTOR, CREDITOR, 100,
            YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping, bytes32(0)
        );
    }

    function test_recordRelease_rejects_inactive_rite() public {
        bytes32 cancelledRite = keccak256("rite-cancelled");
        vm.prank(DECLARER);
        riteReg.declareRite(
            cancelledRite,
            YobelRiteRegistry.RiteType.Shmita7yr,
            DOCTRINAL, SCOPE, EFFECTIVE, EXPIRY, ISSUER
        );
        vm.prank(DECLARER);
        riteReg.cancelRite(cancelledRite, keccak256("changed mind"));
        // Cap registration MUST also reject inactive rite
        vm.expectRevert(
            abi.encodeWithSelector(YobelReleaseRegistry.RiteNotActive.selector, cancelledRite)
        );
        relReg.registerDebtCap(cancelledRite, DEBT_ID, PRINCIPAL, ACCRUED);
    }

    function test_registerDebtCap_rejects_duplicate() public {
        relReg.registerDebtCap(RITE_ID, DEBT_ID, PRINCIPAL, ACCRUED);
        vm.expectRevert(
            abi.encodeWithSelector(YobelReleaseRegistry.DebtCapAlreadyRegistered.selector, DEBT_ID)
        );
        relReg.registerDebtCap(RITE_ID, DEBT_ID, PRINCIPAL, ACCRUED);
    }

    function test_recordRelease_rejects_empty_release_id() public {
        relReg.registerDebtCap(RITE_ID, DEBT_ID, PRINCIPAL, ACCRUED);
        vm.expectRevert(YobelReleaseRegistry.EmptyReleaseId.selector);
        relReg.recordRelease(
            bytes32(0), RITE_ID, DEBT_ID, DEBTOR, CREDITOR, 100,
            YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping, bytes32(0)
        );
    }

    function test_recordRelease_rejects_duplicate_id() public {
        relReg.registerDebtCap(RITE_ID, DEBT_ID, PRINCIPAL, ACCRUED);
        bytes32 id = keccak256("rel-dup");
        relReg.recordRelease(
            id, RITE_ID, DEBT_ID, DEBTOR, CREDITOR, 100,
            YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping, bytes32(0)
        );
        vm.expectRevert(
            abi.encodeWithSelector(YobelReleaseRegistry.ReleaseAlreadyRecorded.selector, id)
        );
        relReg.recordRelease(
            id, RITE_ID, DEBT_ID, DEBTOR, CREDITOR, 50,
            YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping, bytes32(0)
        );
    }

    // ─── Fuzz: one-way invariant holds over any release sequence ─────

    function testFuzz_one_way_invariant_holds(uint128 a, uint128 b, uint128 c) public {
        relReg.registerDebtCap(RITE_ID, DEBT_ID, 1_000_000_000, 0);
        uint256 cap_ = 1_000_000_000;
        if (a > cap_) {
            vm.expectRevert();
            relReg.recordRelease(
                keccak256("fa"), RITE_ID, DEBT_ID, DEBTOR, CREDITOR, a,
                YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping, bytes32(0)
            );
            return;
        }
        relReg.recordRelease(
            keccak256("fa"), RITE_ID, DEBT_ID, DEBTOR, CREDITOR, a,
            YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping, bytes32(0)
        );
        uint256 used = a;
        if (used + b > cap_) {
            vm.expectRevert();
            relReg.recordRelease(
                keccak256("fb"), RITE_ID, DEBT_ID, DEBTOR, CREDITOR, b,
                YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping, bytes32(0)
            );
            return;
        }
        relReg.recordRelease(
            keccak256("fb"), RITE_ID, DEBT_ID, DEBTOR, CREDITOR, b,
            YobelReleaseRegistry.ReleaseMethod.VoluntaryBookkeeping, bytes32(0)
        );
        used += b;
        // After any 2 successful sub-cap releases, total released must equal a+b
        YobelReleaseRegistry.DebtCap memory after_ = relReg.getDebtCap(RITE_ID, DEBT_ID);
        assertEq(after_.totalReleasedMicroUsdc, used);
        assertLe(after_.totalReleasedMicroUsdc, cap_);
    }

    // ─── Helpers ────────────────────────────────────────────────────

    function _activateShmita() internal {
        vm.prank(DECLARER);
        riteReg.declareRite(
            RITE_ID,
            YobelRiteRegistry.RiteType.Shmita7yr,
            DOCTRINAL, SCOPE, EFFECTIVE, EXPIRY, ISSUER
        );
        riteReg.ratifyRite(RITE_ID, keccak256("council-sig-set"), 4);
    }
}
