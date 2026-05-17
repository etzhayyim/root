// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title EtzhayyimMembership
 * @notice On-chain registry of etzhayyim 信者 (followers / members) on Base L2.
 *         Per ADR-2605172600.
 *
 * @dev Design rules (from ADR-2605172600):
 *      - NO admin function. NO whitelist. NO expel. NO upgrade.
 *      - Anyone with a Smart Account can call join() (= Level 1).
 *      - Members advance through Levels 2..7 sequentially via advance().
 *      - Members can voluntarily revoke (additive history; original Joined event remains).
 *      - allMembers[] gives full enumeration; gas grows linearly with member count, which
 *        is acceptable for a religious-corp roster (<<O(1M)).
 *
 * @dev 7-level commitment ladder (per ADR-2605172600 § "Levels"):
 *      L1 誓 Oath        — join() — base membership, signed oath
 *      L2 修 Practice    — advance(2, ...) — first member-DID AT record write
 *      L3 献 Dedication  — advance(3, ...) — first merged PR to etzhayyim/root
 *      L4 証 Witness     — advance(4, ...) — vouch for a newly joined member
 *      L5 護 Steward     — advance(5, ...) — operate substrate node / maintain open-* app
 *      L6 議 Council     — advance(6, ...) — participate in council session
 *      L7 老 Elder       — advance(7, ...) — sustain Council level for time-cohort
 */
contract EtzhayyimMembership {
    uint8 public constant LEVEL_OATH = 1;
    uint8 public constant LEVEL_MAX = 7;

    struct Member {
        bytes32 oathHash;
        string githubUsername;  // can be empty
        uint64 joinedAt;        // unix seconds at first join (Level 1)
        uint64 revokedAt;       // 0 if active
        uint8 level;            // 1..7, starts at 1 on join
    }

    /// @dev address (Smart Account or EOA) → Member entry. Joining is idempotent
    ///      by revert; second call on the same address reverts AlreadyMember.
    mapping(address => Member) public members;

    /// @dev Append-only enumeration list. Revoked members stay in this list
    ///      (revoked = soft state, not removal).
    address[] public allMembers;

    /// @dev address → level → evidence hash (keccak256 of AT URI / commit SHA / etc.)
    mapping(address => mapping(uint8 => bytes32)) public levelEvidence;
    /// @dev address → level → unix seconds when advanced to that level.
    ///      levelAdvancedAt[member][1] == joinedAt by construction.
    mapping(address => mapping(uint8 => uint64)) public levelAdvancedAt;

    event Joined(
        address indexed member,
        bytes32 indexed oathHash,
        string githubUsername,
        uint64 joinedAt
    );

    event Advanced(
        address indexed member,
        uint8 indexed level,
        bytes32 evidenceHash,
        string memo,
        uint64 advancedAt
    );

    event Revoked(address indexed member, uint64 revokedAt);

    error AlreadyMember(address sender);
    error NotMember(address sender);
    error EmptyOathHash();
    error AlreadyRevoked(address sender);
    error InvalidLevel(uint8 level);
    error LevelNotSequential(uint8 requested, uint8 current);
    error EmptyEvidence();

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
            revokedAt: 0,
            level: LEVEL_OATH
        });
        allMembers.push(msg.sender);
        levelEvidence[msg.sender][LEVEL_OATH] = oathHash;
        levelAdvancedAt[msg.sender][LEVEL_OATH] = nowTs;
        emit Joined(msg.sender, oathHash, githubUsername, nowTs);
    }

    /**
     * @notice Advance to the next commitment level. Sequential only — no skipping.
     * @param newLevel target level (must equal current + 1, and 2..LEVEL_MAX)
     * @param evidenceHash keccak256 of the evidence (AT URI / github commit SHA / etc.)
     * @param memo short human-readable note (≤ 280 chars by client convention)
     */
    function advance(uint8 newLevel, bytes32 evidenceHash, string calldata memo) external {
        Member storage m = members[msg.sender];
        if (m.joinedAt == 0 || m.revokedAt != 0) revert NotMember(msg.sender);
        if (newLevel < LEVEL_OATH + 1 || newLevel > LEVEL_MAX) revert InvalidLevel(newLevel);
        if (newLevel != m.level + 1) revert LevelNotSequential(newLevel, m.level);
        if (evidenceHash == bytes32(0)) revert EmptyEvidence();
        uint64 nowTs = uint64(block.timestamp);
        m.level = newLevel;
        levelEvidence[msg.sender][newLevel] = evidenceHash;
        levelAdvancedAt[msg.sender][newLevel] = nowTs;
        emit Advanced(msg.sender, newLevel, evidenceHash, memo, nowTs);
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

    /// @notice Current level of a member. Returns 0 for non-members or revoked.
    function levelOf(address who) external view returns (uint8) {
        Member storage m = members[who];
        if (m.joinedAt == 0 || m.revokedAt != 0) return 0;
        return m.level;
    }
}
