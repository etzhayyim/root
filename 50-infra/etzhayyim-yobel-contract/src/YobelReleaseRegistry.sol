// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {YobelRiteRegistry} from "./YobelRiteRegistry.sol";

/**
 * @title YobelReleaseRegistry
 * @notice Immutable append-only registry of individual debt releases under
 *         active rites in {YobelRiteRegistry}.
 *
 * @dev Per ADR-2605201800 + Charter Compliance Rider v2.0 §2(b).
 *      Apache-2.0.
 *
 *      Design rules:
 *
 *        - **NO admin / no upgrade / no pause.** Same constitutional
 *          pattern as YobelRiteRegistry + EtzhayyimAnchor.
 *
 *        - **Permissionless write.** Anyone can call {recordRelease}.
 *          The on-chain msg.sender + DID resolution provides the audit
 *          trail. Off-chain DMN tax warning + Council DMN eligibility
 *          are enforced by the {ReleaseSettlementCell} before this call.
 *
 *        - **Append-only.** Once recorded, a release is immutable. There
 *          is no reverse / undo / amend. Reversing a forgiveness would
 *          violate the one-way invariant.
 *
 *        - **One-way boundary check.** {recordRelease} enforces
 *          {releasedMicroUsdc} ≤ {debtCap} for the (riteId, debtIdHash)
 *          pair. The debt cap is registered via {registerDebtCap}, which
 *          is also permissionless but separately tracked for audit.
 *
 *        - **Rite must be Active.** Cross-references {YobelRiteRegistry}
 *          to assert {YobelRiteRegistry.isActive(riteId)} at release time.
 *          Releases recorded against superseded rites are explicitly
 *          rejected (Charter §1.3 transparent governance).
 *
 *        - **No fiat / no Stripe.** Contract takes no value. USDC transfer
 *          (when releaseMethod=BaseL2Transfer) happens via the
 *          EtzhayyimPaymaster or direct ERC20 transfer in a separate tx;
 *          {baseL2TxHashCrossRef} stores the reference for audit.
 *
 *      Privacy: debtor / creditor DIDs are stored as keccak256 hashes only.
 *      The plain DID + signature set lives in encrypted AT MST records
 *      (XChaCha20-Poly1305 envelope per ADR-2605181100). On-chain witnesses
 *      can verify the hash given the plaintext from authorized decryption.
 *
 *      **Natural-person-only invariant**: yobel releases debt for individuals
 *      (自然人) only. Legal-person debt (sovereign / corporate restructuring)
 *      is out of scope. This invariant is enforced off-chain by the
 *      debtor_enrollment cell DMN R14 short-circuit. The contract does NOT
 *      hold an entityType field — keeping it off-chain reduces gas + storage
 *      cost and keeps the invariant under cell-level governance where it can
 *      be amended via ADR rather than redeploying contracts.
 *
 *      Cross-link to bankruptcy.etzhayyim.com (vendor): off-chain pipeline can
 *      attach this {YobelReleaseRegistry} contract address + releaseId hash
 *      to a `bankruptcyCase.parallelReleases[]` field on vendor side to
 *      satisfy "voluntary release attached to formal bankruptcy filing"
 *      (see ADR-2605201700 §Cluster Integration).
 */
