// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Test} from "forge-std/Test.sol";

import {etzhayyimAgentRegistry} from "../src/EtzhayyimAgentRegistry.sol";
import {etzhayyimRootIdentity} from "../src/EtzhayyimRootIdentity.sol";
import {etzhayyimRootIdentityRegistry} from "../src/EtzhayyimRootIdentityRegistry.sol";

contract etzhayyimAgentRuntimeRegistriesTest is Test {
    etzhayyimRootIdentityRegistry rootRegistry;
    etzhayyimAgentRegistry agentRegistry;

    address owner = address(0xA11CE);
    address controller = address(0xB0B);
    bytes32 rootDidHash = keccak256(bytes("did:erc725:etzhayyim:260425:0xroot"));
    bytes32 facadeDidHash = keccak256(bytes("did:web:yoro.etzhayyim.com"));

    function setUp() public {
        rootRegistry = new etzhayyimRootIdentityRegistry(owner);
        agentRegistry = new etzhayyimAgentRegistry(owner);
    }

    function testDeployRootIdentityAndSetERC725Data() public {
        vm.prank(owner);
        address identityAddr = rootRegistry.deployRootIdentity(rootDidHash, "did:erc725:etzhayyim:260425:0xroot", controller);

        assertEq(rootRegistry.identityByRootDid(rootDidHash), identityAddr);
        etzhayyimRootIdentity identity = etzhayyimRootIdentity(payable(identityAddr));
        assertEq(identity.owner(), controller);

        bytes32 policyKey = keccak256(bytes("etzhayyim.root.policy.cid"));
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
        etzhayyimAgentRegistry.ValidationRecord memory validation = agentRegistry.validation(validationId);
        assertEq(validation.tokenId, tokenId);
        assertEq(validation.validator, address(0xCAFE));

        bytes32 reputationId = keccak256(bytes("reputation-1"));
        vm.prank(address(0xF00D));
        agentRegistry.recordReputation(reputationId, tokenId, 7, keccak256(bytes("claim")), "ipfs://bafy-reputation");
        assertEq(agentRegistry.reputationScore(tokenId), 7);
    }
}
