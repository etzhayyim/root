// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";

import {
    MurakumoAgentBridge,
    IMurakumoRegistry,
    IetzhayyimAgentRegistry
} from "../src/MurakumoAgentBridge.sol";

/// @title DeployMurakumoBridge — ADR-2604271400 ERC-8004 ↔ Murakumo bridge
///
/// Reads existing addresses from env (`MURAKUMO_REGISTRY_ADDR`,
/// `etzhayyim_AGENT_REGISTRY_ADDR`) and deploys the stateless join contract.
/// Run AFTER both `DeployMurakumo.s.sol` and
/// `DeployAgentRuntimeRegistries.s.sol` have populated `ADDRESSES.md`.
contract DeployMurakumoBridge is Script {
    function run() external {
        uint256 deployerPk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPk);
        address murakumoAddr = vm.envAddress("MURAKUMO_REGISTRY_ADDR");
        address agentsAddr = vm.envAddress("etzhayyim_AGENT_REGISTRY_ADDR");
        require(murakumoAddr.code.length > 0, "MURAKUMO_REGISTRY_ADDR has no code on this chain");
        require(agentsAddr.code.length > 0, "etzhayyim_AGENT_REGISTRY_ADDR has no code on this chain");

        vm.startBroadcast(deployerPk);

        MurakumoAgentBridge bridge = new MurakumoAgentBridge(
            IMurakumoRegistry(murakumoAddr),
            IetzhayyimAgentRegistry(agentsAddr),
            deployer // owner = sealer (Phase 3 → multisig)
        );
        console.log("MurakumoAgentBridge: ", address(bridge));

        vm.stopBroadcast();

        require(address(bridge.murakumo()) == murakumoAddr, "bridge murakumo mismatch");
        require(address(bridge.agents()) == agentsAddr, "bridge agents mismatch");
        require(bridge.owner() == deployer, "bridge owner mismatch");
        console.log("Post-deploy sanity: all checks pass");
    }
}
