// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

/// @title etzhayyimAgentRegistry
/// @notice ERC-8004-compatible agent identity, validation, and reputation
///         registry for etzhayyim runtimes.
///
/// This is a compact private-chain implementation shaped for ERC-8004
/// discovery. Runtime execution stays in k8s/Zeebe/Python; IPFS stores the
/// public registration document pointed to by `agentURI`.
contract etzhayyimAgentRegistry {
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

    struct ValidationRecord {
        bytes32 validationId;
        uint256 tokenId;
        address validator;
        bytes32 requestHash;
        bytes32 resultHash;
        string evidenceURI;
        uint64 recordedAt;
    }

    struct ReputationRecord {
        bytes32 reputationId;
        uint256 tokenId;
        address issuer;
        int256 scoreDelta;
        bytes32 claimHash;
        string evidenceURI;
        uint64 recordedAt;
    }

    address public owner;
    bool public openRegistration;
    uint256 public nextTokenId = 1;

    mapping(uint256 tokenId => Agent) internal _agents;
    mapping(bytes32 rootDidHash => uint256 tokenId) public tokenByRootDid;
    mapping(uint256 tokenId => address approved) public getApproved;
    mapping(address account => uint256 balance) public balanceOf;
    mapping(bytes32 validationId => ValidationRecord record) internal _validations;
    mapping(bytes32 reputationId => ReputationRecord record) internal _reputations;
    mapping(uint256 tokenId => int256 score) public reputationScore;

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event AgentRegistered(
        uint256 indexed tokenId,
        bytes32 indexed rootDidHash,
        address indexed owner,
        bytes32 agentUriHash,
        bytes32 metadataHash,
        string agentURI,
        uint64 registeredAt
    );
    event AgentURISet(uint256 indexed tokenId, bytes32 agentUriHash, bytes32 metadataHash, string agentURI);
    event AgentStatusSet(uint256 indexed tokenId, bool active);
    event ValidationRecorded(
        bytes32 indexed validationId,
        uint256 indexed tokenId,
        address indexed validator,
        bytes32 requestHash,
        bytes32 resultHash,
        string evidenceURI,
        uint64 recordedAt
    );
    event ReputationRecorded(
        bytes32 indexed reputationId,
        uint256 indexed tokenId,
        address indexed issuer,
        int256 scoreDelta,
        int256 aggregateScore,
        bytes32 claimHash,
        string evidenceURI,
        uint64 recordedAt
    );
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event OpenRegistrationSet(bool openRegistration);

    error NotOwner();
    error NotAuthorized();
    error EmptyRootDid();
    error EmptyAgentURI();
    error UnknownAgent();
    error RootAlreadyRegistered();
    error InvalidOwner();
    error TransferToZero();
    error RecordAlreadyExists();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier onlyAgentController(uint256 tokenId) {
        Agent storage storedAgent = _agents[tokenId];
        if (storedAgent.owner == address(0)) revert UnknownAgent();
        if (msg.sender != owner && msg.sender != storedAgent.owner && msg.sender != getApproved[tokenId]) {
            revert NotAuthorized();
        }
        _;
    }

    constructor(address owner_) {
        owner = owner_ == address(0) ? msg.sender : owner_;
        emit OwnershipTransferred(address(0), owner);
    }

    function name() external pure returns (string memory) {
        return "etzhayyim Agent Identity";
    }

    function symbol() external pure returns (string memory) {
        return "etzhayyimAGENT";
    }

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == 0x01ffc9a7 || interfaceId == 0x80ac58cd || interfaceId == 0x5b5e139f;
    }

    function ownerOf(uint256 tokenId) public view returns (address) {
        address tokenOwner = _agents[tokenId].owner;
        if (tokenOwner == address(0)) revert UnknownAgent();
        return tokenOwner;
    }

    function tokenURI(uint256 tokenId) external view returns (string memory) {
        return agentURI(tokenId);
    }

    function agentURI(uint256 tokenId) public view returns (string memory) {
        Agent storage storedAgent = _agents[tokenId];
        if (storedAgent.owner == address(0)) revert UnknownAgent();
        return storedAgent.agentURI;
    }

    function agent(uint256 tokenId) external view returns (Agent memory) {
        Agent storage stored = _agents[tokenId];
        if (stored.owner == address(0)) revert UnknownAgent();
        return stored;
    }

    function validation(bytes32 validationId) external view returns (ValidationRecord memory) {
        ValidationRecord storage stored = _validations[validationId];
        if (stored.recordedAt == 0) revert UnknownAgent();
        return stored;
    }

    function reputation(bytes32 reputationId) external view returns (ReputationRecord memory) {
        ReputationRecord storage stored = _reputations[reputationId];
        if (stored.recordedAt == 0) revert UnknownAgent();
        return stored;
    }

    function registerAgent(
        bytes32 rootDidHash,
        address agentOwner,
        string calldata uri,
        bytes32 metadataHash
    ) external returns (uint256 tokenId) {
        if (!openRegistration && msg.sender != owner) revert NotAuthorized();
        if (rootDidHash == bytes32(0)) revert EmptyRootDid();
        if (bytes(uri).length == 0) revert EmptyAgentURI();
        if (agentOwner == address(0)) revert InvalidOwner();
        if (tokenByRootDid[rootDidHash] != 0) revert RootAlreadyRegistered();

        tokenId = nextTokenId++;
        bytes32 uriHash = keccak256(bytes(uri));
        _agents[tokenId] = Agent({
            tokenId: tokenId,
            rootDidHash: rootDidHash,
            agentUriHash: uriHash,
            metadataHash: metadataHash,
            agentURI: uri,
            owner: agentOwner,
            registeredAt: uint64(block.timestamp),
            active: true
        });
        tokenByRootDid[rootDidHash] = tokenId;
        balanceOf[agentOwner] += 1;

        emit Transfer(address(0), agentOwner, tokenId);
        emit AgentRegistered(
            tokenId,
            rootDidHash,
            agentOwner,
            uriHash,
            metadataHash,
            uri,
            _agents[tokenId].registeredAt
        );
    }

    function setAgentURI(uint256 tokenId, string calldata uri, bytes32 metadataHash)
        external
        onlyAgentController(tokenId)
    {
        if (bytes(uri).length == 0) revert EmptyAgentURI();
        Agent storage stored = _agents[tokenId];
        stored.agentURI = uri;
        stored.agentUriHash = keccak256(bytes(uri));
        stored.metadataHash = metadataHash;
        emit AgentURISet(tokenId, stored.agentUriHash, metadataHash, uri);
    }

    function setAgentActive(uint256 tokenId, bool active) external onlyAgentController(tokenId) {
        _agents[tokenId].active = active;
        emit AgentStatusSet(tokenId, active);
    }

    function approve(address approved, uint256 tokenId) external {
        address tokenOwner = ownerOf(tokenId);
        if (msg.sender != tokenOwner && msg.sender != owner) revert NotAuthorized();
        getApproved[tokenId] = approved;
        emit Approval(tokenOwner, approved, tokenId);
    }

    function transferFrom(address from, address to, uint256 tokenId) external {
        Agent storage stored = _agents[tokenId];
        if (stored.owner == address(0)) revert UnknownAgent();
        if (to == address(0)) revert TransferToZero();
        if (stored.owner != from) revert NotAuthorized();
        if (msg.sender != owner && msg.sender != from && msg.sender != getApproved[tokenId]) revert NotAuthorized();

        getApproved[tokenId] = address(0);
        balanceOf[from] -= 1;
        balanceOf[to] += 1;
        stored.owner = to;
        emit Transfer(from, to, tokenId);
    }

    function recordValidation(
        bytes32 validationId,
        uint256 tokenId,
        bytes32 requestHash,
        bytes32 resultHash,
        string calldata evidenceURI
    ) external {
        if (_agents[tokenId].owner == address(0)) revert UnknownAgent();
        if (validationId == bytes32(0)) {
            validationId = keccak256(abi.encode(tokenId, msg.sender, requestHash, resultHash, evidenceURI));
        }
        if (_validations[validationId].recordedAt != 0) revert RecordAlreadyExists();

        _validations[validationId] = ValidationRecord({
            validationId: validationId,
            tokenId: tokenId,
            validator: msg.sender,
            requestHash: requestHash,
            resultHash: resultHash,
            evidenceURI: evidenceURI,
            recordedAt: uint64(block.timestamp)
        });

        emit ValidationRecorded(
            validationId, tokenId, msg.sender, requestHash, resultHash, evidenceURI, uint64(block.timestamp)
        );
    }

    function recordReputation(
        bytes32 reputationId,
        uint256 tokenId,
        int256 scoreDelta,
        bytes32 claimHash,
        string calldata evidenceURI
    ) external {
        if (_agents[tokenId].owner == address(0)) revert UnknownAgent();
        if (reputationId == bytes32(0)) {
            reputationId = keccak256(abi.encode(tokenId, msg.sender, scoreDelta, claimHash, evidenceURI));
        }
        if (_reputations[reputationId].recordedAt != 0) revert RecordAlreadyExists();

        int256 aggregate = reputationScore[tokenId] + scoreDelta;
        reputationScore[tokenId] = aggregate;
        _reputations[reputationId] = ReputationRecord({
            reputationId: reputationId,
            tokenId: tokenId,
            issuer: msg.sender,
            scoreDelta: scoreDelta,
            claimHash: claimHash,
            evidenceURI: evidenceURI,
            recordedAt: uint64(block.timestamp)
        });

        emit ReputationRecorded(
            reputationId, tokenId, msg.sender, scoreDelta, aggregate, claimHash, evidenceURI, uint64(block.timestamp)
        );
    }

    function setOpenRegistration(bool open) external onlyOwner {
        openRegistration = open;
        emit OpenRegistrationSet(open);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert InvalidOwner();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}
