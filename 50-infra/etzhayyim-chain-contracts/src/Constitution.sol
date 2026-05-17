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
    // vocabulary. Off-chain code SHOULD use the same labels via keccak256.

    // CONSTANTS (set once):
    //   "one_sbt_one_vote"        => bytes32(uint256(1))
    //   "no_transferable_share"   => bytes32(uint256(1))
    //   "license"                 => bytes32("Apache-2.0")
    //   "kappa_floor_bps"         => bytes32(uint256(100))   // 1.00%
    //   "kappa_ceiling_bps"       => bytes32(uint256(500))   // 5.00%
    //   "phenotype_min_bps"       => bytes32(uint256(5000))  // 0.50x
    //   "phenotype_max_bps"       => bytes32(uint256(20000)) // 2.00x
    //   "quorum_floor_bps"        => bytes32(uint256(2000))  // 20.00%
    //
    // MUTABLES (Governance-changeable):
    //   "kisha_base_rate"         => USDC base units per adherent per day
    //   "kappa_bps"               => current κ in basis points (init 300 = 3%)
    //   "tier_liquid_bps"         => target liquid tier ratio (init 1000)
    //   "tier_reserve_bps"        => target reserve tier ratio (init 6000)
    //   "tier_corpus_bps"         => target corpus tier ratio (init 3000)
    //   "quorum_bps"              => current quorum (init 3300)
    //   "active_window_secs"      => "active adherent" window (init 30 days)
    //   "timelock_secs"           => governance timelock (init 72h)

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
