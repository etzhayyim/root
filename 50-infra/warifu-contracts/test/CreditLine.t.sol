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
        require(outstanding == 600_000, "interest accrued — must be 0%");
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
        vm.expectRevert(CreditLine.OverLimit.selector);
        vm.prank(router);
        credit.draw(holder, 1_000_001);
    }

    // --- only router may draw ---
    function testDrawOnlyRouter() public {
        vm.expectRevert(CreditLine.NotRouter.selector);
        vm.prank(holder);
        credit.draw(holder, 1);
    }
}
