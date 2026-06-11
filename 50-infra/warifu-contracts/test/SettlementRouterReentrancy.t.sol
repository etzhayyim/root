// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
pragma solidity ^0.8.26;

import {SettlementRouter} from "../src/SettlementRouter.sol";
import {CreditLine} from "../src/CreditLine.sol";

interface Vm {
    function prank(address) external;
    function expectRevert(bytes4) external;
}

/// A hostile token whose transferFrom re-enters the router mid-settlement.
contract ReenterToken {
    address public router;
    bool public attack;
    mapping(address => uint256) public balanceOf;

    function setRouter(address r) external { router = r; }
    function setAttack(bool a) external { attack = a; }
    function mint(address to, uint256 a) external { balanceOf[to] += a; }
    function approve(address, uint256) external pure returns (bool) { return true; }
    function transfer(address, uint256) external pure returns (bool) { return true; }

    function transferFrom(address f, address t, uint256 a) external returns (bool) {
        if (attack) {
            attack = false; // avoid infinite loop if the guard were absent
            // Re-enter: a correctly guarded router must revert here.
            SettlementRouter(router).settleDebit(bytes32("reenter"), f, t, a, "internal-purchase");
        }
        balanceOf[f] -= a;
        balanceOf[t] += a;
        return true;
    }
}

/// @title SettlementRouter reentrancy hardening (ADR-2605302000)
contract SettlementRouterReentrancyTest {
    Vm constant vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

    ReenterToken token;
    CreditLine credit;
    SettlementRouter router;
    address council = address(0xC0);
    address holder = address(0x11);
    address merchant = address(0x3E);
    address wakaiFloat = address(0xFA);

    function setUp() public {
        token = new ReenterToken();
        credit = new CreditLine(wakaiFloat, council);
        router = new SettlementRouter(address(token), address(credit), wakaiFloat, council);
        vm.prank(council);
        credit.setRouter(address(router));
        token.setRouter(address(router));
        token.mint(holder, 1_000_000);
    }

    // The re-entrant call inside transferFrom must bubble Reentrancy() and revert the whole tx.
    function testReentrancyBlocked() public {
        token.setAttack(true);
        vm.expectRevert(SettlementRouter.Reentrancy.selector);
        router.settleDebit(bytes32("auth"), holder, merchant, 100_000, "internal-purchase");
    }

    // Sanity: with attack off, the same settlement succeeds (guard does not block normal flow).
    function testNormalSettlementSucceeds() public {
        token.setAttack(false);
        router.settleDebit(bytes32("auth"), holder, merchant, 100_000, "internal-purchase");
        require(token.balanceOf(merchant) == 100_000, "normal settle failed");
    }
}
