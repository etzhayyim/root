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
        paymaster = new EtzhayyimPaymaster(ep, owner);
        vm.deal(address(this), 10 ether);
    }

    function test_only_owner_can_set_allowlist() public {
        vm.expectRevert(EtzhayyimPaymaster.NotOwner.selector);
        paymaster.setAllowedTarget(allowedTarget, true);

        vm.prank(owner);
        paymaster.setAllowedTarget(allowedTarget, true);
        assertTrue(paymaster.allowedTarget(allowedTarget));
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

    function test_default_cap_is_0_02_eth() public view {
        assertEq(paymaster.defaultDailyCapWei(), 0.02 ether);
    }
}
