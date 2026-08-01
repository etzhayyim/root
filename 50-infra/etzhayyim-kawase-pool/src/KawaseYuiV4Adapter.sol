// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {KawaseYuiAmmRegistry} from "./KawaseYuiAmmRegistry.sol";

type Currency is address;
type BalanceDelta is int256;

interface IERC20V4Adapter {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

struct PoolKey {
    Currency currency0;
    Currency currency1;
    uint24 fee;
    int24 tickSpacing;
    address hooks;
}

struct SwapParams {
    bool zeroForOne;
    int256 amountSpecified;
    uint160 sqrtPriceLimitX96;
}

interface IPoolManagerV4 {
    function unlock(bytes calldata data) external returns (bytes memory);
    function swap(PoolKey memory key, SwapParams memory params, bytes calldata hookData)
        external
        returns (BalanceDelta);
    function sync(Currency currency) external;
    function settle() external payable returns (uint256 paid);
    function take(Currency currency, address to, uint256 amount) external;
}

interface IKawaseAmmPolicy {
    function validateAmmQuote(
        uint256 executionRateBps,
        uint256 oracleRateBps,
        uint256 quotedAmountOutMinor,
        uint256 minAmountOutMinor,
        uint256 availableAmountOutMinor,
        uint256 lpFeeBps,
        uint256 protocolFeeBps
    ) external pure returns (bool);
}

interface IKawaseRateOracle {
    function latestRateBps(bool zeroForOne)
        external
        view
        returns (uint256 rateBps, uint256 observedAt);
}

/// @title KawaseYuiV4Adapter
/// @notice Exact-input, single-pool Uniswap v4 adapter. It deliberately has no
///         arbitrary multicall, arbitrary hookData, dynamic fee, native token,
///         delegatecall, liquidity management or token rescue surface.
contract KawaseYuiV4Adapter {
    error NotExecutor();
    error NotPoolManager();
    error RegistryRefused();
    error DeadlineExpired();
    error ReentrantCall();
    error UnsupportedCurrency();
    error DynamicFeeForbidden();
    error LpFeeTooHigh(uint256 feeBps);
    error AmountTooLarge();
    error InvalidRecipient();
    error UnexpectedDelta(int128 inputDelta, int128 outputDelta);
    error UnexpectedSettlement(uint256 expected, uint256 paid);
    error TransferFailed(address token);

    uint24 private constant DYNAMIC_FEE_FLAG = 0x800000;
    uint256 private constant BPS_DENOMINATOR = 10_000;

    struct ExactInputRequest {
        address tokenIn;
        uint256 amountIn;
        uint256 minAmountOut;
        uint256 deadline;
        uint160 sqrtPriceLimitX96;
        address recipient;
    }

    struct Settlement {
        bool zeroForOne;
        address tokenOut;
        uint256 amountInUsed;
        uint256 amountOut;
        uint256 executionRateBps;
    }

    IPoolManagerV4 public immutable poolManager;
    KawaseYuiAmmRegistry public immutable registry;
    IKawaseAmmPolicy public immutable policy;
    IKawaseRateOracle public immutable oracle;
    address public immutable executor;
    PoolKey private poolKey;
    bytes32 public immutable poolId;
    uint8 public immutable currency0Decimals;
    uint8 public immutable currency1Decimals;
    bool private entered;
    bool private unlocking;

    event ExactInputExecuted(
        address indexed tokenIn,
        address indexed tokenOut,
        address indexed recipient,
        uint256 amountIn,
        uint256 amountOut,
        uint256 oracleRateBps,
        uint256 oracleObservedAt,
        uint256 executionRateBps
    );

    constructor(
        IPoolManagerV4 _poolManager,
        KawaseYuiAmmRegistry _registry,
        IKawaseAmmPolicy _policy,
        IKawaseRateOracle _oracle,
        address _executor,
        PoolKey memory _poolKey,
        uint8 _currency0Decimals,
        uint8 _currency1Decimals
    ) {
        require(address(_poolManager) != address(0), "manager=0");
        require(address(_registry) != address(0), "registry=0");
        require(address(_policy) != address(0), "policy=0");
        require(address(_oracle) != address(0), "oracle=0");
        require(_executor != address(0), "executor=0");
        require(Currency.unwrap(_poolKey.currency0) < Currency.unwrap(_poolKey.currency1), "order");
        if (
            Currency.unwrap(_poolKey.currency0).code.length == 0
                || Currency.unwrap(_poolKey.currency1).code.length == 0
        ) revert UnsupportedCurrency();
        if ((_poolKey.fee & DYNAMIC_FEE_FLAG) != 0) revert DynamicFeeForbidden();
        if (_poolKey.fee > 3_000) {
            revert LpFeeTooHigh((uint256(_poolKey.fee) + 99) / 100);
        }
        require(_currency0Decimals <= 18 && _currency1Decimals <= 18, "decimals");
        poolManager = _poolManager;
        registry = _registry;
        policy = _policy;
        oracle = _oracle;
        executor = _executor;
        poolKey = _poolKey;
        currency0Decimals = _currency0Decimals;
        currency1Decimals = _currency1Decimals;
        poolId = keccak256(abi.encode(_poolKey));
    }

    function key() external view returns (PoolKey memory) {
        return poolKey;
    }

    function executeExactInput(ExactInputRequest calldata request)
        external
        returns (uint256 amountOut)
    {
        if (msg.sender != executor) revert NotExecutor();
        if (entered) revert ReentrantCall();
        if (block.timestamp > request.deadline) revert DeadlineExpired();
        if (!registry.isAdapterApproved(address(this))) revert RegistryRefused();
        if (!registry.isPoolApproved(poolId, address(poolManager), poolKey.hooks)) {
            revert RegistryRefused();
        }
        if (request.recipient == address(0)) revert InvalidRecipient();
        if (request.amountIn == 0 || request.amountIn > uint256(uint128(type(int128).max))) {
            revert AmountTooLarge();
        }
        address currency0 = Currency.unwrap(poolKey.currency0);
        address currency1 = Currency.unwrap(poolKey.currency1);
        if (request.tokenIn != currency0 && request.tokenIn != currency1) {
            revert UnsupportedCurrency();
        }
        entered = true;
        _safeTransferFrom(request.tokenIn, msg.sender, address(this), request.amountIn);
        unlocking = true;
        bytes memory result = poolManager.unlock(abi.encode(request));
        unlocking = false;
        (uint256 amountInUsed, uint256 received) = abi.decode(result, (uint256, uint256));
        if (amountInUsed < request.amountIn) {
            _safeTransfer(request.tokenIn, msg.sender, request.amountIn - amountInUsed);
        }
        entered = false;
        amountOut = received;
    }

    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        if (msg.sender != address(poolManager)) revert NotPoolManager();
        if (!entered || !unlocking) revert ReentrantCall();
        unlocking = false;
        ExactInputRequest memory request = abi.decode(data, (ExactInputRequest));
        Settlement memory settlement = _swapExactInput(request);
        (uint256 oracleRateBps, uint256 oracleObservedAt) =
            oracle.latestRateBps(settlement.zeroForOne);
        settlement.executionRateBps = _validateQuote(
            request,
            settlement.amountInUsed,
            settlement.amountOut,
            settlement.zeroForOne,
            oracleRateBps
        );

        poolManager.sync(Currency.wrap(request.tokenIn));
        _safeTransfer(request.tokenIn, address(poolManager), settlement.amountInUsed);
        uint256 paid = poolManager.settle();
        if (paid != settlement.amountInUsed) {
            revert UnexpectedSettlement(settlement.amountInUsed, paid);
        }
        poolManager.take(
            Currency.wrap(settlement.tokenOut), request.recipient, settlement.amountOut
        );
        emit ExactInputExecuted(
            request.tokenIn,
            settlement.tokenOut,
            request.recipient,
            settlement.amountInUsed,
            settlement.amountOut,
            oracleRateBps,
            oracleObservedAt,
            settlement.executionRateBps
        );
        return abi.encode(settlement.amountInUsed, settlement.amountOut);
    }

