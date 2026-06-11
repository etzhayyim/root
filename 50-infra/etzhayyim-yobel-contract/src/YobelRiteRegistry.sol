// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title YobelRiteRegistry
 * @notice Immutable append-only registry of collective debt release rites
 *         (shmita / yobel / tokusei-rei / Catholic Jubilee / political amnesty)
 *         declared under etzhayyim religious-corp doctrinal authority.
 *
 * @dev Per ADR-2605201800 (Yobel Collective Debt Release Actor).
 *      Apache-2.0 + Charter Compliance Rider v2.0.
 *
 *      Design rules (matching EtzhayyimAnchor / AnchorBridge pattern):
 *
 *        - **NO admin.** No owner, no upgrade path, no pause. The contract
 *          code is the only governance — to change behavior, deploy a new
 *          contract under a new yobel actor version.
 *
 *        - **Permissionless write.** Anyone can call {declareRite}. The
 *          on-chain record of who declared (msg.sender + their on-chain
 *          identity, resolvable to a DID via attestation) is the audit
 *          trail. There is no whitelist; the declarer's reputation is
 *          established off-chain via their DID + Council SBT.
 *
 *        - **Append-only.** Once a rite is declared with a given `riteId`,
 *          its core fields (riteType, scope hash, doctrinalBasis hash,
 *          effectiveDate, expiryDate, issuer) are immutable. Status
 *          transitions are gated by the state machine in {ratifyRite},
 *          {completeRite}, {cancelRite}, {supersedeRite}.
 *
 *        - **Ratification is privacy-preserving.** Council signatures are
 *          stored as a single hash of the canonical signature set + a
 *          ratifier count; the full signature set lives off-chain (encrypted
 *          per ADR-2605181100). Verifiers reconstruct the canonical hash
 *          and assert equality against {ratificationHash}.
 *
 *        - **No fiat / no Stripe / no RisingWave.** This contract takes
 *          ETH only for direct revert refunds (it does not accept value).
 *          USDC settlement happens in {YobelReleaseRegistry} cross-linked
 *          via riteId.
 *
 *        - **Charter Rider §2(b) one-way invariant.** This contract has
 *          NO loan / interest / margin / liquidation methods. Rites are
 *          declared, ratified, completed, or superseded — never amended
 *          to increase debtor coercion.
 *
 *      Status state machine:
 *
 *        Declared ──{ratifyRite, Council Lv6+ × 3 + Lv9 chair}──► Active
 *        Declared ──{cancelRite, declarer or Council Lv9}──► Cancelled
 *        Active   ──{completeRite, anyone after expiry}──► Completed
 *        Active   ──{supersedeRite, audit_witness on tampering or new rite}──► Superseded
 *
 *      Status transitions emit events for off-chain indexers (yoro feed,
 *      Public Fund audit, third-party verifiers).
 */
