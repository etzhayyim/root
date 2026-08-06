// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {ECDSA} from "../src/utils/ECDSA.sol";
import {EIP712} from "../src/utils/EIP712.sol";
import {
    ForceAuthorization,
    IAdherentRegistry as FA_IAdh,
    IChartersComplianceRegistry as FA_ICCR
} from "../src/ForceAuthorization.sol";

contract MockFAAdherent is FA_IAdh {
    mapping(address => uint256) private _tokenOf;
    mapping(uint256 => bool) private _active;
    uint256 public override totalMinted;
    function setToken(address holder, uint256 tokenId) external {
        _tokenOf[holder] = tokenId;
        _active[tokenId] = true;
        if (tokenId > totalMinted) totalMinted = tokenId;
    }
    function tokenOf(address h) external view override returns (uint256) { return _tokenOf[h]; }
    function isActive(uint256 tokenId, uint64) external view override returns (bool) { return _active[tokenId]; }
}

contract MockFACharters is FA_ICCR {
    mapping(address => bool) public override isCouncilMember;
    mapping(uint256 => bool) public override isNonAlignedTokenId;
    function setCouncil(address a, bool b) external { isCouncilMember[a] = b; }
    function setNonAlignedToken(uint256 id, bool b) external { isNonAlignedTokenId[id] = b; }
}

