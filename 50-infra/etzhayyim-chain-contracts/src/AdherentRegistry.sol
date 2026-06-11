// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title AdherentRegistry
 * @notice ERC-5192-style soulbound token (SBT) representing **Adherent
 *         (構成員) enrollment in the economic body** of the etzhayyim
 *         religious voluntary association — distinct from the broader
 *         public 信者 (shinto / follower) commitment of ADR-2605172600.
 *         Per ADR-2605172700, every Adherent is also a 信者, but most
 *         信者 are not Adherents. This contract gates the kisha + voting
 *         layer; the 信者 layer lives on Base via {EtzhayyimMembership}.
 *
 *         One SBT per DID. Non-transferable. Tracks attestations (prayer /
 *         study / service / donation) for use by the off-chain
 *         EligibilityCell (ADR-2605172300 §3.1).
 *
 * @dev Per ADR-2605172300 §2. Apache-2.0.
 *
 *      This is a minimal-surface S0 implementation:
 *        - intentionally NOT a full ERC-721 (we do not pretend the SBT is
 *          a tradable NFT; transferFrom is permanently disabled);
 *        - ERC-5192 `locked(uint256)` is exposed so any wallet that
 *          recognizes the standard renders this as soulbound;
 *        - DID linkage stores a DID string per token; bridging to address
 *          ownership is handled by the join attestation (signature checked
 *          off-chain at join time — the registry just records the bond).
 *
 *      What S0 does NOT do (deferred to later stages):
 *        - signature verification of the join attestation against the
 *          DID document (off-chain in S0; on-chain DID resolver in S2+);
 *        - per-attestation evidence verification (S2);
 *        - revocation appeals (S3).
 */

interface IERC5192 {
    function locked(uint256 tokenId) external view returns (bool);
    event Locked(uint256 tokenId);
    event Unlocked(uint256 tokenId);
}

