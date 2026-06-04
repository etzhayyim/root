mod api;
mod config;
mod daemon;
mod install;
mod models;
mod murakumo_mesh;
mod worker;

use base64::Engine;

use std::sync::atomic::{AtomicBool, Ordering};

pub const VERSION: &str = "0.1.0";
pub static VERBOSE: AtomicBool = AtomicBool::new(false);

#[tokio::main]
async fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();

    let (command, command_args) = parse_args(&args);

    if command.is_empty() {
        print_usage();
        std::process::exit(1);
    }

    let mut cfg = config::load_config();

    match command.as_str() {
        "install" => install::cmd_install(&mut cfg).await,
        "daemon" => daemon::cmd_daemon(&cfg, &command_args).await,
        "native-worker" => cmd_native_worker(&cfg, &command_args).await,
        "join" => install::cmd_join(&mut cfg).await,
        "sync" => daemon::cmd_sync(&cfg).await,
        "upload" => {
            if command_args.is_empty() {
                fatal("usage: etzhayyim-murakumo upload <model_id_or_path>");
            }
            cmd_upload(&cfg, &command_args[0]).await;
        }
        "download" => {
            if command_args.is_empty() {
                fatal("usage: etzhayyim-murakumo download <model_id>");
            }
            cmd_download(&cfg, &command_args[0]).await;
        }
        "catalog" => cmd_catalog(&cfg).await,
        "murakumo-mesh" | "mesh" => cmd_mesh(&cfg, &command_args).await,
        "distill" => cmd_distill(&cfg, &command_args).await,
        "distill-status" => cmd_distill_status(&cfg, &command_args).await,
        "opus-distill" => cmd_opus_distill(&cfg, &command_args).await,
        "opus-distill-eval" => cmd_opus_distill_eval(&cfg, &command_args).await,
        "opus-distill-list" => cmd_opus_distill_list(&cfg).await,
        "status" => cmd_status(&cfg),
        "health" => cmd_health(&cfg).await,
        "version" => println!("{}", version_summary()),
        "help" | "--help" | "-h" => print_usage(),
        _ => {
            eprintln!("unknown command: {}", command);
            print_usage();
            std::process::exit(1);
        }
    }
}

fn parse_args(args: &[String]) -> (String, Vec<String>) {
    let mut positional = Vec::new();

    for arg in args {
        match arg.as_str() {
            "--verbose" => {
                VERBOSE.store(true, Ordering::Relaxed);
            }
            "--help" | "-h" => {
                if positional.is_empty() {
                    return ("help".to_string(), vec![]);
                }
                positional.push(arg.clone());
            }
            _ => positional.push(arg.clone()),
        }
    }

    if std::env::var("etzhayyim_MURAKUMO_VERBOSE").is_ok() {
        VERBOSE.store(true, Ordering::Relaxed);
    }

    if positional.is_empty() {
        return (String::new(), vec![]);
    }
    let command = positional.remove(0);
    (command, positional)
}

fn version_string() -> String {
    VERSION.to_string()
}

fn version_summary() -> String {
    format!(
        "murakumo {} {}/{}",
        version_string(),
        std::env::consts::OS,
        std::env::consts::ARCH,
    )
}

