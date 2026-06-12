// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.23;

import {Test} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {GCCStablecoin} from "../src/GCCStablecoin.sol";
import {
    MishmarBondEscrow,
    IAdherentSBT,
    ICharterComplianceRegistry
} from "../src/MishmarBondEscrow.sol";

/// Minimal Adherent-SBT mock: balanceOf > 0 == covenant member.
contract MockSBT {
    mapping(address => uint256) public bal;
    function setMember(address a, bool m) external {
        bal[a] = m ? 1 : 0;
    }
    function balanceOf(address o) external view returns (uint256) {
        return bal[o];
    }
}

/// Minimal Charter-compliance-registry mock.
contract MockCharter {
    mapping(address => bool) public nonAligned;
    function setNonAligned(address a, bool v) external {
        nonAligned[a] = v;
    }
    function isNonAlignedAddress(address s) external view returns (bool) {
        return nonAligned[s];
    }
}

/// @title  MishmarBondEscrowTest
/// @notice Forge tests for ADR-2606082100 Mishmar Storage Covenant: postPin →
///         (witness) challenge → proveAvailability (≥K-of-N quorum) → slash /
///         release / yobelRelease, plus the SBT + Charter gates. Mirrors the
///         StakedClaimE2E pattern (fresh GCC + escrow, GCC accounting asserted).
///
/// @dev    Verifies the Charter-critical money paths: NO yield (release returns
///         exactly the bond), slash → commons 90/10 (NOTHING to individuals), and
///         the K-of-N witness-signature gate.
contract MishmarBondEscrowTest is Test {
    GCCStablecoin internal gcc;
    MishmarBondEscrow internal escrow;
    MockSBT internal sbt;
    MockCharter internal charter;

    address constant OWNER = address(0xA11CE);
    address constant RETAINER = address(0x8EEF); // commons retainer pool
    address constant PUBLIC_FUND = address(0xF00D); // Public Fund Safe

    uint256 internal pinnerPk;
    address internal pinner;

    // 5 witnesses; default quorum threshold = 3.
    uint256[5] internal witnessPk;
    address[5] internal witness;

    bytes32 constant PIN_ID = keccak256("pin-1");
    bytes32 constant ROOT_CID = keccak256("root-1");
    bytes32 constant DID_HASH = keccak256("did:web:pinner.etzhayyim.com");
    bytes32 constant NONCE = keccak256("challenge-nonce-1");
    uint256 constant BOND = 1 ether;
    uint64 constant DURATION_EPOCHS = 7; // 7 * EPOCH(1 day)

    function setUp() public {
        pinnerPk = 0xC0FFEE01;
        pinner = vm.addr(pinnerPk);
        for (uint256 i = 0; i < 5; i++) {
            witnessPk[i] = 0xBEEF00 + i; // 5 distinct secp256k1 scalars
            witness[i] = vm.addr(witnessPk[i]);
        }

        vm.prank(OWNER);
        gcc = new GCCStablecoin(
            "etzhayyim Credit", "GCC", 18, 1_000_000_000 ether,
            OWNER, OWNER, OWNER, OWNER
        );
        vm.startPrank(OWNER);
        gcc.configureMinter(OWNER, 100 ether);
        gcc.mint(pinner, 10 ether);
        vm.stopPrank();

        sbt = new MockSBT();
        charter = new MockCharter();
        sbt.setMember(pinner, true); // pinner is a covenant member

        escrow = new MishmarBondEscrow(
            IERC20(address(gcc)),
            IAdherentSBT(address(sbt)),
            ICharterComplianceRegistry(address(charter)),
            RETAINER,
            PUBLIC_FUND,
            OWNER
        );

        // register the 5 witnesses (owner-only).
        vm.startPrank(OWNER);
        for (uint256 i = 0; i < 5; i++) {
            escrow.setWitness(witness[i], true);
        }
        vm.stopPrank();

        vm.prank(pinner);
        gcc.approve(address(escrow), type(uint256).max);
    }

    function _postPin() internal {
        vm.prank(pinner);
        escrow.postPin(PIN_ID, ROOT_CID, DID_HASH, BOND, DURATION_EPOCHS);
    }

    // witness sig over keccak256(pinId, nonce, escrow, chainid), eth-signed.
    function _signProof(uint256 pk) internal view returns (bytes memory) {
        bytes32 payload = keccak256(abi.encode(PIN_ID, NONCE, address(escrow), block.chainid));
        bytes32 ethHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", payload));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, ethHash);
        return abi.encodePacked(r, s, v);
    }

    // a valid 3-of-5 quorum (witnesses 0,1,2).
    function _quorum3() internal view returns (address[] memory signers, bytes[] memory sigs) {
        signers = new address[](3);
        sigs = new bytes[](3);
        for (uint256 i = 0; i < 3; i++) {
            signers[i] = witness[i];
            sigs[i] = _signProof(witnessPk[i]);
        }
    }

    // ── postPin + gates ────────────────────────────────────────────────────

    function test_postPin_locksBond_andSetsPinned() public {
        uint256 before = gcc.balanceOf(pinner);
        _postPin();
        assertEq(gcc.balanceOf(pinner), before - BOND, "bond not locked");
        assertEq(gcc.balanceOf(address(escrow)), BOND, "escrow did not receive bond");
        assertEq(uint256(escrow.pins(PIN_ID).state), uint256(MishmarBondEscrow.State.Pinned));
        assertEq(escrow.pins(PIN_ID).pinner, pinner);
    }

    function test_postPin_revertsForNonMember() public {
        sbt.setMember(pinner, false);
        vm.prank(pinner);
        vm.expectRevert(MishmarBondEscrow.NotMember.selector);
        escrow.postPin(PIN_ID, ROOT_CID, DID_HASH, BOND, DURATION_EPOCHS);
    }

    function test_postPin_revertsForCharterNonCompliant() public {
        charter.setNonAligned(pinner, true);
        vm.prank(pinner);
        vm.expectRevert(MishmarBondEscrow.CharterNonCompliant.selector);
        escrow.postPin(PIN_ID, ROOT_CID, DID_HASH, BOND, DURATION_EPOCHS);
    }

    function test_postPin_revertsBelowMinBond() public {
        vm.prank(pinner);
        vm.expectRevert(MishmarBondEscrow.BondTooSmall.selector);
        escrow.postPin(PIN_ID, ROOT_CID, DID_HASH, 0.5 ether, DURATION_EPOCHS);
    }

    // ── release: full refund, NO yield (anti-usury) ──────────────────────────

    function test_release_refundsExactBond_noYield() public {
        uint256 before = gcc.balanceOf(pinner);
        _postPin();
        vm.warp(block.timestamp + uint256(DURATION_EPOCHS) * 1 days + 1);
        escrow.release(PIN_ID);
        assertEq(gcc.balanceOf(pinner), before, "release must return EXACTLY the bond (no interest)");
        assertEq(uint256(escrow.pins(PIN_ID).state), uint256(MishmarBondEscrow.State.Released));
    }

    function test_release_revertsBeforeExpiry() public {
        _postPin();
        vm.expectRevert(MishmarBondEscrow.NotExpired.selector);
        escrow.release(PIN_ID);
    }

    // ── challenge: witness-gated ──────────────────────────────────────────────

    function test_challenge_byWitness_setsChallenged() public {
        _postPin();
        vm.prank(witness[0]);
        escrow.challenge(PIN_ID, NONCE);
        assertEq(uint256(escrow.pins(PIN_ID).state), uint256(MishmarBondEscrow.State.Challenged));
    }

    function test_challenge_byNonWitness_reverts() public {
        _postPin();
        vm.prank(pinner); // not a registered witness
        vm.expectRevert(MishmarBondEscrow.NotWitness.selector);
        escrow.challenge(PIN_ID, NONCE);
    }

    // ── proveAvailability: K-of-N quorum ──────────────────────────────────────

    function test_proveAvailability_quorumMet_returnsToPinned() public {
        _postPin();
        vm.prank(witness[0]);
        escrow.challenge(PIN_ID, NONCE);
        (address[] memory signers, bytes[] memory sigs) = _quorum3();
        escrow.proveAvailability(PIN_ID, signers, sigs);
        assertEq(uint256(escrow.pins(PIN_ID).state), uint256(MishmarBondEscrow.State.Pinned));
    }

    function test_proveAvailability_belowThreshold_reverts() public {
        _postPin();
        vm.prank(witness[0]);
        escrow.challenge(PIN_ID, NONCE);
        // only 2 sigs (< threshold 3)
        address[] memory signers = new address[](2);
        bytes[] memory sigs = new bytes[](2);
        for (uint256 i = 0; i < 2; i++) {
            signers[i] = witness[i];
            sigs[i] = _signProof(witnessPk[i]);
        }
        vm.expectRevert(MishmarBondEscrow.QuorumNotMet.selector);
        escrow.proveAvailability(PIN_ID, signers, sigs);
    }

    function test_proveAvailability_duplicateSigner_reverts() public {
        _postPin();
        vm.prank(witness[0]);
        escrow.challenge(PIN_ID, NONCE);
        address[] memory signers = new address[](3);
        bytes[] memory sigs = new bytes[](3);
        signers[0] = witness[0];
        sigs[0] = _signProof(witnessPk[0]);
        signers[1] = witness[1];
        sigs[1] = _signProof(witnessPk[1]);
        signers[2] = witness[0]; // duplicate
        sigs[2] = _signProof(witnessPk[0]);
        vm.expectRevert(MishmarBondEscrow.DuplicateSigner.selector);
        escrow.proveAvailability(PIN_ID, signers, sigs);
    }

    function test_proveAvailability_nonWitnessSigner_reverts() public {
        _postPin();
        vm.prank(witness[0]);
        escrow.challenge(PIN_ID, NONCE);
        address[] memory signers = new address[](3);
        bytes[] memory sigs = new bytes[](3);
        signers[0] = witness[0];
        sigs[0] = _signProof(witnessPk[0]);
        signers[1] = witness[1];
        sigs[1] = _signProof(witnessPk[1]);
        signers[2] = pinner; // not a registered witness
        sigs[2] = _signProof(pinnerPk);
        vm.expectRevert(MishmarBondEscrow.SignerNotWitness.selector);
        escrow.proveAvailability(PIN_ID, signers, sigs);
    }

    function test_proveAvailability_afterWindowClosed_reverts() public {
        _postPin();
        vm.prank(witness[0]);
        escrow.challenge(PIN_ID, NONCE);
        vm.warp(block.timestamp + 1 days + 1); // past proofWindow
        (address[] memory signers, bytes[] memory sigs) = _quorum3();
        vm.expectRevert(MishmarBondEscrow.ProofWindowClosed.selector);
        escrow.proveAvailability(PIN_ID, signers, sigs);
    }

    // ── slash: bond → commons 90/10, NOTHING to individuals ──────────────────

    function test_slash_splitsBondToCommons_9010() public {
        _postPin();
        vm.prank(witness[0]);
        escrow.challenge(PIN_ID, NONCE);
        vm.warp(block.timestamp + 1 days + 1); // proof window elapsed, no proof
        escrow.slash(PIN_ID);

        assertEq(gcc.balanceOf(RETAINER), 0.9 ether, "90% to retainer pool");
        assertEq(gcc.balanceOf(PUBLIC_FUND), 0.1 ether, "10% tithe to Public Fund");
        assertEq(gcc.balanceOf(address(escrow)), 0, "escrow fully drained");
        assertEq(uint256(escrow.pins(PIN_ID).state), uint256(MishmarBondEscrow.State.Slashed));
    }

    function test_slash_revertsWhileProofWindowOpen() public {
        _postPin();
        vm.prank(witness[0]);
        escrow.challenge(PIN_ID, NONCE);
        // window still open
        vm.expectRevert(MishmarBondEscrow.ProofWindowOpen.selector);
        escrow.slash(PIN_ID);
    }

    // ── yobelRelease: jubilee forgiveness ────────────────────────────────────

    function test_yobelRelease_byOwner_refundsAndForgives() public {
        uint256 before = gcc.balanceOf(pinner);
        _postPin();
        vm.prank(OWNER);
        escrow.yobelRelease(PIN_ID);
        assertEq(gcc.balanceOf(pinner), before, "yobel returns the bond in full");
        assertEq(uint256(escrow.pins(PIN_ID).state), uint256(MishmarBondEscrow.State.Forgiven));
    }

    function test_yobelRelease_byStranger_reverts() public {
        _postPin();
        vm.prank(pinner);
        vm.expectRevert(MishmarBondEscrow.NotYobel.selector);
        escrow.yobelRelease(PIN_ID);
    }
}
