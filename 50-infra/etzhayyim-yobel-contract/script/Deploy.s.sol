// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Script.sol";
import {YobelRiteRegistry} from "../src/YobelRiteRegistry.sol";
import {YobelReleaseRegistry} from "../src/YobelReleaseRegistry.sol";

/**
 * @title Deploy
 * @notice Foundry deploy script for the yobel contract bundle. Per
 *         ADR-2605201800. Apache-2.0 + Charter Compliance Rider v2.0.
 *
 * @dev Usage:
 *
 *      # Base Sepolia (testnet)
 *      forge script script/Deploy.s.sol \
 *        --rpc-url base_sepolia \
 *        --broadcast \
 *        --verify
 *
 *      # Base mainnet (Council Lv9 chair-signed multisig only)
 *      forge script script/Deploy.s.sol \
 *        --rpc-url base_mainnet \
 *        --broadcast \
 *        --verify
 *
 *      Environment:
 *        DEPLOYER_PRIVATE_KEY   — deployer's hot key (NEVER a Lv9 chair key)
 *        BASE_SEPOLIA_RPC_URL   — public Base Sepolia RPC (e.g. Alchemy)
 *        BASE_MAINNET_RPC_URL   — Base mainnet RPC
 *        BASESCAN_API_KEY       — for source verification
 *
 *      Output addresses are recorded in 90-docs/deployments/yobel.md
 *      (committed back to the repo for indexer + verifier configuration).
 */
contract Deploy is Script {
    function run() external returns (YobelRiteRegistry, YobelReleaseRegistry) {
        uint256 pk = vm.envUint("DEPLOYER_PRIVATE_KEY");
        vm.startBroadcast(pk);

        YobelRiteRegistry rite = new YobelRiteRegistry();
        YobelReleaseRegistry rel = new YobelReleaseRegistry(rite);

        vm.stopBroadcast();

        // Hand the addresses back for downstream tooling.
        console2.log("YobelRiteRegistry deployed at:    ", address(rite));
        console2.log("YobelReleaseRegistry deployed at: ", address(rel));
        return (rite, rel);
    }
}
