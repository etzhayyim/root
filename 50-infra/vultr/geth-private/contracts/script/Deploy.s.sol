// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {EntryPoint} from "account-abstraction/core/EntryPoint.sol";

import {CoinbaseSmartWalletFactory} from "smart-wallet/CoinbaseSmartWalletFactory.sol";

import {DeployRegistry} from "../src/DeployRegistry.sol";
import {GCCStablecoin} from "../src/GCCStablecoin.sol";
import {etzhayyimActorAccount} from "../src/etzhayyimActorAccount.sol";
import {etzhayyimActorRegistry} from "../src/etzhayyimActorRegistry.sol";

/// @title Phase 2-A unified deploy
///
/// Deploys, in dependency order:
///   1. EntryPoint (ERC-4337 v0.6, vendored unchanged from eth-infinitism)
///   2. etzhayyimActorAccount impl (CoinbaseSmartWallet subclass with chain-local
///      EntryPoint override — used as the implementation for all ERC-1967
///      proxies the factory clones)
///   3. CoinbaseSmartWalletFactory (canonical Coinbase factory pointed at
///      our impl)
///   4. etzhayyimActorRegistry (root DID hash → account address index, salt convention)
///   5. GCCStablecoin (USDC-style ERC-20 — credits / stake / payment unit)
///   6. DeployRegistry (`etzhayyim deploy` provenance ledger)
///
/// All admin roles (GCC owner / masterMinter / pauser / blacklister,
/// DeployRegistry owner) start as the deployer (= sealer). Phase 3 will
/// transfer them to a multisig.
contract Deploy is Script {
    function run() external {
        uint256 deployerPk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPk);

        vm.startBroadcast(deployerPk);

        // 1. ERC-4337 EntryPoint v0.6 (canonical contract, vendored unchanged).
        EntryPoint entryPoint = new EntryPoint();
        console.log("EntryPoint:               ", address(entryPoint));

        // 2. Smart-wallet implementation (Coinbase subclass with our EntryPoint).
        etzhayyimActorAccount actorImpl = new etzhayyimActorAccount(address(entryPoint));
        console.log("etzhayyimActorAccount (impl):  ", address(actorImpl));

        // 3. Factory pointed at our subclass — clones ERC-1967 proxies that
        //    delegate to etzhayyimActorAccount.
        CoinbaseSmartWalletFactory cswFactory = new CoinbaseSmartWalletFactory(address(actorImpl));
        console.log("CoinbaseSmartWalletFactory:", address(cswFactory));

        // 4. Root DID hash → account index + salt convention.
        etzhayyimActorRegistry actorRegistry = new etzhayyimActorRegistry(cswFactory);
        console.log("etzhayyimActorRegistry:         ", address(actorRegistry));

        // 5. etzhayyim Compute Credit (GCC) — USDC-style. Deployer holds all roles
        //    initially; configureMinter gives the deployer 100M GCC mint
        //    headroom for bootstrap (Murakumo escrow funding, faucet, etc.).
        GCCStablecoin gcc = new GCCStablecoin(
            "etzhayyim Compute Credit", // name
            "GCC",                  // symbol
            18,                     // decimals
            1_000_000_000 ether,    // supplyCap (1B GCC)
            deployer,               // owner
            deployer,               // masterMinter
            deployer,               // pauser
            deployer                // blacklister
        );
        gcc.configureMinter(deployer, 100_000_000 ether);
        console.log("GCCStablecoin (GCC):       ", address(gcc));

        // 6. Deploy provenance ledger.
        DeployRegistry deployRegistry = new DeployRegistry(deployer);
        console.log("DeployRegistry:            ", address(deployRegistry));

        vm.stopBroadcast();

        // Quick post-deploy sanity — read back from each.
        require(actorImpl.entryPoint() == address(entryPoint), "ep override broken");
        require(cswFactory.implementation() == address(actorImpl), "factory impl mismatch");
        require(address(actorRegistry.factory()) == address(cswFactory), "registry factory mismatch");
        require(gcc.supplyCap() == 1_000_000_000 ether, "gcc cap mismatch");
        require(deployRegistry.owner() == deployer, "deploy registry owner mismatch");
        console.log("Post-deploy sanity:        all checks pass");
    }
}
