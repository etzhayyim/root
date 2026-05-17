// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title Postage
 * @notice On-chain postage for app.openmail.message records. Per ADR-2605172200.
 *
 *         A sender pays `rateUsdcPerRecipient * recipientCount` in USDC to the
 *         treasury and emits a Paid event whose `messageHash` indexed parameter
 *         binds the payment to one specific MST record. AppView indexers reject
 *         openmail records whose `postage.txHash` doesn't resolve to a Paid
 *         event whose `messageHash` matches the record's canonical CBOR hash.
 *
 * @dev    Stateless beyond rate + owner + treasury. History lives in the event
 *         log; the chain itself is the canonical record. Same design ethos as
 *         CheckpointAnchor.sol (ADR-2605171800).
 *
 *         Owner = etzhayyim treasury Safe (multisig, ADR-2605172100). Can:
 *         - setRate: adjust per-recipient USDC rate
 *         - setOwner: rotate the Safe address
 *
 *         NO pause. NO proxy. NO upgrade. To change policy beyond rate, deploy
 *         a new Postage at a new address and update the SDK / AppView config.
 *
 *         USDC and treasury are immutable. To migrate either, redeploy.
 */

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract Postage {
    /// @notice USDC contract used for payments (Base mainnet: 0x833...DCa6).
    IERC20 public immutable usdc;

    /// @notice Recipient of all postage payments (etzhayyim treasury Safe).
    address public immutable treasury;

    /// @notice USDC amount per recipient in USDC base units (6 decimals).
    ///         e.g. 10_000 = 0.01 USDC. Adjustable by owner.
    uint256 public rateUsdcPerRecipient;

    /// @notice Admin Safe authorized to set rate and rotate ownership.
    address public owner;

    /// @notice Emitted on every successful postage payment. Indexed by sender
    ///         and messageHash so AppViews can efficiently look up by either.
    /// @param sender         The msg.sender that paid (EOA or ERC-4337 SCA).
    /// @param messageHash    keccak256 of the canonical CBOR encoding of the
    ///                       parent message record with `postage` elided.
    /// @param recipientCount How many recipients this payment covers (1-100).
    /// @param amount         USDC base units transferred to treasury.
    /// @param paidAtMs       block.timestamp * 1000 (millisecond-precision ts).
    event Paid(
        address indexed sender,
        bytes32 indexed messageHash,
        uint16  recipientCount,
        uint256 amount,
        uint64  paidAtMs
    );

    event RateUpdated(uint256 oldRate, uint256 newRate);
    event OwnerRotated(address indexed oldOwner, address indexed newOwner);

    error NotOwner();
    error BadRecipientCount(uint16 recipientCount);
    error TransferFailed();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(IERC20 _usdc, address _treasury, uint256 _initialRate) {
        usdc = _usdc;
        treasury = _treasury;
        rateUsdcPerRecipient = _initialRate;
        owner = msg.sender;
    }

    // ─── Public API ──────────────────────────────────────────────────

    /// @notice Pay postage for one openmail message.
    /// @dev    Caller MUST have approved at least `rate * recipientCount`
    ///         USDC to this contract beforehand.
    function payPostage(bytes32 messageHash, uint16 recipientCount) external {
        if (recipientCount == 0 || recipientCount > 100) {
            revert BadRecipientCount(recipientCount);
        }
        uint256 amount = rateUsdcPerRecipient * recipientCount;
        bool ok = usdc.transferFrom(msg.sender, treasury, amount);
        if (!ok) revert TransferFailed();
        emit Paid(
            msg.sender,
            messageHash,
            recipientCount,
            amount,
            uint64(block.timestamp * 1000)
        );
    }

    // ─── Admin (owner = treasury Safe) ───────────────────────────────

    function setRate(uint256 newRate) external onlyOwner {
        emit RateUpdated(rateUsdcPerRecipient, newRate);
        rateUsdcPerRecipient = newRate;
    }

    function setOwner(address newOwner) external onlyOwner {
        address old = owner;
        owner = newOwner;
        emit OwnerRotated(old, newOwner);
    }
}
