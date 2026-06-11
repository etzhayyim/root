// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Script.sol";
import {EtzhayyimAuthz} from "../src/EtzhayyimAuthz.sol";

/**
 * @title Deploy
 * @notice Phase α P0 of ADR-2605212030 — deploy EtzhayyimAuthz to a target
 *         chain (local Anvil / Base Sepolia / Base mainnet).
 *
 *         The Council 5-of-7 Safe is the canonical owner on mainnet. For
 *         testnet smoke runs, a deployer-controlled key is acceptable.
 *
 * Usage:
 *   forge script script/Deploy.s.sol:Deploy \
 *     --sig "run(address)" <COUNCIL_SAFE> \
 *     --rpc-url base_sepolia --broadcast --verify
 *
 *   forge script script/Deploy.s.sol:Deploy \
 *     --sig "runLocal()" \
 *     --rpc-url http://localhost:8545 --broadcast \
 *     --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
 */
contract Deploy is Script {
    function run(address councilSafe) external returns (address authz) {
        require(councilSafe != address(0), "councilSafe is zero");
        vm.startBroadcast();
        EtzhayyimAuthz authzContract = new EtzhayyimAuthz(councilSafe);
        vm.stopBroadcast();
        authz = address(authzContract);
        console.log("EtzhayyimAuthz deployed at:", authz);
        console.log("owner (Council Safe):", authzContract.owner());
    }

    function runLocal() external returns (address authz) {
        // Anvil default account #0
        address councilSafe = 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266;
        vm.startBroadcast();
        EtzhayyimAuthz authzContract = new EtzhayyimAuthz(councilSafe);
        vm.stopBroadcast();
        authz = address(authzContract);
        console.log("EtzhayyimAuthz (local) deployed at:", authz);
        console.log("owner:", authzContract.owner());
    }
}