contract YobelRiteRegistry {

    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error RiteAlreadyExists(bytes32 riteId);
    error RiteNotFound(bytes32 riteId);
    error InvalidStatusTransition(bytes32 riteId, Status from, Status to);
    error InvalidRiteType(uint8 riteType);
    error EmptyDoctrinalBasisHash();
    error EmptyScopeHash();
    error EmptyRatificationHash();
    error RatifierCountTooLow(uint16 actual, uint16 required);
    error ExpiryBeforeEffective(uint64 effectiveDate, uint64 expiryDate);
    error ExpiryNotReached(uint64 expiryDate, uint64 currentBlockTimestamp);
    error NotDeclarer(address actual, address declarer);
    error ZeroIssuer();

    // -------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------

    /// @notice One of the 5 canonical rite types per ADR-2605201800.
    enum RiteType {
        Shmita7yr,
        Yobel50yr,
        TokuseiRei,
        ReligiousJubilee,
        PoliticalAmnesty
    }

    /// @notice Lifecycle status per ADR-2605201800 §Decision.
    enum Status {
        Unknown,     // sentinel (uninitialized riteId)
        Declared,    // emit declared, awaiting Council ratification
        Active,      // ratified, accepting enrollments + releases
        Completed,   // expiry passed, rite complete
        Cancelled,   // never ratified or declarer withdrew
        Superseded   // audit_witness detected tampering / new rite overrides
    }

    /// @dev One declared rite. Stored 1:1 with riteId.
    struct Rite {
        bytes32 riteId;
        RiteType riteType;
        bytes32 doctrinalBasisHash;  // keccak256(canonical doctrinalBasis text)
        bytes32 scopeHash;           // keccak256(canonical scope text)
        uint64 effectiveDate;
        uint64 expiryDate;           // 0 = perpetual / single-event
        address declarer;            // msg.sender at declareRite time
        bytes32 issuerDidHash;       // keccak256(issuer DID — etzhayyim-aligned)
        Status status;
        bytes32 ratificationHash;    // keccak256(canonical Council signature set), 0 if not ratified
        uint16 ratifierCount;        // count of Council Lv6+ signers (must be ≥ minRatifierCount)
        uint64 declaredAt;
        uint64 ratifiedAt;
        uint64 completedOrSupersededAt;
        bytes32 supersededByRiteId;  // 0 unless status=Superseded
    }

    // -------------------------------------------------------------------
    // Constants
    // -------------------------------------------------------------------

    /// @notice Minimum Council Lv6+ ratifier count (Charter §1.13 + ADR-2605192230
    ///         Three-Tier Enforcement tier 3 baseline). Per-rite-type aggregation
    ///         (DMN council-ratification-threshold.md) is enforced off-chain — this
    ///         contract gates only the floor.
    uint16 public constant MIN_RATIFIER_COUNT = 4;

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    /// @notice riteId → rite. Append-only after declareRite.
    mapping(bytes32 => Rite) public rites;

    /// @notice Append-only list of all declared riteIds for enumeration.
    bytes32[] public allRiteIds;

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event RiteDeclared(
        bytes32 indexed riteId,
        RiteType indexed riteType,
        address indexed declarer,
        bytes32 doctrinalBasisHash,
        bytes32 scopeHash,
        bytes32 issuerDidHash,
        uint64 effectiveDate,
        uint64 expiryDate,
        uint64 declaredAt
    );

    event RiteRatified(
        bytes32 indexed riteId,
        bytes32 indexed ratificationHash,
        uint16 ratifierCount,
        uint64 ratifiedAt
    );

    event RiteCompleted(bytes32 indexed riteId, uint64 completedAt);

    event RiteCancelled(bytes32 indexed riteId, address indexed canceller, uint64 cancelledAt, bytes32 reasonHash);

    event RiteSuperseded(
        bytes32 indexed riteId,
        bytes32 indexed supersededByRiteId,
        address indexed canceller,
        uint64 supersededAt,
        bytes32 reasonHash
    );

    // -------------------------------------------------------------------
    // Declare
    // -------------------------------------------------------------------

    /**
     * @notice Declare a new rite. Permissionless; msg.sender is recorded
     *         as `declarer` for off-chain DID resolution.
     *
     *         Status transitions to Declared immediately. Ratification
     *         requires a subsequent {ratifyRite} call once Council Lv6+
     *         × 3 + Lv9 chair signatures are collected off-chain.
     *
     * @param riteId            Globally unique identifier (e.g. keccak256("shmita-5786"))
     * @param riteType          One of the 5 canonical RiteType enum values
     * @param doctrinalBasisHash keccak256 of the canonical doctrinalBasis text (Lev 25:1-7 etc.)
     * @param scopeHash         keccak256 of the canonical scope text
     * @param effectiveDate     Unix timestamp when the rite becomes effective
     * @param expiryDate        Unix timestamp when the rite expires (0 = perpetual)
     * @param issuerDidHash     keccak256 of the issuer DID string
     */
    function declareRite(
        bytes32 riteId,
        RiteType riteType,
        bytes32 doctrinalBasisHash,
        bytes32 scopeHash,
        uint64 effectiveDate,
        uint64 expiryDate,
        bytes32 issuerDidHash
    ) external {
        if (rites[riteId].status != Status.Unknown) {
            revert RiteAlreadyExists(riteId);
        }
        if (uint8(riteType) > uint8(RiteType.PoliticalAmnesty)) {
            revert InvalidRiteType(uint8(riteType));
        }
        if (doctrinalBasisHash == bytes32(0)) revert EmptyDoctrinalBasisHash();
        if (scopeHash == bytes32(0)) revert EmptyScopeHash();
        if (issuerDidHash == bytes32(0)) revert ZeroIssuer();
        if (expiryDate != 0 && expiryDate <= effectiveDate) {
            revert ExpiryBeforeEffective(effectiveDate, expiryDate);
        }

        rites[riteId] = Rite({
            riteId: riteId,
            riteType: riteType,
            doctrinalBasisHash: doctrinalBasisHash,
            scopeHash: scopeHash,
            effectiveDate: effectiveDate,
            expiryDate: expiryDate,
            declarer: msg.sender,
            issuerDidHash: issuerDidHash,
            status: Status.Declared,
            ratificationHash: bytes32(0),
            ratifierCount: 0,
            declaredAt: uint64(block.timestamp),
            ratifiedAt: 0,
            completedOrSupersededAt: 0,
            supersededByRiteId: bytes32(0)
        });
        allRiteIds.push(riteId);

        emit RiteDeclared(
            riteId,
            riteType,
            msg.sender,
            doctrinalBasisHash,
            scopeHash,
            issuerDidHash,
            effectiveDate,
            expiryDate,
            uint64(block.timestamp)
        );
    }

    // -------------------------------------------------------------------
    // Ratify
    // -------------------------------------------------------------------

    /**
     * @notice Transition Declared → Active by recording Council ratification.
     *         The signature set is hashed off-chain via canonical encoding;
     *         this contract stores only the hash + count. Verifiers fetch
     *         the signature set from the encrypted AT MST record and verify
     *         the hash on-chain.
     *
     *         The {MIN_RATIFIER_COUNT} floor (4 = 3 Lv6+ + 1 Lv9 chair) is
     *         enforced on-chain. Per-rite-type higher thresholds (yobel_50yr
     *         +2, political_amnesty +3, etc.) are enforced by the
     *         {YobelOrchestrator} off-chain before this call is made.
     *
     * @param riteId               Existing rite, must be in Declared status
     * @param ratificationHash     keccak256 of the canonical signature set
     * @param ratifierCount        Number of distinct Council Lv6+ signers in the set
     */
    function ratifyRite(
        bytes32 riteId,
        bytes32 ratificationHash,
        uint16 ratifierCount
    ) external {
        Rite storage r = rites[riteId];
        if (r.status == Status.Unknown) revert RiteNotFound(riteId);
        if (r.status != Status.Declared) {
            revert InvalidStatusTransition(riteId, r.status, Status.Active);
        }
        if (ratificationHash == bytes32(0)) revert EmptyRatificationHash();
        if (ratifierCount < MIN_RATIFIER_COUNT) {
            revert RatifierCountTooLow(ratifierCount, MIN_RATIFIER_COUNT);
        }

        r.status = Status.Active;
        r.ratificationHash = ratificationHash;
        r.ratifierCount = ratifierCount;
        r.ratifiedAt = uint64(block.timestamp);

        emit RiteRatified(riteId, ratificationHash, ratifierCount, uint64(block.timestamp));
    }

    // -------------------------------------------------------------------
    // Complete
    // -------------------------------------------------------------------

    /**
     * @notice Transition Active → Completed. Permissionless; anyone can
     *         finalize an active rite once its expiry has passed.
     *         Idempotent (re-completing reverts via status check).
     */
    function completeRite(bytes32 riteId) external {
        Rite storage r = rites[riteId];
        if (r.status == Status.Unknown) revert RiteNotFound(riteId);
        if (r.status != Status.Active) {
            revert InvalidStatusTransition(riteId, r.status, Status.Completed);
        }
        if (r.expiryDate == 0) {
            // Perpetual rite; complete requires a separate supersedeRite
            revert ExpiryNotReached(r.expiryDate, uint64(block.timestamp));
        }
        if (uint64(block.timestamp) < r.expiryDate) {
            revert ExpiryNotReached(r.expiryDate, uint64(block.timestamp));
        }

        r.status = Status.Completed;
        r.completedOrSupersededAt = uint64(block.timestamp);

        emit RiteCompleted(riteId, uint64(block.timestamp));
    }

    // -------------------------------------------------------------------
    // Cancel
    // -------------------------------------------------------------------

    /**
     * @notice Transition Declared → Cancelled by the original declarer.
     *         (Council Lv9 cancellation requires a multisig path — deferred
     *         to a future YobelGovernance contract.)
     */
    function cancelRite(bytes32 riteId, bytes32 reasonHash) external {
        Rite storage r = rites[riteId];
        if (r.status == Status.Unknown) revert RiteNotFound(riteId);
        if (r.status != Status.Declared) {
            revert InvalidStatusTransition(riteId, r.status, Status.Cancelled);
        }
        if (msg.sender != r.declarer) revert NotDeclarer(msg.sender, r.declarer);

        r.status = Status.Cancelled;
        r.completedOrSupersededAt = uint64(block.timestamp);

        emit RiteCancelled(riteId, msg.sender, uint64(block.timestamp), reasonHash);
    }

    // -------------------------------------------------------------------
    // Supersede
    // -------------------------------------------------------------------

    /**
     * @notice Transition Active → Superseded. Permissionless; called by
     *         {AuditWitnessCell} on confirmed tampering, or by a newer rite
     *         that overrides this one. The `supersededByRiteId` MUST be a
     *         declared rite in this same registry (caller's responsibility
     *         to ensure causal chain off-chain).
     */
    function supersedeRite(
        bytes32 riteId,
        bytes32 supersededByRiteId,
        bytes32 reasonHash
    ) external {
        Rite storage r = rites[riteId];
        if (r.status == Status.Unknown) revert RiteNotFound(riteId);
        if (r.status != Status.Active) {
            revert InvalidStatusTransition(riteId, r.status, Status.Superseded);
        }

        r.status = Status.Superseded;
        r.supersededByRiteId = supersededByRiteId;
        r.completedOrSupersededAt = uint64(block.timestamp);

        emit RiteSuperseded(
            riteId,
            supersededByRiteId,
            msg.sender,
            uint64(block.timestamp),
            reasonHash
        );
    }

    // -------------------------------------------------------------------
    // Views
    // -------------------------------------------------------------------

    function getRite(bytes32 riteId) external view returns (Rite memory) {
        return rites[riteId];
    }

    function isActive(bytes32 riteId) external view returns (bool) {
        return rites[riteId].status == Status.Active;
    }

    function riteCount() external view returns (uint256) {
        return allRiteIds.length;
    }
}
