// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {Postage, IERC20} from "../src/Postage.sol";

/// @dev Minimal USDC mock — only transferFrom is exercised by Postage.sol.
contract MockUsdc is IERC20 {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    bool public nextTransferShouldFail;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        if (nextTransferShouldFail) {
            nextTransferShouldFail = false;
            return false;
        }
        require(balanceOf[from] >= amount, "mock: insufficient balance");
        require(allowance[from][msg.sender] >= amount, "mock: insufficient allowance");
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function setNextTransferShouldFail() external {
        nextTransferShouldFail = true;
    }
}

contract PostageTest is Test {
    MockUsdc usdc;
    Postage  postage;

    address constant TREASURY = address(0xBEEF);
    address constant ALICE    = address(0xA11CE);
    address constant BOB      = address(0xB0B);
    uint256 constant INITIAL_RATE = 10_000; // 0.01 USDC (6 decimals)

    event Paid(
        address indexed sender,
        bytes32 indexed messageHash,
        uint16  recipientCount,
        uint256 amount,
        uint64  paidAtMs
    );
    event RateUpdated(uint256 oldRate, uint256 newRate);
    event OwnerRotated(address indexed oldOwner, address indexed newOwner);

    function setUp() public {
        usdc = new MockUsdc();
        postage = new Postage(IERC20(address(usdc)), TREASURY, INITIAL_RATE);
        usdc.mint(ALICE, 1_000_000); // 1 USDC
        vm.prank(ALICE);
        usdc.approve(address(postage), type(uint256).max);
    }

    // ─── Happy path ──────────────────────────────────────────────────

    function test_payPostage_singleRecipient_transfersAndEmits() public {
        bytes32 mh = keccak256("msg-1");

        vm.expectEmit(true, true, false, true);
        emit Paid(ALICE, mh, 1, INITIAL_RATE, uint64(block.timestamp * 1000));

        vm.prank(ALICE);
        postage.payPostage(mh, 1);

        assertEq(usdc.balanceOf(TREASURY), INITIAL_RATE);
        assertEq(usdc.balanceOf(ALICE),    1_000_000 - INITIAL_RATE);
    }

    function test_payPostage_multipleRecipients_scalesLinearly() public {
        bytes32 mh = keccak256("msg-bulk");
        uint16 n = 5;

        vm.prank(ALICE);
        postage.payPostage(mh, n);

        assertEq(usdc.balanceOf(TREASURY), INITIAL_RATE * n);
    }

    function test_payPostage_maxRecipients_succeeds() public {
        usdc.mint(ALICE, 100 * INITIAL_RATE); // top up
        bytes32 mh = keccak256("msg-max");

        vm.prank(ALICE);
        postage.payPostage(mh, 100);

        assertEq(usdc.balanceOf(TREASURY), INITIAL_RATE * 100);
    }

    // ─── Validation ──────────────────────────────────────────────────

    function test_payPostage_zeroRecipients_reverts() public {
        vm.prank(ALICE);
        vm.expectRevert(abi.encodeWithSelector(Postage.BadRecipientCount.selector, uint16(0)));
        postage.payPostage(keccak256("zero"), 0);
    }

    function test_payPostage_over100Recipients_reverts() public {
        vm.prank(ALICE);
        vm.expectRevert(abi.encodeWithSelector(Postage.BadRecipientCount.selector, uint16(101)));
        postage.payPostage(keccak256("over"), 101);
    }

    function test_payPostage_transferReturnsFalse_reverts() public {
        usdc.setNextTransferShouldFail();
        vm.prank(ALICE);
        vm.expectRevert(Postage.TransferFailed.selector);
        postage.payPostage(keccak256("fail"), 1);
    }

    // ─── Admin ───────────────────────────────────────────────────────

    function test_setRate_byOwner_updates() public {
        uint256 newRate = 20_000;
        vm.expectEmit(false, false, false, true);
        emit RateUpdated(INITIAL_RATE, newRate);
        postage.setRate(newRate);
        assertEq(postage.rateUsdcPerRecipient(), newRate);
    }

    function test_setRate_byNonOwner_reverts() public {
        vm.prank(ALICE);
        vm.expectRevert(Postage.NotOwner.selector);
        postage.setRate(99);
    }

    function test_setOwner_rotatesAdmin() public {
        vm.expectEmit(true, true, false, false);
        emit OwnerRotated(address(this), BOB);
        postage.setOwner(BOB);
        assertEq(postage.owner(), BOB);

        // old owner can no longer set rate
        vm.expectRevert(Postage.NotOwner.selector);
        postage.setRate(1);

        // new owner can
        vm.prank(BOB);
        postage.setRate(1);
        assertEq(postage.rateUsdcPerRecipient(), 1);
    }

    // ─── Immutables ──────────────────────────────────────────────────

    function test_constructor_setsImmutables() public view {
        assertEq(address(postage.usdc()), address(usdc));
        assertEq(postage.treasury(), TREASURY);
        assertEq(postage.rateUsdcPerRecipient(), INITIAL_RATE);
        assertEq(postage.owner(), address(this));
    }
}
