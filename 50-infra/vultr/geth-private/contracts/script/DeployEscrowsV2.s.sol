// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import {ClaimStakeEscrow} from "../src/ClaimStakeEscrow.sol";
import {MurakumoEscrow} from "../src/MurakumoEscrow.sol";
import {MurakumoRegistry} from "../src/MurakumoRegistry.sol";

/// @title DeployEscrowsV2
/// @notice Deploys ERC-1271–enabled v2 of ClaimStakeEscrow + MurakumoEscrow.
///
///         v2 differences from v1:
///         - `settle()` / `settleJob()` accept both EOA ECDSA sigs (bot path,
///           backward compat) AND ERC-1271 contract sigs (Safe multisig path).
///
///         Ownership is transferred to the Safe multisig at deploy time so the
///         new contracts are immediately under multisig governance.
///         `arbiter` and `oracle` remain the sealer key so the existing
///         rego-arbiter-settler bot can continue to sign settlements without
///         any config change.
///
/// @dev    Environment variables required:
///         GCC_ADDR                  — GCCStablecoin proxy address
///         MURAKUMO_REGISTRY_ADDR    — MurakumoRegistry address
///         SAFE_ADDR                 — Gnosis Safe multisig (owner of new contracts)
///         SEALER_ADDR               — sealer EOA (arbiter + oracle + treasury + rewardPool)
///         PRIVATE_KEY               — deployer private key (sealer for gas)
contract DeployEscrowsV2 is Script {
    function run() external {
        uint256 deployerPk    = vm.envUint("PRIVATE_KEY");
        address gcc           = vm.envAddress("GCC_ADDR");
        address registry      = vm.envAddress("MURAKUMO_REGISTRY_ADDR");
        address safe          = vm.envAddress("SAFE_ADDR");
        address sealer        = vm.envAddress("SEALER_ADDR");

        require(gcc.code.length > 0,      "GCC_ADDR has no code");
        require(registry.code.length > 0, "MURAKUMO_REGISTRY_ADDR has no code");
        require(safe.code.length > 0,     "SAFE_ADDR has no code");

        vm.startBroadcast(deployerPk);

        ClaimStakeEscrow claimEscrow = new ClaimStakeEscrow(
            IERC20(gcc),
            sealer,   // arbiter  — sealer key; rego-arbiter-settler bot signs unchanged
            safe,     // treasury — Safe governs fee destination
            safe,     // rewardPool — Safe governs subsidy pool
            safe      // owner    — Safe multisig owns from deploy
        );
        console.log("ClaimStakeEscrow v2:", address(claimEscrow));

        MurakumoEscrow murakumoEscrow = new MurakumoEscrow(
            IERC20(gcc),
            MurakumoRegistry(registry),
            sealer,   // oracle   — sealer key; gateway signs unchanged
            safe,     // treasury — Safe governs fee destination
            safe      // owner    — Safe multisig owns from deploy
        );
        console.log("MurakumoEscrow v2:  ", address(murakumoEscrow));

        vm.stopBroadcast();

        // Sanity checks.
        require(claimEscrow.owner()           == safe,   "CSE owner mismatch");
        require(claimEscrow.arbiter()         == sealer, "CSE arbiter mismatch");
        require(claimEscrow.treasury()        == safe,   "CSE treasury mismatch");
        require(claimEscrow.rewardPool()      == safe,   "CSE rewardPool mismatch");
        require(murakumoEscrow.owner()        == safe,   "ME owner mismatch");
        require(murakumoEscrow.oracle()       == sealer, "ME oracle mismatch");
        require(murakumoEscrow.treasury()     == safe,   "ME treasury mismatch");
        console.log("Post-deploy sanity: all checks pass");
        console.log("");
        console.log("Next steps:");
        console.log("1. Update ADDRESSES.md with new addresses above");
        console.log("2. Update authz Worker secrets:");
        console.log("   etzhayyim_CLAIM_STAKE_ESCROW_ADDR =", address(claimEscrow));
        console.log("   etzhayyim_MURAKUMO_ESCROW_ADDR    =", address(murakumoEscrow));
    }
}
