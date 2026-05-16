// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

/// @title ActorRuntimeRegistry
/// @notice EVM trust anchor for actor-oriented WASM/BPMN execution.
///
/// The EVM does not execute WASM, BPMN, browser sessions, or LLM calls. It
/// anchors the runtime inputs and outputs: module/process hashes, operator
/// identity, signed execution receipts, and periodic actor source-chain roots.
/// Operational state stays in RisingWave / object storage; this contract keeps
/// the small, immutable facts that workers and auditors need to agree on.
contract ActorRuntimeRegistry {
    enum RuntimeKind {
        Unknown,
        WasmWasi,
        BpmnZeebe,
        BrowserPod,
        LangGraph
    }

    struct RuntimeArtifact {
        bytes32 artifactId;
        RuntimeKind kind;
        bytes32 contentHash;
        bytes32 policyHash;
        bytes32 publisherDid;
        string uri;
        uint32 version;
        uint64 registeredAt;
        address publisher;
        bool active;
    }

    struct ExecutionReceipt {
        bytes32 jobId;
        bytes32 actorDid;
        bytes32 artifactId;
        bytes32 inputHash;
        bytes32 outputHash;
        bytes32 traceHash;
        bytes32 operatorDid;
        uint64 startedAt;
        uint64 finishedAt;
        address submitter;
    }

    struct ActorCheckpoint {
        bytes32 actorDid;
        bytes32 sourceChainRoot;
        bytes32 previousRoot;
        bytes32 evidenceHash;
        uint64 sequence;
        uint64 checkpointedAt;
        address submitter;
    }

    address public owner;
    bool public openRegistration;
    bool public openReceipt;

    mapping(bytes32 artifactId => RuntimeArtifact) internal _artifacts;
    mapping(bytes32 artifactId => uint32) public artifactVersionCount;
    mapping(bytes32 jobId => ExecutionReceipt) internal _receipts;
    mapping(bytes32 actorDid => ActorCheckpoint) internal _latestCheckpoint;

    event RuntimeArtifactRegistered(
        bytes32 indexed artifactId,
        RuntimeKind indexed kind,
        uint32 indexed version,
        bytes32 contentHash,
        bytes32 policyHash,
        bytes32 publisherDid,
        string uri,
        address publisher,
        uint64 registeredAt
    );
    event RuntimeArtifactStatusSet(bytes32 indexed artifactId, bool active);
    event ExecutionReceiptRecorded(
        bytes32 indexed jobId,
        bytes32 indexed actorDid,
        bytes32 indexed artifactId,
        bytes32 inputHash,
        bytes32 outputHash,
        bytes32 traceHash,
        bytes32 operatorDid,
        uint64 startedAt,
        uint64 finishedAt,
        address submitter
    );
    event ActorCheckpointRecorded(
        bytes32 indexed actorDid,
        uint64 indexed sequence,
        bytes32 sourceChainRoot,
        bytes32 previousRoot,
        bytes32 evidenceHash,
        address submitter,
        uint64 checkpointedAt
    );
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event OpenRegistrationSet(bool openRegistration);
    event OpenReceiptSet(bool openReceipt);

    error NotOwner();
    error NotAuthorized();
    error EmptyArtifactId();
    error EmptyContentHash();
    error EmptyJobId();
    error EmptyActorDid();
    error UnknownArtifact();
    error InactiveArtifact();
    error ReceiptAlreadyExists();
    error CheckpointSequenceNotMonotonic();

    modifier onlyOwner() {
        _onlyOwner();
        _;
    }

    function _onlyOwner() internal view {
        if (msg.sender != owner) revert NotOwner();
    }

    constructor(address owner_) {
        owner = owner_ == address(0) ? msg.sender : owner_;
        emit OwnershipTransferred(address(0), owner);
    }

    function registerArtifact(
        bytes32 artifactId,
        RuntimeKind kind,
        bytes32 contentHash,
        bytes32 policyHash,
        bytes32 publisherDid,
        string calldata uri
    ) external returns (uint32 version) {
        if (!openRegistration && msg.sender != owner) revert NotAuthorized();
        if (artifactId == bytes32(0)) revert EmptyArtifactId();
        if (contentHash == bytes32(0)) revert EmptyContentHash();
        if (kind == RuntimeKind.Unknown) revert UnknownArtifact();

        version = ++artifactVersionCount[artifactId];
        RuntimeArtifact memory artifact = RuntimeArtifact({
            artifactId: artifactId,
            kind: kind,
            contentHash: contentHash,
            policyHash: policyHash,
            publisherDid: publisherDid,
            uri: uri,
            version: version,
            registeredAt: uint64(block.timestamp),
            publisher: msg.sender,
            active: true
        });
        _artifacts[artifactId] = artifact;

        emit RuntimeArtifactRegistered(
            artifactId,
            kind,
            version,
            contentHash,
            policyHash,
            publisherDid,
            uri,
            msg.sender,
            artifact.registeredAt
        );
    }

    function setArtifactActive(bytes32 artifactId, bool active) external onlyOwner {
        RuntimeArtifact storage artifact = _artifacts[artifactId];
        if (artifact.version == 0) revert UnknownArtifact();
        artifact.active = active;
        emit RuntimeArtifactStatusSet(artifactId, active);
    }

    function recordExecutionReceipt(
        bytes32 jobId,
        bytes32 actorDid,
        bytes32 artifactId,
        bytes32 inputHash,
        bytes32 outputHash,
        bytes32 traceHash,
        bytes32 operatorDid,
        uint64 startedAt,
        uint64 finishedAt
    ) external {
        if (!openReceipt && msg.sender != owner) revert NotAuthorized();
        if (jobId == bytes32(0)) revert EmptyJobId();
        if (actorDid == bytes32(0)) revert EmptyActorDid();
        RuntimeArtifact storage artifact = _artifacts[artifactId];
        if (artifact.version == 0) revert UnknownArtifact();
        if (!artifact.active) revert InactiveArtifact();
        if (_receipts[jobId].submitter != address(0)) revert ReceiptAlreadyExists();

        _receipts[jobId] = ExecutionReceipt({
            jobId: jobId,
            actorDid: actorDid,
            artifactId: artifactId,
            inputHash: inputHash,
            outputHash: outputHash,
            traceHash: traceHash,
            operatorDid: operatorDid,
            startedAt: startedAt,
            finishedAt: finishedAt,
            submitter: msg.sender
        });

        emit ExecutionReceiptRecorded(
            jobId,
            actorDid,
            artifactId,
            inputHash,
            outputHash,
            traceHash,
            operatorDid,
            startedAt,
            finishedAt,
            msg.sender
        );
    }

    function recordActorCheckpoint(
        bytes32 actorDid,
        bytes32 sourceChainRoot,
        bytes32 evidenceHash,
        uint64 sequence
    ) external {
        if (!openReceipt && msg.sender != owner) revert NotAuthorized();
        if (actorDid == bytes32(0)) revert EmptyActorDid();
        ActorCheckpoint storage previous = _latestCheckpoint[actorDid];
        if (sequence <= previous.sequence) revert CheckpointSequenceNotMonotonic();

        bytes32 previousRoot = previous.sourceChainRoot;
        ActorCheckpoint memory checkpoint = ActorCheckpoint({
            actorDid: actorDid,
            sourceChainRoot: sourceChainRoot,
            previousRoot: previousRoot,
            evidenceHash: evidenceHash,
            sequence: sequence,
            checkpointedAt: uint64(block.timestamp),
            submitter: msg.sender
        });
        _latestCheckpoint[actorDid] = checkpoint;

        emit ActorCheckpointRecorded(
            actorDid,
            sequence,
            sourceChainRoot,
            previousRoot,
            evidenceHash,
            msg.sender,
            checkpoint.checkpointedAt
        );
    }

    function setOpenRegistration(bool open) external onlyOwner {
        openRegistration = open;
        emit OpenRegistrationSet(open);
    }

    function setOpenReceipt(bool open) external onlyOwner {
        openReceipt = open;
        emit OpenReceiptSet(open);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert NotOwner();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function artifacts(bytes32 artifactId) external view returns (RuntimeArtifact memory) {
        return _artifacts[artifactId];
    }

    function receipts(bytes32 jobId) external view returns (ExecutionReceipt memory) {
        return _receipts[jobId];
    }

    function latestCheckpoint(bytes32 actorDid) external view returns (ActorCheckpoint memory) {
        return _latestCheckpoint[actorDid];
    }
}
