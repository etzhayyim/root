use sha2::{Digest, Sha256};
use std::collections::{BTreeSet, HashMap};
use std::process::Command;
use std::time::{Duration, Instant};

use crate::api::{connect_call, http_client};
use crate::config::*;
use crate::models::*;

/// Detect GPU capabilities for the native worker.
pub fn detect_gpu() -> (String, i32, Vec<String>) {
    let arch = std::env::consts::ARCH;
    let os = std::env::consts::OS;

    if arch == "aarch64" && os == "macos" {
        let caps = vec!["arm64".into(), "mlx".into(), "apple-silicon".into()];
        let (tier, vram_mb) = match Command::new("sysctl").args(["-n", "hw.memsize"]).output() {
            Ok(out) => {
                let mem_str = String::from_utf8_lossy(&out.stdout).trim().to_string();
                let mem_bytes: i64 = mem_str.parse().unwrap_or(0);
                let mem_gb = (mem_bytes / (1024 * 1024 * 1024)) as i32;
                let mem_gb = if mem_gb <= 0 { 8 } else { mem_gb };
                let vram = mem_gb * 1024 / 2;
                let tier = match mem_gb {
                    g if g >= 64 => "g4",
                    g if g >= 32 => "g3",
                    g if g >= 16 => "g2",
                    _ => "g1",
                };
                (tier.to_string(), vram)
            }
            Err(_) => ("g1".to_string(), 4096),
        };
        return (tier, vram_mb, caps);
    }

    let mut caps = vec!["x86_64".to_string()];
    let mut tier = "g0".to_string();
    let mut vram_mb = 0i32;

    // Check NVIDIA GPU
    if which::which("nvidia-smi").is_ok() {
        if let Ok(out) = Command::new("nvidia-smi")
            .args(["--query-gpu=memory.total", "--format=csv,noheader,nounits"])
            .output()
        {
            let vram_str = String::from_utf8_lossy(&out.stdout).trim().to_string();
            vram_mb = vram_str.parse().unwrap_or(0);
            caps.push("cuda".into());
            tier = match vram_mb {
                v if v >= 16000 => "g4".to_string(),
                v if v >= 8000 => "g3".to_string(),
                _ => "g2".to_string(),
            };
        }
    }

    (tier, vram_mb, caps)
}

/// Detect the native worker capability struct.
pub fn detect_native_worker_capability(cfg: &NodeConfig) -> WorkerCapability {
    let (mut tier, mut vram_mb, _caps) = detect_gpu();
    if !cfg.gpu_tier.is_empty() {
        tier = cfg.gpu_tier.clone();
    }
    tier = normalize_native_gpu_tier(&tier);
    if !cfg.gpu_vram_mb.is_empty() {
        if let Ok(parsed) = cfg.gpu_vram_mb.parse::<i32>() {
            if parsed > 0 {
                vram_mb = parsed;
            }
        }
    }

    let available = env_bool("etzhayyim_NATIVE_WEBGPU_AVAILABLE", true);
    let os = std::env::consts::OS;
    let arch = std::env::consts::ARCH;

    let runtime_class = std::env::var("etzhayyim_NATIVE_WORKER_RUNTIME_CLASS").unwrap_or_else(|_| {
        if os == "macos" && arch == "aarch64" {
            "native_mlx".to_string()
        } else if available {
            "native_webgpu".to_string()
        } else {
            "native_cpu".to_string()
        }
    });

    let accelerator_class = std::env::var("etzhayyim_NATIVE_WORKER_ACCELERATOR_CLASS").unwrap_or_else(|_| {
        if os == "macos" && arch == "aarch64" {
            "mlx".to_string()
        } else if available {
            "webgpu".to_string()
        } else {
            "cpu".to_string()
        }
    });

    let adapter = std::env::var("etzhayyim_NATIVE_WEBGPU_ADAPTER")
        .unwrap_or_else(|_| detect_native_gpu_adapter());

    let features = env_list("etzhayyim_NATIVE_WEBGPU_FEATURES")
        .unwrap_or_else(|| default_native_webgpu_features(&tier, available));

    let max_storage = env_i64("etzhayyim_NATIVE_WEBGPU_MAX_STORAGE_BUFFER_BINDING_SIZE")
        .unwrap_or_else(|| default_native_max_storage_buffer(&tier, available));

    let max_compute = env_i64("etzhayyim_NATIVE_WEBGPU_MAX_COMPUTE_WORKGROUP_STORAGE_SIZE")
        .unwrap_or(32768);

    WorkerCapability {
        wasm_simd: true,
        wasm_threads: num_cpus() > 1,
        gpu: GpuCapability {
            available,
            adapter,
            features,
            max_storage_buffer_binding_size: max_storage,
            max_compute_workgroup_storage_size: max_compute,
        },
        mem_class: env_or("etzhayyim_NATIVE_MEM_CLASS", &classify_native_memory_class(vram_mb)),
        net_class: env_or("etzhayyim_NATIVE_NET_CLASS", "good"),
        power_class: env_or("etzhayyim_NATIVE_POWER_CLASS", "desktop"),
        gpu_tier: env_or("etzhayyim_NATIVE_GPU_TIER", &tier),
        runtime_class,
        accelerator_class,
    }
}

