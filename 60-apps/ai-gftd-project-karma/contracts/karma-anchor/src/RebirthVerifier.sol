// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title RebirthVerifier (Phase K3 stub)
 * @notice Groth16 verifier for the RebirthNonLinkability Circom circuit.
 *
 * Phase K3: this is a *stub* that always returns true. Phase K4 replaces
 * this with the snarkjs-generated Groth16 verifier. The BPMN flow +
 * primitive + on-chain registry are exercised end-to-end against the
 * stub so the integration shape is locked in before circuit compile.
 *
 * Real verifier signature:
 *   function verifyProof(
 *     uint[2] calldata _pA,
 *     uint[2][2] calldata _pB,
 *     uint[2] calldata _pC,
 *     uint[2] calldata _pubSignals
 *   ) external view returns (bool)
 *
 * Public signals (matching Circom main.public):
 *   _pubSignals[0] = newSantanaRoot
 *   _pubSignals[1] = nullifier
 */
contract RebirthVerifier {
    /// @notice Burned nullifiers — prevents double-spend of an old organism.
    mapping(bytes32 => bool) public burnedNullifiers;

    event RebirthProofAccepted(
        bytes32 indexed newSantanaRoot,
        bytes32 indexed nullifier,
        address indexed submitter
    );

    /**
     * @notice Verify a rebirth non-linkability proof and burn the nullifier.
     *         Phase K3 stub: returns true unless nullifier already burned.
     *         Phase K4: integrates snarkjs Groth16 verifier.
     *
     * @param _proofA       Groth16 proof point A (Phase K4)
     * @param _proofB       Groth16 proof point B (Phase K4)
     * @param _proofC       Groth16 proof point C (Phase K4)
     * @param newSantanaRoot Public — the fresh organism's santana root
     * @param nullifier      Public — the consumed old organism nullifier
     */
    function verifyAndBurn(
        uint[2] calldata _proofA,
        uint[2][2] calldata _proofB,
        uint[2] calldata _proofC,
        bytes32 newSantanaRoot,
        bytes32 nullifier
    ) external returns (bool ok) {
        require(newSantanaRoot != bytes32(0), "RebirthVerifier: empty newSantanaRoot");
        require(nullifier != bytes32(0), "RebirthVerifier: empty nullifier");
        require(!burnedNullifiers[nullifier], "RebirthVerifier: nullifier already burned");

        // Phase K4: real Groth16 verification goes here.
        // For Phase K3 we accept any proof, but still record the
        // burn so the audit trail is meaningful.
        // _proofA, _proofB, _proofC currently unused (silence warning).
        _proofA; _proofB; _proofC;

        burnedNullifiers[nullifier] = true;
        emit RebirthProofAccepted(newSantanaRoot, nullifier, msg.sender);
        return true;
    }

    /// @notice Phase K3 read helper.
    function isNullifierBurned(bytes32 nullifier) external view returns (bool) {
        return burnedNullifiers[nullifier];
    }
}
