// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2605192130 (10% Tithe Redistribution).
// Routes donation/grant tx: 90% recipient + 10% Public Fund Safe, atomic split.

pragma solidity ^0.8.24;

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

    /// @notice ADR-2605192100 §2 constitutional constant (immutable, = 1000 bps).
    bytes32 public constant TITHE_BPS_KEY = keccak256("economic.tithe_to_public_fund_bps");
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

    constructor(IERC20 _usdc, IConstitution _constitution, IChartersComplianceRegistry _charters) {
        usdc = _usdc;
        constitution = _constitution;
        charters = _charters;
    }

    function route(address recipient, uint256 grossAmount, bytes32 purpose)
        external
        returns (uint256 titheAmount, uint256 netAmount)
    {
        if (grossAmount == 0) revert ZeroAmount();
        if (!_isTitheablePurpose(purpose)) revert PurposeNotTitheable(purpose);
        if (charters.isNonAlignedAddress(msg.sender)) revert PayerCharterNonCompliant(msg.sender);
        if (charters.isNonAlignedAddress(recipient)) revert RecipientCharterNonCompliant(recipient);

        // Constitution returns bytes32; cast to uint256/address per ADR-2605172300 idiom.
        uint256 titheBps = uint256(constitution.getConstant(TITHE_BPS_KEY));
        address publicFund = address(uint160(uint256(constitution.getMutable(PUBLIC_FUND_ADDRESS_KEY))));
        require(publicFund != address(0), "TitheRouter: public_fund.safe_address not wired");

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
