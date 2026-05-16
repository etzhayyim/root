// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console} from "forge-std/Script.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import {ClaimStakeEscrow} from "../src/ClaimStakeEscrow.sol";

/// @title ADR-2604261717 Phase 1 — deploy ClaimStakeEscrow
///
/// @notice Incremental on top of Phase 2-A (run after `Deploy.s.sol` and
///         `DeployMurakumo.s.sol`). Reads the existing GCC address from the
///         `GCC_ADDR` env var rather than deploying a fresh token, so the
///         claim escrow latches onto the canonical GCC.
///
/// @dev    `arbiter` defaults to the sealer (single-signer DMN proxy in
///         Phase 1). Phase 2-B introduces a dedicated `RegoArbiter` adapter
///         contract that delegates to a Rego/DMN policy engine.
contract DeployClaimStake is Script {
    function run() external {
        uint256 deployerPk = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPk);
        address gccAddr = vm.envAddress("GCC_ADDR");
        require(gccAddr.code.length > 0, "GCC_ADDR has no code on this chain");

        vm.startBroadcast(deployerPk);

        ClaimStakeEscrow escrow = new ClaimStakeEscrow(
            IERC20(gccAddr),
            deployer,            // arbiter   = sealer (Phase 2 → RegoArbiter / multisig)
            deployer,            // treasury  = sealer (Phase 3 → multisig)
            deployer,            // rewardPool= sealer (Phase 3 → dedicated subsidy wallet)
            deployer             // owner
        );
        console.log("ClaimStakeEscrow:", address(escrow));

        vm.stopBroadcast();

        // Sanity: read back immutables / config wiring.
        require(address(escrow.gcc()) == gccAddr, "escrow GCC mismatch");
        require(escrow.winnerBps() == 8_500, "winnerBps mismatch");
        require(escrow.treasuryBps() == 1_000, "treasuryBps mismatch");
        require(escrow.rewardBps() == 500, "rewardBps mismatch");
        require(escrow.minCounterBondBps() == 5_000, "minCounterBondBps mismatch");
        require(escrow.minBond() == 1 ether, "minBond mismatch");
        require(escrow.DEFAULT_CHALLENGE_PERIOD() == 7 days, "default period mismatch");
        require(escrow.MAX_CHALLENGE_PERIOD() == 90 days, "max period mismatch");
        console.log("Post-deploy sanity: all checks pass");
    }
}
