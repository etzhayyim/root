pragma circom 2.1.6;

include "circomlib/circuits/poseidon.circom";

/*
 * RebirthNonLinkability — Karma.lean N3 (anatman) zk proof.
 *
 * Public inputs (revealed on-chain):
 *   newSantanaRoot      — fresh organism's santana root (Poseidon hash)
 *   nullifier           — prevents double-spend of an old commitment
 *
 * Private inputs (witness, never revealed):
 *   freshNonce          — 256-bit random independent of any old DID
 *   salt                — 256-bit binding salt for organism identity
 *   oldRootWitness      — old santana root preimage (for nullifier link
 *                          ONLY, not for new root derivation)
 *
 * Constraints:
 *   1. newSantanaRoot == Poseidon(freshNonce, salt)
 *   2. nullifier == Poseidon(oldRootWitness, "rebirth-burn")
 *      (this prevents the same old organism from rebirthing twice
 *       without revealing its identity)
 *   3. freshNonce ≠ oldRootWitness (independence; checked off-circuit
 *       via Poseidon bit-equality assert — added in K4 when full
 *       circomlib bit-decomposition is available)
 *
 * The verifier learns:
 *   - The new organism committed to a fresh santana_root.
 *   - Some old organism (matching nullifier) is now consumed.
 *   - The new organism's identity material is independent of any
 *     known old organism (by virtue of Poseidon collision resistance
 *     and the freshNonce being witness-only).
 *
 * What the verifier does NOT learn:
 *   - Which old organism (oldRootWitness is hidden behind nullifier).
 *   - Whether the rebirthing person is the same biological human as
 *     the dissolved organism's biological host (anatman: structurally
 *     unprovable).
 *
 * Phase K3 status: skeleton circuit. Full snarkjs compile + Groth16
 * trusted setup is K4. The K3 stub verifier in Solidity returns true
 * for any input so the BPMN flow can be exercised end-to-end.
 */
template RebirthNonLinkability() {
    signal input freshNonce;       // private
    signal input salt;             // private
    signal input oldRootWitness;   // private

    signal output newSantanaRoot;  // public
    signal output nullifier;       // public

    // Constraint 1: newSantanaRoot = Poseidon(freshNonce, salt)
    component newRootHasher = Poseidon(2);
    newRootHasher.inputs[0] <== freshNonce;
    newRootHasher.inputs[1] <== salt;
    newSantanaRoot <== newRootHasher.out;

    // Constraint 2: nullifier = Poseidon(oldRootWitness, BURN_TAG)
    // BURN_TAG = field-element form of "rebirth-burn" — fixed circuit constant
    component nullHasher = Poseidon(2);
    nullHasher.inputs[0] <== oldRootWitness;
    nullHasher.inputs[1] <== 0x726562697274682d6275726e;  // "rebirth-burn" hex
    nullifier <== nullHasher.out;

    // Constraint 3: independence (Phase K4 — adds bit-level
    // decomposition of freshNonce and oldRootWitness, then asserts
    // they differ in at least one position). For K3 the protocol
    // commits to independence via signed input from the rebirth
    // operator (off-circuit attestation).
}

component main { public [newSantanaRoot, nullifier] } = RebirthNonLinkability();
