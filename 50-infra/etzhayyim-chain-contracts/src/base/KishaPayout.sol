// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title KishaPayout
 * @notice Base L2 settlement contract for kisha claim tickets issued
 *         on geth-private by {KishaStream}. Pulls USDC from the Treasury
 *         Safe and forwards it to the adherent's Base recipient address.
 *
 * @dev Lives on Base L2 (NOT on geth-private). Per ADR-2605172300 §5
 *      and ADR-2605172100. Apache-2.0.
 *
 *      Flow:
 *
 *        1. Adherent calls {KishaStream.claim} on geth-private.
 *        2. KishaStream emits ClaimTicketIssued(ticketId, ...).
 *        3. An off-chain relayer (officer-controlled) signs a
 *           Fulfillment payload referencing the ticket and submits
 *           {fulfill} on Base.
 *        4. {fulfill} verifies the relayer signature, marks ticketId
 *           as fulfilled (preventing double-pay), then transfers USDC
 *           from the Treasury Safe to baseRecipient via
 *           IERC20.transferFrom.
 *        5. Emits {Fulfilled} as the public audit record. The SDK
 *           writes com.etzhayyim.apps.payment.kisha referencing this tx.
 *
 *      The Treasury Safe MUST have pre-approved this contract for the
 *      USDC allowance it intends to make claimable. Allowance budgets
 *      the monthly kisha envelope.
 *
 *      Security:
 *        - Sole authentication = the signer set ("relayers") whose
 *          M-of-N signatures are accepted by {fulfill}. Compromise of
 *          M keys = full drain of approved allowance. Mitigations:
 *            (a) Treasury Safe sets a conservative allowance ceiling;
 *            (b) relayer set is itself a multisig of officers;
 *            (c) anomaly detection on payout volume off-chain.
 *        - Replay protection via fulfilled[ticketId] set, populated
 *          by ticketId from {KishaStream}: keccak256(stream, tokenId, seq).
 *        - No upgrade. No admin. To rotate the relayer set, deploy a
 *          new KishaPayout and migrate Safe approval.
 */

interface IERC20 {
    function transferFrom(address from, address to, uint256 value) external returns (bool);
    function balanceOf(address) external view returns (uint256);
    function allowance(address, address) external view returns (uint256);
}

contract KishaPayout {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error AlreadyFulfilled(bytes32 ticketId);
    error ExpiredTicket();
    error InvalidSignatureCount();
    error InvalidSignature();
    error DuplicateSigner();
    error UnknownSigner(address signer);
    error TransferFailed();

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event Fulfilled(
        bytes32 indexed ticketId,
        uint256 indexed tokenId,
        address indexed baseRecipient,
        uint256 amount,
        uint64  fulfilledAt
    );

    // -------------------------------------------------------------------
    // Immutable wiring
    // -------------------------------------------------------------------

    /// @notice USDC contract on Base (Coinbase Bridged, ADR-2605172100).
    IERC20 public immutable usdc;

    /// @notice Treasury Safe address that pre-approves this contract.
    address public immutable treasury;

    /// @notice The KishaStream contract on geth-private. Used only as
    ///         a label in ticketId derivation; this contract cannot read
    ///         across chains.
    address public immutable kishaStream;

    /// @notice Threshold of relayer signatures required to fulfill.
    uint8 public immutable threshold;

    // -------------------------------------------------------------------
    // Relayer set (immutable in S1)
    // -------------------------------------------------------------------

    /// @notice Addresses authorized to co-sign fulfillment payloads.
    ///         Frozen at construction in S1; future stages move
    ///         rotation to Governance.
    mapping(address => bool) public isRelayer;
    uint8 public immutable relayerCount;

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    mapping(bytes32 => bool) public fulfilled;

    // -------------------------------------------------------------------
    // Construction
    // -------------------------------------------------------------------

    constructor(
        IERC20 usdc_,
        address treasury_,
        address kishaStream_,
        address[] memory relayers,
        uint8 threshold_
    ) {
        require(relayers.length > 0 && relayers.length < 256, "relayer count");
        require(threshold_ > 0 && threshold_ <= relayers.length, "threshold");
        usdc = usdc_;
        treasury = treasury_;
        kishaStream = kishaStream_;
        threshold = threshold_;
        relayerCount = uint8(relayers.length);
        for (uint256 i = 0; i < relayers.length; ++i) {
            require(relayers[i] != address(0), "zero relayer");
            require(!isRelayer[relayers[i]], "duplicate relayer");
            isRelayer[relayers[i]] = true;
        }
    }

    // -------------------------------------------------------------------
    // Fulfillment
    // -------------------------------------------------------------------

    /**
     * @notice Fulfill a claim ticket. Anyone may submit; security comes
     *         from the M-of-N relayer signatures over the fulfillment
     *         payload. Sorted signer addresses required (ascending) to
     *         simplify duplicate-detection.
     */
    function fulfill(
        bytes32 ticketId,
        uint256 tokenId,
        address baseRecipient,
        uint256 amount,
        uint64  expiresAt,
        bytes[] calldata signatures,
        address[] calldata signers
    ) external {
        if (fulfilled[ticketId]) revert AlreadyFulfilled(ticketId);
        if (block.timestamp > expiresAt) revert ExpiredTicket();
        if (signatures.length != signers.length) revert InvalidSignatureCount();
        if (signatures.length < threshold) revert InvalidSignatureCount();

        bytes32 payloadHash = _payloadHash(ticketId, tokenId, baseRecipient, amount, expiresAt);

        address previous = address(0);
        for (uint256 i = 0; i < signers.length; ++i) {
            address s = signers[i];
            if (s <= previous) revert DuplicateSigner();
            if (!isRelayer[s]) revert UnknownSigner(s);
            if (!_verify(payloadHash, signatures[i], s)) revert InvalidSignature();
            previous = s;
        }

        fulfilled[ticketId] = true;

        bool ok = usdc.transferFrom(treasury, baseRecipient, amount);
        if (!ok) revert TransferFailed();

        emit Fulfilled(ticketId, tokenId, baseRecipient, amount, uint64(block.timestamp));
    }

    // -------------------------------------------------------------------
    // Payload hashing — EIP-191 personal_sign envelope for S1 simplicity.
    // S2 candidate: switch to EIP-712 typed data once the relayer client
    // is hardened.
    // -------------------------------------------------------------------

    function _payloadHash(
        bytes32 ticketId,
        uint256 tokenId,
        address baseRecipient,
        uint256 amount,
        uint64 expiresAt
    ) internal view returns (bytes32) {
        bytes32 inner = keccak256(abi.encode(
            address(this),
            block.chainid,
            ticketId,
            tokenId,
            baseRecipient,
            amount,
            expiresAt
        ));
        return keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", inner));
    }

    function _verify(bytes32 hash, bytes calldata sig, address expected) internal pure returns (bool) {
        if (sig.length != 65) return false;
        bytes32 r;
        bytes32 s;
        uint8 v;
        // calldata sig layout: 0..32 r, 32..64 s, 64..65 v
        assembly ("memory-safe") {
            r := calldataload(sig.offset)
            s := calldataload(add(sig.offset, 32))
            v := byte(0, calldataload(add(sig.offset, 64)))
        }
        if (v < 27) v += 27;
        if (v != 27 && v != 28) return false;
        // Disallow malleable high-s.
        if (uint256(s) > 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0) {
            return false;
        }
        address recovered = ecrecover(hash, v, r, s);
        return recovered != address(0) && recovered == expected;
    }
}
