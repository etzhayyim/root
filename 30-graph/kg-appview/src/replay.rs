//! K3.a snapshot replay — rehydrate the store from a kg-projector
//! `bundle.jsonl` file. One JSON record per line. Records are applied
//! through the same primitive ([`crate::load::apply_record_value`]) that
//! the K2.c firehose path uses, so the two ingestion surfaces share
//! exact semantics.
//!
//! K3.b (deferred): fetch the bundle over HTTP from an IPFS gateway URL
//! whose CID is resolved from the latest L2 anchor. The current snapshot
//! file is what `ipfs-pinner` will pin in that flow; loading it from a
//! local path is functionally equivalent for an in-process AppView.

use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;

use anyhow::{Context, Result};
use serde_json::Value;

use crate::load::{apply_record_value, ApplyOutcome, LoadStats};
use crate::store::AppStore;

pub fn replay_snapshot_file(app: &AppStore, path: &Path) -> Result<LoadStats> {
    let file = File::open(path)
        .with_context(|| format!("opening snapshot {}", path.display()))?;
    let reader = BufReader::new(file);
    let mut stats = LoadStats::default();
    for (idx, line) in reader.lines().enumerate() {
        let line = line.with_context(|| format!("reading line {} of {}", idx + 1, path.display()))?;
        if line.trim().is_empty() {
            continue;
        }
        let value: Value = serde_json::from_str(&line)
            .with_context(|| format!("parsing line {} of {}", idx + 1, path.display()))?;
        let outcome = apply_record_value(app, &value)
            .with_context(|| format!("applying line {} of {}", idx + 1, path.display()))?;
        match outcome {
            ApplyOutcome::Node { triples, .. } => {
                stats.node_count += 1;
                stats.triple_count += triples;
            }
            ApplyOutcome::Edge { triples, .. } => {
                stats.edge_count += 1;
                stats.triple_count += triples;
            }
        }
    }
    Ok(stats)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn replay_matches_loader_output_for_tiny_snapshot() {
        // 2-record bundle: one node + one edge from the same projection
        // shape that kg-projector emits.
        let dir = tempdir_path();
        let bundle = dir.join("bundle.jsonl");
        let mut f = std::fs::File::create(&bundle).unwrap();
        writeln!(
            f,
            r#"{{"$type":"com.etzhayyim.kg.node","nodeId":"urn:adr:test-1","nodeType":"adr","source":"adr-frontmatter","createdAt":"2026-05-19T00:00:00.000Z"}}"#
        )
        .unwrap();
        writeln!(
            f,
            r#"{{"$type":"com.etzhayyim.kg.edge","subject":"urn:adr:test-1","predicate":"depends_on","object":"urn:adr:test-2","createdAt":"2026-05-19T00:00:00.000Z"}}"#
        )
        .unwrap();
        drop(f);

        let app = AppStore::new().unwrap();
        let stats = replay_snapshot_file(&app, &bundle).unwrap();
        assert_eq!(stats.node_count, 1);
        assert_eq!(stats.edge_count, 1);
        assert!(stats.triple_count >= 4);
    }

    fn tempdir_path() -> std::path::PathBuf {
        let p = std::env::temp_dir().join(format!("kg-appview-test-{}", std::process::id()));
        std::fs::create_dir_all(&p).unwrap();
        p
    }
}
