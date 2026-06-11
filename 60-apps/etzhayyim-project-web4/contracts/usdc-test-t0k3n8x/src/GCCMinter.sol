// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {TestUSDC} from "./TestUSDC.sol";

/**
 * @title GCCMinter
 * @notice Accepts ETH, USDC, or USDT and mints GCC (Etzhayyim Computing Credits) to the buyer.
 *
 * This contract must be registered as a minter on the GCC token via
 * `gcc.configureMinter(address(this), cap)` called by the masterMinter (Safe).
 *
 * ETH pricing uses a Chainlink ETH/USD price feed.
 * Stablecoins (USDC/USDT) are treated as 1 USD at a configurable rate.
 */
contract GCCMinter {
    // ──────────────────────────────────────────────
    // Immutables
    // ──────────────────────────────────────────────
    TestUSDC public immutable gcc;
    address public immutable usdc;
    address public immutable usdt;
    AggregatorV3Interface public immutable ethUsdFeed;

    // ──────────────────────────────────────────────
    // Config (mutable by owner)
    // ──────────────────────────────────────────────
    address public owner;
    address public treasury;
    uint256 public stablecoinRate; // GCC minted per 1 USD of stablecoin (6 decimals). 1e6 = 1:1
    bool public paused;

    // ──────────────────────────────────────────────
    // Events
    // ──────────────────────────────────────────────
    event CreditsPurchased(address indexed buyer, string currency, uint256 paid, uint256 gccMinted);
    event TreasuryUpdated(address indexed newTreasury);
    event RateUpdated(uint256 newRate);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event Paused();
    event Unpaused();

    // ──────────────────────────────────────────────
    // Modifiers
    // ──────────────────────────────────────────────
    modifier onlyOwner() {
        require(msg.sender == owner, "GCCMinter: caller is not the owner");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "GCCMinter: paused");
        _;
    }

    // ──────────────────────────────────────────────
    // Constructor
    // ──────────────────────────────────────────────
    constructor(
        address _gcc,
        address _usdc,
        address _usdt,
        address _ethUsdFeed,
        address _treasury,
        address _owner,
        uint256 _stablecoinRate
    ) {
        require(_gcc != address(0), "zero gcc");
        require(_usdc != address(0), "zero usdc");
        require(_usdt != address(0), "zero usdt");
        require(_ethUsdFeed != address(0), "zero feed");
        require(_treasury != address(0), "zero treasury");
        require(_owner != address(0), "zero owner");
        require(_stablecoinRate > 0, "zero rate");

        gcc = TestUSDC(_gcc);
        usdc = _usdc;
        usdt = _usdt;
        ethUsdFeed = AggregatorV3Interface(_ethUsdFeed);
        treasury = _treasury;
        owner = _owner;
        stablecoinRate = _stablecoinRate;
    }

    // ══════════════════════════════════════════════
    // Buy functions
    // ══════════════════════════════════════════════

    /**
     * @notice Buy GCC with ETH. Chainlink ETH/USD feed determines the exchange rate.
     */
    function buyWithETH() external payable whenNotPaused {
        require(msg.value > 0, "GCCMinter: zero ETH");

        uint256 ethUsdPrice = _getETHPrice(); // 8 decimals
        // msg.value is 18 decimals, ethUsdPrice is 8 decimals, GCC is 6 decimals
        // usdValue (6 dec) = msg.value (18 dec) * ethUsdPrice (8 dec) / 1e20
        uint256 usdValue = msg.value * ethUsdPrice / 1e20;
        uint256 gccAmount = usdValue * stablecoinRate / 1e6;
        require(gccAmount > 0, "GCCMinter: amount too small");

        // Forward ETH to treasury
        (bool sent,) = treasury.call{value: msg.value}("");
        require(sent, "GCCMinter: ETH transfer failed");

        // Mint GCC to buyer
        gcc.mint(msg.sender, gccAmount);

        emit CreditsPurchased(msg.sender, "ETH", msg.value, gccAmount);
    }

    /**
     * @notice Buy GCC with USDC. Caller must approve this contract first.
     * @param amount USDC amount (6 decimals)
     */
    function buyWithUSDC(uint256 amount) external whenNotPaused {
        require(amount > 0, "GCCMinter: zero amount");

        uint256 gccAmount = amount * stablecoinRate / 1e6;
        require(gccAmount > 0, "GCCMinter: amount too small");

        // Pull USDC from buyer to treasury
        _safeTransferFrom(usdc, msg.sender, treasury, amount);

        // Mint GCC to buyer
        gcc.mint(msg.sender, gccAmount);

        emit CreditsPurchased(msg.sender, "USDC", amount, gccAmount);
    }

    /**
     * @notice Buy GCC with USDT. Caller must approve this contract first.
     *         Uses safeTransferFrom since USDT doesn't return bool.
     * @param amount USDT amount (6 decimals)
     */
    function buyWithUSDT(uint256 amount) external whenNotPaused {
        require(amount > 0, "GCCMinter: zero amount");

        uint256 gccAmount = amount * stablecoinRate / 1e6;
        require(gccAmount > 0, "GCCMinter: amount too small");

        // Pull USDT from buyer to treasury (non-standard ERC-20)
        _safeTransferFrom(usdt, msg.sender, treasury, amount);

        // Mint GCC to buyer
        gcc.mint(msg.sender, gccAmount);

        emit CreditsPurchased(msg.sender, "USDT", amount, gccAmount);
    }

    // ══════════════════════════════════════════════
    // Chainlink price feed
    // ══════════════════════════════════════════════

    function _getETHPrice() internal view returns (uint256) {
        (, int256 answer,, uint256 updatedAt,) = ethUsdFeed.latestRoundData();
        require(answer > 0, "GCCMinter: invalid price");
        require(updatedAt + 1 hours > block.timestamp, "GCCMinter: stale price");
        return uint256(answer);
    }

    /**
     * @notice Read current ETH/USD price from Chainlink (8 decimals).
     */
    function getETHPrice() external view returns (uint256) {
        return _getETHPrice();
    }

    // ══════════════════════════════════════════════
    // Safe ERC-20 transfer (handles non-standard USDT)
    // ══════════════════════════════════════════════

    function _safeTransferFrom(address token, address from, address to, uint256 amount) internal {
        (bool success, bytes memory data) =
            token.call(abi.encodeWithSelector(0x23b872dd, from, to, amount)); // transferFrom(address,address,uint256)
        require(success && (data.length == 0 || abi.decode(data, (bool))), "GCCMinter: transferFrom failed");
    }

    // ══════════════════════════════════════════════
    // Owner functions
    // ══════════════════════════════════════════════

    function setTreasury(address _treasury) external onlyOwner {
        require(_treasury != address(0), "zero treasury");
        treasury = _treasury;
        emit TreasuryUpdated(_treasury);
    }

    function setRate(uint256 _rate) external onlyOwner {
        require(_rate > 0, "zero rate");
        stablecoinRate = _rate;
        emit RateUpdated(_rate);
    }

    function pause() external onlyOwner {
        paused = true;
        emit Paused();
    }

    function unpause() external onlyOwner {
        paused = false;
        emit Unpaused();
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "zero owner");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    // Reject direct ETH sends without buyWithETH()
    receive() external payable {
        revert("GCCMinter: use buyWithETH()");
    }
}

/**
 * @notice Minimal Chainlink AggregatorV3Interface.
 */
interface AggregatorV3Interface {
    function latestRoundData()
        external
        view
        returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound);
}
