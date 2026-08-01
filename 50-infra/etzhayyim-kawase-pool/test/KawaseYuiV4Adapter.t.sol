// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {KawaseYuiAmmRegistry} from "../src/KawaseYuiAmmRegistry.sol";
import {
    BalanceDelta,
    Currency,
    IKawaseAmmPolicy,
    IKawaseRateOracle,
    IPoolManagerV4,
    KawaseYuiV4Adapter,
    PoolKey,
    SwapParams
} from "../src/KawaseYuiV4Adapter.sol";

contract KawaseYuiV4AdapterTest {
    error AssertFailed(string what);

    MockAdapterToken private currency0;
    MockAdapterToken private currency1;
    MockV4PoolManager private manager;
    MockBoundedPolicy private policy;
    MockRateOracle private oracle;
    KawaseYuiAmmRegistry private registry;
    KawaseYuiV4Adapter private adapter;

    function setUp() public {
        MockAdapterToken a = new MockAdapterToken();
        MockAdapterToken b = new MockAdapterToken();
        (currency0, currency1) = address(a) < address(b) ? (a, b) : (b, a);
        manager = new MockV4PoolManager();
        policy = new MockBoundedPolicy();
        oracle = new MockRateOracle();
        registry = new KawaseYuiAmmRegistry(address(this));
        PoolKey memory key = PoolKey({
            currency0: Currency.wrap(address(currency0)),
            currency1: Currency.wrap(address(currency1)),
            fee: 3_000,
            tickSpacing: 60,
            hooks: address(0)
        });
        adapter = new KawaseYuiV4Adapter(
            IPoolManagerV4(address(manager)),
            registry,
            IKawaseAmmPolicy(address(policy)),
            IKawaseRateOracle(address(oracle)),
            address(this),
            key,
            6,
            6
        );
        registry.approveAdapter(address(adapter));
        registry.approvePool(adapter.poolId(), address(manager), address(0), 0);
        currency0.mint(address(this), 2_000_000);
        currency1.mint(address(manager), 2_000_000);
        currency0.approve(address(adapter), type(uint256).max);
    }

    function test_exact_input_uses_unlock_swap_settle_take() public {
        uint256 beforeOut = currency1.balanceOf(address(this));
        uint256 amountOut = adapter.executeExactInput(_request(block.timestamp + 60));

        _assertEq(amountOut, 997_000, "amount out");
        _assertEq(currency0.balanceOf(address(this)), 1_000_000, "input debited");
        _assertEq(currency1.balanceOf(address(this)) - beforeOut, 997_000, "output taken");
        _assertEq(manager.unlockCount(), 1, "one unlock");
        _assertEq(manager.swapCount(), 1, "one swap");
        _assertEq(manager.settleCount(), 1, "one settle");
        _assertEq(manager.takeCount(), 1, "one take");
    }

    function test_registry_pause_stops_execution_before_token_transfer() public {
        registry.setPaused(true);
        uint256 beforeIn = currency0.balanceOf(address(this));
        (bool ok,) = address(adapter)
            .call(abi.encodeCall(adapter.executeExactInput, (_request(block.timestamp + 60))));
        _assertTrue(!ok, "paused registry refused");
        _assertEq(currency0.balanceOf(address(this)), beforeIn, "no token movement");
        _assertEq(manager.unlockCount(), 0, "no unlock");
    }

    function test_expired_request_stops_execution() public {
        (bool ok,) = address(adapter).call(abi.encodeCall(adapter.executeExactInput, (_request(0))));
        _assertTrue(!ok, "expired request refused");
        _assertEq(manager.unlockCount(), 0, "no unlock");
    }

    function test_revoked_pool_stops_execution() public {
        registry.revokePool(adapter.poolId());
        (bool ok,) = address(adapter)
            .call(abi.encodeCall(adapter.executeExactInput, (_request(block.timestamp + 60))));
        _assertTrue(!ok, "revoked pool refused");
        _assertEq(manager.unlockCount(), 0, "no unlock");
    }

    function test_unlock_callback_can_only_be_consumed_once() public {
        manager.setDoubleCallback(true);
        uint256 beforeIn = currency0.balanceOf(address(this));
        (bool ok,) = address(adapter)
            .call(abi.encodeCall(adapter.executeExactInput, (_request(block.timestamp + 60))));
        _assertTrue(!ok, "second callback refused");
        _assertEq(currency0.balanceOf(address(this)), beforeIn, "transaction rolled back");
    }

    function test_registry_rejects_eoa_as_reviewed_runtime() public {
        (bool ok,) =
            address(registry).call(abi.encodeCall(registry.approveAdapter, (address(0xBEEF))));
        _assertTrue(!ok, "EOA has no reviewed runtime");
    }

    function test_safety_observer_can_pause_on_protocol_fee_mismatch() public {
        registry.setSafetyObserver(address(this), true);
        registry.reportProtocolFeeMismatch(adapter.poolId(), 1);
        _assertTrue(registry.paused(), "mismatch pauses registry");
    }

    function test_safety_observer_cannot_report_zero_fee_as_mismatch() public {
        registry.setSafetyObserver(address(this), true);
        (bool ok,) = address(registry)
            .call(abi.encodeCall(registry.reportProtocolFeeMismatch, (adapter.poolId(), 0)));
        _assertTrue(!ok, "zero is not a mismatch");
        _assertTrue(!registry.paused(), "registry remains available");
    }

    function test_constructor_rejects_fractional_fee_above_30_bps() public {
        PoolKey memory key = PoolKey({
            currency0: Currency.wrap(address(currency0)),
            currency1: Currency.wrap(address(currency1)),
            fee: 3_001,
            tickSpacing: 60,
            hooks: address(0)
        });
        bool reverted;
        try new KawaseYuiV4Adapter(
            IPoolManagerV4(address(manager)),
            registry,
            IKawaseAmmPolicy(address(policy)),
            IKawaseRateOracle(address(oracle)),
            address(this),
            key,
            6,
            6
        ) {
            reverted = false;
        } catch {
            reverted = true;
        }
        _assertTrue(reverted, "30.01 bps refused");
    }

    function _request(uint256 deadline)
        private
        view
        returns (KawaseYuiV4Adapter.ExactInputRequest memory)
    {
        return KawaseYuiV4Adapter.ExactInputRequest({
            tokenIn: address(currency0),
            amountIn: 1_000_000,
            minAmountOut: 996_000,
            deadline: deadline,
            sqrtPriceLimitX96: 1,
            recipient: address(this)
        });
    }

    function _assertTrue(bool condition, string memory what) private pure {
        if (!condition) revert AssertFailed(what);
    }

    function _assertEq(uint256 actual, uint256 expected, string memory what) private pure {
        if (actual != expected) revert AssertFailed(what);
    }
}

