// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import {ContributionRoyaltyRegistry} from "../src/ContributionRoyaltyRegistry.sol";

/// @title ADR-2604281400 Phase 1 — deploy ContributionRoyaltyRegistry
///
/// @notice Deploys a fresh registry and (optionally) funds it with an initial
///         GCC seed from the deployer wallet.
///
///         Required env vars:
///           PRIVATE_KEY  — deployer / oracle key (sealer EOA in Phase 1)
///           GCC_ADDR     — GCCStablecoin address (0x8e9A…)
///           SAFE_ADDR    — Gnosis Safe address that becomes owner (0xc0C2…)
///           SEED_AMOUNT  — optional, initial GCC to seed in wei (default 0)
///
///         Example (dry-run):
///           forge script script/DeployContributionRegistry.s.sol \
///             --rpc-url https://geth.etzhayyim.com --legacy
///
///         Example (broadcast):
///           MIGRATE_LIVE=true \
///           forge script script/DeployContributionRegistry.s.sol \
///             --rpc-url https://geth.etzhayyim.com --broadcast --legacy -vvv
contract DeployContributionRegistry is Script {
    function run() external {
        uint256 deployerPk = vm.envUint("PRIVATE_KEY");
        address deployer   = vm.addr(deployerPk);
        address gccAddr    = vm.envAddress("GCC_ADDR");
        address safeAddr   = vm.envOr("SAFE_ADDR", deployer);
        uint256 seedAmount = vm.envOr("SEED_AMOUNT", uint256(0));

        require(gccAddr.code.length > 0, "GCC_ADDR has no code on this chain");

        vm.startBroadcast(deployerPk);

        ContributionRoyaltyRegistry registry = new ContributionRoyaltyRegistry(
            gccAddr,
            deployer,  // oracle = sealer EOA (Phase 2: dedicated BPMN bot key)
            safeAddr   // owner  = Safe multisig
        );
        console.log("ContributionRoyaltyRegistry:", address(registry));
        console.log("  gcc:    ", address(registry.gcc()));
        console.log("  oracle: ", registry.oracle());

        if (seedAmount > 0) {
            IERC20 gcc = IERC20(gccAddr);
            require(gcc.transfer(address(registry), seedAmount), "seed transfer failed");
            console.log("  seeded: ", seedAmount);
        }

        vm.stopBroadcast();

        // Sanity checks
        require(address(registry.gcc()) == gccAddr, "gcc mismatch");
        require(registry.oracle() == deployer, "oracle mismatch");
        console.log("Post-deploy sanity: all checks pass");
    }
}
