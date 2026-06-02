// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {GCCMinter} from "../src/GCCMinter.sol";

/**
 * @title DeployMinter
 * @notice Deploy the GCCMinter contract on Ethereum mainnet.
 *
 * Dry-run:
 *   forge script script/DeployMinter.s.sol:DeployMinter \
 *       --rpc-url $MAINNET_RPC_URL \
 *       --private-key $DEPLOYER_PRIVATE_KEY
 *
 * Broadcast + verify:
 *   forge script script/DeployMinter.s.sol:DeployMinter \
 *       --rpc-url $MAINNET_RPC_URL \
 *       --private-key $DEPLOYER_PRIVATE_KEY \
 *       --broadcast --verify --slow
 *
 * After deployment:
 *   1. Safe calls GCC.configureMinter(minterAddress, 100_000_000_000e6)
 *   2. Safe calls GCCMinter.transferOwnership(safeAddress)  [or deployer does it]
 */
contract DeployMinter is Script {
    // Mainnet addresses
    address constant GCC_TOKEN = 0x799d24a6FFBb758C6E2Ed8f981822A17Eaa5F30B;
    address constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
    address constant USDT = 0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address constant ETH_USD_FEED = 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419; // Chainlink ETH/USD (8 dec)
    address constant SAFE = 0xA00366234D29d4F882088048c0B2fa0dB7302D4E;

    function run() external {
        address deployer = msg.sender;
        console.log("Deployer:", deployer);
        console.log("Chain ID:", block.chainid);

        vm.startBroadcast();

        GCCMinter minter = new GCCMinter(
            GCC_TOKEN,
            USDC,
            USDT,
            ETH_USD_FEED,
            SAFE,       // treasury — ETH/stablecoins go here
            deployer,   // owner — transfer to Safe after deployment
            1e6         // stablecoinRate: 1 USDC = 1 GCC (1:1)
        );

        console.log("GCCMinter deployed at:", address(minter));

        // Transfer ownership to Safe
        minter.transferOwnership(SAFE);
        console.log("Ownership transferred to Safe:", SAFE);

        vm.stopBroadcast();

        console.log("=== Deployment Summary ===");
        console.log("Minter:        ", address(minter));
        console.log("GCC Token:     ", address(minter.gcc()));
        console.log("USDC:          ", minter.usdc());
        console.log("USDT:          ", minter.usdt());
        console.log("ETH/USD Feed:  ", address(minter.ethUsdFeed()));
        console.log("Treasury:      ", minter.treasury());
        console.log("Owner:         ", minter.owner());
        console.log("Rate:          ", minter.stablecoinRate());
        console.log("");
        console.log("=== Next Steps ===");
        console.log("1. Safe calls: GCC.configureMinter(minterAddress, 100_000_000_000e6)");
        console.log("   This grants the minter contract permission to mint GCC.");
    }
}