fn normalize_native_gpu_tier(tier: &str) -> String {
    match tier.trim().to_lowercase().as_str() {
        "" | "none" | "unknown" => "g0".to_string(),
        _ => tier.to_string(),
    }
}

fn detect_native_gpu_adapter() -> String {
    match std::env::consts::OS {
        "macos" => "apple".to_string(),
        "linux" => {
            if which::which("nvidia-smi").is_ok() {
                "nvidia".to_string()
            } else {
                "unknown".to_string()
            }
        }
        _ => "unknown".to_string(),
    }
}

fn default_native_webgpu_features(tier: &str, available: bool) -> Vec<String> {
    if !available {
        return vec![];
    }
    let mut features = vec!["timestamp-query".to_string()];
    match tier {
        "g4" | "g3" | "g2" => features.push("shader-f16".to_string()),
        _ => {}
    }
    features
}

fn default_native_max_storage_buffer(tier: &str, available: bool) -> i64 {
    if !available {
        return 0;
    }
    match tier {
        "g4" => 1 << 30,
        "g3" => 512 << 20,
        "g2" => 256 << 20,
        _ => 128 << 20,
    }
}

fn classify_native_memory_class(vram_mb: i32) -> String {
    match vram_mb {
        v if v >= 16384 => "high".to_string(),
        v if v >= 8192 => "mid".to_string(),
        _ => "low".to_string(),
    }
}

pub fn native_worker_user_agent() -> String {
    format!(
        "etzhayyim-murakumo-native/{} {}/{}",
        crate::VERSION,
        std::env::consts::OS,
        std::env::consts::ARCH,
    )
}

/// Check if magatama-inference binary is available.
pub fn has_magatama_inference() -> bool {
    which::which("magatama-inference").is_ok()
}

/// Check if a model is a vision-language model.
pub fn is_vision_language_model(model: &str) -> bool {
    let lower = model.to_lowercase();
    lower.contains("-vl") || lower.contains("vision")
}

/// Preferred python3 binary path (venv or system).
pub fn preferred_python() -> Option<String> {
    if let Some(home) = dirs::home_dir() {
        let venv_python = home
            .join(".local/share/murakumo-venv/bin/python3");
        if venv_python.exists() {
            return Some(venv_python.to_string_lossy().to_string());
        }
    }
    which::which("python3")
        .ok()
        .map(|p| p.to_string_lossy().to_string())
}

/// Scan local HF cache for available models.
pub fn scan_local_models() -> Vec<String> {
    let hf_cache = hf_cache_dir();
    let mut models = Vec::new();
    if let Ok(entries) = std::fs::read_dir(&hf_cache) {
        for entry in entries.flatten() {
            if entry.path().is_dir() {
                let name = entry.file_name().to_string_lossy().to_string();
                if name.starts_with("models--") {
                    let id = name.strip_prefix("models--").unwrap_or(&name).replace("--", "/");
                    if !id.starts_with("__bin__/") {
                        models.push(id);
                    }
                }
            }
        }
    }
    models.truncate(50);
    models
}

