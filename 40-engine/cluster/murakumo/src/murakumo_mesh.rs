use base64::Engine;
use chacha20poly1305::aead::{Aead, KeyInit};
use chacha20poly1305::{XChaCha20Poly1305, XNonce};
use rand::RngCore;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::net::{Ipv4Addr, SocketAddr, UdpSocket};
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};
use x25519_dalek::{PublicKey, StaticSecret};

const MESH_KEY_CTX: &[u8] = b"etzhayyim-murakumo-mesh-v1";

/// Mesh subnet: 10.99.0.0/16 (65534 peers max)
const MESH_SUBNET_PREFIX: [u8; 2] = [10, 99];
const MESH_UDP_PORT: u16 = 41820;
const STUN_TIMEOUT_MS: u64 = 3000;
const RELAY_MAGIC: &[u8; 4] = b"MREL";
const TUNNEL_MAGIC: &[u8; 4] = b"MTUN";
const KEEPALIVE_INTERVAL_SECS: u64 = 25;
const PEER_TIMEOUT_SECS: u64 = 90;
const REKEY_INTERVAL_SECS: u64 = 3600;

// ── Identity ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeshIdentity {
    pub node_id: String,
    pub public_key: String,
    pub secret_key: String,
    #[serde(default)]
    pub mesh_ip: String,
}

// ── Peer ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerEntry {
    pub node_id: String,
    pub public_key: String,
    #[serde(default)]
    pub endpoint: Option<String>,
    #[serde(default)]
    pub mesh_ip: String,
    #[serde(default)]
    pub relay_only: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegisterPeerRequest {
    pub node_id: String,
    pub public_key: String,
    #[serde(default)]
    pub endpoint: Option<String>,
    #[serde(default)]
    pub stun_endpoint: Option<String>,
    #[serde(default)]
    pub capabilities: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegisterPeerResponse {
    pub ok: bool,
    #[serde(default)]
    pub assigned: Option<PeerEntry>,
    #[serde(default)]
    pub mesh_ip: String,
    #[serde(default)]
    pub peers: Vec<PeerEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerListResponse {
    pub peers: Vec<PeerEntry>,
}

// ── Encrypted frame ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptedFrame {
    pub nonce: String,
    pub ciphertext: String,
}

// ── STUN ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StunResult {
    pub public_addr: String,
    pub nat_type: String,
}

// ── Tunnel packet header (binary, 16 bytes) ──
// [4] MTUN magic
// [4] src mesh IP
// [4] dst mesh IP
// [2] payload length (big-endian)
// [2] flags (0x01 = encrypted, 0x02 = keepalive, 0x04 = relay-forwarded)

#[derive(Debug, Clone)]
pub struct TunnelHeader {
    pub src_ip: Ipv4Addr,
    pub dst_ip: Ipv4Addr,
    pub payload_len: u16,
    pub flags: u16,
}

impl TunnelHeader {
    pub const SIZE: usize = 16;

    pub fn encode(&self) -> [u8; Self::SIZE] {
        let mut buf = [0u8; Self::SIZE];
        buf[0..4].copy_from_slice(TUNNEL_MAGIC);
        buf[4..8].copy_from_slice(&self.src_ip.octets());
        buf[8..12].copy_from_slice(&self.dst_ip.octets());
        buf[12..14].copy_from_slice(&self.payload_len.to_be_bytes());
        buf[14..16].copy_from_slice(&self.flags.to_be_bytes());
        buf
    }

    pub fn decode(buf: &[u8]) -> Result<Self, String> {
        if buf.len() < Self::SIZE {
            return Err("tunnel header too short".into());
        }
        if &buf[0..4] != TUNNEL_MAGIC {
            return Err("invalid tunnel magic".into());
        }
        Ok(Self {
            src_ip: Ipv4Addr::new(buf[4], buf[5], buf[6], buf[7]),
            dst_ip: Ipv4Addr::new(buf[8], buf[9], buf[10], buf[11]),
            payload_len: u16::from_be_bytes([buf[12], buf[13]]),
            flags: u16::from_be_bytes([buf[14], buf[15]]),
        })
    }

