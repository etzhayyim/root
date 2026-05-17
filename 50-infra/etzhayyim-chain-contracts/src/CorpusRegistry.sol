// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {Constitution} from "./Constitution.sol";

/**
 * @title CorpusRegistry
 * @notice On-chain registry of 本財 (goji-shisan corpus) assets — the
 *         untouchable principal tier of the etzhayyim Treasury per
 *         ADR-2605172300 §4. Each corpus asset is represented by a
 *         soulbound NFT whose state can only be mutated by Governance.
 *
 * @dev S4 of ADR-2605172300. Apache-2.0.
 *
 *      LEGAL CAVEAT — important for reviewers:
 *      ───────────────────────────────────────
 *      etzhayyim is a 宗教法人法非登記の任意団体 (unincorporated
 *      religious voluntary association). Under Japanese law, a 任意団体
 *      cannot hold real-property title in its own name. Real-world
 *      legal title to corpus assets is therefore held under the
 *      個人名義 of the 代表者 (representative officer), with this
 *      contract recording the *commitment* that the holder owns the
 *      asset in trust for the association.
 *
 *      The {HoldingAttestation} contract is the legal binding hook:
 *      every CorpusRegistry mint MUST reference an attestation hash
 *      whose preimage is a notarized off-chain document signed by the
 *      代表者 acknowledging the trust relationship and binding their
 *      individual disposition rights to a governance vote.
 *
 *      This contract is **structurally complete** but **legally
 *      contingent**: deploy only after a Japan-jurisdiction lawfirm
 *      review of the attestation document template (referenced via
 *      {HoldingAttestation}.docTemplateCid). The ADR S4 acceptance
 *      criterion explicitly defers production deployment until that
 *      review clears.
 *
 *      What this contract does:
 *        - Mints a soulbound (ERC-5192-style) NFT per corpus asset,
 *          via a governance-executed call to {mint}.
 *        - Stores asset metadata: kind, jurisdiction, legal holder DID,
 *          attestation hash, governance-lock flag, and content URI.
 *        - Refuses any transfer attempt (Soulbound revert).
 *        - Exposes governance-only {updateMetadata}, {setLock},
 *          {flagDisposed} so the lifecycle of an asset is fully
 *          observable on-chain.
 *
 *      What this contract does NOT do:
 *        - Pretend to be the legal title. Title remains off-chain.
 *        - Validate the attestation document. Validation is human
 *          (lawfirm + 代表者 wet-signature) before {mint} is called.
 *        - Hold value. Yield from corpus (if any) is accounted via
 *          {TreasuryMirror} on the reserve tier, not here.
 */

interface IERC5192 {
    function locked(uint256 tokenId) external view returns (bool);
    event Locked(uint256 tokenId);
    event Unlocked(uint256 tokenId);
}

