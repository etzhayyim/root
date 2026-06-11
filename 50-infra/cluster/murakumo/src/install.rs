use std::process::Command;

use crate::api::{connect_call, http_client};
use crate::config::*;
use crate::daemon::cmd_sync;
use crate::models::*;
use crate::worker::detect_gpu;

pub async fn cmd_install(cfg: &mut NodeConfig) {
    println!("═══════════════════════════════════════════════════");
    println!("  etzhayyim-murakumo -- Native Compute Worker");
    println!("  HTTP/3 direct to murakumo.etzhayyim.com CF Worker");
    println!("═══════════════════════════════════════════════════");
    println!();
    println!("Endpoint:  {}", cfg.endpoint);
    println!("Mode:      {}", cfg.mode);
    println!();

    // Update mode: already installed -> binary update + service restart only
    if !cfg.node_id.is_empty() {
        logf(&format!("-> Already installed (node={}), updating binary + restarting daemon...", cfg.node_id));
        install_binary();
        install_service(cfg);
        logf("Update complete");
        return;
    }

    // 1. Install binary
    logf("-> Installing binary...");
    install_binary();

    // 2. Detect GPU
    logf("-> Detecting capabilities...");
    let (gpu_tier, vram_mb, capabilities) = detect_gpu();
    logf(&format!("  GPU tier: {} (VRAM: {}MB)", gpu_tier, vram_mb));
    logf(&format!("  capabilities: {:?}", capabilities));

    // 3. Register
    logf("-> Registering with murakumo.etzhayyim.com/join...");
    let hostname = hostname::get()
        .map(|h| h.to_string_lossy().to_string())
        .unwrap_or_default();

    let client = http_client();
    let resp: Result<RegisterMeshNodeResp, _> = connect_call(
        &client,
        &cfg.endpoint,
        "RegisterMeshNode",
        &RegisterMeshNodeReq {
            hostname: hostname.clone(),
            pubkey: String::new(),
            endpoint: String::new(),
            role: cfg.mode.clone(),
            gpu_tier: gpu_tier.clone(),
            vram_mb,
            capabilities,
        },
    )
    .await;

    let resp = match resp {
        Ok(r) => r,
        Err(e) => {
            eprintln!("registration failed: {}", e);
            std::process::exit(1);
        }
    };

    logf(&format!("  node_id: {}", resp.node_id));
    logf(&format!("  worker_id: {}", resp.worker_id));

    // 4. Save config
    cfg.node_id = resp.node_id.clone();
    cfg.worker_id = resp.worker_id.clone();
    cfg.gpu_tier = gpu_tier.clone();
    cfg.gpu_vram_mb = vram_mb.to_string();
    let _ = cfg.save();

    // 5. Install kotodama-inference
    logf("-> Installing kotodama-inference engine...");
    install_kotodama_inference();

    // 6. Sync models
    logf("-> Syncing models...");
    cmd_sync(cfg).await;

    // 7. Install service
    logf("-> Installing service...");
    install_service(cfg);

    // 8. Print summary
    println!();
    println!("═══════════════════════════════════════════════════");
    println!("  etzhayyim-murakumo worker registered!");
    println!("═══════════════════════════════════════════════════");
    println!();
    println!("  Mode:        {}", cfg.mode);
    println!("  Node ID:     {}", resp.node_id);
    println!("  Worker ID:   {}", resp.worker_id);
    println!("  GPU Tier:    {} ({}MB)", gpu_tier, vram_mb);
    println!();
    println!("  Daemon:      etzhayyim-murakumo daemon --verbose");
    println!("  OpenAI API:  {}/api/openai/v1/chat/completions", cfg.endpoint);
    println!();
}

pub async fn cmd_join(cfg: &mut NodeConfig) {
    logf("-> Joining murakumo cluster...");
    let hostname = hostname::get()
        .map(|h| h.to_string_lossy().to_string())
        .unwrap_or_default();
    let (gpu_tier, vram_mb, capabilities) = detect_gpu();

    let client = http_client();
    let resp: Result<RegisterMeshNodeResp, _> = connect_call(
        &client,
        &cfg.endpoint,
        "RegisterMeshNode",
        &RegisterMeshNodeReq {
            hostname,
            pubkey: String::new(),
            endpoint: String::new(),
            role: cfg.mode.clone(),
            gpu_tier: gpu_tier.clone(),
            vram_mb,
            capabilities,
        },
    )
    .await;

    match resp {
        Ok(r) => {
            cfg.node_id = r.node_id.clone();
            cfg.worker_id = r.worker_id.clone();
            cfg.gpu_tier = gpu_tier;
            cfg.gpu_vram_mb = vram_mb.to_string();
            let _ = cfg.save();
            println!("Joined: node={} worker={} gpu={}", r.node_id, r.worker_id, cfg.gpu_tier);
        }
        Err(e) => {
            eprintln!("join failed: {}", e);
            std::process::exit(1);
        }
    }
}

