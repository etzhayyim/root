// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Script.sol";
import {Reserve, IERC20} from "../src/Reserve.sol";

/**
 * @title Deploy
 * @notice Phase δ of ADR-2605212050 — deploy Reserve to a target chain.
 *
 *         USDC addresses:
 *           - Base mainnet: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
 *           - Base Sepolia: 0x036CbD53842c5426634e7929541eC2318f3dCF7e
 *             (Circle-issued Sepolia USDC, per Coinbase docs)
 *
 *         Initial daily cap default: 50_000 USDC = 50_000_000_000 micros.
 *         Council can adjust via setDailyCap().
 *
 * Usage:
 *   forge script script/Deploy.s.sol:Deploy \
 *     --sig "run(address,address,address,uint256)" \
 *     <COUNCIL_SAFE> <USDC> <PUBLIC_FUND_SAFE> <DAILY_CAP_MICROS> \
 *     --rpc-url base_sepolia --broadcast --verify
 */
contract Deploy is Script {
    function run(
        address councilSafe,
        address usdc,
        address publicFundSafe,
        uint256 dailyCapMicros
    ) external returns (address reserve) {
        require(councilSafe != address(0), "councilSafe is zero");
        require(usdc != address(0), "usdc is zero");
        require(publicFundSafe != address(0), "publicFundSafe is zero");
        require(dailyCapMicros > 0, "dailyCapMicros is zero");

        vm.startBroadcast();
        Reserve r = new Reserve(councilSafe, IERC20(usdc), publicFundSafe, dailyCapMicros);
        vm.stopBroadcast();
        reserve = address(r);
        console.log("Reserve deployed at:    ", reserve);
        console.log("owner (Council Safe):   ", councilSafe);
        console.log("USDC token:             ", usdc);
        console.log("Public Fund Safe:       ", publicFundSafe);
        console.log("daily cap (micros):     ", dailyCapMicros);
    }
}
