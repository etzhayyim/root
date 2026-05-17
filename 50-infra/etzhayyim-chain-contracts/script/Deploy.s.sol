// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Script.sol";
import {Constitution}      from "../src/Constitution.sol";
import {AdherentRegistry}  from "../src/AdherentRegistry.sol";
import {KishaStream}       from "../src/KishaStream.sol";
import {Phenotype}         from "../src/Phenotype.sol";
import {AnchorBridge}      from "../src/AnchorBridge.sol";
import {Governance}        from "../src/Governance.sol";
import {TreasuryMirror}    from "../src/TreasuryMirror.sol";
import {CorpusRegistry}    from "../src/CorpusRegistry.sol";
import {HoldingAttestation} from "../src/HoldingAttestation.sol";
import {KishaPayout, IERC20} from "../src/base/KishaPayout.sol";

/**
 * @title Deploy
 * @notice Canonical deployment script for the etzhayyim chain-contracts
 *         stack. Run twice — once on geth-private (`--rpc-url
 *         etzhayyim_private`) for the internal contracts, and once on
 *         Base (`--rpc-url base` or `base_sepolia`) for the
 *         {KishaPayout} settlement contract.
 *
 * @dev See `RUNBOOK-deploy.md` for the full bootstrap sequence
 *      (Constitution.bindGovernance, founder SBT mints, bootstrap
 *      governance proposal, timelock wait, execute).
 *
 *      Apache 2.0. Per ADR-2605172300 S5.
 */
