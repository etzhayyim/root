// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {GCCStablecoin} from "../src/GCCStablecoin.sol";
import {ClaimStakeEscrow} from "../src/ClaimStakeEscrow.sol";

/// @title  StakedClaimE2ETest
/// @notice End-to-end forge tests for the ADR-2604261717 staked-claim
///         mechanism: postClaim → challenge → settle / claimUnchallenged /
///         noShow. Each test deploys a fresh GCC + escrow, funds the
///         participants, and verifies the GCC accounting matches the
///         85/10/5 split spec.
///
/// @dev    Contract source is the truth; this suite catches drift between
///         the inline split percentages, the OZ ECDSA recovery shape, and
///         the on-chain payout math the off-chain settler / yoro UI rely
///         on. Run before any `MIGRATE_LIVE=true` Phase 3 hardening to
///         confirm the contract still behaves as the integration
///         expects.
contract StakedClaimE2ETest is Test {
    GCCStablecoin internal gcc;
    ClaimStakeEscrow internal escrow;

    address constant OWNER     = address(0xA11CE);
    address constant TREASURY  = address(0xC0FFEE);
    address constant REWARD    = address(0xFEED);

    // arbiter is an EOA (so we can vm.sign on its behalf).
    uint256 internal arbiterPk = 0xA1B17E1;
    address internal arbiter;

    // claimant + challenger get GCC, post bonds.
    uint256 internal claimantPk   = 0xC141A11;
    uint256 internal challengerPk = 0xCB411E11;
    address internal claimant;
    address internal challenger;

    bytes32 constant CLAIM_ID         = keccak256("e2e-claim-1");
    bytes32 constant CLAIMANT_DID     = keccak256("did:web:claimant.etzhayyim.com");
    bytes32 constant CHALLENGER_DID   = keccak256("did:web:challenger.etzhayyim.com");
    bytes32 constant AT_RECORD_CID    = keccak256("at://record/1");
    uint256 constant BOND             = 1 ether;
    uint256 constant COUNTER_BOND     = 1 ether; // 100% of bond — well above 50% min

    function setUp() public {
        arbiter    = vm.addr(arbiterPk);
        claimant   = vm.addr(claimantPk);
        challenger = vm.addr(challengerPk);

        // Deploy GCC. supplyCap = 1B * 1e18 mirrors the live contract.
        vm.prank(OWNER);
        gcc = new GCCStablecoin(
            "etzhayyim Credit",
            "GCC",
            18,
            1_000_000_000 ether,
            OWNER,        // owner
            OWNER,        // masterMinter
            OWNER,        // pauser
            OWNER         // blacklister
        );

        // OWNER opens its own minter slot, then mints to the participants.
        vm.startPrank(OWNER);
        gcc.configureMinter(OWNER, 100 ether);
        gcc.mint(claimant,   10 ether);
        gcc.mint(challenger, 10 ether);
        vm.stopPrank();

        // Deploy escrow with arbiter = our test EOA so we can sign settle().
        escrow = new ClaimStakeEscrow(IERC20(address(gcc)), arbiter, TREASURY, REWARD, OWNER);

        // Pre-approve the escrow from both participants so postClaim /
        // challenge can transferFrom without separate approvals per call.
        vm.prank(claimant);
        gcc.approve(address(escrow), type(uint256).max);
        vm.prank(challenger);
        gcc.approve(address(escrow), type(uint256).max);
    }

    // ── Path A: unchallenged → claimant gets bond back ─────────────────────

    function test_pathA_claimUnchallenged_refundsBond() public {
        uint256 claimantBalanceBefore = gcc.balanceOf(claimant);

        vm.prank(claimant);
        escrow.postClaim(CLAIM_ID, CLAIMANT_DID, AT_RECORD_CID, BOND, 7 days);

        assertEq(gcc.balanceOf(claimant), claimantBalanceBefore - BOND, "bond not deducted");

        // Fast-forward past the challenge window.
        vm.warp(block.timestamp + 7 days + 1);

        escrow.claimUnchallenged(CLAIM_ID);

        assertEq(gcc.balanceOf(claimant), claimantBalanceBefore, "bond not refunded");
        assertEq(uint256(escrow.claims(CLAIM_ID).state), uint256(ClaimStakeEscrow.State.Refunded));
    }

    function test_pathA_claimUnchallenged_revertsBeforeWindowCloses() public {
        vm.prank(claimant);
        escrow.postClaim(CLAIM_ID, CLAIMANT_DID, AT_RECORD_CID, BOND, 7 days);

        // Window still open — refund must revert.
        vm.expectRevert(ClaimStakeEscrow.ChallengeWindowOpen.selector);
        escrow.claimUnchallenged(CLAIM_ID);
    }

    // ── Path B: challenged → arbiter signs settle ──────────────────────────

    function test_pathB_settle_upheld_payoutSplit() public {
        vm.prank(claimant);
        escrow.postClaim(CLAIM_ID, CLAIMANT_DID, AT_RECORD_CID, BOND, 7 days);
        vm.prank(challenger);
        escrow.challenge(CLAIM_ID, CHALLENGER_DID, COUNTER_BOND);

        bytes memory sig = _signSettle(CLAIM_ID, true);

        uint256 claimantBefore  = gcc.balanceOf(claimant);
        uint256 treasuryBefore  = gcc.balanceOf(TREASURY);
        uint256 rewardBefore    = gcc.balanceOf(REWARD);

        escrow.settle(CLAIM_ID, true, sig);

        // claimWins: claimant gets bond + 85% of counter; treasury 10%; reward 5% of counter.
        uint256 winnerSlice   = (COUNTER_BOND * 8500) / 10_000;
        uint256 treasurySlice = (COUNTER_BOND * 1000) / 10_000;
        uint256 rewardSlice   = COUNTER_BOND - winnerSlice - treasurySlice;

        assertEq(gcc.balanceOf(claimant) - claimantBefore, BOND + winnerSlice, "claimant payout");
        assertEq(gcc.balanceOf(TREASURY) - treasuryBefore, treasurySlice,      "treasury slice");
        assertEq(gcc.balanceOf(REWARD)   - rewardBefore,   rewardSlice,        "reward slice");
        assertEq(uint256(escrow.claims(CLAIM_ID).state), uint256(ClaimStakeEscrow.State.Upheld));
    }

    function test_pathB_settle_slashed_payoutSplit() public {
        vm.prank(claimant);
        escrow.postClaim(CLAIM_ID, CLAIMANT_DID, AT_RECORD_CID, BOND, 7 days);
        vm.prank(challenger);
        escrow.challenge(CLAIM_ID, CHALLENGER_DID, COUNTER_BOND);

        bytes memory sig = _signSettle(CLAIM_ID, false);

        uint256 challengerBefore = gcc.balanceOf(challenger);
        uint256 treasuryBefore   = gcc.balanceOf(TREASURY);
        uint256 rewardBefore     = gcc.balanceOf(REWARD);

        escrow.settle(CLAIM_ID, false, sig);

        // claimSlashed: challenger gets counter + 85% of bond; treasury 10%; reward 5% of bond.
        uint256 winnerSlice   = (BOND * 8500) / 10_000;
        uint256 treasurySlice = (BOND * 1000) / 10_000;
        uint256 rewardSlice   = BOND - winnerSlice - treasurySlice;

        assertEq(gcc.balanceOf(challenger) - challengerBefore, COUNTER_BOND + winnerSlice, "challenger payout");
        assertEq(gcc.balanceOf(TREASURY)   - treasuryBefore,   treasurySlice,              "treasury slice");
        assertEq(gcc.balanceOf(REWARD)     - rewardBefore,     rewardSlice,                "reward slice");
        assertEq(uint256(escrow.claims(CLAIM_ID).state), uint256(ClaimStakeEscrow.State.Slashed));
    }

    function test_pathB_settle_revertsOnInvalidSignature() public {
        vm.prank(claimant);
        escrow.postClaim(CLAIM_ID, CLAIMANT_DID, AT_RECORD_CID, BOND, 7 days);
        vm.prank(challenger);
        escrow.challenge(CLAIM_ID, CHALLENGER_DID, COUNTER_BOND);

        // Sign with a wrong key → escrow's ECDSA recover yields wrong addr.
        uint256 wrongPk = 0xDEADBEEF;
        bytes memory sig = _signSettleWith(wrongPk, CLAIM_ID, true);

        vm.expectRevert(ClaimStakeEscrow.InvalidArbiterSignature.selector);
        escrow.settle(CLAIM_ID, true, sig);
    }

    function test_pathB_challenge_revertsBelowMinCounterBond() public {
        vm.prank(claimant);
        escrow.postClaim(CLAIM_ID, CLAIMANT_DID, AT_RECORD_CID, BOND, 7 days);

        // 49% — under the 50% floor.
        uint256 tooLow = (BOND * 49) / 100;
        vm.prank(challenger);
        vm.expectRevert(ClaimStakeEscrow.CounterBondTooSmall.selector);
        escrow.challenge(CLAIM_ID, CHALLENGER_DID, tooLow);
    }

    // ── Path C: arbiter no-show → both refunded ────────────────────────────

    function test_pathC_noShow_refundsBothSides() public {
        vm.prank(claimant);
        escrow.postClaim(CLAIM_ID, CLAIMANT_DID, AT_RECORD_CID, BOND, 7 days);
        vm.prank(challenger);
        escrow.challenge(CLAIM_ID, CHALLENGER_DID, COUNTER_BOND);

        uint256 claimantBalance   = gcc.balanceOf(claimant);
        uint256 challengerBalance = gcc.balanceOf(challenger);
        uint256 treasuryBalance   = gcc.balanceOf(TREASURY);

        // Arbiter timeout = 14 days.
        vm.warp(block.timestamp + 14 days + 1);

        escrow.noShow(CLAIM_ID);

        assertEq(gcc.balanceOf(claimant)   - claimantBalance,   BOND,         "claimant refund");
        assertEq(gcc.balanceOf(challenger) - challengerBalance, COUNTER_BOND, "challenger refund");
        assertEq(gcc.balanceOf(TREASURY),                       treasuryBalance, "treasury untouched");
        assertEq(uint256(escrow.claims(CLAIM_ID).state), uint256(ClaimStakeEscrow.State.Refunded));
    }

    function test_pathC_noShow_revertsBeforeArbiterTimeout() public {
        vm.prank(claimant);
        escrow.postClaim(CLAIM_ID, CLAIMANT_DID, AT_RECORD_CID, BOND, 7 days);
        vm.prank(challenger);
        escrow.challenge(CLAIM_ID, CHALLENGER_DID, COUNTER_BOND);

        // Only 13 days in — arbiter still has time.
        vm.warp(block.timestamp + 13 days);
        vm.expectRevert(ClaimStakeEscrow.ArbiterStillResponsive.selector);
        escrow.noShow(CLAIM_ID);
    }

    // ── Sealer-funded settler path (msg.sender ≠ arbiter, sig still valid) ─

    function test_settle_canBeBroadcastByThirdParty() public {
        vm.prank(claimant);
        escrow.postClaim(CLAIM_ID, CLAIMANT_DID, AT_RECORD_CID, BOND, 7 days);
        vm.prank(challenger);
        escrow.challenge(CLAIM_ID, CHALLENGER_DID, COUNTER_BOND);

        bytes memory sig = _signSettle(CLAIM_ID, true);

        // The settler bot in production calls this with sealer's tx, not
        // the arbiter's. ECDSA.recover only checks the signature shape, so
        // a third-party broadcaster should work — verify here.
        address broadcaster = address(0xBA7);
        vm.prank(broadcaster);
        escrow.settle(CLAIM_ID, true, sig);

        assertEq(uint256(escrow.claims(CLAIM_ID).state), uint256(ClaimStakeEscrow.State.Upheld));
    }

    // ── ERC-1271 contract-arbiter path (Safe multisig) ────────────────────

    /// Deploy a fresh escrow with a mock ERC-1271 arbiter contract and verify
    /// that settle() accepts isValidSignature() returning the magic value.
    function test_pathB_settle_erc1271Arbiter_upheld() public {
        // Minimal stub — `vm.mockCall` overrides the selector we care about.
        address mockArbiter = address(0xE1271);
        vm.etch(mockArbiter, hex"6080604052");

        ClaimStakeEscrow e = new ClaimStakeEscrow(
            IERC20(address(gcc)), mockArbiter, TREASURY, REWARD, address(this)
        );
        vm.prank(claimant);   gcc.approve(address(e), type(uint256).max);
        vm.prank(challenger); gcc.approve(address(e), type(uint256).max);

        vm.prank(claimant);
        e.postClaim(CLAIM_ID, CLAIMANT_DID, AT_RECORD_CID, BOND, 7 days);
        vm.prank(challenger);
        e.challenge(CLAIM_ID, CHALLENGER_DID, COUNTER_BOND);

        bytes32 payloadHash = keccak256(abi.encode(CLAIM_ID, true, address(e), block.chainid));
        bytes memory fakeSig = hex"aabbccdd"; // arbitrary bytes; ECDSA path won't match

        // isValidSignature(payloadHash, fakeSig) → magic value
        vm.mockCall(
            mockArbiter,
            abi.encodeWithSignature("isValidSignature(bytes32,bytes)", payloadHash, fakeSig),
            abi.encode(bytes4(0x1626ba7e))
        );

        e.settle(CLAIM_ID, true, fakeSig);
        assertEq(uint256(e.claims(CLAIM_ID).state), uint256(ClaimStakeEscrow.State.Upheld));
    }

    /// ERC-1271 arbiter returns wrong magic → settle must revert.
    function test_pathB_settle_erc1271Arbiter_revertsOnBadMagic() public {
        address mockArbiter = address(0xE1272);
        vm.etch(mockArbiter, hex"6080604052");

        ClaimStakeEscrow e = new ClaimStakeEscrow(
            IERC20(address(gcc)), mockArbiter, TREASURY, REWARD, address(this)
        );
        vm.prank(claimant);   gcc.approve(address(e), type(uint256).max);
        vm.prank(challenger); gcc.approve(address(e), type(uint256).max);

        vm.prank(claimant);
        e.postClaim(CLAIM_ID, CLAIMANT_DID, AT_RECORD_CID, BOND, 7 days);
        vm.prank(challenger);
        e.challenge(CLAIM_ID, CHALLENGER_DID, COUNTER_BOND);

        bytes32 payloadHash = keccak256(abi.encode(CLAIM_ID, true, address(e), block.chainid));
        bytes memory fakeSig = hex"aabbccdd";

        // Returns wrong magic → signature invalid.
        vm.mockCall(
            mockArbiter,
            abi.encodeWithSignature("isValidSignature(bytes32,bytes)", payloadHash, fakeSig),
            abi.encode(bytes4(0xdeadbeef))
        );

        vm.expectRevert(ClaimStakeEscrow.InvalidArbiterSignature.selector);
        e.settle(CLAIM_ID, true, fakeSig);
    }

    // ── helpers ────────────────────────────────────────────────────────────

    function _signSettle(bytes32 claimId, bool claimWins) internal view returns (bytes memory) {
        return _signSettleWith(arbiterPk, claimId, claimWins);
    }

    /// Mirrors the script's wire-format: keccak256(abi.encode(claimId,
    /// claimWins, escrow, chainid)) wrapped in eth_signedMessage prefix.
    function _signSettleWith(uint256 pk, bytes32 claimId, bool claimWins) internal view returns (bytes memory) {
        bytes32 payloadHash = keccak256(abi.encode(claimId, claimWins, address(escrow), block.chainid));
        bytes32 ethSignedHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", payloadHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, ethSignedHash);
        return abi.encodePacked(r, s, v);
    }
}
