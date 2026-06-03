// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {CoinbaseSmartWallet} from "smart-wallet/CoinbaseSmartWallet.sol";

/// @title etzhayyimActorAccount
///
/// @notice Coinbase Smart Wallet (ERC-4337-compatible smart account) with the
///         EntryPoint address overridable at impl deploy time. The vendored
///         Coinbase implementation hardcodes the canonical mainnet/L2
///         EntryPoint v0.6 (`0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789`),
///         which on the etzhayyim private chain (260425) has no code. This
///         subclass reads its EntryPoint from an immutable set by the
///         deploy script, so all ERC-1967 proxies cloned by the factory
///         see our chain-local EntryPoint.
///
/// @dev    All other behaviour (MultiOwnable, P-256 verification via FCL,
///         WebAuthn assertion validation, ERC-1271 isValidSignature, UUPS
///         upgrades, replay-protected user operations) is inherited from
///         CoinbaseSmartWallet untouched. This is the *only* etzhayyim-side
///         change to the smart-wallet stack — keeping the surface area
///         identical to the audited Coinbase code.
contract etzhayyimActorAccount is CoinbaseSmartWallet {
    address private immutable _ENTRY_POINT;

    constructor(address entryPoint_) {
        _ENTRY_POINT = entryPoint_;
    }

    /// @inheritdoc CoinbaseSmartWallet
    function entryPoint() public view virtual override returns (address) {
        return _ENTRY_POINT;
    }
}
