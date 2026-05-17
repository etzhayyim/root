// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {Fixture} from "./_helpers/Fixture.sol";
import {KishaStream} from "../src/KishaStream.sol";
import {Phenotype} from "../src/Phenotype.sol";

contract KishaStreamTest is Fixture {
    function setUp() public {
        _deployStack();
    }

    function test_accruedNow_zeroBeforeWindow() public {
        uint256 id = _joinAndAttest(alice, "did:web:alice.example.com");
        assertEq(ks.accruedNow(id), 0);
    }

    function test_accruedNow_afterOneDay_matchesBaseRate() public {
        uint256 id = _joinAndAttest(alice, "did:web:alice.example.com");
        vm.warp(block.timestamp + 1 days);
        assertEq(ks.accruedNow(id), 1_000_000); // 1 USDC, 6 decimals
    }

    function test_accruedNow_zeroWhenInactive() public {
        uint256 id = _joinAndAttest(alice, "did:web:alice.example.com");
        vm.warp(block.timestamp + 31 days); // active window expired
        assertEq(ks.accruedNow(id), 0);
    }

    function test_claim_nonHolder_reverts() public {
        uint256 id = _joinAndAttest(alice, "did:web:alice.example.com");
        vm.warp(block.timestamp + 1 days);
        vm.prank(bob);
        vm.expectRevert(KishaStream.NotHolder.selector);
        ks.claim(id, alice, 0);
    }

    function test_claim_revoked_reverts() public {
        uint256 id = _joinAndAttest(alice, "did:web:alice.example.com");
        vm.warp(block.timestamp + 1 days);
        vm.prank(officer);
        r.revoke(id, bytes32(uint256(0xDEAD)));
        vm.prank(alice);
        // KishaStream.claim checks `r.revoked` before `isActive`, so the
        // revoked branch is hit first.
        vm.expectRevert(KishaStream.TokenRevoked.selector);
        ks.claim(id, alice, 0);
    }

    function test_claim_inactive_reverts() public {
        uint256 id = _joinAndAttest(alice, "did:web:alice.example.com");
        vm.warp(block.timestamp + 40 days);
        vm.prank(alice);
        vm.expectRevert(KishaStream.NotActive.selector);
        ks.claim(id, alice, 0);
    }

    function test_claim_full_advancesLastClaimedAt() public {
        uint256 id = _joinAndAttest(alice, "did:web:alice.example.com");
        vm.warp(block.timestamp + 2 days);
        vm.prank(alice);
        (bytes32 ticketId, uint256 amount) = ks.claim(id, alice, 0);
        assertEq(amount, 2_000_000);
        assertTrue(ticketId != bytes32(0));
        // After full claim, accrual resets.
        assertEq(ks.accruedNow(id), 0);
    }

    function test_claim_partial_leavesRemainder() public {
        uint256 id = _joinAndAttest(alice, "did:web:alice.example.com");
        vm.warp(block.timestamp + 2 days);
        vm.prank(alice);
        (, uint256 amount) = ks.claim(id, alice, 500_000); // 0.5 USDC
        assertEq(amount, 500_000);
        // 1.5 USDC worth of accrual remains.
        assertEq(ks.accruedNow(id), 1_500_000);
    }

    function test_phenotypeNeutral_whenUnset() public {
        // With phenotype contract unwired, accrual is base.
        uint256 id = _joinAndAttest(alice, "did:web:alice.example.com");
        vm.warp(block.timestamp + 1 days);
        assertEq(ks.accruedNow(id), 1_000_000);
    }

    function test_phenotype_halvesOnMin() public {
        uint256 id = _joinAndAttest(alice, "did:web:alice.example.com");
        // Wire Phenotype via Governance bypass: we have c.governance = gov;
        // KishaStream.setPhenotype checks msg.sender == c.governance().
        // Simulate by pranking as that address.
        vm.prank(address(gov));
        ks.setPhenotype(pn);

        // Phenotype.registerCell requires governance too; same prank trick.
        vm.prank(address(gov));
        pn.registerCell(cellAddr, keccak256("test"));

        // Cell-signed update to floor (5000 bps == 0.5x)
        uint64 epoch = 1;
        uint64 nonce = 0;
        uint64 expiresAt = uint64(block.timestamp + 1 hours);
        bytes32 evid = bytes32(0);

        bytes32 inner = pn.payloadHash(id, 5_000, epoch, nonce, expiresAt, evid, cellAddr);
        bytes memory sig = _signEip191(cellKey, inner);
        pn.setMultiplier(id, 5_000, epoch, nonce, expiresAt, evid, cellAddr, sig);

        vm.warp(block.timestamp + 1 days);
        // base 1 USDC × 0.5 = 0.5 USDC
        assertEq(ks.accruedNow(id), 500_000);
    }

    function test_phenotype_doublesOnMax() public {
        uint256 id = _joinAndAttest(alice, "did:web:alice.example.com");

        vm.prank(address(gov));
        ks.setPhenotype(pn);
        vm.prank(address(gov));
        pn.registerCell(cellAddr, keccak256("test"));

        uint64 epoch = 1;
        uint64 nonce = 0;
        uint64 expiresAt = uint64(block.timestamp + 1 hours);
        bytes32 evid = bytes32(0);

        bytes32 inner = pn.payloadHash(id, 20_000, epoch, nonce, expiresAt, evid, cellAddr);
        bytes memory sig = _signEip191(cellKey, inner);
        pn.setMultiplier(id, 20_000, epoch, nonce, expiresAt, evid, cellAddr, sig);

        vm.warp(block.timestamp + 1 days);
        assertEq(ks.accruedNow(id), 2_000_000);
    }

    function test_setBaseRate_onlyGovernance() public {
        vm.expectRevert(KishaStream.NotGovernance.selector);
        ks.setBaseRate(2_000_000);
    }
}