    pub fn is_encrypted(&self) -> bool {
        self.flags & 0x01 != 0
    }

    pub fn is_keepalive(&self) -> bool {
        self.flags & 0x02 != 0
    }

    pub fn is_relay_forwarded(&self) -> bool {
        self.flags & 0x04 != 0
    }
}

// ── Relay header (binary, 12 bytes) ──
// [4] MREL magic
// [4] destination mesh IP
// [4] source mesh IP

#[derive(Debug, Clone)]
pub struct RelayHeader {
    pub dst_ip: Ipv4Addr,
    pub src_ip: Ipv4Addr,
}

impl RelayHeader {
    pub const SIZE: usize = 12;

    pub fn encode(&self) -> [u8; Self::SIZE] {
        let mut buf = [0u8; Self::SIZE];
        buf[0..4].copy_from_slice(RELAY_MAGIC);
        buf[4..8].copy_from_slice(&self.dst_ip.octets());
        buf[8..12].copy_from_slice(&self.src_ip.octets());
        buf
    }

    pub fn decode(buf: &[u8]) -> Result<Self, String> {
        if buf.len() < Self::SIZE {
            return Err("relay header too short".into());
        }
        if &buf[0..4] != RELAY_MAGIC {
            return Err("invalid relay magic".into());
        }
        Ok(Self {
            dst_ip: Ipv4Addr::new(buf[4], buf[5], buf[6], buf[7]),
            src_ip: Ipv4Addr::new(buf[8], buf[9], buf[10], buf[11]),
        })
    }
}

// ── Routing table ──

#[derive(Debug, Clone)]
pub struct RouteEntry {
    pub mesh_ip: Ipv4Addr,
    pub node_id: String,
    pub public_key: String,
    pub direct_addr: Option<SocketAddr>,
    pub relay_addr: Option<SocketAddr>,
    pub last_seen: Instant,
    pub last_handshake: Instant,
    pub tx_bytes: u64,
    pub rx_bytes: u64,
    pub rtt_us: u64,
}

pub struct RoutingTable {
    routes: HashMap<Ipv4Addr, RouteEntry>,
    node_to_ip: HashMap<String, Ipv4Addr>,
}

impl RoutingTable {
    pub fn new() -> Self {
        Self {
            routes: HashMap::new(),
            node_to_ip: HashMap::new(),
        }
    }

    pub fn upsert(&mut self, entry: RouteEntry) {
        self.node_to_ip.insert(entry.node_id.clone(), entry.mesh_ip);
        self.routes.insert(entry.mesh_ip, entry);
    }

    pub fn lookup_ip(&self, ip: &Ipv4Addr) -> Option<&RouteEntry> {
        self.routes.get(ip)
    }

    pub fn lookup_node(&self, node_id: &str) -> Option<&RouteEntry> {
        self.node_to_ip.get(node_id).and_then(|ip| self.routes.get(ip))
    }

    pub fn resolve_addr(&self, dst: &Ipv4Addr) -> Option<SocketAddr> {
        self.routes.get(dst).and_then(|r| {
            r.direct_addr.or(r.relay_addr)
        })
    }

    pub fn remove_stale(&mut self, timeout: Duration) -> Vec<String> {
        let now = Instant::now();
        let stale: Vec<Ipv4Addr> = self.routes.iter()
            .filter(|(_, r)| now.duration_since(r.last_seen) > timeout)
            .map(|(ip, _)| *ip)
            .collect();
        let mut removed = Vec::new();
        for ip in stale {
            if let Some(entry) = self.routes.remove(&ip) {
                self.node_to_ip.remove(&entry.node_id);
                removed.push(entry.node_id);
            }
        }
        removed
    }

    pub fn all_peers(&self) -> Vec<&RouteEntry> {
        self.routes.values().collect()
    }

    pub fn peer_count(&self) -> usize {
        self.routes.len()
    }

    pub fn update_last_seen(&mut self, ip: &Ipv4Addr) {
        if let Some(entry) = self.routes.get_mut(ip) {
            entry.last_seen = Instant::now();
        }
    }