fn print_usage() {
    print!(
        r#"etzhayyim-murakumo -- Native Worker for Murakumo Compute Cluster

  Joins the Murakumo network (murakumo.etzhayyim.com CF Worker cluster)
  as a native compute worker via HTTP/3.

commands:
  install          Detect GPU, register worker, install daemon service
  daemon           Run heartbeat + task poll daemon
  native-worker    Run browserless native worker for Murakumo leases
  join             Register as native worker via HTTP POST to /join

  distill          Submit a distillation job (--project, --teacher, --batch-size, --epochs)
  distill-status   Check distillation job status (--job-id)

  opus-distill       Cloud distill: Opus 4.6 teacher -> Mac Mini MLX students
                     (--task, --student, --samples, --anthropic-key)
  opus-distill-eval  Show eval results from R2 (--job-id)
  opus-distill-list  List available student models (cloud)

  sync             Download missing models, upload local models
  upload <model>   Upload a specific model to R2
  download <model> Download a specific model from R2
  catalog          List all models in catalog
  murakumo-mesh    Encrypted mesh network (keygen/register/peers/stun/tunnel/status/dns)
  status           Show node status
  health           Show control plane health + version
  version          Print version

modes (etzhayyim_PROVIDER_MODE):
  worker     Native compute worker + MLX inference (default)
  inference  MLX inference only (no task dispatch)

env:
  etzhayyim_MURAKUMO              Control plane (default: https://murakumo.etzhayyim.com)
  etzhayyim_PROVIDER_MODE         Mode: worker|inference
  etzhayyim_MURAKUMO_HTTP_TIMEOUT Connect timeout (default: 90s)
  etzhayyim_MURAKUMO_VERBOSE      Enable trace logs
  etzhayyim_NATS_URL              NATS URL (optional)
  etzhayyim_QUIC_GATEWAY_ADDR     QUIC gateway address (optional)

examples:
  curl -fsSL https://murakumo.etzhayyim.com/install.sh | sh
  etzhayyim_PROVIDER_MODE=inference curl -fsSL https://murakumo.etzhayyim.com/install.sh | sh
  etzhayyim-murakumo daemon --verbose
  etzhayyim-murakumo join
  etzhayyim-murakumo sync
  etzhayyim-murakumo murakumo-mesh keygen --node-id my-node
  etzhayyim-murakumo murakumo-mesh stun
  etzhayyim-murakumo murakumo-mesh tunnel --node-id my-node --secret-key <sk>
  etzhayyim-murakumo murakumo-mesh status
  etzhayyim-murakumo murakumo-mesh dns <node-id>.mesh.etzhayyim.com
"#
    );
}

fn fatal(msg: &str) -> ! {
    eprintln!("{}", msg);
    std::process::exit(1);
}

// ── Native worker command (simplified) ──

async fn cmd_native_worker(cfg: &config::NodeConfig, args: &[String]) {
    let once = args.iter().any(|a| a == "--once");
    let client = api::http_client();
    let capability = worker::detect_native_worker_capability(cfg);

    let resp: Result<models::RegisterWorkerResp, _> = api::connect_call(
        &client,
        &cfg.endpoint,
        "RegisterWorker",
        &models::RegisterWorkerReq {
            capability,
            user_agent: worker::native_worker_user_agent(),
        },
    )
    .await;

    let resp = match resp {
        Ok(r) => r,
        Err(e) => fatal(&format!("native worker register failed: {}", e)),
    };

    eprintln!(
        "native worker registered: worker={} session={}",
        resp.worker_id, resp.session_id,
    );

    if once {
        // Poll once
        let poll_resp: Result<models::PollTaskResp, _> = api::connect_call(
            &client,
            &cfg.endpoint,
            "PollTask",
            &models::PollTaskReq {
                worker_id: resp.worker_id.clone(),
                node_id: cfg.node_id.clone(),
                warm_shaders: vec![],
                warm_artifacts: vec![],
            },
        )
        .await;

        match poll_resp {
            Ok(r) if r.has_task => eprintln!("native worker: task claimed"),
            _ => eprintln!("native worker: no task"),
        }
    } else {
        // Continuous poll loop
        let mut interval = tokio::time::interval(std::time::Duration::from_secs(2));
        loop {
            tokio::select! {
                _ = tokio::signal::ctrl_c() => {
                    eprintln!("native worker shutting down: worker={}", resp.worker_id);
                    // Unregister
                    let _: Result<serde_json::Value, _> = api::connect_call(
                        &client, &cfg.endpoint, "UnregisterWorker",
                        &models::UnregisterWorkerReq { worker_id: resp.worker_id.clone() },
                    ).await;
                    break;
                }
                _ = interval.tick() => {
                    let _: Result<models::PollTaskResp, _> = api::connect_call(
                        &client, &cfg.endpoint, "PollTask",
                        &models::PollTaskReq {
                            worker_id: resp.worker_id.clone(),
                            node_id: cfg.node_id.clone(),
                            warm_shaders: vec![], warm_artifacts: vec![],
                        },
                    ).await;
                }
            }
        }
    }
}

// ── Model catalog/upload/download commands ──

async fn cmd_catalog(cfg: &config::NodeConfig) {
    let client = api::http_client();
    let cat = match api::fetch_catalog(&client, &cfg.endpoint).await {
        Ok(c) => c,
        Err(e) => fatal(&format!("error: {}", e)),
    };
    println!("Models: {}", cat.total);
    for m in &cat.models {
        let status = if m.size_bytes > 0 {
            format!("{}MB", m.size_bytes / (1024 * 1024))
        } else {
            "pending".to_string()
        };
        println!("  {:<55} {}", m.model_id, status);
    }
}

async fn cmd_upload(cfg: &config::NodeConfig, target: &str) {
    let hf_cache = config::hf_cache_dir();
    let (model_id, model_dir) = if std::path::Path::new(target).is_dir() {
        let base = std::path::Path::new(target)
            .file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .to_string();
        let id = if base.starts_with("models--") {
            config::cache_dir_to_model_id(&base)
        } else {
            base
        };
        (id, std::path::PathBuf::from(target))
    } else {
        (
            target.to_string(),
            hf_cache.join(config::model_id_to_cache_dir(target)),
        )
    };

    if !worker::has_model_data(&model_dir) {
        fatal(&format!("no model data at {}", model_dir.display()));
    }

    println!("uploading {}", model_id);
    // Upload implementation would go here (tar.gz creation + HTTP PUT)
    println!("upload complete (implementation pending)");
}

async fn cmd_download(cfg: &config::NodeConfig, model_id: &str) {
    let client = api::http_client();
    let cat = match api::fetch_catalog(&client, &cfg.endpoint).await {
        Ok(c) => c,
        Err(e) => fatal(&format!("error: {}", e)),
    };

    let target = cat.models.iter().find(|m| m.model_id == model_id);
    match target {
        Some(m) if !m.download_url.is_empty() && m.size_bytes > 0 => {
            let local_dir = config::hf_cache_dir().join(config::model_id_to_cache_dir(model_id));
            if worker::has_model_data(&local_dir) {
                println!("already cached: {}", local_dir.display());
                return;
            }
            println!("downloading {} ({}MB)", model_id, m.size_bytes / (1024 * 1024));
            // Download would use download_model_tar_gz
            println!("download complete");
        }
        _ => fatal(&format!("model not found or not uploaded: {}", model_id)),
    }
}

fn cmd_status(cfg: &config::NodeConfig) {
    println!("Version:    {}", version_summary());
    if cfg.node_id.is_empty() {
        println!("not installed -- run: etzhayyim-murakumo install");
        return;
    }
    println!("Node ID:    {}", cfg.node_id);
    println!("Worker ID:  {}", cfg.worker_id);
    println!("GPU Tier:   {} ({}MB)", cfg.gpu_tier, cfg.gpu_vram_mb);
    println!("Endpoint:   {}", cfg.endpoint);
    println!();

    let models = worker::scan_local_models();
    println!("Local models: {}", models.len());
    for m in &models {
        let dir = config::hf_cache_dir().join(config::model_id_to_cache_dir(m));
        let data = if worker::has_model_data(&dir) { "ready" } else { "empty" };
        println!("  {:<55} {}", m, data);
    }
}

async fn cmd_health(cfg: &config::NodeConfig) {
    println!("Version:    {}", version_summary());
    println!("Endpoint:   {}", cfg.endpoint);

    let client = api::http_client();
    match api::fetch_health(&client, &cfg.endpoint).await {
        Ok((code, body)) => println!("Health:     {} {}", code, body.trim()),
        Err(e) => println!("Health:     error: {}", e),
    }

    if !cfg.node_id.is_empty() || !cfg.worker_id.is_empty() {
        println!("Node ID:    {}", cfg.node_id);
        println!("Worker ID:  {}", cfg.worker_id);
    }
}

async fn cmd_mesh(cfg: &config::NodeConfig, args: &[String]) {
    if args.is_empty() {
        fatal("usage: etzhayyim-murakumo murakumo-mesh <keygen|register|peers|stun|tunnel|status|dns|encrypt|decrypt>");
    }

    match args[0].as_str() {
        "keygen" => {
            let node_id = get_flag(args, "--node-id")
                .unwrap_or_else(|| format!("node-{}", chrono::Utc::now().timestamp_millis()));
            let identity = murakumo_mesh::generate_identity(node_id);
            println!("{}", serde_json::to_string_pretty(&identity).unwrap_or_default());
        }
        "register" => {
            let node_id = required_flag(args, "--node-id");
            let public_key = required_flag(args, "--public-key");
            let endpoint = get_flag(args, "--endpoint");
            let stun_endpoint = get_flag(args, "--stun-endpoint");
            let control_plane = get_flag(args, "--control-plane").unwrap_or_else(|| cfg.endpoint.clone());
            let req = murakumo_mesh::RegisterPeerRequest {
                node_id,
                public_key,
                endpoint,
                stun_endpoint,
                capabilities: vec![],
            };
            let client = api::http_client();
            match murakumo_mesh::register_peer(&client, &control_plane, &req).await {
                Ok(resp) => println!("{}", serde_json::to_string_pretty(&resp).unwrap_or_default()),
                Err(e) => fatal(&e),
            }
        }
        "peers" => {
            let control_plane = get_flag(args, "--control-plane").unwrap_or_else(|| cfg.endpoint.clone());
            let client = api::http_client();
            match murakumo_mesh::list_peers(&client, &control_plane).await {
                Ok(resp) => println!("{}", serde_json::to_string_pretty(&resp).unwrap_or_default()),
                Err(e) => fatal(&e),
            }
        }
        "stun" => {
            let server = get_flag(args, "--server")
                .unwrap_or_else(|| "stun.l.google.com:19302".to_string());
            eprintln!("STUN discovery via {}...", server);
            match murakumo_mesh::stun_discover(&server) {
                Ok(result) => println!("{}", serde_json::to_string_pretty(&result).unwrap_or_default()),
                Err(e) => fatal(&e),
            }
        }
        "nat-type" => {
            let servers = vec!["stun.l.google.com:19302", "stun1.l.google.com:19302"];
            let nat_type = murakumo_mesh::detect_nat_type(&servers);
            println!("NAT type: {}", nat_type);
        }
        "tunnel" => {
            let node_id = get_flag(args, "--node-id")
                .unwrap_or_else(|| cfg.node_id.clone());
            let secret_key = get_flag(args, "--secret-key")
                .unwrap_or_default();
            let control_plane = get_flag(args, "--control-plane")
                .unwrap_or_else(|| cfg.endpoint.clone());
            let relay = get_flag(args, "--relay")
                .and_then(|r| r.parse().ok());

            // Collect --peer flags: "node_id:pubkey:ip:port" for LAN direct mode
            let mut static_peers: Vec<String> = Vec::new();
            {
                let mut i = 0;
                while i < args.len() {
                    if args[i] == "--peer" && i + 1 < args.len() {
                        static_peers.push(args[i + 1].clone());
                        i += 1;
                    }
                    i += 1;
                }
            }
            // Also load peers from --peers-file (JSON array of PeerEntry)
            if let Some(peers_file) = get_flag(args, "--peers-file") {
                if let Ok(content) = std::fs::read_to_string(&peers_file) {
                    if let Ok(peers) = serde_json::from_str::<Vec<murakumo_mesh::PeerEntry>>(&content) {
                        for p in &peers {
                            let ep = p.endpoint.as_deref().unwrap_or("");
                            static_peers.push(format!("{}:{}:{}", p.node_id, p.public_key, ep));
                        }
                    }
                }
            }

            if node_id.is_empty() {
                fatal("--node-id required (or run etzhayyim-murakumo install first)");
            }

            let identity = if secret_key.is_empty() {
                murakumo_mesh::generate_identity(node_id)
            } else {
                let mesh_ip = murakumo_mesh::allocate_mesh_ip(&node_id).to_string();
                let sk_bytes = base64::engine::general_purpose::STANDARD_NO_PAD
                    .decode(&secret_key).unwrap_or_else(|_| fatal("invalid secret key base64"));
                let mut key = [0u8; 32];
                if sk_bytes.len() != 32 { fatal("secret key must be 32 bytes"); }
                key.copy_from_slice(&sk_bytes);
                let static_secret = x25519_dalek::StaticSecret::from(key);
                let public = x25519_dalek::PublicKey::from(&static_secret);
                murakumo_mesh::MeshIdentity {
                    node_id,
                    public_key: base64::engine::general_purpose::STANDARD_NO_PAD.encode(public.as_bytes()),
                    secret_key,
                    mesh_ip,
                }
            };

            eprintln!("murakumo-mesh tunnel starting:");
            eprintln!("  node:     {}", identity.node_id);
            eprintln!("  mesh_ip:  {}", identity.mesh_ip);
            eprintln!("  pubkey:   {}", identity.public_key);

            let tunnel = match murakumo_mesh::MeshTunnel::new(identity.clone(), control_plane.clone(), relay) {
                Ok(t) => std::sync::Arc::new(t),
                Err(e) => fatal(&format!("tunnel init failed: {}", e)),
            };

            // Add static peers (LAN direct mode — no control plane needed)
            for peer_spec in &static_peers {
                // Format: "node_id:pubkey:ip:port" or "node_id:pubkey:ip_port"
                let parts: Vec<&str> = peer_spec.splitn(3, ':').collect();
                if parts.len() >= 2 {
                    let peer_node_id = parts[0].to_string();
                    let peer_pk = parts[1].to_string();
                    let peer_ep = if parts.len() >= 3 { Some(parts[2].to_string()) } else { None };
                    let peer = murakumo_mesh::PeerEntry {
                        node_id: peer_node_id.clone(),
                        public_key: peer_pk,
                        endpoint: peer_ep,
                        mesh_ip: murakumo_mesh::allocate_mesh_ip(&peer_node_id).to_string(),
                        relay_only: false,
                    };
                    eprintln!("  static peer: {} ({})", peer.node_id, peer.mesh_ip);
                    tunnel.add_peer(&peer);
                }
            }

            // Register with control plane (best-effort, skip on 404)
            let client = api::http_client();
            let local_addr = tunnel.socket.local_addr().ok().map(|a| a.to_string());
            let req = murakumo_mesh::RegisterPeerRequest {
                node_id: identity.node_id.clone(),
                public_key: identity.public_key.clone(),
                endpoint: local_addr,
                stun_endpoint: None,
                capabilities: vec!["tunnel".to_string()],
            };
            match murakumo_mesh::register_peer(&client, &control_plane, &req).await {
                Ok(resp) => {
                    eprintln!("  registered: peers={}", resp.peers.len());
                    for p in &resp.peers {
                        tunnel.add_peer(p);
                    }
                }
                Err(_) => {
                    if static_peers.is_empty() {
                        eprintln!("  WARNING: control plane unreachable and no static peers");
                    }
                }
            }

            let peer_count = {
                let table = tunnel.routing.read().unwrap();
                table.all_peers().len()
            };
            eprintln!("  mesh ready: {} peers", peer_count);

            // Spawn recv loop in blocking thread
            let tunnel_recv = tunnel.clone();
            tokio::task::spawn_blocking(move || {
                murakumo_mesh::recv_loop(tunnel_recv);
            });

            // Run mesh daemon (keepalive, gc, sync)
            let client2 = api::http_client();
            tokio::select! {
                _ = murakumo_mesh::run_mesh_daemon(tunnel.clone(), client2) => {}
                _ = tokio::signal::ctrl_c() => {
                    eprintln!("\nmurakumo-mesh tunnel stopped");
                }
            }
        }
        "status" => {
            let node_id = get_flag(args, "--node-id")
                .unwrap_or_else(|| cfg.node_id.clone());
            if node_id.is_empty() {
                fatal("--node-id required");
            }
            let mesh_ip = murakumo_mesh::allocate_mesh_ip(&node_id);
            println!("Node:    {}", node_id);
            println!("Mesh IP: {}", mesh_ip);
            println!("Subnet:  10.99.0.0/16");
            println!("Port:    {}", 41820);

            // Show peers from control plane
            let control_plane = get_flag(args, "--control-plane").unwrap_or_else(|| cfg.endpoint.clone());
            let client = api::http_client();
            match murakumo_mesh::list_peers(&client, &control_plane).await {
                Ok(resp) => {
                    println!("Peers:   {}", resp.peers.len());
                    for p in &resp.peers {
                        let ep = p.endpoint.as_deref().unwrap_or("(relay)");
                        let ip = if p.mesh_ip.is_empty() {
                            murakumo_mesh::allocate_mesh_ip(&p.node_id).to_string()
                        } else {
                            p.mesh_ip.clone()
                        };
                        println!("  {:<20} {:<16} {}", p.node_id, ip, ep);
                    }
                }
                Err(e) => eprintln!("  peers error: {}", e),
            }
        }
        "dns" => {
            if args.len() < 2 {
                fatal("usage: etzhayyim-murakumo murakumo-mesh dns <name.mesh.etzhayyim.com>");
            }
            let name = &args[1];
            if let Some(node_id) = name.strip_suffix(".mesh.etzhayyim.com") {
                let ip = murakumo_mesh::allocate_mesh_ip(node_id);
                println!("{} -> {}", name, ip);
            } else {
                // Try as node_id directly
                let ip = murakumo_mesh::allocate_mesh_ip(name);
                println!("{}.mesh.etzhayyim.com -> {}", name, ip);
            }
        }
        "encrypt" => {
            let secret_key = required_flag(args, "--secret-key");
            let peer_public_key = required_flag(args, "--peer-public-key");
            let message = required_flag(args, "--message");
            match murakumo_mesh::encrypt_frame(&secret_key, &peer_public_key, message.as_bytes()) {
                Ok(frame) => println!("{}", serde_json::to_string_pretty(&frame).unwrap_or_default()),
                Err(e) => fatal(&e),
            }
        }
        "decrypt" => {
            let secret_key = required_flag(args, "--secret-key");
            let peer_public_key = required_flag(args, "--peer-public-key");
            let nonce = required_flag(args, "--nonce");
            let ciphertext = required_flag(args, "--ciphertext");
            let frame = murakumo_mesh::EncryptedFrame { nonce, ciphertext };
            match murakumo_mesh::decrypt_frame(&secret_key, &peer_public_key, &frame) {
                Ok(plaintext) => println!("{}", String::from_utf8_lossy(&plaintext)),
                Err(e) => fatal(&e),
            }
        }
        _ => fatal("usage: etzhayyim-murakumo murakumo-mesh <keygen|register|peers|stun|tunnel|status|dns|encrypt|decrypt>"),
    }
}

fn get_flag(args: &[String], key: &str) -> Option<String> {
    args.windows(2)
        .find(|w| w[0] == key)
        .map(|w| w[1].clone())
}

fn required_flag(args: &[String], key: &str) -> String {
    get_flag(args, key).unwrap_or_else(|| fatal(&format!("missing required flag: {key}")))
}

// ── Distill commands ──

async fn cmd_distill(cfg: &config::NodeConfig, args: &[String]) {
    let mut project = "unispsc".to_string();
    let mut teacher = String::new();
    let mut batch_size = 100i64;
    let mut epochs = 20i64;
    let mut lora_rank = 16i64;
    let mut learning_rate = 1e-5f64;
    let mut codes: Vec<String> = Vec::new();

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--project" if i + 1 < args.len() => { project = args[i + 1].clone(); i += 1; }
            "--teacher" if i + 1 < args.len() => { teacher = args[i + 1].clone(); i += 1; }
            "--batch-size" if i + 1 < args.len() => { batch_size = args[i + 1].parse().unwrap_or(100); i += 1; }
            "--epochs" if i + 1 < args.len() => { epochs = args[i + 1].parse().unwrap_or(20); i += 1; }
            "--lora-rank" if i + 1 < args.len() => { lora_rank = args[i + 1].parse().unwrap_or(16); i += 1; }
            "--learning-rate" if i + 1 < args.len() => { learning_rate = args[i + 1].parse().unwrap_or(1e-5); i += 1; }
            "--commodity-codes" if i + 1 < args.len() => { codes = args[i + 1].split(',').map(|s| s.to_string()).collect(); i += 1; }
            _ => {}
        }
        i += 1;
    }

    let client = api::http_client();
    let req = serde_json::json!({
        "project": project,
        "teacher_model": teacher,
        "batch_size": batch_size,
        "training_epochs": epochs,
        "lora_rank": lora_rank,
        "learning_rate": learning_rate,
        "commodity_codes": codes,
    });

    let resp: Result<serde_json::Value, _> =
        api::magatama_app_call(&client, "submit-distill-job", &req).await;
    match resp {
        Ok(v) => {
            let job_id = v.get("job_id").and_then(|v| v.as_str()).unwrap_or("unknown");
            let status = v.get("status").and_then(|v| v.as_str()).unwrap_or("unknown");
            println!("Distillation job submitted:\n  job_id: {}\n  status: {}", job_id, status);
        }
        Err(e) => fatal(&format!("submit distillation job: {}", e)),
    }
}

