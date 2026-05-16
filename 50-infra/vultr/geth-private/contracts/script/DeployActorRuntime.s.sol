// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";

import {ActorRuntimeRegistry} from "../src/ActorRuntimeRegistry.sol";

/// @title Incremental deploy — actor runtime anchor
///
/// Deploys the EVM trust anchor for BPMN/WASM/browser/LangGraph execution
/// receipts. Run after Phase 2-A; this contract is intentionally independent
/// from GCC and Murakumo escrow so it can be adopted without changing the
/// existing inference economy contracts.
contract DeployActorRuntime is Script {
    function run() external {
        uint256 deployerPk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPk);

        vm.startBroadcast(deployerPk);

        ActorRuntimeRegistry registry = new ActorRuntimeRegistry(deployer);
        console.log("ActorRuntimeRegistry: ", address(registry));

        vm.stopBroadcast();

        require(registry.owner() == deployer, "owner mismatch");
        require(!registry.openRegistration(), "openRegistration default mismatch");
        require(!registry.openReceipt(), "openReceipt default mismatch");
        console.log("Post-deploy sanity: all checks pass");
    }
}