    pub fn update_rtt(&mut self, ip: &Ipv4Addr, rtt_us: u64) {
        if let Some(entry) = self.routes.get_mut(ip) {
            entry.rtt_us = rtt_us;
        }
    }

    pub fn add_tx_bytes(&mut self, ip: &Ipv4Addr, n: u64) {
        if let Some(entry) = self.routes.get_mut(ip) {
            entry.tx_bytes += n;
        }
    }

    pub fn add_rx_bytes(&mut self, ip: &Ipv4Addr, n: u64) {
        if let Some(entry) = self.routes.get_mut(ip) {
            entry.rx_bytes += n;
        }
    }
}

// ── Mesh DNS resolver ──

pub struct MeshDns {
    table: Arc<RwLock<RoutingTable>>,
    suffix: String,
}

impl MeshDns {
    pub fn new(table: Arc<RwLock<RoutingTable>>) -> Self {
        Self {
            table,
            suffix: ".mesh.etzhayyim.com".to_string(),
        }
    }

    /// Resolve node-id.mesh.etzhayyim.com → mesh IP
    pub fn resolve(&self, name: &str) -> Option<Ipv4Addr> {
        let node_id = name.strip_suffix(&self.suffix)?;
        let table = self.table.read().ok()?;
        table.lookup_node(node_id).map(|r| r.mesh_ip)
    }

    /// Reverse: mesh IP → node-id.mesh.etzhayyim.com
    pub fn reverse(&self, ip: &Ipv4Addr) -> Option<String> {
        let table = self.table.read().ok()?;
        table.lookup_ip(ip).map(|r| format!("{}{}", r.node_id, self.suffix))
    }
}

// ── Mesh IP allocation ──

/// Allocate mesh IP from node_id hash (deterministic)
pub fn allocate_mesh_ip(node_id: &str) -> Ipv4Addr {
    let hash = blake3::hash(node_id.as_bytes());
    let bytes = hash.as_bytes();
    // 10.99.H.L where H,L derived from hash (avoid .0.0 and .255.255)
    let h = bytes[0].max(1);
    let l = bytes[1].max(1).min(254);
    Ipv4Addr::new(MESH_SUBNET_PREFIX[0], MESH_SUBNET_PREFIX[1], h, l)
}

/// Check if IP is in the mesh subnet
pub fn is_mesh_ip(ip: &Ipv4Addr) -> bool {
    let octets = ip.octets();
    octets[0] == MESH_SUBNET_PREFIX[0] && octets[1] == MESH_SUBNET_PREFIX[1]
}

// ── STUN client (lightweight, RFC 5389 Binding Request) ──

