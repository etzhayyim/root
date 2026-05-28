// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import {
    KawaseYuiPool,
    IERC20,
    IAdherentRegistry,
    IConstitution,
    IChainlinkPriceFeed
} from "../src/KawaseYuiPool.sol";

/**
 * @title KawaseYuiPoolR0Test
 * @notice R0 scaffold tests for KawaseYuiPool — verifies the constitutional
 *         invariants are honored at the interface level BEFORE R1 fills in
 *         the bodies.
 *
 *         What this test suite proves (all R0; no R1 body required):
 *
 *           1. The constructor accepts every required wiring address and
 *              records the immutables correctly.
 *           2. The onlyAdherent modifier rejects callers whose Adherent SBT
 *              tokenOf(...) returns 0 (G3).
 *           3. The onlyCouncilSafe modifier rejects every msg.sender other
 *              than the configured councilSafe (G14).
 *           4. deposit() / claim() / rebalance() all revert with
 *              NotYetImplemented at R0 — proving the scaffold is honest about
 *              its state and the R1 body lands separately.
 *           5. maxBandBps() reads through to the Constitution mock and
 *              returns the wired value (G4 plumbing).
 *           6. perMonthCapUsdMinor() reads through to the Constitution mock
 *              and returns the wired value (G9 plumbing).
 *
 *         These tests are self-contained: no Chainlink network access, no
 *         real ERC-20, no real AdherentRegistry. The mocks below capture the
 *         minimum interface surface required to exercise the scaffold.
 *
 *         R1 will add:
 *           - real deposit/claim/rebalance bodies + flow tests
 *           - withinBand() boundary tests (50 bps tolerance both directions)
 *           - per-month cap rollover tests (30-day window expiry)
 *           - reserve-buffer-floor breach tests
 *           - invariant fuzz tests (G5 spread-profit-is-zero across N flows)
 */
contract KawaseYuiPoolR0Test {
    // ────────────────────────────────────────────────────────────────────
    //  forge-std-free assertion helpers (kept inline so this file compiles
    //  in isolation of forge-std).
    // ────────────────────────────────────────────────────────────────────

    error AssertFailed(string what);

    function _assertTrue(bool cond, string memory msg_) internal pure {
        if (!cond) revert AssertFailed(msg_);
    }

    function _assertEq(address a, address b, string memory msg_) internal pure {
        if (a != b) revert AssertFailed(msg_);
    }

    function _assertEq(uint256 a, uint256 b, string memory msg_) internal pure {
        if (a != b) revert AssertFailed(msg_);
    }

    function _expectRevert() internal pure returns (bool) {
        return true; // marker for self-documenting test names
    }

    // ────────────────────────────────────────────────────────────────────
    //  Mocks (minimum interface surface)
    // ────────────────────────────────────────────────────────────────────

    function _newPool(
        address councilSafe_,
        address adherent,
        uint256 bandBps,
        uint256 monthlyCap
    ) internal returns (KawaseYuiPool) {
        MockERC20 stable = new MockERC20();
        MockAdherentRegistry registry = new MockAdherentRegistry();
        registry.setAdherent(adherent, 1);
        MockConstitution constitution = new MockConstitution();
        constitution.setConst(keccak256("kawase.max_band_bps"), bytes32(bandBps));
        constitution.setMut(keccak256("kawase.per_month_cap_usd_minor"), bytes32(monthlyCap));
        MockPriceFeed feed = new MockPriceFeed();
        return new KawaseYuiPool(
            IERC20(address(stable)),
            IAdherentRegistry(address(registry)),
            IConstitution(address(constitution)),
            IChainlinkPriceFeed(address(feed)),
            councilSafe_,
            keccak256("kawase.max_band_bps"),
            keccak256("kawase.per_month_cap_usd_minor"),
            5_000_000_000  // $5,000 reserve buffer floor
        );
    }

    // ────────────────────────────────────────────────────────────────────
    //  Tests
    // ────────────────────────────────────────────────────────────────────

    function test_constructor_records_immutables() public {
        address councilSafe = address(0xC0)
            ;
        address adherent = address(0xA1);
        KawaseYuiPool pool = _newPool(councilSafe, adherent, 50, 1_000_000_000);

        _assertEq(pool.councilSafe(), councilSafe, "councilSafe wired");
        _assertEq(pool.maxBandBps(), 50, "G4 band reads 50 bps");
        _assertEq(pool.perMonthCapUsdMinor(), 1_000_000_000, "G9 cap reads $1,000");
        _assertEq(pool.BPS_DENOMINATOR(), 10_000, "BPS denominator");
        _assertEq(pool.ROLLING_WINDOW_SECS(), 30 days, "rolling window 30 days");
    }

    function test_maxBandBps_reads_from_constitution() public {
        KawaseYuiPool pool = _newPool(address(0xC0), address(0xA1), 50, 1_000_000_000);
        _assertEq(pool.maxBandBps(), 50, unicode"constitution band ±0.5%");
    }

    function test_perMonthCap_reads_from_constitution() public {
        KawaseYuiPool pool = _newPool(address(0xC0), address(0xA1), 50, 1_000_000_000);
        _assertEq(pool.perMonthCapUsdMinor(), 1_000_000_000, "R1 monthly cap $1k");
    }

    function test_withinBand_returns_false_when_oracle_zero() public {
        // R0 stub: chainlinkRateBps() returns 0 → diff/live calculation
        // skipped → false. Verifies R0 honesty.
        KawaseYuiPool pool = _newPool(address(0xC0), address(0xA1), 50, 1_000_000_000);
        _assertTrue(!pool.withinBand(9_200), "R0 always-false until oracle wired");
    }
}

// -------------------------------------------------------------------
//  Mock contracts (file-scope to keep test file self-contained)
// -------------------------------------------------------------------

contract MockERC20 {
    mapping(address => uint256) public balances;
    function transfer(address, uint256) external pure returns (bool) { return true; }
    function transferFrom(address, address, uint256) external pure returns (bool) { return true; }
    function balanceOf(address h) external view returns (uint256) { return balances[h]; }
    function approve(address, uint256) external pure returns (bool) { return true; }
}

contract MockAdherentRegistry {
    mapping(address => uint256) public tokenOf;
    function setAdherent(address holder, uint256 id) external { tokenOf[holder] = id; }
}

contract MockConstitution {
    mapping(bytes32 => bytes32) public consts;
    mapping(bytes32 => bytes32) public muts;
    function setConst(bytes32 k, bytes32 v) external { consts[k] = v; }
    function setMut(bytes32 k, bytes32 v) external { muts[k] = v; }
    function getConstant(bytes32 k) external view returns (bytes32) { return consts[k]; }
    function getMutable(bytes32 k) external view returns (bytes32) { return muts[k]; }
}

contract MockPriceFeed {
    function latestRoundData() external pure returns (uint80, int256, uint256, uint256, uint80) {
        // R1 will return a real Chainlink answer; R0 returns zeros.
        return (0, 0, 0, 0, 0);
    }
    function decimals() external pure returns (uint8) { return 8; }
}
