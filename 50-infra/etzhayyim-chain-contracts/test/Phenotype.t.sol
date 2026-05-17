// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {Fixture} from "./_helpers/Fixture.sol";
import {Phenotype} from "../src/Phenotype.sol";

contract PhenotypeTest is Fixture {
    function setUp() public {
        _deployStack();
        vm.prank(address(gov));
        pn.registerCell(cellAddr, keccak256("eligibility-cell-0"));
    }

    function _id() internal returns (uint256) {
        return _joinAndAttest(alice, "did:web:alice.example.com");
    }

    function test_setMultiplier_happyPath() public {
        uint256 id = _id();
        uint64 expiresAt = uint64(block.timestamp + 1 hours);
        bytes32 evid = bytes32(uint256(0xCD));
        bytes32 inner = pn.payloadHash(id, 12_000, 1, 0, expiresAt, evid, cellAddr);
        bytes memory sig = _signEip191(cellKey, inner);
        pn.setMultiplier(id, 12_000, 1, 0, expiresAt, evid, cellAddr, sig);
        assertEq(pn.getMultiplierBps(id), 12_000);
        assertEq(pn.expectedNonce(cellAddr), 1);
    }

    function test_setMultiplier_unknownCell() public {
        uint256 id = _id();
        uint64 expiresAt = uint64(block.timestamp + 1 hours);
        bytes32 inner = pn.payloadHash(id, 12_000, 1, 0, expiresAt, bytes32(0), address(0xDEAD));
        bytes memory sig = _signEip191(cellKey, inner);
        vm.expectRevert(abi.encodeWithSelector(Phenotype.UnknownCell.selector, address(0xDEAD)));
        pn.setMultiplier(id, 12_000, 1, 0, expiresAt, bytes32(0), address(0xDEAD), sig);
    }

    function test_setMultiplier_expired() public {
        uint256 id = _id();
        uint64 expiresAt = uint64(block.timestamp);
        vm.warp(block.timestamp + 2);
        bytes32 inner = pn.payloadHash(id, 12_000, 1, 0, expiresAt, bytes32(0), cellAddr);
        bytes memory sig = _signEip191(cellKey, inner);
        vm.expectRevert(Phenotype.ExpiredSignature.selector);
        pn.setMultiplier(id, 12_000, 1, 0, expiresAt, bytes32(0), cellAddr, sig);
    }

    function test_setMultiplier_badNonce() public {
        uint256 id = _id();
        uint64 expiresAt = uint64(block.timestamp + 1 hours);
        bytes32 inner = pn.payloadHash(id, 12_000, 1, 7, expiresAt, bytes32(0), cellAddr);
        bytes memory sig = _signEip191(cellKey, inner);
        vm.expectRevert(abi.encodeWithSelector(Phenotype.BadNonce.selector, uint64(0), uint64(7)));
        pn.setMultiplier(id, 12_000, 1, 7, expiresAt, bytes32(0), cellAddr, sig);
    }

    function test_setMultiplier_outOfBand_underFloor() public {
        uint256 id = _id();
        uint64 expiresAt = uint64(block.timestamp + 1 hours);
        bytes32 inner = pn.payloadHash(id, 4_000, 1, 0, expiresAt, bytes32(0), cellAddr);
        bytes memory sig = _signEip191(cellKey, inner);
        vm.expectRevert(abi.encodeWithSelector(Phenotype.OutOfBand.selector, uint16(4_000), uint16(5_000), uint16(20_000)));
        pn.setMultiplier(id, 4_000, 1, 0, expiresAt, bytes32(0), cellAddr, sig);
    }

    function test_setMultiplier_outOfBand_overCeiling() public {
        uint256 id = _id();
        uint64 expiresAt = uint64(block.timestamp + 1 hours);
        bytes32 inner = pn.payloadHash(id, 30_000, 1, 0, expiresAt, bytes32(0), cellAddr);
        bytes memory sig = _signEip191(cellKey, inner);
        vm.expectRevert(abi.encodeWithSelector(Phenotype.OutOfBand.selector, uint16(30_000), uint16(5_000), uint16(20_000)));
        pn.setMultiplier(id, 30_000, 1, 0, expiresAt, bytes32(0), cellAddr, sig);
    }

    function test_setMultiplier_invalidSignature() public {
        uint256 id = _id();
        uint64 expiresAt = uint64(block.timestamp + 1 hours);
        bytes32 inner = pn.payloadHash(id, 12_000, 1, 0, expiresAt, bytes32(0), cellAddr);
        // Sign with a different key to mismatch.
        bytes memory sig = _signEip191(uint256(keccak256("wrong-key")), inner);
        vm.expectRevert(Phenotype.InvalidSignature.selector);
        pn.setMultiplier(id, 12_000, 1, 0, expiresAt, bytes32(0), cellAddr, sig);
    }

    function test_getMultiplierBps_defaultNeutral() public {
        uint256 id = _id();
        assertEq(pn.getMultiplierBps(id), 10_000);
    }

    function test_registerCell_onlyGovernance() public {
        vm.expectRevert(Phenotype.NotGovernance.selector);
        pn.registerCell(address(0xBEEF), keccak256("nope"));
    }

    function test_revokeCell_blocksFutureUpdates() public {
        uint256 id = _id();
        vm.prank(address(gov));
        pn.revokeCell(cellAddr, bytes32(uint256(0xDEAD)));
        uint64 expiresAt = uint64(block.timestamp + 1 hours);
        bytes32 inner = pn.payloadHash(id, 12_000, 1, 0, expiresAt, bytes32(0), cellAddr);
        bytes memory sig = _signEip191(cellKey, inner);
        vm.expectRevert(abi.encodeWithSelector(Phenotype.UnknownCell.selector, cellAddr));
        pn.setMultiplier(id, 12_000, 1, 0, expiresAt, bytes32(0), cellAddr, sig);
    }
}
