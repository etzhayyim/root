// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
//
// Per ADR-2606032130 (Displacement Dividend — tenure-weighted in-kind Basic High Income).
// Couples to ADR-2606032100 (OSS-robotics actor wave) as its redistribution half.
//
// DisplacementDividend — a Public-Fund module that registers humans displaced by an
// etzhayyim OSS-robotics actor into a per-cohort, tenure-weighted, IN-KIND Basic-High-
// Income transition. It computes ONLY weights and priority ranks; it NEVER moves cash to
// a worker (cash≡0, N1). Disbursement is in-kind provisioning along the Liberation Ladder,
// authorized through PublicFundGovernance (1 SBT = 1 vote → 48h timelock).
//
// HARD INVARIANTS (enforced by construction + governance, not by this stub alone):
//   - cash≡0: no function transfers value to a `subject`. The only on-chain money path is
//     a Public-Fund grant to an IN-KIND PROVISIONING program, voted via PublicFundGovernance.
//   - donation-only inflow: the cohort pool is funded via TitheRouter.donate() earmarked
//     recipientProgram="displacement-dividend"; this contract never accepts a fee/premium.
//   - no payroll: subjects are covenant members on the Liberation Ladder, not employees.
//   - adherent-gated, universally-admissible: full weight applies once covenantStatus=vowed.
//
// STATUS: R0 SCAFFOLD — every state-mutating function reverts NotYetActivated() until a
// post-Bootstrap-Council activation ADR enables it. Pure-view weight math is live so the
// formula is auditable on-chain and matches the Python reference allocator.

pragma solidity 0.8.27;

interface IPublicFundGovernance {
    function publicFundSafe() external view returns (address);
}

interface IChartersComplianceRegistry {
    function isCouncilMember(address) external view returns (bool);
}

contract DisplacementDividend {
    // ─── Constants (mirror ADR-2606032130 + allocate.py) ───────────────────
    uint64 public constant TENURE_CAP_MONTHS = 600;   // 40 years
    uint16 public constant HAZARD_MIN_PERMILLE = 1000; // 1.0
    uint16 public constant HAZARD_MAX_PERMILLE = 2000; // 2.0
    uint64 public constant HORIZON_MONTHS = 60;       // 5-year transition floor decay
    uint8  public constant MIN_COUNCIL_SIGNERS = 3;

    enum Covenant { None, Outreach, Vowed }

    struct Subject {
        bytes32 cohortId;
        address displacingActor;     // robotics actor whose surplus funds the cohort
        uint32  displacedIscoCode;   // ISCO-08, numeric
        uint64  tenureMonths;        // 勤続年数 × 12
        uint16  hazardPermille;      // [1000,2000]
        uint64  priorImputedUsdMicrosYr; // in-kind valuation only; NEVER paid as cash
        Covenant covenant;
        uint64  registeredAt;
        bytes32 evidenceCid;         // encrypted tenure-evidence envelope ref (ADR-2605181100)
    }

    // cohortId => list of subject SBT ids ; subjectId => Subject
    mapping(bytes32 => uint256[]) public cohortSubjects;
    mapping(uint256 => Subject) public subjects;

    bool public activated;
    address public publicFundGovernance;
    address public charters;

    error NotYetActivated();
    error InvalidHazard(uint16 permille);
    error CashIsNeverPaidToSubject(); // tripwire: any value→subject path must revert
    error InsufficientCouncilSigners();

    event SubjectRegistered(uint256 indexed subjectId, bytes32 indexed cohortId, address indexed displacingActor, uint32 iscoCode);
    event CohortPoolEarmarked(bytes32 indexed cohortId, uint256 amountUsdMicros, bytes32 policyCid);
    event CovenantAdvanced(uint256 indexed subjectId, Covenant to);

    constructor(address _charters) {
        charters = _charters;
    }

    // ─── Pure weight math (LIVE — auditable, matches allocate.py) ───────────

    /// @notice ln(1 + min(tenure, cap)) × hazard, returned in basis points.
    /// @dev Integer ln via a fixed-point natural-log approximation is out of scope for
    ///      the R0 stub; this returns the *hazard-scaled capped tenure* in months×permille
    ///      so off-chain allocate.py owns the ln() and on-chain we expose the inputs it used.
    ///      R1 wires a fixed-point ln library (e.g. PRBMath) so the weight is fully on-chain.
    function tenureWeightInputs(uint64 tenureMonths, uint16 hazardPermille)
        external
        pure
        returns (uint64 cappedMonths, uint16 hazard)
    {
        if (hazardPermille < HAZARD_MIN_PERMILLE || hazardPermille > HAZARD_MAX_PERMILLE) {
            revert InvalidHazard(hazardPermille);
        }
        cappedMonths = tenureMonths > TENURE_CAP_MONTHS ? TENURE_CAP_MONTHS : tenureMonths;
        hazard = hazardPermille;
    }

    /// @notice Transition-floor decay multiplier in per-mille over the HORIZON.
    /// decay(t) = clamp(1 − t/HORIZON, 0, 1)  → 1000..0 per-mille.
    function floorDecayPermille(uint64 elapsedMonths) external pure returns (uint16) {
        if (elapsedMonths >= HORIZON_MONTHS) return 0;
        return uint16(1000 - (uint256(elapsedMonths) * 1000) / HORIZON_MONTHS);
    }

    // ─── Registration / lifecycle (R0 stubs — revert until activated) ──────

    /// @notice Register a displaced worker into a cohort (G2 coupling, ADR-2606032100).
    /// @dev R0: reverts. R1+: Council-attested; stores Subject; emits SubjectRegistered.
    function registerSubject(
        uint256, /*subjectSbtId*/
        bytes32, /*cohortId*/
        address, /*displacingActor*/
        uint32,  /*iscoCode*/
        uint64,  /*tenureMonths*/
        uint16,  /*hazardPermille*/
        bytes32  /*evidenceCid*/
    ) external pure returns (bool) {
        revert NotYetActivated();
    }

    /// @notice Earmark a Public-Fund pool for a cohort (donation-funded; voted upstream).
    /// @dev R0: reverts. The actual money path is PublicFundGovernance → in-kind program;
    ///      this only records the earmark + the voted policy CID.
    function earmarkCohortPool(
        bytes32, /*cohortId*/
        uint256, /*amountUsdMicros*/
        bytes32, /*policyCid*/
        bytes[] calldata, /*councilSigs*/
        address[] calldata /*councilSigners*/
    ) external pure {
        revert NotYetActivated();
    }

    /// @notice Advance a subject's conversion covenant (Outreach → Vowed) after the
    ///         triple-permanent vow (kotoba+IPFS+SBT, ADR-2605302357 §1.16.3a).
    function advanceCovenant(uint256 /*subjectId*/, Covenant /*to*/) external pure {
        revert NotYetActivated();
    }

    /// @notice Structural tripwire. There is NO function that pays a subject cash, by design.
    ///         If any future caller attempts a subject-cash path, it must route here and revert.
    function payoutToSubject(uint256, uint256) external pure {
        revert CashIsNeverPaidToSubject();
    }
}
