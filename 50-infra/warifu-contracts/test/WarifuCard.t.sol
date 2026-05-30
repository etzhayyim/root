// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
pragma solidity ^0.8.26;

import {WarifuCard} from "../src/WarifuCard.sol";

interface Vm {
    function prank(address) external;
    function expectRevert(bytes4) external;
}

/// @title WarifuCard invariants — soulbound card identity + access control (ADR-2605302000)
contract WarifuCardTest {
    Vm constant vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

    WarifuCard card;
    address council = address(0xC0);
    address issuer = address(0x155);
    address holder = address(0x11); // ERC-4337 smart account
    address rando = address(0x000000000000000000000000000000000000bEEF);
    bytes32 did = keccak256("did:web:etzhayyim.com");

    function setUp() public {
        card = new WarifuCard(council);
        vm.prank(council);
        card.setIssuer(issuer, true);
    }

    // --- issuance: soulbound + bound to smart account ---
    function testIssueSoulbound() public {
        vm.prank(issuer);
        uint256 id = card.issue(holder, did, false);
        require(id == 1, "first token id != 1");
        require(card.locked(id), "card must be soulbound (locked)");
        require(card.smartAccountOf(id) == holder, "smart account mismatch");
        (address sa,, bool credit, bool active) = card.cards(id);
        require(sa == holder && !credit && active, "card record mismatch");
    }

    // --- only an authorized issuer may issue ---
    function testOnlyIssuerCanIssue() public {
        vm.prank(rando);
        vm.expectRevert(WarifuCard.NotIssuer.selector);
        card.issue(holder, did, false);
    }

    // --- only council may set issuers ---
    function testOnlyCouncilSetsIssuer() public {
        vm.prank(rando);
        vm.expectRevert(WarifuCard.NotCouncil.selector);
        card.setIssuer(rando, true);
    }

    // --- holder may deactivate their own card; reads then revert CardInactive ---
    function testDeactivateByHolder() public {
        vm.prank(issuer);
        uint256 id = card.issue(holder, did, true);
        vm.prank(holder);
        card.deactivate(id);
        vm.expectRevert(WarifuCard.CardInactive.selector);
        card.smartAccountOf(id);
    }

    // --- council may deactivate (e.g. lost device) ---
    function testDeactivateByCouncil() public {
        vm.prank(issuer);
        uint256 id = card.issue(holder, did, false);
        vm.prank(council);
        card.deactivate(id);
        (,,, bool active) = card.cards(id);
        require(!active, "council deactivate failed");
    }

    // --- a third party may NOT seize/deactivate a binding ---
    function testDeactivateUnauthorizedReverts() public {
        vm.prank(issuer);
        uint256 id = card.issue(holder, did, false);
        vm.prank(rando);
        vm.expectRevert(WarifuCard.NotCouncil.selector);
        card.deactivate(id);
    }

    // --- soulbound invariant holds for every id (no unlock path) ---
    function testAllCardsPermanentlyLocked() public view {
        require(card.locked(0) && card.locked(1) && card.locked(999), "locked must always be true");
    }

    // --- zero-fee constants are immutable on the identity contract too ---
    function testZeroFeeConstants() public view {
        require(card.INTERCHANGE_BPS() == 0 && card.MERCHANT_FEE_BPS() == 0, "fee bps must be 0");
    }
}
