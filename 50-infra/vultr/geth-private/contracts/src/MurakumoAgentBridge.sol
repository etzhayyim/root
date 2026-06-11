// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

/// @title MurakumoAgentBridge
///
/// @notice Bidirectional binding between a `MurakumoRegistry` operator
///         (`bytes32 operatorDid`) and a `etzhayyimAgentRegistry` ERC-8004 token
///         (`uint256 agentTokenId`). External agent-discovery callers
///         (LangGraph, OpenAI Apps SDK, Claude Desktop, A2A peers) can
///         resolve a single contract view to learn (a) the agent's IPFS
///         agentURI and (b) the inference operator's stake / endpoint, in
///         one round trip — without per-system knowledge of etzhayyim's internal
///         registry topology.
///
/// @dev    Stateless bridge — no escrow, no slash. Authoritative state lives
///         in `MurakumoRegistry` (stake/endpoint/active) and
///         `etzhayyimAgentRegistry` (agentURI/owner/reputation). The bridge only
///         joins them. ADR-2604271400.
interface IMurakumoRegistry {
    struct Operator {
        bytes32 operatorDid;
        address payoutAddress;
        uint256 stake;
        bytes32 capabilities;
        string endpoint;
        uint64 registeredAt;
        bool active;
    }
    function operators(bytes32 operatorDid) external view returns (Operator memory);
    function payoutAddressOf(bytes32 operatorDid) external view returns (address);
}

interface IetzhayyimAgentRegistry {
    struct Agent {
        uint256 tokenId;
        bytes32 rootDidHash;
        bytes32 agentUriHash;
        bytes32 metadataHash;
        string agentURI;
        address owner;
        uint64 registeredAt;
        bool active;
    }
    function ownerOf(uint256 tokenId) external view returns (address);
    function nextTokenId() external view returns (uint256);
    function tokenByRootDid(bytes32 rootDidHash) external view returns (uint256);
    function reputationScore(uint256 tokenId) external view returns (int256);
}

contract MurakumoAgentBridge {
    IMurakumoRegistry public immutable murakumo;
    IetzhayyimAgentRegistry public immutable agents;
    address public owner;

    mapping(bytes32 operatorDid => uint256 agentTokenId) public agentByOperator;
    mapping(uint256 agentTokenId => bytes32 operatorDid) public operatorByAgent;

    event Linked(bytes32 indexed operatorDid, uint256 indexed agentTokenId, address indexed by);
    event Unlinked(bytes32 indexed operatorDid, uint256 indexed agentTokenId, address indexed by);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    error NotOwner();
    error NotAuthorized();
    error OperatorInactive();
    error AgentInvalid();
    error AlreadyLinked();
    error NotLinked();
    error MismatchedLink();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(IMurakumoRegistry murakumo_, IetzhayyimAgentRegistry agents_, address owner_) {
        murakumo = murakumo_;
        agents = agents_;
        owner = owner_ == address(0) ? msg.sender : owner_;
        emit OwnershipTransferred(address(0), owner);
    }

    /// @notice Link an active Murakumo operator to an issued ERC-8004 agent
    ///         token. Caller must be the operator's `payoutAddress` OR the
    ///         bridge owner (Phase 2-A conservative; Phase 3 multisig).
    function link(bytes32 operatorDid, uint256 agentTokenId) external {
        IMurakumoRegistry.Operator memory op = murakumo.operators(operatorDid);
        if (!op.active) revert OperatorInactive();

        if (agentTokenId == 0 || agentTokenId >= agents.nextTokenId()) revert AgentInvalid();
        // ownerOf reverts if the token was never minted; we want a clean error.
        address agentOwner = agents.ownerOf(agentTokenId);
        if (agentOwner == address(0)) revert AgentInvalid();

        if (msg.sender != op.payoutAddress && msg.sender != owner) revert NotAuthorized();

        if (agentByOperator[operatorDid] != 0) revert AlreadyLinked();
        if (operatorByAgent[agentTokenId] != bytes32(0)) revert AlreadyLinked();

        agentByOperator[operatorDid] = agentTokenId;
        operatorByAgent[agentTokenId] = operatorDid;
        emit Linked(operatorDid, agentTokenId, msg.sender);
    }

    /// @notice Sever the link. Either the operator's `payoutAddress` or the
    ///         bridge owner can call.
    function unlink(bytes32 operatorDid) external {
        uint256 agentTokenId = agentByOperator[operatorDid];
        if (agentTokenId == 0) revert NotLinked();
        if (operatorByAgent[agentTokenId] != operatorDid) revert MismatchedLink();

        IMurakumoRegistry.Operator memory op = murakumo.operators(operatorDid);
        if (msg.sender != op.payoutAddress && msg.sender != owner) revert NotAuthorized();

        delete agentByOperator[operatorDid];
        delete operatorByAgent[agentTokenId];
        emit Unlinked(operatorDid, agentTokenId, msg.sender);
    }

    /// @notice Resolve an operator → ERC-8004 agent view in one call.
    function resolveAgent(bytes32 operatorDid)
        external
        view
        returns (uint256 agentTokenId, address agentOwner, int256 reputation)
    {
        agentTokenId = agentByOperator[operatorDid];
        if (agentTokenId == 0) return (0, address(0), 0);
        agentOwner = agents.ownerOf(agentTokenId);
        reputation = agents.reputationScore(agentTokenId);
    }

    /// @notice Resolve an ERC-8004 agent → Murakumo operator view in one call.
    function resolveOperator(uint256 agentTokenId)
        external
        view
        returns (bytes32 operatorDid, address payoutAddress, uint256 stake, string memory endpoint, bool active)
    {
        operatorDid = operatorByAgent[agentTokenId];
        if (operatorDid == bytes32(0)) return (bytes32(0), address(0), 0, "", false);
        IMurakumoRegistry.Operator memory op = murakumo.operators(operatorDid);
        payoutAddress = op.payoutAddress;
        stake = op.stake;
        endpoint = op.endpoint;
        active = op.active;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert NotOwner();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}