pub fn stun_discover(stun_server: &str) -> Result<StunResult, String> {
    let addr: SocketAddr = stun_server
        .parse()
        .map_err(|e| format!("invalid stun server: {e}"))?;

    let sock = UdpSocket::bind("0.0.0.0:0")
        .map_err(|e| format!("bind failed: {e}"))?;
    sock.set_read_timeout(Some(Duration::from_millis(STUN_TIMEOUT_MS)))
        .map_err(|e| format!("set timeout: {e}"))?;

    // STUN Binding Request (RFC 5389)
    // Type: 0x0001, Length: 0, Magic Cookie: 0x2112A442, Transaction ID: 12 random bytes
    let mut req = [0u8; 20];
    req[0] = 0x00; req[1] = 0x01; // Binding Request
    req[2] = 0x00; req[3] = 0x00; // Length = 0
    req[4] = 0x21; req[5] = 0x12; req[6] = 0xA4; req[7] = 0x42; // Magic Cookie
    rand::thread_rng().fill_bytes(&mut req[8..20]);

    sock.send_to(&req, addr)
        .map_err(|e| format!("stun send: {e}"))?;

    let mut buf = [0u8; 256];
    let (n, _) = sock.recv_from(&mut buf)
        .map_err(|e| format!("stun recv: {e}"))?;

    if n < 20 {
        return Err("stun response too short".into());
    }

    // Parse MAPPED-ADDRESS or XOR-MAPPED-ADDRESS from response
    let mut offset = 20; // skip header
    while offset + 4 <= n {
        let attr_type = u16::from_be_bytes([buf[offset], buf[offset + 1]]);
        let attr_len = u16::from_be_bytes([buf[offset + 2], buf[offset + 3]]) as usize;
        let attr_start = offset + 4;

        if attr_type == 0x0020 && attr_len >= 8 {
            // XOR-MAPPED-ADDRESS
            let port = u16::from_be_bytes([buf[attr_start + 2], buf[attr_start + 3]]) ^ 0x2112;
            let ip = Ipv4Addr::new(
                buf[attr_start + 4] ^ 0x21,
                buf[attr_start + 5] ^ 0x12,
                buf[attr_start + 6] ^ 0xA4,
                buf[attr_start + 7] ^ 0x42,
            );
            return Ok(StunResult {
                public_addr: format!("{}:{}", ip, port),
                nat_type: "cone".to_string(),
            });
        } else if attr_type == 0x0001 && attr_len >= 8 {
            // MAPPED-ADDRESS
            let port = u16::from_be_bytes([buf[attr_start + 2], buf[attr_start + 3]]);
            let ip = Ipv4Addr::new(
                buf[attr_start + 4],
                buf[attr_start + 5],
                buf[attr_start + 6],
                buf[attr_start + 7],
            );
            return Ok(StunResult {
                public_addr: format!("{}:{}", ip, port),
                nat_type: "unknown".to_string(),
            });
        }

        offset = attr_start + ((attr_len + 3) & !3); // 4-byte aligned
    }

    Err("no mapped address in stun response".into())
}

/// Detect NAT type by comparing two STUN responses
pub fn detect_nat_type(stun_servers: &[&str]) -> String {
    if stun_servers.len() < 2 {
        return match stun_discover(stun_servers.first().unwrap_or(&"")) {
            Ok(_) => "unknown".to_string(),
            Err(_) => "blocked".to_string(),
        };
    }

    let r1 = stun_discover(stun_servers[0]);
    let r2 = stun_discover(stun_servers[1]);

    match (r1, r2) {
        (Ok(a), Ok(b)) => {
            if a.public_addr == b.public_addr {
                "full_cone".to_string()
            } else {
                // Different mapped addresses = symmetric NAT (relay needed)
                "symmetric".to_string()
            }
        }
        (Ok(_), Err(_)) | (Err(_), Ok(_)) => "restricted".to_string(),
        (Err(_), Err(_)) => "blocked".to_string(),
    }
}

// ── Tunnel state ──

pub struct MeshTunnel {
    pub identity: MeshIdentity,
    pub local_ip: Ipv4Addr,
    pub socket: UdpSocket,
    pub routing: Arc<RwLock<RoutingTable>>,
    pub dns: MeshDns,
    pub control_plane: String,
    pub relay_addr: Option<SocketAddr>,
}

impl MeshTunnel {
    /// Bind UDP socket and initialize tunnel
    pub fn new(
        identity: MeshIdentity,
        control_plane: String,
        relay_addr: Option<SocketAddr>,
    ) -> Result<Self, String> {
        let local_ip: Ipv4Addr = if identity.mesh_ip.is_empty() {
            allocate_mesh_ip(&identity.node_id)
        } else {
            identity.mesh_ip.parse().map_err(|e| format!("invalid mesh_ip: {e}"))?
        };

        let socket = UdpSocket::bind(format!("0.0.0.0:{}", MESH_UDP_PORT))
            .or_else(|_| UdpSocket::bind("0.0.0.0:0"))
            .map_err(|e| format!("bind udp: {e}"))?;
        socket.set_nonblocking(true)
            .map_err(|e| format!("set nonblocking: {e}"))?;

        let routing = Arc::new(RwLock::new(RoutingTable::new()));
        let dns = MeshDns::new(routing.clone());

        Ok(Self {
            identity: MeshIdentity {
                mesh_ip: local_ip.to_string(),
                ..identity
            },
            local_ip,
            socket,
            routing,
            dns,
            control_plane,
            relay_addr,
        })
    }

