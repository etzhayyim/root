// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title etzhayyimAgentRegistry
 * @notice ERC-8004-shaped Identity Registry for the religious-corp
 *         agent fleet. Per ADR-2604262100 + ADR-2604262145 + ADR-2605241800.
 *
 *         Each agent is registered with:
 *           - `didHash`     = keccak256 of the canonical DID string
 *                             (e.g. "did:pkh:eip155:8453:0xabc…" or
 *                              "did:web:etzhayyim.com:actor:dataset-pinner")
 *           - `agentAddr`   = EOA or smart-account that controls the agent
 *           - `agentURI`    = IPFS pointer to the agent.json document
 *                             (per ADR-2605241800 §D1, the agent.json
 *                             carries the libp2p Multiaddr service[])
 *           - `scopeHash`   = bytes32 binding to an AgentAuthorityToken
 *                             scope (per ADR-2605231500), OR bytes32(0)
 *                             for infra actors that don't carry an AAT
 *           - `steward`     = controller (typically the AAT issuer; may
 *                             update agentURI, may deactivate). For infra
 *                             actors the Council Safe is the steward.
 *
 *         ERC-5192 (soulbound) — no transfers. ERC-721-shaped enumeration
 *         for compatibility with the ERC-8004 reference shape.
 *
 *         Council multisig can REVOKE any agent (Charter-violation
 *         enforcement). Steward can DEACTIVATE their own agent (graceful
 *         retirement).
 *
 * @dev Phase 1 surface (this contract):
 *        - registerAgent / updateAgentURI / deactivateAgent / revokeAgent
 *        - getAgentByDid / getAgentById / isActive
 *        - getAgentURI (the ERC-8004 read entry point)
 *
 *      Deferred:
 *        - reputation registry (ERC-8004 second pillar)
 *        - validation registry (ERC-8004 third pillar)
 *        - on-chain agentURI validation (off-chain in Phase 1)
 *        - ERC-1271 isValidSignature integration for smart-account
 *          steward (covered by the Council Safe binding directly)
 */

interface IERC5192Locked {
    function locked(uint256 tokenId) external view returns (bool);
    event Locked(uint256 tokenId);
    event Unlocked(uint256 tokenId);
}

