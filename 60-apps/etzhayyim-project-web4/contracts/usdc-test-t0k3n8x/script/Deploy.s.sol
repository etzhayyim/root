// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {TestUSDC} from "../src/TestUSDC.sol";

/**
 * @title Deploy
 * @notice Deploy GCC (Etzhayyim Computing Credits) and configure initial minter.
 *
 * Step 1 — Dry-run (no gas spent):
 *   forge script script/Deploy.s.sol:Deploy \
 *       --rpc-url $MAINNET_RPC_URL \
 *       --private-key $DEPLOYER_PRIVATE_KEY
 *
 * Step 2 — Broadcast + verify:
 *   forge script script/Deploy.s.sol:Deploy \
 *       --rpc-url $MAINNET_RPC_URL \
 *       --private-key $DEPLOYER_PRIVATE_KEY \
 *       --broadcast --verify --slow
 *
 * Step 3 — Transfer all roles to Safe:
 *   TOKEN_ADDRESS=0x... SAFE_ADDRESS=0x... \
 *   forge script script/TransferToSafe.s.sol:TransferToSafe \
 *       --rpc-url $MAINNET_RPC_URL \
 *       --private-key $DEPLOYER_PRIVATE_KEY \
 *       --broadcast --slow
 */
contract Deploy is Script {
    function run() external {
        // All roles default to deployer; transfer to Safe after deployment
        address deployer = msg.sender;

        console.log("Deployer:", deployer);
        console.log("Chain ID:", block.chainid);

        vm.startBroadcast();

        TestUSDC token = new TestUSDC(
            "Etzhayyim Computing Credits", // name
            "GCC",                    // symbol
            "USD",                    // currency
            deployer,        // masterMinter
            deployer,        // pauser
            deployer,        // blacklister
            deployer         // owner
        );

        console.log("TestUSDC deployed at:", address(token));

        // Configure deployer as minter with 100B GCC allowance
        uint256 mintCap = 100_000_000_000 * 1e6; // 100 billion GCC (6 decimals)
        token.configureMinter(deployer, mintCap);
        console.log("Minter configured with allowance:", mintCap);

        // Mint initial supply to deployer: 10M GCC
        uint256 initialMint = 10_000_000 * 1e6;
        token.mint(deployer, initialMint);
        console.log("Minted initial supply:", initialMint);

        vm.stopBroadcast();

        console.log("=== Deployment Summary ===");
        console.log("Token:         ", address(token));
        console.log("Name:          ", token.name());
        console.log("Symbol:        ", token.symbol());
        console.log("Decimals:       6");
        console.log("Total Supply:  ", token.totalSupply());
        console.log("Owner:         ", token.owner());
        console.log("MasterMinter:  ", token.masterMinter());
    }
}
