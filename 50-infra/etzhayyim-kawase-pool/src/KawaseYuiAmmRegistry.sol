// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/// @title KawaseYuiAmmRegistry
/// @notice Council-owned allow-list for the exact v4 components whose runtime
///         bytecode has been reviewed. Address allow-lists alone are not
///         enough: metamorphic or upgraded components fail closed when their
///         current extcodehash differs from the attested hash.
contract KawaseYuiAmmRegistry {
    error NotCouncilSafe();
    error ZeroAddress();
    error NoRuntimeCode(address component);
    error ProtocolFeeMustBeZeroAtR1(uint16 suppliedBps);
    error NotSafetyObserver();
    error NoMismatch();
    error PoolNotApproved(bytes32 poolId);

    struct PoolApproval {
        address manager;
        address hook;
        bytes32 managerCodehash;
        bytes32 hookCodehash;
        uint16 observedProtocolFeeBps;
        bool approved;
    }

    address public immutable councilSafe;
    bool public paused;
    mapping(address => bytes32) public adapterCodehash;
    mapping(bytes32 => PoolApproval) public pools;
    mapping(address => bool) public safetyObservers;

    event AdapterApprovalChanged(address indexed adapter, bytes32 codehash, bool approved);
    event PoolApprovalChanged(
        bytes32 indexed poolId,
        address indexed manager,
        address indexed hook,
        bytes32 managerCodehash,
        bytes32 hookCodehash,
        bool approved
    );
    event PauseChanged(bool paused);
    event SafetyObserverChanged(address indexed observer, bool approved);
    event ProtocolFeeMismatchReported(
        bytes32 indexed poolId, address indexed observer, uint16 observedProtocolFeeBps
    );

    constructor(address _councilSafe) {
        if (_councilSafe == address(0)) revert ZeroAddress();
        councilSafe = _councilSafe;
    }

    modifier onlyCouncilSafe() {
        if (msg.sender != councilSafe) revert NotCouncilSafe();
        _;
    }

    function setPaused(bool value) external onlyCouncilSafe {
        paused = value;
        emit PauseChanged(value);
    }

    function setSafetyObserver(address observer, bool approved) external onlyCouncilSafe {
        if (observer == address(0)) revert ZeroAddress();
        safetyObservers[observer] = approved;
        emit SafetyObserverChanged(observer, approved);
    }

    /// @notice A designated observer may only move the registry toward safety.
    ///         It cannot unpause, approve components or alter the recorded fee.
    function reportProtocolFeeMismatch(bytes32 poolId, uint16 observedProtocolFeeBps) external {
        if (!safetyObservers[msg.sender]) revert NotSafetyObserver();
        if (observedProtocolFeeBps == 0) revert NoMismatch();
        if (!pools[poolId].approved) revert PoolNotApproved(poolId);
        paused = true;
        emit ProtocolFeeMismatchReported(poolId, msg.sender, observedProtocolFeeBps);
        emit PauseChanged(true);
    }

    function approveAdapter(address adapter) external onlyCouncilSafe {
        bytes32 hash = _runtimeCodehash(adapter);
        adapterCodehash[adapter] = hash;
        emit AdapterApprovalChanged(adapter, hash, true);
    }

    function revokeAdapter(address adapter) external onlyCouncilSafe {
        delete adapterCodehash[adapter];
        emit AdapterApprovalChanged(adapter, bytes32(0), false);
    }

    /// @dev R1 requires observedProtocolFeeBps=0. PoolManager protocol fees can
    ///      change independently after this transaction, so the observer must
    ///      pause the registry on a mismatch; this record is evidence, not an
    ///      impossible claim of controlling the external manager.
    function approvePool(
        bytes32 poolId,
        address manager,
        address hook,
        uint16 observedProtocolFeeBps
    ) external onlyCouncilSafe {
        if (observedProtocolFeeBps != 0) {
            revert ProtocolFeeMustBeZeroAtR1(observedProtocolFeeBps);
        }
        bytes32 managerHash = _runtimeCodehash(manager);
        bytes32 hookHash = hook == address(0) ? bytes32(0) : _runtimeCodehash(hook);
        pools[poolId] = PoolApproval({
            manager: manager,
            hook: hook,
            managerCodehash: managerHash,
            hookCodehash: hookHash,
            observedProtocolFeeBps: observedProtocolFeeBps,
            approved: true
        });
        emit PoolApprovalChanged(poolId, manager, hook, managerHash, hookHash, true);
    }

    function revokePool(bytes32 poolId) external onlyCouncilSafe {
        PoolApproval memory prior = pools[poolId];
        delete pools[poolId];
        emit PoolApprovalChanged(poolId, prior.manager, prior.hook, bytes32(0), bytes32(0), false);
    }

    function isAdapterApproved(address adapter) public view returns (bool) {
        bytes32 expected = adapterCodehash[adapter];
        return !paused && adapter.code.length != 0 && expected != bytes32(0)
            && adapter.codehash == expected;
    }

    function isPoolApproved(bytes32 poolId, address manager, address hook)
        public
        view
        returns (bool)
    {
        PoolApproval memory approval = pools[poolId];
        return !paused && approval.approved && approval.manager == manager && approval.hook == hook
            && manager.code.length != 0 && manager.codehash == approval.managerCodehash
            && (hook == address(0)
                || (hook.code.length != 0 && hook.codehash == approval.hookCodehash))
            && approval.observedProtocolFeeBps == 0;
    }

    function _runtimeCodehash(address component) private view returns (bytes32 hash) {
        if (component == address(0)) revert ZeroAddress();
        if (component.code.length == 0) revert NoRuntimeCode(component);
        hash = component.codehash;
    }
}
