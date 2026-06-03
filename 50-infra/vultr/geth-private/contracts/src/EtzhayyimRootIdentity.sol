// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

/// @title etzhayyimRootIdentity
/// @notice Minimal ERC725-style root identity for etzhayyim actors, agents, orgs,
///         and accounts.
///
/// The contract intentionally stores only compact pointers: hashes, CIDs,
/// account addresses, and revocation roots. Raw OAuth tokens, WebAuthn
/// credential material, PII, Kubernetes secrets, and policy bodies stay
/// offchain.
contract etzhayyimRootIdentity {
    bytes4 internal constant _INTERFACE_ID_ERC165 = 0x01ffc9a7;
    bytes4 internal constant _INTERFACE_ID_ERC725X = 0x7545acac;
    bytes4 internal constant _INTERFACE_ID_ERC725Y = 0x629aa694;

    enum Operation {
        Call,
        Create,
        Create2
    }

    address public owner;
    mapping(bytes32 key => bytes value) internal _data;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event DataChanged(bytes32 indexed key, bytes value);
    event Executed(uint256 indexed operation, address indexed to, uint256 value, bytes data, bytes result);

    error NotOwner();
    error ZeroOwner();
    error UnsupportedOperation();
    error ExecuteFailed();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(address owner_) {
        if (owner_ == address(0)) revert ZeroOwner();
        owner = owner_;
        emit OwnershipTransferred(address(0), owner_);
    }

    receive() external payable {}

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == _INTERFACE_ID_ERC165 || interfaceId == _INTERFACE_ID_ERC725X
            || interfaceId == _INTERFACE_ID_ERC725Y;
    }

    function getData(bytes32 key) external view returns (bytes memory) {
        return _data[key];
    }

    function getDataBatch(bytes32[] calldata keys) external view returns (bytes[] memory values) {
        values = new bytes[](keys.length);
        for (uint256 i = 0; i < keys.length; i++) {
            values[i] = _data[keys[i]];
        }
    }

    function setData(bytes32 key, bytes calldata value) external onlyOwner {
        _data[key] = value;
        emit DataChanged(key, value);
    }

    function setDataBatch(bytes32[] calldata keys, bytes[] calldata values) external onlyOwner {
        require(keys.length == values.length, "length mismatch");
        for (uint256 i = 0; i < keys.length; i++) {
            _data[keys[i]] = values[i];
            emit DataChanged(keys[i], values[i]);
        }
    }

    function execute(uint256 operation, address to, uint256 value, bytes calldata data)
        external
        payable
        onlyOwner
        returns (bytes memory result)
    {
        if (operation != uint256(Operation.Call)) revert UnsupportedOperation();
        (bool ok, bytes memory ret) = to.call{value: value}(data);
        if (!ok) revert ExecuteFailed();
        emit Executed(operation, to, value, data, ret);
        return ret;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroOwner();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}