contract MockRateOracle is IKawaseRateOracle {
    function latestRateBps(bool) external view returns (uint256 rateBps, uint256 observedAt) {
        return (10_000, block.timestamp);
    }
}

contract MockAdapterToken {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address account, uint256 amount) external {
        balanceOf[account] += amount;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        uint256 approved = allowance[from][msg.sender];
        require(approved >= amount, "allowance");
        if (approved != type(uint256).max) allowance[from][msg.sender] = approved - amount;
        _transfer(from, to, amount);
        return true;
    }

    function _transfer(address from, address to, uint256 amount) private {
        require(balanceOf[from] >= amount, "balance");
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
    }
}

contract MockBoundedPolicy is IKawaseAmmPolicy {
    function validateAmmQuote(
        uint256 executionRateBps,
        uint256 oracleRateBps,
        uint256 quotedAmountOutMinor,
        uint256 minAmountOutMinor,
        uint256 availableAmountOutMinor,
        uint256 lpFeeBps,
        uint256 protocolFeeBps
    ) external pure returns (bool) {
        require(oracleRateBps != 0, "oracle");
        uint256 impact = executionRateBps > oracleRateBps
            ? executionRateBps - oracleRateBps
            : oracleRateBps - executionRateBps;
        require(impact * 10_000 <= oracleRateBps * 50, "impact");
        require(quotedAmountOutMinor >= minAmountOutMinor, "min-out");
        require(quotedAmountOutMinor <= availableAmountOutMinor, "liquidity");
        require(lpFeeBps <= 30, "lp-fee");
        require(protocolFeeBps == 0, "protocol-fee");
        return true;
    }
}

contract MockV4PoolManager is IPoolManagerV4 {
    uint256 public unlockCount;
    uint256 public swapCount;
    uint256 public settleCount;
    uint256 public takeCount;
    uint256 private amountOwed;
    bool private doubleCallback;

    function setDoubleCallback(bool value) external {
        doubleCallback = value;
    }

    function unlock(bytes calldata data) external returns (bytes memory) {
        unlockCount++;
        (bool ok, bytes memory result) =
            msg.sender.call(abi.encodeWithSignature("unlockCallback(bytes)", data));
        require(ok, "callback");
        if (doubleCallback) {
            (ok,) = msg.sender.call(abi.encodeWithSignature("unlockCallback(bytes)", data));
            require(ok, "second callback");
        }
        return abi.decode(result, (bytes));
    }

    function swap(PoolKey memory, SwapParams memory params, bytes calldata hookData)
        external
        returns (BalanceDelta)
    {
        require(hookData.length == 0, "hookData");
        require(params.amountSpecified < 0, "exact-input");
        swapCount++;
        uint256 amountIn = uint256(-params.amountSpecified);
        uint256 amountOut = amountIn * 997 / 1_000;
        amountOwed = amountIn;
        int128 input = -int128(int256(amountIn));
        int128 output = int128(int256(amountOut));
        int128 amount0 = params.zeroForOne ? input : output;
        int128 amount1 = params.zeroForOne ? output : input;
        int256 packed = (int256(amount0) << 128) | int256(uint256(uint128(amount1)));
        return BalanceDelta.wrap(packed);
    }

    function sync(Currency) external {}

    function settle() external payable returns (uint256 paid) {
        settleCount++;
        paid = amountOwed;
        amountOwed = 0;
    }

    function take(Currency currency, address to, uint256 amount) external {
        takeCount++;
        MockAdapterToken(Currency.unwrap(currency)).transfer(to, amount);
    }
}
