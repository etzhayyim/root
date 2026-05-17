// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {Fixture} from "./_helpers/Fixture.sol";
import {CorpusRegistry} from "../src/CorpusRegistry.sol";

contract CorpusRegistryTest is Fixture {
    CorpusRegistry cr;

    function setUp() public {
        _deployStack();
        cr = new CorpusRegistry(c);
    }

    function _mintShrine() internal returns (uint256) {
        vm.prank(address(gov));
        return cr.mint(
            cr.KIND_FACILITY(),
            "did:web:rep.etzhayyim.com",
            keccak256("JP-13"),
            keccak256("attestation-1"),
            keccak256("ipfs-cid-shrine-doc-bundle")
        );
    }

    function test_mint_byGovernance_emitsLocked() public {
        vm.expectEmit(true, true, true, true);
        emit CorpusRegistry.CorpusMinted(
            1,
            cr.KIND_FACILITY(),
            keccak256("attestation-1"),
            "did:web:rep.etzhayyim.com",
            keccak256("JP-13"),
            keccak256("ipfs-cid-shrine-doc-bundle")
        );
        vm.expectEmit(true, false, false, false);
        emit CorpusRegistry.Locked(1);

        uint256 id = _mintShrine();
        assertEq(id, 1);
        assertTrue(cr.locked(id));
        CorpusRegistry.CorpusRecord memory rec = cr.getRecord(id);
        assertEq(rec.kind, cr.KIND_FACILITY());
        assertTrue(rec.governanceLocked);
        assertFalse(rec.disposed);
    }

    function test_mint_onlyGovernance() public {
        vm.expectRevert(CorpusRegistry.NotGovernance.selector);
        cr.mint(cr.KIND_REAL_PROPERTY(), "did:web:x", bytes32(0), keccak256("a"), bytes32(0));
    }

    function test_mint_rejectsZeroKind() public {
        vm.prank(address(gov));
        vm.expectRevert(abi.encodeWithSelector(CorpusRegistry.InvalidKind.selector, uint8(0)));
        cr.mint(0, "did:web:x", bytes32(0), keccak256("a"), bytes32(0));
    }

    function test_mint_rejectsEmptyHolder() public {
        vm.prank(address(gov));
        vm.expectRevert(CorpusRegistry.EmptyHolderDid.selector);
        cr.mint(cr.KIND_IP(), "", bytes32(0), keccak256("a"), bytes32(0));
    }

    function test_mint_rejectsEmptyAttestation() public {
        vm.prank(address(gov));
        vm.expectRevert(CorpusRegistry.EmptyAttestation.selector);
        cr.mint(cr.KIND_IP(), "did:web:x", bytes32(0), bytes32(0), bytes32(0));
    }

    function test_transferFrom_revertsSoulbound() public {
        uint256 id = _mintShrine();
        vm.expectRevert(CorpusRegistry.Soulbound.selector);
        cr.transferFrom(address(this), alice, id);
    }

    function test_updateMetadata_byGovernance() public {
        uint256 id = _mintShrine();
        vm.prank(address(gov));
        cr.updateMetadata(id, keccak256("attestation-2"), keccak256("ipfs-cid-v2"));
        CorpusRegistry.CorpusRecord memory rec = cr.getRecord(id);
        assertEq(rec.attestationHash, keccak256("attestation-2"));
        assertEq(rec.contentCid, keccak256("ipfs-cid-v2"));
    }

    function test_updateMetadata_rejectsEmptyAttestation() public {
        uint256 id = _mintShrine();
        vm.prank(address(gov));
        vm.expectRevert(CorpusRegistry.EmptyAttestation.selector);
        cr.updateMetadata(id, bytes32(0), keccak256("ipfs-cid-v2"));
    }

    function test_setLock_byGovernance() public {
        uint256 id = _mintShrine();
        vm.prank(address(gov));
        cr.setLock(id, false);
        CorpusRegistry.CorpusRecord memory rec = cr.getRecord(id);
        assertFalse(rec.governanceLocked);
    }

    function test_flagDisposed_blocksFurtherUpdates() public {
        uint256 id = _mintShrine();
        vm.startPrank(address(gov));
        cr.flagDisposed(id, keccak256("sold-for-renovation"));
        vm.expectRevert(CorpusRegistry.AlreadyDisposed.selector);
        cr.updateMetadata(id, keccak256("attestation-2"), bytes32(0));
        vm.expectRevert(CorpusRegistry.AlreadyDisposed.selector);
        cr.setLock(id, false);
        vm.expectRevert(CorpusRegistry.AlreadyDisposed.selector);
        cr.flagDisposed(id, bytes32(0));
        vm.stopPrank();
    }

    function test_locked_unknownTokenReverts() public {
        vm.expectRevert(abi.encodeWithSelector(CorpusRegistry.UnknownToken.selector, uint256(99)));
        cr.locked(99);
    }
}
