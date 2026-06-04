// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test, console} from "forge-std/Test.sol";
import {TestUSDC} from "../src/TestUSDC.sol";
import {GCCMinter, AggregatorV3Interface} from "../src/GCCMinter.sol";

/**
 * @title MockERC20
 * @notice Minimal ERC-20 for testing (USDC/USDT mock).
 */
contract MockERC20 {
    string public name;
    string public symbol;
    uint8 public decimals;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    constructor(string memory _name, string memory _symbol, uint8 _decimals) {
        name = _name;
        symbol = _symbol;
        decimals = _decimals;
    }

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
        totalSupply += amount;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "insufficient");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(balanceOf[from] >= amount, "insufficient");
        require(allowance[from][msg.sender] >= amount, "not approved");
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}

/**
 * @title MockChainlinkFeed
 * @notice Returns a fixed ETH/USD price for testing.
 */
contract MockChainlinkFeed {
    int256 public price;
    uint256 public updatedAt;

    constructor(int256 _price) {
        price = _price;
        updatedAt = block.timestamp;
    }

    function setPrice(int256 _price) external {
        price = _price;
        updatedAt = block.timestamp;
    }

    function setStale() external {
        updatedAt = block.timestamp - 2 hours;
    }

    function latestRoundData()
        external
        view
        returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 _updatedAt, uint80 answeredInRound)
    {
        return (1, price, block.timestamp, updatedAt, 1);
    }
}

