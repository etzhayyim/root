// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Script.sol";
import {Constitution}      from "../src/Constitution.sol";
import {ConstitutionKeys}  from "../src/ConstitutionKeys.sol";
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
        // 8 original (ADR-2605172300) + 30 religious-corp wave (ADR-2605192100 §2)
        // + 1 kawase-yui (ADR-2605282200 G4) − 2 retired (tithe-pinned, rider-version)
        // + 9 priority/memory/enforcement/tithe-band (ADR-2606062100) = 47 constants
        keys = new bytes32[](47);
        vals = new bytes32[](47);

        // ─── Original ADR-2605172300 (8) ─────────────────────────────
        keys[0] = ConstitutionKeys.ONE_SBT_ONE_VOTE;          vals[0] = bytes32(uint256(1));
        keys[1] = ConstitutionKeys.NO_TRANSFERABLE_SHARE;     vals[1] = bytes32(uint256(1));
        keys[2] = ConstitutionKeys.LICENSE;                    vals[2] = bytes32("Apache-2.0");
        keys[3] = ConstitutionKeys.PHENOTYPE_MIN_BPS;          vals[3] = bytes32(uint256(5_000));    // 0.50x
        keys[4] = ConstitutionKeys.PHENOTYPE_MAX_BPS;          vals[4] = bytes32(uint256(20_000));   // 2.00x
        keys[5] = ConstitutionKeys.KAPPA_FLOOR_BPS;            vals[5] = bytes32(uint256(100));      // 1.00%
        keys[6] = ConstitutionKeys.KAPPA_CEILING_BPS;          vals[6] = bytes32(uint256(500));      // 5.00%
        keys[7] = ConstitutionKeys.QUORUM_FLOOR_BPS;           vals[7] = bytes32(uint256(2_000));    // 20.00%

        // ─── Mission Charter §1.1-§1.7 (5) ───────────────────────────
        keys[8]  = ConstitutionKeys.MISSION_LABOR_LIBERATION;          vals[8]  = bytes32(uint256(1));
        keys[9]  = ConstitutionKeys.MISSION_ROBOTICS_UNIVERSAL;        vals[9]  = bytes32(uint256(1));
        keys[10] = ConstitutionKeys.MISSION_IP_FREE_RELEASE;           vals[10] = bytes32(uint256(1));
        keys[11] = ConstitutionKeys.MISSION_DISINTERMEDIATION;         vals[11] = bytes32(uint256(1));
        keys[12] = ConstitutionKeys.MISSION_SPECIALIST_ANTI_GATEKEEPING; vals[12] = bytes32(uint256(1));

        // ─── Religious ontology §1.8-§1.10 (4) ───────────────────────
        keys[13] = ConstitutionKeys.MISSION_ANTI_INDIVIDUALISM;        vals[13] = bytes32(uint256(1));
        keys[14] = ConstitutionKeys.MISSION_MULTI_GENERATIONAL_PRIORITY; vals[14] = bytes32(uint256(1));
        keys[15] = ConstitutionKeys.MISSION_MULTI_GENERATIONAL_HORIZON_YEARS; vals[15] = bytes32(uint256(50));
        keys[16] = ConstitutionKeys.MISSION_WELLBECOMING_PRIORITY;     vals[16] = bytes32(uint256(1));

        // ─── Land + State + Force §1.11-§1.12 (6) ────────────────────
        keys[17] = ConstitutionKeys.MISSION_LAND_AS_RELIGIOUS_TRUST;   vals[17] = bytes32(uint256(1));
        keys[18] = ConstitutionKeys.MISSION_PARALLEL_GOVERNANCE_TO_STATE; vals[18] = bytes32(uint256(1));
        keys[19] = ConstitutionKeys.MISSION_TRANSPARENT_FORCE_ONLY;    vals[19] = bytes32(uint256(1));
        keys[20] = ConstitutionKeys.MISSION_PROPRIETARY_FORCE_DESIGN_PROHIBITED; vals[20] = bytes32(uint256(1));
        keys[21] = ConstitutionKeys.MISSION_FORCE_REQUIRES_SBT_VOTE;   vals[21] = bytes32(uint256(1));
        keys[22] = ConstitutionKeys.MISSION_NO_STATE_MILITARY_ALLIANCE; vals[22] = bytes32(uint256(1));

        // ─── Eros / Gore §1.13 (2) ────────────────────────────────────
        keys[23] = ConstitutionKeys.MISSION_EROS_PERMITTED;            vals[23] = bytes32(uint256(1));
        keys[24] = ConstitutionKeys.MISSION_GORE_PROHIBITED;           vals[24] = bytes32(uint256(1));

        // ─── Lineage + Canon §1.14-§1.15 (4) ─────────────────────────
        keys[25] = ConstitutionKeys.MISSION_LINEAGE_JAPANESE_PROTESTANT; vals[25] = bytes32(uint256(1));
        keys[26] = ConstitutionKeys.MISSION_ESCHATOLOGICAL;             vals[26] = bytes32(uint256(0));  // false
        keys[27] = ConstitutionKeys.MISSION_REVELATION_IN_CANON;        vals[27] = bytes32(uint256(0));  // false
        keys[28] = ConstitutionKeys.MISSION_CONTINUOUS_BECOMING;        vals[28] = bytes32(uint256(1));

        // ─── Governance + Economic + License + Enforcement (9) ───────
        keys[29] = ConstitutionKeys.GOVERNANCE_FUTURE_GENERATIONS_THIRD_PARTY_BENEFICIARY; vals[29] = bytes32(uint256(1));
        keys[30] = ConstitutionKeys.ECONOMIC_NON_PROFIT_ONLY;          vals[30] = bytes32(uint256(1));
        keys[31] = ConstitutionKeys.ECONOMIC_DONATION_ONLY;            vals[31] = bytes32(uint256(1));
        keys[32] = ConstitutionKeys.ECONOMIC_NO_ADVERTISING;           vals[32] = bytes32(uint256(1));
        // [33] tithe: Tier-0 now locks only that redistribution EXISTS (the 10% RATE
        // moved to the Tier-2 mutable TITHE_BPS within the TITHE_FLOOR/CEILING band).
        keys[33] = ConstitutionKeys.ECONOMIC_TITHE_REDISTRIBUTION_EXISTS; vals[33] = bytes32(uint256(1));
        keys[34] = ConstitutionKeys.LICENSE_BASE;                       vals[34] = bytes32("Apache-2.0");
        keys[35] = ConstitutionKeys.LICENSE_CHARTER_RIDER_REQUIRED;    vals[35] = bytes32(uint256(1));
        // [36] was LICENSE_CHARTER_RIDER_VERSION (moved to mutable). Slot reused for the
        // L3 enforcement floor, now a Tier-0 CONSTANT (bug fix — was mis-deployed mutable).
        keys[36] = ConstitutionKeys.PHENOTYPE_NON_COMPLIANT_MULTIPLIER; vals[36] = bytes32(uint256(0));
        keys[37] = ConstitutionKeys.ENFORCEMENT_THREE_TIER;            vals[37] = bytes32(uint256(1));

        // ─── kawase-yui FX band (ADR-2605282200 G4) (1) ──────────────
        // 50 bps = ±0.5% Chainlink mid-market tolerance. Constitutional
        // because mid-market-only is the §2(b) speculative finance fence;
        // widening the band would allow spread profit at the pool layer.
        keys[38] = ConstitutionKeys.KAWASE_MAX_BAND_BPS;               vals[38] = bytes32(uint256(50));

        // ─── Priority-over-specifics (ADR-2606062100 §1-§2) (8) ──────
        // Tier-0 locks PRIORITIES (existence/ordering bools) — the lock target
        // shifts from individual policies to the priority ordering itself.
        keys[39] = ConstitutionKeys.PRIORITY_WELLBECOMING_OVER_WELLBEING; vals[39] = bytes32(uint256(1));
        keys[40] = ConstitutionKeys.PRIORITY_MULTIGEN_OVER_CURRENT;       vals[40] = bytes32(uint256(1));
        keys[41] = ConstitutionKeys.PRIORITY_COLLECTIVE_OVER_INDIVIDUAL;  vals[41] = bytes32(uint256(1));
        // Permanent memory (神の監視): no right to be forgotten; deeds public,
        // intimate encrypted-retained (encryption ≠ forgetting).
        keys[42] = ConstitutionKeys.MEMORY_RIGHT_TO_ERASURE_DENIED;       vals[42] = bytes32(uint256(1));
        keys[43] = ConstitutionKeys.MEMORY_PERMANENT_RECORD;             vals[43] = bytes32(uint256(1));
        keys[44] = ConstitutionKeys.MEMORY_DEEDS_PUBLIC_INTIMATE_ENCRYPTED; vals[44] = bytes32(uint256(1));
        // Tithe band guards (Tier-0): the mutable rate must stay within [5%, 20%].
        keys[45] = ConstitutionKeys.TITHE_FLOOR_BPS;                      vals[45] = bytes32(uint256(500));    // 5.00%
        keys[46] = ConstitutionKeys.TITHE_CEILING_BPS;                    vals[46] = bytes32(uint256(2_000));  // 20.00%
    }

    function _mutables() internal pure returns (bytes32[] memory keys, bytes32[] memory vals) {
        // 8 original (ADR-2605172300) + 3 reclassified (ADR-2606062100: tithe rate,
        // rider version, rider text-hash) + 6 reference addresses (initial = 0, set
        // via governance post-deploy) + 1 kawase.per_month_cap_usd_minor = 18 mutables.
        // NOTE: phenotype.non_compliant_multiplier moved OUT to constants (bug fix,
        // ADR-2606062100 §4); the buffer slot is removed.
        keys = new bytes32[](18);
        vals = new bytes32[](18);

        // ─── Original ADR-2605172300 mutables (8) ────────────────────
        keys[0] = ConstitutionKeys.KISHA_BASE_RATE;       vals[0] = bytes32(uint256(1_000_000));  // 1 USDC/day base
        keys[1] = ConstitutionKeys.KAPPA_BPS;              vals[1] = bytes32(uint256(300));        // 3.00% κ
        keys[2] = ConstitutionKeys.TIER_LIQUID_BPS;        vals[2] = bytes32(uint256(1_000));      // 10%
        keys[3] = ConstitutionKeys.TIER_RESERVE_BPS;       vals[3] = bytes32(uint256(6_000));      // 60%
        keys[4] = ConstitutionKeys.TIER_CORPUS_BPS;        vals[4] = bytes32(uint256(3_000));      // 30%
        keys[5] = ConstitutionKeys.QUORUM_BPS;             vals[5] = bytes32(uint256(3_300));      // 33.00%
        keys[6] = ConstitutionKeys.ACTIVE_WINDOW_SECS;     vals[6] = bytes32(uint256(30 days));
        keys[7] = ConstitutionKeys.TIMELOCK_SECS;          vals[7] = bytes32(uint256(72 hours));

        // ─── Reclassified to Tier-2 by ADR-2606062100 §4 (3) ─────────
        // The tithe RATE (init 1000 = 10%), governance-mutable within the Tier-0
        // [TITHE_FLOOR_BPS, TITHE_CEILING_BPS] = [500, 2000] band. TitheRouter reads
        // this via getMutable. The Rider version is a parameter (tracks amendments);
        // the Rider text-hash anchors integrity, wired post-ratification (= 0 here).
        keys[8]  = ConstitutionKeys.TITHE_BPS;                       vals[8]  = bytes32(uint256(1_000));  // 10.00%
        keys[9]  = ConstitutionKeys.LICENSE_CHARTER_RIDER_VERSION;   vals[9]  = bytes32("v3.6");
        // keccak256 of the exact bytes of /CHARTER-RIDER.md (v3.6). Drift-locked by
        // ConstitutionInvariants.t.sol::test_rider_text_hash_matches_file — editing the
        // Rider without updating this literal fails CI. (ADR-2606062100 §4 anchor.)
        keys[10] = ConstitutionKeys.LICENSE_CHARTER_RIDER_TEXT_HASH; vals[10] = 0x549c99eacb894c9bc74025cf09cb892b6b66e407b112c7c528ab6e7c9b14630b;

        // ─── Reference addresses (6) — initial = address(0)        ───
        // Wired post-deploy via Governance proposal + 48h+ timelock.
        // See RUNBOOK-deploy.md step "Wire references" for the
        // canonical bootstrap proposal payload.
        keys[11] = ConstitutionKeys.PUBLIC_FUND_SAFE_ADDRESS;            vals[11] = bytes32(0);
        keys[12] = ConstitutionKeys.CHARTERS_COMPLIANCE_REGISTRY_ADDRESS; vals[12] = bytes32(0);
        keys[13] = ConstitutionKeys.TITHE_ROUTER_ADDRESS;                 vals[13] = bytes32(0);
        keys[14] = ConstitutionKeys.LAND_REGISTRY_ADDRESS;                vals[14] = bytes32(0);
        keys[15] = ConstitutionKeys.FORCE_AUTHORIZATION_ADDRESS;          vals[15] = bytes32(0);
        keys[16] = ConstitutionKeys.PUBLIC_FUND_GOVERNANCE_ADDRESS;       vals[16] = bytes32(0);

        // ─── kawase-yui per-member monthly cap (ADR-2605282200 G9) ────
        // 1_000_000_000 = $1_000.00 USD-equivalent in USDC minor units
        // (6 decimals). R1 default; R2 raises to $5_000, R3 to $25_000.
        // KawaseYuiPool reads this at deposit time; reverts on cap breach.
        keys[17] = ConstitutionKeys.KAWASE_PER_MONTH_CAP_USD_MINOR; vals[17] = bytes32(uint256(1_000_000_000));
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
