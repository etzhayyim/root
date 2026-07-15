// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";

import {EntryPoint} from "account-abstraction/core/EntryPoint.sol";
import {SimpleAccount} from "account-abstraction/samples/SimpleAccount.sol";
import {SimpleAccountFactory} from "account-abstraction/samples/SimpleAccountFactory.sol";
import {PackedUserOperation as RealPackedUserOperation} from "account-abstraction/interfaces/PackedUserOperation.sol";
import {IEntryPoint as RealIEntryPoint} from "account-abstraction/interfaces/IEntryPoint.sol";

import {EtzhayyimPaymaster, IEntryPoint as PaymasterIEntryPoint} from "../src/EtzhayyimPaymaster.sol";

import {MessageHashUtils} from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

/// @dev Minimal target contract for the paymaster integration test.
///      Stands in for EtzhayyimMembership.join() — exact selector + arg
///      shape don't matter for paymaster validation, which only checks
///      that the target address is allowlisted.
contract TargetMock {
    event Touched(address indexed sender, bytes32 indexed key, string note);

    function poke(bytes32 key, string calldata note) external {
        emit Touched(msg.sender, key, note);
    }
}

/**
 * @title PaymasterIntegrationTest
 * @notice End-to-end integration of EtzhayyimPaymaster against the real
 *         ERC-4337 v0.7 EntryPoint + SimpleAccount stack from
 *         eth-infinitism/account-abstraction. Verifies a sponsored
 *         UserOperation:
 *
 *           1. Deploys a SimpleAccount via initCode (factory creation
 *              inside handleOps).
 *           2. The SimpleAccount calls the target.
 *           3. EtzhayyimPaymaster sponsors gas — no ETH leaves the
 *              SimpleAccount.
 *           4. Paymaster requires a valid off-chain operator signature
 *              (fix #1519) AND the allowlist + daily-cap policy;
 *              non-allowlisted targets / missing-or-bad signatures revert.
 *
 *         This replaces the MockEntryPoint test pattern with a real
 *         EntryPoint so the paymaster's behavior under handleOps is
 *         pinned to the canonical ERC-4337 semantics.
 */
