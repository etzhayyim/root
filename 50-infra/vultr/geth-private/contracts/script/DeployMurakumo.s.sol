// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import {MurakumoEscrow} from "../src/MurakumoEscrow.sol";
import {MurakumoRegistry} from "../src/MurakumoRegistry.sol";

/// @title Phase 2-A.3 — Murakumo inference economy contracts
///
/// Incremental on top of Phase 2-A (run after `Deploy.s.sol`). Reads the
/// existing GCC address from the `GCC_ADDR` env var rather than deploying
/// a fresh token, so escrow + registry latch onto the canonical GCC.
contract DeployMurakumo is Script {
    function run() external {
        uint256 deployerPk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPk);
        address gccAddr = vm.envAddress("GCC_ADDR");
        require(gccAddr.code.length > 0, "GCC_ADDR has no code on this chain");

        vm.startBroadcast(deployerPk);

        MurakumoRegistry registry = new MurakumoRegistry(
            IERC20(gccAddr),
            deployer,            // owner = sealer (Phase 3 → multisig)
            1_000 ether          // minStake = 1000 GCC
        );
        console.log("MurakumoRegistry: ", address(registry));

        MurakumoEscrow escrow = new MurakumoEscrow(
            IERC20(gccAddr),
            registry,
            deployer,            // oracle = sealer (rotates separately Phase 3)
            deployer,            // treasury = sealer (Phase 3 → multisig)
            deployer             // owner = sealer
        );
        console.log("MurakumoEscrow:   ", address(escrow));

        vm.stopBroadcast();

        // Sanity: reads back the immutables / config wiring.
        require(address(registry.gcc()) == gccAddr, "registry GCC mismatch");
        require(address(escrow.gcc()) == gccAddr, "escrow GCC mismatch");
        require(address(escrow.registry()) == address(registry), "escrow registry mismatch");
        require(escrow.operatorBps() == 7_000, "operatorBps mismatch");
        require(escrow.treasuryBps() == 2_500, "treasuryBps mismatch");
        require(escrow.referrerBps() == 500,   "referrerBps mismatch");
        require(registry.minStake() == 1_000 ether, "minStake mismatch");
        console.log("Post-deploy sanity: all checks pass");
    }
}
