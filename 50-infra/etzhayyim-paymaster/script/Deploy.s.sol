// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Script.sol";
import {EtzhayyimPaymaster, IEntryPoint} from "../src/EtzhayyimPaymaster.sol";

contract Deploy is Script {
    /// @notice Canonical EntryPoint v0.7 address on all EVM L2s.
    address constant ENTRY_POINT_V07 = 0x0000000071727De22E5E9d8BAf0edAc6f37da032;

    function run() external returns (EtzhayyimPaymaster) {
        uint256 pk = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address owner = vm.envAddress("PAYMASTER_OWNER"); // 2-of-3 Safe address
        vm.startBroadcast(pk);
        EtzhayyimPaymaster pm = new EtzhayyimPaymaster(IEntryPoint(ENTRY_POINT_V07), owner);
        vm.stopBroadcast();
        console2.log("EtzhayyimPaymaster deployed at:", address(pm));
        console2.log("Owner (Safe):", owner);
        console2.log("Next: send ETH to paymaster (auto-forwarded to EntryPoint via receive())");
        console2.log("Next: cast send paymaster addStake(uint32) 86400 --value 0.1ether");
        return pm;
    }
}