    function _swapExactInput(ExactInputRequest memory request)
        private
        returns (Settlement memory settlement)
    {
        settlement.zeroForOne = request.tokenIn == Currency.unwrap(poolKey.currency0);
        settlement.tokenOut = settlement.zeroForOne
            ? Currency.unwrap(poolKey.currency1)
            : Currency.unwrap(poolKey.currency0);
        BalanceDelta wrapped = poolManager.swap(
            poolKey,
            SwapParams({
                zeroForOne: settlement.zeroForOne,
                amountSpecified: -int256(request.amountIn),
                sqrtPriceLimitX96: request.sqrtPriceLimitX96
            }),
            bytes("")
        );
        int256 raw = BalanceDelta.unwrap(wrapped);
        int128 amount0 = int128(raw >> 128);
        int128 amount1 = int128(raw);
        int128 inputDelta = settlement.zeroForOne ? amount0 : amount1;
        int128 outputDelta = settlement.zeroForOne ? amount1 : amount0;
        if (inputDelta >= 0 || outputDelta <= 0) {
            revert UnexpectedDelta(inputDelta, outputDelta);
        }
        settlement.amountInUsed = uint256(uint128(-inputDelta));
        settlement.amountOut = uint256(uint128(outputDelta));
        if (settlement.amountInUsed > request.amountIn) revert AmountTooLarge();
    }

    function _validateQuote(
        ExactInputRequest memory request,
        uint256 amountInUsed,
        uint256 amountOut,
        bool zeroForOne,
        uint256 oracleRateBps
    ) private view returns (uint256 executionRateBps) {
        executionRateBps = _executionRateBps(amountInUsed, amountOut, zeroForOne);
        policy.validateAmmQuote(
            executionRateBps,
            oracleRateBps,
            amountOut,
            request.minAmountOut,
            amountOut,
            uint256(poolKey.fee) / 100,
            0
        );
    }

    function _executionRateBps(uint256 amountIn, uint256 amountOut, bool zeroForOne)
        private
        view
        returns (uint256)
    {
        uint8 inDecimals = zeroForOne ? currency0Decimals : currency1Decimals;
        uint8 outDecimals = zeroForOne ? currency1Decimals : currency0Decimals;
        if (inDecimals >= outDecimals) {
            return amountOut * (10 ** (inDecimals - outDecimals)) * BPS_DENOMINATOR / amountIn;
        }
        return amountOut * BPS_DENOMINATOR / (amountIn * (10 ** (outDecimals - inDecimals)));
    }

    function _safeTransfer(address token, address to, uint256 amount) private {
        (bool ok, bytes memory result) =
            token.call(abi.encodeCall(IERC20V4Adapter.transfer, (to, amount)));
        if (!ok || (result.length != 0 && (result.length != 32 || !abi.decode(result, (bool))))) {
            revert TransferFailed(token);
        }
    }

    function _safeTransferFrom(address token, address from, address to, uint256 amount) private {
        (bool ok, bytes memory result) =
            token.call(abi.encodeCall(IERC20V4Adapter.transferFrom, (from, to, amount)));
        if (!ok || (result.length != 0 && (result.length != 32 || !abi.decode(result, (bool))))) {
            revert TransferFailed(token);
        }
    }
}
