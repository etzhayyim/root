// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

/**
 * @title KawaseYuiPool (為替結) — R0 bounded-AMM scaffold
 * @notice Religious-corp adherent-to-adherent multi-stable remittance pool
 *         per ADR-2605282200. One deploy per Base L2 stablecoin (USDC + EURC
 *         at R1; +JPYC R2; +KRWO/GBPe/CHFe R3 with Council Lv7+ unanimity per
 *         pair).
 *
 *         This file is the R0 scaffold — it defines the externally-callable
 *         interface, the events, the errors, and the Constitution + Adherent
 *         dependency surface, but every state-mutating function is marked
 *         `notYetImplemented` with a stub revert. R1 (post-Bootstrap-Council
 *         ratify) fills in the bodies.
 *
 *         Why ship a stub? Because the constitutional invariants (G3 adherent
 *         gating, G4 oracle band, G5 non-extractive fee accounting, G6 bounded
 *         AMM execution, G9 per-month cap, G11 no chargeback and Council-only
 *         policy changes) live in the SHAPE of this contract, not only in its
 *         implementation. AMM price impact, LP compensation and protocol
 *         revenue are deliberately represented as different quantities.
 *
 * @dev Constitution read pattern:
 *
 *          maxBandBps  = constitution.getConstant(K.KAWASE_MAX_BAND_BPS)
 *          monthlyCap  = constitution.getMutable(K.KAWASE_PER_MONTH_CAP_USD_MINOR)
 *
 *      Both keys wired in Deploy.s.sol + DeployReligiousCorp.s.sol +
 *      ConstitutionReligiousCorpWave.t.sol.
 */

// -------------------------------------------------------------------
//  Dependency interface surface (kept inline so this file compiles
//  in isolation; R1 imports the canonical ones from
//  ../etzhayyim-chain-contracts/src/.)
// -------------------------------------------------------------------

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address holder) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
}

interface IConstitution {
    function getConstant(bytes32 key) external view returns (bytes32);
    function getMutable(bytes32 key) external view returns (bytes32);
}

interface IAdherentRegistry {
    /// @notice Returns the SBT tokenId for an address, or 0 if the address
    ///         is not an Adherent. Adherent SBTs are minted with tokenIds
    ///         starting at 1, so `tokenOf(x) != 0` is the canonical
    ///         "is x an Adherent" check.
    function tokenOf(address holder) external view returns (uint256);
}

interface IChainlinkPriceFeed {
    function latestRoundData() external view returns (
        uint80  roundId,
        int256  answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80  answeredInRound
    );
    function decimals() external view returns (uint8);
}

// -------------------------------------------------------------------
//  KawaseYuiPool
// -------------------------------------------------------------------

