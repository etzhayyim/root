// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {MessageHashUtils} from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

/**
 * @title EtzhayyimPaymaster
 * @notice ERC-4337 Paymaster sponsoring gas for etzhayyim app user-ops on Base L2.
 *         Per ADR-2605172100.
 *
 * @dev Policy:
 *      - target contract must be on the allowlist
 *      - sender must not have exceeded their per-day gas cap
 *      - userOp.callData top-level selector should be safe (transfer / contract calls only)
 *
 *      Verifying signer (Mitigates #1519 — Sybil drain):
 *      - a UserOp is only sponsored if it carries a valid ECDSA signature
 *        (over {userOpHash-equivalent, validUntil, validAfter}) from the
 *        off-chain paymaster operator key (`verifyingSigner`). Without that
 *        signature ANY address could drain the deposit via allowlisted targets.
 *      - `verifyingSigner` is rotatable by the owner (2-of-3 Safe) via
 *        setVerifyingSigner, so a leaked hot key can be revoked without
 *        redeploying the paymaster.
 *
 *      Admin (2-of-3 Safe):
 *      - setAllowlist (add/remove target contract)
 *      - setDailyLimit (per-sender ETH-equivalent cap)
 *      - setVerifyingSigner (rotate operator signing key)
 *      - withdraw (move excess to funding Safe)
 *      - setOwner (rotate admin Safe)
 *
 *      NO pause. NO proxy. NO upgrade. To change policy, deploy a new
 *      paymaster and update the SDK config.
 */

interface IEntryPoint {
    function depositTo(address account) external payable;
    function balanceOf(address account) external view returns (uint256);
    function withdrawTo(address payable withdrawAddress, uint256 amount) external;
    function addStake(uint32 unstakeDelaySec) external payable;
    function unlockStake() external;
    function withdrawStake(address payable withdrawAddress) external;
}

/// @dev Subset of ERC-4337 v0.7 PackedUserOperation. Real impl pulls full struct from EntryPoint.
struct PackedUserOperation {
    address sender;
    uint256 nonce;
    bytes initCode;
    bytes callData;
    bytes32 accountGasLimits;
    uint256 preVerificationGas;
    bytes32 gasFees;
    bytes paymasterAndData;
    bytes signature;
}

enum PostOpMode {
    opSucceeded,
    opReverted,
    postOpReverted
}

