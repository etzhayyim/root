// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Test} from "forge-std/Test.sol";

import {GftdAgentRegistry} from "../src/GftdAgentRegistry.sol";
import {GftdRootIdentity} from "../src/GftdRootIdentity.sol";
import {GftdRootIdentityRegistry} from "../src/GftdRootIdentityRegistry.sol";

contract GftdAgentRuntimeRegistriesTest is Test {
    GftdRootIdentityRegistry rootRegistry;
    GftdAgentRegistry agentRegistry;

    address owner = address(0xA11CE);
    address controller = address(0xB0B);
    bytes32 rootDidHash = keccak256(bytes("did:erc725:gftd:260425:0xroot"));
    bytes32 facadeDidHash = keccak256(bytes("did:web:yoro.etzhayyim.com"));

    function setUp() public {
        rootRegistry = new GftdRootIdentityRegistry(owner);
        agentRegistry = new GftdAgentRegistry(owner);
    }

    function testDeployRootIdentityAndSetERC725Data() public {
        vm.prank(owner);
        address identityAddr = rootRegistry.deployRootIdentity(rootDidHash, "did:erc725:gftd:260425:0xroot", controller);

        assertEq(rootRegistry.identityByRootDid(rootDidHash), identityAddr);
        GftdRootIdentity identity = GftdRootIdentity(payable(identityAddr));
        assertEq(identity.owner(), controller);

        bytes32 policyKey = keccak256(bytes("gftd.root.policy.cid"));
        bytes memory policyCid = bytes("ipfs://bafy-policy");
        vm.prank(controller);
        identity.setData(policyKey, policyCid);
        assertEq(identity.getData(policyKey), policyCid);

        vm.prank(owner);
        rootRegistry.linkFacade(rootDidHash, facadeDidHash, "did:web:yoro.etzhayyim.com");
        assertEq(rootRegistry.resolveFacade(facadeDidHash), identityAddr);
    }

    function testRegisterAgentAndUpdateUri() public {
        vm.prank(owner);
        uint256 tokenId = agentRegistry.registerAgent(
            rootDidHash,
            controller,
            "ipfs://bafy-agent/agent.json",
            keccak256(bytes("metadata-v1"))
        );

        assertEq(tokenId, 1);
        assertEq(agentRegistry.ownerOf(tokenId), controller);
        assertEq(agentRegistry.tokenByRootDid(rootDidHash), tokenId);
        assertEq(agentRegistry.agentURI(tokenId), "ipfs://bafy-agent/agent.json");

        vm.prank(controller);
        agentRegistry.setAgentURI(tokenId, "ipfs://bafy-agent-v2/agent.json", keccak256(bytes("metadata-v2")));
        assertEq(agentRegistry.agentURI(tokenId), "ipfs://bafy-agent-v2/agent.json");
    }

    function testValidationAndReputationRecords() public {
        vm.prank(owner);
        uint256 tokenId = agentRegistry.registerAgent(rootDidHash, controller, "ipfs://bafy-agent/agent.json", bytes32(0));

        bytes32 validationId = keccak256(bytes("validation-1"));
        vm.prank(address(0xCAFE));
        agentRegistry.recordValidation(
            validationId,
            tokenId,
            keccak256(bytes("request")),
            keccak256(bytes("result")),
            "ipfs://bafy-validation"
        );
        GftdAgentRegistry.ValidationRecord memory validation = agentRegistry.validation(validationId);
        assertEq(validation.tokenId, tokenId);
        assertEq(validation.validator, address(0xCAFE));

        bytes32 reputationId = keccak256(bytes("reputation-1"));
        vm.prank(address(0xF00D));
        agentRegistry.recordReputation(reputationId, tokenId, 7, keccak256(bytes("claim")), "ipfs://bafy-reputation");
        assertEq(agentRegistry.reputationScore(tokenId), 7);
    }
}
