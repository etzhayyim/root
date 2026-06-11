// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Ownable2Step} from "@openzeppelin/contracts/access/Ownable2Step.sol";

/// @title ContributionRoyaltyRegistry — ADR-2604281400 Phase 1
///
/// @notice GCC royalty pool for OSS / media / model / dataset contributors.
///         The oracle (BPMN sealer) calls credit() daily from the
///         mv_contribution_royalty_daily aggregate.  Contributors pull via
///         claim() / claimPending().
///
/// @dev    owner  = Safe 0xc0C2…  (registerSource governance)
///         oracle = sealer EOA    (credit() — future: dedicated BPMN bot key)
contract ContributionRoyaltyRegistry is Ownable2Step {
    IERC20 public immutable gcc;
    address public oracle;

    // keccak256(canonical_id) → contributor smart-account address
    mapping(bytes32 => address) public contributors;
    // contributor address → accumulated earned GCC (wei)
    mapping(address => uint256) public earned;
    // keccak256(canonical_id) → pending wei for unregistered contributors
    mapping(bytes32 => uint256) public pendingEarned;

    event SourceRegistered(bytes32 indexed sourceHash, address indexed contributor);
    event Credited(address indexed contributor, uint256 amount);
    event PendingCredited(bytes32 indexed sourceHash, uint256 amount);
    event Claimed(address indexed contributor, uint256 amount);
    event PendingClaimed(bytes32 indexed sourceHash, address indexed contributor, uint256 amount);
    event OracleUpdated(address indexed oldOracle, address indexed newOracle);

    constructor(address _gcc, address _oracle, address _owner) {
        gcc = IERC20(_gcc);
        oracle = _oracle;
        _transferOwnership(_owner);
    }

    // --- Governance (Safe owner only) ---

    function registerSource(bytes32 sourceHash, address contributor) external onlyOwner {
        require(contributor != address(0), "zero contributor");
        contributors[sourceHash] = contributor;
        emit SourceRegistered(sourceHash, contributor);
    }

    function setOracle(address _oracle) external onlyOwner {
        emit OracleUpdated(oracle, _oracle);
        oracle = _oracle;
    }

    // --- Oracle (BPMN sealer) ---

    /// @notice Credit batched daily royalties. Caller must have pre-approved
    ///         `total` GCC to this contract (ERC-20 approve pattern).
    function credit(
        bytes32[] calldata sourceHashes,
        uint256[] calldata amounts
    ) external {
        require(msg.sender == oracle, "not oracle");
        require(sourceHashes.length == amounts.length, "length mismatch");
        uint256 total;
        for (uint256 i = 0; i < sourceHashes.length; i++) {
            uint256 amt = amounts[i];
            if (amt == 0) continue;
            address c = contributors[sourceHashes[i]];
            if (c != address(0)) {
                earned[c] += amt;
                emit Credited(c, amt);
            } else {
                pendingEarned[sourceHashes[i]] += amt;
                emit PendingCredited(sourceHashes[i], amt);
            }
            total += amt;
        }
        if (total > 0) {
            require(gcc.transferFrom(msg.sender, address(this), total), "transfer failed");
        }
    }

    // --- Contributor pull ---

    function claim() external {
        uint256 amount = earned[msg.sender];
        require(amount > 0, "nothing to claim");
        earned[msg.sender] = 0;
        require(gcc.transfer(msg.sender, amount), "transfer failed");
        emit Claimed(msg.sender, amount);
    }

    /// @notice Claim accumulated pending balance once the source is registered
    ///         to msg.sender.
    function claimPending(bytes32 sourceHash) external {
        require(contributors[sourceHash] == msg.sender, "not registered contributor");
        uint256 amount = pendingEarned[sourceHash];
        require(amount > 0, "nothing pending");
        pendingEarned[sourceHash] = 0;
        require(gcc.transfer(msg.sender, amount), "transfer failed");
        emit PendingClaimed(sourceHash, msg.sender, amount);
    }

    // --- View helpers ---

    function earnedBalance(address contributor) external view returns (uint256) {
        return earned[contributor];
    }

    function pendingBalance(bytes32 sourceHash) external view returns (uint256) {
        return pendingEarned[sourceHash];
    }

    function gccBalance() external view returns (uint256) {
        return gcc.balanceOf(address(this));
    }
}
