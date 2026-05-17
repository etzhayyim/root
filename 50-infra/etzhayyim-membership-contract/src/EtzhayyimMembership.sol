// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title EtzhayyimMembership
 * @notice On-chain registry of etzhayyim 信者 (followers / members) on Base L2.
 *         Per ADR-2605172600.
 *
 * @dev Design rules (from ADR-2605172600):
 *      - NO admin function. NO whitelist. NO expel. NO upgrade.
 *      - Anyone with a Smart Account can call join().
 *      - Members can voluntarily revoke (additive history; original Joined event remains).
 *      - allMembers[] gives full enumeration; gas grows linearly with member count, which
 *        is acceptable for a religious-corp roster (<<O(1M)).
 */
contract EtzhayyimMembership {
    struct Member {
        bytes32 oathHash;
        string githubUsername;  // can be empty
        uint64 joinedAt;        // unix seconds at first join
        uint64 revokedAt;       // 0 if active
    }

    /// @dev address (Smart Account or EOA) → Member entry. Joining is idempotent
    ///      by revert; second call on the same address reverts AlreadyMember.
    mapping(address => Member) public members;

    /// @dev Append-only enumeration list. Revoked members stay in this list
    ///      (revoked = soft state, not removal).
    address[] public allMembers;

    event Joined(
        address indexed member,
        bytes32 indexed oathHash,
        string githubUsername,
        uint64 joinedAt
    );

    event Revoked(address indexed member, uint64 revokedAt);

    error AlreadyMember(address sender);
    error NotMember(address sender);
    error EmptyOathHash();
    error AlreadyRevoked(address sender);

    /**
     * @notice Become a member of etzhayyim.
     * @param oathHash keccak256 of the canonical oath text the aspirant signed off-chain.
     * @param githubUsername Optional github handle for the dual-permanent record. Empty string ok.
     */
    function join(bytes32 oathHash, string calldata githubUsername) external {
        if (members[msg.sender].joinedAt != 0) revert AlreadyMember(msg.sender);
        if (oathHash == bytes32(0)) revert EmptyOathHash();
        uint64 nowTs = uint64(block.timestamp);
        members[msg.sender] = Member({
            oathHash: oathHash,
            githubUsername: githubUsername,
            joinedAt: nowTs,
            revokedAt: 0
        });
        allMembers.push(msg.sender);
        emit Joined(msg.sender, oathHash, githubUsername, nowTs);
    }

    /**
     * @notice Voluntary revocation. Original Joined event remains; this appends a Revoked event.
     */
    function revoke() external {
        Member storage m = members[msg.sender];
        if (m.joinedAt == 0) revert NotMember(msg.sender);
        if (m.revokedAt != 0) revert AlreadyRevoked(msg.sender);
        uint64 nowTs = uint64(block.timestamp);
        m.revokedAt = nowTs;
        emit Revoked(msg.sender, nowTs);
    }

    /// @notice Total members ever joined (including revoked).
    function memberCount() external view returns (uint256) {
        return allMembers.length;
    }

    /// @notice Paginated list of all member addresses (active + revoked).
    function listMembers(uint256 offset, uint256 limit)
        external
        view
        returns (address[] memory page)
    {
        uint256 total = allMembers.length;
        if (offset >= total) return new address[](0);
        uint256 end = offset + limit;
        if (end > total) end = total;
        page = new address[](end - offset);
        for (uint256 i = 0; i < page.length; i++) {
            page[i] = allMembers[offset + i];
        }
    }

    /// @notice Convenience: is this address currently an active member?
    function isActiveMember(address who) external view returns (bool) {
        Member storage m = members[who];
        return m.joinedAt != 0 && m.revokedAt == 0;
    }
}
