// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {EtzhayyimPaymaster, IEntryPoint, PackedUserOperation} from "../src/EtzhayyimPaymaster.sol";

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

    function setUp() public {
        ep = new MockEntryPoint();
        address[] memory initialFactories = new address[](0);
        paymaster = new EtzhayyimPaymaster(ep, owner, initialFactories);
        vm.deal(address(this), 10 ether);
    }

    function test_only_owner_can_set_allowlist() public {
        vm.expectRevert(EtzhayyimPaymaster.NotOwner.selector);
        paymaster.setAllowedTarget(allowedTarget, true);

        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);
        assertTrue(paymaster.allowedTarget(allowedTarget));
    }

    function test_constructor_allows_initial_factory() public {
        address[] memory initialFactories = new address[](1);
        initialFactories[0] = address(0x1234);

        EtzhayyimPaymaster seeded = new EtzhayyimPaymaster(ep, owner, initialFactories);
        assertTrue(seeded.allowedFactory(address(0x1234)));
    }

    function test_only_owner_can_set_allowed_factory() public {
        vm.expectRevert(EtzhayyimPaymaster.NotOwner.selector);
        paymaster.setAllowedFactory(address(0x1234), true);

        vm.prank(owner);
        paymaster.setAllowedFactory(address(0x1234), true);
        assertTrue(paymaster.allowedFactory(address(0x1234)));
    }

    function test_validate_rejects_non_allowed_factory() public {
        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);

        bytes memory callData = abi.encodePacked(
            bytes4(0x12345678),
            bytes32(uint256(uint160(allowedTarget)))
        );
        bytes memory initCode = abi.encodePacked(address(0x1234), bytes(""));
        PackedUserOperation memory uop = PackedUserOperation({
            sender: sender,
            nonce: 0,
            initCode: initCode,
            callData: callData,
            accountGasLimits: bytes32(0),
            preVerificationGas: 0,
            gasFees: bytes32(0),
            paymasterAndData: "",
            signature: ""
        });

        vm.prank(address(ep));
        vm.expectRevert(abi.encodeWithSelector(EtzhayyimPaymaster.FactoryNotAllowed.selector, address(0x1234)));
        paymaster.validatePaymasterUserOp(uop, bytes32(0), 0.001 ether);
    }

    function test_validate_accepts_allowed_factory_and_target() public {
        address factory = address(0x1234);
        vm.prank(owner);
        paymaster.setAllowedFactory(factory, true);
        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);

        bytes memory callData = abi.encodePacked(
            bytes4(0x12345678),
            bytes32(uint256(uint160(allowedTarget)))
        );
        bytes memory initCode = abi.encodePacked(factory, bytes(""));
        PackedUserOperation memory uop = PackedUserOperation({
            sender: sender,
            nonce: 0,
            initCode: initCode,
            callData: callData,
            accountGasLimits: bytes32(0),
            preVerificationGas: 0,
            gasFees: bytes32(0),
            paymasterAndData: "",
            signature: ""
        });

        vm.prank(address(ep));
        (bytes memory context, uint256 validationData) = paymaster.validatePaymasterUserOp(uop, bytes32(0), 0.001 ether);
        assertEq(validationData, 0);
        (address senderOut, uint256 todayOut, uint256 maxCostOut) = abi.decode(context, (address, uint256, uint256));
        assertEq(senderOut, sender);
        assertEq(todayOut, block.timestamp / 1 days);
        assertEq(maxCostOut, 0.001 ether);
    }

    function test_validate_rejects_non_allowed_target() public {
        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);

        // callData decodes target as address(0xDEAD), not on allowlist
        bytes memory callData = abi.encodePacked(
            bytes4(0x12345678),  // selector
            bytes32(uint256(uint160(address(0xDEAD))))
        );
        PackedUserOperation memory uop = PackedUserOperation({
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

        vm.prank(address(ep));
        vm.expectRevert(abi.encodeWithSelector(EtzhayyimPaymaster.TargetNotAllowed.selector, address(0xDEAD)));
        paymaster.validatePaymasterUserOp(uop, bytes32(0), 0.001 ether);
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

    function test_default_cap_is_0_02_eth() public {
        assertEq(paymaster.defaultDailyCapWei(), 0.02 ether);
    }
}
