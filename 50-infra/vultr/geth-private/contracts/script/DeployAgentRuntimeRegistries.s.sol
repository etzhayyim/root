// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";

import {etzhayyimAgentRegistry} from "../src/EtzhayyimAgentRegistry.sol";
import {etzhayyimRootIdentityRegistry} from "../src/EtzhayyimRootIdentityRegistry.sol";

/// @title Incremental deploy — ERC725/ERC-8004 agent runtime registries
contract DeployAgentRuntimeRegistries is Script {
    function run() external {
        uint256 deployerPk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPk);

        vm.startBroadcast(deployerPk);

        etzhayyimRootIdentityRegistry rootRegistry = new etzhayyimRootIdentityRegistry(deployer);
        console.log("etzhayyimRootIdentityRegistry:", address(rootRegistry));

        etzhayyimAgentRegistry agentRegistry = new etzhayyimAgentRegistry(deployer);
        console.log("etzhayyimAgentRegistry:       ", address(agentRegistry));

        vm.stopBroadcast();

        require(rootRegistry.owner() == deployer, "root registry owner mismatch");
        require(agentRegistry.owner() == deployer, "agent registry owner mismatch");
        require(agentRegistry.nextTokenId() == 1, "agent token sequence mismatch");
        console.log("Post-deploy sanity: all checks pass");
    }
}
