// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Script.sol";
import {KarmaAnchor} from "../src/KarmaAnchor.sol";
import {CohortLifecycle} from "../src/CohortLifecycle.sol";

/**
 * @title Deploy
 * @notice Phase β of ADR-2605212040 — deploy KarmaAnchor + CohortLifecycle
 *         to a target chain (local Anvil / Base Sepolia / Base mainnet).
 *         Council 5-of-7 Safe is the canonical owner on mainnet.
 *
 * Usage:
 *   forge script script/Deploy.s.sol:Deploy \
 *     --sig "run(address)" <COUNCIL_SAFE> \
 *     --rpc-url base_sepolia --broadcast --verify
 *
 *   forge script script/Deploy.s.sol:Deploy \
 *     --sig "runLocal()" --rpc-url http://localhost:8545 --broadcast \
 *     --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
 */
contract Deploy is Script {
    struct K2Deployment {
        address karmaAnchor;
        address cohortLifecycle;
    }

    function run(address councilSafe) external returns (K2Deployment memory dep) {
        require(councilSafe != address(0), "councilSafe is zero");
        vm.startBroadcast();
        KarmaAnchor ka = new KarmaAnchor(councilSafe);
        CohortLifecycle cl = new CohortLifecycle(councilSafe);
        vm.stopBroadcast();
        dep = K2Deployment({karmaAnchor: address(ka), cohortLifecycle: address(cl)});
        console.log("KarmaAnchor deployed at:    ", dep.karmaAnchor);
        console.log("CohortLifecycle deployed at:", dep.cohortLifecycle);
        console.log("owner (Council Safe):       ", councilSafe);
    }

    function runLocal() external returns (K2Deployment memory dep) {
        address councilSafe = 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266;
        vm.startBroadcast();
        KarmaAnchor ka = new KarmaAnchor(councilSafe);
        CohortLifecycle cl = new CohortLifecycle(councilSafe);
        vm.stopBroadcast();
        dep = K2Deployment({karmaAnchor: address(ka), cohortLifecycle: address(cl)});
        console.log("KarmaAnchor (local) at:    ", dep.karmaAnchor);
        console.log("CohortLifecycle (local) at:", dep.cohortLifecycle);
    }
}
