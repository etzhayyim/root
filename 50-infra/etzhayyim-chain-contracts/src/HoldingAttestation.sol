// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import {Constitution} from "./Constitution.sol";

/**
 * @title HoldingAttestation
 * @notice Records the on-chain commitment of a 代表者 (representative
 *         officer) that they hold legal title to a real-world asset in
 *         trust for the etzhayyim religious voluntary association,
 *         and that their right of disposition is bound to a governance
 *         vote unless the corresponding {CorpusRegistry} token is
 *         explicitly unlocked.
 *
 * @dev S4 of ADR-2605172300. Apache-2.0.
 *
 *      LEGAL CAVEAT (mirrors {CorpusRegistry}):
 *      ────────────────────────────────────────
 *      This contract is a structural commitment hook only. The legal
 *      binding mechanism is the **off-chain notarized document** whose
 *      keccak256 commitment is recorded here via {attest}. The
 *      Japan-jurisdiction lawfirm review must clear the document
 *      template before any attestation is recorded on production.
 *
 *      The contract does:
 *        - Record an attestation tuple: holderDid + assetUri + docHash +
 *          on-chain EIP-191 signature by the representative's wallet.
 *        - Verify the signature so a hostile party cannot forge a
 *          binding commitment in the representative's name.
 *        - Allow governance to {revoke} an attestation when the
 *          representative rotates and the new representative re-signs.
 *        - Track an immutable history: every attestation, even revoked,
 *          stays addressable on-chain.
 *
 *      The contract does NOT:
 *        - Move legal title (that lives in the 法務局 registry).
 *        - Replace civil-law recourse — if a representative disposes
 *          of a corpus asset in breach of the on-chain commitment, the
 *          association's recourse is a civil suit grounded in this
 *          signed commitment plus the off-chain document.
 *        - Take custody of any funds.
 */