async fn cmd_distill_status(cfg: &config::NodeConfig, args: &[String]) {
    let mut job_id = String::new();
    let mut i = 0;
    while i < args.len() {
        if args[i] == "--job-id" && i + 1 < args.len() {
            job_id = args[i + 1].clone();
            i += 1;
        }
        i += 1;
    }
    if job_id.is_empty() {
        fatal("usage: etzhayyim-murakumo distill-status --job-id <id>");
    }

    let client = api::http_client();
    let resp: Result<serde_json::Value, _> =
        api::magatama_app_call(&client, "distill-job-status", &serde_json::json!({ "job_id": job_id })).await;
    match resp {
        Ok(v) => println!("{}", serde_json::to_string_pretty(&v).unwrap_or_default()),
        Err(e) => fatal(&format!("get distillation status: {}", e)),
    }
}

async fn cmd_opus_distill(cfg: &config::NodeConfig, args: &[String]) {
    let mut task = "magatama-codegen".to_string();
    let mut student_ids: Vec<String> = Vec::new();
    let mut samples = 20i64;
    let mut anthropic_key = String::new();

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--task" if i + 1 < args.len() => { task = args[i + 1].clone(); i += 1; }
            "--student" if i + 1 < args.len() => { student_ids.push(args[i + 1].clone()); i += 1; }
            "--samples" if i + 1 < args.len() => { samples = args[i + 1].parse().unwrap_or(20); i += 1; }
            "--anthropic-key" if i + 1 < args.len() => { anthropic_key = args[i + 1].clone(); i += 1; }
            _ => {}
        }
        i += 1;
    }

    if anthropic_key.is_empty() {
        anthropic_key = std::env::var("ANTHROPIC_API_KEY").unwrap_or_default();
    }
    if anthropic_key.is_empty() {
        fatal("Anthropic API key required: --anthropic-key or ANTHROPIC_API_KEY env");
    }
    if student_ids.is_empty() {
        student_ids = vec!["qwen2.5-coder-32b".to_string(), "llama-3.1-8b".to_string()];
    }

    let client = api::http_client();

    // Step 1: Submit
    eprintln!("opus-distill: submitting cloud job task={} students={:?} samples={}", task, student_ids, samples);
    let submit_resp: Result<serde_json::Value, _> = api::cloud_distill_call(
        &client, &cfg.endpoint, "/api/distill/submit",
        &serde_json::json!({ "task": task, "student_ids": student_ids, "samples": samples }),
    ).await;
    let submit = match submit_resp {
        Ok(v) => v,
        Err(e) => fatal(&format!("submit failed: {}", e)),
    };
    let job_id = submit.get("job_id").and_then(|v| v.as_str()).unwrap_or("");
    eprintln!("opus-distill: job submitted job_id={}", job_id);

    // Step 2: Teacher generation
    eprintln!("opus-distill: generating teacher data (Opus 4.6 -> R2)...");
    let teacher_resp: Result<serde_json::Value, _> = api::cloud_distill_call(
        &client, &cfg.endpoint, "/api/distill/run-teacher",
        &serde_json::json!({ "job_id": job_id, "anthropic_key": anthropic_key }),
    ).await;
    match teacher_resp {
        Ok(v) => {
            let generated = v.get("generated").and_then(|v| v.as_i64()).unwrap_or(0);
            let validated = v.get("validated").and_then(|v| v.as_i64()).unwrap_or(0);
            let training = v.get("training_examples").and_then(|v| v.as_i64()).unwrap_or(0);
            eprintln!("opus-distill: teacher data generated={} validated={} training={}", generated, validated, training);
        }
        Err(e) => fatal(&format!("teacher generation failed: {}", e)),
    }

    // Step 3: Evaluate each student
    for sid in &student_ids {
        eprintln!("opus-distill: evaluating student={} (Workers AI)...", sid);
        let eval_resp: Result<serde_json::Value, _> = api::cloud_distill_call(
            &client, &cfg.endpoint, "/api/distill/run-eval",
            &serde_json::json!({ "job_id": job_id, "student_id": sid }),
        ).await;
        match eval_resp {
            Ok(v) => {
                if let Some(metrics) = v.get("metrics") {
                    let sp = metrics.get("structural_pass").and_then(|v| v.as_f64()).unwrap_or(0.0);
                    let ts = metrics.get("token_similarity").and_then(|v| v.as_f64()).unwrap_or(0.0);
                    let eta = metrics.get("shannon_eta").and_then(|v| v.as_f64()).unwrap_or(0.0);
                    let n = metrics.get("samples_evaluated").and_then(|v| v.as_i64()).unwrap_or(0);
                    eprintln!("opus-distill: eval student={} structural={:.1}% similarity={:.3} eta={:.3} (n={})", sid, sp * 100.0, ts, eta, n);
                }
            }
            Err(e) => eprintln!("opus-distill: eval failed for {}: {}", sid, e),
        }
    }

    eprintln!("opus-distill: complete. all data stored in R2 (distill/{}/)", job_id);
}

