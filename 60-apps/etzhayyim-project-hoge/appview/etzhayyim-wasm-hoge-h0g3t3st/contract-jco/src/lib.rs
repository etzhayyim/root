/// Hoge Shannon JCO — Rust WIT Component Model implementation.
///
/// Pattern C: WIT Component Model (P2) via cargo-component + jco transpile.
/// Exports: etzhayyim:hoge-compute/compute → shannon-score(params: string) -> result<string, string>
///
/// ABI: Component Model canonical ABI (managed by wit-bindgen).
/// No manual memory management — wit-bindgen generates all glue.
/// Transpiled to ESM JS via `jco transpile --instantiation async`.
wit_bindgen::generate!({
    world: "compute-world",
    path: "wit",
});

struct Component;

impl exports::etzhayyim::hoge_compute::compute::Guest for Component {
    /// Shannon entropy of UTF-8 bytes in `params`.
    /// Returns JSON: {"score": f64, "len": usize, "pattern": "jco"}
    fn shannon_score(params: String) -> Result<String, String> {
        let bytes = params.as_bytes();
        let n = bytes.len();

        if n == 0 {
            return Ok(r#"{"score":0.0,"len":0,"pattern":"jco"}"#.to_string());
        }

        let mut freq = [0u32; 256];
        for &b in bytes {
            freq[b as usize] += 1;
        }

        let n_f = n as f64;
        let mut h = 0.0f64;
        for &c in &freq {
            if c > 0 {
                let p = c as f64 / n_f;
                h -= p * p.log2();
            }
        }

        Ok(format!(
            r#"{{"score":{},"len":{},"pattern":"jco"}}"#,
            h, n
        ))
    }
}

export!(Component);
