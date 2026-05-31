// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
pragma solidity ^0.8.26;

import {SettlementRouter} from "../src/SettlementRouter.sol";
import {CreditLine} from "../src/CreditLine.sol";
import {WarifuCard} from "../src/WarifuCard.sol";

interface Vm {
    function prank(address) external;
    function expectEmit(bool, bool, bool, bool) external;
}

contract MockUSDC {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    function mint(address to, uint256 a) external { balanceOf[to] += a; }
    function approve(address s, uint256 a) external returns (bool) { allowance[msg.sender][s] = a; return true; }
    function transferFrom(address f, address t, uint256 a) external returns (bool) {
        allowance[f][msg.sender] -= a; balanceOf[f] -= a; balanceOf[t] += a; return true;
    }
}

/// @title Event-emission coverage — Settled / Phase2Enabled / Locked (ADR-2605302000)
contract EventsTest {
    Vm constant vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

    // mirror the contract event signatures so expectEmit can match by topic+data
    event Settled(bytes32 indexed authId, address indexed merchant, uint256 amount, string funding);
    event Phase2Enabled(bytes32 adrAmendmentRecord);
    event Locked(uint256 tokenId);

    MockUSDC usdc;
    CreditLine credit;
    SettlementRouter router;
    WarifuCard card;
    address council = address(0xC0);
    address issuer = address(0x155);
    address holder = address(0x11);
    address merchant = address(0x3E);
    address wakaiFloat = address(0xFA);
    bytes32 did = keccak256("did:web:etzhayyim.com");

    function setUp() public {
        usdc = new MockUSDC();
        credit = new CreditLine(wakaiFloat, council);
        router = new SettlementRouter(address(usdc), address(credit), wakaiFloat, council);
        card = new WarifuCard(council);
        vm.prank(council);
        credit.setRouter(address(router));
        vm.prank(council);
        card.setIssuer(issuer, true);
    }

    // --- debit settlement emits Settled(authId, merchant, amount, "debit") ---
    function testDebitEmitsSettled() public {
        usdc.mint(holder, 500_000);
        vm.prank(holder);
        usdc.approve(address(router), 500_000);

        vm.expectEmit(true, true, false, true);
        emit Settled(bytes32("e1"), merchant, 300_000, "debit");
        router.settleDebit(bytes32("e1"), holder, merchant, 300_000, "internal-purchase");
    }

    // --- credit settlement emits Settled(... "credit") ---
    function testCreditEmitsSettled() public {
        vm.prank(council);
        credit.setLimit(holder, 1_000_000);
        usdc.mint(wakaiFloat, 500_000);
        vm.prank(wakaiFloat);
        usdc.approve(address(router), 500_000);

        vm.expectEmit(true, true, false, true);
        emit Settled(bytes32("e2"), merchant, 200_000, "credit");
        router.settleCredit(bytes32("e2"), holder, merchant, 200_000, "internal-purchase");
    }

    // --- enablePhase2 emits Phase2Enabled with the amendment record ---
    function testEnablePhase2EmitsEvent() public {
        vm.expectEmit(false, false, false, true);
        emit Phase2Enabled(bytes32("amendment-rec"));
        vm.prank(council);
        router.enablePhase2(bytes32("amendment-rec"));
    }

    // --- issuing a card emits Locked(tokenId) (soulbound from birth) ---
    function testIssueEmitsLocked() public {
        vm.expectEmit(false, false, false, true);
        emit Locked(1);
        vm.prank(issuer);
        card.issue(holder, did, false);
    }

    // --- multiple issues produce sequential ids, each soulbound, credit flag preserved ---
    function testMultipleIssueSequentialIds() public {
        vm.prank(issuer);
        uint256 id1 = card.issue(holder, did, false);
        vm.prank(issuer);
        uint256 id2 = card.issue(merchant, did, true);
        require(id1 == 1 && id2 == 2, "ids must increment");
        (, , bool credit1, ) = card.cards(id1);
        (, , bool credit2, ) = card.cards(id2);
        require(!credit1 && credit2, "credit flag not preserved per card");
        require(card.locked(id1) && card.locked(id2), "both must be soulbound");
    }
}
