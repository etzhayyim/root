// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Script.sol";
import {EtzhayyimMembership} from "../src/EtzhayyimMembership.sol";

contract Deploy is Script {
    function run() external returns (EtzhayyimMembership) {
        uint256 pk = vm.envUint("DEPLOYER_PRIVATE_KEY");
        vm.startBroadcast(pk);
        EtzhayyimMembership reg = new EtzhayyimMembership();
        vm.stopBroadcast();
        console2.log("EtzhayyimMembership deployed at:", address(reg));
        console2.log("Next: deps.toml [platform.l2.membership_contract].address_* = ", address(reg));
        console2.log("Next: EtzhayyimPaymaster.setAllowedTarget(", address(reg), ", true)");
        return reg;
    }
}