contract HoldingAttestation {
    // -------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------

    error NotGovernance();
    error EmptyHolderDid();
    error EmptyDocHash();
    error UnknownAttestation(bytes32 attestationId);
    error AlreadyRevoked();
    error InvalidSignature();

    // -------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------

    event TemplateSet(bytes32 indexed docTemplateCid, bytes32 indexed lawfirmReviewCid);
    event Attested(
        bytes32 indexed attestationId,
        address indexed holder,
        string holderDid,
        bytes32 assetUriHash,
        bytes32 docHash
    );
    event AttestationRevoked(bytes32 indexed attestationId, bytes32 reasonCid);

    // -------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------

    struct AttestationRecord {
        address holder;          // wallet that signed
        string  holderDid;       // representative DID
        bytes32 assetUriHash;    // keccak of the canonical asset reference
                                  // (e.g., 法務局 estate ID URI, patent serial, etc.)
        bytes32 docHash;         // keccak256 of the notarized document text
        bytes32 docTemplateCid;  // snapshot of the template at signing time
        uint64  attestedAt;
        bool    revoked;
        bytes32 revokeReason;    // zero if not revoked
    }

    // -------------------------------------------------------------------
    // Immutable wiring
    // -------------------------------------------------------------------

    Constitution public immutable constitution;

    // -------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------

    /// @notice Current canonical template CID. Settable only by
    ///         governance. Each new {attest} call snapshots the
    ///         template hash valid at signing time, so older
    ///         attestations remain bound to their template.
    bytes32 public docTemplateCid;
    /// @notice IPFS CID hash of the lawfirm review opinion attached to
    ///         the current template. Useful for auditors.
    bytes32 public lawfirmReviewCid;

    mapping(bytes32 => AttestationRecord) private _records;
    bytes32[] public allAttestations;

    // -------------------------------------------------------------------
    // Construction
    // -------------------------------------------------------------------

    constructor(Constitution constitution_) {
        constitution = constitution_;
    }

    // -------------------------------------------------------------------
    // Template management (governance-only)
    // -------------------------------------------------------------------

    modifier onlyGovernance() {
        if (msg.sender != constitution.governance()) revert NotGovernance();
        _;
    }

    function setTemplate(bytes32 newTemplateCid, bytes32 newLawfirmReviewCid) external onlyGovernance {
        docTemplateCid = newTemplateCid;
        lawfirmReviewCid = newLawfirmReviewCid;
        emit TemplateSet(newTemplateCid, newLawfirmReviewCid);
    }

    // -------------------------------------------------------------------
    // Attest — representative officer signs a commitment
    // -------------------------------------------------------------------

    /**
     * @notice Record a signed holding attestation. Caller may be anyone
     *         (typically the same officer or a governance relayer);
     *         security comes from the `sig` over the payload.
     *
     * @dev The attestation id is deterministic:
     *      ``keccak256(holder, assetUriHash, docHash, docTemplateCid)``
     *      — so re-signing the same (holder, asset, doc, template)
     *      tuple is idempotent.
     */
    function attest(
        address holder,
        string calldata holderDid,
        bytes32 assetUriHash,
        bytes32 docHash,
        bytes calldata sig
    ) external returns (bytes32 attestationId) {
        if (bytes(holderDid).length == 0) revert EmptyHolderDid();
        if (docHash == bytes32(0)) revert EmptyDocHash();

        bytes32 template = docTemplateCid;
        attestationId = keccak256(abi.encode(holder, assetUriHash, docHash, template));

        // Idempotency: re-attesting the exact same payload is a no-op
        // revert so callers detect the duplicate.
        require(_records[attestationId].attestedAt == 0, "duplicate attestation");

        bytes32 inner = payloadHash(holder, holderDid, assetUriHash, docHash, template);
        bytes32 envelope = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", inner));
        if (!_verify(envelope, sig, holder)) revert InvalidSignature();

        _records[attestationId] = AttestationRecord({
            holder: holder,
            holderDid: holderDid,
            assetUriHash: assetUriHash,
            docHash: docHash,
            docTemplateCid: template,
            attestedAt: uint64(block.timestamp),
            revoked: false,
            revokeReason: bytes32(0)
        });
        allAttestations.push(attestationId);

        emit Attested(attestationId, holder, holderDid, assetUriHash, docHash);
    }

    /**
     * @notice Mark an attestation as revoked. Used during representative
     *         rotation or when a corpus token is disposed.
     */
    function revoke(bytes32 attestationId, bytes32 reasonCid) external onlyGovernance {
        AttestationRecord storage r = _records[attestationId];
        if (r.attestedAt == 0) revert UnknownAttestation(attestationId);
        if (r.revoked) revert AlreadyRevoked();
        r.revoked = true;
        r.revokeReason = reasonCid;
        emit AttestationRevoked(attestationId, reasonCid);
    }

    // -------------------------------------------------------------------
    // Reads
    // -------------------------------------------------------------------

    function getAttestation(bytes32 attestationId) external view returns (AttestationRecord memory) {
        AttestationRecord memory r = _records[attestationId];
        if (r.attestedAt == 0) revert UnknownAttestation(attestationId);
        return r;
    }

    function isActiveAttestation(bytes32 attestationId) external view returns (bool) {
        AttestationRecord memory r = _records[attestationId];
        if (r.attestedAt == 0) return false;
        return !r.revoked;
    }

    function totalAttestations() external view returns (uint256) {
        return allAttestations.length;
    }

    function payloadHash(
        address holder,
        string calldata holderDid,
        bytes32 assetUriHash,
        bytes32 docHash,
        bytes32 templateCid
    ) public view returns (bytes32) {
        return keccak256(abi.encode(
            address(this),
            block.chainid,
            holder,
            keccak256(bytes(holderDid)),
            assetUriHash,
            docHash,
            templateCid
        ));
    }

    // -------------------------------------------------------------------
    // Signature verification (same envelope as Phenotype / TreasuryMirror)
    // -------------------------------------------------------------------

    function _verify(bytes32 hash, bytes calldata sig, address expected) internal pure returns (bool) {
        if (sig.length != 65) return false;
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly ("memory-safe") {
            r := calldataload(sig.offset)
            s := calldataload(add(sig.offset, 32))
            v := byte(0, calldataload(add(sig.offset, 64)))
        }
        if (v < 27) v += 27;
        if (v != 27 && v != 28) return false;
        if (uint256(s) > 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0) {
            return false;
        }
        address recovered = ecrecover(hash, v, r, s);
        return recovered != address(0) && recovered == expected;
    }
}
