// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {Fixture} from "./_helpers/Fixture.sol";
import {TreasuryMirror} from "../src/TreasuryMirror.sol";

contract TreasuryMirrorTest is Fixture {
    // Cached tier constants — read once at setUp so `vm.prank` /
    // `vm.expectRevert` are never consumed by a getter in argument
    // position.
    uint8 internal TIER_RESERVE;

    function setUp() public {
        _deployStack();
        TIER_RESERVE = tm.TIER_RESERVE();
        vm.prank(address(gov));
        tm.registerOracle(oracleAddr, keccak256("nav-oracle-0"));
    }

    function _signAndPost(uint8 tier, uint256 amount, uint64 epoch, uint64 nonce) internal {
        uint64 exp = uint64(block.timestamp + 1 hours);
        bytes32 inner = tm.payloadHash(tier, amount, epoch, nonce, exp, oracleAddr);
        bytes memory sig = _signEip191(oracleKey, inner);
        tm.updateNAV(tier, amount, epoch, nonce, exp, oracleAddr, sig);
    }

    function test_updateNAV_happyPath() public {
        _signAndPost(TIER_RESERVE, 1_000_000_000, 1, 0);
        assertEq(tm.tierLatest(TIER_RESERVE), 1_000_000_000);
        assertEq(tm.tierFilledSamples(TIER_RESERVE), 1);
        assertEq(tm.oracleNonce(oracleAddr), 1);
    }

    function test_updateNAV_invalidTier() public {
        uint64 exp = uint64(block.timestamp + 1 hours);
        bytes32 inner = tm.payloadHash(99, 1_000, 1, 0, exp, oracleAddr);
        bytes memory sig = _signEip191(oracleKey, inner);
        vm.expectRevert(abi.encodeWithSelector(TreasuryMirror.InvalidTier.selector, uint8(99)));
        tm.updateNAV(99, 1_000, 1, 0, exp, oracleAddr, sig);
    }

    function test_updateNAV_unknownOracle() public {
        uint256 fakeKey = uint256(keccak256("nope"));
        address fakeAddr = vm.addr(fakeKey);
        uint64 exp = uint64(block.timestamp + 1 hours);
        bytes32 inner = tm.payloadHash(TIER_RESERVE, 1_000, 1, 0, exp, fakeAddr);
        bytes memory sig = _signEip191(fakeKey, inner);
        vm.expectRevert(abi.encodeWithSelector(TreasuryMirror.UnknownOracle.selector, fakeAddr));
        tm.updateNAV(TIER_RESERVE, 1_000, 1, 0, exp, fakeAddr, sig);
    }

    function test_updateNAV_expired() public {
        uint64 exp = uint64(block.timestamp);
        vm.warp(block.timestamp + 2);
        bytes32 inner = tm.payloadHash(TIER_RESERVE, 1_000, 1, 0, exp, oracleAddr);
        bytes memory sig = _signEip191(oracleKey, inner);
        vm.expectRevert(TreasuryMirror.ExpiredSignature.selector);
        tm.updateNAV(TIER_RESERVE, 1_000, 1, 0, exp, oracleAddr, sig);
    }

    function test_updateNAV_badNonce() public {
        uint64 exp = uint64(block.timestamp + 1 hours);
        bytes32 inner = tm.payloadHash(TIER_RESERVE, 1_000, 1, 5, exp, oracleAddr);
        bytes memory sig = _signEip191(oracleKey, inner);
        vm.expectRevert(abi.encodeWithSelector(TreasuryMirror.BadNonce.selector, uint64(0), uint64(5)));
        tm.updateNAV(TIER_RESERVE, 1_000, 1, 5, exp, oracleAddr, sig);
    }

    function test_reserveAverage_overSamples() public {
        // Post 3 samples: 100, 200, 300 → avg 200
        _signAndPost(TIER_RESERVE, 100, 1, 0);
        _signAndPost(TIER_RESERVE, 200, 2, 1);
        _signAndPost(TIER_RESERVE, 300, 3, 2);
        assertEq(tm.reserveAverage(), 200);
    }

    function test_monthlyEnvelope_appliesKappa() public {
        // kappa_bps default = 300 (3%)
        // monthly = avg * 300 / 10_000 / 12 = avg * 0.0025
        // For avg=1_200_000, expect 3_000.
        _signAndPost(TIER_RESERVE, 1_200_000, 1, 0);
        assertEq(tm.monthlyEnvelopeUsdc(), 3_000);
    }

    function test_monthlyEnvelope_clampsKappaToCeiling() public {
        // Push kappa above ceiling and confirm the envelope clamps.
        vm.prank(address(gov));
        c.setMutable(K_KAPPA, bytes32(uint256(9_999)));
        _signAndPost(TIER_RESERVE, 1_200_000, 1, 0);
        // ceiling = 500 → annual = avg * 500/10_000 = avg * 0.05; monthly /12
        // For avg=1_200_000, expect 1_200_000 * 500 / 10_000 / 12 = 5_000
        assertEq(tm.monthlyEnvelopeUsdc(), 5_000);
    }

    function test_registerOracle_onlyGovernance() public {
        vm.expectRevert(TreasuryMirror.NotGovernance.selector);
        tm.registerOracle(address(0xBEEF), keccak256("nope"));
    }
}
