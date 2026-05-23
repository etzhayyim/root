// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title AgentAuthorityToken (AAT)
 * @notice ERC-5192-style soulbound token representing **scoped, revocable,
 *         delegated authority for an AI agent to act on behalf of a human
 *         Steward** within the religious-corp economic body.
 *
 *         Per ADR-2605231500. Companion to {AdherentRegistry}: humans
 *         hold Adherent SBTs (1 SBT = 1 vote), AI agents hold AATs
 *         (no voting power, delegated authority only). An AAT is minted
 *         by a Steward who themselves holds an Adherent SBT — the AAT
 *         carries that adherentTokenId as its accountability anchor.
 *
 * @dev    Constitutional invariants (NOT amendable):
 *           - AAT MUST NOT confer voting power (no Governance hook).
 *           - Steward MUST hold a valid (non-revoked) Adherent SBT at
 *             mint time. Subsequent Steward revocation does NOT auto-
 *             revoke the AAT (intentional, audit-grade); separate
 *             revoke() call required.
 *           - Soulbound: transferFrom / safeTransferFrom permanently
 *             disabled (ERC-5192 locked).
 *           - Scope is immutable at mint: changes require revoke + mint.
 *           - expiresAt MUST be in the future at mint (no perpetual AATs).
 *
 *         What S0 does NOT do (deferred):
 *           - on-chain UNSPSC prefix evaluation against envelope subjects
 *             (off-chain in the charter-compliance-gate library);
 *           - DID document signature verification (off-chain in S0);
 *           - automatic revocation cascades from Adherent revocation (S2).
 */

interface IERC5192 {
    function locked(uint256 tokenId) external view returns (bool);
    event Locked(uint256 tokenId);
    event Unlocked(uint256 tokenId);
}

/// @notice Minimal slice of AdherentRegistry the AAT contract needs to
///         verify Steward eligibility at mint time.
interface IAdherentRegistry {
    function tokenOf(address holder) external view returns (uint256);
    function locked(uint256 tokenId) external view returns (bool);
    function isRevoked(uint256 tokenId) external view returns (bool);
}