contract CorpusRegistry is IERC5192 {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error NotGovernance();
    error UnknownToken(uint256 tokenId);
    error AlreadyDisposed();
    error Soulbound();
    error EmptyHolderDid();
    error EmptyAttestation();
    error InvalidKind(uint8 kind);

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event CorpusMinted(
        uint256 indexed tokenId,
        uint8   indexed kind,
        bytes32 indexed attestationHash,
        string  holderDid,
        bytes32 jurisdictionHash,
        bytes32 contentCid
    );
    event CorpusMetadataUpdated(
        uint256 indexed tokenId,
        bytes32 oldAttestationHash,
        bytes32 newAttestationHash,
        bytes32 newContentCid
    );
    event CorpusLockSet(uint256 indexed tokenId, bool locked);
    event CorpusDisposed(uint256 indexed tokenId, bytes32 reasonCid);

    // -------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------

    // Asset kinds — extend by governance-mutating Constitution.
    uint8 public constant KIND_REAL_PROPERTY = 1; // 不動産
    uint8 public constant KIND_IP            = 2; // 知的財産 (商標 / 著作権 etc.)
    uint8 public constant KIND_FACILITY      = 3; // 宗教施設
    uint8 public constant KIND_RWA_TOKEN     = 4; // bridged RWA token reference
    uint8 public constant KIND_OTHER         = 99;

    struct CorpusRecord {
        uint8   kind;
        bool    disposed;
        bool    governanceLocked;   // when true, disposition requires gov vote (default true)
        string  holderDid;          // representative officer DID (off-chain owner of legal title)
        bytes32 jurisdictionHash;   // keccak("JP-13") etc.
        bytes32 attestationHash;    // ↔ HoldingAttestation.attestationId
        bytes32 contentCid;         // IPFS CID hash of notarized document bundle
        uint64  mintedAt;
        uint64  lastUpdatedAt;
    }

    // -------------------------------------------------------------------
    // Immutable wiring
    // -------------------------------------------------------------------

    Constitution public immutable constitution;

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    uint256 public totalMinted;
    mapping(uint256 => CorpusRecord) private _records;

    // -------------------------------------------------------------------
    // Construction
    // -------------------------------------------------------------------

    constructor(Constitution constitution_) {
        constitution = constitution_;
    }

    // -------------------------------------------------------------------
    // Governance gate
    // -------------------------------------------------------------------

    modifier onlyGovernance() {
        if (msg.sender != constitution.governance()) revert NotGovernance();
        _;
    }

    // -------------------------------------------------------------------
    // Mint
    // -------------------------------------------------------------------

    function mint(
        uint8 kind,
        string calldata holderDid,
        bytes32 jurisdictionHash,
        bytes32 attestationHash,
        bytes32 contentCid
    ) external onlyGovernance returns (uint256 tokenId) {
        if (kind == 0) revert InvalidKind(kind);
        if (bytes(holderDid).length == 0) revert EmptyHolderDid();
        if (attestationHash == bytes32(0)) revert EmptyAttestation();

        tokenId = ++totalMinted;
        _records[tokenId] = CorpusRecord({
            kind: kind,
            disposed: false,
            governanceLocked: true,
            holderDid: holderDid,
            jurisdictionHash: jurisdictionHash,
            attestationHash: attestationHash,
            contentCid: contentCid,
            mintedAt: uint64(block.timestamp),
            lastUpdatedAt: uint64(block.timestamp)
        });

        emit CorpusMinted(tokenId, kind, attestationHash, holderDid, jurisdictionHash, contentCid);
        emit Locked(tokenId);
    }

    // -------------------------------------------------------------------
    // Governance lifecycle ops
    // -------------------------------------------------------------------

    /**
     * @notice Update the attestation reference or content CID. Used
     *         when the underlying document bundle is re-notarized or
     *         the representative officer rotates and re-signs.
     */
    function updateMetadata(
        uint256 tokenId,
        bytes32 newAttestationHash,
        bytes32 newContentCid
    ) external onlyGovernance {
        CorpusRecord storage r = _records[tokenId];
        if (r.mintedAt == 0) revert UnknownToken(tokenId);
        if (r.disposed) revert AlreadyDisposed();
        if (newAttestationHash == bytes32(0)) revert EmptyAttestation();
        bytes32 old = r.attestationHash;
        r.attestationHash = newAttestationHash;
        r.contentCid = newContentCid;
        r.lastUpdatedAt = uint64(block.timestamp);
        emit CorpusMetadataUpdated(tokenId, old, newAttestationHash, newContentCid);
    }

    /**
     * @notice Toggle the governance-lock flag. While true (default), the
     *         representative officer's off-chain disposition of the
     *         underlying asset is a breach of the on-chain commitment.
     *         Governance may explicitly unlock a token before a
     *         sanctioned sale (e.g., asset reallocation).
     */
    function setLock(uint256 tokenId, bool flag) external onlyGovernance {
        CorpusRecord storage r = _records[tokenId];
        if (r.mintedAt == 0) revert UnknownToken(tokenId);
        if (r.disposed) revert AlreadyDisposed();
        r.governanceLocked = flag;
        r.lastUpdatedAt = uint64(block.timestamp);
        emit CorpusLockSet(tokenId, flag);
    }

    /**
     * @notice Mark a corpus token as disposed (sold / transferred /
     *         destroyed). The token remains on-chain for audit but
     *         further updates are blocked. Governance MUST have first
     *         unlocked the token via {setLock(false)} unless the
     *         disposition reason is involuntary (eminent domain, etc.).
     */
    function flagDisposed(uint256 tokenId, bytes32 reasonCid) external onlyGovernance {
        CorpusRecord storage r = _records[tokenId];
        if (r.mintedAt == 0) revert UnknownToken(tokenId);
        if (r.disposed) revert AlreadyDisposed();
        r.disposed = true;
        r.lastUpdatedAt = uint64(block.timestamp);
        emit CorpusDisposed(tokenId, reasonCid);
    }

    // -------------------------------------------------------------------
    // Reads
    // -------------------------------------------------------------------

    function getRecord(uint256 tokenId) external view returns (CorpusRecord memory) {
        CorpusRecord memory r = _records[tokenId];
        if (r.mintedAt == 0) revert UnknownToken(tokenId);
        return r;
    }

    /// @inheritdoc IERC5192
    function locked(uint256 tokenId) external view returns (bool) {
        if (_records[tokenId].mintedAt == 0) revert UnknownToken(tokenId);
        return true; // SBT — always locked at the transfer layer
    }

    /// @dev Soulbound: transferFrom is permanently disabled. We do not
    ///      implement the rest of ERC-721; this function exists only so
    ///      ERC-721-assuming callers get a clear revert reason.
    function transferFrom(address, address, uint256) external pure {
        revert Soulbound();
    }
}