contract KawaseYuiPool {
    // ─── Errors (constitutional-invariant-named) ──────────────────────────

    /// @notice G3 — sender or recipient lacks an Adherent SBT.
    error NotAdherent(address who);
    /// @notice G4 — quoted fxRateBps falls outside the ±maxBandBps tolerance
    ///         around the live Chainlink mid-market rate.
    error OutOfBandFx(uint256 quotedBps, uint256 chainlinkBps, uint256 maxBandBps);
    /// @notice G9 — deposit would push sender's rolling 30-day USD-equivalent
    ///         volume past the per-member monthly cap.
    error PerMonthCapBreached(address sender, uint256 attempted, uint256 cap);
    /// @notice rebalance() callable only by councilSafe (G14 / Lv6+ ≥4/7).
    error NotCouncilSafe();
    /// @notice intentCid was never deposited or has already been claimed.
    error UnknownOrClaimedIntent(bytes32 intentCid);
    /// @notice R0 scaffold guard — body lands at R1.
    error NotYetImplemented(string phase);
    /// @notice settlement contract requires explicit ERC-20 approve() first.
    error InsufficientPoolAllowance();
    /// @notice reserve buffer would fall below the configured floor.
    error ReserveBufferFloorBreached(uint256 want, uint256 available);
    /// @notice depositor's own address differs from the SBT-recorded holder.
    error DepositorNotSbtHolder(address signer, uint256 sbtTokenId);
    /// @notice G5 — protocol revenue is separately capped from LP compensation.
    error ProtocolFeeTooHigh(uint256 actualBps, uint256 maximumBps);
    /// @notice G5/G6 — liquidity-provider compensation exceeds policy.
    error LpFeeTooHigh(uint256 actualBps, uint256 maximumBps);
    /// @notice G4/G6 — execution price has moved too far from the oracle.
    error PriceImpactTooHigh(uint256 executionBps, uint256 oracleBps, uint256 maximumBps);
    /// @notice G6 — the quoted output violates the participant's own floor.
    error MinimumAmountOutBreached(uint256 quotedOut, uint256 minimumOut);
    /// @notice G6 — the bounded pool cannot honestly satisfy this output.
    error InsufficientAmmLiquidity(uint256 quotedOut, uint256 availableOut);

    // ─── Events ──────────────────────────────────────────────────────────

    event Deposited(
        bytes32 indexed intentCid,
        address indexed senderDid,
        address indexed recipientDid,
        uint256 srcAmountMinor,
        uint256 fxRateBps,
        bytes32 fxRateAttestationCid
    );

    event Matched(
        bytes32 indexed intentCid,
        bytes32 indexed counterCid,
        uint256 srcMinor,
        uint256 tgtMinor
    );

    event ReserveDisbursed(
        bytes32 indexed intentCid,
        uint256 srcMinor,
        uint256 tgtMinor
    );

    event Claimed(
        bytes32 indexed intentCid,
        address indexed recipientDid,
        uint256 tgtMinor
    );

    event Rebalanced(
        uint256 fromMinor,
        uint256 toMinor,
        address indexed dex,
        uint256 swapRateBps,
        bytes32 attestationCid
    );

    event BoundedAmmSwap(
        bytes32 indexed intentCid,
        address indexed adapter,
        uint256 amountInMinor,
        uint256 amountOutMinor,
        uint256 oracleRateBps,
        uint256 executionRateBps,
        uint256 lpFeeBps,
        uint256 protocolFeeBps
    );

    // ─── Types ───────────────────────────────────────────────────────────

    struct Intent {
        address senderDid;        // wallet that called deposit
        address recipientDid;     // claim() must come from this address
        uint256 srcAmountMinor;   // amount sender paid in
        uint256 tgtAmountMinor;   // amount recipient will claim
        uint256 fxRateBps;        // locked at deposit time
        uint256 depositedAt;      // block.timestamp at deposit
        bool    claimed;
    }

    // ─── Immutable wiring ────────────────────────────────────────────────

    IERC20              public immutable stable;            // USDC or EURC
    IAdherentRegistry   public immutable adherentRegistry;  // G3 gate
    IConstitution       public immutable constitution;      // G4 + G9 reads
    IChainlinkPriceFeed public immutable priceFeed;         // G4 oracle
    address             public immutable councilSafe;       // G14 rebalance
    bytes32             public immutable maxBandBpsKey;     // KAWASE_MAX_BAND_BPS
    bytes32             public immutable monthlyCapKey;     // KAWASE_PER_MONTH_CAP_USD_MINOR

    uint256 public constant BPS_DENOMINATOR = 10_000;
    uint256 public constant ROLLING_WINDOW_SECS = 30 days;
    /// @notice LP compensation is disclosed and capped independently from
    ///         protocol revenue. 30 bps matches the conservative R1 ceiling;
    ///         a deployment may select a lower tier, including zero.
    uint256 public constant MAX_LP_FEE_BPS = 30;
    /// @notice R1 launches with protocolFeeBps=0. This hard ceiling prevents a
    ///         future adapter from turning the mutual-aid pool into an
    ///         extractive spread business without replacing this contract.
    uint256 public constant MAX_PROTOCOL_FEE_BPS = 5;
    /// @notice Maximum execution-price deviation from the attested oracle.
    uint256 public constant MAX_AMM_PRICE_IMPACT_BPS = 50;

    // ─── Mutable storage ─────────────────────────────────────────────────

    mapping(bytes32 => Intent) public intents;

    /// @notice Rolling 30-day USD-equivalent volume per Adherent address. R1
    ///         expires entries older than ROLLING_WINDOW_SECS on each deposit;
    ///         R0 scaffold leaves the eviction policy to the body.
    mapping(address => uint256) public monthlyVolumeUsdMinor;
    mapping(address => uint256) public monthlyVolumeWindowStart;

    /// @notice Reserve buffer floor (minor units of `stable`). Below this
    ///         floor, new deposits halt for the pair. Wired post-deploy
    ///         (Council Lv6+ ≥3 attestation chain).
    uint256 public reserveBufferFloorMinor;

    // ─── Constructor ─────────────────────────────────────────────────────

    constructor(
        IERC20 _stable,
        IAdherentRegistry _adherentRegistry,
        IConstitution _constitution,
        IChainlinkPriceFeed _priceFeed,
        address _councilSafe,
        bytes32 _maxBandBpsKey,
        bytes32 _monthlyCapKey,
        uint256 _reserveBufferFloorMinor
    ) {
        require(address(_stable) != address(0), "stable=0");
        require(address(_adherentRegistry) != address(0), "registry=0");
        require(address(_constitution) != address(0), "constitution=0");
        require(address(_priceFeed) != address(0), "priceFeed=0");
        require(_councilSafe != address(0), "councilSafe=0");
        stable = _stable;
        adherentRegistry = _adherentRegistry;
        constitution = _constitution;
        priceFeed = _priceFeed;
        councilSafe = _councilSafe;
        maxBandBpsKey = _maxBandBpsKey;
        monthlyCapKey = _monthlyCapKey;
        reserveBufferFloorMinor = _reserveBufferFloorMinor;
    }

    // ─── Modifiers ───────────────────────────────────────────────────────

    /// @notice G3 — both legs of every kawase flow must be Adherent SBT
    ///         holders. The contract revert is the constitutional fence;
    ///         no governance proposal can disable this modifier.
    modifier onlyAdherent(address who) {
        if (adherentRegistry.tokenOf(who) == 0) revert NotAdherent(who);
        _;
    }

    /// @notice G14 — councilSafe is the only address authorized to call
    ///         rebalance(). Council Lv6+ ≥4/7 threshold is enforced at the
    ///         Safe (multisig) layer; the contract only checks identity.
    modifier onlyCouncilSafe() {
        if (msg.sender != councilSafe) revert NotCouncilSafe();
        _;
    }

    // ─── External surface (R0 stubs; R1 fills in) ────────────────────────

    /**
     * @notice Sender deposits `srcAmountMinor` of `stable` into the pool,
     *         designating `recipientDid` as the claimant. The Chainlink
     *         mid-market rate is locked at this call site; subsequent
     *         oracle drift is absorbed by the reserve buffer.
     *
     *         R1 will:
     *           1. require(intents[intentCid].senderDid == address(0)) — no replay
     *           2. require senderDid + recipientDid both onlyAdherent
     *           3. read chainlink latestRoundData() + check withinBand(±maxBandBps)
     *           4. read monthlyCap + verify _newRollingTotal ≤ cap
     *           5. transferFrom(senderDid → this) srcAmountMinor of `stable`
     *           6. store intents[intentCid] + bump monthlyVolume
     *           7. emit Deposited
     *
     *         The pool-match Pregel cell (off-chain) consumes the event +
     *         emits matchExecution OR reserve-disburses via fillFromReserve().
     */
    function deposit(
        bytes32 /* intentCid */,
        address recipientDid,
        uint256 /* srcAmountMinor */,
        uint256 /* fxRateBps */,
        bytes32 /* fxRateAttestationCid */
    )
        external
        onlyAdherent(msg.sender)
        onlyAdherent(recipientDid)
    {
        revert NotYetImplemented("R1: deposit() body lands post-Bootstrap-Council ratify");
    }

    /**
     * @notice Recipient claims the matched amount.
     *
     *         R1 will:
     *           1. load intents[intentCid]; revert if claimed or unknown
     *           2. require msg.sender == intents[intentCid].recipientDid
     *           3. transfer(recipient, tgtAmountMinor) of `stable`
     *           4. set intents[intentCid].claimed = true
     *           5. emit Claimed
     */
    function claim(bytes32 /* intentCid */)
        external
        onlyAdherent(msg.sender)
    {
        revert NotYetImplemented("R1: claim() body lands post-Bootstrap-Council ratify");
    }

    /**
     * @notice Council-authorized DEX swap to restore pool balance when
     *         |driftBps| > 500 (5%) on the paired pool.
     *
     *         R1 will:
     *           1. require msg.sender == councilSafe (modifier)
     *           2. require attestationCid CID corresponds to a Council-signed
     *              rebalanceAttestation Lexicon record (off-chain verified;
     *              contract just records the CID for audit)
     *           3. stable.approve(dex, amountInMinor)
     *           4. call dex.swap(...) with the supplied amountInMinor + min-out
     *           5. emit Rebalanced
     */
    function rebalance(
        address /* dex */,
        uint256 /* amountInMinor */,
        uint256 /* minAmountOutMinor */,
        uint256 /* swapRateBps */,
        bytes32 /* attestationCid */
    )
        external
        onlyCouncilSafe
    {
        revert NotYetImplemented("R1: rebalance() body lands post-Bootstrap-Council ratify");
    }

    /**
     * @notice Validate an AMM quote without conflating price impact, LP fee and
     *         protocol revenue. R1 adapters MUST call this before a swap and
     *         additionally enforce deadline, approved adapter/hook codehash,
     *         fresh-oracle and exact minAmountOut calldata on-chain.
     *
     *         This policy permits a constant-product or concentrated-liquidity
     *         implementation. It does not permit leverage, rehypothecation,
     *         arbitrary hooks, hidden routing or an operator price override.
     */
    function validateAmmQuote(
        uint256 executionRateBps,
        uint256 oracleRateBps,
        uint256 quotedAmountOutMinor,
        uint256 minAmountOutMinor,
        uint256 availableAmountOutMinor,
        uint256 lpFeeBps,
        uint256 protocolFeeBps
    ) public pure returns (bool) {
        if (protocolFeeBps > MAX_PROTOCOL_FEE_BPS) {
            revert ProtocolFeeTooHigh(protocolFeeBps, MAX_PROTOCOL_FEE_BPS);
        }
        if (lpFeeBps > MAX_LP_FEE_BPS) {
            revert LpFeeTooHigh(lpFeeBps, MAX_LP_FEE_BPS);
        }
        if (oracleRateBps == 0) {
            revert PriceImpactTooHigh(
                executionRateBps, oracleRateBps, MAX_AMM_PRICE_IMPACT_BPS
            );
        }
        uint256 rateDiff = executionRateBps > oracleRateBps
            ? executionRateBps - oracleRateBps
            : oracleRateBps - executionRateBps;
        if (rateDiff > (oracleRateBps * MAX_AMM_PRICE_IMPACT_BPS) / BPS_DENOMINATOR) {
            revert PriceImpactTooHigh(
                executionRateBps, oracleRateBps, MAX_AMM_PRICE_IMPACT_BPS
            );
        }
        if (quotedAmountOutMinor < minAmountOutMinor) {
            revert MinimumAmountOutBreached(quotedAmountOutMinor, minAmountOutMinor);
        }
        if (quotedAmountOutMinor > availableAmountOutMinor) {
            revert InsufficientAmmLiquidity(quotedAmountOutMinor, availableAmountOutMinor);
        }
        return true;
    }

    // ─── Reads ──────────────────────────────────────────────────────────

    /// @notice Returns the live Chainlink mid-market rate in basis points
    ///         (10000 = 1.0000). R1 will scale by 10**(4 - feed.decimals())
    ///         or vice versa; R0 placeholder returns 0.
    function chainlinkRateBps() public view returns (uint256) {
        // R1: (uint80, int256 answer, uint256, uint256 updatedAt, uint80) = priceFeed.latestRoundData();
        // R1: scale by decimals; return uint256(answer) * BPS_DENOMINATOR / 10**feed.decimals();
        priceFeed; // silence unused warning until R1
        return 0;
    }

    /// @notice Returns the constitutional ±band tolerance in basis points.
    function maxBandBps() public view returns (uint256) {
        return uint256(constitution.getConstant(maxBandBpsKey));
    }

    /// @notice Returns the per-member monthly cap (mutable; Council Lv6+ ≥3
    ///         may adjust between R-cycles).
    function perMonthCapUsdMinor() public view returns (uint256) {
        return uint256(constitution.getMutable(monthlyCapKey));
    }

    /// @notice True iff `quotedBps` is within ±maxBandBps() of the live
    ///         Chainlink mid-market. R0 always returns false because
    ///         chainlinkRateBps() returns 0 in the scaffold; R1 wires the
    ///         real check.
    function withinBand(uint256 quotedBps) public view returns (bool) {
        uint256 live = chainlinkRateBps();
        uint256 band = maxBandBps();
        if (live == 0) return false;
        uint256 diff = quotedBps > live ? quotedBps - live : live - quotedBps;
        return diff <= (live * band) / BPS_DENOMINATOR;
    }
}
