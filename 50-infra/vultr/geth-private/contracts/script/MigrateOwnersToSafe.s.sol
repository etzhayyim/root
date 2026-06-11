// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";

// ─── Contract role surfaces ──────────────────────────────────────────────────
// Minimal interfaces so we don't pull the whole repo into the script.

interface IOwnable {
    function owner() external view returns (address);
    function transferOwnership(address newOwner) external;
}

interface IGCCStablecoin is IOwnable {
    function masterMinter() external view returns (address);
    function pauser() external view returns (address);
    function blacklister() external view returns (address);
    function updateMasterMinter(address) external;
    function updatePauser(address) external;
    function updateBlacklister(address) external;
}

interface IMurakumoEscrow is IOwnable {
    function oracle() external view returns (address);
    function treasury() external view returns (address);
    function setOracle(address) external;
    function setTreasury(address) external;
}

interface IClaimStakeEscrow is IOwnable {
    function arbiter() external view returns (address);
    function treasury() external view returns (address);
    function rewardPool() external view returns (address);
    function setArbiter(address) external;
    function setTreasury(address) external;
    function setRewardPool(address) external;
}

interface IRegoArbiter is IOwnable {
    function setSigner(address signer, bool authorized) external;
}

/// @title MigrateOwnersToSafe
/// @notice Phase 3 owner migration — sealer → Safe. ADR-2604270900.
/// @dev    `simulate(safe)` prints what `execute(safe)` would do without
///         broadcasting any transaction. `execute(safe)` is gated by the
///         `MIGRATE_LIVE=true` env var so a casual `forge script` won't
///         fire role transfers on geth-private. See ADR §"Migration script".
contract MigrateOwnersToSafe is Script {
    // Addresses are mirrored from
    // `50-infra/vultr/geth-private/contracts/ADDRESSES.md`. Re-run after any
    // contract redeploy.
    address constant GCC                          = 0x8e9A5162b2800E0D19acC1708A531A3954900E21;
    address constant DEPLOY_REGISTRY              = 0x995AD6A2bb4D8916Ba036f5B2e29E7739Ee243b5;
    address constant etzhayyim_ACTOR_REGISTRY          = 0xc097cC8f6dfa6f3a539b0De36E9Bb550B9AA7025;
    address constant etzhayyim_ROOT_IDENTITY_REGISTRY  = 0x11405300Fb75C5CDd665B9c0Ef445F8E312e3ee8;
    address constant etzhayyim_AGENT_REGISTRY          = 0xcA3480edDAfa39c9377B83eEB18291286C8Cb865;
    address constant ACTOR_RUNTIME_REGISTRY       = 0x9C730960e9BF7A403E610Dca0C8a565CF655b6a1;
    address constant MURAKUMO_REGISTRY            = 0x4E3d742ece9483f97c3094b40c4b8C7901a6E3B6;
    address constant MURAKUMO_ESCROW              = 0xD0DAB2B574948d4c8Bb9cF1D751CD0C6662f484d; // v2 ERC-1271
    address constant CLAIM_STAKE_ESCROW           = 0x8448Bd7FC883d0735D8A2416DAd0B7e4FbFA9767; // v2 ERC-1271
    address constant REGO_ARBITER                 = 0x53E29CA12Bd77fD35926627318036c7B2BBE245d;

    address constant SEALER = 0xaFed0Cb7633EDBd26aA52658e71528309F562501;

    error SafeIsZero();
    error SafeIsEOA();
    error SafeIsSealer();
    error LiveGateMissing();

    function simulate(address safe) external {
        _validateSafe(safe);
        console2.log("=== MigrateOwnersToSafe simulate ===");
        console2.log("safe   :", safe);
        console2.log("sealer :", SEALER);
        console2.log("");
        _planRolesPerContract(safe, /*broadcast*/ false);
        console2.log("");
        console2.log("=== plan complete (no tx broadcast) ===");
    }

    function execute(address safe) external {
        // Gate: MIGRATE_LIVE=true must be set in env. Without it, a stray
        // `forge script ... --broadcast` cannot fire transfers.
        try vm.envBool("MIGRATE_LIVE") returns (bool live) {
            if (!live) revert LiveGateMissing();
        } catch {
            revert LiveGateMissing();
        }
        _validateSafe(safe);

        vm.startBroadcast();
        _planRolesPerContract(safe, /*broadcast*/ true);
        vm.stopBroadcast();
    }

    // ─── helpers ─────────────────────────────────────────────────────────────

    function _validateSafe(address safe) internal view {
        if (safe == address(0)) revert SafeIsZero();
        if (safe.code.length == 0) revert SafeIsEOA();
        if (safe == SEALER) revert SafeIsSealer();
    }

    function _planRolesPerContract(address safe, bool broadcast) internal {
        // Single-role contracts (just `owner()`).
        // Note: etzhayyimActorRegistry has no Ownable — activate() is permissionless
        // by design and requires no ownership transfer.
        _maybeTransferOwnership("DeployRegistry",            DEPLOY_REGISTRY,             safe, broadcast);
        _maybeTransferOwnership("etzhayyimRootIdentityRegistry",  etzhayyim_ROOT_IDENTITY_REGISTRY, safe, broadcast);
        _maybeTransferOwnership("etzhayyimAgentRegistry",         etzhayyim_AGENT_REGISTRY,         safe, broadcast);
        _maybeTransferOwnership("ActorRuntimeRegistry",      ACTOR_RUNTIME_REGISTRY,      safe, broadcast);
        _maybeTransferOwnership("MurakumoRegistry",          MURAKUMO_REGISTRY,           safe, broadcast);

        // GCCStablecoin — 4 roles. Role setters require onlyOwner, so rotate
        // non-owner roles first, then transfer ownership last.
        IGCCStablecoin gcc = IGCCStablecoin(GCC);
        _maybeRotate("GCC.masterMinter", gcc.masterMinter(), safe, broadcast, abi.encodeCall(IGCCStablecoin.updateMasterMinter, (safe)), GCC);
        _maybeRotate("GCC.pauser",       gcc.pauser(),       safe, broadcast, abi.encodeCall(IGCCStablecoin.updatePauser,       (safe)), GCC);
        _maybeRotate("GCC.blacklister",  gcc.blacklister(),  safe, broadcast, abi.encodeCall(IGCCStablecoin.updateBlacklister,  (safe)), GCC);
        _maybeTransferOwnership("GCCStablecoin",             GCC,                         safe, broadcast);

        // MurakumoEscrow — 3 roles. Same: rotate first, transfer ownership last.
        IMurakumoEscrow me = IMurakumoEscrow(MURAKUMO_ESCROW);
        _maybeRotate("MurakumoEscrow.oracle",   me.oracle(),   safe, broadcast, abi.encodeCall(IMurakumoEscrow.setOracle,   (safe)), MURAKUMO_ESCROW);
        _maybeRotate("MurakumoEscrow.treasury", me.treasury(), safe, broadcast, abi.encodeCall(IMurakumoEscrow.setTreasury, (safe)), MURAKUMO_ESCROW);
        _maybeTransferOwnership("MurakumoEscrow",            MURAKUMO_ESCROW,             safe, broadcast);

        // ClaimStakeEscrow — 4 roles. Same: rotate first, transfer ownership last.
        IClaimStakeEscrow cse = IClaimStakeEscrow(CLAIM_STAKE_ESCROW);
        _maybeRotate("ClaimStakeEscrow.arbiter",    cse.arbiter(),    safe, broadcast, abi.encodeCall(IClaimStakeEscrow.setArbiter,    (safe)), CLAIM_STAKE_ESCROW);
        _maybeRotate("ClaimStakeEscrow.treasury",   cse.treasury(),   safe, broadcast, abi.encodeCall(IClaimStakeEscrow.setTreasury,   (safe)), CLAIM_STAKE_ESCROW);
        _maybeRotate("ClaimStakeEscrow.rewardPool", cse.rewardPool(), safe, broadcast, abi.encodeCall(IClaimStakeEscrow.setRewardPool, (safe)), CLAIM_STAKE_ESCROW);
        _maybeTransferOwnership("ClaimStakeEscrow",          CLAIM_STAKE_ESCROW,          safe, broadcast);

        // RegoArbiter — owner only (signers are an allow-list, not transferred wholesale).
        _maybeTransferOwnership("RegoArbiter",               REGO_ARBITER,                safe, broadcast);
        // Note: rego-arbiter-settler bot's signer key (separate ECDSA, see
        // 50-infra/vultr/rego-arbiter-settler/CLAUDE.md) stays on the bot's
        // own keypair — Phase 3 does NOT rotate it through Safe. Safe only
        // gains the ability to add/remove signers via setSigner, which is
        // what the new RegoArbiter.owner can call.
    }

    function _maybeTransferOwnership(
        string memory label,
        address target,
        address safe,
        bool broadcast
    ) internal {
        address current = IOwnable(target).owner();
        if (current == safe) {
            console2.log(unicode"  ✓ skip", label, "already owned by safe");
            return;
        }
        if (current != SEALER) {
            console2.log(unicode"  ⚠ skip", label, "owner is neither sealer nor safe");
            console2.log("       owner=", current);
            return;
        }
        console2.log(unicode"  →     transferOwnership", label, unicode"→ safe");
        if (broadcast) {
            IOwnable(target).transferOwnership(safe);
        }
    }

    function _maybeRotate(
        string memory label,
        address current,
        address safe,
        bool broadcast,
        bytes memory callData,
        address target
    ) internal {
        if (current == safe) {
            console2.log(unicode"  ✓ skip", label, "already safe");
            return;
        }
        if (current != SEALER) {
            console2.log(unicode"  ⚠ skip", label, "current is neither sealer nor safe");
            console2.log("       current=", current);
            return;
        }
        console2.log(unicode"  →     rotate", label, unicode"→ safe");
        if (broadcast) {
            (bool ok,) = target.call(callData);
            require(ok, "rotate: call failed");
        }
    }
}
