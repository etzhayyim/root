// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Script, console} from "forge-std/Script.sol";

import {AgentRuntimeLeaseEscrow} from "../src/AgentRuntimeLeaseEscrow.sol";

/// @title DeployAgentRuntimeLeaseEscrow — ADR-2604301200 runtime lease bond escrow
///
/// Required env:
/// - PRIVATE_KEY
/// - GCC_ADDR
/// - TREASURY_ADDR
///
/// Optional env:
/// - OWNER_ADDR (defaults to deployer)
contract DeployAgentRuntimeLeaseEscrow is Script {
    function run() external {
        uint256 deployerPk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPk);
        address gccAddr = vm.envAddress("GCC_ADDR");
        address treasuryAddr = vm.envAddress("TREASURY_ADDR");
        address ownerAddr = vm.envOr("OWNER_ADDR", deployer);

        require(gccAddr.code.length > 0, "GCC_ADDR has no code on this chain");
        require(treasuryAddr != address(0), "TREASURY_ADDR is zero");
        require(ownerAddr != address(0), "OWNER_ADDR is zero");

        vm.startBroadcast(deployerPk);

        AgentRuntimeLeaseEscrow escrow = new AgentRuntimeLeaseEscrow(IERC20(gccAddr), treasuryAddr, ownerAddr);
        console.log("AgentRuntimeLeaseEscrow: ", address(escrow));

        vm.stopBroadcast();

        require(address(escrow.gcc()) == gccAddr, "escrow gcc mismatch");
        require(escrow.treasury() == treasuryAddr, "escrow treasury mismatch");
        require(escrow.owner() == ownerAddr, "escrow owner mismatch");
        console.log("Post-deploy sanity: all checks pass");
    }
}
