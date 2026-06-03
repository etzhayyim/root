// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test, console} from "forge-std/Test.sol";
import {TestUSDC} from "../src/TestUSDC.sol";

contract TestUSDCTest is Test {
    TestUSDC public token;

    address public owner = makeAddr("owner");
    address public masterMinter = makeAddr("masterMinter");
    address public pauser = makeAddr("pauser");
    address public blacklister = makeAddr("blacklister");
    address public minter = makeAddr("minter");
    address public alice = makeAddr("alice");
    address public bob = makeAddr("bob");

    uint256 public constant MINT_CAP = 100_000_000_000 * 1e6; // 100B
    uint256 public constant INITIAL_MINT = 10_000_000 * 1e6; // 10M

    function setUp() public {
        token = new TestUSDC("Etzhayyim Computing Credits", "GCC", "USD", masterMinter, pauser, blacklister, owner);

        // Configure minter
        vm.prank(masterMinter);
        token.configureMinter(minter, MINT_CAP);

        // Mint initial supply to alice
        vm.prank(minter);
        token.mint(alice, INITIAL_MINT);
    }

    // ──────────────────────────────────────────────
    // ERC-20 Metadata
    // ──────────────────────────────────────────────

    function test_name() public view {
        assertEq(token.name(), "Etzhayyim Computing Credits");
    }

    function test_symbol() public view {
        assertEq(token.symbol(), "GCC");
    }

    function test_decimals() public view {
        assertEq(token.decimals(), 6);
    }

    function test_version() public view {
        assertEq(token.version(), "2");
    }

    function test_currency() public view {
        assertEq(token.currency(), "USD");
    }

    function test_totalSupply() public view {
        assertEq(token.totalSupply(), INITIAL_MINT);
    }

    // ──────────────────────────────────────────────
    // ERC-20 Transfer
    // ──────────────────────────────────────────────

    function test_transfer() public {
        uint256 amount = 1_000 * 1e6;
        vm.prank(alice);
        assertTrue(token.transfer(bob, amount));
        assertEq(token.balanceOf(bob), amount);
        assertEq(token.balanceOf(alice), INITIAL_MINT - amount);
    }

    function test_transfer_reverts_insufficient_balance() public {
        vm.prank(alice);
        vm.expectRevert("ERC20: transfer amount exceeds balance");
        token.transfer(bob, INITIAL_MINT + 1);
    }

    function test_transfer_emits_event() public {
        uint256 amount = 500 * 1e6;
        vm.expectEmit(true, true, false, true);
        emit TestUSDC.Transfer(alice, bob, amount);
        vm.prank(alice);
        token.transfer(bob, amount);
    }

    // ──────────────────────────────────────────────
    // ERC-20 Approve / TransferFrom
    // ──────────────────────────────────────────────

    function test_approve_and_transferFrom() public {
        uint256 amount = 2_000 * 1e6;
        vm.prank(alice);
        assertTrue(token.approve(bob, amount));
        assertEq(token.allowance(alice, bob), amount);

        vm.prank(bob);
        assertTrue(token.transferFrom(alice, bob, amount));
        assertEq(token.balanceOf(bob), amount);
        assertEq(token.allowance(alice, bob), 0);
    }

    function test_increaseAllowance() public {
        vm.prank(alice);
        token.approve(bob, 100e6);

        vm.prank(alice);
        assertTrue(token.increaseAllowance(bob, 50e6));
        assertEq(token.allowance(alice, bob), 150e6);
    }

    function test_decreaseAllowance() public {
        vm.prank(alice);
        token.approve(bob, 100e6);

        vm.prank(alice);
        assertTrue(token.decreaseAllowance(bob, 30e6));
        assertEq(token.allowance(alice, bob), 70e6);
    }

    function test_decreaseAllowance_reverts_below_zero() public {
        vm.prank(alice);
        token.approve(bob, 100e6);

        vm.prank(alice);
        vm.expectRevert("ERC20: decreased allowance below zero");
        token.decreaseAllowance(bob, 101e6);
    }

    // ──────────────────────────────────────────────
    // Minting
    // ──────────────────────────────────────────────

    function test_mint() public {
        uint256 amount = 5_000 * 1e6;
        vm.prank(minter);
        assertTrue(token.mint(bob, amount));
        assertEq(token.balanceOf(bob), amount);
        assertEq(token.totalSupply(), INITIAL_MINT + amount);
    }

    function test_mint_reverts_non_minter() public {
        vm.prank(alice);
        vm.expectRevert("FiatToken: caller is not a minter");
        token.mint(bob, 1e6);
    }

    function test_mint_reverts_exceeds_allowance() public {
        vm.prank(minter);
        vm.expectRevert("FiatToken: mint amount exceeds minterAllowance");
        token.mint(bob, MINT_CAP + 1);
    }

    function test_mint_decreases_minter_allowance() public {
        uint256 before = token.minterAllowance(minter);
        uint256 amount = 1_000 * 1e6;
        vm.prank(minter);
        token.mint(bob, amount);
        assertEq(token.minterAllowance(minter), before - amount);
    }

    // ──────────────────────────────────────────────
    // Burning
    // ──────────────────────────────────────────────

    function test_burn() public {
        uint256 amount = 500 * 1e6;
        // Mint to minter so they can burn
        vm.prank(minter);
        token.mint(minter, amount);

        uint256 supplyBefore = token.totalSupply();
        vm.prank(minter);
        token.burn(amount);
        assertEq(token.totalSupply(), supplyBefore - amount);
        assertEq(token.balanceOf(minter), 0);
    }

    function test_burn_reverts_non_minter() public {
        vm.prank(alice);
        vm.expectRevert("FiatToken: caller is not a minter");
        token.burn(1e6);
    }

    // ──────────────────────────────────────────────
    // Minter Configuration
    // ──────────────────────────────────────────────

    function test_configureMinter() public {
        address newMinter = makeAddr("newMinter");
        vm.prank(masterMinter);
        assertTrue(token.configureMinter(newMinter, 999e6));
        assertTrue(token.isMinter(newMinter));
        assertEq(token.minterAllowance(newMinter), 999e6);
    }

    function test_removeMinter() public {
        vm.prank(masterMinter);
        assertTrue(token.removeMinter(minter));
        assertFalse(token.isMinter(minter));
        assertEq(token.minterAllowance(minter), 0);
    }

    function test_configureMinter_reverts_non_masterMinter() public {
        vm.prank(alice);
        vm.expectRevert("FiatToken: caller is not the masterMinter");
        token.configureMinter(alice, 1e6);
    }

    // ──────────────────────────────────────────────
    // Blacklisting
    // ──────────────────────────────────────────────

    function test_blacklist_blocks_transfer() public {
        vm.prank(blacklister);
        token.blacklist(alice);
        assertTrue(token.isBlacklisted(alice));

        vm.prank(alice);
        vm.expectRevert("Blacklistable: account is blacklisted");
        token.transfer(bob, 1e6);
    }

    function test_blacklist_blocks_transferFrom_sender() public {
        vm.prank(alice);
        token.approve(bob, 1e6);

        vm.prank(blacklister);
        token.blacklist(bob);

        vm.prank(bob);
        vm.expectRevert("Blacklistable: account is blacklisted");
        token.transferFrom(alice, bob, 1e6);
    }

    function test_blacklist_blocks_approve() public {
        vm.prank(blacklister);
        token.blacklist(alice);

        vm.prank(alice);
        vm.expectRevert("Blacklistable: account is blacklisted");
        token.approve(bob, 1e6);
    }

    function test_unBlacklist() public {
        vm.prank(blacklister);
        token.blacklist(alice);
        assertTrue(token.isBlacklisted(alice));

        vm.prank(blacklister);
        token.unBlacklist(alice);
        assertFalse(token.isBlacklisted(alice));

        // Should be able to transfer again
        vm.prank(alice);
        assertTrue(token.transfer(bob, 1e6));
    }

    function test_blacklist_reverts_non_blacklister() public {
        vm.prank(alice);
        vm.expectRevert("FiatToken: caller is not the blacklister");
        token.blacklist(bob);
    }

    // ──────────────────────────────────────────────
    // Pausing
    // ──────────────────────────────────────────────

    function test_pause_blocks_transfer() public {
        vm.prank(pauser);
        token.pause();
        assertTrue(token.paused());

        vm.prank(alice);
        vm.expectRevert("Pausable: paused");
        token.transfer(bob, 1e6);
    }

    function test_pause_blocks_mint() public {
        vm.prank(pauser);
        token.pause();

        vm.prank(minter);
        vm.expectRevert("Pausable: paused");
        token.mint(bob, 1e6);
    }

    function test_unpause_restores_operations() public {
        vm.prank(pauser);
        token.pause();

        vm.prank(pauser);
        token.unpause();
        assertFalse(token.paused());

        vm.prank(alice);
        assertTrue(token.transfer(bob, 1e6));
    }

    function test_pause_reverts_non_pauser() public {
        vm.prank(alice);
        vm.expectRevert("FiatToken: caller is not the pauser");
        token.pause();
    }

    // ──────────────────────────────────────────────
    // Ownership
    // ──────────────────────────────────────────────

    function test_transferOwnership() public {
        address newOwner = makeAddr("newOwner");
        vm.prank(owner);
        token.transferOwnership(newOwner);
        assertEq(token.owner(), newOwner);
    }

    function test_transferOwnership_reverts_non_owner() public {
        vm.prank(alice);
        vm.expectRevert("Ownable: caller is not the owner");
        token.transferOwnership(alice);
    }

    // ──────────────────────────────────────────────
    // Role Updates (owner only)
    // ──────────────────────────────────────────────

    function test_updateMasterMinter() public {
        address newMM = makeAddr("newMasterMinter");
        vm.prank(owner);
        token.updateMasterMinter(newMM);
        assertEq(token.masterMinter(), newMM);
    }

    function test_updatePauser() public {
        address newPauser = makeAddr("newPauser");
        vm.prank(owner);
        token.updatePauser(newPauser);
        assertEq(token.pauser(), newPauser);
    }

    function test_updateBlacklister() public {
        address newBL = makeAddr("newBL");
        vm.prank(owner);
        token.updateBlacklister(newBL);
        assertEq(token.blacklister(), newBL);
    }

    // ──────────────────────────────────────────────
    // EIP-2612 Permit
    // ──────────────────────────────────────────────

    function test_permit() public {
        uint256 ownerKey = 0xA11CE;
        address permitOwner = vm.addr(ownerKey);

        // Give permitOwner some tokens
        vm.prank(minter);
        token.mint(permitOwner, 1_000e6);

        uint256 value = 500e6;
        uint256 deadline = block.timestamp + 1 hours;
        uint256 nonce = token.nonces(permitOwner);

        bytes32 structHash = keccak256(
            abi.encode(token.PERMIT_TYPEHASH(), permitOwner, bob, value, nonce, deadline)
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(ownerKey, digest);

        token.permit(permitOwner, bob, value, deadline, v, r, s);

        assertEq(token.allowance(permitOwner, bob), value);
        assertEq(token.nonces(permitOwner), nonce + 1);
    }

    function test_permit_reverts_expired() public {
        uint256 ownerKey = 0xA11CE;
        address permitOwner = vm.addr(ownerKey);

        uint256 deadline = block.timestamp - 1;
        bytes32 structHash = keccak256(
            abi.encode(token.PERMIT_TYPEHASH(), permitOwner, bob, 100e6, 0, deadline)
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(ownerKey, digest);

        vm.expectRevert("FiatTokenV2: permit is expired");
        token.permit(permitOwner, bob, 100e6, deadline, v, r, s);
    }

    function test_permit_reverts_invalid_signature() public {
        uint256 ownerKey = 0xA11CE;
        address permitOwner = vm.addr(ownerKey);
        uint256 wrongKey = 0xB0B;

        uint256 deadline = block.timestamp + 1 hours;
        bytes32 structHash = keccak256(
            abi.encode(token.PERMIT_TYPEHASH(), permitOwner, bob, 100e6, 0, deadline)
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(wrongKey, digest);

        vm.expectRevert("EIP2612: invalid signature");
        token.permit(permitOwner, bob, 100e6, deadline, v, r, s);
    }

    // ──────────────────────────────────────────────
    // EIP-3009 TransferWithAuthorization
    // ──────────────────────────────────────────────

    function test_transferWithAuthorization() public {
        uint256 fromKey = 0xA11CE;
        address from = vm.addr(fromKey);

        vm.prank(minter);
        token.mint(from, 5_000e6);

        uint256 value = 1_000e6;
        uint256 validAfter = 0;
        uint256 validBefore = block.timestamp + 1 hours;
        bytes32 nonce = keccak256("unique-nonce-1");

        bytes32 structHash = keccak256(
            abi.encode(
                token.TRANSFER_WITH_AUTHORIZATION_TYPEHASH(),
                from, bob, value, validAfter, validBefore, nonce
            )
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(fromKey, digest);

        vm.warp(1); // ensure block.timestamp > validAfter (0)
        token.transferWithAuthorization(from, bob, value, validAfter, validBefore, nonce, v, r, s);

        assertEq(token.balanceOf(bob), value);
        assertTrue(token.authorizationState(from, nonce));
    }

    function test_transferWithAuthorization_reverts_reuse() public {
        uint256 fromKey = 0xA11CE;
        address from = vm.addr(fromKey);

        vm.prank(minter);
        token.mint(from, 5_000e6);

        uint256 value = 100e6;
        uint256 validAfter = 0;
        uint256 validBefore = block.timestamp + 1 hours;
        bytes32 nonce = keccak256("nonce-reuse-test");

        bytes32 structHash = keccak256(
            abi.encode(
                token.TRANSFER_WITH_AUTHORIZATION_TYPEHASH(),
                from, bob, value, validAfter, validBefore, nonce
            )
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(fromKey, digest);

        vm.warp(1);
        token.transferWithAuthorization(from, bob, value, validAfter, validBefore, nonce, v, r, s);

        vm.expectRevert("FiatTokenV2: authorization is used or canceled");
        token.transferWithAuthorization(from, bob, value, validAfter, validBefore, nonce, v, r, s);
    }

    // ──────────────────────────────────────────────
    // EIP-3009 ReceiveWithAuthorization
    // ──────────────────────────────────────────────

    function test_receiveWithAuthorization() public {
        uint256 fromKey = 0xA11CE;
        address from = vm.addr(fromKey);

        vm.prank(minter);
        token.mint(from, 5_000e6);

        uint256 value = 2_000e6;
        uint256 validAfter = 0;
        uint256 validBefore = block.timestamp + 1 hours;
        bytes32 nonce = keccak256("receive-nonce-1");

        bytes32 structHash = keccak256(
            abi.encode(
                token.RECEIVE_WITH_AUTHORIZATION_TYPEHASH(),
                from, bob, value, validAfter, validBefore, nonce
            )
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(fromKey, digest);

        vm.warp(1);
        vm.prank(bob); // caller must be `to`
        token.receiveWithAuthorization(from, bob, value, validAfter, validBefore, nonce, v, r, s);

        assertEq(token.balanceOf(bob), value);
    }

    function test_receiveWithAuthorization_reverts_wrong_caller() public {
        uint256 fromKey = 0xA11CE;
        address from = vm.addr(fromKey);

        vm.prank(minter);
        token.mint(from, 5_000e6);

        bytes32 nonce = keccak256("receive-nonce-wrong");
        bytes32 structHash = keccak256(
            abi.encode(
                token.RECEIVE_WITH_AUTHORIZATION_TYPEHASH(),
                from, bob, 100e6, 0, block.timestamp + 1 hours, nonce
            )
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(fromKey, digest);

        vm.warp(1);
        vm.prank(alice); // wrong caller, should be bob
        vm.expectRevert("FiatTokenV2: caller must be the payee");
        token.receiveWithAuthorization(from, bob, 100e6, 0, block.timestamp + 1 hours, nonce, v, r, s);
    }

    // ──────────────────────────────────────────────
    // EIP-3009 CancelAuthorization
    // ──────────────────────────────────────────────

    function test_cancelAuthorization() public {
        uint256 authorizerKey = 0xA11CE;
        address authorizer = vm.addr(authorizerKey);

        bytes32 nonce = keccak256("cancel-nonce-1");

        bytes32 structHash = keccak256(
            abi.encode(token.CANCEL_AUTHORIZATION_TYPEHASH(), authorizer, nonce)
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(authorizerKey, digest);

        token.cancelAuthorization(authorizer, nonce, v, r, s);
        assertTrue(token.authorizationState(authorizer, nonce));
    }

    // ──────────────────────────────────────────────
    // DOMAIN_SEPARATOR stability
    // ──────────────────────────────────────────────

    function test_domainSeparator_matches_eip712() public view {
        bytes32 expected = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256("Etzhayyim Computing Credits"),
                keccak256("2"),
                block.chainid,
                address(token)
            )
        );
        assertEq(token.DOMAIN_SEPARATOR(), expected);
    }

    // ──────────────────────────────────────────────
    // Fuzz: transfer never creates tokens
    // ──────────────────────────────────────────────

    function testFuzz_transfer_conservation(uint256 amount) public {
        amount = bound(amount, 0, INITIAL_MINT);

        uint256 supplyBefore = token.totalSupply();
        vm.prank(alice);
        token.transfer(bob, amount);

        assertEq(token.totalSupply(), supplyBefore);
        assertEq(token.balanceOf(alice) + token.balanceOf(bob), INITIAL_MINT);
    }
}
