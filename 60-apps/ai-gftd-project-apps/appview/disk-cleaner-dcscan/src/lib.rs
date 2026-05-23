use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanRoot {
    pub path: String,
    pub total_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanSummary {
    pub scanned_roots: Vec<ScanRoot>,
    pub duplicate_groups: u32,
    pub reclaimable_bytes: u64,
}

impl Default for ScanSummary {
    fn default() -> Self {
        Self {
            scanned_roots: vec![ScanRoot {
                path: "/Users/example/Downloads".to_string(),
                total_bytes: 0,
            }],
            duplicate_groups: 0,
            reclaimable_bytes: 0,
        }
    }
}

pub fn sample_summary_json() -> String {
    serde_json::to_string_pretty(&ScanSummary::default()).expect("serialize sample summary")
}
