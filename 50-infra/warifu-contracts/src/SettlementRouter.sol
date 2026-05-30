// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
pragma solidity ^0.8.26;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
}

interface ICreditLine {
    function draw(address account, uint256 amount) external;
    function repay(address account, uint256 amount) external;
}

/// @title SettlementRouter — zero-fee T+0 USDC settlement for warifu (ADR-2605302000)
/// @notice Merchant fee is ALWAYS 0 (決済手数料ゼロ). Gas is sponsored by etzhayyim-paymaster
///         (ERC-4337). Enforces the payment-purpose allow-list: Phase 1 = SBT↔SBT carve-out
///         only; external `purchase`/`subscription` are GATED until the Council Lv7+ amendment
///         of ADR-2605192115 (phase2Enabled).
/// @dev R0 scaffold. Holds no float of its own; debit pulls from holder smart account,
///      credit draws the wakai float via CreditLine.
contract SettlementRouter {
    uint16 public constant MERCHANT_FEE_BPS = 0; // immutable invariant

    IERC20 public immutable usdc;
    ICreditLine public creditLine;
    address public wakaiFloat; // source of credit-funded settlements
    address public council;    // Lv6+ multisig (ops), Lv7+ required to flip phase2

    bool public phase2Enabled; // external purchase/subscription gate (default false)

    // purpose => allowed (Phase 1 set true in constructor)
    mapping(bytes32 => bool) public phase1Purpose;

    event Settled(bytes32 indexed authId, address indexed merchant, uint256 amount, string funding);
    event Phase2Enabled(bytes32 adrAmendmentRecord);

    error NotCouncil();
    error PurposeGated();
    error PurposeNotAllowed();
    error Reentrancy();

    bool private _entered; // reentrancy guard

    constructor(address _usdc, address _creditLine, address _wakaiFloat, address _council) {
        usdc = IERC20(_usdc);
        creditLine = ICreditLine(_creditLine);
        wakaiFloat = _wakaiFloat;
        council = _council;
        // Phase 1 charter-clean purposes (ADR-2605192115 SBT↔SBT carve-out + escrow-refund).
        phase1Purpose[keccak256("internal-purchase")] = true;
        phase1Purpose[keccak256("internal-subscription")] = true;
        phase1Purpose[keccak256("internal-promo")] = true;
        phase1Purpose[keccak256("escrow-refund")] = true;
    }

    modifier onlyCouncil() {
        if (msg.sender != council) revert NotCouncil();
        _;
    }

    /// @dev Blocks re-entry via a malicious/hook token during transferFrom.
    modifier nonReentrant() {
        if (_entered) revert Reentrancy();
        _entered = true;
        _;
        _entered = false;
    }

    /// @dev Records the on-chain ADR-2605192115 amendment hash; must be set by Lv7+ multisig
    ///      (the `council` address MUST be the Lv7+ Safe for this call to be legitimate).
    function enablePhase2(bytes32 adrAmendmentRecord) external onlyCouncil {
        phase2Enabled = true;
        emit Phase2Enabled(adrAmendmentRecord);
    }

    function _checkPurpose(string calldata purpose) internal view {
        bytes32 p = keccak256(bytes(purpose));
        if (phase1Purpose[p]) return;
        // external commercial purposes
        if (p == keccak256("purchase") || p == keccak256("subscription")) {
            if (!phase2Enabled) revert PurposeGated();
            return;
        }
        revert PurposeNotAllowed();
    }

    /// @notice Settle a debit transaction: pull USDC from holder smart account to merchant.
    /// @dev Holder smart account must have approved this router (ERC-4337 session/approval).
    function settleDebit(
        bytes32 authId,
        address holder,
        address merchant,
        uint256 amount,
        string calldata purpose
    ) external nonReentrant {
        _checkPurpose(purpose);
        // fee = 0: merchant receives exactly `amount`.
        require(usdc.transferFrom(holder, merchant, amount), "usdc transfer failed");
        emit Settled(authId, merchant, amount, "debit");
    }

    /// @notice Settle a credit transaction: draw the wakai float (0%) and pay merchant.
    function settleCredit(
        bytes32 authId,
        address holder,
        address merchant,
        uint256 amount,
        string calldata purpose
    ) external nonReentrant {
        _checkPurpose(purpose);
        creditLine.draw(holder, amount); // 0% interest
        require(usdc.transferFrom(wakaiFloat, merchant, amount), "wakai transfer failed");
        emit Settled(authId, merchant, amount, "credit");
    }
}
