// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {AgentAuthorityToken, IAdherentRegistry} from "../src/AgentAuthorityToken.sol";

/**
 * @dev Minimal mock of IAdherentRegistry for AAT tests. Records
 *      Steward → adherent tokenId + revoked status. Real AdherentRegistry
 *      is exercised in AdherentRegistry.t.sol; this mock isolates AAT
 *      mint-eligibility logic from Adherent join machinery.
 */
contract MockAdherentRegistry is IAdherentRegistry {
    mapping(address => uint256) public override tokenOf;
    mapping(uint256 => bool) public _revoked;

    function setHolder(address holder, uint256 tokenId) external {
        tokenOf[holder] = tokenId;
    }

    function setRevoked(uint256 tokenId, bool flag) external {
        _revoked[tokenId] = flag;
    }

    function locked(uint256) external pure override returns (bool) {
        return true;
    }

    function isRevoked(uint256 tokenId) external view override returns (bool) {
        return _revoked[tokenId];
    }
}

contract AgentAuthorityTokenTest is Test {
    AgentAuthorityToken aat;
    MockAdherentRegistry mock;

    address constant STEWARD = address(0xA11CE);
    address constant COUNCIL = address(0xC0FFEE);
    address constant STRANGER = address(0xDEAD);

    string constant AGENT_DID = "did:web:c43221501.etzhayyim.com";

    function setUp() public {
        mock = new MockAdherentRegistry();
        mock.setHolder(STEWARD, 1);
        aat = new AgentAuthorityToken(IAdherentRegistry(address(mock)), COUNCIL);
    }

    function _defaultScope()
        internal
        pure
        returns (AgentAuthorityToken.Scope memory s)
    {
        bytes32[] memory prefixes = new bytes32[](1);
        prefixes[0] = keccak256("4322");
        bytes32[] memory purposes = new bytes32[](2);
        purposes[0] = keccak256("donation-in-kind");
        purposes[1] = keccak256("internal-allocation");
        s = AgentAuthorityToken.Scope({
            unspscPrefixes: prefixes,
            purposes: purposes,
            valueCap: 1000
        });
    }

    function test_mint_byStewardWithAdherent_emitsAndStores() public {
        AgentAuthorityToken.Scope memory s = _defaultScope();
        uint64 exp = uint64(block.timestamp + 30 days);

        vm.prank(STEWARD);
        uint256 tokenId = aat.mint(AGENT_DID, s, exp);

        assertEq(tokenId, 1);
        assertEq(aat.totalMinted(), 1);
        assertTrue(aat.isValid(tokenId));
        assertEq(aat.activeTokenIdForAgent(AGENT_DID), tokenId);

        AgentAuthorityToken.AATRecord memory rec = aat.recordOf(tokenId);
        assertEq(rec.steward, STEWARD);
        assertEq(rec.stewardAdherentTokenId, 1);
        assertEq(rec.agentDid, AGENT_DID);
        assertEq(rec.expiresAt, exp);
        assertFalse(rec.revoked);

        (bytes32[] memory pfxs, bytes32[] memory purs, uint256 cap) =
            aat.scopeOf(tokenId);
        assertEq(pfxs.length, 1);
        assertEq(pfxs[0], keccak256("4322"));
        assertEq(purs.length, 2);
        assertEq(cap, 1000);
    }

    function test_mint_rejectsStewardWithoutAdherent() public {
        AgentAuthorityToken.Scope memory s = _defaultScope();
        vm.prank(STRANGER);
        vm.expectRevert(
            abi.encodeWithSelector(
                AgentAuthorityToken.StewardLacksAdherent.selector,
                STRANGER
            )
        );
        aat.mint(AGENT_DID, s, uint64(block.timestamp + 1 days));
    }

    function test_mint_rejectsRevokedAdherent() public {
        mock.setRevoked(1, true);
        AgentAuthorityToken.Scope memory s = _defaultScope();
        vm.prank(STEWARD);
        vm.expectRevert(
            abi.encodeWithSelector(
                AgentAuthorityToken.StewardAdherentRevoked.selector,
                uint256(1)
            )
        );
        aat.mint(AGENT_DID, s, uint64(block.timestamp + 1 days));
    }

    function test_mint_rejectsEmptyScope() public {
        AgentAuthorityToken.Scope memory empty;
        vm.prank(STEWARD);
        vm.expectRevert(AgentAuthorityToken.EmptyScope.selector);
        aat.mint(AGENT_DID, empty, uint64(block.timestamp + 1 days));
    }

    function test_mint_rejectsPastExpiry() public {
        AgentAuthorityToken.Scope memory s = _defaultScope();
        vm.warp(1000);
        vm.prank(STEWARD);
        vm.expectRevert(AgentAuthorityToken.InvalidExpiry.selector);
        aat.mint(AGENT_DID, s, 999);
    }

    function test_revoke_byStewardClearsActiveDidIndex() public {
        AgentAuthorityToken.Scope memory s = _defaultScope();
        vm.prank(STEWARD);
        uint256 tokenId = aat.mint(AGENT_DID, s, uint64(block.timestamp + 1 days));

        vm.prank(STEWARD);
        aat.revoke(tokenId, bytes32("reason-cid"));

        assertFalse(aat.isValid(tokenId));
        assertEq(aat.activeTokenIdForAgent(AGENT_DID), 0);
    }

    function test_revoke_byCouncilWorks() public {
        AgentAuthorityToken.Scope memory s = _defaultScope();
        vm.prank(STEWARD);
        uint256 tokenId = aat.mint(AGENT_DID, s, uint64(block.timestamp + 1 days));

        vm.prank(COUNCIL);
        aat.revoke(tokenId, bytes32("council-reason"));

        assertFalse(aat.isValid(tokenId));
    }

    function test_revoke_byStrangerReverts() public {
        AgentAuthorityToken.Scope memory s = _defaultScope();
        vm.prank(STEWARD);
        uint256 tokenId = aat.mint(AGENT_DID, s, uint64(block.timestamp + 1 days));

        vm.prank(STRANGER);
        vm.expectRevert(AgentAuthorityToken.NotSteward.selector);
        aat.revoke(tokenId, bytes32("nope"));
    }

    function test_expiry_invalidatesToken() public {
        AgentAuthorityToken.Scope memory s = _defaultScope();
        uint64 exp = uint64(block.timestamp + 1 days);
        vm.prank(STEWARD);
        uint256 tokenId = aat.mint(AGENT_DID, s, exp);

        vm.warp(exp + 1);
        assertTrue(aat.isExpired(tokenId));
        assertFalse(aat.isValid(tokenId));
    }

    function test_transferFrom_reverts() public {
        AgentAuthorityToken.Scope memory s = _defaultScope();
        vm.prank(STEWARD);
        uint256 tokenId = aat.mint(AGENT_DID, s, uint64(block.timestamp + 1 days));

        vm.expectRevert(AgentAuthorityToken.Soulbound.selector);
        aat.transferFrom(STEWARD, STRANGER, tokenId);
    }

    function test_locked_returnsTrue() public {
        AgentAuthorityToken.Scope memory s = _defaultScope();
        vm.prank(STEWARD);
        uint256 tokenId = aat.mint(AGENT_DID, s, uint64(block.timestamp + 1 days));
        assertTrue(aat.locked(tokenId));
    }
}
