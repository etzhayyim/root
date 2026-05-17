// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {AdherentRegistry} from "./AdherentRegistry.sol";
import {Constitution} from "./Constitution.sol";
import {Phenotype} from "./Phenotype.sol";

/**
 * @title KishaStream
 * @notice Per-adherent basic-income (喜捨 / kisha) accrual on geth-private.
 *         Stage-1 ("S1") of ADR-2605172300: flat per-day rate, pure
 *         time-based accrual, no Pregel cell yet, no Phenotype multiplier
 *         yet.
 *
 * @dev Lives on geth-private (ChainID 2605). The USDC settlement step
 *      runs on Base L2 (see {KishaPayout}); this contract only:
 *
 *        1. computes the accrued amount as a pure function of
 *           (now - lastClaimedAt) × baseRate
 *        2. updates lastClaimedAt to "now" on claim
 *        3. emits a ClaimTicketIssued(...) event that an off-chain
 *           officer-relayer picks up and submits to Base KishaPayout
 *
 *      Double-claim on geth-private is prevented by lastClaimedAt
 *      monotonicity. Double-fulfillment on Base is prevented by
 *      KishaPayout's own (ticketId → fulfilled) set, keyed on
 *      keccak256(tokenId, claimSeq), which is also the event's
 *      `ticketId`. There is no back-relay to mark fulfillment on
 *      geth-private; the act of issuing the ticket already consumed
 *      the accrual on this side.
 *
 *      Per ADR-2605172300 §2 + §5. Apache-2.0.
 */
