// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/// @title MurakumoRegistry
///
/// @notice On-chain register of Murakumo inference operators (ADR-0074
///         Phase 2-A). Each operator stakes GCC to enable their endpoint
///         to receive jobs via `MurakumoEscrow`. Stake is held until they
///         unregister; an authorised slasher (owner — sealer for now,
///         multisig in Phase 3) can confiscate part of it for SLA breach
///         or fraud.
///
/// @dev    Stake is the *only* mechanism on-chain. Endpoint URL +
///         capabilities are advertised here for off-chain matching by
///         the etzhayyim routing-gateway; the gateway reads `operatorList` /
///         `operators(did)` to pick a node, and the resulting job lands
///         in `MurakumoEscrow` referencing this operator's `did`.
contract MurakumoRegistry {
    IERC20 public immutable gcc;
    address public owner;
    uint256 public minStake;

    struct Operator {
        // Operator-side identity. Caller passes a did:etzhayyim hash; etzhayyim
        // off-chain code resolves it back to a handle for routing.
        bytes32 operatorDid;
        // Address that receives stake refunds on unregister and earnings
        // routed by `MurakumoEscrow`. Recommended: the operator's smart
        // account (etzhayyimActorRegistry.actorByDid).
        address payoutAddress;
        uint256 stake;
        // Capability bitfield — encoding chosen by off-chain code (e.g.
        // bit 0 = text generation, bit 1 = image, bit 2 = vision, etc.).
        // Stored as bytes32 to leave room for future schemes without
        // contract migration.
        bytes32 capabilities;
        // Inference HTTP endpoint, e.g. "https://murakumo-3.etzhayyim.com/v1".
        string endpoint;
        uint64 registeredAt;
        bool active;
    }

    mapping(bytes32 operatorDid => Operator) internal _operators;
    bytes32[] public operatorList;

    event OperatorRegistered(
        bytes32 indexed operatorDid,
        address indexed payoutAddress,
        string endpoint,
        bytes32 capabilities,
        uint256 stake
    );
    event OperatorStakeIncreased(bytes32 indexed operatorDid, uint256 amount, uint256 totalStake);
    event OperatorSlashed(bytes32 indexed operatorDid, uint256 amount, uint256 remainingStake);
    event OperatorUnregistered(bytes32 indexed operatorDid, uint256 stakeReturned);
    event OperatorEndpointUpdated(bytes32 indexed operatorDid, string newEndpoint, bytes32 newCapabilities);
    event MinStakeUpdated(uint256 oldMinStake, uint256 newMinStake);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    error NotOwner();
    error NotAuthorized();
    error AlreadyRegistered();
    error NotRegistered();
    error StakeBelowMinimum(uint256 provided, uint256 required);
    error TransferFailed();
    error InsufficientStake(uint256 requested, uint256 available);
    error EmptyEndpoint();
    error EmptyDid();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(IERC20 gcc_, address owner_, uint256 minStake_) {
        gcc = gcc_;
        owner = owner_ == address(0) ? msg.sender : owner_;
        minStake = minStake_;
        emit OwnershipTransferred(address(0), owner);
        emit MinStakeUpdated(0, minStake_);
    }

    /// @notice Register a new operator. Caller pulls `initialStake` GCC
    ///         from themselves into the registry (must `gcc.approve` this
    ///         contract first). The `did:etzhayyim` is canonical — operators
    ///         already exist as actors, this just enables them to take
    ///         inference jobs and earn revenue.
    function register(
        bytes32 operatorDid,
        address payoutAddress,
        string calldata endpoint,
        bytes32 capabilities,
        uint256 initialStake
    ) external {
        if (operatorDid == bytes32(0)) revert EmptyDid();
        if (bytes(endpoint).length == 0) revert EmptyEndpoint();
        if (initialStake < minStake) revert StakeBelowMinimum(initialStake, minStake);
        if (_operators[operatorDid].active) revert AlreadyRegistered();

        bool ok = gcc.transferFrom(msg.sender, address(this), initialStake);
        if (!ok) revert TransferFailed();

        _operators[operatorDid] = Operator({
            operatorDid: operatorDid,
            payoutAddress: payoutAddress == address(0) ? msg.sender : payoutAddress,
            stake: initialStake,
            capabilities: capabilities,
            endpoint: endpoint,
            registeredAt: uint64(block.timestamp),
            active: true
        });
        operatorList.push(operatorDid);

        emit OperatorRegistered(operatorDid, _operators[operatorDid].payoutAddress, endpoint, capabilities, initialStake);
    }

    /// @notice Top up stake. Anyone can call (e.g. a treasury can stake on
    ///         behalf of an operator).
    function addStake(bytes32 operatorDid, uint256 amount) external {
        Operator storage op = _operators[operatorDid];
        if (!op.active) revert NotRegistered();
        bool ok = gcc.transferFrom(msg.sender, address(this), amount);
        if (!ok) revert TransferFailed();
        op.stake += amount;
        emit OperatorStakeIncreased(operatorDid, amount, op.stake);
    }

    /// @notice Update advertised endpoint or capabilities. Operator only.
    function updateEndpoint(bytes32 operatorDid, string calldata newEndpoint, bytes32 newCapabilities) external {
        Operator storage op = _operators[operatorDid];
        if (!op.active) revert NotRegistered();
        if (msg.sender != op.payoutAddress && msg.sender != owner) revert NotAuthorized();
        if (bytes(newEndpoint).length == 0) revert EmptyEndpoint();
        op.endpoint = newEndpoint;
        op.capabilities = newCapabilities;
        emit OperatorEndpointUpdated(operatorDid, newEndpoint, newCapabilities);
    }

    /// @notice Confiscate part of an operator's stake (SLA / fraud).
    /// @dev    Slashed funds are sent to `owner` (treasury). Phase 3 will
    ///         partition between insurance fund + burn.
    function slash(bytes32 operatorDid, uint256 amount) external onlyOwner {
        Operator storage op = _operators[operatorDid];
        if (!op.active) revert NotRegistered();
        if (amount > op.stake) revert InsufficientStake(amount, op.stake);
        op.stake -= amount;
        bool ok = gcc.transfer(owner, amount);
        if (!ok) revert TransferFailed();
        emit OperatorSlashed(operatorDid, amount, op.stake);
    }

    /// @notice Unregister and recover stake. Either the operator (their
    ///         payoutAddress) or the owner may call — the latter is for
    ///         emergency removal of a misbehaving operator after slashing.
    function unregister(bytes32 operatorDid) external {
        Operator storage op = _operators[operatorDid];
        if (!op.active) revert NotRegistered();
        if (msg.sender != op.payoutAddress && msg.sender != owner) revert NotAuthorized();

        uint256 refund = op.stake;
        op.active = false;
        op.stake = 0;
        if (refund > 0) {
            bool ok = gcc.transfer(op.payoutAddress, refund);
            if (!ok) revert TransferFailed();
        }
        emit OperatorUnregistered(operatorDid, refund);
    }

    function setMinStake(uint256 newMinStake) external onlyOwner {
        emit MinStakeUpdated(minStake, newMinStake);
        minStake = newMinStake;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert NotOwner();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function operators(bytes32 operatorDid) external view returns (Operator memory) {
        return _operators[operatorDid];
    }

    /// @notice Read the operator's payout address — convenience for
    ///         `MurakumoEscrow` so it doesn't have to ABI-decode the full
    ///         struct on every settle.
    function payoutAddressOf(bytes32 operatorDid) external view returns (address) {
        Operator storage op = _operators[operatorDid];
        if (!op.active) revert NotRegistered();
        return op.payoutAddress;
    }

    function operatorCount() external view returns (uint256) {
        return operatorList.length;
    }
}
