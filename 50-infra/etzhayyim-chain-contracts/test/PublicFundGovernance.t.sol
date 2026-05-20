// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {
    PublicFundGovernance,
    IAdherentRegistry,
    IChartersComplianceRegistry
} from "../src/PublicFundGovernance.sol";

contract MockAdherent is IAdherentRegistry {
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

contract MockCharters is IChartersComplianceRegistry {
    mapping(address => bool) public override isCouncilMember;
    mapping(address => bool) public override isNonAlignedAddress;
    mapping(uint256 => bool) public override isNonAlignedTokenId;
    function setCouncil(address a, bool b) external { isCouncilMember[a] = b; }
    function setNonAlignedAddr(address a, bool b) external { isNonAlignedAddress[a] = b; }
    function setNonAlignedToken(uint256 id, bool b) external { isNonAlignedTokenId[id] = b; }
}

contract PublicFundGovernanceTest is Test {
    PublicFundGovernance gov;
    MockAdherent adh;
    MockCharters chs;

    address constant PUBLIC_FUND_SAFE = address(0xF00D);
    address constant ALICE = address(0xA11CE);
    address constant BOB = address(0xB0B);
    address constant CAROL = address(0xCA401);
    address constant GRANT_RECIPIENT = address(0x6000);
    address constant COUNCIL_1 = address(0xC001);
    address constant COUNCIL_2 = address(0xC002);
    address constant COUNCIL_3 = address(0xC003);

    bytes32 constant MISSION_AXIS = keccak256("mission.ip_free_release");
    bytes32 constant EVIDENCE = keccak256("ipfs://Qm...");

    function setUp() public {
        adh = new MockAdherent();
        chs = new MockCharters();
        gov = new PublicFundGovernance(adh, chs, PUBLIC_FUND_SAFE);

        // 10 SBT holders → quorum 20% = 2 votes minimum
        for (uint256 i = 1; i <= 10; i++) {
            adh.setToken(address(uint160(0x10000 + i)), i);
        }
        adh.setToken(ALICE, 11);  // tokenId 11
        adh.setToken(BOB, 12);
        adh.setToken(CAROL, 13);

        chs.setCouncil(COUNCIL_1, true);
        chs.setCouncil(COUNCIL_2, true);
        chs.setCouncil(COUNCIL_3, true);
    }

    function _propose() internal returns (bytes32) {
        address[] memory recipients = new address[](1);
        recipients[0] = GRANT_RECIPIENT;
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = 1_000_000;  // 1 USDC
        vm.prank(ALICE);
        return gov.propose(recipients, amounts, MISSION_AXIS, EVIDENCE);
    }

    function test_propose_records_grant() public {
        bytes32 pid = _propose();
        (
            address proposer, bytes32 axis, bytes32 evid,
            ,, ,
            PublicFundGovernance.ProposalState state,
            ,,
        ) = gov.grants(pid);
        assertEq(proposer, ALICE);
        assertEq(axis, MISSION_AXIS);
        assertEq(evid, EVIDENCE);
        assertEq(uint8(state), uint8(PublicFundGovernance.ProposalState.Active));
    }

    function test_propose_rejects_non_aligned_recipient() public {
        chs.setNonAlignedAddr(GRANT_RECIPIENT, true);
        address[] memory r = new address[](1); r[0] = GRANT_RECIPIENT;
        uint256[] memory a = new uint256[](1); a[0] = 1;
        vm.prank(ALICE);
        vm.expectRevert(abi.encodeWithSelector(PublicFundGovernance.RecipientNonAligned.selector, GRANT_RECIPIENT));
        gov.propose(r, a, MISSION_AXIS, EVIDENCE);
    }

    function test_vote_for_against_abstain() public {
        bytes32 pid = _propose();
        vm.prank(ALICE);
        gov.vote(pid, PublicFundGovernance.Choice.For);
        vm.prank(BOB);
        gov.vote(pid, PublicFundGovernance.Choice.Against);
        vm.prank(CAROL);
        gov.vote(pid, PublicFundGovernance.Choice.Abstain);

        (, , , , , ,
         PublicFundGovernance.ProposalState state,
         uint256 forV, uint256 againstV, uint256 abstainV) = gov.grants(pid);
        assertEq(forV, 1);
        assertEq(againstV, 1);
        assertEq(abstainV, 1);
        assertEq(uint8(state), uint8(PublicFundGovernance.ProposalState.Active));
    }

    function test_vote_blocks_double_vote() public {
        bytes32 pid = _propose();
        vm.prank(ALICE);
        gov.vote(pid, PublicFundGovernance.Choice.For);
        vm.prank(ALICE);
        vm.expectRevert(abi.encodeWithSelector(PublicFundGovernance.AlreadyVoted.selector, uint256(11)));
        gov.vote(pid, PublicFundGovernance.Choice.For);
    }

    function test_vote_blocks_non_aligned_sbt() public {
        bytes32 pid = _propose();
        chs.setNonAlignedToken(11, true);
        vm.prank(ALICE);
        vm.expectRevert(abi.encodeWithSelector(PublicFundGovernance.VoterNonAligned.selector, uint256(11)));
        gov.vote(pid, PublicFundGovernance.Choice.For);
    }

    function test_succeeds_with_3_for_meets_quorum() public {
        // totalMinted=13, quorum=20% → ceil(13*0.2)=2 votes minimum.
        bytes32 pid = _propose();
        vm.prank(ALICE); gov.vote(pid, PublicFundGovernance.Choice.For);
        vm.prank(BOB);   gov.vote(pid, PublicFundGovernance.Choice.For);
        vm.prank(CAROL); gov.vote(pid, PublicFundGovernance.Choice.For);

        skip(7 days + 1);
        gov.queue(pid);

        (, , , , , ,
         PublicFundGovernance.ProposalState state,,, ) = gov.grants(pid);
        assertEq(uint8(state), uint8(PublicFundGovernance.ProposalState.Queued));

        skip(48 hours + 1);
        gov.execute(pid);
        (, , , , , ,
         PublicFundGovernance.ProposalState executed,,, ) = gov.grants(pid);
        assertEq(uint8(executed), uint8(PublicFundGovernance.ProposalState.Executed));
    }

    function test_defeated_below_quorum() public {
        bytes32 pid = _propose();
        // Only 1 vote — below 20% of 13 = 2.6 → quorum=2
        vm.prank(ALICE); gov.vote(pid, PublicFundGovernance.Choice.For);

        skip(7 days + 1);
        vm.expectRevert();  // queue() reverts because state didn't reach Succeeded
        gov.queue(pid);
    }

    function test_defeated_below_50pct_approval() public {
        bytes32 pid = _propose();
        // 2 for + 3 against — below 50% threshold
        vm.prank(ALICE); gov.vote(pid, PublicFundGovernance.Choice.For);
        vm.prank(BOB);   gov.vote(pid, PublicFundGovernance.Choice.For);

        // Add 3 against voters
        address[3] memory againsts = [address(0x1A), address(0x1B), address(0x1C)];
        for (uint256 i = 0; i < 3; i++) {
            adh.setToken(againsts[i], 20 + i);
            vm.prank(againsts[i]);
            gov.vote(pid, PublicFundGovernance.Choice.Against);
        }

        skip(7 days + 1);
        vm.expectRevert();  // not Succeeded
        gov.queue(pid);
    }

    function test_cancel_requires_council_3() public {
        bytes32 pid = _propose();
        address[] memory signers = new address[](3);
        signers[0] = COUNCIL_1; signers[1] = COUNCIL_2; signers[2] = COUNCIL_3;
        bytes[] memory sigs = new bytes[](3);
        sigs[0] = bytes("s1"); sigs[1] = bytes("s2"); sigs[2] = bytes("s3");

        gov.cancel(pid, keccak256("test-cancel"), sigs, signers);

        (, , , , , ,
         PublicFundGovernance.ProposalState state,,, ) = gov.grants(pid);
        assertEq(uint8(state), uint8(PublicFundGovernance.ProposalState.Cancelled));
    }
}