contract KishaStream {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error NotGovernance();
    error UnknownToken(uint256 tokenId);
    error NotHolder();
    error TokenRevoked();
    error NotActive();
    error NothingAccrued();
    error AmountAboveAccrued();

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event BaseRateSet(uint256 oldRate, uint256 newRate);
    event PhenotypeSet(address indexed oldPhenotype, address indexed newPhenotype);
    event ClaimTicketIssued(
        bytes32 indexed ticketId,
        uint256 indexed tokenId,
        address indexed holder,
        address baseRecipient,
        uint256 amount,
        uint64  claimSeq,
        uint64  issuedAt,
        uint64  expiresAt
    );

    // -------------------------------------------------------------------
    // Immutable wiring
    // -------------------------------------------------------------------

    AdherentRegistry public immutable registry;
    Constitution     public immutable constitution;

    /// @notice Active-adherent window read from Constitution at construct
    ///         time. Cached for cheap reads; can be refreshed only by
    ///         redeploying KishaStream (kept simple for S1; S3 governance
    ///         can call setActiveWindow).
    uint64 public activeWindowSecs;

    /// @notice Claim ticket TTL on Base L2. After this, the relayer must
    ///         drop the ticket; user must call claim() again.
    uint64 public constant TICKET_TTL_SECS = 14 days;

    // -------------------------------------------------------------------
    // Mutable state
    // -------------------------------------------------------------------

    /// @notice USDC base units (6 decimals) per adherent per day.
    ///         S1 default: 1_000_000 = 1.00 USDC / day.
    ///         Settable only by Constitution-bound governance.
    uint256 public baseRatePerDay;

    /// @notice tokenId → last block.timestamp at which kisha was claimed
    ///         (or joinedAt if never claimed).
    mapping(uint256 => uint64) public lastClaimedAt;

    /// @notice tokenId → monotonically increasing claim sequence number,
    ///         used as the ticket's uniqueness component.
    mapping(uint256 => uint64) public claimSeq;

    /// @notice Optional Phenotype contract (S2). When unset, the
    ///         multiplier is treated as 10_000 bps (1.0×).
    Phenotype public phenotype;

    // -------------------------------------------------------------------
    // Construction
    // -------------------------------------------------------------------

    constructor(
        AdherentRegistry registry_,
        Constitution constitution_,
        uint256 initialBaseRatePerDay,
        uint64 initialActiveWindowSecs
    ) {
        registry = registry_;
        constitution = constitution_;
        baseRatePerDay = initialBaseRatePerDay;
        activeWindowSecs = initialActiveWindowSecs;
    }

    // -------------------------------------------------------------------
    // Governance-only setters
    // -------------------------------------------------------------------

    modifier onlyGovernance() {
        if (msg.sender != constitution.governance()) revert NotGovernance();
        _;
    }

    function setBaseRate(uint256 newRatePerDay) external onlyGovernance {
        emit BaseRateSet(baseRatePerDay, newRatePerDay);
        baseRatePerDay = newRatePerDay;
    }

    function setActiveWindow(uint64 newWindowSecs) external onlyGovernance {
        activeWindowSecs = newWindowSecs;
    }

    function setPhenotype(Phenotype newPhenotype) external onlyGovernance {
        emit PhenotypeSet(address(phenotype), address(newPhenotype));
        phenotype = newPhenotype;
    }

    // -------------------------------------------------------------------
    // Reads
    // -------------------------------------------------------------------

    /**
     * @notice Pure accrual computation as of `at`. Does not mutate state.
     *         Returns 0 if the adherent is not active in the trailing
     *         `activeWindowSecs` window.
     *
     * @dev S2: applies Phenotype multiplier when the phenotype contract
     *      is wired. Multiplier is in basis points (10_000 = 1.0×) and
     *      is already bounded by Phenotype.sol against constitutional
     *      floor/ceiling — no second clamp needed here.
     */
    function previewAccrued(uint256 tokenId, uint64 at) public view returns (uint256) {
        AdherentRegistry.AdherentRecord memory r = registry.getRecord(tokenId);
        if (r.revoked) return 0;
        if (!registry.isActive(tokenId, activeWindowSecs)) return 0;

        uint64 last = lastClaimedAt[tokenId];
        if (last == 0) last = r.joinedAt;
        if (at <= last) return 0;

        unchecked {
            uint256 elapsed = uint256(at - last);
            // base amount = baseRatePerDay × elapsed / 86400
            uint256 base = (baseRatePerDay * elapsed) / 1 days;
            if (address(phenotype) == address(0)) return base;
            uint16 mulBps = phenotype.getMultiplierBps(tokenId);
            // amount = base × mulBps / 10_000
            return (base * uint256(mulBps)) / 10_000;
        }
    }

    function accruedNow(uint256 tokenId) external view returns (uint256) {
        return previewAccrued(tokenId, uint64(block.timestamp));
    }

    // -------------------------------------------------------------------
    // Claim — issue a ticket to be fulfilled on Base
    // -------------------------------------------------------------------

    /**
     * @notice Claim accrued kisha. Mints a ClaimTicket consumable by
     *         {KishaPayout} on Base L2. Updates lastClaimedAt to now
     *         (preventing double-claim on this side regardless of
     *         whether the Base side ever fulfills).
     *
     * @param tokenId         The adherent's SBT id.
     * @param baseRecipient   The Base L2 address that will receive USDC.
     *                        Usually the adherent's Coinbase Smart Wallet
     *                        (may differ from the geth-private holder).
     * @param maxAmount       Cap on the issued amount. Pass 0 to claim
     *                        the entire accrued balance.
     * @return ticketId       keccak256(tokenId, claimSeq) — the unique
     *                        identifier the relayer passes to KishaPayout.
     * @return amount         Amount actually issued (≤ accrued, ≤ maxAmount).
     */
    function claim(
        uint256 tokenId,
        address baseRecipient,
        uint256 maxAmount
    ) external returns (bytes32 ticketId, uint256 amount) {
        AdherentRegistry.AdherentRecord memory r = registry.getRecord(tokenId);
        if (r.holder == address(0)) revert UnknownToken(tokenId);
        if (msg.sender != r.holder) revert NotHolder();
        if (r.revoked) revert TokenRevoked();
        if (!registry.isActive(tokenId, activeWindowSecs)) revert NotActive();

        uint256 accrued = previewAccrued(tokenId, uint64(block.timestamp));
        if (accrued == 0) revert NothingAccrued();

        amount = (maxAmount == 0 || maxAmount > accrued) ? accrued : maxAmount;
        if (amount > accrued) revert AmountAboveAccrued();

        // Advance lastClaimedAt proportionally to the amount we issued
        // (partial claim). Use the same multiplier as previewAccrued so
        // the inverse maps elapsed back from amount correctly even with
        // a non-unity phenotype multiplier.
        uint16 mulBps = (address(phenotype) == address(0)) ? uint16(10_000) : phenotype.getMultiplierBps(tokenId);
        uint256 elapsed = (amount * 1 days * 10_000) / (baseRatePerDay * uint256(mulBps));
        uint64 advanced = uint64(uint256(lastClaimedAt[tokenId] == 0 ? r.joinedAt : lastClaimedAt[tokenId]) + elapsed);
        if (advanced > uint64(block.timestamp)) advanced = uint64(block.timestamp);
        lastClaimedAt[tokenId] = advanced;

        uint64 seq = ++claimSeq[tokenId];
        ticketId = keccak256(abi.encodePacked(address(this), tokenId, seq));

        emit ClaimTicketIssued(
            ticketId,
            tokenId,
            r.holder,
            baseRecipient,
            amount,
            seq,
            uint64(block.timestamp),
            uint64(block.timestamp) + TICKET_TTL_SECS
        );
    }
}
