// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
pragma solidity ^0.8.26;

import {SettlementRouter} from "../src/SettlementRouter.sol";
import {CreditLine} from "../src/CreditLine.sol";

/// Minimal HEVM cheatcode surface (avoids a forge-std dependency in the R0 scaffold).
interface Vm {
    function prank(address) external;
    function startPrank(address) external;
    function stopPrank() external;
    function expectRevert(bytes4) external;
}

/// Minimal mock USDC (6dp) — enough to exercise transferFrom paths.
contract MockUSDC {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address to, uint256 a) external {
        balanceOf[to] += a;
    }

    function approve(address s, uint256 a) external returns (bool) {
        allowance[msg.sender][s] = a;
        return true;
    }

    function transfer(address to, uint256 a) external returns (bool) {
        balanceOf[msg.sender] -= a;
        balanceOf[to] += a;
        return true;
    }

    function transferFrom(address f, address t, uint256 a) external returns (bool) {
        allowance[f][msg.sender] -= a;
        balanceOf[f] -= a;
        balanceOf[t] += a;
        return true;
    }
}

/// @title SettlementRouter invariants — zero fee + purpose allow-list (ADR-2605302000)
contract SettlementRouterTest {
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

    // --- zero-fee invariant: merchant receives EXACTLY the amount, holder pays EXACTLY it ---
    function testDebitZeroFee() public {
        uint256 amount = 1_200_000; // 1.2 USDC
        usdc.mint(holder, amount);
        vm.prank(holder);
        usdc.approve(address(router), amount);

        router.settleDebit(bytes32("auth1"), holder, merchant, amount, "internal-purchase");

        require(usdc.balanceOf(merchant) == amount, "merchant != amount (fee leaked)");
        require(usdc.balanceOf(holder) == 0, "holder overcharged (fee leaked)");
        require(router.MERCHANT_FEE_BPS() == 0, "fee bps must be 0");
    }

    // --- credit path: draws the 0% line and pays merchant from the wakai float (fee 0) ---
    function testCreditZeroFeeDrawsLine() public {
        uint256 amount = 800_000;
        vm.prank(council);
        credit.setLimit(holder, 1_000_000); // interest-free limit
        usdc.mint(wakaiFloat, amount);
        vm.prank(wakaiFloat);
        usdc.approve(address(router), amount);

        router.settleCredit(bytes32("authC"), holder, merchant, amount, "internal-purchase");

        require(usdc.balanceOf(merchant) == amount, "merchant != amount (fee leaked)");
        require(usdc.balanceOf(wakaiFloat) == 0, "wakai float not drawn");
        require(credit.available(holder) == 200_000, "credit line not drawn at 0%");
    }

    // --- purpose gate: external 'purchase' reverts before Phase 2 is enabled ---
    function testExternalPurposeGatedBeforePhase2() public {
        uint256 amount = 500_000;
        usdc.mint(holder, amount);
        vm.prank(holder);
        usdc.approve(address(router), amount);

        vm.expectRevert(SettlementRouter.PurposeGated.selector);
        router.settleDebit(bytes32("auth2"), holder, merchant, amount, "purchase");
    }

    // --- purpose gate: after Lv7+ enablePhase2, external 'purchase' is allowed ---
    function testExternalPurposeAllowedAfterPhase2() public {
        uint256 amount = 500_000;
        usdc.mint(holder, amount);
        vm.prank(holder);
        usdc.approve(address(router), amount);

        vm.prank(council); // council MUST be the Lv7+ Safe for this to be legitimate
        router.enablePhase2(bytes32("adr-2605192115-amendment"));

        router.settleDebit(bytes32("auth3"), holder, merchant, amount, "purchase");
        require(usdc.balanceOf(merchant) == amount, "phase2 debit failed");
    }

    // --- purpose gate: unknown purpose always reverts ---
    function testUnknownPurposeReverts() public {
        vm.expectRevert(SettlementRouter.PurposeNotAllowed.selector);
        router.settleDebit(bytes32("auth4"), holder, merchant, 1, "tip");
    }

    // --- only council may flip phase2 ---
    function testEnablePhase2OnlyCouncil() public {
        vm.prank(holder);
        vm.expectRevert(SettlementRouter.NotCouncil.selector);
        router.enablePhase2(bytes32("nope"));
    }
}
