// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {Reserve, IERC20} from "../src/Reserve.sol";

/// @dev Minimal ERC20 mock for tests — only the functions Reserve calls.
contract MockUSDC is IERC20 {
    mapping(address => uint256) public _balanceOf;
    function transfer(address to, uint256 amount) external returns (bool) {
        require(_balanceOf[msg.sender] >= amount, "insufficient");
        _balanceOf[msg.sender] -= amount;
        _balanceOf[to] += amount;
        return true;
    }
    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(_balanceOf[from] >= amount, "insufficient");
        _balanceOf[from] -= amount;
        _balanceOf[to] += amount;
        return true;
    }
    function balanceOf(address account) external view returns (uint256) {
        return _balanceOf[account];
    }
    function decimals() external pure returns (uint8) { return 6; }
    function mint(address to, uint256 amount) external { _balanceOf[to] += amount; }
}

contract ReserveTest is Test {
    Reserve internal reserve;
    MockUSDC internal usdc;

    address internal council = makeAddr("council");
    address internal publicFund = makeAddr("publicFund");
    address internal operator = makeAddr("operator");
    address internal recipient = makeAddr("recipient");
    address internal stranger = makeAddr("stranger");

    uint256 internal constant DAILY_CAP = 50_000 * 1e6; // 50,000 USDC in micros

    function setUp() public {
        usdc = new MockUSDC();
        reserve = new Reserve(council, IERC20(address(usdc)), publicFund, DAILY_CAP);
        // Fund the reserve with 100k USDC.
        usdc.mint(address(reserve), 100_000 * 1e6);
        // Council whitelists the operator.
        vm.prank(council);
        reserve.setOperator(operator, true);
    }

    // ─── Construction ──────────────────────────────────────────────────

    function test_constructor() public view {
        assertEq(reserve.owner(), council);
        assertEq(address(reserve.usdc()), address(usdc));
        assertEq(reserve.publicFundSafe(), publicFund);
        assertEq(reserve.titheBps(), 1000);
        assertEq(reserve.dailyCapMicros(), DAILY_CAP);
    }

    function test_constructor_revertsZeroOwner() public {
        vm.expectRevert(Reserve.ZeroAddress.selector);
        new Reserve(address(0), IERC20(address(usdc)), publicFund, DAILY_CAP);
    }

    function test_constructor_revertsZeroUsdc() public {
        vm.expectRevert(Reserve.ZeroAddress.selector);
        new Reserve(council, IERC20(address(0)), publicFund, DAILY_CAP);
    }

    function test_constructor_revertsZeroPublicFund() public {
        vm.expectRevert(Reserve.ZeroAddress.selector);
        new Reserve(council, IERC20(address(usdc)), address(0), DAILY_CAP);
    }

    function test_constructor_revertsZeroCap() public {
        vm.expectRevert(Reserve.InvalidArgument.selector);
        new Reserve(council, IERC20(address(usdc)), publicFund, 0);
    }

    // ─── creditFromFiat happy path ─────────────────────────────────────

    function test_creditFromFiat_splitTithe10pct() public {
        bytes32 key = keccak256("stripe-auth-1");
        uint256 amount = 1_000 * 1e6; // 1000 USDC

        vm.prank(operator);
        (uint256 net, uint256 tithe) = reserve.creditFromFiat(key, recipient, amount);

        assertEq(tithe, 100 * 1e6); // 10% of 1000
        assertEq(net, 900 * 1e6);
        assertEq(usdc.balanceOf(recipient), net);
        assertEq(usdc.balanceOf(publicFund), tithe);
        assertEq(usdc.balanceOf(address(reserve)), 100_000 * 1e6 - amount);
        assertTrue(reserve.isIdempotencyKeyConsumed(key));
    }

    function test_creditFromFiat_idempotencyReplay() public {
        bytes32 key = keccak256("stripe-auth-1");
        vm.prank(operator);
        reserve.creditFromFiat(key, recipient, 100 * 1e6);
        vm.prank(operator);
        vm.expectRevert(Reserve.Idempotent.selector);
        reserve.creditFromFiat(key, recipient, 100 * 1e6);
    }

    function test_creditFromFiat_revertsNotOperator() public {
        vm.prank(stranger);
        vm.expectRevert(Reserve.NotOperator.selector);
        reserve.creditFromFiat(keccak256("k"), recipient, 100 * 1e6);
    }

    function test_creditFromFiat_revertsDailyCapExceeded() public {
        uint256 amount = DAILY_CAP / 2 + 1;
        vm.prank(operator);
        reserve.creditFromFiat(keccak256("k1"), recipient, amount);
        vm.prank(operator);
        vm.expectRevert(Reserve.DailyCapExceeded.selector);
        reserve.creditFromFiat(keccak256("k2"), recipient, amount);
    }

    function test_creditFromFiat_revertsInsufficientReserve() public {
        // Withdraw most of the reserve first.
        vm.prank(council);
        reserve.withdraw(council, 100_000 * 1e6 - 50 * 1e6);

        vm.prank(operator);
        vm.expectRevert(Reserve.InsufficientTreasuryReserve.selector);
        reserve.creditFromFiat(keccak256("k"), recipient, 100 * 1e6);
    }

    function test_creditFromFiat_revertsZeroAmount() public {
        vm.prank(operator);
        vm.expectRevert(Reserve.InvalidArgument.selector);
        reserve.creditFromFiat(keccak256("k"), recipient, 0);
    }

    function test_creditFromFiat_dailyCapResetsBetweenDays() public {
        uint256 amount = (DAILY_CAP * 2) / 3; // 2/3 of cap

        vm.prank(operator);
        reserve.creditFromFiat(keccak256("k1"), recipient, amount);
        // Same day — second call should exceed cap.
        vm.prank(operator);
        vm.expectRevert(Reserve.DailyCapExceeded.selector);
        reserve.creditFromFiat(keccak256("k2"), recipient, amount);

        // Advance 24h.
        vm.warp(block.timestamp + 86_400);

        vm.prank(operator);
        reserve.creditFromFiat(keccak256("k3"), recipient, amount);
        // Now spent again ok.
    }

    // ─── Council config paths ──────────────────────────────────────────

    function test_setOperator_addRemove() public {
        address newOp = makeAddr("newOp");
        vm.prank(council);
        reserve.setOperator(newOp, true);
        assertTrue(reserve.isOperator(newOp));
        vm.prank(council);
        reserve.setOperator(newOp, false);
        assertFalse(reserve.isOperator(newOp));
    }

    function test_setOperator_revertsNotOwner() public {
        vm.prank(stranger);
        vm.expectRevert(Reserve.NotOwner.selector);
        reserve.setOperator(stranger, true);
    }

    function test_setDailyCap_happyPath() public {
        vm.prank(council);
        reserve.setDailyCap(123_456);
        assertEq(reserve.dailyCapMicros(), 123_456);
    }

    function test_setDailyCap_revertsZero() public {
        vm.prank(council);
        vm.expectRevert(Reserve.InvalidArgument.selector);
        reserve.setDailyCap(0);
    }

    function test_setTitheBps_happyPath() public {
        vm.prank(council);
        reserve.setTitheBps(500); // 5%
        assertEq(reserve.titheBps(), 500);

        // Run a credit to verify it uses the new tithe.
        vm.prank(operator);
        (uint256 net, uint256 tithe) = reserve.creditFromFiat(keccak256("k"), recipient, 1_000 * 1e6);
        assertEq(tithe, 50 * 1e6);
        assertEq(net, 950 * 1e6);
    }

    function test_setTitheBps_revertsOutOfRange() public {
        vm.prank(council);
        vm.expectRevert(Reserve.TitheBpsOutOfRange.selector);
        reserve.setTitheBps(5_001);
    }

    function test_setPublicFundSafe_happyPath() public {
        address newSafe = makeAddr("newSafe");
        vm.prank(council);
        reserve.setPublicFundSafe(newSafe);
        assertEq(reserve.publicFundSafe(), newSafe);
    }

    function test_withdraw_happyPath() public {
        vm.prank(council);
        reserve.withdraw(council, 100 * 1e6);
        assertEq(usdc.balanceOf(council), 100 * 1e6);
    }

    function test_withdraw_revertsInsufficient() public {
        vm.prank(council);
        vm.expectRevert(Reserve.InsufficientTreasuryReserve.selector);
        reserve.withdraw(council, 1_000_000 * 1e6);
    }

    function test_setOwner_happyPath() public {
        address newCouncil = makeAddr("newCouncil");
        vm.prank(council);
        reserve.setOwner(newCouncil);
        assertEq(reserve.owner(), newCouncil);
    }

    function test_setOwner_revertsNotOwner() public {
        vm.prank(stranger);
        vm.expectRevert(Reserve.NotOwner.selector);
        reserve.setOwner(stranger);
    }

    // ─── Reads ────────────────────────────────────────────────────────

    function test_remainingDailyCap() public {
        assertEq(reserve.remainingDailyCapMicros(), DAILY_CAP);
        vm.prank(operator);
        reserve.creditFromFiat(keccak256("k"), recipient, 1_000 * 1e6);
        assertEq(reserve.remainingDailyCapMicros(), DAILY_CAP - 1_000 * 1e6);
    }

    function test_reserveBalance() public view {
        assertEq(reserve.reserveBalanceMicros(), 100_000 * 1e6);
    }
}
