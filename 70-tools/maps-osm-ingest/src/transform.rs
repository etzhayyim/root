//! OSM element → row converters.
//!
//! Vertex ID convention: `osm:{n|w|r}:{id}:{version}`. Edge ID: same pattern
//! with source + seq suffix for uniqueness. S2 cell computed at level 16,
//! geohash length 8.

use osmpbf::{DenseNode, Node, RelMemberType, Relation, Way};

#[inline]
fn info_user(info: &osmpbf::Info<'_>) -> Option<String> {
    info.user().and_then(|r| r.ok()).map(|s| s.to_string())
}

/// Row projected onto `vertex_osm_element`.
#[derive(Debug, Clone, serde::Serialize)]
pub struct VertexOsmElementRow {
    pub vertex_id: String,
    pub owner_did: String,
    pub source_did: String,
    pub sensitivity_ord: i16,
    pub created_date: String, // ISO date derived from timestamp or '1970-01-01'
    pub osm_type: &'static str,
    pub osm_id: i64,
    pub version: i32,
    pub changeset_id: Option<i64>,
    pub user_name: Option<String>,
    pub uid: Option<i64>,
    pub timestamp: Option<i64>, // epoch seconds
    pub valid_from: Option<i64>,
    pub valid_to: Option<i64>,
    pub lat: Option<f64>,
    pub lon: Option<f64>,
    pub s2_cell_id: Option<u64>,
    pub geohash: Option<String>,
    pub tags: serde_json::Value,
    pub bbox_min_lng: Option<f64>,
    pub bbox_min_lat: Option<f64>,
    pub bbox_max_lng: Option<f64>,
    pub bbox_max_lat: Option<f64>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct EdgeWayNodeRow {
    pub edge_id: String,
    pub owner_did: String,
    pub source_did: String,
    pub created_date: String,
    pub way_vertex_id: String,
    pub node_vertex_id: String, // points to node (version unknown here → latest)
    pub seq: i32,
    pub valid_from: Option<i64>,
    pub valid_to: Option<i64>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct EdgeRelationMemberRow {
    pub edge_id: String,
    pub owner_did: String,
    pub source_did: String,
    pub created_date: String,
    pub relation_vertex_id: String,
    pub member_vertex_id: String,
    pub member_type: &'static str, // 'n' | 'w' | 'r'
    pub role: String,
    pub seq: i32,
    pub valid_from: Option<i64>,
    pub valid_to: Option<i64>,
}

#[derive(Debug)]
pub struct WayBatch {
    pub vertices: Vec<VertexOsmElementRow>,
    pub edges: Vec<EdgeWayNodeRow>,
}

#[derive(Debug)]
pub struct RelationBatch {
    pub vertices: Vec<VertexOsmElementRow>,
    pub edges: Vec<EdgeRelationMemberRow>,
}

#[inline]
fn created_date_from_epoch(ts: Option<i64>) -> String {
    // Fast path: cheap YYYY-MM-DD from epoch seconds. For null or invalid, use the Unix
    // epoch — downstream analytics key this by ingest date separately.
    let Some(mut s) = ts else { return "1970-01-01".to_string() };
    if s < 0 {
        s = 0;
    }
    // Days since epoch.
    let days = s / 86_400;
    // Use chrono-free conversion (Rata Die-ish). Keep simple to avoid a dep.
    // Delegate to OffsetDateTime via a tiny inline date algorithm.
    let (y, m, d) = epoch_day_to_ymd(days);
    format!("{:04}-{:02}-{:02}", y, m, d)
}

// Howard Hinnant's date algorithm (public domain) — days since 1970-01-01 → (y, m, d).
fn epoch_day_to_ymd(days: i64) -> (i32, u32, u32) {
    let z = days + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = (z - era * 146_097) as u64;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146_096) / 365;
    let y = yoe as i64 + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    (y as i32, m as u32, d as u32)
}

fn s2_cell_id(lat: f64, lon: f64, level: u64) -> Option<u64> {
    // `s2` crate provides `CellID::from(LatLng)` then `parent(level)`.
    use s2::cellid::CellID;
    use s2::latlng::LatLng;
    let ll = LatLng::from_degrees(lat, lon);
    let cid: CellID = CellID::from(ll);
    let parent = cid.parent(level);
    Some(parent.0)
}

fn geohash_encode(lat: f64, lon: f64, len: usize) -> Option<String> {
    use geohash::{encode, Coord};
    encode(Coord { x: lon, y: lat }, len).ok()
}

fn tags_to_json<'a, I>(iter: I) -> serde_json::Value
where
    I: IntoIterator<Item = (&'a str, &'a str)>,
{
    let mut m = serde_json::Map::new();
    for (k, v) in iter {
        m.insert(k.to_string(), serde_json::Value::String(v.to_string()));
    }
    serde_json::Value::Object(m)
}

pub fn node_to_vertex(
    n: &Node,
    source_did: &str,
    owner_did: &str,
    s2_level: u64,
    geohash_len: usize,
) -> Option<VertexOsmElementRow> {
    let info = n.info();
    let version = info.version().unwrap_or(1);
    let lat = n.lat();
    let lon = n.lon();
    let ts = info.milli_timestamp().map(|ms| ms / 1000);
    Some(VertexOsmElementRow {
        vertex_id: format!("osm:n:{}:{}", n.id(), version),
        owner_did: owner_did.to_string(),
        source_did: source_did.to_string(),
        sensitivity_ord: 0,
        created_date: created_date_from_epoch(ts),
        osm_type: "n",
        osm_id: n.id(),
        version,
        changeset_id: info.changeset(),
        user_name: info_user(&info),
        uid: info.uid().map(|u| u as i64),
        timestamp: ts,
        valid_from: ts,
        valid_to: None,
        lat: Some(lat),
        lon: Some(lon),
        s2_cell_id: s2_cell_id(lat, lon, s2_level),
        geohash: geohash_encode(lat, lon, geohash_len),
        tags: tags_to_json(n.tags()),
        bbox_min_lng: Some(lon),
        bbox_min_lat: Some(lat),
        bbox_max_lng: Some(lon),
        bbox_max_lat: Some(lat),
    })
}

pub fn dense_node_to_vertex(
    n: &DenseNode,
    source_did: &str,
    owner_did: &str,
    s2_level: u64,
    geohash_len: usize,
) -> Option<VertexOsmElementRow> {
    let info = n.info();
    let version = info.map(|i| i.version()).unwrap_or(1);
    let lat = n.lat();
    let lon = n.lon();
    let ts = info.map(|i| i.milli_timestamp() / 1000);
    let (changeset, user, uid) = match info {
        Some(i) => (
            Some(i.changeset()),
            i.user().ok().map(|s| s.to_string()),
            Some(i.uid() as i64),
        ),
        None => (None, None, None),
    };
    Some(VertexOsmElementRow {
        vertex_id: format!("osm:n:{}:{}", n.id(), version),
        owner_did: owner_did.to_string(),
        source_did: source_did.to_string(),
        sensitivity_ord: 0,
        created_date: created_date_from_epoch(ts),
        osm_type: "n",
        osm_id: n.id(),
        version,
        changeset_id: changeset,
        user_name: user,
        uid,
        timestamp: ts,
        valid_from: ts,
        valid_to: None,
        lat: Some(lat),
        lon: Some(lon),
        s2_cell_id: s2_cell_id(lat, lon, s2_level),
        geohash: geohash_encode(lat, lon, geohash_len),
        tags: tags_to_json(n.tags()),
        bbox_min_lng: Some(lon),
        bbox_min_lat: Some(lat),
        bbox_max_lng: Some(lon),
        bbox_max_lat: Some(lat),
    })
}

pub fn way_to_rows(
    w: &Way,
    source_did: &str,
    owner_did: &str,
) -> (Option<VertexOsmElementRow>, Vec<EdgeWayNodeRow>) {
    let info = w.info();
    let version = info.version().unwrap_or(1);
    let ts = info.milli_timestamp().map(|ms| ms / 1000);
    let vertex_id = format!("osm:w:{}:{}", w.id(), version);
    let created_date = created_date_from_epoch(ts);

    let vertex = VertexOsmElementRow {
        vertex_id: vertex_id.clone(),
        owner_did: owner_did.to_string(),
        source_did: source_did.to_string(),
        sensitivity_ord: 0,
        created_date: created_date.clone(),
        osm_type: "w",
        osm_id: w.id(),
        version,
        changeset_id: info.changeset(),
        user_name: info_user(&info),
        uid: info.uid().map(|u| u as i64),
        timestamp: ts,
        valid_from: ts,
        valid_to: None,
        lat: None,
        lon: None,
        s2_cell_id: None,
        geohash: None,
        tags: tags_to_json(w.tags()),
        bbox_min_lng: None,
        bbox_min_lat: None,
        bbox_max_lng: None,
        bbox_max_lat: None,
    };

    let mut edges = Vec::new();
    for (seq, nid) in w.refs().enumerate() {
        edges.push(EdgeWayNodeRow {
            edge_id: format!("osm:wn:{}:{}:{}", w.id(), version, seq),
            owner_did: owner_did.to_string(),
            source_did: source_did.to_string(),
            created_date: created_date.clone(),
            way_vertex_id: vertex_id.clone(),
            // Node version is not known here — reference by (n, id, 0) as sentinel latest.
            node_vertex_id: format!("osm:n:{}:0", nid),
            seq: seq as i32,
            valid_from: ts,
            valid_to: None,
        });
    }
    (Some(vertex), edges)
}

pub fn relation_to_rows(
    r: &Relation,
    source_did: &str,
    owner_did: &str,
) -> (Option<VertexOsmElementRow>, Vec<EdgeRelationMemberRow>) {
    let info = r.info();
    let version = info.version().unwrap_or(1);
    let ts = info.milli_timestamp().map(|ms| ms / 1000);
    let vertex_id = format!("osm:r:{}:{}", r.id(), version);
    let created_date = created_date_from_epoch(ts);

    let vertex = VertexOsmElementRow {
        vertex_id: vertex_id.clone(),
        owner_did: owner_did.to_string(),
        source_did: source_did.to_string(),
        sensitivity_ord: 0,
        created_date: created_date.clone(),
        osm_type: "r",
        osm_id: r.id(),
        version,
        changeset_id: info.changeset(),
        user_name: info_user(&info),
        uid: info.uid().map(|u| u as i64),
        timestamp: ts,
        valid_from: ts,
        valid_to: None,
        lat: None,
        lon: None,
        s2_cell_id: None,
        geohash: None,
        tags: tags_to_json(r.tags()),
        bbox_min_lng: None,
        bbox_min_lat: None,
        bbox_max_lng: None,
        bbox_max_lat: None,
    };

    let mut edges = Vec::new();
    for (seq, m) in r.members().enumerate() {
        let (mt_char, mt_prefix) = match m.member_type {
            RelMemberType::Node => ("n", "n"),
            RelMemberType::Way => ("w", "w"),
            RelMemberType::Relation => ("r", "r"),
        };
        let role = m.role().unwrap_or("").to_string();
        edges.push(EdgeRelationMemberRow {
            edge_id: format!("osm:rm:{}:{}:{}", r.id(), version, seq),
            owner_did: owner_did.to_string(),
            source_did: source_did.to_string(),
            created_date: created_date.clone(),
            relation_vertex_id: vertex_id.clone(),
            member_vertex_id: format!("osm:{}:{}:0", mt_prefix, m.member_id),
            member_type: mt_char,
            role,
            seq: seq as i32,
            valid_from: ts,
            valid_to: None,
        });
    }
    (Some(vertex), edges)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn s2_level16_known_point() {
        // Tokyo Station.
        let id = s2_cell_id(35.6812, 139.7671, 16).unwrap();
        assert!(id != 0);
    }

    #[test]
    fn geohash_len8_known_point() {
        let g = geohash_encode(35.6812, 139.7671, 8).unwrap();
        assert_eq!(g.len(), 8);
    }

    #[test]
    fn epoch_date_smoketest() {
        assert_eq!(created_date_from_epoch(Some(0)), "1970-01-01");
        assert_eq!(created_date_from_epoch(None), "1970-01-01");
        // 2020-01-01 UTC = 1577836800
        assert_eq!(created_date_from_epoch(Some(1_577_836_800)), "2020-01-01");
    }

    #[test]
    fn _json_tags_compiles() {
        let _ = json!({});
    }
}
