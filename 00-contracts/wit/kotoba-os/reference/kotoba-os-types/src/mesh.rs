//! Agent-centric mesh reference (ADR-2606031600 §D5).
//!
//! Holochain-style: each kotoba-os node is an agent whose **source chain IS its
//! local Datom-log segment** (append-only, hash-linked, content-addressed);
//! published entries are accepted by a **deterministic witness quorum** and only
//! if they pass the **membrane** (content-addressed validation rule = the DNA).
//!
//! This is a reference model: the chain hash is a small explicit FNV-1a (the
//! real substrate uses CIDv1 blake3 via kotoba-core). The witness-selection rule
//! is the one fixed by ADR-2605231902: `witness_index = hash(record_cid) + i mod n`.

use crate::WitInterface;

/// Deterministic 64-bit FNV-1a. Explicit + stable so the reference's
/// content-addressing and witness selection are reproducible across machines
/// (unlike `std::hash::DefaultHasher`, whose output is not a stability contract).
pub fn fnv1a(bytes: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf2_9ce4_8422_2325;
    for &b in bytes {
        h ^= b as u64;
        h = h.wrapping_mul(0x0000_0100_0000_01b3);
    }
    h
}

/// One entry in a node's source chain: a content-addressed Datom batch
/// (`payload_cid`) linked to the previous entry's `hash`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChainEntry {
    pub payload_cid: String,
    pub prev: u64,
    pub hash: u64,
}

/// A node's append-only, hash-linked source chain (= its local Datom-log segment).
#[derive(Debug, Clone, Default)]
pub struct SourceChain {
    entries: Vec<ChainEntry>,
}

impl SourceChain {
    pub fn new() -> Self {
        Self { entries: Vec::new() }
    }

    fn link_hash(prev: u64, payload_cid: &str) -> u64 {
        let mut buf = prev.to_le_bytes().to_vec();
        buf.extend_from_slice(payload_cid.as_bytes());
        fnv1a(&buf)
    }

    /// Append a content-addressed Datom batch; returns the new chain head hash.
    pub fn append(&mut self, payload_cid: &str) -> u64 {
        let prev = self.head();
        let hash = Self::link_hash(prev, payload_cid);
        self.entries.push(ChainEntry { payload_cid: payload_cid.to_string(), prev, hash });
        hash
    }

    /// The current head hash (0 for an empty chain = genesis predecessor).
    pub fn head(&self) -> u64 {
        self.entries.last().map(|e| e.hash).unwrap_or(0)
    }

    pub fn len(&self) -> usize {
        self.entries.len()
    }

    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    pub fn entries(&self) -> &[ChainEntry] {
        &self.entries
    }

    /// Recompute every hash + link; returns false if any entry was tampered
    /// (payload changed, hash forged, or a link broken).
    pub fn verify(&self) -> bool {
        let mut prev = 0u64;
        for e in &self.entries {
            if e.prev != prev {
                return false; // broken link
            }
            if e.hash != Self::link_hash(prev, &e.payload_cid) {
                return false; // forged/tampered payload or hash
            }
            prev = e.hash;
        }
        true
    }

    /// Test/adversary helper: mutate an entry's payload WITHOUT re-linking, to
    /// prove `verify` detects tampering.
    pub fn tamper_payload(&mut self, idx: usize, new_cid: &str) {
        if let Some(e) = self.entries.get_mut(idx) {
            e.payload_cid = new_cid.to_string();
        }
    }
}

/// Deterministic witness index for the i-th pick over `n` witnesses
/// (ADR-2605231902: `hash(record_cid) + i mod n`).
pub fn witness_index(record_cid: &str, i: usize, n: usize) -> usize {
    debug_assert!(n > 0);
    (fnv1a(record_cid.as_bytes()) as usize).wrapping_add(i) % n
}

/// Select `quorum` distinct witness indices deterministically (probing i=0,1,2…
/// past collisions). Capped at `n_witnesses`.
pub fn select_witnesses(record_cid: &str, n_witnesses: usize, quorum: usize) -> Vec<usize> {
    let mut chosen: Vec<usize> = Vec::new();
    let want = quorum.min(n_witnesses);
    let mut i = 0usize;
    while chosen.len() < want {
        let idx = witness_index(record_cid, i, n_witnesses);
        if !chosen.contains(&idx) {
            chosen.push(idx);
        }
        i += 1;
    }
    chosen
}

