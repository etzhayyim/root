// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Test} from "forge-std/Test.sol";

import {AgentRuntimeLeaseEscrow} from "../src/AgentRuntimeLeaseEscrow.sol";
import {GCCStablecoin} from "../src/GCCStablecoin.sol";

contract AgentRuntimeLeaseEscrowTest is Test {
    GCCStablecoin gcc;
    AgentRuntimeLeaseEscrow escrow;

    address owner = address(0xA11CE);
    address treasury = address(0x7100);
    address agent = address(0xA6E17);
    address beneficiary = address(0xBEEF);

    bytes32 leaseId = keccak256(bytes("lease-1"));
    bytes32 agentDidHash = keccak256(bytes("did:web:agent.etzhayyim.com"));
    bytes32 resourceHash = keccak256(bytes("cpu=2,memory=8192,gpu=l4"));
    bytes32 policyHash = keccak256(bytes("slash-policy-v1"));

    function setUp() public {
        gcc = new GCCStablecoin("etzhayyim Compute Credit", "GCC", 18, 1_000_000 ether, owner, owner, owner, owner);
        vm.prank(owner);
        gcc.configureMinter(owner, 100_000 ether);
        vm.prank(owner);
        gcc.mint(agent, 1_000 ether);

        escrow = new AgentRuntimeLeaseEscrow(IERC20(address(gcc)), treasury, owner);
    }

    function testReserveRenewAndHibernate() public {
        vm.startPrank(agent);
        gcc.approve(address(escrow), 150 ether);
        escrow.reserveLease(leaseId, agentDidHash, resourceHash, policyHash, 100 ether, 7 days);
        escrow.renewLease(leaseId, 50 ether, 1 days);
        vm.stopPrank();

        AgentRuntimeLeaseEscrow.Lease memory lease = escrow.leases(leaseId);
        assertEq(lease.lessee, agent);
        assertEq(lease.bond, 150 ether);
        assertEq(uint8(lease.status), uint8(AgentRuntimeLeaseEscrow.LeaseStatus.Active));

        vm.prank(agent);
        escrow.hibernate(leaseId);

        lease = escrow.leases(leaseId);
        assertEq(lease.bond, 0);
        assertEq(uint8(lease.status), uint8(AgentRuntimeLeaseEscrow.LeaseStatus.Hibernated));
        assertEq(gcc.balanceOf(agent), 1_000 ether);
    }

    function testOwnerCanSlashBondToBeneficiary() public {
        vm.startPrank(agent);
        gcc.approve(address(escrow), 100 ether);
        escrow.reserveLease(leaseId, agentDidHash, resourceHash, policyHash, 100 ether, 7 days);
        vm.stopPrank();

        vm.prank(owner);
        escrow.slashLease(leaseId, 40 ether, beneficiary, keccak256(bytes("false-runtime-receipt")));

        AgentRuntimeLeaseEscrow.Lease memory lease = escrow.leases(leaseId);
        assertEq(lease.bond, 60 ether);
        assertEq(gcc.balanceOf(beneficiary), 40 ether);
        assertEq(uint8(lease.status), uint8(AgentRuntimeLeaseEscrow.LeaseStatus.Active));
    }

    function testReleaseExpiredRefundsRemainingBond() public {
        vm.startPrank(agent);
        gcc.approve(address(escrow), 100 ether);
        escrow.reserveLease(leaseId, agentDidHash, resourceHash, policyHash, 100 ether, 1 hours);
        vm.stopPrank();

        vm.warp(block.timestamp + 1 hours);
        escrow.releaseExpired(leaseId);

        AgentRuntimeLeaseEscrow.Lease memory lease = escrow.leases(leaseId);
        assertEq(lease.bond, 0);
        assertEq(uint8(lease.status), uint8(AgentRuntimeLeaseEscrow.LeaseStatus.Released));
        assertEq(gcc.balanceOf(agent), 1_000 ether);
    }
}
