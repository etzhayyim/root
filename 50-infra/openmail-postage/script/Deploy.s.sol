// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Script.sol";
import {Postage, IERC20} from "../src/Postage.sol";

/**
 * @notice Deploy Postage to Base mainnet or Base Sepolia.
 *         Reads from env:
 *           USDC_ADDR        — USDC token address (chain-specific)
 *           TREASURY_ADDR    — etzhayyim treasury Safe address
 *           INITIAL_RATE     — USDC base units per recipient (default 10_000 = 0.01 USDC)
 *           PRIVATE_KEY      — deployer key (rotates owner to TREASURY_ADDR after deploy
 *                              if SET_OWNER_TO_TREASURY=1)
 *
 *         Example:
 *           forge script script/Deploy.s.sol \
 *             --rpc-url base_sepolia \
 *             --broadcast --verify
 */
contract Deploy is Script {
    function run() external returns (Postage postage) {
        address usdc = vm.envAddress("USDC_ADDR");
        address treasury = vm.envAddress("TREASURY_ADDR");
        uint256 initialRate = vm.envOr("INITIAL_RATE", uint256(10_000)); // 0.01 USDC
        uint256 pk = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(pk);
        postage = new Postage(IERC20(usdc), treasury, initialRate);

        if (vm.envOr("SET_OWNER_TO_TREASURY", uint256(0)) == 1) {
            postage.setOwner(treasury);
        }
        vm.stopBroadcast();

        console2.log("Postage deployed at:", address(postage));
        console2.log("  usdc:", usdc);
        console2.log("  treasury:", treasury);
        console2.log("  rate (USDC base units):", initialRate);
        console2.log("  owner:", postage.owner());
    }
}
