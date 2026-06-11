// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
pragma solidity ^0.8.26;

import {SettlementRouter} from "../src/SettlementRouter.sol";
import {CreditLine} from "../src/CreditLine.sol";

interface Vm {
    function prank(address) external;
    function expectRevert(bytes4) external;
    function expectRevert() external; // generic: matches any revert (incl. arithmetic panic)
}

/// Minimal mock USDC whose transferFrom reverts on insufficient allowance/balance (underflow).
contract MockUSDC {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address to, uint256 a) external { balanceOf[to] += a; }
    function approve(address s, uint256 a) external returns (bool) { allowance[msg.sender][s] = a; return true; }

    function transferFrom(address f, address t, uint256 a) external returns (bool) {
        allowance[f][msg.sender] -= a; // reverts (panic 0x11) if not approved for >= a
        balanceOf[f] -= a;             // reverts if balance < a
        balanceOf[t] += a;
        return true;
    }
}

/// @title SettlementRouter failure-path coverage (ADR-2605302000)
contract SettlementRouterEdgeTest {
    Vm constant vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

    MockUSDC usdc;
    CreditLine credit;
    SettlementRouter router;
    address council = address(0xC0);
    address holder = address(0x11);
    address merchant = address(0x3E);
    address wakaiFloat = address(0xFA);

    function setUp() public {
        usdc = new MockUSDC();
        credit = new CreditLine(wakaiFloat, council);
        router = new SettlementRouter(address(usdc), address(credit), wakaiFloat, council);
        vm.prank(council);
        credit.setRouter(address(router));
    }

    // --- debit with funds but NO approval must revert (no silent transfer) ---
    function testDebitInsufficientAllowanceReverts() public {
        usdc.mint(holder, 1_000_000); // has balance, but never approved the router
        vm.expectRevert();
        router.settleDebit(bytes32("a"), holder, merchant, 300_000, "internal-purchase");
    }

    // --- debit approved but balance too low must revert ---
    function testDebitInsufficientBalanceReverts() public {
        vm.prank(holder);
        usdc.approve(address(router), 1_000_000); // approved...
        // ...but holder has 0 balance
        vm.expectRevert();
        router.settleDebit(bytes32("a"), holder, merchant, 300_000, "internal-purchase");
    }

    // --- credit settle with NO credit line drawn must revert at CreditLine.draw (OverLimit) ---
    function testCreditWithoutLimitReverts() public {
        usdc.mint(wakaiFloat, 1_000_000);
        vm.prank(wakaiFloat);
        usdc.approve(address(router), 1_000_000);
        vm.expectRevert(CreditLine.OverLimit.selector);
        router.settleCredit(bytes32("c"), holder, merchant, 300_000, "internal-purchase");
    }

    // --- sanity: properly approved + funded debit succeeds with fee 0 ---
    function testDebitApprovedSucceeds() public {
        usdc.mint(holder, 1_000_000);
        vm.prank(holder);
        usdc.approve(address(router), 300_000);
        router.settleDebit(bytes32("a"), holder, merchant, 300_000, "internal-purchase");
        require(usdc.balanceOf(merchant) == 300_000, "merchant != amount (fee leaked)");
        require(usdc.balanceOf(holder) == 700_000, "holder overcharged");
    }
}