/// Check if model data exists in the given directory.
pub fn has_model_data(dir: &std::path::Path) -> bool {
    let exts = [".safetensors", ".bin", ".gguf", ".json", ".model", ".pth", ".msgpack"];
    let mut found = false;
    let mut complete = true;

    fn walk(dir: &std::path::Path, exts: &[&str], found: &mut bool, complete: &mut bool) {
        if let Ok(entries) = std::fs::read_dir(dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    walk(&path, exts, found, complete);
                } else {
                    let name = entry.file_name().to_string_lossy().to_string();
                    if name.ends_with(".incomplete") {
                        *complete = false;
                        return;
                    }
                    for ext in exts {
                        if name.ends_with(ext) {
                            *found = true;
                        }
                    }
                }
                if *found && !*complete {
                    return;
                }
            }
        }
    }

    walk(dir, &exts, &mut found, &mut complete);
    found && complete
}

/// Compute SHA-256 hex digest of bytes.
pub fn digest_hex(payload: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(payload);
    hex::encode(hasher.finalize())
}

/// Parse task params JSON string into a map.
pub fn parse_task_params(raw: &str) -> serde_json::Map<String, serde_json::Value> {
    if raw.trim().is_empty() {
        return serde_json::Map::new();
    }
    serde_json::from_str::<serde_json::Map<String, serde_json::Value>>(raw)
        .unwrap_or_else(|_| {
            let mut m = serde_json::Map::new();
            m.insert("raw".to_string(), serde_json::Value::String(raw.to_string()));
            m
        })
}

/// Extract a string field from a JSON map.
pub fn str_field(m: &serde_json::Map<String, serde_json::Value>, key: &str) -> String {
    m.get(key)
        .map(|v| match v {
            serde_json::Value::String(s) => s.clone(),
            other => other.to_string().trim_matches('"').to_string(),
        })
        .unwrap_or_default()
}

/// Extract an int field from a JSON map with fallback.
pub fn int_field(m: &serde_json::Map<String, serde_json::Value>, key: &str, fallback: i64) -> i64 {
    m.get(key)
        .map(|v| match v {
            serde_json::Value::Number(n) => n.as_i64().unwrap_or(fallback),
            serde_json::Value::String(s) => s.parse().unwrap_or(fallback),
            _ => fallback,
        })
        .unwrap_or(fallback)
}

/// Extract a float field from a JSON map with fallback.
pub fn float_field(m: &serde_json::Map<String, serde_json::Value>, key: &str, fallback: f64) -> f64 {
    m.get(key)
        .map(|v| match v {
            serde_json::Value::Number(n) => n.as_f64().unwrap_or(fallback),
            serde_json::Value::String(s) => s.parse().unwrap_or(fallback),
            _ => fallback,
        })
        .unwrap_or(fallback)
}

/// Extract a bool field from a JSON map.
pub fn bool_field(m: &serde_json::Map<String, serde_json::Value>, key: &str) -> bool {
    m.get(key)
        .map(|v| match v {
            serde_json::Value::Bool(b) => *b,
            serde_json::Value::String(s) => s.eq_ignore_ascii_case("true") || s == "1",
            serde_json::Value::Number(n) => n.as_f64().unwrap_or(0.0) != 0.0,
            _ => false,
        })
        .unwrap_or(false)
}

// ── env helpers ──

fn env_bool(key: &str, def: bool) -> bool {
    match std::env::var(key) {
        Ok(raw) => match raw.trim().to_lowercase().as_str() {
            "1" | "true" | "yes" | "on" => true,
            "0" | "false" | "no" | "off" => false,
            _ => def,
        },
        Err(_) => def,
    }
}

fn env_i64(key: &str) -> Option<i64> {
    std::env::var(key).ok().and_then(|v| v.trim().parse().ok())
}

fn env_list(key: &str) -> Option<Vec<String>> {
    std::env::var(key).ok().map(|raw| {
        raw.split(',')
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .collect()
    })
}

fn num_cpus() -> usize {
    std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1)
}

