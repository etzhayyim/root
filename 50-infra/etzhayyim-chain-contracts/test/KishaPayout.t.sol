// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {KishaPayout, IERC20} from "../src/base/KishaPayout.sol";

contract MockUsdc is IERC20 {
    mapping(address => uint256) public bal;
    mapping(address => mapping(address => uint256)) internal _allow;

    function balanceOf(address a) external view returns (uint256) { return bal[a]; }
    function allowance(address o, address s) external view returns (uint256) { return _allow[o][s]; }

    function mint(address to, uint256 amt) external { bal[to] += amt; }

    function approve(address spender, uint256 amt) external returns (bool) {
        _allow[msg.sender][spender] = amt;
        return true;
    }

    function transferFrom(address from, address to, uint256 amt) external returns (bool) {
        require(_allow[from][msg.sender] >= amt, "allow");
        require(bal[from] >= amt, "bal");
        unchecked {
            _allow[from][msg.sender] -= amt;
            bal[from] -= amt;
            bal[to] += amt;
        }
        return true;
    }
}

contract KishaPayoutTest is Test {
    MockUsdc usdc;
    KishaPayout kp;

    address constant TREASURY = address(0xCAFE);
    address constant KISHA_STREAM = address(0xC0FFEE);
    address constant RECIPIENT = address(0xBEEF);

    // 3 relayer keys
    uint256 internal k1 = uint256(keccak256("r1"));
    uint256 internal k2 = uint256(keccak256("r2"));
    uint256 internal k3 = uint256(keccak256("r3"));
    address r1; address r2; address r3;

    function setUp() public {
        r1 = vm.addr(k1);
        r2 = vm.addr(k2);
        r3 = vm.addr(k3);
        // Sort signers ascending for the strict-monotone check.
        (address[] memory sorted) = _sort3(r1, r2, r3);
        usdc = new MockUsdc();
        kp = new KishaPayout(IERC20(address(usdc)), TREASURY, KISHA_STREAM, sorted, 2);

        usdc.mint(TREASURY, 1_000_000_000);
        vm.prank(TREASURY);
        usdc.approve(address(kp), type(uint256).max);
    }

    function _sort3(address a, address b, address c) internal pure returns (address[] memory out) {
        out = new address[](3);
        out[0] = a; out[1] = b; out[2] = c;
        // bubble sort
        for (uint256 i = 0; i < 3; ++i) {
            for (uint256 j = i + 1; j < 3; ++j) {
                if (out[i] > out[j]) {
                    (out[i], out[j]) = (out[j], out[i]);
                }
            }
        }
    }

    function _ticketId(uint256 tokenId, uint64 seq) internal view returns (bytes32) {
        return keccak256(abi.encodePacked(KISHA_STREAM, tokenId, seq));
    }

    function _payloadHash(
        bytes32 ticketId, uint256 tokenId, address recipient, uint256 amount, uint64 expiresAt
    ) internal view returns (bytes32) {
        bytes32 inner = keccak256(abi.encode(
            address(kp), block.chainid, ticketId, tokenId, recipient, amount, expiresAt
        ));
        return keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", inner));
    }

    function _sig(uint256 pk, bytes32 envelope) internal pure returns (bytes memory) {
        (uint8 v, bytes32 rSig, bytes32 sSig) = vm.sign(pk, envelope);
        return abi.encodePacked(rSig, sSig, v);
    }

    function test_fulfill_with2of3_transfers() public {
        bytes32 ticket = _ticketId(1, 1);
        uint256 amt = 1_000_000;
        uint64 exp = uint64(block.timestamp + 1 hours);
        bytes32 env = _payloadHash(ticket, 1, RECIPIENT, amt, exp);

        // Build sorted signer set with 2 of 3
        address[] memory signers = new address[](2);
        bytes[] memory sigs = new bytes[](2);
        if (r1 < r2) { signers[0] = r1; signers[1] = r2; sigs[0] = _sig(k1, env); sigs[1] = _sig(k2, env); }
        else         { signers[0] = r2; signers[1] = r1; sigs[0] = _sig(k2, env); sigs[1] = _sig(k1, env); }

        kp.fulfill(ticket, 1, RECIPIENT, amt, exp, sigs, signers);
        assertEq(usdc.balanceOf(RECIPIENT), amt);
        assertTrue(kp.fulfilled(ticket));
    }

    function test_fulfill_doubleFulfill_reverts() public {
        bytes32 ticket = _ticketId(1, 1);
        uint256 amt = 1_000_000;
        uint64 exp = uint64(block.timestamp + 1 hours);
        bytes32 env = _payloadHash(ticket, 1, RECIPIENT, amt, exp);

        address[] memory signers = new address[](2);
        bytes[] memory sigs = new bytes[](2);
        if (r1 < r2) { signers[0] = r1; signers[1] = r2; sigs[0] = _sig(k1, env); sigs[1] = _sig(k2, env); }
        else         { signers[0] = r2; signers[1] = r1; sigs[0] = _sig(k2, env); sigs[1] = _sig(k1, env); }

        kp.fulfill(ticket, 1, RECIPIENT, amt, exp, sigs, signers);
        vm.expectRevert(abi.encodeWithSelector(KishaPayout.AlreadyFulfilled.selector, ticket));
        kp.fulfill(ticket, 1, RECIPIENT, amt, exp, sigs, signers);
    }

    function test_fulfill_belowThreshold_reverts() public {
        bytes32 ticket = _ticketId(1, 1);
        uint256 amt = 1_000_000;
        uint64 exp = uint64(block.timestamp + 1 hours);
        bytes32 env = _payloadHash(ticket, 1, RECIPIENT, amt, exp);

        address[] memory signers = new address[](1);
        bytes[] memory sigs = new bytes[](1);
        signers[0] = r1;
        sigs[0] = _sig(k1, env);

        vm.expectRevert(KishaPayout.InvalidSignatureCount.selector);
        kp.fulfill(ticket, 1, RECIPIENT, amt, exp, sigs, signers);
    }

    function test_fulfill_expired_reverts() public {
        bytes32 ticket = _ticketId(1, 1);
        uint256 amt = 1_000_000;
        uint64 exp = uint64(block.timestamp);
        vm.warp(block.timestamp + 2);
        bytes32 env = _payloadHash(ticket, 1, RECIPIENT, amt, exp);

        address[] memory signers = new address[](2);
        bytes[] memory sigs = new bytes[](2);
        if (r1 < r2) { signers[0] = r1; signers[1] = r2; sigs[0] = _sig(k1, env); sigs[1] = _sig(k2, env); }
        else         { signers[0] = r2; signers[1] = r1; sigs[0] = _sig(k2, env); sigs[1] = _sig(k1, env); }

        vm.expectRevert(KishaPayout.ExpiredTicket.selector);
        kp.fulfill(ticket, 1, RECIPIENT, amt, exp, sigs, signers);
    }

    function test_fulfill_unsortedSigners_reverts() public {
        bytes32 ticket = _ticketId(1, 1);
        uint256 amt = 1_000_000;
        uint64 exp = uint64(block.timestamp + 1 hours);
        bytes32 env = _payloadHash(ticket, 1, RECIPIENT, amt, exp);

        // Force descending order to trigger DuplicateSigner check (s <= previous).
        address[] memory signers = new address[](2);
        bytes[] memory sigs = new bytes[](2);
        if (r1 < r2) { signers[0] = r2; signers[1] = r1; sigs[0] = _sig(k2, env); sigs[1] = _sig(k1, env); }
        else         { signers[0] = r1; signers[1] = r2; sigs[0] = _sig(k1, env); sigs[1] = _sig(k2, env); }

        vm.expectRevert(KishaPayout.DuplicateSigner.selector);
        kp.fulfill(ticket, 1, RECIPIENT, amt, exp, sigs, signers);
    }

    function test_fulfill_unknownSigner_reverts() public {
        bytes32 ticket = _ticketId(1, 1);
        uint256 amt = 1_000_000;
        uint64 exp = uint64(block.timestamp + 1 hours);
        bytes32 env = _payloadHash(ticket, 1, RECIPIENT, amt, exp);

        uint256 kBad = uint256(keccak256("bad"));
        address rBad = vm.addr(kBad);
        // Place rBad in sorted position, paired with r1 or r2.
        address other = r1 < r2 ? r1 : r2;
        uint256 kOther = r1 < r2 ? k1 : k2;
        address[] memory signers = new address[](2);
        bytes[] memory sigs = new bytes[](2);
        if (other < rBad) {
            signers[0] = other; signers[1] = rBad;
            sigs[0] = _sig(kOther, env); sigs[1] = _sig(kBad, env);
        } else {
            signers[0] = rBad;  signers[1] = other;
            sigs[0] = _sig(kBad, env); sigs[1] = _sig(kOther, env);
        }

        vm.expectRevert(abi.encodeWithSelector(KishaPayout.UnknownSigner.selector, rBad));
        kp.fulfill(ticket, 1, RECIPIENT, amt, exp, sigs, signers);
    }
}
