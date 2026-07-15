// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {EtzhayyimPaymaster, IEntryPoint, PackedUserOperation} from "../src/EtzhayyimPaymaster.sol";
import {MessageHashUtils} from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

/// @dev Minimal mock that records deposits + balances + withdrawals.
contract MockEntryPoint is IEntryPoint {
    mapping(address => uint256) public deposits;

    function depositTo(address account) external payable override {
        deposits[account] += msg.value;
    }
    function balanceOf(address account) external view override returns (uint256) {
        return deposits[account];
    }
    function withdrawTo(address payable withdrawAddress, uint256 amount) external override {
        deposits[msg.sender] -= amount;
        (bool ok, ) = withdrawAddress.call{value: amount}("");
        require(ok, "withdraw failed");
    }
    function addStake(uint32) external payable override {}
    function unlockStake() external override {}
    function withdrawStake(address payable) external override {}
    receive() external payable {}
}

contract EtzhayyimPaymasterTest is Test {
    EtzhayyimPaymaster paymaster;
    MockEntryPoint ep;
    address owner = address(0xA);
    address sender = address(0xBEEF);
    address allowedTarget = address(0xCAFE);

    // Off-chain paymaster operator key (fix #1519). Its address is the
    // `verifyingSigner` the contract trusts.
    uint256 signerKey = uint256(keccak256("paymaster-operator"));
    address signerAddr;

    // An attacker that never holds the operator key.
    uint256 attackerKey = uint256(keccak256("attacker"));

    function setUp() public {
        signerAddr = vm.addr(signerKey);
        ep = new MockEntryPoint();
        address[] memory initialFactories = new address[](0);
        paymaster = new EtzhayyimPaymaster(ep, owner, signerAddr, initialFactories);
        vm.deal(address(this), 10 ether);
    }

    // ─── paymasterAndData builder (verifying signature) ─────────────

    /// @dev Build a fully-signed paymasterAndData for a given UserOp + time window.
    function _signedPaymasterAndData(PackedUserOperation memory uop, uint48 validUntil, uint48 validAfter)
        internal
        view
        returns (bytes memory)
    {
        bytes memory prefix = abi.encodePacked(
            address(paymaster),
            uint128(200_000), // PAYMASTER_VALIDATION_GAS_OFFSET..POSTOP
            uint128(100_000), // PAYMASTER_POSTOP_GAS_OFFSET..DATA
            abi.encode(validUntil, validAfter)
        );
        // getHash reads paymasterAndData[20:52]; the gas-limit fields are present above.
        uop.paymasterAndData = prefix;
        bytes32 hash = _operatorHash(uop, validUntil, validAfter);
        bytes32 ethHash = MessageHashUtils.toEthSignedMessageHash(hash);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(signerKey, ethHash);
        return abi.encodePacked(prefix, r, s, v);
    }

    function _signedBy(PackedUserOperation memory uop, uint48 validUntil, uint48 validAfter, uint256 key)
        internal
        view
        returns (bytes memory)
    {
        bytes memory prefix = abi.encodePacked(
            address(paymaster), uint128(200_000), uint128(100_000), abi.encode(validUntil, validAfter)
        );
        uop.paymasterAndData = prefix;
        bytes32 hash = _operatorHash(uop, validUntil, validAfter);
        bytes32 ethHash = MessageHashUtils.toEthSignedMessageHash(hash);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(key, ethHash);
        return abi.encodePacked(prefix, r, s, v);
    }

    function _validOp(address target) internal view returns (PackedUserOperation memory uop) {
        bytes memory callData = abi.encodePacked(bytes4(0x12345678), bytes32(uint256(uint160(target))));
        uop = PackedUserOperation({
            sender: sender,
            nonce: 0,
            initCode: "",
            callData: callData,
            accountGasLimits: bytes32(0),
            preVerificationGas: 0,
            gasFees: bytes32(0),
            paymasterAndData: "",
            signature: ""
        });
    }

    /// @dev Operator hash over a UserOp, mirroring EtzhayyimPaymaster.getHash.
    ///      The paymasterAndData gas-limit bytes are reconstructed from the
    ///      constants used by _signedPaymasterAndData (memory bytes can't be
    ///      range-sliced in Solidity, unlike calldata).
    function _operatorHash(PackedUserOperation memory userOp, uint48 validUntil, uint48 validAfter)
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

    // ─── cases ──────────────────────────────────────────────────────

    function test_only_owner_can_set_allowlist() public {
        vm.expectRevert(EtzhayyimPaymaster.NotOwner.selector);
        paymaster.setAllowedTarget(allowedTarget, true);

        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);
        assertTrue(paymaster.allowedTarget(allowedTarget));
    }

    function test_validate_accepts_valid_operator_signature() public {
        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);

        PackedUserOperation memory uop = _validOp(allowedTarget);
        uop.paymasterAndData = _signedPaymasterAndData(uop, type(uint48).max, 0);

        vm.prank(address(ep));
        (bytes memory context, uint256 validationData) =
            paymaster.validatePaymasterUserOp(uop, bytes32(0), 0.001 ether);
        // sigFailed bit must be clear for a valid operator signature.
        assertEq(validationData & 1, 0, "sigFailed should be 0 for valid operator sig");
        assertGt(context.length, 0);
    }

    function test_validate_rejects_bad_operator_signature() public {
        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);

        PackedUserOperation memory uop = _validOp(allowedTarget);
        // Signed by the attacker, not the operator → sigFailed bit set (no revert).
        uop.paymasterAndData = _signedBy(uop, type(uint48).max, 0, attackerKey);

        vm.prank(address(ep));
        (, uint256 validationData) = paymaster.validatePaymasterUserOp(uop, bytes32(0), 0.001 ether);
        assertEq(validationData & 1, 1, "sigFailed should be 1 for bad operator sig");
    }

    function test_validate_reverts_on_short_paymaster_data() public {
        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);

        PackedUserOperation memory uop = _validOp(allowedTarget);
        // No signature / too-short paymasterAndData → denied before any policy check.
        uop.paymasterAndData = abi.encodePacked(address(paymaster), uint128(200_000), uint128(100_000));
        assertLt(uop.paymasterAndData.length, 116);

        vm.prank(address(ep));
        vm.expectRevert(EtzhayyimPaymaster.InvalidPaymasterDataLength.selector);
        paymaster.validatePaymasterUserOp(uop, bytes32(0), 0.001 ether);
    }

    function test_validate_respects_validUntil_validAfter() public {
        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);

        uint48 validAfter = 1_000;
        uint48 validUntil = 2_000;
        PackedUserOperation memory uop = _validOp(allowedTarget);
        uop.paymasterAndData = _signedPaymasterAndData(uop, validUntil, validAfter);

        vm.prank(address(ep));
        (, uint256 validationData) = paymaster.validatePaymasterUserOp(uop, bytes32(0), 0.001 ether);
        // Packing: sigFailed(b0) | validUntil(<<160) | validAfter(<<208)
        assertEq(validationData & 1, 0);
        assertEq(uint48(validationData >> 160), validUntil, "validUntil mismatch");
        assertEq(uint48(validationData >> 208), validAfter, "validAfter mismatch");
    }

    function test_validate_rejects_non_allowed_target_even_with_valid_sig() public {
        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);

        PackedUserOperation memory uop = _validOp(address(0xDEAD));
        uop.paymasterAndData = _signedPaymasterAndData(uop, type(uint48).max, 0);

        vm.prank(address(ep));
        vm.expectRevert(abi.encodeWithSelector(EtzhayyimPaymaster.TargetNotAllowed.selector, address(0xDEAD)));
        paymaster.validatePaymasterUserOp(uop, bytes32(0), 0.001 ether);
    }

    function test_only_owner_can_rotate_verifying_signer() public {
        address newSigner = vm.addr(attackerKey);
        vm.expectRevert(EtzhayyimPaymaster.NotOwner.selector);
        paymaster.setVerifyingSigner(newSigner);

        vm.prank(owner);
        paymaster.setVerifyingSigner(newSigner);
        assertEq(paymaster.verifyingSigner(), newSigner);

        // Old operator key now fails; new key passes.
        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);

        PackedUserOperation memory uopOld = _validOp(allowedTarget);
        uopOld.paymasterAndData = _signedPaymasterAndData(uopOld, type(uint48).max, 0);
        vm.prank(address(ep));
        (, uint256 vdOld) = paymaster.validatePaymasterUserOp(uopOld, bytes32(0), 0.001 ether);
        assertEq(vdOld & 1, 1, "old key should now fail");

        PackedUserOperation memory uopNew = _validOp(allowedTarget);
        uopNew.paymasterAndData = _signedBy(uopNew, type(uint48).max, 0, attackerKey);
        vm.prank(address(ep));
        (, uint256 vdNew) = paymaster.validatePaymasterUserOp(uopNew, bytes32(0), 0.001 ether);
        assertEq(vdNew & 1, 0, "rotated key should pass");
    }

    function test_reject_zero_verifying_signer() public {
        address[] memory factories = new address[](0);
        vm.expectRevert(EtzhayyimPaymaster.InvalidSigner.selector);
        new EtzhayyimPaymaster(ep, owner, address(0), factories);
    }

    function test_receive_deposits_to_entrypoint() public {
        (bool ok, ) = address(paymaster).call{value: 1 ether}("");
        assertTrue(ok);
        assertEq(ep.balanceOf(address(paymaster)), 1 ether);
    }

    function test_owner_can_rotate() public {
        address newOwner = address(0xB);
        vm.prank(owner);
        paymaster.setOwner(newOwner);
        assertEq(paymaster.owner(), newOwner);
    }

    function test_default_cap_is_0_02_eth() public view {
        assertEq(paymaster.defaultDailyCapWei(), 0.02 ether);
    }
}
