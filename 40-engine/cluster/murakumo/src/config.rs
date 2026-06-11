use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone)]
pub struct NodeConfig {
    pub endpoint: String,
    pub role: String,
    pub mode: String,
    pub node_id: String,
    pub worker_id: String,
    pub gpu_tier: String,
    pub gpu_vram_mb: String,
    pub nats_url: String,
    pub quic_gateway_addr: String,
}

impl Default for NodeConfig {
    fn default() -> Self {
        Self {
            endpoint: "https://murakumo.etzhayyim.com".to_string(),
            role: "worker".to_string(),
            mode: "worker".to_string(),
            node_id: String::new(),
            worker_id: String::new(),
            gpu_tier: String::new(),
            gpu_vram_mb: String::new(),
            nats_url: String::new(),
            quic_gateway_addr: String::new(),
        }
    }
}

pub fn config_dir() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".etzhayyim")
}

pub fn config_path() -> PathBuf {
    config_dir().join("node.conf")
}

pub fn load_config() -> NodeConfig {
    let mut cfg = NodeConfig::default();

    // Load from file
    if let Ok(content) = fs::read_to_string(config_path()) {
        for line in content.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            if let Some((key, val)) = line.split_once('=') {
                match key {
                    "etzhayyim_NODE_ID" => cfg.node_id = val.to_string(),
                    "etzhayyim_WORKER_ID" => cfg.worker_id = val.to_string(),
                    "etzhayyim_MURAKUMO" => cfg.endpoint = val.to_string(),
                    "etzhayyim_GPU_TIER" => cfg.gpu_tier = val.to_string(),
                    "etzhayyim_GPU_VRAM_MB" => cfg.gpu_vram_mb = val.to_string(),
                    "etzhayyim_PROVIDER_MODE" => cfg.mode = val.to_string(),
                    _ => {}
                }
            }
        }
    }

    // Override with env vars
    if let Ok(v) = std::env::var("etzhayyim_NODE_ID") { cfg.node_id = v; }
    if let Ok(v) = std::env::var("etzhayyim_WORKER_ID") { cfg.worker_id = v; }
    if let Ok(v) = std::env::var("etzhayyim_MURAKUMO") { cfg.endpoint = v; }
    if let Ok(v) = std::env::var("etzhayyim_NODE_ROLE") { cfg.role = v; }
    if let Ok(v) = std::env::var("etzhayyim_GPU_TIER") { cfg.gpu_tier = v; }
    if let Ok(v) = std::env::var("etzhayyim_GPU_VRAM_MB") { cfg.gpu_vram_mb = v; }
    if let Ok(v) = std::env::var("etzhayyim_PROVIDER_MODE") { cfg.mode = v; }
    if let Ok(v) = std::env::var("etzhayyim_NATS_URL") { cfg.nats_url = v; }
    if let Ok(v) = std::env::var("etzhayyim_QUIC_GATEWAY_ADDR") { cfg.quic_gateway_addr = v; }

    cfg
}

impl NodeConfig {
    pub fn save(&self) -> std::io::Result<()> {
        let dir = config_dir();
        fs::create_dir_all(&dir)?;
        let content = format!(
            "etzhayyim_NODE_ID={}\netzhayyim_WORKER_ID={}\netzhayyim_MURAKUMO={}\netzhayyim_GPU_TIER={}\netzhayyim_GPU_VRAM_MB={}\netzhayyim_PROVIDER_MODE={}\n",
            self.node_id, self.worker_id, self.endpoint, self.gpu_tier, self.gpu_vram_mb, self.mode,
        );
        fs::write(config_path(), content)
    }

    pub fn update_field(&mut self, key: &str, val: &str) {
        match key {
            "etzhayyim_NODE_ID" => self.node_id = val.to_string(),
            "etzhayyim_WORKER_ID" => self.worker_id = val.to_string(),
            _ => {}
        }
        let _ = self.save();
    }
}

pub fn env_or(key: &str, def: &str) -> String {
    std::env::var(key).unwrap_or_else(|_| def.to_string())
}

pub fn hf_cache_dir() -> PathBuf {
    if let Ok(hf_home) = std::env::var("HF_HOME") {
        return PathBuf::from(hf_home).join("hub");
    }
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".cache")
        .join("huggingface")
        .join("hub")
}

pub fn bin_install_path() -> &'static str {
    "/usr/local/bin/etzhayyim-murakumo"
}

pub fn model_id_to_cache_dir(id: &str) -> String {
    format!("models--{}", id.replace('/', "--"))
}

pub fn cache_dir_to_model_id(dir: &str) -> String {
    dir.strip_prefix("models--")
        .unwrap_or(dir)
        .replace("--", "/")
}

/// Resolve model short aliases to full HuggingFace model IDs.
pub fn resolve_model_alias(model_id: &str) -> String {
    let aliases: HashMap<&str, &str> = HashMap::from([
        ("qwen3-vl-8b", "mlx-community/Qwen3-VL-8B-Instruct-4bit"),
        ("qwen3-vl-8b-instruct", "mlx-community/Qwen3-VL-8B-Instruct-4bit"),
        ("qwen3-vl-8b-instruct-4bit", "mlx-community/Qwen3-VL-8B-Instruct-4bit"),
        ("mlx-community/qwen3-vl-8b-instruct-4bit", "mlx-community/Qwen3-VL-8B-Instruct-4bit"),
        ("qwen3.5-4b", "Qwen/Qwen3.5-4B"),
        ("qwen3.5-4b-int8", "Qwen/Qwen3.5-4B"),
        ("qwen3.5-4b-4bit", "Qwen/Qwen3.5-4B"),
        ("mlx-community/qwen3.5-4b-4bit", "Qwen/Qwen3.5-4B"),
        ("swe-260316", "etzhayyim/swe-260316"),
        ("etzhayyim-swe", "etzhayyim/swe-260316"),
        ("wai-real", "John6666/wai-real-mix-v11-sdxl"),
        ("wan2-t2v", "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"),
        ("wan2-t2v-5b", "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"),
        ("musicgen-small", "facebook/musicgen-small"),
        ("musicgen-medium", "facebook/musicgen-medium"),
        ("musicgen-large", "facebook/musicgen-large"),
        ("audiogen-medium", "facebook/audiogen-medium"),
    ]);
    let lower = model_id.to_lowercase();
    aliases.get(lower.as_str())
        .map(|s| s.to_string())
        .unwrap_or_else(|| model_id.to_string())
}
