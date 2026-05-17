// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Script.sol";
import {EtzhayyimAnchor} from "../src/EtzhayyimAnchor.sol";

contract Deploy is Script {
    function run() external returns (EtzhayyimAnchor) {
        uint256 pk = vm.envUint("DEPLOYER_PRIVATE_KEY");
        vm.startBroadcast(pk);
        EtzhayyimAnchor a = new EtzhayyimAnchor();
        vm.stopBroadcast();
        return a;
    }
}
