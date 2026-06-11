use serde::{Deserialize, Serialize};

// ── API request/response types ──

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RegisterMeshNodeReq {
    pub hostname: String,
    #[serde(default)]
    pub pubkey: String,
    #[serde(default)]
    pub endpoint: String,
    pub role: String,
    pub gpu_tier: String,
    pub vram_mb: i32,
    #[serde(default)]
    pub capabilities: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RegisterMeshNodeResp {
    pub node_id: String,
    pub worker_id: String,
    #[serde(default)]
    pub assigned_ip: String,
    #[serde(default)]
    pub peers: Vec<Peer>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Peer {
    pub pubkey: String,
    pub ip: String,
    pub endpoint: String,
    pub hostname: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HeartbeatReq {
    pub node_id: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub worker_id: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub hostname: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub gpu_tier: String,
    #[serde(default)]
    pub vram_mb: i32,
    pub mlx_models: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct HeartbeatResp {
    #[serde(default)]
    pub status: String,
    #[serde(default)]
    pub node_id: String,
    #[serde(default)]
    pub worker_id: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PollTaskReq {
    pub worker_id: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub node_id: String,
    #[serde(default)]
    pub warm_shaders: Vec<String>,
    #[serde(default)]
    pub warm_artifacts: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct PollTaskResp {
    #[serde(default)]
    pub has_task: bool,
    #[serde(default)]
    pub worker_not_found: bool,
    pub task: Option<TaskInfo>,
    pub lease: Option<LeaseInfo>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct GpuCapability {
    pub available: bool,
    #[serde(default)]
    pub adapter: String,
    #[serde(default)]
    pub features: Vec<String>,
    #[serde(default)]
    pub max_storage_buffer_binding_size: i64,
    #[serde(default)]
    pub max_compute_workgroup_storage_size: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WorkerCapability {
    pub wasm_simd: bool,
    pub wasm_threads: bool,
    pub gpu: GpuCapability,
    #[serde(default)]
    pub mem_class: String,
    #[serde(default)]
    pub net_class: String,
    #[serde(default)]
    pub power_class: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub gpu_tier: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub runtime_class: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub accelerator_class: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RegisterWorkerReq {
    pub capability: WorkerCapability,
    pub user_agent: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct RegisterWorkerResp {
    #[serde(default)]
    pub worker_id: String,
    #[serde(default)]
    pub session_id: String,
    #[serde(default)]
    pub gpu_tier: String,
    #[serde(default)]
    pub poll_interval_ms: u64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct UnregisterWorkerReq {
    pub worker_id: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TaskInfo {
    pub task_id: String,
    pub task_type: String,
    #[serde(default)]
    pub artifact_keys: Vec<String>,
    #[serde(default)]
    pub shader_hash: String,
    #[serde(default)]
    pub params: String,
    #[serde(default)]
    pub package_ref: String,
    #[serde(default)]
    pub input_blob_refs: Vec<String>,
    #[serde(default)]
    pub checkpoint_blob_ref: String,
    #[serde(default)]
    pub result_blob_ref: String,
    #[serde(default)]
    pub runtime_class: String,
    #[serde(default)]
    pub accelerator_class: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LeaseInfo {
    pub lease_id: String,
    #[serde(default)]
    pub task_id: String,
    #[serde(default)]
    pub worker_id: String,
    #[serde(default)]
    pub issued_at: String,
    #[serde(default)]
    pub expires_at: String,
    #[serde(default)]
    pub renew_deadline: String,
    #[serde(default)]
    pub checkpoint_interval_sec: i32,
    #[serde(default)]
    pub verification_mode: String,
    #[serde(default)]
    pub resume_from_checkpoint: String,
    #[serde(default)]
    pub max_output_bytes: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CommitCheckpointReq {
    pub lease_id: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub checkpoint_key: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub checkpoint_blob_ref: String,
    #[serde(default)]
    pub checkpoint_size: i64,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub checkpoint_digest: String,
    #[serde(default)]
    pub iteration: i64,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub state_metadata: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct CommitCheckpointResp {
    #[serde(default)]
    pub status: String,
    #[serde(default)]
    pub checkpoint_key: String,
    #[serde(default)]
    pub checkpoint_blob_ref: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct CommitResultReq {
    pub lease_id: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub result_key: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub result_blob_ref: String,
    #[serde(default)]
    pub result_size: i64,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub result_digest: String,
    #[serde(default)]
    pub total_gpu_time_ms: i64,
    #[serde(default)]
    pub total_units: i32,
    #[serde(default)]
    pub output: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct CommitResultResp {
    #[serde(default)]
    pub status: String,
    #[serde(default)]
    pub task_id: String,
    #[serde(default)]
    pub result_key: String,
    #[serde(default)]
    pub result_blob_ref: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ReportFailureReq {
    pub lease_id: String,
    pub reason: String,
    pub error_message: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RenewLeaseReq {
    pub lease_id: String,
    pub progress_seq: i32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WorkerStatusReq {
    pub worker_id: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct WorkerStatusResp {
    #[serde(default)]
    pub worker_id: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CatalogResponse {
    pub models: Vec<CatalogModel>,
    pub total: i32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CatalogModel {
    pub model_id: String,
    #[serde(default)]
    pub size_bytes: i64,
    #[serde(default)]
    pub format: String,
    #[serde(default)]
    pub download_url: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct UploadUrlResp {
    #[serde(default)]
    pub upload_url: String,
    #[serde(default)]
    pub s3_key: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct NativeExecRequest {
    pub worker_id: String,
    pub session_id: String,
    pub user_agent: String,
    pub capability: WorkerCapability,
    pub lease: Option<LeaseInfo>,
    pub task: Option<TaskInfo>,
    pub params: serde_json::Map<String, serde_json::Value>,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct NativeCheckpointResult {
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub checkpoint_key: String,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub checkpoint_blob_ref: String,
    #[serde(default)]
    pub checkpoint_size: i64,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub checkpoint_digest: String,
    #[serde(default)]
    pub iteration: i64,
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub state_metadata: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct NativeExecResult {
    #[serde(default)]
    pub output: String,
    #[serde(default)]
    pub result_key: String,
    #[serde(default)]
    pub result_blob_ref: String,
    #[serde(default)]
    pub result_size: i64,
    #[serde(default)]
    pub result_digest: String,
    #[serde(default)]
    pub total_gpu_time_ms: i64,
    #[serde(default)]
    pub total_units: i32,
    #[serde(default)]
    pub warm_shaders: Vec<String>,
    #[serde(default)]
    pub warm_artifacts: Vec<String>,
    #[serde(default)]
    pub checkpoint: Option<NativeCheckpointResult>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct GeneratedMedia {
    #[serde(default)]
    pub b64_json: String,
    #[serde(default)]
    pub mime_type: String,
}

// ── Student model config for distillation ──

#[derive(Debug, Clone)]
pub struct StudentConfig {
    pub id: &'static str,
    pub model: &'static str,
    pub rank: i32,
    pub alpha: i32,
    pub lr: f64,
    pub epochs: i32,
    pub quant: &'static str,
    pub ram_gb: f64,
}

pub const MODEL_FAMILY: &str = "etzhayyim/etzhayyim-moe-moe-kyun";

pub static OPUS_STUDENT_MODELS: &[StudentConfig] = &[
    StudentConfig { id: "qwen2.5-3b", model: "mlx-community/Qwen2.5-3B-Instruct-4bit", rank: 8, alpha: 16, lr: 2e-5, epochs: 10, quant: "4bit-MLX", ram_gb: 2.5 },
    StudentConfig { id: "gemma-4-12b", model: "mlx-community/gemma-4-12b-it-4bit", rank: 16, alpha: 32, lr: 1e-5, epochs: 20, quant: "4bit-MLX", ram_gb: 7.0 },
    StudentConfig { id: "glm-4.7-flash", model: "THUDM/GLM-4.7-Flash", rank: 64, alpha: 128, lr: 2e-6, epochs: 20, quant: "IQ3_XXS", ram_gb: 12.0 },
    StudentConfig { id: "qwen3.5-35b-a3b", model: "Qwen/Qwen3.5-35B-A3B", rank: 48, alpha: 96, lr: 3e-6, epochs: 15, quant: "Q2_K", ram_gb: 12.0 },
];

pub fn find_student_by_id(id: &str) -> Option<&'static StudentConfig> {
    OPUS_STUDENT_MODELS.iter().find(|s| s.id == id)
}

pub fn moe_kyun_model_id(specialist: &str, version: &str) -> String {
    format!("{}-{}-{}", MODEL_FAMILY, specialist, version)
}

// ── Eval metrics ──

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct EvalMetrics {
    #[serde(default)]
    pub build_pass: f64,
    #[serde(default)]
    pub bertscore: f64,
    #[serde(default)]
    pub shannon_eta: f64,
    #[serde(default)]
    pub exact_match: f64,
}
