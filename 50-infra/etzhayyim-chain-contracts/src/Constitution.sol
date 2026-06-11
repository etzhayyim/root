// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title Constitution
 * @notice On-chain constitution of the etzhayyim religious voluntary
 *         association (任意団体). Holds two classes of parameters:
 *
 *           - CONSTANTS: immutable forever, set at construction. These
 *             encode the foundational invariants (1 SBT = 1 vote, κ
 *             ceiling/floor, no-transferable-share rule, license).
 *             Changing a CONSTANT requires forking the chain — i.e.
 *             founding a different association.
 *
 *           - MUTABLES: changeable only by the bound Governance contract
 *             (see {bindGovernance}). These encode parameters that the
 *             association may legitimately adjust over time (kisha base
 *             rate, κ, asset-tier ratios, quorum, etc.) within bounds
 *             enforced by the CONSTANTS.
 *
 * @dev Per ADR-2605172300 §2 and §8. Apache-2.0.
 *
 *      Design rules:
 *      - No admin key. No pause. No upgrade. The only mutation path is
 *        {setMutable} called from `governance`, and `governance` is
 *        bound exactly once via {bindGovernance}.
 *      - Bound types are not enforced here per-key — the governance
 *        proposal layer is responsible for sanity-checking proposed
 *        values against {getConstant} guards (e.g., κ floor/ceiling)
 *        before submitting them to {setMutable}.
 *      - This contract does NOT custody assets. It is a parameter
 *        registry only. Asset custody lives in the Base-side Safe.
 */