contract AgentAuthorityToken is IERC5192 {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error NotSteward();
    error NotMinterOrCouncil();
    error StewardLacksAdherent(address steward);
    error StewardAdherentRevoked(uint256 adherentTokenId);
    error UnknownToken(uint256 tokenId);
    error AlreadyRevoked(uint256 tokenId);
    error EmptyScope();
    error InvalidExpiry();
    error Soulbound();

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event AAT_Minted(
        uint256 indexed tokenId,
        string agentDid,
        address indexed steward,
        uint256 indexed stewardAdherentTokenId,
        uint64 expiresAt
    );
    event AAT_Revoked(uint256 indexed tokenId, address indexed by, bytes32 reasonCid);
    event AAT_ScopeRecorded(
        uint256 indexed tokenId,
        bytes32[] unspscPrefixes,
        bytes32[] purposes,
        uint256 valueCap
    );

    // -------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------

    struct Scope {
        bytes32[] unspscPrefixes; // keccak256 of prefix strings (e.g. "4322")
        bytes32[] purposes;       // keccak256 of purpose enum values
        uint256 valueCap;         // per-envelope ceiling (item count or USDC-6dp)
    }

    struct AATRecord {
        address steward;                 // wallet of the human Steward
        uint256 stewardAdherentTokenId;  // Adherent SBT backing the delegation
        string agentDid;                 // DID of the AI agent
        uint64 mintedAt;
        uint64 expiresAt;
        bool revoked;
        bytes32 revokeReason; // IPFS CID hash; zero if not revoked
    }

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    IAdherentRegistry public immutable ADHERENT_REGISTRY;

    /// @notice Council multisig address allowed to revoke any AAT
    ///         (override beyond the Steward's own revoke right).
    address public council;

    /// @notice tokenId → record
    mapping(uint256 => AATRecord) private _records;

    /// @notice tokenId → scope (mapping carries the variable-length arrays)
    mapping(uint256 => Scope) private _scopes;

    /// @notice agentDid hash → tokenId. One *active* AAT per agent DID at a
    ///         time; once revoked, a new AAT may be minted under the same DID.
    mapping(bytes32 => uint256) private _agentDidToActiveTokenId;

    /// @notice Total minted (== max tokenId issued); tokenIds start at 1.
    uint256 public totalMinted;

    // -------------------------------------------------------------------
    // Modifiers
    // -------------------------------------------------------------------

    modifier onlyCouncil() {
        if (msg.sender != council) revert NotMinterOrCouncil();
        _;
    }

    // -------------------------------------------------------------------
    // Construction
    // -------------------------------------------------------------------

    constructor(IAdherentRegistry adherentRegistry, address initialCouncil) {
        ADHERENT_REGISTRY = adherentRegistry;
        council = initialCouncil;
    }

    // -------------------------------------------------------------------
    // Mint
    // -------------------------------------------------------------------

    /**
     * @notice Mint a new AAT delegating authority to `agentDid`. Caller
     *         is the Steward; they MUST hold a valid Adherent SBT.
     *
     * @param  agentDid         DID of the AI agent (e.g. did:web:c43221501.etzhayyim.com)
     * @param  scope            Authority scope (UNSPSC prefixes + purposes + value cap)
     * @param  expiresAt        unix timestamp at which the AAT auto-revokes
     */
    function mint(
        string calldata agentDid,
        Scope calldata scope,
        uint64 expiresAt
    ) external returns (uint256 tokenId) {
        if (scope.unspscPrefixes.length == 0 || scope.purposes.length == 0) {
            revert EmptyScope();
        }
        if (expiresAt <= block.timestamp) revert InvalidExpiry();

        uint256 adherentTokenId = ADHERENT_REGISTRY.tokenOf(msg.sender);
        if (adherentTokenId == 0) revert StewardLacksAdherent(msg.sender);
        if (ADHERENT_REGISTRY.isRevoked(adherentTokenId)) {
            revert StewardAdherentRevoked(adherentTokenId);
        }

        tokenId = ++totalMinted;

        _records[tokenId] = AATRecord({
            steward: msg.sender,
            stewardAdherentTokenId: adherentTokenId,
            agentDid: agentDid,
            mintedAt: uint64(block.timestamp),
            expiresAt: expiresAt,
            revoked: false,
            revokeReason: bytes32(0)
        });

        // Storage copy of the scope (mapping carries dynamic arrays correctly).
        Scope storage stored = _scopes[tokenId];
        for (uint256 i = 0; i < scope.unspscPrefixes.length; ++i) {
            stored.unspscPrefixes.push(scope.unspscPrefixes[i]);
        }
        for (uint256 i = 0; i < scope.purposes.length; ++i) {
            stored.purposes.push(scope.purposes[i]);
        }
        stored.valueCap = scope.valueCap;

        _agentDidToActiveTokenId[keccak256(bytes(agentDid))] = tokenId;

        emit AAT_Minted(tokenId, agentDid, msg.sender, adherentTokenId, expiresAt);
        emit AAT_ScopeRecorded(tokenId, scope.unspscPrefixes, scope.purposes, scope.valueCap);
        emit Locked(tokenId);
    }

    // -------------------------------------------------------------------
    // Revoke
    // -------------------------------------------------------------------

    /**
     * @notice Revoke an AAT. Callable by the original Steward OR by the
     *         Council multisig address.
     */
    function revoke(uint256 tokenId, bytes32 reasonCid) external {
        AATRecord storage r = _records[tokenId];
        if (r.steward == address(0)) revert UnknownToken(tokenId);
        if (r.revoked) revert AlreadyRevoked(tokenId);
        if (msg.sender != r.steward && msg.sender != council) revert NotSteward();

        r.revoked = true;
        r.revokeReason = reasonCid;

        bytes32 didKey = keccak256(bytes(r.agentDid));
        if (_agentDidToActiveTokenId[didKey] == tokenId) {
            _agentDidToActiveTokenId[didKey] = 0;
        }

        emit AAT_Revoked(tokenId, msg.sender, reasonCid);
    }

    // -------------------------------------------------------------------
    // Council rotation
    // -------------------------------------------------------------------

    function setCouncil(address newCouncil) external onlyCouncil {
        council = newCouncil;
    }

    // -------------------------------------------------------------------
    // Read helpers
    // -------------------------------------------------------------------

    function recordOf(uint256 tokenId) external view returns (AATRecord memory) {
        if (_records[tokenId].steward == address(0)) revert UnknownToken(tokenId);
        return _records[tokenId];
    }

    function scopeOf(uint256 tokenId)
        external
        view
        returns (
            bytes32[] memory unspscPrefixes,
            bytes32[] memory purposes,
            uint256 valueCap
        )
    {
        if (_records[tokenId].steward == address(0)) revert UnknownToken(tokenId);
        Scope storage s = _scopes[tokenId];
        return (s.unspscPrefixes, s.purposes, s.valueCap);
    }

    function activeTokenIdForAgent(string calldata agentDid)
        external
        view
        returns (uint256)
    {
        return _agentDidToActiveTokenId[keccak256(bytes(agentDid))];
    }

    function isExpired(uint256 tokenId) public view returns (bool) {
        AATRecord storage r = _records[tokenId];
        if (r.steward == address(0)) revert UnknownToken(tokenId);
        return uint64(block.timestamp) >= r.expiresAt;
    }

    function isValid(uint256 tokenId) external view returns (bool) {
        AATRecord storage r = _records[tokenId];
        if (r.steward == address(0)) return false;
        return !r.revoked && uint64(block.timestamp) < r.expiresAt;
    }

    // -------------------------------------------------------------------
    // ERC-5192 (soulbound flag)
    // -------------------------------------------------------------------

    function locked(uint256 tokenId) external view returns (bool) {
        if (_records[tokenId].steward == address(0)) revert UnknownToken(tokenId);
        return true;
    }

    // -------------------------------------------------------------------
    // ERC-721 transfer surface — permanently disabled
    // -------------------------------------------------------------------

    function transferFrom(address, address, uint256) external pure {
        revert Soulbound();
    }

    function safeTransferFrom(address, address, uint256) external pure {
        revert Soulbound();
    }

    function safeTransferFrom(address, address, uint256, bytes calldata) external pure {
        revert Soulbound();
    }

    function approve(address, uint256) external pure {
        revert Soulbound();
    }

    function setApprovalForAll(address, bool) external pure {
        revert Soulbound();
    }
}
