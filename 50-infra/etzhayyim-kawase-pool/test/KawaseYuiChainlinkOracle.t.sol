// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {IAggregatorV3Kawase, KawaseYuiChainlinkOracle} from "../src/KawaseYuiChainlinkOracle.sol";

interface VmKawase {
    function warp(uint256 timestamp) external;
}

contract KawaseYuiChainlinkOracleTest {
    error AssertFailed(string what);

    VmKawase private constant vm =
        VmKawase(address(uint160(uint256(keccak256("hevm cheat code")))));

    MockAggregator private feed0;
    MockAggregator private feed1;
    MockAggregator private sequencer;
    KawaseYuiChainlinkOracle private oracle;

    function setUp() public {
        vm.warp(10_000);
        feed0 = new MockAggregator(8);
        feed1 = new MockAggregator(18);
        sequencer = new MockAggregator(0);
        feed0.setRound(10, 100_000_000, 9_900, 9_900, 10);
        feed1.setRound(11, 1 ether, 9_900, 9_900, 11);
        sequencer.setRound(5, 0, 5_000, 9_999, 5);
        oracle = new KawaseYuiChainlinkOracle(
            IAggregatorV3Kawase(address(feed0)),
            IAggregatorV3Kawase(address(feed1)),
            IAggregatorV3Kawase(address(sequencer)),
            300,
            300,
            3_600
        );
    }

    function test_normalizes_feed_decimals_and_returns_older_timestamp() public view {
        (uint256 forward, uint256 observedAt) = oracle.latestRateBps(true);
        (uint256 reverse,) = oracle.latestRateBps(false);
        _assertEq(forward, 10_000, "forward par rate");
        _assertEq(reverse, 10_000, "reverse par rate");
        _assertEq(observedAt, 9_900, "older observation");
    }

    function test_cross_rate_is_computed_in_both_directions() public {
        feed1.setRound(12, 80e16, 9_950, 9_950, 12);
        (uint256 forward,) = oracle.latestRateBps(true);
        (uint256 reverse,) = oracle.latestRateBps(false);
        _assertEq(forward, 12_500, "one currency0 buys 1.25 currency1");
        _assertEq(reverse, 8_000, "inverse rate");
    }

    function test_rejects_stale_price() public {
        feed0.setRound(12, 100_000_000, 9_000, 9_000, 12);
        _assertLatestReverts("stale feed refused");
    }

    function test_rejects_non_positive_price() public {
        feed0.setRound(12, -1, 9_990, 9_990, 12);
        _assertLatestReverts("negative feed refused");
    }

    function test_rejects_incomplete_round() public {
        feed0.setRound(12, 100_000_000, 9_990, 9_990, 11);
        _assertLatestReverts("incomplete round refused");
    }

    function test_rejects_sequencer_down() public {
        sequencer.setRound(6, 1, 5_000, 9_999, 6);
        _assertLatestReverts("sequencer down refused");
    }

    function test_rejects_sequencer_recovery_grace_period() public {
        sequencer.setRound(6, 0, 9_500, 9_999, 6);
        _assertLatestReverts("recovery grace enforced");
    }

    function test_rejects_future_sequencer_timestamp() public {
        sequencer.setRound(6, 0, 5_000, 10_001, 6);
        _assertLatestReverts("future sequencer timestamp refused");
    }

    function test_rejects_feed_decimals_change() public {
        feed0.setDecimals(18);
        _assertLatestReverts("feed decimals change refused");
    }

    function test_constructor_requires_nonzero_grace_period() public {
        bool reverted;
        try new KawaseYuiChainlinkOracle(
            IAggregatorV3Kawase(address(feed0)),
            IAggregatorV3Kawase(address(feed1)),
            IAggregatorV3Kawase(address(sequencer)),
            300,
            300,
            0
        ) {
            reverted = false;
        } catch {
            reverted = true;
        }
        if (!reverted) revert AssertFailed("zero grace refused");
    }

    function _assertLatestReverts(string memory what) private {
        (bool ok,) = address(oracle).call(abi.encodeCall(oracle.latestRateBps, (true)));
        if (ok) revert AssertFailed(what);
    }

    function _assertEq(uint256 actual, uint256 expected, string memory what) private pure {
        if (actual != expected) revert AssertFailed(what);
    }
}

contract MockAggregator is IAggregatorV3Kawase {
    uint8 public decimals;
    uint80 private roundId;
    int256 private answer;
    uint256 private startedAt;
    uint256 private updatedAt;
    uint80 private answeredInRound;

    constructor(uint8 _decimals) {
        decimals = _decimals;
    }

    function setDecimals(uint8 value) external {
        decimals = value;
    }

    function setRound(
        uint80 _roundId,
        int256 _answer,
        uint256 _startedAt,
        uint256 _updatedAt,
        uint80 _answeredInRound
    ) external {
        roundId = _roundId;
        answer = _answer;
        startedAt = _startedAt;
        updatedAt = _updatedAt;
        answeredInRound = _answeredInRound;
    }

    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80) {
        return (roundId, answer, startedAt, updatedAt, answeredInRound);
    }
}
