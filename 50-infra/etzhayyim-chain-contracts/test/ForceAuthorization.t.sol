// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Test.sol";
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
    address constant COUNCIL_1 = address(0xC001);
    address constant COUNCIL_2 = address(0xC002);
    address constant COUNCIL_3 = address(0xC003);

    bytes32 constant PROPOSAL_CID = keccak256("ipfs://Qm...proposal");
    bytes32 constant INTENDED_USE_LAND_DEFENSE = keccak256("defense-of-land");

    function setUp() public {
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
        return fa.propose(PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, false, emptySigs, emptySigners);
    }

    function _councilSigs() internal pure returns (bytes[] memory sigs, address[] memory signers) {
        signers = new address[](3);
        signers[0] = COUNCIL_1; signers[1] = COUNCIL_2; signers[2] = COUNCIL_3;
        sigs = new bytes[](3);
        sigs[0] = bytes("s1"); sigs[1] = bytes("s2"); sigs[2] = bytes("s3");
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
        fa.propose(PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, true, emptySigs, emptySigners);
    }

    function test_propose_emergency_with_council_24h_voting() public {
        (bytes[] memory sigs, address[] memory signers) = _councilSigs();
        vm.prank(ALICE);
        bytes32 id = fa.propose(PROPOSAL_CID, INTENDED_USE_LAND_DEFENSE, true, sigs, signers);
        (,, , bool emergency,, uint64 votingDeadline,
         ForceAuthorization.AuthState state,,,, ,) = fa.authorizations(id);
        assertTrue(emergency);
        assertEq(votingDeadline, block.timestamp + 24 hours);
        assertEq(uint8(state), uint8(ForceAuthorization.AuthState.Active));
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

        // After-action review
        (bytes[] memory sigs, address[] memory signers) = _councilSigs();
        bytes32 afterActionCid = keccak256("ipfs://after-action");
        fa.recordAfterAction(id, afterActionCid, sigs, signers);
        (,, ,, ,,
         ForceAuthorization.AuthState reviewed,,, ,
         , bytes32 storedAfterAction) = fa.authorizations(id);
        assertEq(uint8(reviewed), uint8(ForceAuthorization.AuthState.AfterActionReviewed));
        assertEq(storedAfterAction, afterActionCid);
    }
}