contract Deploy is Script {
    // -------------------------------------------------------------------
    // Canonical constitutional keys
    // -------------------------------------------------------------------

    bytes32 internal constant K_ONE_SBT_ONE_VOTE   = keccak256("one_sbt_one_vote");
    bytes32 internal constant K_NO_TRANSFER_SHARE  = keccak256("no_transferable_share");
    bytes32 internal constant K_LICENSE            = keccak256("license");
    bytes32 internal constant K_PHENOTYPE_MIN      = keccak256("phenotype_min_bps");
    bytes32 internal constant K_PHENOTYPE_MAX      = keccak256("phenotype_max_bps");
    bytes32 internal constant K_KAPPA_FLOOR        = keccak256("kappa_floor_bps");
    bytes32 internal constant K_KAPPA_CEILING      = keccak256("kappa_ceiling_bps");
    bytes32 internal constant K_QUORUM_FLOOR       = keccak256("quorum_floor_bps");

    bytes32 internal constant K_KISHA_BASE         = keccak256("kisha_base_rate");
    bytes32 internal constant K_KAPPA              = keccak256("kappa_bps");
    bytes32 internal constant K_TIER_LIQUID        = keccak256("tier_liquid_bps");
    bytes32 internal constant K_TIER_RESERVE       = keccak256("tier_reserve_bps");
    bytes32 internal constant K_TIER_CORPUS        = keccak256("tier_corpus_bps");
    bytes32 internal constant K_QUORUM             = keccak256("quorum_bps");
    bytes32 internal constant K_ACTIVE_WINDOW      = keccak256("active_window_secs");
    bytes32 internal constant K_TIMELOCK           = keccak256("timelock_secs");

    // -------------------------------------------------------------------
    // Bundle returned to the JSON sink
    // -------------------------------------------------------------------

    struct Internal {
        address constitution;
        address adherentRegistry;
        address kishaStream;
        address phenotype;
        address anchorBridge;
        address governance;
        address treasuryMirror;
        address corpusRegistry;
        address holdingAttestation;
    }

    // -------------------------------------------------------------------
    // Entrypoints
    // -------------------------------------------------------------------

    /// @notice Deploy the geth-private (internal) contract stack.
    ///         Caller is responsible for calling
    ///         `Constitution.bindGovernance(<governance address>)`
    ///         post-deploy (see RUNBOOK step 5).
    function runInternal(address[] memory initialOfficers) public returns (Internal memory out) {
        require(initialOfficers.length >= 1, "no officers");

        vm.startBroadcast();

        // ---- Constitution ------------------------------------------------
        (bytes32[] memory cK, bytes32[] memory cV) = _constants();
        (bytes32[] memory mK, bytes32[] memory mV) = _mutables();
        Constitution c = new Constitution(cK, cV, mK, mV);

        // ---- AdherentRegistry --------------------------------------------
        AdherentRegistry r = new AdherentRegistry(initialOfficers);

        // ---- KishaStream + Phenotype -------------------------------------
        // base rate 1 USDC/day (6-decimal base units), active window 30d.
        KishaStream ks = new KishaStream(r, c, 1_000_000, uint64(30 days));
        Phenotype pn = new Phenotype(c);

        // ---- AnchorBridge -----------------------------------------------
        AnchorBridge ab = new AnchorBridge();

        // ---- Governance + TreasuryMirror --------------------------------
        Governance gov = new Governance(r, c);
        TreasuryMirror tm = new TreasuryMirror(c);

        // ---- Corpus tier (legal-review-contingent) ----------------------
        CorpusRegistry cr = new CorpusRegistry(c);
        HoldingAttestation ha = new HoldingAttestation(c);

        vm.stopBroadcast();

        out = Internal({
            constitution: address(c),
            adherentRegistry: address(r),
            kishaStream: address(ks),
            phenotype: address(pn),
            anchorBridge: address(ab),
            governance: address(gov),
            treasuryMirror: address(tm),
            corpusRegistry: address(cr),
            holdingAttestation: address(ha)
        });

        _emitInternal(out);
    }

    /// @notice One-shot bind of the freshly deployed Governance contract
    ///         as Constitution's mutator. Anyone may call this; the
    ///         contract enforces idempotency. Run as the next step after
    ///         {runInternal}.
    function bindGovernance(address constitution, address governance) public {
        vm.startBroadcast();
        Constitution(constitution).bindGovernance(governance);
        vm.stopBroadcast();
    }

    /// @notice Deploy the Base L2 settlement contract. Requires the
    ///         KishaStream address on geth-private (passed in as a
    ///         label for ticketId derivation), the Treasury Safe
    ///         address, the USDC contract on Base, and the initial
    ///         M-of-N relayer set.
    function runBase(
        address usdc,
        address treasurySafe,
        address kishaStreamLabel,
        address[] memory relayers,
        uint8 threshold
    ) public returns (address kishaPayout) {
        vm.startBroadcast();
        KishaPayout kp = new KishaPayout(
            IERC20(usdc), treasurySafe, kishaStreamLabel, relayers, threshold
        );
        vm.stopBroadcast();
        kishaPayout = address(kp);
        console.log("KishaPayout (Base):", kishaPayout);
    }

    // -------------------------------------------------------------------
    // Constitutional defaults
    // -------------------------------------------------------------------

    function _constants() internal pure returns (bytes32[] memory keys, bytes32[] memory vals) {
        keys = new bytes32[](8);
        vals = new bytes32[](8);
        keys[0] = K_ONE_SBT_ONE_VOTE;   vals[0] = bytes32(uint256(1));
        keys[1] = K_NO_TRANSFER_SHARE;  vals[1] = bytes32(uint256(1));
        keys[2] = K_LICENSE;             vals[2] = bytes32("Apache-2.0");
        keys[3] = K_PHENOTYPE_MIN;       vals[3] = bytes32(uint256(5_000));   // 0.50x
        keys[4] = K_PHENOTYPE_MAX;       vals[4] = bytes32(uint256(20_000));  // 2.00x
        keys[5] = K_KAPPA_FLOOR;         vals[5] = bytes32(uint256(100));     // 1.00%
        keys[6] = K_KAPPA_CEILING;       vals[6] = bytes32(uint256(500));     // 5.00%
        keys[7] = K_QUORUM_FLOOR;        vals[7] = bytes32(uint256(2_000));   // 20.00%
    }

    function _mutables() internal pure returns (bytes32[] memory keys, bytes32[] memory vals) {
        keys = new bytes32[](8);
        vals = new bytes32[](8);
        keys[0] = K_KISHA_BASE;     vals[0] = bytes32(uint256(1_000_000));   // 1 USDC/day base
        keys[1] = K_KAPPA;           vals[1] = bytes32(uint256(300));         // 3.00% κ
        keys[2] = K_TIER_LIQUID;     vals[2] = bytes32(uint256(1_000));       // 10%
        keys[3] = K_TIER_RESERVE;    vals[3] = bytes32(uint256(6_000));       // 60%
        keys[4] = K_TIER_CORPUS;     vals[4] = bytes32(uint256(3_000));       // 30%
        keys[5] = K_QUORUM;          vals[5] = bytes32(uint256(3_300));       // 33.00%
        keys[6] = K_ACTIVE_WINDOW;   vals[6] = bytes32(uint256(30 days));
        keys[7] = K_TIMELOCK;        vals[7] = bytes32(uint256(72 hours));
    }

    function _emitInternal(Internal memory o) internal pure {
        console.log("--- etzhayyim chain-contracts (geth-private) ---");
        console.log("Constitution       ", o.constitution);
        console.log("AdherentRegistry   ", o.adherentRegistry);
        console.log("KishaStream        ", o.kishaStream);
        console.log("Phenotype          ", o.phenotype);
        console.log("AnchorBridge       ", o.anchorBridge);
        console.log("Governance         ", o.governance);
        console.log("TreasuryMirror     ", o.treasuryMirror);
        console.log("CorpusRegistry     ", o.corpusRegistry);
        console.log("HoldingAttestation ", o.holdingAttestation);
    }
}