contract PaymasterIntegrationTest is Test {
    EntryPoint entryPoint;
    SimpleAccountFactory factory;
    EtzhayyimPaymaster paymaster;
    TargetMock target;

    address paymasterOwner = address(0xAA);

    // Off-chain paymaster operator key (fix #1519). Address is the
    // `verifyingSigner` the contract trusts.
    uint256 signerKey = uint256(keccak256("paymaster-operator"));
    address signerAddr = vm.addr(signerKey);
    // An attacker that never holds the operator key.
    uint256 attackerKey = uint256(keccak256("attacker"));

    // SimpleAccount owner EOA — its private key signs UserOperations.
    uint256 ownerKey = uint256(keccak256("simple-account-owner"));
    address ownerAddr;

    // Sender (handles the handleOps tx and earns the beneficiary fee).
    address payable beneficiary = payable(address(0xBB));

    function setUp() public {
        ownerAddr = vm.addr(ownerKey);

        entryPoint = new EntryPoint();
        factory = new SimpleAccountFactory(entryPoint);
        address[] memory initialFactories = new address[](0);
        paymaster = new EtzhayyimPaymaster(
            PaymasterIEntryPoint(address(entryPoint)),
            paymasterOwner,
            signerAddr,
            initialFactories
        );
        target = new TargetMock();

        // Fund the paymaster's deposit at EntryPoint (its `receive()`
        // forwards to EntryPoint.depositTo(this)).
        vm.deal(address(this), 10 ether);
        (bool ok, ) = address(paymaster).call{value: 1 ether}("");
        assertTrue(ok);
        assertEq(entryPoint.balanceOf(address(paymaster)), 1 ether);

        // Allowlist the factory (for initCode-based deploys) and the target contract.
        vm.prank(paymasterOwner);
        paymaster.setAllowedFactory(address(factory), true);
        vm.prank(paymasterOwner);
        paymaster.setAllowedTarget(address(target), true);
    }

    // -------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------

    /// @dev v0.7 layout: accountGasLimits = (verificationGasLimit << 128) | callGasLimit
    function _packGasLimits(uint128 verificationGasLimit, uint128 callGasLimit)
        internal
        pure
        returns (bytes32)
    {
        return bytes32((uint256(verificationGasLimit) << 128) | uint256(callGasLimit));
    }

    /// @dev gasFees = (maxPriorityFeePerGas << 128) | maxFeePerGas
    function _packGasFees(uint128 maxPriorityFeePerGas, uint128 maxFeePerGas)
        internal
        pure
        returns (bytes32)
    {
        return bytes32((uint256(maxPriorityFeePerGas) << 128) | uint256(maxFeePerGas));
    }

    /// @dev Operator hash over a UserOp, mirroring EtzhayyimPaymaster.getHash.
    ///      MUST stay in sync with the contract. Re-implemented here because
    ///      the integration test uses the canonical account-abstraction
    ///      `PackedUserOperation` type (structurally identical, but a distinct type).
    ///      The paymasterAndData gas-limit bytes are reconstructed from the
    ///      constants below (memory bytes can't be range-sliced in Solidity).
    function _operatorHash(RealPackedUserOperation memory userOp, uint48 validUntil, uint48 validAfter)
        internal
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
                uint256(bytes32(abi.encodePacked(uint128(200_000), uint128(100_000)))),
                userOp.preVerificationGas,
                userOp.gasFees,
                block.chainid,
                address(paymaster),
                validUntil,
                validAfter
            )
        );
    }

    /// @dev Build a valid, operator-signed paymasterAndData for a given UserOp.
    function _signedPaymasterAndData(RealPackedUserOperation memory userOp, uint48 validUntil, uint48 validAfter)
        internal
        view
        returns (bytes memory)
    {
        bytes memory prefix = abi.encodePacked(
            address(paymaster), uint128(200_000), uint128(100_000), abi.encode(validUntil, validAfter)
        );
        userOp.paymasterAndData = prefix; // so _operatorHash's [20:52] slice is valid
        bytes32 hash = _operatorHash(userOp, validUntil, validAfter);
        bytes32 ethHash = MessageHashUtils.toEthSignedMessageHash(hash);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(signerKey, ethHash);
        return abi.encodePacked(prefix, r, s, v);
    }

    /// @dev Build an operator-signed paymasterAndData using a (malicious) key.
    function _signedPaymasterAndDataBy(
        RealPackedUserOperation memory userOp,
        uint48 validUntil,
        uint48 validAfter,
        uint256 key
    ) internal view returns (bytes memory) {
        bytes memory prefix = abi.encodePacked(
            address(paymaster), uint128(200_000), uint128(100_000), abi.encode(validUntil, validAfter)
        );
        userOp.paymasterAndData = prefix;
        bytes32 hash = _operatorHash(userOp, validUntil, validAfter);
        bytes32 ethHash = MessageHashUtils.toEthSignedMessageHash(hash);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(key, ethHash);
        return abi.encodePacked(prefix, r, s, v);
    }

    /// @dev Sign the (account) UserOp with the SimpleAccount owner EOA.
    function _signAccount(RealPackedUserOperation memory userOp) internal view {
        bytes32 userOpHash = entryPoint.getUserOpHash(userOp);
        bytes32 ethHash = MessageHashUtils.toEthSignedMessageHash(userOpHash);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(ownerKey, ethHash);
        userOp.signature = abi.encodePacked(r, s, v);
    }

    function _buildSignedUserOp(
        address smartAccount,
        bytes memory initCode,
        bytes memory accountCallData
    ) internal returns (RealPackedUserOperation memory userOp) {
        userOp = RealPackedUserOperation({
            sender: smartAccount,
            nonce: entryPoint.getNonce(smartAccount, 0),
            initCode: initCode,
            callData: accountCallData,
            // Tuned so maxCost stays under defaultDailyCapWei (0.02 ether):
            //   gas = 500k + 800k + 100k = 1.4M; maxFeePerGas = 10 gwei
            //   → maxCost ≈ 0.014 ether < 0.02 ether
            accountGasLimits: _packGasLimits(500_000, 800_000),
            preVerificationGas: 100_000,
            gasFees: _packGasFees(1 gwei, 10 gwei),
            paymasterAndData: "",
            signature: ""
        });

        // Attach the operator signature, then the account signature over the
        // whole op (incl. the operator-signed paymasterAndData).
        userOp.paymasterAndData = _signedPaymasterAndData(userOp, type(uint48).max, 0);
        _signAccount(userOp);
    }

    function _initCodeFor(address owner_, uint256 salt) internal view returns (bytes memory) {
        return abi.encodePacked(
            address(factory),
            abi.encodeCall(SimpleAccountFactory.createAccount, (owner_, salt))
        );
    }

    function _accountCallDataFor(address to_, bytes memory innerCallData) internal pure returns (bytes memory) {
        return abi.encodeCall(SimpleAccount.execute, (to_, 0, innerCallData));
    }

    // -------------------------------------------------------------------
    // Cases
    // -------------------------------------------------------------------

    function test_sponsored_userop_lands_on_allowlisted_target() public {
        address smartAccount = factory.getAddress(ownerAddr, 0);
        // SimpleAccount has zero ETH; only paymaster covers gas.
        assertEq(smartAccount.balance, 0);

        bytes memory innerCallData = abi.encodeCall(TargetMock.poke, (keccak256("hello"), "first-touch"));
        bytes memory accountCallData = _accountCallDataFor(address(target), innerCallData);
        bytes memory initCode = _initCodeFor(ownerAddr, 0);

        RealPackedUserOperation memory userOp = _buildSignedUserOp(smartAccount, initCode, accountCallData);

        // Record logs and assert on the Touched event post-hoc — handleOps
        // emits AccountDeployed + the inner call's events + UserOperationEvent;
        // expectEmit's "next log" semantics doesn't fit this multi-emit flow.
        vm.recordLogs();
        RealPackedUserOperation[] memory ops = new RealPackedUserOperation[](1);
        ops[0] = userOp;
        entryPoint.handleOps(ops, beneficiary);

        // SimpleAccount was deployed (code now present at the
        // pre-computed CREATE2 address).
        assertGt(smartAccount.code.length, 0);

        // The Touched event was emitted by the inner call.
        Vm.Log[] memory logs = vm.getRecordedLogs();
        bool sawTouched = false;
        bytes32 touchedSig = keccak256("Touched(address,bytes32,string)");
        for (uint256 i = 0; i < logs.length; ++i) {
            if (logs[i].emitter == address(target) && logs[i].topics[0] == touchedSig) {
                sawTouched = true;
                break;
            }
        }
        assertTrue(sawTouched, "Touched event missing");
        // Beneficiary received the gas reimbursement from the paymaster's
        // EntryPoint deposit.
        assertGt(beneficiary.balance, 0);
        // Paymaster's deposit decreased.
        assertLt(entryPoint.balanceOf(address(paymaster)), 1 ether);
    }

    function test_sponsored_userop_rejected_when_operator_signature_missing() public {
        // paymasterAndData carries no operator signature → contract reverts
        // with InvalidPaymasterDataLength before sponsoring.
        address smartAccount = factory.getAddress(ownerAddr, 1);

        bytes memory innerCallData = abi.encodeCall(TargetMock.poke, (keccak256("nosig"), "no-sig"));
        bytes memory accountCallData = _accountCallDataFor(address(target), innerCallData);
        bytes memory initCode = _initCodeFor(ownerAddr, 1);

        RealPackedUserOperation memory userOp = RealPackedUserOperation({
            sender: smartAccount,
            nonce: entryPoint.getNonce(smartAccount, 0),
            initCode: initCode,
            callData: accountCallData,
            accountGasLimits: _packGasLimits(500_000, 800_000),
            preVerificationGas: 100_000,
            gasFees: _packGasFees(1 gwei, 10 gwei),
            paymasterAndData: abi.encodePacked(address(paymaster), uint128(200_000), uint128(100_000)),
            signature: ""
        });
        // Re-sign the account over the (unsigned) paymasterAndData so the
        // account check passes and the revert originates from the paymaster.
        _signAccount(userOp);

        RealPackedUserOperation[] memory ops = new RealPackedUserOperation[](1);
        ops[0] = userOp;
        vm.expectRevert();
        entryPoint.handleOps(ops, beneficiary);
    }

    function test_sponsored_userop_rejected_when_operator_signature_bad() public {
        // paymasterAndData carries a signature from the attacker (not the
        // operator) → sigFailed bit set → handleOps reverts.
        address smartAccount = factory.getAddress(ownerAddr, 2);

        bytes memory innerCallData = abi.encodeCall(TargetMock.poke, (keccak256("badsig"), "bad-sig"));
        bytes memory accountCallData = _accountCallDataFor(address(target), innerCallData);
        bytes memory initCode = _initCodeFor(ownerAddr, 2);

        RealPackedUserOperation memory userOp = RealPackedUserOperation({
            sender: smartAccount,
            nonce: entryPoint.getNonce(smartAccount, 0),
            initCode: initCode,
            callData: accountCallData,
            accountGasLimits: _packGasLimits(500_000, 800_000),
            preVerificationGas: 100_000,
            gasFees: _packGasFees(1 gwei, 10 gwei),
            paymasterAndData: "",
            signature: ""
        });
        userOp.paymasterAndData = _signedPaymasterAndDataBy(userOp, type(uint48).max, 0, attackerKey);
        _signAccount(userOp);

        RealPackedUserOperation[] memory ops = new RealPackedUserOperation[](1);
        ops[0] = userOp;
        vm.expectRevert();
        entryPoint.handleOps(ops, beneficiary);
    }

    function test_sponsored_userop_rejected_when_target_not_allowlisted() public {
        // Deploy a second target that is NOT on the allowlist.
        TargetMock evilTarget = new TargetMock();
        address smartAccount = factory.getAddress(ownerAddr, 3);

        bytes memory innerCallData = abi.encodeCall(TargetMock.poke, (keccak256("evil"), "no-touch"));
        bytes memory accountCallData = _accountCallDataFor(address(evilTarget), innerCallData);
        bytes memory initCode = _initCodeFor(ownerAddr, 3);

        RealPackedUserOperation memory userOp = _buildSignedUserOp(smartAccount, initCode, accountCallData);

        RealPackedUserOperation[] memory ops = new RealPackedUserOperation[](1);
        ops[0] = userOp;

        // EntryPoint surfaces paymaster reverts as FailedOpWithRevert; we
        // assert only that the handleOps call reverts. The on-chain
        // unit test already pins the specific TargetNotAllowed selector.
        vm.expectRevert();
        entryPoint.handleOps(ops, beneficiary);
    }

    function test_sponsored_userop_respects_default_daily_cap() public {
        // defaultDailyCapWei = 0.02 ether. The first sponsored UserOp's
        // cost is well under that, so it succeeds.
        address smartAccount = factory.getAddress(ownerAddr, 4);
        bytes memory innerCallData = abi.encodeCall(TargetMock.poke, (keccak256("cap"), "under-cap"));
        bytes memory accountCallData = _accountCallDataFor(address(target), innerCallData);

        RealPackedUserOperation memory userOp = _buildSignedUserOp(
            smartAccount,
            _initCodeFor(ownerAddr, 4),
            accountCallData
        );

        RealPackedUserOperation[] memory ops = new RealPackedUserOperation[](1);
        ops[0] = userOp;
        entryPoint.handleOps(ops, beneficiary);

        // After the call, the sender's daily spent for today is non-zero.
        uint256 today = block.timestamp / 1 days;
        assertGt(paymaster.senderSpentOnDay(smartAccount, today), 0);
        assertLe(paymaster.senderSpentOnDay(smartAccount, today), paymaster.defaultDailyCapWei());
    }
}