contract AdherentRegistry is IERC5192 {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error NotOfficer();
    error AlreadyJoined(string did);
    error UnknownToken(uint256 tokenId);
    error TokenRevoked(uint256 tokenId);
    error Soulbound();

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event OfficerSet(address indexed officer, bool isOfficer);
    event Joined(uint256 indexed tokenId, address indexed holder, string did, bytes32 attestationCid);
    event Revoked(uint256 indexed tokenId, bytes32 reasonCid);
    event Attested(
        uint256 indexed tokenId,
        bytes32 indexed eventType,
        bytes32 evidenceCid,
        uint64  attestedAt
    );

    // -------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------

    struct AdherentRecord {
        address holder;          // wallet bound at join time
        string  did;             // DID string (did:web / did:plc / did:etzhayyim)
        bytes32 joinAttestation; // IPFS CID hash of the creed-acceptance doc
        uint64  joinedAt;        // block.timestamp at join
        uint64  lastAttestedAt;  // most recent attest(...) call
        uint32  attestationCount;
        bool    revoked;
        bytes32 revokeReason;    // IPFS CID hash; zero if not revoked
    }

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    /// @notice Officer ↔ flag. Officers may mint, revoke, and (later) be
    ///         removed by Governance. In S0, officers are set by the
    ///         deployer in the constructor; later stages move officer-set
    ///         management to Governance.
    mapping(address => bool) public isOfficer;

    /// @notice tokenId → record
    mapping(uint256 => AdherentRecord) private _records;

    /// @notice did string hash → tokenId (collision-resistant unique index)
    mapping(bytes32 => uint256) private _didToTokenId;

    /// @notice holder address → tokenId (one membership per wallet)
    mapping(address => uint256) public tokenOf;

    /// @notice Per-token per-eventType attestation count.
    ///         eventType is keccak256 of "prayer" / "study" / "service" / "donation"
    ///         (or future event types).
    mapping(uint256 => mapping(bytes32 => uint32)) public attestationCountByType;

    /// @notice Total minted (== max tokenId issued); tokenIds start at 1.
    uint256 public totalMinted;

    // -------------------------------------------------------------------
    // Modifiers
    // -------------------------------------------------------------------

    modifier onlyOfficer() {
        if (!isOfficer[msg.sender]) revert NotOfficer();
        _;
    }

    // -------------------------------------------------------------------
    // Construction
    // -------------------------------------------------------------------

    constructor(address[] memory initialOfficers) {
        for (uint256 i = 0; i < initialOfficers.length; ++i) {
            isOfficer[initialOfficers[i]] = true;
            emit OfficerSet(initialOfficers[i], true);
        }
    }

    // -------------------------------------------------------------------
    // Officer set management (S0: deployer-bootstrapped; S3: governance)
    // -------------------------------------------------------------------

    function setOfficer(address officer, bool flag) external onlyOfficer {
        isOfficer[officer] = flag;
        emit OfficerSet(officer, flag);
    }

    // -------------------------------------------------------------------
    // Join (mint SBT)
    // -------------------------------------------------------------------

    /**
     * @notice Mint a new adherent SBT for `holder` bound to `did`.
     *
     * @dev The signature of `holder` over the creed (proving control of
     *      the DID and acceptance of the constitution) is verified
     *      OFF-CHAIN in S0 by the officer submitting this transaction.
     *      Officers therefore act as identity-binding witnesses. In S2+
     *      we move signature verification on-chain via a DID resolver.
     */
    function join(
        address holder,
        string calldata did,
        bytes32 attestationCid
    ) external onlyOfficer returns (uint256 tokenId) {
        bytes32 didKey = keccak256(bytes(did));
        if (_didToTokenId[didKey] != 0) revert AlreadyJoined(did);
        require(tokenOf[holder] == 0, "wallet already bound");

        tokenId = ++totalMinted;

        _records[tokenId] = AdherentRecord({
            holder: holder,
            did: did,
            joinAttestation: attestationCid,
            joinedAt: uint64(block.timestamp),
            lastAttestedAt: 0,
            attestationCount: 0,
            revoked: false,
            revokeReason: bytes32(0)
        });

        _didToTokenId[didKey] = tokenId;
        tokenOf[holder] = tokenId;

        emit Joined(tokenId, holder, did, attestationCid);
        emit Locked(tokenId);
    }

    // -------------------------------------------------------------------
    // Revoke
    // -------------------------------------------------------------------

    function revoke(uint256 tokenId, bytes32 reasonCid) external onlyOfficer {
        AdherentRecord storage r = _records[tokenId];
        if (r.holder == address(0)) revert UnknownToken(tokenId);
        if (r.revoked) revert TokenRevoked(tokenId);
        r.revoked = true;
        r.revokeReason = reasonCid;
        emit Revoked(tokenId, reasonCid);
    }

    // -------------------------------------------------------------------
    // Attest (record a participation event)
    // -------------------------------------------------------------------

    /**
     * @notice Record an attestation for `tokenId`. The actual event body
     *         lives off-chain (AT Record on MST, evidence on IPFS). Only
     *         the type and an evidence CID hash are recorded here.
     *
     * @dev S0: callable by the adherent's bound holder address or by any
     *      officer (officer-as-witness covers the case where the adherent
     *      signs via a passkey but the tx is relayed by an officer to
     *      preserve gas-zero UX). S2+ will move to passkey-direct via the
     *      paymaster, removing the officer relay path.
     */
    function attest(
        uint256 tokenId,
        bytes32 eventType,
        bytes32 evidenceCid
    ) external {
        AdherentRecord storage r = _records[tokenId];
        if (r.holder == address(0)) revert UnknownToken(tokenId);
        if (r.revoked) revert TokenRevoked(tokenId);
        require(msg.sender == r.holder || isOfficer[msg.sender], "not adherent or officer");

        r.lastAttestedAt = uint64(block.timestamp);
        unchecked { r.attestationCount += 1; }
        unchecked { attestationCountByType[tokenId][eventType] += 1; }

        emit Attested(tokenId, eventType, evidenceCid, uint64(block.timestamp));
    }

    // -------------------------------------------------------------------
    // Reads
    // -------------------------------------------------------------------

    function getRecord(uint256 tokenId) external view returns (AdherentRecord memory) {
        AdherentRecord memory r = _records[tokenId];
        if (r.holder == address(0)) revert UnknownToken(tokenId);
        return r;
    }

    function tokenIdOfDid(string calldata did) external view returns (uint256) {
        return _didToTokenId[keccak256(bytes(did))];
    }

    /**
     * @notice "Active" = not revoked and has attested at least once
     *         within the trailing `windowSecs` window. Used by Governance
     *         to compute eligible-voter denominator.
     */
    function isActive(uint256 tokenId, uint64 windowSecs) external view returns (bool) {
        AdherentRecord memory r = _records[tokenId];
        if (r.holder == address(0) || r.revoked) return false;
        if (r.lastAttestedAt == 0) return false;
        return (block.timestamp - r.lastAttestedAt) <= windowSecs;
    }

    // -------------------------------------------------------------------
    // ERC-5192 (soulbound signal) + transfer hard-disable
    // -------------------------------------------------------------------

    /// @inheritdoc IERC5192
    function locked(uint256 tokenId) external view returns (bool) {
        if (_records[tokenId].holder == address(0)) revert UnknownToken(tokenId);
        return true; // always locked
    }

    /// @dev SBT — transfer is permanently disabled. We do NOT implement
    ///      ERC-721 at all; this function exists only so any caller that
    ///      naively assumes ERC-721 gets a clear revert reason.
    function transferFrom(address, address, uint256) external pure {
        revert Soulbound();
    }
}
