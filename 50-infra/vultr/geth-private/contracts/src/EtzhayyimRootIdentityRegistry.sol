// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {etzhayyimRootIdentity} from "./EtzhayyimRootIdentity.sol";

/// @title etzhayyimRootIdentityRegistry
/// @notice Registry mapping ERC725 root DID hashes and facade DID hashes to
///         etzhayyim root identity contracts.
contract etzhayyimRootIdentityRegistry {
    address public owner;

    mapping(bytes32 rootDidHash => address identity) public identityByRootDid;
    mapping(bytes32 facadeDidHash => bytes32 rootDidHash) public rootByFacadeDid;

    event RootIdentityRegistered(
        bytes32 indexed rootDidHash, address indexed identity, address indexed controller, string rootDidUri
    );
    event FacadeLinked(bytes32 indexed facadeDidHash, bytes32 indexed rootDidHash, string facadeDidUri);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    error NotOwner();
    error EmptyRootDid();
    error EmptyFacadeDid();
    error UnknownRoot();
    error IdentityAlreadyRegistered();
    error InvalidIdentity();
    error ZeroOwner();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(address owner_) {
        owner = owner_ == address(0) ? msg.sender : owner_;
        emit OwnershipTransferred(address(0), owner);
    }

    function deployRootIdentity(bytes32 rootDidHash, string calldata rootDidUri, address controller)
        external
        onlyOwner
        returns (address identity)
    {
        if (rootDidHash == bytes32(0)) revert EmptyRootDid();
        if (identityByRootDid[rootDidHash] != address(0)) revert IdentityAlreadyRegistered();

        address identityOwner = controller == address(0) ? owner : controller;
        etzhayyimRootIdentity root = new etzhayyimRootIdentity(identityOwner);
        identity = address(root);
        identityByRootDid[rootDidHash] = identity;
        emit RootIdentityRegistered(rootDidHash, identity, identityOwner, rootDidUri);
    }

    function registerRootIdentity(bytes32 rootDidHash, address identity, string calldata rootDidUri)
        external
        onlyOwner
    {
        if (rootDidHash == bytes32(0)) revert EmptyRootDid();
        if (identity.code.length == 0) revert InvalidIdentity();
        if (identityByRootDid[rootDidHash] != address(0)) revert IdentityAlreadyRegistered();

        identityByRootDid[rootDidHash] = identity;
        emit RootIdentityRegistered(rootDidHash, identity, etzhayyimRootIdentity(payable(identity)).owner(), rootDidUri);
    }

    function linkFacade(bytes32 rootDidHash, bytes32 facadeDidHash, string calldata facadeDidUri) external onlyOwner {
        if (rootDidHash == bytes32(0)) revert EmptyRootDid();
        if (facadeDidHash == bytes32(0)) revert EmptyFacadeDid();
        if (identityByRootDid[rootDidHash] == address(0)) revert UnknownRoot();

        rootByFacadeDid[facadeDidHash] = rootDidHash;
        emit FacadeLinked(facadeDidHash, rootDidHash, facadeDidUri);
    }

    function resolveFacade(bytes32 facadeDidHash) external view returns (address identity) {
        bytes32 rootDidHash = rootByFacadeDid[facadeDidHash];
        if (rootDidHash == bytes32(0)) return address(0);
        return identityByRootDid[rootDidHash];
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroOwner();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}