contract EtzhayyimPaymaster {
    using ECDSA for bytes32;

    IEntryPoint public immutable entryPoint;
    address public owner;
    /// @dev Off-chain paymaster operator key that pre-approves sponsored UserOps.
    address public verifyingSigner;

    /// @dev v0.7 paymasterAndData layout. Custom data starts at PAYMASTER_DATA_OFFSET;
    ///      PAYMASTER_DATA_OFFSET[:64] is abi.encode(validUntil, validAfter); the
    ///      remaining bytes are the operator ECDSA signature. Layout matches
    ///      account-abstraction v0.7 samples.VerifyingPaymaster so off-chain SDKs align.
    uint256 private constant PAYMASTER_VALIDATION_GAS_OFFSET = 20;
    uint256 private constant PAYMASTER_POSTOP_GAS_OFFSET = 36;
    uint256 private constant PAYMASTER_DATA_OFFSET = 52;
    uint256 private constant SIGNATURE_OFFSET = PAYMASTER_DATA_OFFSET + 64; // 116

    /// @dev target contract address → allowed?
    mapping(address => bool) public allowedTarget;
    /// @dev sender contract factory address → allowed?
    mapping(address => bool) public allowedFactory;
    /// @dev sender → daily gas spend cap in wei
    mapping(address => uint256) public senderDailyCapWei;
    /// @dev sender → epoch day → wei spent
    mapping(address => mapping(uint256 => uint256)) public senderSpentOnDay;
    /// @dev default cap if senderDailyCapWei[sender] == 0 (sponsoring new users)
    uint256 public defaultDailyCapWei = 0.02 ether;

    event AllowedTargetSet(address indexed target, bool allowed);
    event AllowedFactorySet(address indexed factory, bool allowed);
    event DailyLimitSet(address indexed sender, uint256 capWei);
    event DefaultDailyLimitSet(uint256 capWei);
    event VerifyingSignerRotated(address indexed oldSigner, address indexed newSigner);
    event Withdrew(address indexed to, uint256 amount);
    event OwnerRotated(address indexed oldOwner, address indexed newOwner);

    error NotOwner();
    error NotEntryPoint();
    error TargetNotAllowed(address target);
    error FactoryNotAllowed(address factory);
    error DailyCapExceeded(address sender, uint256 spent, uint256 cap);
    error PolicyRejected(bytes reason);
    error InvalidSigner();
    error InvalidPaymasterDataLength();
    error InvalidSignatureLength();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }
    modifier onlyEntryPoint() {
        if (msg.sender != address(entryPoint)) revert NotEntryPoint();
        _;
    }

    constructor(
        IEntryPoint _entryPoint,
        address _owner,
        address _verifyingSigner,
        address[] memory initialFactories
    ) {
        if (_verifyingSigner == address(0)) revert InvalidSigner();
        entryPoint = _entryPoint;
        owner = _owner;
        verifyingSigner = _verifyingSigner;
        for (uint256 i = 0; i < initialFactories.length; ++i) {
            allowedFactory[initialFactories[i]] = true;
            emit AllowedFactorySet(initialFactories[i], true);
        }
    }

    // ─── EntryPoint hooks ────────────────────────────────────────────

    /// @notice Called by EntryPoint to validate the paymaster will pay for this userOp.
    /// @dev Returns context bytes used in postOp; validationData encodes sigFailed /
    ///      validUntil / validAfter (ERC-4337). A UserOp is denied when the operator
    ///      signature is missing/invalid (sigFailed bit set) or any policy check fails.
    function validatePaymasterUserOp(
        PackedUserOperation calldata userOp,
        bytes32 /*userOpHash*/,
        uint256 maxCost
    ) external onlyEntryPoint returns (bytes memory context, uint256 validationData) {
        // 1. paymasterAndData must carry the operator signature, else deny.
        if (userOp.paymasterAndData.length < SIGNATURE_OFFSET) revert InvalidPaymasterDataLength();

        (uint48 validUntil, uint48 validAfter, bytes calldata signature) =
            parsePaymasterAndData(userOp.paymasterAndData);
        if (signature.length != 64 && signature.length != 65) revert InvalidSignatureLength();

        // 2. verify the off-chain operator pre-approved this UserOp.
        bytes32 hash =
            MessageHashUtils.toEthSignedMessageHash(getHash(userOp, validUntil, validAfter));
        address recovered = hash.recover(signature);
        bool sigFailed = recovered != verifyingSigner;

        // 3. policy gate (defense-in-depth) — enforced even with a valid signature.
        if (userOp.initCode.length > 0) {
            address factory = _decodeFactory(userOp.initCode);
            if (!allowedFactory[factory]) revert FactoryNotAllowed(factory);
        }

        address target = _decodeTarget(userOp.callData);
        if (!allowedTarget[target]) revert TargetNotAllowed(target);

        uint256 today = block.timestamp / 1 days;
        uint256 cap = senderDailyCapWei[userOp.sender];
        if (cap == 0) cap = defaultDailyCapWei;
        uint256 spent = senderSpentOnDay[userOp.sender][today];
        if (spent + maxCost > cap) revert DailyCapExceeded(userOp.sender, spent, cap);

        // pack {sender, today, maxCost} for postOp
        context = abi.encode(userOp.sender, today, maxCost);
        // sigFailed is returned (not reverted) so EntryPoint simulation sees a clean
        // validationData rather than an opaque revert — matches ERC-4337 semantics.
        validationData = _packValidationData(sigFailed, validUntil, validAfter);
    }

    /// @dev Returns the factory address encoded at initCode[0:20], or zero for an already-deployed account.
    function _decodeFactory(bytes calldata initCode) internal pure returns (address factory) {
        if (initCode.length < 20) return address(0);
        assembly {
            factory := shr(96, calldataload(add(initCode.offset, 0)))
        }
    }

    /// @notice Called by EntryPoint after the userOp executes. Reconcile gas spent.
    function postOp(
        PostOpMode /*mode*/,
        bytes calldata context,
        uint256 actualGasCost,
        uint256 /*actualUserOpFeePerGas*/
    ) external onlyEntryPoint {
        (address sender, uint256 day, uint256 maxCost) = abi.decode(context, (address, uint256, uint256));
        // Refund the slack between maxCost and actualGasCost back to the daily counter
        uint256 actual = actualGasCost < maxCost ? actualGasCost : maxCost;
        senderSpentOnDay[sender][day] += actual;
    }

    // ─── Verifying-paymaster helpers (fix #1519) ─────────────────────

    /**
     * @notice Hash the off-chain operator signs to pre-approve a UserOp.
     * @dev Covers all UserOp fields except the trailing signature in
     *      paymasterAndData (which would be circular). Layout matches
     *      account-abstraction v0.7 samples.VerifyingPaymaster.getHash.
     */
    function getHash(PackedUserOperation calldata userOp, uint48 validUntil, uint48 validAfter)
        public
        view
        returns (bytes32)
    {
        return keccak256(
            abi.encode(
                userOp.sender,
                userOp.nonce,
                keccak256(userOp.initCode),
                keccak256(userOp.callData),
                userOp.accountGasLimits,
                uint256(bytes32(userOp.paymasterAndData[PAYMASTER_VALIDATION_GAS_OFFSET:PAYMASTER_DATA_OFFSET])),
                userOp.preVerificationGas,
                userOp.gasFees,
                block.chainid,
                address(this),
                validUntil,
                validAfter
            )
        );
    }

    /// @dev Parse validUntil/validAfter (uint48×2) and the trailing signature out of paymasterAndData.
    function parsePaymasterAndData(bytes calldata paymasterAndData)
        public
        pure
        returns (uint48 validUntil, uint48 validAfter, bytes calldata signature)
    {
        (validUntil, validAfter) =
            abi.decode(paymasterAndData[PAYMASTER_DATA_OFFSET:], (uint48, uint48));
        signature = paymasterAndData[SIGNATURE_OFFSET:];
    }

    /// @dev Inlined from account-abstraction Helpers._packValidationData to avoid the GPL import.
    function _packValidationData(bool sigFailed, uint48 validUntil, uint48 validAfter)
        internal
        pure
        returns (uint256)
    {
        return (sigFailed ? 1 : 0) | (uint256(validUntil) << 160) | (uint256(validAfter) << 208);
    }

    // ─── Policy helpers ──────────────────────────────────────────────

    /// @dev Naive extraction of the first 20 bytes of callData (assumes
    ///      AccountAbstraction execute(target, value, data) layout). Real
    ///      impl should parse the SCA's execute() ABI properly.
    function _decodeTarget(bytes calldata callData) internal pure returns (address target) {
        if (callData.length < 4 + 32) return address(0);
        assembly {
            // skip 4-byte selector and 12 bytes of leading zeros for the first uint256 arg
            target := shr(96, calldataload(add(callData.offset, 16)))
        }
    }

    // ─── Admin (owner = Safe multisig) ───────────────────────────────

    function setAllowedTarget(address target, bool allowed) external onlyOwner {
        allowedTarget[target] = allowed;
        emit AllowedTargetSet(target, allowed);
    }

    function setAllowedFactory(address factory, bool allowed) external onlyOwner {
        allowedFactory[factory] = allowed;
        emit AllowedFactorySet(factory, allowed);
    }

    function setDailyLimit(address sender, uint256 capWei) external onlyOwner {
        senderDailyCapWei[sender] = capWei;
        emit DailyLimitSet(sender, capWei);
    }

    function setDefaultDailyLimit(uint256 capWei) external onlyOwner {
        defaultDailyCapWei = capWei;
        emit DefaultDailyLimitSet(capWei);
    }

    /// @notice Rotate the off-chain operator signing key. Callable only by the owner Safe.
    function setVerifyingSigner(address newSigner) external onlyOwner {
        if (newSigner == address(0)) revert InvalidSigner();
        address old = verifyingSigner;
        verifyingSigner = newSigner;
        emit VerifyingSignerRotated(old, newSigner);
    }

    function setOwner(address newOwner) external onlyOwner {
        address old = owner;
        owner = newOwner;
        emit OwnerRotated(old, newOwner);
    }

    // ─── EntryPoint deposit / stake passthrough ──────────────────────

    /// @notice Deposit ETH into EntryPoint to back paymaster gas payments.
    receive() external payable {
        entryPoint.depositTo{value: msg.value}(address(this));
    }

    function getDeposit() external view returns (uint256) {
        return entryPoint.balanceOf(address(this));
    }

    function withdraw(address payable to, uint256 amount) external onlyOwner {
        entryPoint.withdrawTo(to, amount);
        emit Withdrew(to, amount);
    }

    function addStake(uint32 unstakeDelaySec) external payable onlyOwner {
        entryPoint.addStake{value: msg.value}(unstakeDelaySec);
    }

    function unlockStake() external onlyOwner {
        entryPoint.unlockStake();
    }

    function withdrawStake(address payable to) external onlyOwner {
        entryPoint.withdrawStake(to);
    }
}
