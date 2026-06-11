// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function decimals() external view returns (uint8);
}

/**
 * @title Reserve
 * @notice Council-controlled USDC reserve backing the Stripe Issuing →
 *         ERC-4337 + USDC bridge per ADR-2605212050.
 *
 *         Vendor (etzhayyim) holds fiat receivables; this contract holds
 *         the on-chain USDC backing. Each `creditFromFiat` call consumes
 *         from the reserve and atomically splits 90% to the recipient +
 *         10% to the Public Fund (ADR-2605192130 tithe).
 *
 * @dev Roles:
 *      - owner (Council 5-of-7 Safe): rotates operators, sets daily cap,
 *        sets Public Fund address, withdraws excess, rotates owner.
 *      - operator (the etzhayyim-fiat-bridge XRPC service): calls
 *        creditFromFiat. Allowlist-gated; Council adds/removes.
 *
 *      Idempotency: every creditFromFiat carries an idempotencyKey
 *      (vendor Stripe authorization id). Replay is rejected.
 *
 *      Daily cap: aggregate `amountUSDCMicros` per UTC day must stay
 *      under `dailyCapMicros`. Cap is Council-governed.
 *
 *      No upgrade, no pause. To change behaviour, deploy a new Reserve
 *      and update the bridge service config.
 */
contract Reserve {
    // ─── State ─────────────────────────────────────────────────────────

    address public owner;
    IERC20 public immutable usdc;
    address public publicFundSafe;
    uint256 public titheBps = 1000;          // 10.00% (basis points, mutable by Council)
    uint256 public dailyCapMicros;            // per-UTC-day aggregate cap
    mapping(uint256 => uint256) public dailySpent; // utcDay => micros credited
    mapping(address => bool) public isOperator;
    mapping(bytes32 => bool) public consumedIdempotencyKey;

    uint256 public constant BPS_DIVISOR = 10_000;

    // ─── Events ────────────────────────────────────────────────────────

    event OwnerChanged(address indexed previousOwner, address indexed newOwner);
    event OperatorSet(address indexed operator, bool active);
    event DailyCapSet(uint256 newCapMicros);
    event TitheBpsSet(uint256 newTitheBps);
    event PublicFundSafeSet(address indexed newSafe);
    event FiatCredit(
        bytes32 indexed idempotencyKey,
        address indexed recipient,
        uint256 amountUSDCMicros,
        uint256 titheUSDCMicros,
        uint256 utcDay
    );
    event Withdraw(address indexed to, uint256 amountUSDCMicros);

    // ─── Errors ────────────────────────────────────────────────────────

    error NotOwner();
    error NotOperator();
    error ZeroAddress();
    error InvalidArgument();
    error DailyCapExceeded();
    error InsufficientTreasuryReserve();
    error Idempotent();
    error TitheBpsOutOfRange();

    // ─── Construction ──────────────────────────────────────────────────

    constructor(
        address initialOwner,
        IERC20 usdcToken,
        address initialPublicFundSafe,
        uint256 initialDailyCapMicros
    ) {
        if (initialOwner == address(0)) revert ZeroAddress();
        if (address(usdcToken) == address(0)) revert ZeroAddress();
        if (initialPublicFundSafe == address(0)) revert ZeroAddress();
        if (initialDailyCapMicros == 0) revert InvalidArgument();
        owner = initialOwner;
        usdc = usdcToken;
        publicFundSafe = initialPublicFundSafe;
        dailyCapMicros = initialDailyCapMicros;
        emit OwnerChanged(address(0), initialOwner);
        emit PublicFundSafeSet(initialPublicFundSafe);
        emit DailyCapSet(initialDailyCapMicros);
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }
    modifier onlyOperator() {
        if (!isOperator[msg.sender]) revert NotOperator();
        _;
    }

    // ─── Council-governed config ───────────────────────────────────────

    function setOwner(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroAddress();
        emit OwnerChanged(owner, newOwner);
        owner = newOwner;
    }

    function setOperator(address operator, bool active) external onlyOwner {
        if (operator == address(0)) revert ZeroAddress();
        isOperator[operator] = active;
        emit OperatorSet(operator, active);
    }

    function setDailyCap(uint256 newCapMicros) external onlyOwner {
        if (newCapMicros == 0) revert InvalidArgument();
        dailyCapMicros = newCapMicros;
        emit DailyCapSet(newCapMicros);
    }

    function setTitheBps(uint256 newTitheBps) external onlyOwner {
        // Constrain to 0–50% to make accidental misconfiguration a revert
        // rather than silently destroying recipient value.
        if (newTitheBps > 5_000) revert TitheBpsOutOfRange();
        titheBps = newTitheBps;
        emit TitheBpsSet(newTitheBps);
    }

    function setPublicFundSafe(address newSafe) external onlyOwner {
        if (newSafe == address(0)) revert ZeroAddress();
        publicFundSafe = newSafe;
        emit PublicFundSafeSet(newSafe);
    }

    /// @notice Council withdraws excess USDC (e.g. surplus after vendor
    ///         monthly reconciliation). The reserve never drops below 0.
    function withdraw(address to, uint256 amountUSDCMicros) external onlyOwner {
        if (to == address(0)) revert ZeroAddress();
        if (amountUSDCMicros == 0) revert InvalidArgument();
        if (usdc.balanceOf(address(this)) < amountUSDCMicros) revert InsufficientTreasuryReserve();
        require(usdc.transfer(to, amountUSDCMicros), "usdc transfer failed");
        emit Withdraw(to, amountUSDCMicros);
    }

    // ─── Operator path — fiat → on-chain mint ──────────────────────────

    function creditFromFiat(
        bytes32 idempotencyKey,
        address recipient,
        uint256 amountUSDCMicros
    ) external onlyOperator returns (uint256 net, uint256 tithe) {
        if (idempotencyKey == bytes32(0)) revert InvalidArgument();
        if (recipient == address(0)) revert ZeroAddress();
        if (amountUSDCMicros == 0) revert InvalidArgument();
        if (consumedIdempotencyKey[idempotencyKey]) revert Idempotent();

        // UTC day = unix timestamp / 86400. block.timestamp is UTC in EVM.
        uint256 utcDay = block.timestamp / 86_400;
        uint256 spent = dailySpent[utcDay] + amountUSDCMicros;
        if (spent > dailyCapMicros) revert DailyCapExceeded();

        if (usdc.balanceOf(address(this)) < amountUSDCMicros) revert InsufficientTreasuryReserve();

        tithe = (amountUSDCMicros * titheBps) / BPS_DIVISOR;
        net = amountUSDCMicros - tithe;

        consumedIdempotencyKey[idempotencyKey] = true;
        dailySpent[utcDay] = spent;

        if (tithe > 0) {
            require(usdc.transfer(publicFundSafe, tithe), "tithe transfer failed");
        }
        require(usdc.transfer(recipient, net), "recipient transfer failed");

        emit FiatCredit(idempotencyKey, recipient, amountUSDCMicros, tithe, utcDay);
    }

    // ─── Read accessors ────────────────────────────────────────────────

    function reserveBalanceMicros() external view returns (uint256) {
        return usdc.balanceOf(address(this));
    }

    function remainingDailyCapMicros() external view returns (uint256) {
        uint256 spent = dailySpent[block.timestamp / 86_400];
        return spent >= dailyCapMicros ? 0 : dailyCapMicros - spent;
    }

    function isIdempotencyKeyConsumed(bytes32 key) external view returns (bool) {
        return consumedIdempotencyKey[key];
    }
}
