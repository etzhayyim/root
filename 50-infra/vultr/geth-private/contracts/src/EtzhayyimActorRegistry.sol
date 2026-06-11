// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {CoinbaseSmartWallet} from "smart-wallet/CoinbaseSmartWallet.sol";
import {CoinbaseSmartWalletFactory} from "smart-wallet/CoinbaseSmartWalletFactory.sol";

/// @title etzhayyimActorRegistry
///
/// @notice Thin index/router over the canonical CoinbaseSmartWalletFactory.
///         Adds two things on top of the audited factory:
///
///         1. A salt convention tying ERC-4337 account addresses to root DID
///            hashes — `nonce = uint256(keccak256("etzhayyim-actor", didHash))`.
///            New callers hash the ERC725 root DID string; legacy callers may
///            still hash did:etzhayyim during migration. Off-chain code (yoro UI,
///            authz Worker) can compute the address before activation.
///
///         2. A `mapping(didHash => account)` populated on first activation,
///            with an `ActorActivated` event for indexer pickup. Without
///            this, looking up an actor's account from their DID would
///            require replaying every `AccountCreated` event from the
///            factory and re-hashing each (owners, nonce) tuple.
///
/// @dev    Account creation itself is delegated unchanged to the factory.
///         Owners are arbitrary — `bytes` per item (32-byte secp256k1
///         address, 64-byte P-256 pubkey, etc.). Adding additional owners
///         after activation is done directly on the smart account via
///         MultiOwnable — this registry only handles the initial bind.
contract etzhayyimActorRegistry {
    /// @notice Coinbase Smart Wallet factory used for actual proxy deploys.
    CoinbaseSmartWalletFactory public immutable factory;

    /// @notice Resolved account address per root DID hash. Zero address
    ///         means the actor has not yet activated their smart account.
    mapping(bytes32 didHash => address account) public actorByDid;

    event ActorActivated(bytes32 indexed didHash, address indexed account, bytes[] owners);

    error ZeroFactory();
    error EmptyDid();
    error NoOwners();

    constructor(CoinbaseSmartWalletFactory factory_) {
        if (address(factory_) == address(0)) revert ZeroFactory();
        factory = factory_;
    }

    /// @notice Salt nonce used for the underlying CSW factory call.
    function _nonceFor(bytes32 didHash) internal pure returns (uint256) {
        return uint256(keccak256(abi.encode("etzhayyim-actor", didHash)));
    }

    /// @notice Predict the address of the actor's smart account before
    ///         activation. Same value will be returned by `activate` once
    ///         `owners` is finalised and the proxy is deployed.
    function predictAddress(bytes32 didHash, bytes[] calldata owners) external view returns (address) {
        if (didHash == bytes32(0)) revert EmptyDid();
        if (owners.length == 0) revert NoOwners();
        return factory.getAddress(owners, _nonceFor(didHash));
    }

    /// @notice Activate (deploy on first call, idempotent on re-call) the
    ///         smart account for a root DID, with the given initial owners.
    ///
    /// @dev    The CSW factory itself is idempotent on `(owners, nonce)` —
    ///         re-calling with identical inputs is a no-op. We additionally
    ///         enforce that the *registry* row stays stable: once a did is
    ///         indexed, the recorded account is the canonical answer even
    ///         if a caller later passes different owners (which would
    ///         deploy a *different* proxy that this registry doesn't track).
    function activate(bytes32 didHash, bytes[] calldata owners) external returns (address account) {
        if (didHash == bytes32(0)) revert EmptyDid();
        if (owners.length == 0) revert NoOwners();

        address existing = actorByDid[didHash];
        if (existing != address(0)) {
            return existing;
        }

        account = address(factory.createAccount(owners, _nonceFor(didHash)));
        actorByDid[didHash] = account;
        emit ActorActivated(didHash, account, owners);
    }
}