/// Normalize an exec result: fill in missing fields.
pub fn normalize_exec_result(result: &mut NativeExecResult) {
    if result.total_units <= 0 {
        result.total_units = 1;
    }
    if !result.output.is_empty() {
        if result.result_size == 0 {
            result.result_size = result.output.len() as i64;
        }
        if result.result_digest.is_empty() {
            result.result_digest = digest_hex(result.output.as_bytes());
        }
    }
    if let Some(ref mut cp) = result.checkpoint {
        if !cp.state_metadata.is_empty() {
            if cp.checkpoint_size == 0 {
                cp.checkpoint_size = cp.state_metadata.len() as i64;
            }
            if cp.checkpoint_digest.is_empty() {
                cp.checkpoint_digest = digest_hex(cp.state_metadata.as_bytes());
            }
        }
    }
}

/// Auto-select the best local LLM model.
pub fn auto_select_model() -> String {
    if let Ok(v) = std::env::var("etzhayyim_DEFAULT_MODEL") {
        let model = v.trim();
        if !model.is_empty() {
            return model.to_string();
        }
    }
    let hf_cache = hf_cache_dir();
    let preferred = "Qwen/Qwen3.5-4B";
    let preferred_dir = hf_cache.join("models--Qwen--Qwen3.5-4B");
    if preferred_dir.exists() {
        return preferred.to_string();
    }
    if let Ok(entries) = std::fs::read_dir(&hf_cache) {
        let mut first_model = String::new();
        for entry in entries.flatten() {
            if !entry.path().is_dir() {
                continue;
            }
            let name = entry.file_name().to_string_lossy().to_string();
            if !name.starts_with("models--") {
                continue;
            }
            let id = name.strip_prefix("models--").unwrap_or(&name).replace("--", "/");
            if first_model.is_empty() {
                first_model = id.clone();
            }
            let lower = name.to_lowercase();
            if lower.contains("instruct") || lower.contains("chat") || lower.contains("coder") {
                return id;
            }
        }
        return first_model;
    }
    String::new()
}

/// Auto-select the best local image generation model.
pub fn auto_select_image_model() -> String {
    let models = scan_local_models();
    let preferred = [
        "votepurchase/waiREALCN_v14",
        "SG161222/RealVisXL_V4.0",
        "John6666/wai-real-mix-v11-sdxl",
    ];
    for want in &preferred {
        if models.iter().any(|m| m == *want) {
            return want.to_string();
        }
    }
    for model in &models {
        let lower = model.to_lowercase();
        if lower.contains("nsfw") {
            continue;
        }
        if lower.contains("sdxl") || lower.contains("realvis")
            || lower.contains("animagine") || lower.contains("cyberrealistic")
        {
            return model.clone();
        }
    }
    auto_select_model()
}

/// Auto-select the best local video generation model.
pub fn auto_select_video_model() -> String {
    for model in scan_local_models() {
        let lower = model.to_lowercase();
        if lower.contains("wan") || lower.contains("ti2v") || lower.contains("video") {
            return model;
        }
    }
    auto_select_model()
}

/// Parse media size string like "1024x1024" into (width, height).
pub fn parse_media_size(size: &str, fallback_w: i32, fallback_h: i32) -> (i32, i32) {
    if size.is_empty() {
        return (fallback_w, fallback_h);
    }
    let size_lower = size.to_lowercase();
    let parts: Vec<&str> = size_lower.split('x').collect();
    if parts.len() != 2 {
        return (fallback_w, fallback_h);
    }
    let w: i32 = parts[0].trim().parse().unwrap_or(0);
    let h: i32 = parts[1].trim().parse().unwrap_or(0);
    if w <= 0 || h <= 0 {
        (fallback_w, fallback_h)
    } else {
        (w, h)
    }
}

/// Parse duration string to number of frames (8 fps).
pub fn parse_duration_frames(duration: &str) -> i32 {
    if duration.is_empty() {
        return 16;
    }
    let cleaned = duration.trim().trim_end_matches('s');
    let sec: i32 = cleaned.parse().unwrap_or(0);
    if sec <= 0 {
        return 16;
    }
    let frames = sec * 8;
    frames.clamp(8, 64)
}

