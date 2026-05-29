use cid::Cid;
use multihash::Multihash;
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::sync::{Arc, RwLock};

/// SHA2-256 multihash code.
const SHA2_256: u64 = 0x12;
/// CIDv1 raw codec.
const RAW: u64 = 0x55;

/// Compute a CIDv1 SHA2-256 raw content identifier.
pub fn cid_for(data: &[u8]) -> Cid {
    let digest = Sha256::digest(data);
    let mh = Multihash::<64>::wrap(SHA2_256, &digest).expect("multihash wrap");
    Cid::new_v1(RAW, mh)
}

/// In-memory block store keyed by CIDv1 SHA2-256.
#[derive(Clone, Default)]
pub struct MemBlockStore {
    inner: Arc<RwLock<HashMap<Cid, Vec<u8>>>>,
}

impl MemBlockStore {
    pub fn new() -> Self {
        Self::default()
    }

    /// Compute CID and store block; returns the CID.
    pub fn put(&self, data: Vec<u8>) -> Cid {
        let cid = cid_for(&data);
        self.inner.write().unwrap().insert(cid, data);
        cid
    }

    /// Store block under an already-known CID (received from remote).
    pub fn insert(&self, cid: Cid, data: Vec<u8>) {
        self.inner.write().unwrap().insert(cid, data);
    }

    pub fn get_local(&self, cid: &Cid) -> Option<Vec<u8>> {
        self.inner.read().unwrap().get(cid).cloned()
    }

    pub fn contains_local(&self, cid: &Cid) -> bool {
        self.inner.read().unwrap().contains_key(cid)
    }
}

#[cfg(test)]
mod tests {
    use super::{cid_for, MemBlockStore, RAW, SHA2_256};
    use cid::Version;
    use sha2::{Digest, Sha256};

    #[test]
    fn cid_for_is_deterministic() {
        assert_eq!(cid_for(b"hello kotoba"), cid_for(b"hello kotoba"));
    }

    #[test]
    fn cid_for_distinguishes_distinct_inputs() {
        assert_ne!(cid_for(b"alpha"), cid_for(b"beta"));
    }

    #[test]
    fn cid_for_uses_cidv1_raw_sha256() {
        let cid = cid_for(b"payload");
        assert_eq!(cid.version(), Version::V1);
        assert_eq!(cid.codec(), RAW, "must use the IPFS raw-leaf codec");
        assert_eq!(cid.hash().code(), SHA2_256, "must use SHA2-256 multihash");
        // Digest must equal a direct SHA2-256 of the data (no salting/framing).
        assert_eq!(cid.hash().digest(), &Sha256::digest(b"payload")[..]);
    }

    #[test]
    fn cid_for_handles_empty_data() {
        let cid = cid_for(b"");
        assert_eq!(cid.hash().code(), SHA2_256);
        assert_eq!(cid.hash().digest(), &Sha256::digest(b"")[..]);
    }

    #[test]
    fn put_round_trips_and_returns_content_address() {
        let store = MemBlockStore::new();
        let data = b"block-bytes".to_vec();
        let cid = store.put(data.clone());
        assert_eq!(cid, cid_for(&data), "put must return the content address");
        assert_eq!(store.get_local(&cid), Some(data));
    }

    #[test]
    fn contains_and_get_reflect_membership() {
        let store = MemBlockStore::new();
        let cid = store.put(b"x".to_vec());
        assert!(store.contains_local(&cid));
        let unknown = cid_for(b"never stored");
        assert!(!store.contains_local(&unknown));
        assert_eq!(store.get_local(&unknown), None);
    }

    #[test]
    fn put_is_idempotent_for_identical_data() {
        let store = MemBlockStore::new();
        let c1 = store.put(b"same".to_vec());
        let c2 = store.put(b"same".to_vec());
        assert_eq!(c1, c2, "identical data is content-addressed to one CID");
        assert_eq!(store.get_local(&c1), Some(b"same".to_vec()));
    }

    #[test]
    fn insert_stores_under_supplied_cid() {
        // Mirrors receiving a block from a remote peer under its advertised CID.
        let store = MemBlockStore::new();
        let data = b"remote".to_vec();
        let cid = cid_for(&data);
        store.insert(cid, data.clone());
        assert_eq!(store.get_local(&cid), Some(data));
    }

    #[test]
    fn clone_shares_backing_storage() {
        // MemBlockStore is Arc-backed; a clone must observe writes through the original.
        let store = MemBlockStore::new();
        let clone = store.clone();
        let cid = store.put(b"shared".to_vec());
        assert_eq!(clone.get_local(&cid), Some(b"shared".to_vec()));
    }
}
