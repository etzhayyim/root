// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

interface IAggregatorV3Kawase {
    function decimals() external view returns (uint8);
    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );
}

/// @title KawaseYuiChainlinkOracle
/// @notice Computes a currency0/currency1 cross-rate from two Chainlink feeds
///         and refuses stale, incomplete or L2-sequencer-unsafe observations.
contract KawaseYuiChainlinkOracle {
    error ZeroAddress();
    error InvalidMaxAge();
    error InvalidGracePeriod();
    error UnsupportedDecimals(uint8 decimals);
    error FeedDecimalsChanged(address feed, uint8 expected, uint8 actual);
    error InvalidRound(address feed, uint80 roundId, uint80 answeredInRound);
    error InvalidAnswer(address feed, int256 answer);
    error InvalidTimestamp(address feed, uint256 updatedAt);
    error StaleAnswer(address feed, uint256 age, uint256 maximumAge);
    error SequencerDown();
    error SequencerGracePeriod(uint256 elapsed, uint256 required);
    error AnswerTooLarge(address feed);

    uint256 private constant BPS_DENOMINATOR = 10_000;
    uint8 private constant NORMALIZED_DECIMALS = 18;

    IAggregatorV3Kawase public immutable currency0Feed;
    IAggregatorV3Kawase public immutable currency1Feed;
    IAggregatorV3Kawase public immutable sequencerUptimeFeed;
    uint256 public immutable currency0MaxAge;
    uint256 public immutable currency1MaxAge;
    uint256 public immutable sequencerGracePeriod;
    uint8 public immutable currency0FeedDecimals;
    uint8 public immutable currency1FeedDecimals;

    constructor(
        IAggregatorV3Kawase _currency0Feed,
        IAggregatorV3Kawase _currency1Feed,
        IAggregatorV3Kawase _sequencerUptimeFeed,
        uint256 _currency0MaxAge,
        uint256 _currency1MaxAge,
        uint256 _sequencerGracePeriod
    ) {
        if (
            address(_currency0Feed) == address(0) || address(_currency1Feed) == address(0)
                || address(_sequencerUptimeFeed) == address(0)
        ) revert ZeroAddress();
        if (_currency0MaxAge == 0 || _currency1MaxAge == 0) revert InvalidMaxAge();
        if (_sequencerGracePeriod == 0) revert InvalidGracePeriod();
        uint8 decimals0 = _currency0Feed.decimals();
        uint8 decimals1 = _currency1Feed.decimals();
        if (decimals0 > NORMALIZED_DECIMALS) revert UnsupportedDecimals(decimals0);
        if (decimals1 > NORMALIZED_DECIMALS) revert UnsupportedDecimals(decimals1);
        currency0Feed = _currency0Feed;
        currency1Feed = _currency1Feed;
        sequencerUptimeFeed = _sequencerUptimeFeed;
        currency0MaxAge = _currency0MaxAge;
        currency1MaxAge = _currency1MaxAge;
        sequencerGracePeriod = _sequencerGracePeriod;
        currency0FeedDecimals = decimals0;
        currency1FeedDecimals = decimals1;
    }

    /// @return rateBps 10_000 means one input unit per output unit.
    /// @return observedAt The older of the two price observations.
    function latestRateBps(bool zeroForOne)
        external
        view
        returns (uint256 rateBps, uint256 observedAt)
    {
        _requireSequencerHealthy();
        (uint256 price0, uint256 updated0) =
            _readPrice(currency0Feed, currency0FeedDecimals, currency0MaxAge);
        (uint256 price1, uint256 updated1) =
            _readPrice(currency1Feed, currency1FeedDecimals, currency1MaxAge);
        uint256 numerator = zeroForOne ? price0 : price1;
        uint256 denominator = zeroForOne ? price1 : price0;
        address numeratorFeed = zeroForOne ? address(currency0Feed) : address(currency1Feed);
        if (numerator > type(uint256).max / BPS_DENOMINATOR) {
            revert AnswerTooLarge(numeratorFeed);
        }
        rateBps = numerator * BPS_DENOMINATOR / denominator;
        observedAt = updated0 < updated1 ? updated0 : updated1;
    }

    function _requireSequencerHealthy() private view {
        (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        ) = sequencerUptimeFeed.latestRoundData();
        if (roundId == 0 || answeredInRound < roundId) {
            revert InvalidRound(address(sequencerUptimeFeed), roundId, answeredInRound);
        }
        if (
            updatedAt == 0 || updatedAt > block.timestamp || startedAt == 0
                || startedAt > block.timestamp
        ) {
            revert InvalidTimestamp(address(sequencerUptimeFeed), updatedAt);
        }
        if (answer != 0) revert SequencerDown();
        uint256 elapsed = block.timestamp - startedAt;
        if (elapsed <= sequencerGracePeriod) {
            revert SequencerGracePeriod(elapsed, sequencerGracePeriod);
        }
    }

    function _readPrice(IAggregatorV3Kawase feed, uint8 feedDecimals, uint256 maximumAge)
        private
        view
        returns (uint256 normalizedPrice, uint256 updatedAt)
    {
        uint8 currentDecimals = feed.decimals();
        if (currentDecimals != feedDecimals) {
            revert FeedDecimalsChanged(address(feed), feedDecimals, currentDecimals);
        }
        (uint80 roundId, int256 answer,, uint256 timestamp, uint80 answeredInRound) =
            feed.latestRoundData();
        if (roundId == 0 || answeredInRound < roundId) {
            revert InvalidRound(address(feed), roundId, answeredInRound);
        }
        if (answer <= 0) revert InvalidAnswer(address(feed), answer);
        if (timestamp == 0 || timestamp > block.timestamp) {
            revert InvalidTimestamp(address(feed), timestamp);
        }
        uint256 age = block.timestamp - timestamp;
        if (age > maximumAge) revert StaleAnswer(address(feed), age, maximumAge);
        uint256 scale = 10 ** (NORMALIZED_DECIMALS - feedDecimals);
        if (uint256(answer) > type(uint256).max / scale) {
            revert AnswerTooLarge(address(feed));
        }
        normalizedPrice = uint256(answer) * scale;
        updatedAt = timestamp;
    }
}