contract YobelReleaseRegistry {

    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error ReleaseAlreadyRecorded(bytes32 releaseId);
    error RiteNotActive(bytes32 riteId);
    error DebtCapNotRegistered(bytes32 debtIdHash);
    error DebtCapAlreadyRegistered(bytes32 debtIdHash);
    error OneWayViolation(uint256 released, uint256 cap);
    error InvalidReleaseMethod(uint8 method);
    error EmptyReleaseId();
    error ZeroAmount();
    error ZeroDebtCap();

    // -------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------

    enum ReleaseMethod {
        VoluntaryBookkeeping,
        BaseL2Transfer,
        CourtOrder,
        SovereignDecree,
        EcclesiasticalIndulgence
    }

    struct Release {
        bytes32 releaseId;
        bytes32 riteId;
        bytes32 debtIdHash;
        bytes32 debtorDidHash;
        bytes32 creditorDidHash;
        uint256 releasedMicroUsdc;
        ReleaseMethod releaseMethod;
        bytes32 baseL2TxHashCrossRef;  // 0 unless releaseMethod=BaseL2Transfer
        uint64 releasedAt;
        address recorder;
    }

    struct DebtCap {
        uint256 principalMicroUsdc;
        uint256 accruedMicroUsdc;
        uint256 totalReleasedMicroUsdc;  // running sum across all releases against this debt
        address registrar;
        uint64 registeredAt;
    }

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    /// @notice Cross-link to the rite registry. Set at construction; immutable.
    YobelRiteRegistry public immutable RITE_REGISTRY;

    /// @notice releaseId → release. Append-only.
    mapping(bytes32 => Release) public releases;
    bytes32[] public allReleaseIds;

    /// @notice (riteId, debtIdHash) → cap. Set once via {registerDebtCap}.
    ///         Keyed by a combined hash to keep the same debt under different
    ///         rites separately accounted.
    mapping(bytes32 => DebtCap) public debtCaps;

    /// @notice Index: riteId → all releaseIds under that rite (for enumeration).
    mapping(bytes32 => bytes32[]) public releasesByRite;

    /// @notice Index: debtorDidHash → all releaseIds (for debtor self-lookup).
    mapping(bytes32 => bytes32[]) public releasesByDebtor;

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event DebtCapRegistered(
        bytes32 indexed riteId,
        bytes32 indexed debtIdHash,
        uint256 principalMicroUsdc,
        uint256 accruedMicroUsdc,
        address indexed registrar,
        uint64 registeredAt
    );

    event ReleaseRecorded(
        bytes32 indexed releaseId,
        bytes32 indexed riteId,
        bytes32 indexed debtIdHash,
        bytes32 debtorDidHash,
        bytes32 creditorDidHash,
        uint256 releasedMicroUsdc,
        ReleaseMethod releaseMethod,
        bytes32 baseL2TxHashCrossRef,
        address recorder,
        uint64 releasedAt
    );

    // -------------------------------------------------------------------
    // Construction
    // -------------------------------------------------------------------

    constructor(YobelRiteRegistry riteRegistry) {
        RITE_REGISTRY = riteRegistry;
    }

    // -------------------------------------------------------------------
    // Debt cap (set by creditor enrollment off-chain, mirrored on-chain)
    // -------------------------------------------------------------------

    /**
     * @notice Mirror the encrypted creditor enrollment's debt principal +
     *         accrued amounts on-chain as a cap. Permissionless;
     *         {ReleaseSettlementCell} typically calls this just before
     *         {recordRelease}.
     *
     *         The "cap" represents the maximum releasable amount under
     *         Charter Rider §2(b) one-way invariant. Once registered, it
     *         cannot be amended.
     */
    function registerDebtCap(
        bytes32 riteId,
        bytes32 debtIdHash,
        uint256 principalMicroUsdc,
        uint256 accruedMicroUsdc
    ) external {
        if (!RITE_REGISTRY.isActive(riteId)) revert RiteNotActive(riteId);
        if (principalMicroUsdc + accruedMicroUsdc == 0) revert ZeroDebtCap();

        bytes32 key = _capKey(riteId, debtIdHash);
        if (debtCaps[key].registeredAt != 0) {
            revert DebtCapAlreadyRegistered(debtIdHash);
        }

        debtCaps[key] = DebtCap({
            principalMicroUsdc: principalMicroUsdc,
            accruedMicroUsdc: accruedMicroUsdc,
            totalReleasedMicroUsdc: 0,
            registrar: msg.sender,
            registeredAt: uint64(block.timestamp)
        });

        emit DebtCapRegistered(
            riteId,
            debtIdHash,
            principalMicroUsdc,
            accruedMicroUsdc,
            msg.sender,
            uint64(block.timestamp)
        );
    }

    // -------------------------------------------------------------------
    // Record release
    // -------------------------------------------------------------------

    /**
     * @notice Record an immutable release of debt. Enforces:
     *
     *           1. Rite must be Active in {RITE_REGISTRY}
     *           2. Debt cap must have been registered (via {registerDebtCap})
     *           3. Cumulative released amount ≤ cap (Charter Rider §2(b) one-way)
     *           4. releaseMethod must be a valid enum value
     *           5. releaseId must be globally unique
     *
     *         No constraint on debtor / creditor DID hashes — verification
     *         that the (debtor, creditor) pair corresponds to a real
     *         encrypted enrollment is the {ReleaseSettlementCell}'s
     *         responsibility off-chain.
     */
    function recordRelease(
        bytes32 releaseId,
        bytes32 riteId,
        bytes32 debtIdHash,
        bytes32 debtorDidHash,
        bytes32 creditorDidHash,
        uint256 releasedMicroUsdc,
        ReleaseMethod releaseMethod,
        bytes32 baseL2TxHashCrossRef
    ) external {
        if (releaseId == bytes32(0)) revert EmptyReleaseId();
        if (releases[releaseId].releasedAt != 0) revert ReleaseAlreadyRecorded(releaseId);
        if (!RITE_REGISTRY.isActive(riteId)) revert RiteNotActive(riteId);
        if (uint8(releaseMethod) > uint8(ReleaseMethod.EcclesiasticalIndulgence)) {
            revert InvalidReleaseMethod(uint8(releaseMethod));
        }

        bytes32 capKey = _capKey(riteId, debtIdHash);
        DebtCap storage cap = debtCaps[capKey];
        if (cap.registeredAt == 0) revert DebtCapNotRegistered(debtIdHash);

        uint256 totalCap = cap.principalMicroUsdc + cap.accruedMicroUsdc;
        uint256 newTotal = cap.totalReleasedMicroUsdc + releasedMicroUsdc;
        if (newTotal > totalCap) {
            revert OneWayViolation(newTotal, totalCap);
        }

        // releasedMicroUsdc=0 is legal (e.g. voluntary_bookkeeping records the rite
        // event without monetary transfer; ecclesiastical_indulgence is purely
        // doctrinal). Only the cumulative bound matters.

        cap.totalReleasedMicroUsdc = newTotal;

        releases[releaseId] = Release({
            releaseId: releaseId,
            riteId: riteId,
            debtIdHash: debtIdHash,
            debtorDidHash: debtorDidHash,
            creditorDidHash: creditorDidHash,
            releasedMicroUsdc: releasedMicroUsdc,
            releaseMethod: releaseMethod,
            baseL2TxHashCrossRef: baseL2TxHashCrossRef,
            releasedAt: uint64(block.timestamp),
            recorder: msg.sender
        });
        allReleaseIds.push(releaseId);
        releasesByRite[riteId].push(releaseId);
        releasesByDebtor[debtorDidHash].push(releaseId);

        emit ReleaseRecorded(
            releaseId,
            riteId,
            debtIdHash,
            debtorDidHash,
            creditorDidHash,
            releasedMicroUsdc,
            releaseMethod,
            baseL2TxHashCrossRef,
            msg.sender,
            uint64(block.timestamp)
        );
    }

    // -------------------------------------------------------------------
    // Views
    // -------------------------------------------------------------------

    function getRelease(bytes32 releaseId) external view returns (Release memory) {
        return releases[releaseId];
    }

    function getDebtCap(bytes32 riteId, bytes32 debtIdHash)
        external
        view
        returns (DebtCap memory)
    {
        return debtCaps[_capKey(riteId, debtIdHash)];
    }

    function releaseCount() external view returns (uint256) {
        return allReleaseIds.length;
    }

    function releaseCountByRite(bytes32 riteId) external view returns (uint256) {
        return releasesByRite[riteId].length;
    }

    function releaseCountByDebtor(bytes32 debtorDidHash) external view returns (uint256) {
        return releasesByDebtor[debtorDidHash].length;
    }

    // -------------------------------------------------------------------
    // Internals
    // -------------------------------------------------------------------

    function _capKey(bytes32 riteId, bytes32 debtIdHash) internal pure returns (bytes32) {
        return keccak256(abi.encode(riteId, debtIdHash));
    }
}
