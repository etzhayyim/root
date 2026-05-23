// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {GftdAgentRegistry} from "../src/GftdAgentRegistry.sol";

contract GftdAgentRegistryTest is Test {
    GftdAgentRegistry r;

    address constant COUNCIL = address(0xC0DEC011);
    address constant STEWARD = address(0x57E4A4D);
    address constant STEWARD_2 = address(0x57E4A4D2);
    address constant AGENT_ADDR = address(0xA9E47);
    address constant AGENT_ADDR_2 = address(0xA9E472);
    address constant STRANGER = address(0xDEADBEEF);

    bytes32 constant DID_A = keccak256("did:web:etzhayyim.com:actor:dataset-pinner");
    bytes32 constant DID_B = keccak256("did:web:etzhayyim.com:actor:pinner");
    bytes32 constant SCOPE_NONE = bytes32(0);
    bytes32 constant SCOPE_DATASETPIN = keccak256("ai.gftd.apps.substrate.datasetPin");

    string constant URI_A = "ipfs://bafybeigdataset/agent.json";
    string constant URI_A_V2 = "ipfs://bafybeigdatasetv2/agent.json";

    function setUp() public {
        r = new GftdAgentRegistry(COUNCIL);
    }

    function test_constructor_rejectsZeroCouncil() public {
        vm.expectRevert(GftdAgentRegistry.StewardZero.selector);
        new GftdAgentRegistry(address(0));
    }

    function test_register_mintsMonotonically() public {
        uint256 t1 = r.registerAgent(DID_A, AGENT_ADDR, STEWARD, URI_A, SCOPE_DATASETPIN);
        uint256 t2 = r.registerAgent(DID_B, AGENT_ADDR_2, STEWARD_2, URI_A, SCOPE_NONE);
        assertEq(t1, 1);
        assertEq(t2, 2);
        assertEq(r.totalMinted(), 2);
        assertEq(r.didHashToTokenId(DID_A), 1);
        assertEq(r.didHashToTokenId(DID_B), 2);
        assertEq(r.addrToTokenId(AGENT_ADDR), 1);

        GftdAgentRegistry.Agent memory a = r.getAgentById(t1);
        assertEq(a.didHash, DID_A);
        assertEq(a.agentAddr, AGENT_ADDR);
        assertEq(a.steward, STEWARD);
        assertEq(a.agentURI, URI_A);
        assertEq(a.scopeHash, SCOPE_DATASETPIN);
        assertTrue(a.active);
    }

    function test_register_rejectsDuplicateDid() public {
        r.registerAgent(DID_A, AGENT_ADDR, STEWARD, URI_A, SCOPE_NONE);
        vm.expectRevert(abi.encodeWithSelector(GftdAgentRegistry.AlreadyRegistered.selector, DID_A));
        r.registerAgent(DID_A, AGENT_ADDR_2, STEWARD_2, URI_A, SCOPE_NONE);
    }

    function test_register_rejectsZeroSteward() public {
        vm.expectRevert(GftdAgentRegistry.StewardZero.selector);
        r.registerAgent(DID_A, AGENT_ADDR, address(0), URI_A, SCOPE_NONE);
    }

    function test_register_rejectsEmptyURI() public {
        vm.expectRevert(GftdAgentRegistry.AgentURIEmpty.selector);
        r.registerAgent(DID_A, AGENT_ADDR, STEWARD, "", SCOPE_NONE);
    }

    function test_updateAgentURI_onlySteward() public {
        uint256 t = r.registerAgent(DID_A, AGENT_ADDR, STEWARD, URI_A, SCOPE_NONE);
        // Non-steward should be rejected.
        vm.expectRevert(abi.encodeWithSelector(GftdAgentRegistry.NotSteward.selector, t, STRANGER));
        vm.prank(STRANGER);
        r.updateAgentURI(t, URI_A_V2);
        // Steward succeeds.
        vm.prank(STEWARD);
        r.updateAgentURI(t, URI_A_V2);
        assertEq(r.getAgentURI(t), URI_A_V2);
    }

    function test_updateAgentURI_rejectsEmpty() public {
        uint256 t = r.registerAgent(DID_A, AGENT_ADDR, STEWARD, URI_A, SCOPE_NONE);
        vm.prank(STEWARD);
        vm.expectRevert(GftdAgentRegistry.AgentURIEmpty.selector);
        r.updateAgentURI(t, "");
    }

    function test_updateScope_steward() public {
        uint256 t = r.registerAgent(DID_A, AGENT_ADDR, STEWARD, URI_A, SCOPE_NONE);
        vm.prank(STEWARD);
        r.updateScope(t, SCOPE_DATASETPIN);
        assertEq(r.getAgentById(t).scopeHash, SCOPE_DATASETPIN);
    }

    function test_deactivate_stewardCanRetire() public {
        uint256 t = r.registerAgent(DID_A, AGENT_ADDR, STEWARD, URI_A, SCOPE_NONE);
        vm.prank(STEWARD);
        r.deactivateAgent(t);
        assertFalse(r.isActive(t));
        // Cannot deactivate twice.
        vm.prank(STEWARD);
        vm.expectRevert(abi.encodeWithSelector(GftdAgentRegistry.AgentInactive.selector, t));
        r.deactivateAgent(t);
    }

    function test_revoke_councilOnly() public {
        uint256 t = r.registerAgent(DID_A, AGENT_ADDR, STEWARD, URI_A, SCOPE_NONE);
        // Steward cannot revoke.
        vm.prank(STEWARD);
        vm.expectRevert(GftdAgentRegistry.NotCouncil.selector);
        r.revokeAgent(t);
        // Council can.
        vm.prank(COUNCIL);
        r.revokeAgent(t);
        assertFalse(r.isActive(t));
    }

    function test_revoke_rejectsUnknownToken() public {
        vm.prank(COUNCIL);
        vm.expectRevert(abi.encodeWithSelector(GftdAgentRegistry.UnknownToken.selector, uint256(99)));
        r.revokeAgent(99);
    }

    function test_locked_alwaysTrue() public {
        uint256 t = r.registerAgent(DID_A, AGENT_ADDR, STEWARD, URI_A, SCOPE_NONE);
        assertTrue(r.locked(t));
    }

    function test_transferFrom_alwaysReverts() public {
        r.registerAgent(DID_A, AGENT_ADDR, STEWARD, URI_A, SCOPE_NONE);
        vm.expectRevert(GftdAgentRegistry.SoulboundTransfer.selector);
        r.transferFrom(STEWARD, STRANGER, 1);
    }

    function test_getAgentByDid_returnsCorrectAgent() public {
        r.registerAgent(DID_A, AGENT_ADDR, STEWARD, URI_A, SCOPE_DATASETPIN);
        GftdAgentRegistry.Agent memory a = r.getAgentByDid(DID_A);
        assertEq(a.didHash, DID_A);
        assertEq(a.agentURI, URI_A);
        assertEq(a.scopeHash, SCOPE_DATASETPIN);
    }

    function test_getAgentURI_ercAccessor() public {
        uint256 t = r.registerAgent(DID_A, AGENT_ADDR, STEWARD, URI_A, SCOPE_NONE);
        assertEq(r.getAgentURI(t), URI_A);
    }
}
