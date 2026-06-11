// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {Fixture} from "./_helpers/Fixture.sol";
import {HoldingAttestation} from "../src/HoldingAttestation.sol";

contract HoldingAttestationTest is Fixture {
    HoldingAttestation ha;

    // Representative officer signer
    uint256 internal repKey = uint256(keccak256("rep-key"));
    address internal repAddr;

    function setUp() public {
        _deployStack();
        ha = new HoldingAttestation(c);
        repAddr = vm.addr(repKey);
        // Set template via governance (so attestations have a non-zero
        // template anchor).
        vm.prank(address(gov));
        ha.setTemplate(keccak256("template-v1"), keccak256("lawfirm-ok-v1"));
    }

    function _attestShrine() internal returns (bytes32 attId, bytes memory sig) {
        bytes32 assetUriHash = keccak256("hokkaido-shrine-estate-id-12345");
        bytes32 docHash = keccak256("doc-text-v1");
        bytes32 inner = ha.payloadHash(
            repAddr, "did:web:rep.etzhayyim.com", assetUriHash, docHash, keccak256("template-v1")
        );
        sig = _signEip191(repKey, inner);
        attId = ha.attest(repAddr, "did:web:rep.etzhayyim.com", assetUriHash, docHash, sig);
    }

    function test_setTemplate_onlyGovernance() public {
        vm.expectRevert(HoldingAttestation.NotGovernance.selector);
        ha.setTemplate(keccak256("v2"), keccak256("lawfirm-v2"));
    }

    function test_attest_happyPath_emits() public {
        (bytes32 attId, ) = _attestShrine();
        HoldingAttestation.AttestationRecord memory rec = ha.getAttestation(attId);
        assertEq(rec.holder, repAddr);
        assertEq(rec.holderDid, "did:web:rep.etzhayyim.com");
        assertFalse(rec.revoked);
        assertTrue(ha.isActiveAttestation(attId));
        assertEq(ha.totalAttestations(), 1);
    }

    function test_attest_invalidSig_reverts() public {
        bytes32 assetUriHash = keccak256("estate");
        bytes32 docHash = keccak256("doc");
        bytes32 inner = ha.payloadHash(
            repAddr, "did:web:rep.etzhayyim.com", assetUriHash, docHash, keccak256("template-v1")
        );
        // Sign with a wrong key
        bytes memory sig = _signEip191(uint256(keccak256("wrong")), inner);
        vm.expectRevert(HoldingAttestation.InvalidSignature.selector);
        ha.attest(repAddr, "did:web:rep.etzhayyim.com", assetUriHash, docHash, sig);
    }

    function test_attest_emptyHolderDid() public {
        vm.expectRevert(HoldingAttestation.EmptyHolderDid.selector);
        ha.attest(repAddr, "", keccak256("a"), keccak256("b"), hex"");
    }

    function test_attest_emptyDocHash() public {
        vm.expectRevert(HoldingAttestation.EmptyDocHash.selector);
        ha.attest(repAddr, "did:web:rep.etzhayyim.com", keccak256("a"), bytes32(0), hex"");
    }

    function test_attest_idempotentDuplicate_reverts() public {
        (, bytes memory sig) = _attestShrine();
        // re-submit identical payload
        bytes32 assetUriHash = keccak256("hokkaido-shrine-estate-id-12345");
        bytes32 docHash = keccak256("doc-text-v1");
        vm.expectRevert(bytes("duplicate attestation"));
        ha.attest(repAddr, "did:web:rep.etzhayyim.com", assetUriHash, docHash, sig);
    }

    function test_revoke_byGovernance_marksInactive() public {
        (bytes32 attId, ) = _attestShrine();
        vm.prank(address(gov));
        ha.revoke(attId, keccak256("officer-rotation"));
        assertFalse(ha.isActiveAttestation(attId));
        HoldingAttestation.AttestationRecord memory rec = ha.getAttestation(attId);
        assertTrue(rec.revoked);
        assertEq(rec.revokeReason, keccak256("officer-rotation"));
    }

    function test_revoke_unknownAttestation() public {
        vm.prank(address(gov));
        vm.expectRevert(abi.encodeWithSelector(HoldingAttestation.UnknownAttestation.selector, bytes32(uint256(0xDEAD))));
        ha.revoke(bytes32(uint256(0xDEAD)), bytes32(0));
    }

    function test_revoke_alreadyRevoked() public {
        (bytes32 attId, ) = _attestShrine();
        vm.startPrank(address(gov));
        ha.revoke(attId, bytes32(uint256(1)));
        vm.expectRevert(HoldingAttestation.AlreadyRevoked.selector);
        ha.revoke(attId, bytes32(uint256(2)));
        vm.stopPrank();
    }

    function test_attest_snapshotsCurrentTemplate() public {
        (bytes32 attId, ) = _attestShrine();
        // Template change happens AFTER first attestation.
        vm.prank(address(gov));
        ha.setTemplate(keccak256("template-v2"), keccak256("lawfirm-v2"));
        HoldingAttestation.AttestationRecord memory rec = ha.getAttestation(attId);
        assertEq(rec.docTemplateCid, keccak256("template-v1")); // older attestation pinned to v1
    }
}
