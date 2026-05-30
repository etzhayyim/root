// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
pragma solidity ^0.8.26;

import {CreditLine} from "../src/CreditLine.sol";

interface Vm {
    function prank(address) external;
    function expectRevert(bytes4) external;
}

/// @title CreditLine invariants — interest-free (qard ḥasan) credit (ADR-2605302000)
contract CreditLineTest {
    Vm constant vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

    CreditLine credit;
    address council = address(0xC0);
    address router = address(0x4D);
    address wakaiFloat = address(0xFA);
    address holder = address(0x11);

    function setUp() public {
        credit = new CreditLine(wakaiFloat, council);
        vm.prank(council);
        credit.setRouter(router);
        vm.prank(council);
        credit.setLimit(holder, 1_000_000); // 1 USDC interest-free limit
    }

    // --- 0% invariant: drawing N raises outstanding by EXACTLY N (no accrual) ---
    function testDrawNoInterest() public {
        vm.prank(router);
        credit.draw(holder, 600_000);
        (, uint256 outstanding) = credit.lines(holder);
        require(outstanding == 600_000, "interest accrued; must be 0pct");
        require(credit.INTEREST_BPS() == 0, "interest bps must be 0");
        require(credit.LATE_FEE_BPS() == 0, "late fee bps must be 0");
        require(credit.available(holder) == 400_000, "available mismatch");
    }

    // --- repay reduces principal 1:1, no fee ---
    function testRepayNoFee() public {
        vm.prank(router);
        credit.draw(holder, 600_000);
        vm.prank(router);
        credit.repay(holder, 600_000);
        (, uint256 outstanding) = credit.lines(holder);
        require(outstanding == 0, "repay left residue (fee leaked)");
    }

    // --- cannot draw beyond limit ---
    function testOverLimitReverts() public {
        vm.prank(router);
        vm.expectRevert(CreditLine.OverLimit.selector);
        credit.draw(holder, 1_000_001);
    }

    // --- only router may draw ---
    function testDrawOnlyRouter() public {
        vm.prank(holder);
        vm.expectRevert(CreditLine.NotRouter.selector);
        credit.draw(holder, 1);
    }

    // --- repaying more than outstanding reverts (no negative balance, no fee credit) ---
    function testOverpayReverts() public {
        vm.prank(router);
        credit.draw(holder, 500_000);
        vm.prank(router);
        vm.expectRevert(CreditLine.Overpay.selector);
        credit.repay(holder, 500_001);
    }

    // --- multiple draws accumulate against the same 0% line ---
    function testMultipleDrawsAccumulate() public {
        vm.prank(router);
        credit.draw(holder, 300_000);
        vm.prank(router);
        credit.draw(holder, 200_000);
        (, uint256 outstanding) = credit.lines(holder);
        require(outstanding == 500_000, "draws must accumulate");
        require(credit.available(holder) == 500_000, "available mismatch");
    }

    // --- repaying frees the line for reuse up to the full limit (still 0%) ---
    function testLineReusableAfterRepay() public {
        vm.prank(router);
        credit.draw(holder, 600_000);
        vm.prank(router);
        credit.repay(holder, 600_000);
        vm.prank(router);
        credit.draw(holder, 1_000_000); // full limit again, 0%
        require(credit.available(holder) == 0, "line not reusable after repay");
    }

    // --- only the router may repay ---
    function testRepayOnlyRouter() public {
        vm.prank(holder);
        vm.expectRevert(CreditLine.NotRouter.selector);
        credit.repay(holder, 1);
    }

    // --- only council may set limits ---
    function testSetLimitOnlyCouncil() public {
        vm.prank(holder);
        vm.expectRevert(CreditLine.NotCouncil.selector);
        credit.setLimit(holder, 5);
    }
}