    /// Send encrypted tunnel packet to peer
    pub fn send_to_peer(&self, dst_ip: Ipv4Addr, payload: &[u8]) -> Result<usize, String> {
        let route = {
            let table = self.routing.read().map_err(|e| e.to_string())?;
            table.lookup_ip(&dst_ip).cloned()
        };

        let route = route.ok_or_else(|| format!("no route to {}", dst_ip))?;

        let encrypted = encrypt_frame(
            &self.identity.secret_key,
            &route.public_key,
            payload,
        )?;
        let enc_bytes = serde_json::to_vec(&encrypted).map_err(|e| e.to_string())?;

        let header = TunnelHeader {
            src_ip: self.local_ip,
            dst_ip,
            payload_len: enc_bytes.len() as u16,
            flags: 0x01, // encrypted
        };

        let mut packet = Vec::with_capacity(TunnelHeader::SIZE + enc_bytes.len());
        packet.extend_from_slice(&header.encode());
        packet.extend_from_slice(&enc_bytes);

        let target = if let Some(direct) = route.direct_addr {
            direct
        } else if let Some(relay) = route.relay_addr.or(self.relay_addr) {
            // Wrap in relay header
            let rh = RelayHeader { dst_ip, src_ip: self.local_ip };
            let mut relay_packet = Vec::with_capacity(RelayHeader::SIZE + packet.len());
            relay_packet.extend_from_slice(&rh.encode());
            relay_packet.extend_from_slice(&packet);
            self.socket.send_to(&relay_packet, relay)
                .map_err(|e| format!("relay send: {e}"))?;

            if let Ok(mut table) = self.routing.write() {
                table.add_tx_bytes(&dst_ip, relay_packet.len() as u64);
            }
            return Ok(payload.len());
        } else {
            return Err(format!("no direct or relay route to {}", dst_ip));
        };

        let sent = self.socket.send_to(&packet, target)
            .map_err(|e| format!("send: {e}"))?;

        if let Ok(mut table) = self.routing.write() {
            table.add_tx_bytes(&dst_ip, sent as u64);
        }
        Ok(payload.len())
    }

    /// Send keepalive to all peers
    pub fn send_keepalives(&self) {
        let peers: Vec<(Ipv4Addr, Option<SocketAddr>, String)> = {
            let table = self.routing.read().unwrap();
            table.all_peers().iter().map(|r| {
                (r.mesh_ip, r.direct_addr.or(r.relay_addr).or(self.relay_addr), r.public_key.clone())
            }).collect()
        };

        for (dst_ip, addr, _pk) in peers {
            if let Some(target) = addr {
                let header = TunnelHeader {
                    src_ip: self.local_ip,
                    dst_ip,
                    payload_len: 0,
                    flags: 0x02, // keepalive
                };
                let _ = self.socket.send_to(&header.encode(), target);
            }
        }
    }

    /// Process incoming packet from UDP socket
    pub fn process_incoming(&self, buf: &[u8], from: SocketAddr) -> Result<Option<Vec<u8>>, String> {
        // Check for relay header
        if buf.len() >= RelayHeader::SIZE && &buf[0..4] == RELAY_MAGIC {
            let rh = RelayHeader::decode(buf)?;
            // If addressed to us, unwrap and process inner tunnel packet
            if rh.dst_ip == self.local_ip {
                return self.process_incoming(&buf[RelayHeader::SIZE..], from);
            }
            // Otherwise forward (if we're acting as relay)
            return Ok(None);
        }

        if buf.len() < TunnelHeader::SIZE {
            return Err("packet too short".into());
        }

        let header = TunnelHeader::decode(buf)?;

        // Update routing: we now know this peer's direct address
        if let Ok(mut table) = self.routing.write() {
            table.update_last_seen(&header.src_ip);
            table.add_rx_bytes(&header.src_ip, buf.len() as u64);
            // If this came direct (not relayed), update direct_addr
            if !header.is_relay_forwarded() {
                if let Some(entry) = table.routes.get_mut(&header.src_ip) {
                    entry.direct_addr = Some(from);
                }
            }
        }

        if header.is_keepalive() {
            return Ok(None);
        }

        if !header.is_encrypted() {
            let payload = buf[TunnelHeader::SIZE..TunnelHeader::SIZE + header.payload_len as usize].to_vec();
            return Ok(Some(payload));
        }

        // Decrypt
        let enc_bytes = &buf[TunnelHeader::SIZE..TunnelHeader::SIZE + header.payload_len as usize];
        let frame: EncryptedFrame = serde_json::from_slice(enc_bytes)
            .map_err(|e| format!("decode frame: {e}"))?;

        let peer_pk = {
            let table = self.routing.read().map_err(|e| e.to_string())?;
            table.lookup_ip(&header.src_ip).map(|r| r.public_key.clone())
        };

        let peer_pk = peer_pk.ok_or_else(|| format!("unknown peer: {}", header.src_ip))?;
        let plaintext = decrypt_frame(&self.identity.secret_key, &peer_pk, &frame)?;
        Ok(Some(plaintext))
    }

