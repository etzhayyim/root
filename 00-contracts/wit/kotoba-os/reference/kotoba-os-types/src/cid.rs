//! Content-addressing for the kotoba-os boot path (ADR-2606031600 §D1, R2).
//!
//! Real CIDv1 computation + verification, matching kotoba-core's "CIDv1 blake3".
//! The R0 `LowerEdge::verify_cid` did only a structural base32 shape check; this
//! module recomputes the CID from the artifact bytes and compares, so a tampered
//! kernel image / actor / membrane rule fails verification at boot (the trustless
//! `/ipfs/<cid>` re-verify discipline, ADR-2606014600).
//!
//! CIDv1 layout:  0x01 (v1) ‖ codec ‖ multihash(code ‖ len ‖ digest)
//!   - raw codec      = 0x55
//!   - blake3 mh code = 0x1e, len 0x20 (256-bit)   ← kotoba-core default
//!   - sha2-256 code  = 0x12, len 0x20             ← OCI bridge (§D4)
//! multibase: base32 lower, no padding, 'b' prefix.

/// RFC4648 base32 lowercase alphabet (multibase 'b').
const B32: &[u8] = b"abcdefghijklmnopqrstuvwxyz234567";

/// Encode bytes as multibase base32 lower (no padding), WITHOUT the 'b' prefix.
fn base32_lower_nopad(data: &[u8]) -> String {
    let mut out = String::with_capacity(data.len() * 8 / 5 + 1);
    let mut buffer: u64 = 0;
    let mut bits: u32 = 0;
    for &b in data {
        buffer = (buffer << 8) | b as u64;
        bits += 8;
        while bits >= 5 {
            bits -= 5;
            out.push(B32[((buffer >> bits) & 0x1f) as usize] as char);
        }
        buffer &= (1 << bits) - 1; // keep only the pending bits (no overflow)
    }
    if bits > 0 {
        out.push(B32[((buffer << (5 - bits)) & 0x1f) as usize] as char);
    }
    out
}

/// Multicodec/multihash code for the supported hashes.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mh {
    /// blake3-256 (0x1e) — kotoba-core canonical.
    Blake3,
    /// sha2-256 (0x12) — OCI bridge.
    Sha2_256,
}

impl Mh {
    fn code(self) -> u8 {
        match self {
            Mh::Blake3 => 0x1e,
            Mh::Sha2_256 => 0x12,
        }
    }
}

/// Build a CIDv1(raw codec) multibase-base32 string from a 32-byte digest.
fn cidv1_raw(mh: Mh, digest32: &[u8; 32]) -> String {
    let mut bytes = Vec::with_capacity(4 + 32);
    bytes.push(0x01); // CID version 1
    bytes.push(0x55); // raw codec
    bytes.push(mh.code());
    bytes.push(0x20); // length 32
    bytes.extend_from_slice(digest32);
    let mut s = String::with_capacity(1 + bytes.len() * 8 / 5 + 1);
    s.push('b'); // multibase base32-lower
    s.push_str(&base32_lower_nopad(&bytes));
    s
}

/// CIDv1(raw, blake3-256) of `data` — the kotoba-core content address.
pub fn cidv1_raw_blake3(data: &[u8]) -> String {
    let h = blake3::hash(data);
    cidv1_raw(Mh::Blake3, h.as_bytes())
}

/// CIDv1(raw, sha2-256) of a precomputed 32-byte sha2-256 digest (OCI bridge).
pub fn cidv1_raw_sha256(digest32: &[u8; 32]) -> String {
    cidv1_raw(Mh::Sha2_256, digest32)
}

/// Verify that `claimed_cid` is the CIDv1(raw, blake3) of `data` (constant-ish
/// string compare; the real win is recomputing the hash, not a shape check).
pub fn verify_blake3(data: &[u8], claimed_cid: &str) -> bool {
    cidv1_raw_blake3(data) == claimed_cid
}

#[cfg(test)]
mod tests {
    use super::*;

    fn hex32(s: &str) -> [u8; 32] {
        let b: Vec<u8> = (0..s.len())
            .step_by(2)
            .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
            .collect();
        let mut a = [0u8; 32];
        a.copy_from_slice(&b);
        a
    }

    #[test]
    fn base32_matches_independent_oracle() {
        // The sha2-256 CID python produced in iter 10 — an oracle independent of
        // this Rust base32 impl. If our encoder agrees here, the blake3 path
        // (same encoder) is trustworthy too.
        let digest = hex32("1f30a8761ec73ebd9c3f7879b5343157a44826bc7417666343cfd41cfdca271f");
        assert_eq!(
            cidv1_raw_sha256(&digest),
            "bafkreia7gcuhmhwhh26zyp3ypg2timkxurecnpduc5tggq6p2qop3srhd4"
        );
    }

    #[test]
    fn blake3_cid_is_stable_and_verifies() {
        let data = b"kotoba-os actor bytes (representative)";
        let cid = cidv1_raw_blake3(data);
        assert!(cid.starts_with('b'));
        assert!(verify_blake3(data, &cid)); // matching bytes verify
    }

    #[test]
    fn verify_rejects_tampered_bytes() {
        let cid = cidv1_raw_blake3(b"original actor");
        assert!(!verify_blake3(b"tampered actor", &cid)); // different bytes -> reject
    }

    #[test]
    fn verify_rejects_wrong_cid() {
        let data = b"actor";
        assert!(!verify_blake3(data, "bafkrewrongwrongwrongwrongwrongwrongwrongwrong"));
    }

    #[test]
    fn blake3_and_sha256_cids_differ_for_same_logical_content() {
        // distinct multihash codes -> distinct CIDs (codec/mh are part of the CID)
        let data = b"x";
        let b3 = cidv1_raw_blake3(data);
        let sha = cidv1_raw_sha256(&[0u8; 32]);
        assert_ne!(b3, sha);
    }
}