contract ForceAuthorizationTest is Test {
    using ECDSA for bytes32;

    ForceAuthorization fa;
    MockFAAdherent adh;
    MockFACharters chs;

    address constant ALICE = address(0xA11CE);
    address constant BOB = address(0xB0B);
    address constant CAROL = address(0xCA401);
    address constant DAVE = address(0xDA1E);
    address constant EVE = address(0xE7E);
    address constant FRANK = address(0xF4ABC);
    address constant GUS = address(0x6045);

    // Council private keys and their derived addresses
    uint256 constant COUNCIL_1_PK = 0x1111111111111111111111111111111111111111111111111111111111111111;
    uint256 constant COUNCIL_2_PK = 0x2222222222222222222222222222222222222222222222222222222222222222;
    uint256 constant COUNCIL_3_PK = 0x3333333333333333333333333333333333333333333333333333333333333333;

    address COUNCIL_1;
    address COUNCIL_2;
    address COUNCIL_3;

    bytes32 constant PROPOSAL_CID = keccak256("ipfs://Qm...proposal");
    bytes32 constant INTENDED_USE_LAND_DEFENSE = keccak256("defense-of-land");

    function setUp() public {
        COUNCIL_1 = vm.addr(COUNCIL_1_PK);
        COUNCIL_2 = vm.addr(COUNCIL_2_PK);
        COUNCIL_3 = vm.addr(COUNCIL_3_PK);

        adh = new MockFAAdherent();
        chs = new MockFACharters();
        fa = new ForceAuthorization(adh, chs);

        // 10 SBT holders — quorum 50% = 5 votes
        adh.setToken(ALICE, 1);
        adh.setToken(BOB, 2);
        adh.setToken(CAROL, 3);
        adh.setToken(DAVE, 4);
        adh.setToken(EVE, 5);
        adh.setToken(FRANK, 6);
        adh.setToken(GUS, 7);
        for (uint256 i = 8; i <= 10; i++) {
            adh.setToken(address(uint160(0x10000 + i)), i);
        }

        chs.setCouncil(COUNCIL_1, true);
        chs.setCouncil(COUNCIL_2, true);
        chs.setCouncil(COUNCIL_3, true);
    }

    function _proposeNormal() internal returns (bytes32) {
        bytes[] memory emptySigs = new bytes[](0);
        address[] memory emptySigners = new address[](0);
        vm.prank(ALICE);
        return fa.propose(PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, false, emptySigs, emptySigners, 0);
    }

    function _signUsingContractDigest(bytes32 digest, uint256 pk) internal view returns (bytes memory) {
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, digest);
        return abi.encodePacked(r, s, v);
    }

    function _councilSigsEmergencyPropose(
        address proposer,
        bytes32 proposalCid,
        bytes32 intendedUseHash,
        uint256 nonce
    ) internal view returns (bytes[] memory sigs, address[] memory signers) {
        signers = new address[](3);
        signers[0] = COUNCIL_1; signers[1] = COUNCIL_2; signers[2] = COUNCIL_3;
        sigs = new bytes[](3);
        bytes32 digest = fa.computeEmergencyProposeDigest(proposer, proposalCid, intendedUseHash, nonce);
        sigs[0] = _signUsingContractDigest(digest, COUNCIL_1_PK);
        sigs[1] = _signUsingContractDigest(digest, COUNCIL_2_PK);
        sigs[2] = _signUsingContractDigest(digest, COUNCIL_3_PK);
    }

    function _councilSigsAfterAction(bytes32 authId, bytes32 afterActionCid)
        internal view returns (bytes[] memory sigs, address[] memory signers)
    {
        signers = new address[](3);
        signers[0] = COUNCIL_1; signers[1] = COUNCIL_2; signers[2] = COUNCIL_3;
        sigs = new bytes[](3);
        bytes32 digest = fa.computeAfterActionDigest(authId, afterActionCid);
        sigs[0] = _signUsingContractDigest(digest, COUNCIL_1_PK);
        sigs[1] = _signUsingContractDigest(digest, COUNCIL_2_PK);
        sigs[2] = _signUsingContractDigest(digest, COUNCIL_3_PK);
    }

    function _councilSigsCancel(bytes32 authId, bytes32 reasonCid)
        internal view returns (bytes[] memory sigs, address[] memory signers)
    {
        signers = new address[](3);
        signers[0] = COUNCIL_1; signers[1] = COUNCIL_2; signers[2] = COUNCIL_3;
        sigs = new bytes[](3);
        bytes32 digest = fa.computeCancelDigest(authId, reasonCid);
        sigs[0] = _signUsingContractDigest(digest, COUNCIL_1_PK);
        sigs[1] = _signUsingContractDigest(digest, COUNCIL_2_PK);
        sigs[2] = _signUsingContractDigest(digest, COUNCIL_3_PK);
    }

    function test_propose_normal_72h_voting() public {
        bytes32 id = _proposeNormal();
        (address proposer,, , bool emergency, ,
         uint64 votingDeadline,
         ForceAuthorization.AuthState state,,, ,,) = fa.authorizations(id);
        assertEq(proposer, ALICE);
        assertFalse(emergency);
        assertEq(uint8(state), uint8(ForceAuthorization.AuthState.Active));
        assertEq(votingDeadline, block.timestamp + 72 hours);
    }

    function test_propose_emergency_requires_council_attestation() public {
        bytes[] memory emptySigs = new bytes[](0);
        address[] memory emptySigners = new address[](0);
        vm.prank(ALICE);
        vm.expectRevert(ForceAuthorization.EmergencyRequiresCouncilAttestation.selector);
        fa.propose(PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, true, emptySigs, emptySigners, 0);
    }

    function test_propose_emergency_with_valid_council_signatures_24h_voting() public {
        uint256 nonce = 1;
        (bytes[] memory sigs, address[] memory signers) = _councilSigsEmergencyPropose(
            ALICE, PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, nonce
        );
        vm.prank(ALICE);
        bytes32 id = fa.propose(PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, true, sigs, signers, nonce);
        (,, , bool emergency,, uint64 votingDeadline,
         ForceAuthorization.AuthState state,,,, ,) = fa.authorizations(id);
        assertTrue(emergency);
        assertEq(votingDeadline, block.timestamp + 24 hours);
        assertEq(uint8(state), uint8(ForceAuthorization.AuthState.Active));
    }

    function test_propose_emergency_rejects_invalid_signature() public {
        uint256 nonce = 2;
        (bytes[] memory sigs, address[] memory signers) = _councilSigsEmergencyPropose(
            ALICE, PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, nonce
        );
        // Corrupt first signature
        sigs[0] = bytes("invalid");
        vm.prank(ALICE);
        vm.expectRevert(ForceAuthorization.InvalidSignature.selector);
        fa.propose(PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, true, sigs, signers, nonce);
    }

    function test_propose_emergency_rejects_non_council_signer() public {
        uint256 nonce = 3;
        (bytes[] memory sigs, address[] memory signers) = _councilSigsEmergencyPropose(
            ALICE, PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, nonce
        );
        // Replace first signer with non-council member
        signers[0] = ALICE;
        vm.prank(ALICE);
        vm.expectRevert(abi.encodeWithSelector(ForceAuthorization.NotCouncilMember.selector, ALICE));
        fa.propose(PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, true, sigs, signers, nonce);
    }

    function test_propose_emergency_rejects_mismatched_sigs_signers_length() public {
        uint256 nonce = 4;
        (bytes[] memory sigs, address[] memory signers) = _councilSigsEmergencyPropose(
            ALICE, PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, nonce
        );
        // Remove one signer but keep 3 sigs
        signers = new address[](2);
        signers[0] = COUNCIL_1; signers[1] = COUNCIL_2;
        vm.prank(ALICE);
        vm.expectRevert(ForceAuthorization.InsufficientCouncilSigners.selector);
        fa.propose(PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, true, sigs, signers, nonce);
    }

    function test_supermajority_67pct_required() public {
        bytes32 id = _proposeNormal();
        // 5 for + 2 against = 7 votes (meets 50% quorum of 10).
        // 5/(5+2) = 71% which IS >= 67% supermajority — should Succeed.
        address[5] memory forVoters = [ALICE, BOB, CAROL, DAVE, EVE];
        for (uint256 i = 0; i < 5; i++) {
            vm.prank(forVoters[i]);
            fa.vote(id, ForceAuthorization.Choice.For);
        }
        vm.prank(FRANK); fa.vote(id, ForceAuthorization.Choice.Against);
        vm.prank(GUS);   fa.vote(id, ForceAuthorization.Choice.Against);

        skip(72 hours + 1);
        fa.resolve(id);
        (,, ,, ,,
         ForceAuthorization.AuthState state,,, ,,) = fa.authorizations(id);
        assertEq(uint8(state), uint8(ForceAuthorization.AuthState.Approved));
    }

    function test_defeated_at_60pct() public {
        bytes32 id = _proposeNormal();
        // 6 for + 4 against = 10 (meets quorum 5).
        // 6/(6+4) = 60% which is BELOW 67% supermajority — should Defeat.
        address[6] memory forVoters = [ALICE, BOB, CAROL, DAVE, EVE, FRANK];
        for (uint256 i = 0; i < 6; i++) {
            vm.prank(forVoters[i]);
            fa.vote(id, ForceAuthorization.Choice.For);
        }
        address[4] memory againstVoters = [
            GUS, address(uint160(0x10008)), address(uint160(0x10009)), address(uint160(0x1000a))
        ];
        for (uint256 i = 0; i < 4; i++) {
            vm.prank(againstVoters[i]);
            fa.vote(id, ForceAuthorization.Choice.Against);
        }

        skip(72 hours + 1);
        fa.resolve(id);
        (,, ,, ,,
         ForceAuthorization.AuthState state,,, ,,) = fa.authorizations(id);
        assertEq(uint8(state), uint8(ForceAuthorization.AuthState.Defeated));
    }

    function test_defeated_below_quorum() public {
        bytes32 id = _proposeNormal();
        // Only 4 votes — quorum is 5 (50% of 10)
        vm.prank(ALICE); fa.vote(id, ForceAuthorization.Choice.For);
        vm.prank(BOB);   fa.vote(id, ForceAuthorization.Choice.For);
        vm.prank(CAROL); fa.vote(id, ForceAuthorization.Choice.For);
        vm.prank(DAVE);  fa.vote(id, ForceAuthorization.Choice.For);

        skip(72 hours + 1);
        fa.resolve(id);
        (,, ,, ,,
         ForceAuthorization.AuthState state,,, ,,) = fa.authorizations(id);
        assertEq(uint8(state), uint8(ForceAuthorization.AuthState.Defeated));
    }

    function test_full_lifecycle_approve_execute_after_action() public {
        bytes32 id = _proposeNormal();
        address[8] memory forVoters = [
            ALICE, BOB, CAROL, DAVE, EVE, FRANK, GUS, address(uint160(0x10008))
        ];
        for (uint256 i = 0; i < 8; i++) {
            vm.prank(forVoters[i]);
            fa.vote(id, ForceAuthorization.Choice.For);
        }

        skip(72 hours + 1);
        fa.resolve(id);

        // Record execution
        bytes32 logCid = keccak256("ipfs://log");
        fa.recordExecution(id, logCid);
        (,, ,, ,,
         ForceAuthorization.AuthState executed,,, ,
         bytes32 storedLog,) = fa.authorizations(id);
        assertEq(uint8(executed), uint8(ForceAuthorization.AuthState.Executed));
        assertEq(storedLog, logCid);

        // After-action review with valid signatures
        bytes32 afterActionCid = keccak256("ipfs://after-action");
        (bytes[] memory sigs, address[] memory signers) = _councilSigsAfterAction(id, afterActionCid);
        fa.recordAfterAction(id, afterActionCid, sigs, signers);
        (,, ,, ,,
         ForceAuthorization.AuthState reviewed,,, ,
         , bytes32 storedAfterAction) = fa.authorizations(id);
        assertEq(uint8(reviewed), uint8(ForceAuthorization.AuthState.AfterActionReviewed));
        assertEq(storedAfterAction, afterActionCid);
    }

    function test_record_after_action_rejects_invalid_signature() public {
        bytes32 id = _proposeNormal();
        address[8] memory forVoters = [
            ALICE, BOB, CAROL, DAVE, EVE, FRANK, GUS, address(uint160(0x10008))
        ];
        for (uint256 i = 0; i < 8; i++) {
            vm.prank(forVoters[i]);
            fa.vote(id, ForceAuthorization.Choice.For);
        }
        skip(72 hours + 1);
        fa.resolve(id);
        bytes32 logCid = keccak256("ipfs://log");
        fa.recordExecution(id, logCid);

        bytes32 afterActionCid = keccak256("ipfs://after-action");
        (bytes[] memory sigs, address[] memory signers) = _councilSigsAfterAction(id, afterActionCid);
        // Corrupt first signature
        sigs[0] = bytes("invalid");
        vm.expectRevert(ForceAuthorization.InvalidSignature.selector);
        fa.recordAfterAction(id, afterActionCid, sigs, signers);
    }

    function test_cancel_with_valid_signatures() public {
        bytes32 id = _proposeNormal();
        bytes32 reasonCid = keccak256("ipfs://cancel-reason");
        (bytes[] memory sigs, address[] memory signers) = _councilSigsCancel(id, reasonCid);
        fa.cancel(id, reasonCid, sigs, signers);
        (,, ,, ,,
         ForceAuthorization.AuthState cancelled,,, ,,) = fa.authorizations(id);
        assertEq(uint8(cancelled), uint8(ForceAuthorization.AuthState.Cancelled));
    }

    function test_cancel_rejects_invalid_signature() public {
        bytes32 id = _proposeNormal();
        bytes32 reasonCid = keccak256("ipfs://cancel-reason");
        (bytes[] memory sigs, address[] memory signers) = _councilSigsCancel(id, reasonCid);
        sigs[0] = bytes("invalid");
        vm.expectRevert(ForceAuthorization.InvalidSignature.selector);
        fa.cancel(id, reasonCid, sigs, signers);
    }

    function test_cancel_rejects_non_council_signer() public {
        bytes32 id = _proposeNormal();
        bytes32 reasonCid = keccak256("ipfs://cancel-reason");
        (bytes[] memory sigs, address[] memory signers) = _councilSigsCancel(id, reasonCid);
        signers[0] = ALICE;
        vm.expectRevert(abi.encodeWithSelector(ForceAuthorization.NotCouncilMember.selector, ALICE));
        fa.cancel(id, reasonCid, sigs, signers);
    }

    function test_cancel_rejects_after_execution() public {
        bytes32 id = _proposeNormal();
        address[8] memory forVoters = [
            ALICE, BOB, CAROL, DAVE, EVE, FRANK, GUS, address(uint160(0x10008))
        ];
        for (uint256 i = 0; i < 8; i++) {
            vm.prank(forVoters[i]);
            fa.vote(id, ForceAuthorization.Choice.For);
        }
        skip(72 hours + 1);
        fa.resolve(id);
        bytes32 logCid = keccak256("ipfs://log");
        fa.recordExecution(id, logCid);

        bytes32 reasonCid = keccak256("ipfs://cancel-reason");
        (bytes[] memory sigs, address[] memory signers) = _councilSigsCancel(id, reasonCid);
        vm.expectRevert(abi.encodeWithSelector(ForceAuthorization.InvalidStateForOperation.selector, uint8(ForceAuthorization.AuthState.Executed), uint8(ForceAuthorization.AuthState.Active)));
        fa.cancel(id, reasonCid, sigs, signers);
    }
}