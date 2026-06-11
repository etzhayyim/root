// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2605192130 (10% Tithe Redistribution).
// Routes donation/grant tx: 90% recipient + 10% Public Fund Safe, atomic split.

pragma solidity 0.8.27;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

interface IConstitution {
    function getConstant(bytes32 key) external view returns (bytes32);
    function getMutable(bytes32 key) external view returns (bytes32);
}

interface IChartersComplianceRegistry {
    function isNonAlignedAddress(address subject) external view returns (bool);
}

contract TitheRouter {
    IERC20 public immutable usdc;
    IConstitution public immutable constitution;
    IChartersComplianceRegistry public immutable charters;
    /// @notice Public Fund Safe address. Bootstrap-immutable for v0 deploy
    ///         (avoids the circular dependency: Constitution mutables can
    ///         only be set after Governance is bound, which deploys after
    ///         TitheRouter). v1 will read from Constitution.getMutable
    ///         ("public_fund.safe_address") once the deployment sequence
    ///         is reorganised via CREATE2 prediction.
    address public immutable publicFund;

    /// @notice The tithe RATE (init 1000 bps = 10%). Per ADR-2606062100 §4 this is
    ///         now a Tier-2 MUTABLE (`tithe_bps`) governed within the Tier-0
    ///         [tithe_floor_bps, tithe_ceiling_bps] = [500, 2000] band — the
    ///         priority "redistribution exists" is the constant, the rate is tunable.
    bytes32 public constant TITHE_BPS_KEY = keccak256("tithe_bps");
    /// @notice ADR-2605192100 §2 mutable (governance-set at deploy + timelock).
    bytes32 public constant PUBLIC_FUND_ADDRESS_KEY = keccak256("public_fund.safe_address");
    uint256 public constant BPS_DENOMINATOR = 10_000;

    event Routed(
        address indexed payer,
        address indexed recipient,
        uint256 grossAmount,
        uint256 titheAmount,
        uint256 netAmount,
        bytes32 indexed purpose
    );

    error ZeroAmount();
    error PurposeNotTitheable(bytes32 purpose);
    error PayerCharterNonCompliant(address payer);
    error RecipientCharterNonCompliant(address recipient);

    constructor(
        IERC20 _usdc,
        IConstitution _constitution,
        IChartersComplianceRegistry _charters,
        address _publicFund
    ) {
        require(_publicFund != address(0), "TitheRouter: publicFund=0");
        usdc = _usdc;
        constitution = _constitution;
        charters = _charters;
        publicFund = _publicFund;
    }

    function route(address recipient, uint256 grossAmount, bytes32 purpose)
        external
        returns (uint256 titheAmount, uint256 netAmount)
    {
        if (grossAmount == 0) revert ZeroAmount();
        if (!_isTitheablePurpose(purpose)) revert PurposeNotTitheable(purpose);
        if (charters.isNonAlignedAddress(msg.sender)) revert PayerCharterNonCompliant(msg.sender);
        if (charters.isNonAlignedAddress(recipient)) revert RecipientCharterNonCompliant(recipient);

        // Constitution returns bytes32; cast to uint256 per ADR-2605172300 idiom.
        // TODO(v1): read publicFund from constitution.getMutable(PUBLIC_FUND_ADDRESS_KEY)
        //          once CREATE2-based deploy sequencing wires the address before
        //          TitheRouter construction.
        uint256 titheBps = uint256(constitution.getMutable(TITHE_BPS_KEY));

        titheAmount = (grossAmount * titheBps) / BPS_DENOMINATOR;
        netAmount = grossAmount - titheAmount;

        usdc.transferFrom(msg.sender, publicFund, titheAmount);
        usdc.transferFrom(msg.sender, recipient, netAmount);

        emit Routed(msg.sender, recipient, grossAmount, titheAmount, netAmount, purpose);
    }

    function _isTitheablePurpose(bytes32 purpose) internal pure returns (bool) {
        return purpose == keccak256("donation");
        // NOTE: "kisha" / "tithe" / "escrow-refund" / "grant" / "internal-*" are
        // explicitly NOT titheable — see TitheRouter README + ADR-2605192130 §5.
    }
}