/// Extract prompt and images from OpenAI-style messages params.
pub fn extract_prompt_and_images(
    params: &serde_json::Map<String, serde_json::Value>,
) -> (String, Vec<String>) {
    let msgs_raw = params.get("messages");
    let mut msgs: Vec<serde_json::Map<String, serde_json::Value>> = Vec::new();

    match msgs_raw {
        Some(serde_json::Value::String(s)) => {
            if let Ok(parsed) = serde_json::from_str::<Vec<serde_json::Map<String, serde_json::Value>>>(s) {
                msgs = parsed;
            }
        }
        Some(serde_json::Value::Array(arr)) => {
            for item in arr {
                if let serde_json::Value::Object(m) = item {
                    msgs.push(m.clone());
                }
            }
        }
        _ => {}
    }

    if msgs.is_empty() {
        return ("<|user|>\nHello\n<|assistant|>".to_string(), vec![]);
    }

    let mut parts = Vec::new();
    let mut images = Vec::new();

    for m in &msgs {
        let role = str_field(m, "role");
        let content = match m.get("content") {
            Some(serde_json::Value::Array(arr)) => {
                let mut content_parts = Vec::new();
                for item in arr {
                    if let serde_json::Value::Object(part) = item {
                        let typ = str_field(part, "type");
                        match typ.as_str() {
                            "text" | "input_text" => {
                                let text = str_field(part, "text");
                                if !text.is_empty() {
                                    content_parts.push(text);
                                }
                            }
                            "image_url" | "input_image" => {
                                if let Some(serde_json::Value::Object(raw_url)) = part.get("image_url") {
                                    let url = str_field(raw_url, "url");
                                    if !url.is_empty() {
                                        images.push(url);
                                    }
                                } else {
                                    let url = str_field(part, "image_url");
                                    if !url.is_empty() {
                                        images.push(url);
                                    }
                                }
                            }
                            _ => {
                                let text = str_field(part, "text");
                                if !text.is_empty() {
                                    content_parts.push(text);
                                }
                            }
                        }
                    }
                }
                content_parts.join("\n")
            }
            _ => str_field(m, "content"),
        };
        parts.push(format!("<|{}|>\n{}", role, content));
    }
    parts.push("<|assistant|>".to_string());
    (parts.join("\n"), images)
}

/// Token overlap similarity (approximate F1 score).
pub fn token_overlap_similarity(a: &str, b: &str) -> f64 {
    let a_lower = a.to_lowercase();
    let b_lower = b.to_lowercase();
    let tokens_a: Vec<&str> = a_lower.split_whitespace().collect();
    let tokens_b: Vec<&str> = b_lower.split_whitespace().collect();
    if tokens_a.is_empty() || tokens_b.is_empty() {
        return 0.0;
    }
    let set_a: std::collections::HashSet<String> = tokens_a.iter().map(|s| s.to_string()).collect();
    let overlap = tokens_b.iter().filter(|t| set_a.contains(&t.to_string())).count();
    let precision = overlap as f64 / tokens_b.len() as f64;
    let recall = overlap as f64 / tokens_a.len() as f64;
    if precision + recall == 0.0 {
        0.0
    } else {
        2.0 * precision * recall / (precision + recall)
    }
}

/// Extract JSON from a string (strip markdown fences, find first '{').
pub fn extract_json(s: &str) -> String {
    let s = if let Some(idx) = s.find("```json") {
        let rest = &s[idx + 7..];
        if let Some(end) = rest.find("```") {
            &rest[..end]
        } else {
            rest
        }
    } else if let Some(idx) = s.find('{') {
        &s[idx..]
    } else {
        s
    };
    s.trim().to_string()
}

/// SHA-256 hex of a string.
pub fn sha256_hex(s: &str) -> String {
    digest_hex(s.as_bytes())
}

/// Media file extension based on kind/mime.
pub fn media_file_ext(kind: &str, mime_type: &str) -> &'static str {
    match mime_type.to_lowercase().as_str() {
        "video/mp4" => ".mp4",
        "image/bmp" => ".bmp",
        "image/jpeg" => ".jpg",
        "image/webp" => ".webp",
        _ if kind == "video_generation" => ".mp4",
        _ => ".png",
    }
}
