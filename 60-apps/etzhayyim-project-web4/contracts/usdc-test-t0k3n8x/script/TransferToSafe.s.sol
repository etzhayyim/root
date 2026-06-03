// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {TestUSDC} from "../src/TestUSDC.sol";

/**
 * @title TransferToSafe
 * @notice Transfer all admin roles from deployer EOA to a Safe multisig.
 *
 * Transfers: masterMinter, pauser, blacklister, rescuer, owner → Safe.
 * After this tx the deployer EOA has zero privileges.
 *
 * Usage:
 *   TOKEN_ADDRESS=0x... SAFE_ADDRESS=0x... \
 *   forge script script/TransferToSafe.s.sol:TransferToSafe \
 *       --rpc-url $MAINNET_RPC_URL \
 *       --private-key $DEPLOYER_PRIVATE_KEY \
 *       --broadcast --slow
 */
contract TransferToSafe is Script {
    function run() external {
        address tokenAddr = vm.envAddress("TOKEN_ADDRESS");
        address safeAddr = vm.envAddress("SAFE_ADDRESS");

        require(tokenAddr != address(0), "TOKEN_ADDRESS not set");
        require(safeAddr != address(0), "SAFE_ADDRESS not set");

        TestUSDC token = TestUSDC(tokenAddr);

        console.log("Token:        ", tokenAddr);
        console.log("Safe:         ", safeAddr);
        console.log("Current owner:", token.owner());

        vm.startBroadcast();

        // 1. Transfer masterMinter role to Safe
        token.updateMasterMinter(safeAddr);
        console.log("masterMinter -> Safe");

        // 2. Transfer pauser role to Safe
        token.updatePauser(safeAddr);
        console.log("pauser -> Safe");

        // 3. Transfer blacklister role to Safe
        token.updateBlacklister(safeAddr);
        console.log("blacklister -> Safe");

        // 4. Transfer rescuer role to Safe
        token.updateRescuer(safeAddr);
        console.log("rescuer -> Safe");

        // 5. Transfer ownership (must be last — loses onlyOwner access)
        token.transferOwnership(safeAddr);
        console.log("owner -> Safe");

        vm.stopBroadcast();

        console.log("=== All roles transferred to Safe ===");
    }
}
