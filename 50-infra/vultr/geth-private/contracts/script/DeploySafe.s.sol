// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import {Script, console2} from "forge-std/Script.sol";

/// @title  DeploySafe
/// @notice Deploys Safe v1.4.1 to geth-private (chainId 260425) and creates a
///         single multisig with the operator-supplied owner set + threshold.
///         Required pre-flight for ADR-2604270900 / `MigrateOwnersToSafe.s.sol`.
///
/// @dev    Build path: prebuilt Safe v1.4.1 artifacts (hardhat-compiled by
///         the Safe team and shipped via the npm package
///         `safe-global/safe-contracts` at version 1.4.1) are loaded via
///         `vm.readFile` + `vm.parseJsonBytes` and deployed with assembly
///         `create`. Re-compiling Safe sources under the etzhayyim toolchain
///         (solc 0.8.23, evm_version=paris) hits a Yul stack-too-deep on
///         `Safe.execTransaction` regardless of optimizer / via_ir
///         settings — Safe is pinned to solc 0.7.6 upstream, and we keep
///         the etzhayyim contracts on 0.8.23. Pulling the prebuilt JSON
///         sidesteps that mismatch entirely while still giving us
///         canonical, audited Safe bytecode.
///
///         Two-stage by design:
///
///         1. `forge script ... --sig 'simulate(address[],uint256,uint256)' \
///                  '[<K1>,<K2>,<K3>]' 2 0` — prints the predicted Safe address.
///
///         2. `MIGRATE_LIVE=true forge script ... --broadcast \
///                  --sig 'execute(address[],uint256,uint256)' \
///                  '[<K1>,<K2>,<K3>]' 2 0` — actually deploys, sealer-signed.
///
///         Owner set is operator-supplied — this script does NOT pin a default.
///         Picking owners is a governance decision (ADR §"Owner set" recommends
///         K1=operator/Keychain, K2=co-owner/Keychain, K3=cold-storage hardware).
contract DeploySafe is Script {
    address constant SEALER = 0xaFed0Cb7633EDBd26aA52658e71528309F562501;

    // Hardhat artifact paths (shipped under node_modules/@safe-global/safe-contracts).
    // Read with `vm.readFile` so foundry can deploy without re-compiling Safe.
    string constant SAFE_ARTIFACT_PATH    = "node_modules/@safe-global/safe-contracts/build/artifacts/contracts/Safe.sol/Safe.json";
    string constant FACTORY_ARTIFACT_PATH = "node_modules/@safe-global/safe-contracts/build/artifacts/contracts/proxies/SafeProxyFactory.sol/SafeProxyFactory.json";
    string constant HANDLER_ARTIFACT_PATH = "node_modules/@safe-global/safe-contracts/build/artifacts/contracts/handler/CompatibilityFallbackHandler.sol/CompatibilityFallbackHandler.json";

    error LiveGateMissing();
    error OwnerListEmpty();
    error ThresholdInvalid();
    error DuplicateOwner(address dup);
    error OwnerIsZero();
    error OwnerIsSealer(address owner);
    error DeployFailed(string label);
    error CallFailed(string label);

    /// Pre-flight checks + simulation. Forge writes nothing until --broadcast.
    /// @return safe       Safe proxy address
    /// @return singleton  Safe singleton
    /// @return factory    SafeProxyFactory
    /// @return handler    CompatibilityFallbackHandler
    function simulate(address[] calldata owners, uint256 threshold, uint256 saltNonce)
        external
        returns (address safe, address singleton, address factory, address handler)
    {
        _validateOwners(owners, threshold);

        vm.startBroadcast();
        (singleton, factory, handler, safe) = _deployStack(owners, threshold, saltNonce);
        vm.stopBroadcast();

        console2.log("=== DeploySafe simulate ===");
        console2.log("chainId:    ", block.chainid);
        console2.log("singleton:  ", singleton);
        console2.log("factory:    ", factory);
        console2.log("handler:    ", handler);
        console2.log("safe:       ", safe);
        console2.log("threshold:  ", threshold);
        console2.log("saltNonce:  ", saltNonce);
        console2.log("owners (", owners.length, "):");
        for (uint256 i; i < owners.length; ++i) {
            console2.log("  ", i, owners[i]);
        }
        console2.log("");
        console2.log("=== plan complete (forge `--broadcast` not set; nothing landed on chain) ===");
        console2.log("Next: rerun with MIGRATE_LIVE=true + --broadcast to actually deploy.");
    }

    /// Live deploy. Reverts unless MIGRATE_LIVE=true.
    function execute(address[] calldata owners, uint256 threshold, uint256 saltNonce)
        external
        returns (address safe, address singleton, address factory, address handler)
    {
        try vm.envBool("MIGRATE_LIVE") returns (bool live) {
            if (!live) revert LiveGateMissing();
        } catch {
            revert LiveGateMissing();
        }
        _validateOwners(owners, threshold);

        vm.startBroadcast();
        (singleton, factory, handler, safe) = _deployStack(owners, threshold, saltNonce);
        vm.stopBroadcast();

        // Sanity: read back threshold + first owner from chain.
        uint256 readBackThreshold = _readUint256(safe, abi.encodeWithSignature("getThreshold()"));
        require(readBackThreshold == threshold, "threshold mismatch");
        bool isOwner = _readBool(safe, abi.encodeWithSignature("isOwner(address)", owners[0]));
        require(isOwner, "owner[0] missing");

        console2.log("=== DeploySafe execute (BROADCAST) ===");
        console2.log("singleton:  ", singleton);
        console2.log("factory:    ", factory);
        console2.log("handler:    ", handler);
        console2.log("safe:       ", safe);
        console2.log("");
        console2.log("Update 50-infra/vultr/geth-private/contracts/ADDRESSES.md");
        console2.log("with the four addresses above, then run:");
        console2.log("");
        console2.log("  forge script script/MigrateOwnersToSafe.s.sol --rpc-url https://geth.etzhayyim.com \\");
        console2.log("    --sig 'simulate(address)' ", safe);
    }

    // ─── deploy primitives ───────────────────────────────────────────────────

    function _deployStack(address[] calldata owners, uint256 threshold, uint256 saltNonce)
        internal
        returns (address singleton, address factory, address handler, address safe)
    {
        singleton = _createFromArtifact("Safe",                         SAFE_ARTIFACT_PATH);
        factory   = _createFromArtifact("SafeProxyFactory",             FACTORY_ARTIFACT_PATH);
        handler   = _createFromArtifact("CompatibilityFallbackHandler", HANDLER_ARTIFACT_PATH);

        bytes memory initializer = abi.encodeWithSignature(
            "setup(address[],uint256,address,bytes,address,address,uint256,address)",
            owners,
            threshold,
            address(0),                 // to
            "",                         // data
            handler,
            address(0),                 // paymentToken
            uint256(0),                 // payment
            payable(address(0))         // paymentReceiver
        );

        // SafeProxyFactory.createProxyWithNonce(address,bytes,uint256) → SafeProxy
        bytes memory call = abi.encodeWithSignature(
            "createProxyWithNonce(address,bytes,uint256)",
            singleton,
            initializer,
            saltNonce
        );
        (bool ok, bytes memory ret) = factory.call(call);
        if (!ok) revert CallFailed("createProxyWithNonce");
        safe = abi.decode(ret, (address));
    }

    /// Read the `bytecode` field from a hardhat-compiled artifact JSON and
    /// deploy it with `create`. Returns the deployed address.
    function _createFromArtifact(string memory label, string memory path) internal returns (address deployed) {
        string memory artifactJson = vm.readFile(path);
        bytes memory bytecode = vm.parseJsonBytes(artifactJson, ".bytecode");
        // assembly create: stack inputs are (value=0, offset, length).
        // bytes layout: [length][data…]; offset = ptr + 0x20.
        assembly {
            deployed := create(0, add(bytecode, 0x20), mload(bytecode))
        }
        if (deployed == address(0)) revert DeployFailed(label);
        if (deployed.code.length == 0) revert DeployFailed(label);
    }

    function _readUint256(address target, bytes memory call) internal view returns (uint256) {
        (bool ok, bytes memory ret) = target.staticcall(call);
        require(ok && ret.length >= 32, "static read failed");
        return abi.decode(ret, (uint256));
    }

    function _readBool(address target, bytes memory call) internal view returns (bool) {
        (bool ok, bytes memory ret) = target.staticcall(call);
        require(ok && ret.length >= 32, "static read failed");
        return abi.decode(ret, (bool));
    }

    // ─── validation ──────────────────────────────────────────────────────────

    function _validateOwners(address[] calldata owners, uint256 threshold) internal pure {
        if (owners.length == 0) revert OwnerListEmpty();
        if (threshold == 0 || threshold > owners.length) revert ThresholdInvalid();
        for (uint256 i; i < owners.length; ++i) {
            address o = owners[i];
            if (o == address(0)) revert OwnerIsZero();
            // The whole point of Phase 3 is to remove the sealer as the
            // single point of authority; allowing it as a Safe owner
            // re-introduces single-key compromise. Block it explicitly.
            if (o == SEALER) revert OwnerIsSealer(o);
            for (uint256 j = i + 1; j < owners.length; ++j) {
                if (owners[j] == o) revert DuplicateOwner(o);
            }
        }
    }
}