contract etzhayyimAgentRegistry is IERC5192Locked {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error NotCouncil();
    error NotSteward(uint256 tokenId, address caller);
    error UnknownToken(uint256 tokenId);
    error AlreadyRegistered(bytes32 didHash);
    error AgentInactive(uint256 tokenId);
    error AgentURIEmpty();
    error StewardZero();
    error SoulboundTransfer();

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    struct Agent {
        bytes32 didHash;       // keccak256(did string)
        address agentAddr;     // EOA or smart account
        address steward;       // controller (per-actor Steward or Council Safe)
        string  agentURI;      // ipfs://<cid>/agent.json
        bytes32 scopeHash;     // AAT scope binding, or bytes32(0)
        uint64  registeredAt;
        uint64  updatedAt;
        bool    active;
    }

    uint256 public totalMinted;

    mapping(uint256 => Agent) private _agents;
    mapping(bytes32 => uint256) public didHashToTokenId;
    mapping(address => uint256) public addrToTokenId;

    // Council multisig — bootstrap-injected. Per ADR-2605192300, the
    // Council Safe controls revoke. Mutating this requires Council
    // ratify (out-of-scope here; pass new safe via constructor on
    // redeploy, or upgrade via proxy in future).
    address public immutable COUNCIL;

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event AgentRegistered(
        uint256 indexed tokenId,
        bytes32 indexed didHash,
        address indexed agentAddr,
        address steward,
        string agentURI,
        bytes32 scopeHash
    );
    event AgentURIUpdated(uint256 indexed tokenId, string agentURI);
    event AgentScopeUpdated(uint256 indexed tokenId, bytes32 scopeHash);
    event AgentDeactivated(uint256 indexed tokenId, address by);
    event AgentRevoked(uint256 indexed tokenId, address by);

    // -------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------

    constructor(address council) {
        if (council == address(0)) revert StewardZero();
        COUNCIL = council;
    }

    // -------------------------------------------------------------------
    // Modifiers
    // -------------------------------------------------------------------

    modifier onlyCouncil() {
        if (msg.sender != COUNCIL) revert NotCouncil();
        _;
    }

    modifier onlySteward(uint256 tokenId) {
        if (tokenId == 0 || tokenId > totalMinted) revert UnknownToken(tokenId);
        if (_agents[tokenId].steward != msg.sender) {
            revert NotSteward(tokenId, msg.sender);
        }
        _;
    }

    // -------------------------------------------------------------------
    // Registration (ERC-8004 §Identity Registry)
    // -------------------------------------------------------------------

    /**
     * @notice Register a new agent. Token id is monotonic 1..N.
     * @dev Anyone may register, but the steward is recorded and bound at
     *      registration time; updates flow through `onlySteward`. The
     *      Council Safe can override via `revokeAgent`.
     */
    function registerAgent(
        bytes32 didHash,
        address agentAddr,
        address steward,
        string calldata agentURI,
        bytes32 scopeHash
    ) external returns (uint256 tokenId) {
        if (steward == address(0)) revert StewardZero();
        if (bytes(agentURI).length == 0) revert AgentURIEmpty();
        if (didHashToTokenId[didHash] != 0) revert AlreadyRegistered(didHash);

        tokenId = ++totalMinted;
        _agents[tokenId] = Agent({
            didHash:      didHash,
            agentAddr:    agentAddr,
            steward:      steward,
            agentURI:     agentURI,
            scopeHash:    scopeHash,
            registeredAt: uint64(block.timestamp),
            updatedAt:    uint64(block.timestamp),
            active:       true
        });
        didHashToTokenId[didHash] = tokenId;
        if (agentAddr != address(0)) addrToTokenId[agentAddr] = tokenId;

        emit AgentRegistered(tokenId, didHash, agentAddr, steward, agentURI, scopeHash);
        emit Locked(tokenId);
    }

    function updateAgentURI(uint256 tokenId, string calldata agentURI) external onlySteward(tokenId) {
        if (bytes(agentURI).length == 0) revert AgentURIEmpty();
        if (!_agents[tokenId].active) revert AgentInactive(tokenId);
        _agents[tokenId].agentURI = agentURI;
        _agents[tokenId].updatedAt = uint64(block.timestamp);
        emit AgentURIUpdated(tokenId, agentURI);
    }

    function updateScope(uint256 tokenId, bytes32 scopeHash) external onlySteward(tokenId) {
        if (!_agents[tokenId].active) revert AgentInactive(tokenId);
        _agents[tokenId].scopeHash = scopeHash;
        _agents[tokenId].updatedAt = uint64(block.timestamp);
        emit AgentScopeUpdated(tokenId, scopeHash);
    }

    function deactivateAgent(uint256 tokenId) external onlySteward(tokenId) {
        if (!_agents[tokenId].active) revert AgentInactive(tokenId);
        _agents[tokenId].active = false;
        _agents[tokenId].updatedAt = uint64(block.timestamp);
        emit AgentDeactivated(tokenId, msg.sender);
    }

    function revokeAgent(uint256 tokenId) external onlyCouncil {
        if (tokenId == 0 || tokenId > totalMinted) revert UnknownToken(tokenId);
        if (!_agents[tokenId].active) revert AgentInactive(tokenId);
        _agents[tokenId].active = false;
        _agents[tokenId].updatedAt = uint64(block.timestamp);
        emit AgentRevoked(tokenId, msg.sender);
    }

    // -------------------------------------------------------------------
    // Reads
    // -------------------------------------------------------------------

    function getAgentById(uint256 tokenId) external view returns (Agent memory) {
        if (tokenId == 0 || tokenId > totalMinted) revert UnknownToken(tokenId);
        return _agents[tokenId];
    }

    function getAgentByDid(bytes32 didHash) external view returns (Agent memory) {
        uint256 id = didHashToTokenId[didHash];
        if (id == 0) revert UnknownToken(0);
        return _agents[id];
    }

    function getAgentURI(uint256 tokenId) external view returns (string memory) {
        if (tokenId == 0 || tokenId > totalMinted) revert UnknownToken(tokenId);
        return _agents[tokenId].agentURI;
    }

    function isActive(uint256 tokenId) external view returns (bool) {
        if (tokenId == 0 || tokenId > totalMinted) return false;
        return _agents[tokenId].active;
    }

    // -------------------------------------------------------------------
    // ERC-5192 soulbound surface
    // -------------------------------------------------------------------

    function locked(uint256 tokenId) external view returns (bool) {
        if (tokenId == 0 || tokenId > totalMinted) revert UnknownToken(tokenId);
        return true; // always soulbound
    }

    // ERC-721 transferFrom — explicitly disabled. Any wallet that
    // recognizes ERC-5192 will not even attempt to call this; we add
    // the revert as a hard guarantee.
    function transferFrom(address, address, uint256) external pure {
        revert SoulboundTransfer();
    }
}