/// A published entry seeking acceptance into the DHT: what it claims to use.
#[derive(Debug, Clone)]
pub struct PublishedEntry {
    pub record_cid: String,
    pub uses: Vec<WitInterface>,
}

/// The membrane: a content-addressed validation rule (the DNA). A peer accepts
/// an entry only if it validates.
pub trait Membrane {
    fn validate(&self, e: &PublishedEntry) -> bool;
}

/// Reference membrane: capability scoping at the mesh boundary — an entry is
/// valid only if every interface it uses is in this witness's granted set.
pub struct CapabilityMembrane {
    pub granted: Vec<WitInterface>,
}

impl Membrane for CapabilityMembrane {
    fn validate(&self, e: &PublishedEntry) -> bool {
        e.uses.iter().all(|u| self.granted.contains(u))
    }
}

/// An entry is accepted iff at least `quorum` of the deterministically selected
/// witnesses validate it against their membrane.
pub fn quorum_accepts<M: Membrane>(witnesses: &[M], e: &PublishedEntry, quorum: usize) -> bool {
    if witnesses.is_empty() {
        return false;
    }
    let chosen = select_witnesses(&e.record_cid, witnesses.len(), quorum);
    let votes = chosen.iter().filter(|&&idx| witnesses[idx].validate(e)).count();
    votes >= quorum.min(witnesses.len())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::WitInterface::*;

    #[test]
    fn source_chain_links_and_verifies() {
        let mut c = SourceChain::new();
        assert_eq!(c.head(), 0);
        let h1 = c.append("bafyA");
        let h2 = c.append("bafyB");
        assert_eq!(c.len(), 2);
        assert_ne!(h1, h2);
        assert_eq!(c.entries()[1].prev, h1); // entry 2 links to entry 1's hash
        assert!(c.verify());
    }

    #[test]
    fn verify_detects_tampering() {
        let mut c = SourceChain::new();
        c.append("bafyA");
        c.append("bafyB");
        assert!(c.verify());
        c.tamper_payload(0, "bafyEVIL"); // rewrite history without re-linking
        assert!(!c.verify(), "tampered chain must fail verification");
    }

    #[test]
    fn witness_selection_is_deterministic_and_reproducible() {
        let a = select_witnesses("bafyRecord1", 10, 3);
        let b = select_witnesses("bafyRecord1", 10, 3);
        assert_eq!(a, b); // same inputs -> same witnesses (ADR-2605231902)
        assert_eq!(a.len(), 3);
        // distinct indices
        let mut sorted = a.clone();
        sorted.sort();
        sorted.dedup();
        assert_eq!(sorted.len(), 3);
    }

    #[test]
    fn witness_selection_spreads_across_records() {
        // different records generally pick different witness sets
        let a = select_witnesses("recordA", 16, 3);
        let b = select_witnesses("recordB", 16, 3);
        assert_ne!(a, b);
    }

    #[test]
    fn witness_quorum_capped_at_population() {
        let w = select_witnesses("r", 3, 5); // ask 5 from only 3
        assert_eq!(w.len(), 3);
    }

    #[test]
    fn membrane_rejects_ungranted_interface() {
        let m = CapabilityMembrane { granted: vec![IoAnalog, Datom] };
        let ok = PublishedEntry { record_cid: "r1".into(), uses: vec![IoAnalog, Datom] };
        let bad = PublishedEntry { record_cid: "r2".into(), uses: vec![IoAnalog, IoGpio] };
        assert!(m.validate(&ok));
        assert!(!m.validate(&bad)); // IoGpio not granted -> rejected at the membrane
    }

    #[test]
    fn quorum_accepts_only_with_enough_valid_witnesses() {
        // 4 witnesses grant the analog+datom capability, 1 grants nothing useful.
        let good = || CapabilityMembrane { granted: vec![IoAnalog, Datom] };
        let witnesses = vec![good(), good(), good(), good(),
                             CapabilityMembrane { granted: vec![] }];
        let e = PublishedEntry { record_cid: "rX".into(), uses: vec![IoAnalog, Datom] };
        assert!(quorum_accepts(&witnesses, &e, 2));

        // an entry using an interface no witness grants cannot reach quorum
        let e_bad = PublishedEntry { record_cid: "rY".into(), uses: vec![FieldbusEthercat] };
        assert!(!quorum_accepts(&witnesses, &e_bad, 2));
    }
}
