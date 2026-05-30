// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
pragma solidity ^0.8.26;

/// @title WarifuCard — soulbound card identity (ADR-2605302000)
/// @notice ERC-5192-style locked (soulbound) token binding a card to a holder's ERC-4337
///         smart account. The binding is non-transferable by third parties. The card
///         is an identity/credential, NOT a bearer instrument — funds live in the holder's
///         smart account / CreditLine, never in this contract.
/// @dev R0 scaffold. ERC-5192 minimal: tokens are always locked.
contract WarifuCard {
    // --- constants (constitutional invariants) ---------------------------------------
    uint16 public constant INTERCHANGE_BPS = 0; // 決済手数料ゼロ
    uint16 public constant MERCHANT_FEE_BPS = 0;

    // --- ERC-5192 ---------------------------------------------------------------------
    event Locked(uint256 tokenId);
    event Unlocked(uint256 tokenId); // never emitted — cards are permanently locked

    /// @notice ERC-5192: all warifu cards are soulbound (always locked).
    function locked(uint256) external pure returns (bool) {
        return true;
    }

    // --- card binding -----------------------------------------------------------------
    struct Card {
        address smartAccount; // ERC-4337 account of the holder
        bytes32 holderDid;    // keccak of did:web:... / did:plc:...
        bool credit;          // true = credit funding available via CreditLine
        bool active;
    }

    mapping(uint256 => Card) public cards; // tokenId => Card
    mapping(address => bool) public issuer; // authorized issuers (community operators)
    uint256 public nextTokenId = 1;

    address public council; // Lv6+ multisig (governance)

    error NotIssuer();
    error NotCouncil();
    error CardInactive();

    constructor(address _council) {
        council = _council;
    }

    modifier onlyIssuer() {
        if (!issuer[msg.sender]) revert NotIssuer();
        _;
    }

    modifier onlyCouncil() {
        if (msg.sender != council) revert NotCouncil();
        _;
    }

    function setIssuer(address who, bool ok) external onlyCouncil {
        issuer[who] = ok;
    }

    /// @notice Issue a soulbound card bound to an ERC-4337 smart account.
    function issue(address smartAccount, bytes32 holderDid, bool credit)
        external
        onlyIssuer
        returns (uint256 tokenId)
    {
        tokenId = nextTokenId++;
        cards[tokenId] = Card({smartAccount: smartAccount, holderDid: holderDid, credit: credit, active: true});
        emit Locked(tokenId);
    }

    /// @notice Holder/Council may deactivate (e.g. lost device). No transfer/burn-to-seize.
    function deactivate(uint256 tokenId) external {
        Card storage c = cards[tokenId];
        if (msg.sender != c.smartAccount && msg.sender != council) revert NotCouncil();
        c.active = false;
    }

    function smartAccountOf(uint256 tokenId) external view returns (address) {
        Card storage c = cards[tokenId];
        if (!c.active) revert CardInactive();
        return c.smartAccount;
    }

    // Deliberately NO transfer()/burn()/setOwner() that lets a third party seize a binding.
}