fn install_binary() {
    let exe = match std::env::current_exe() {
        Ok(e) => e,
        Err(_) => {
            logf("  WARNING: cannot detect executable path");
            return;
        }
    };
    let dest = bin_install_path();
    if exe.to_string_lossy() == dest {
        logf(&format!("  already at {}", dest));
        return;
    }
    if let Ok(data) = std::fs::read(&exe) {
        let _ = std::fs::write("/tmp/murakumo-bin", &data);
        let _ = std::fs::set_permissions("/tmp/murakumo-bin", std::os::unix::fs::PermissionsExt::from_mode(0o755));
        run_cmd("sudo", &["mv", "/tmp/murakumo-bin", dest]);
        run_cmd("sudo", &["chmod", "+x", dest]);
        run_cmd("sudo", &["ln", "-sf", dest, "/usr/local/bin/murakumo"]);
        logf(&format!("  installed to {}", dest));
    }
}

use std::os::unix::fs::PermissionsExt;

fn install_kotodama_inference() {
    let os = std::env::consts::OS;
    let arch = std::env::consts::ARCH;
    let binary_name = format!("kotodama-inference-{}-{}", os, arch);
    let url = format!("https://cdn.etzhayyim.com/bin/kotodama-inference/latest/{}", binary_name);

    logf(&format!("  downloading {} from {}", binary_name, url));
    let tmp_file = "/tmp/kotodama-inference-download";

    let status = Command::new("curl")
        .args(["-fsSL", "-o", tmp_file, &url])
        .status();

    if status.is_err() || !status.unwrap().success() {
        logf("  WARNING: failed to download kotodama-inference");
        logf("  inference will use MLX fallback only");
        return;
    }

    run_cmd("chmod", &["+x", tmp_file]);
    run_cmd("sudo", &["mv", tmp_file, "/usr/local/bin/kotodama-inference"]);
    logf("  installed kotodama-inference to /usr/local/bin/kotodama-inference");

    if let Ok(out) = Command::new("/usr/local/bin/kotodama-inference").arg("--probe").output() {
        logf(&format!("  verified: {}", String::from_utf8_lossy(&out.stdout).trim()));
    }
}

fn install_service(cfg: &NodeConfig) {
    match std::env::consts::OS {
        "macos" => install_launchd(cfg),
        "linux" => install_systemd(cfg),
        _ => {}
    }
}

fn install_launchd(cfg: &NodeConfig) {
    let home = dirs::home_dir().unwrap_or_else(|| std::path::PathBuf::from("."));
    let home_str = home.to_string_lossy();
    let plist_dir = home.join("Library/LaunchAgents");
    let _ = std::fs::create_dir_all(&plist_dir);

    let launchd_path = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin";

    let plist = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.etzhayyim.murakumo</string>
    <key>ProgramArguments</key>
    <array>
        <string>{}</string>
        <string>daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{}/.etzhayyim/daemon.log</string>
    <key>StandardErrorPath</key>
    <string>{}/.etzhayyim/daemon.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>ETZHAYYIM_MURAKUMO</key>
        <string>{}</string>
        <key>ETZHAYYIM_PROVIDER_MODE</key>
        <string>{}</string>
        <key>PATH</key>
        <string>{}</string>
        <key>HOME</key>
        <string>{}</string>
    </dict>
</dict>
</plist>
"#,
        bin_install_path(),
        home_str,
        home_str,
        cfg.endpoint,
        cfg.mode,
        launchd_path,
        home_str,
    );

    let plist_path = plist_dir.join("com.etzhayyim.murakumo.plist");
    let _ = std::fs::write(&plist_path, &plist);
    let _ = Command::new("launchctl").args(["unload", &plist_path.to_string_lossy()]).status();
    run_cmd("launchctl", &["load", &plist_path.to_string_lossy()]);
    logf("  launchd: com.etzhayyim.murakumo (RunAtLoad)");
}

fn install_systemd(cfg: &NodeConfig) {
    let unit = format!(
        r#"[Unit]
Description=etzhayyim-murakumo native compute worker
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={} daemon
Restart=always
RestartSec=5
Environment=ETZHAYYIM_MURAKUMO={}
Environment=ETZHAYYIM_PROVIDER_MODE={}

[Install]
WantedBy=multi-user.target
"#,
        bin_install_path(),
        cfg.endpoint,
        cfg.mode,
    );

    let _ = std::fs::write("/tmp/etzhayyim-murakumo.service", &unit);
    run_cmd("sudo", &["mv", "/tmp/etzhayyim-murakumo.service", "/etc/systemd/system/etzhayyim-murakumo.service"]);
    run_cmd("sudo", &["systemctl", "daemon-reload"]);
    run_cmd("sudo", &["systemctl", "enable", "etzhayyim-murakumo"]);
    run_cmd("sudo", &["systemctl", "start", "etzhayyim-murakumo"]);
    logf("  systemd: etzhayyim-murakumo.service (enabled)");
}

fn run_cmd(name: &str, args: &[&str]) {
    let status = Command::new(name).args(args).status();
    if let Err(e) = status {
        logf(&format!("  WARNING: {} {:?}: {}", name, args, e));
    } else if let Ok(s) = status {
        if !s.success() {
            logf(&format!("  WARNING: {} {:?}: exit {}", name, args, s));
        }
    }
}

fn logf(msg: &str) {
    let ts = chrono::Utc::now().to_rfc3339();
    eprintln!("{} INFO  {}", ts, msg);
}