    /// Add a peer to the routing table
    pub fn add_peer(&self, peer: &PeerEntry) {
        let mesh_ip: Ipv4Addr = if peer.mesh_ip.is_empty() {
            allocate_mesh_ip(&peer.node_id)
        } else {
            peer.mesh_ip.parse().unwrap_or_else(|_| allocate_mesh_ip(&peer.node_id))
        };

        let direct_addr = peer.endpoint.as_ref().and_then(|e| e.parse().ok());

        let entry = RouteEntry {
            mesh_ip,
            node_id: peer.node_id.clone(),
            public_key: peer.public_key.clone(),
            direct_addr,
            relay_addr: if peer.relay_only { self.relay_addr } else { None },
            last_seen: Instant::now(),
            last_handshake: Instant::now(),
            tx_bytes: 0,
            rx_bytes: 0,
            rtt_us: 0,
        };

        if let Ok(mut table) = self.routing.write() {
            table.upsert(entry);
        }
    }

    /// Remove stale peers and return removed node IDs
    pub fn gc_stale_peers(&self) -> Vec<String> {
        if let Ok(mut table) = self.routing.write() {
            table.remove_stale(Duration::from_secs(PEER_TIMEOUT_SECS))
        } else {
            vec![]
        }
    }

    /// Get mesh status summary
    pub fn status(&self) -> MeshStatus {
        let table = self.routing.read().unwrap();
        let peers: Vec<MeshPeerStatus> = table.all_peers().iter().map(|r| {
            MeshPeerStatus {
                node_id: r.node_id.clone(),
                mesh_ip: r.mesh_ip.to_string(),
                direct: r.direct_addr.is_some(),
                relay: r.relay_addr.is_some(),
                rtt_us: r.rtt_us,
                tx_bytes: r.tx_bytes,
                rx_bytes: r.rx_bytes,
                last_seen_secs: Instant::now().duration_since(r.last_seen).as_secs(),
            }
        }).collect();

        MeshStatus {
            node_id: self.identity.node_id.clone(),
            mesh_ip: self.local_ip.to_string(),
            peer_count: peers.len(),
            peers,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeshPeerStatus {
    pub node_id: String,
    pub mesh_ip: String,
    pub direct: bool,
    pub relay: bool,
    pub rtt_us: u64,
    pub tx_bytes: u64,
    pub rx_bytes: u64,
    pub last_seen_secs: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeshStatus {
    pub node_id: String,
    pub mesh_ip: String,
    pub peer_count: usize,
    pub peers: Vec<MeshPeerStatus>,
}

// ── Control plane API ──

pub async fn register_peer(
    client: &Client,
    control_plane: &str,
    req: &RegisterPeerRequest,
) -> Result<RegisterPeerResponse, String> {
    let url = format!("{}/api/murakumo-mesh/register", control_plane.trim_end_matches('/'));
    let resp = client
        .post(url)
        .json(req)
        .send()
        .await
        .map_err(|e| format!("register request failed: {e}"))?;

    if !resp.status().is_success() {
        let code = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(format!("register failed: {code} {body}"));
    }

    resp.json::<RegisterPeerResponse>()
        .await
        .map_err(|e| format!("register decode failed: {e}"))
}

pub async fn list_peers(client: &Client, control_plane: &str) -> Result<PeerListResponse, String> {
    let url = format!("{}/api/murakumo-mesh/peers", control_plane.trim_end_matches('/'));
    let resp = client
        .get(url)
        .send()
        .await
        .map_err(|e| format!("peers request failed: {e}"))?;
    if !resp.status().is_success() {
        let code = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(format!("peers failed: {code} {body}"));
    }
    resp.json::<PeerListResponse>()
        .await
        .map_err(|e| format!("peers decode failed: {e}"))
}

pub async fn heartbeat_mesh(
    client: &Client,
    control_plane: &str,
    node_id: &str,
    mesh_ip: &str,
    peer_count: usize,
) -> Result<(), String> {
    let url = format!("{}/api/murakumo-mesh/heartbeat", control_plane.trim_end_matches('/'));
    let body = serde_json::json!({
        "node_id": node_id,
        "mesh_ip": mesh_ip,
        "peer_count": peer_count,
    });
    let resp = client.post(url).json(&body).send().await
        .map_err(|e| format!("mesh heartbeat: {e}"))?;
    if !resp.status().is_success() {
        let code = resp.status();
        return Err(format!("mesh heartbeat failed: {code}"));
    }
    Ok(())
}

// ── Crypto primitives ──

pub fn generate_identity(node_id: String) -> MeshIdentity {
    let mut secret = [0u8; 32];
    rand::thread_rng().fill_bytes(&mut secret);
    let static_secret = StaticSecret::from(secret);
    let public = PublicKey::from(&static_secret);
    let mesh_ip = allocate_mesh_ip(&node_id).to_string();

    MeshIdentity {
        node_id,
        public_key: b64_encode(public.as_bytes()),
        secret_key: b64_encode(static_secret.to_bytes()),
        mesh_ip,
    }
}

pub fn encrypt_frame(
    local_secret_key_b64: &str,
    peer_public_key_b64: &str,
    plaintext: &[u8],
) -> Result<EncryptedFrame, String> {
    let secret = parse_secret(local_secret_key_b64)?;
    let peer_public = parse_public(peer_public_key_b64)?;
    let shared = secret.diffie_hellman(&peer_public);
    let key = derive_key(shared.as_bytes());
    let cipher = XChaCha20Poly1305::new_from_slice(&key).map_err(|e| e.to_string())?;

    let mut nonce = [0u8; 24];
    rand::thread_rng().fill_bytes(&mut nonce);
    let ciphertext = cipher
        .encrypt(XNonce::from_slice(&nonce), plaintext)
        .map_err(|e| format!("encrypt failed: {e}"))?;

    Ok(EncryptedFrame {
        nonce: b64_encode(&nonce),
        ciphertext: b64_encode(&ciphertext),
    })
}

pub fn decrypt_frame(
    local_secret_key_b64: &str,
    peer_public_key_b64: &str,
    frame: &EncryptedFrame,
) -> Result<Vec<u8>, String> {
    let secret = parse_secret(local_secret_key_b64)?;
    let peer_public = parse_public(peer_public_key_b64)?;
    let nonce = b64_decode(&frame.nonce)?;
    let ciphertext = b64_decode(&frame.ciphertext)?;
    if nonce.len() != 24 {
        return Err("nonce length must be 24 bytes".to_string());
    }

    let shared = secret.diffie_hellman(&peer_public);
    let key = derive_key(shared.as_bytes());
    let cipher = XChaCha20Poly1305::new_from_slice(&key).map_err(|e| e.to_string())?;
    cipher
        .decrypt(XNonce::from_slice(&nonce), ciphertext.as_slice())
        .map_err(|e| format!("decrypt failed: {e}"))
}

fn derive_key(shared_secret: &[u8]) -> [u8; 32] {
    let mut hasher = blake3::Hasher::new();
    hasher.update(MESH_KEY_CTX);
    hasher.update(shared_secret);
    *hasher.finalize().as_bytes()
}

fn parse_secret(key_b64: &str) -> Result<StaticSecret, String> {
    let bytes = b64_decode(key_b64)?;
    if bytes.len() != 32 {
        return Err("secret key length must be 32 bytes".to_string());
    }
    let mut key = [0u8; 32];
    key.copy_from_slice(&bytes);
    Ok(StaticSecret::from(key))
}

fn parse_public(key_b64: &str) -> Result<PublicKey, String> {
    let bytes = b64_decode(key_b64)?;
    if bytes.len() != 32 {
        return Err("public key length must be 32 bytes".to_string());
    }
    let mut key = [0u8; 32];
    key.copy_from_slice(&bytes);
    Ok(PublicKey::from(key))
}

fn b64_encode(bytes: impl AsRef<[u8]>) -> String {
    base64::engine::general_purpose::STANDARD_NO_PAD.encode(bytes)
}

fn b64_decode(input: &str) -> Result<Vec<u8>, String> {
    base64::engine::general_purpose::STANDARD_NO_PAD
        .decode(input)
        .map_err(|e| format!("base64 decode failed: {e}"))
}

// ── Mesh daemon loop (runs inside tokio) ──

pub async fn run_mesh_daemon(
    tunnel: Arc<MeshTunnel>,
    client: Client,
) {
    let keepalive_interval = Duration::from_secs(KEEPALIVE_INTERVAL_SECS);
    let gc_interval = Duration::from_secs(60);
    let sync_interval = Duration::from_secs(30);

    let mut keepalive_tick = tokio::time::interval(keepalive_interval);
    let mut gc_tick = tokio::time::interval(gc_interval);
    let mut sync_tick = tokio::time::interval(sync_interval);

    // Initial peer sync (best-effort, silent on 404)
    let mut cp_available = sync_peers(&tunnel, &client).await.is_ok();

    loop {
        tokio::select! {
            _ = keepalive_tick.tick() => {
                tunnel.send_keepalives();
            }
            _ = gc_tick.tick() => {
                let removed = tunnel.gc_stale_peers();
                for node_id in &removed {
                    eprintln!("mesh: peer timed out: {}", node_id);
                }
            }
            _ = sync_tick.tick() => {
                match sync_peers(&tunnel, &client).await {
                    Ok(()) => {
                        if !cp_available {
                            eprintln!("mesh: control plane connected");
                            cp_available = true;
                        }
                    }
                    Err(e) => {
                        // Only log once when control plane goes away
                        if cp_available {
                            eprintln!("mesh: control plane unavailable (LAN mode): {}", e);
                            cp_available = false;
                        }
                    }
                }
                if cp_available {
                    let status = tunnel.status();
                    let _ = heartbeat_mesh(
                        &client, &tunnel.control_plane,
                        &tunnel.identity.node_id, &tunnel.identity.mesh_ip,
                        status.peer_count,
                    ).await;
                }
            }
        }
    }
}

/// Sync peer list from control plane
async fn sync_peers(tunnel: &MeshTunnel, client: &Client) -> Result<(), String> {
    let resp = list_peers(client, &tunnel.control_plane).await?;
    for peer in &resp.peers {
        if peer.node_id == tunnel.identity.node_id {
            continue; // skip self
        }
        tunnel.add_peer(peer);
    }
    Ok(())
}

/// UDP receive loop (runs in dedicated thread via tokio::task::spawn_blocking)
pub fn recv_loop(tunnel: Arc<MeshTunnel>) {
    let mut buf = [0u8; 65536];
    loop {
        // Use blocking recv since socket is set to non-blocking,
        // we need to use a small sleep to avoid busy-wait
        match tunnel.socket.recv_from(&mut buf) {
            Ok((n, from)) => {
                if let Err(e) = tunnel.process_incoming(&buf[..n], from) {
                    if crate::VERBOSE.load(std::sync::atomic::Ordering::Relaxed) {
                        eprintln!("mesh: recv error from {}: {}", from, e);
                    }
                }
            }
            Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                std::thread::sleep(Duration::from_millis(10));
            }
            Err(e) => {
                eprintln!("mesh: recv fatal: {}", e);
                break;
            }
        }
    }
}