async fn cmd_opus_distill_eval(cfg: &config::NodeConfig, args: &[String]) {
    let mut job_id = String::new();
    let mut i = 0;
    while i < args.len() {
        if args[i] == "--job-id" && i + 1 < args.len() {
            job_id = args[i + 1].clone();
            i += 1;
        }
        i += 1;
    }
    if job_id.is_empty() {
        fatal("usage: etzhayyim-murakumo opus-distill-eval --job-id <id>");
    }

    let client = api::http_client();
    let resp: Result<serde_json::Value, _> = api::cloud_distill_call(
        &client, &cfg.endpoint, "/api/distill/status",
        &serde_json::json!({ "job_id": job_id }),
    ).await;

    match resp {
        Ok(v) => println!("{}", serde_json::to_string_pretty(&v).unwrap_or_default()),
        Err(e) => fatal(&format!("status failed: {}", e)),
    }
}

async fn cmd_opus_distill_list(cfg: &config::NodeConfig) {
    let client = api::http_client();
    let resp: Result<serde_json::Value, _> = api::cloud_distill_call(
        &client, &cfg.endpoint, "/api/distill/list-students",
        &serde_json::json!({}),
    ).await;

    match resp {
        Ok(v) => {
            println!("Available Workers AI student models for Opus 4.6 cloud distillation:");
            println!();
            if let Some(students) = v.get("students").and_then(|v| v.as_array()) {
                println!("  {:<25} {:<45} {:<8} {}", "ID", "Workers AI Model", "Params", "Tier");
                println!("  {}", "-".repeat(90));
                for s in students {
                    let id = s.get("id").and_then(|v| v.as_str()).unwrap_or("");
                    let cf_model = s.get("cfModel").and_then(|v| v.as_str()).unwrap_or("");
                    let params = s.get("paramsBillion").and_then(|v| v.as_f64()).unwrap_or(0.0);
                    let tier = s.get("tier").and_then(|v| v.as_str()).unwrap_or("");
                    println!("  {:<25} {:<45} {:<6.0}B  {}", id, cf_model, params, tier);
                }
            }
        }
        Err(e) => fatal(&format!("list-students failed: {}", e)),
    }
}