contract GCCMinterTest is Test {
    TestUSDC gcc;
    MockERC20 usdc;
    MockERC20 usdt;
    MockChainlinkFeed feed;
    GCCMinter minter;

    address owner = address(0xBEEF);
    address treasury = address(0xCAFE);
    address buyer = address(0x1234);

    function setUp() public {
        // Set block.timestamp to a realistic value (avoids underflow in staleness checks)
        vm.warp(1700000000);

        // Deploy GCC token
        gcc = new TestUSDC("Etzhayyim Computing Credits", "GCC", "USD", owner, owner, owner, owner);

        // Deploy mock stablecoins
        usdc = new MockERC20("USD Coin", "USDC", 6);
        usdt = new MockERC20("Tether USD", "USDT", 6);

        // Deploy mock Chainlink feed (ETH = $2500, 8 decimals)
        feed = new MockChainlinkFeed(2500e8);

        // Deploy minter
        minter = new GCCMinter(
            address(gcc),
            address(usdc),
            address(usdt),
            address(feed),
            treasury,
            owner,
            1e6 // 1:1 rate
        );

        // Grant minter role to the minter contract (via masterMinter = owner)
        vm.prank(owner);
        gcc.configureMinter(address(minter), 100_000_000_000e6);

        // Give buyer some stablecoins
        usdc.mint(buyer, 10_000e6); // 10k USDC
        usdt.mint(buyer, 10_000e6); // 10k USDT
        vm.deal(buyer, 10 ether);
    }

    // ──────────────────────────────────────────────
    // buyWithETH
    // ──────────────────────────────────────────────

    function test_buyWithETH() public {
        // 1 ETH at $2500 → 2500 GCC
        vm.prank(buyer);
        minter.buyWithETH{value: 1 ether}();

        assertEq(gcc.balanceOf(buyer), 2500e6, "buyer should receive 2500 GCC");
        assertEq(treasury.balance, 1 ether, "treasury should receive 1 ETH");
    }

    function test_buyWithETH_smallAmount() public {
        // 0.001 ETH at $2500 → 2.5 GCC
        vm.prank(buyer);
        minter.buyWithETH{value: 0.001 ether}();

        assertEq(gcc.balanceOf(buyer), 2_500_000, "buyer should receive 2.5 GCC (2500000 units)");
    }

    function test_buyWithETH_zeroReverts() public {
        vm.prank(buyer);
        vm.expectRevert("GCCMinter: zero ETH");
        minter.buyWithETH{value: 0}();
    }

    function test_buyWithETH_stalePriceReverts() public {
        feed.setStale();
        vm.prank(buyer);
        vm.expectRevert("GCCMinter: stale price");
        minter.buyWithETH{value: 1 ether}();
    }

    // ──────────────────────────────────────────────
    // buyWithUSDC
    // ──────────────────────────────────────────────

    function test_buyWithUSDC() public {
        // 100 USDC → 100 GCC
        vm.startPrank(buyer);
        usdc.approve(address(minter), 100e6);
        minter.buyWithUSDC(100e6);
        vm.stopPrank();

        assertEq(gcc.balanceOf(buyer), 100e6, "buyer should receive 100 GCC");
        assertEq(usdc.balanceOf(treasury), 100e6, "treasury should receive 100 USDC");
        assertEq(usdc.balanceOf(buyer), 9_900e6, "buyer USDC should decrease");
    }

    function test_buyWithUSDC_zeroReverts() public {
        vm.prank(buyer);
        vm.expectRevert("GCCMinter: zero amount");
        minter.buyWithUSDC(0);
    }

    function test_buyWithUSDC_noApprovalReverts() public {
        vm.prank(buyer);
        vm.expectRevert("GCCMinter: transferFrom failed");
        minter.buyWithUSDC(100e6);
    }

    // ──────────────────────────────────────────────
    // buyWithUSDT
    // ──────────────────────────────────────────────

    function test_buyWithUSDT() public {
        // 200 USDT → 200 GCC
        vm.startPrank(buyer);
        usdt.approve(address(minter), 200e6);
        minter.buyWithUSDT(200e6);
        vm.stopPrank();

        assertEq(gcc.balanceOf(buyer), 200e6, "buyer should receive 200 GCC");
        assertEq(usdt.balanceOf(treasury), 200e6, "treasury should receive 200 USDT");
    }

    // ──────────────────────────────────────────────
    // Rate changes
    // ──────────────────────────────────────────────

    function test_customRate() public {
        // Set rate to 2x: 1 USDC = 2 GCC
        vm.prank(owner);
        minter.setRate(2e6);

        vm.startPrank(buyer);
        usdc.approve(address(minter), 100e6);
        minter.buyWithUSDC(100e6);
        vm.stopPrank();

        assertEq(gcc.balanceOf(buyer), 200e6, "buyer should receive 200 GCC at 2x rate");
    }

    // ──────────────────────────────────────────────
    // Pause
    // ──────────────────────────────────────────────

    function test_pauseBlocksBuy() public {
        vm.prank(owner);
        minter.pause();

        vm.prank(buyer);
        vm.expectRevert("GCCMinter: paused");
        minter.buyWithETH{value: 1 ether}();
    }

    function test_unpauseResumes() public {
        vm.prank(owner);
        minter.pause();

        vm.prank(owner);
        minter.unpause();

        vm.prank(buyer);
        minter.buyWithETH{value: 1 ether}();
        assertEq(gcc.balanceOf(buyer), 2500e6);
    }

    // ──────────────────────────────────────────────
    // Owner functions
    // ──────────────────────────────────────────────

    function test_nonOwnerCannotPause() public {
        vm.prank(buyer);
        vm.expectRevert("GCCMinter: caller is not the owner");
        minter.pause();
    }

    function test_transferOwnership() public {
        vm.prank(owner);
        minter.transferOwnership(buyer);
        assertEq(minter.owner(), buyer);
    }

    function test_setTreasury() public {
        vm.prank(owner);
        minter.setTreasury(address(0xDEAD));
        assertEq(minter.treasury(), address(0xDEAD));
    }

    // ──────────────────────────────────────────────
    // Reject direct ETH
    // ──────────────────────────────────────────────

    function test_rejectDirectETH() public {
        vm.prank(buyer);
        vm.expectRevert("GCCMinter: use buyWithETH()");
        (bool s,) = address(minter).call{value: 1 ether}("");
        s; // suppress unused warning
    }
}