contract Constitution {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error NotGovernance();
    error GovernanceAlreadyBound();
    error UnknownConstant(bytes32 key);
    error ImmutableKey(bytes32 key);

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event GovernanceBound(address indexed governance);
    event MutableSet(bytes32 indexed key, bytes32 oldValue, bytes32 newValue);

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    /// @notice The Governance contract authorized to call {setMutable}.
    ///         Bound exactly once via {bindGovernance}. Address(0) until bound.
    address public governance;

    /// @notice Immutable constants. Set in constructor, never changed.
    mapping(bytes32 => bytes32) private _constants;

    /// @notice Governance-mutable parameters.
    mapping(bytes32 => bytes32) private _mutables;

    /// @notice Tracks which keys have been registered as constants
    ///         (so {getConstant} can distinguish "unknown" from "zero").
    mapping(bytes32 => bool) private _isConstant;

    // -------------------------------------------------------------------
    // Canonical key labels
    // -------------------------------------------------------------------
    // Keep these documented near the contract — they are the constitutional
    // vocabulary. Off-chain code MUST use {ConstitutionKeys} library for
    // bytes32 keys to avoid drift. See ConstitutionKeys.sol for the full
    // SSoT. Summary of vocabulary by ADR:
    //
    // CONSTANTS (set once at deploy; change = founding new religion):
    //
    //   ADR-2605172300 §8 (original 8):
    //     one_sbt_one_vote, no_transferable_share, license,
    //     phenotype_min_bps, phenotype_max_bps,
    //     kappa_floor_bps, kappa_ceiling_bps, quorum_floor_bps
    //
    //   ADR-2605192100 §1.1-§1.7 (Mission, 5):
    //     mission.labor_liberation, mission.robotics_universal,
    //     mission.ip_free_release, mission.disintermediation,
    //     mission.specialist_anti_gatekeeping
    //
    //   ADR-2605192100 §1.8-§1.10 (Religious ontology, 4):
    //     mission.anti_individualism,
    //     mission.multi_generational_priority,
    //     mission.multi_generational_horizon_years (= 50),
    //     mission.wellbecoming_priority
    //
    //   ADR-2605192100 §1.11-§1.12 (Land + State + Force, 6):
    //     mission.land_as_religious_trust,
    //     mission.parallel_governance_to_state,
    //     mission.transparent_force_only,
    //     mission.proprietary_force_design_prohibited,
    //     mission.force_requires_sbt_vote,
    //     mission.no_state_military_alliance
    //
    //   ADR-2605192100 §1.13 (Eros/Gore, 2):
    //     mission.eros_permitted, mission.gore_prohibited
    //
    //   ADR-2605192100 §1.14-§1.15 (Lineage + Canon, 4):
    //     mission.lineage_japanese_protestant,
    //     mission.eschatological (= false),
    //     mission.revelation_in_canon (= false),
    //     mission.continuous_becoming
    //
    //   ADR-2605192100 §2 + ADRs 2605192115/2605192130/2605192200/2605192230:
    //     governance.future_generations_third_party_beneficiary,
    //     economic.non_profit_only, economic.donation_only,
    //     economic.no_advertising,
    //     economic.tithe_redistribution_exists (Tier-0 bool — redistribution EXISTS;
    //       the 10% RATE is the Tier-2 mutable tithe_bps; ADR-2606062100 §4),
    //     license.base (= "Apache-2.0"),
    //     license.charter_rider_required,
    //     enforcement.three_tier,
    //     phenotype.non_compliant_multiplier (= 0; L3 floor — RECLASSIFIED to a
    //       CONSTANT by ADR-2606062100 §4, was mis-deployed mutable)
    //
    //   ADR-2606062100 (priority-over-specifics) Tier-0 (9):
    //     priority.wellbecoming_over_wellbeing, priority.multigen_over_current,
    //     priority.collective_over_individual,
    //     memory.right_to_erasure_denied, memory.permanent_record,
    //     memory.deeds_public_intimate_encrypted (神の監視 / 永久記憶),
    //     tithe_floor_bps (= 500), tithe_ceiling_bps (= 2000)
    //
    //   The Charter locks PRIORITIES (existence/ordering bools), NOT specific
    //   numbers or named policies (those derive from priority — Tier-1/Tier-2).
    //
    // MUTABLES (Governance-changeable within constant bounds):
    //
    //   ADR-2605172300 §8 (original 8):
    //     kisha_base_rate (USDC base units / adherent / day),
    //     kappa_bps (init 300 = 3%),
    //     tier_liquid_bps / tier_reserve_bps / tier_corpus_bps (10:60:30),
    //     quorum_bps (init 3300), active_window_secs (init 30d),
    //     timelock_secs (init 72h)
    //
    //   ADR-2606062100 §4 reclassified to Tier-2 (3):
    //     tithe_bps (init 1000 = 10%, within [tithe_floor_bps, tithe_ceiling_bps]),
    //     license.charter_rider_version (init "v3.0"; tracks Rider amendments),
    //     license.charter_rider_text_hash (= 0; Rider-integrity anchor, wired
    //       post-ratification via the Lv7+ priority-conformance path)
    //
    //   ADR-2605192100 + 2605192230 + 2605192245 (reference addresses, 6):
    //     public_fund.safe_address, charters_compliance.registry_address,
    //     tithe_router.address, land_registry.address,
    //     force_authorization.address, public_fund.governance_address
    //     (all initial = address(0); wired post-deploy via governance
    //     proposal + 48h+ timelock per RUNBOOK)

    // -------------------------------------------------------------------
    // Construction
    // -------------------------------------------------------------------

    /**
     * @param constantKeys    Parallel array of constant keys
     * @param constantValues  Parallel array of constant values
     * @param initialMutableKeys    Parallel array of mutable keys (initial)
     * @param initialMutableValues  Parallel array of mutable initial values
     *
     * @dev Mutables may be re-set later by governance; constants cannot.
     */
    constructor(
        bytes32[] memory constantKeys,
        bytes32[] memory constantValues,
        bytes32[] memory initialMutableKeys,
        bytes32[] memory initialMutableValues
    ) {
        require(constantKeys.length == constantValues.length, "len(constants)");
        require(initialMutableKeys.length == initialMutableValues.length, "len(mutables)");

        for (uint256 i = 0; i < constantKeys.length; ++i) {
            _constants[constantKeys[i]] = constantValues[i];
            _isConstant[constantKeys[i]] = true;
        }
        for (uint256 i = 0; i < initialMutableKeys.length; ++i) {
            _mutables[initialMutableKeys[i]] = initialMutableValues[i];
            // No event for initial values — read genesis to inspect.
        }
    }

    // -------------------------------------------------------------------
    // Governance binding (one-shot)
    // -------------------------------------------------------------------

    /**
     * @notice Bind the Governance contract address. Callable exactly once,
     *         by anyone (the deployer, typically). Once bound, all
     *         {setMutable} calls must come from `governance`.
     *
     * @dev Rationale for "anyone, once": prevents a hostile redeployment
     *      vector while not requiring an "owner" role that would
     *      contradict the no-admin rule.
     */
    function bindGovernance(address governance_) external {
        if (governance != address(0)) revert GovernanceAlreadyBound();
        governance = governance_;
        emit GovernanceBound(governance_);
    }

    // -------------------------------------------------------------------
    // Reads
    // -------------------------------------------------------------------

    function getConstant(bytes32 key) external view returns (bytes32) {
        if (!_isConstant[key]) revert UnknownConstant(key);
        return _constants[key];
    }

    function getMutable(bytes32 key) external view returns (bytes32) {
        return _mutables[key];
    }

    function isConstant(bytes32 key) external view returns (bool) {
        return _isConstant[key];
    }

    // -------------------------------------------------------------------
    // Writes
    // -------------------------------------------------------------------

    /**
     * @notice Set a mutable parameter. Callable only by `governance`.
     *
     * @dev Refuses to overwrite a key registered as a constant — even
     *      from governance — to make the constant/mutable boundary
     *      structurally inviolable.
     */
    function setMutable(bytes32 key, bytes32 value) external {
        if (msg.sender != governance) revert NotGovernance();
        if (_isConstant[key]) revert ImmutableKey(key);
        bytes32 old = _mutables[key];
        _mutables[key] = value;
        emit MutableSet(key, old, value);
    }
}
