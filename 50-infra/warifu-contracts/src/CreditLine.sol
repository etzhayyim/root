// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
pragma solidity ^0.8.26;

/// @title CreditLine — interest-free (qard ḥasan) credit for warifu cards (ADR-2605302000)
/// @notice 0% interest, no profit-bearing late fee. Limits are underwritten by the `wakai`
///         mutual-aid float + SBT reputation. Default handling is L3 評価 penalty + wakai
///         absorption — NOT penalty interest. Settlement asset is USDC on Base L2.
/// @dev R0 scaffold.
contract CreditLine {
    // --- constitutional invariant -----------------------------------------------------
    uint16 public constant INTEREST_BPS = 0;     // riba-free (immutable)
    uint16 public constant LATE_FEE_BPS = 0;     // no profit-bearing penalty

    address public wakai;    // mutual-aid float source/backstop (ADR-2605263500)
    address public router;   // SettlementRouter (only caller allowed to draw/repay)
    address public council;  // Lv6+ multisig

    struct Line {
        uint256 limit;       // approved limit (USDC minor units)
        uint256 outstanding; // currently drawn
    }

    mapping(address => Line) public lines; // smartAccount => Line

    error NotRouter();
    error NotCouncil();
    error OverLimit();
    error Overpay();

    constructor(address _wakai, address _council) {
        wakai = _wakai;
        council = _council;
    }

    modifier onlyRouter() {
        if (msg.sender != router) revert NotRouter();
        _;
    }

    modifier onlyCouncil() {
        if (msg.sender != council) revert NotCouncil();
        _;
    }

    function setRouter(address _router) external onlyCouncil {
        router = _router;
    }

    /// @notice Set/adjust an account's interest-free limit (wakai-underwritten).
    function setLimit(address account, uint256 limit) external onlyCouncil {
        lines[account].limit = limit;
    }

    /// @notice Draw against the line for a settlement. 0% — outstanding rises by exactly `amount`.
    function draw(address account, uint256 amount) external onlyRouter {
        Line storage l = lines[account];
        if (l.outstanding + amount > l.limit) revert OverLimit();
        l.outstanding += amount; // no interest accrual, ever
    }

    /// @notice Repay outstanding principal. No fee, no interest.
    function repay(address account, uint256 amount) external onlyRouter {
        Line storage l = lines[account];
        if (amount > l.outstanding) revert Overpay();
        l.outstanding -= amount;
    }

    function available(address account) external view returns (uint256) {
        Line storage l = lines[account];
        return l.limit - l.outstanding;
    }
}
