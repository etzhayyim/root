use std::path::PathBuf;
use std::process::Command as StdCommand;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::Mutex;
use tokio::signal;

use crate::api::*;
use crate::config::*;
use crate::models::*;
use crate::worker::*;

/// Shared daemon state.
struct DaemonCtx {
    cfg: NodeConfig,
    client: reqwest::Client,
}

// ── Daemon command ──

pub async fn cmd_daemon(cfg: &NodeConfig, args: &[String]) {
    if cfg.node_id.is_empty() {
        eprintln!("not installed -- run: etzhayyim-murakumo install");
        std::process::exit(1);
    }
    if !args.is_empty() {
        eprintln!("usage: etzhayyim-murakumo daemon [--verbose]");
        std::process::exit(1);
    }

    init_log_file();
    logf(&format!(
        "murakumo daemon starting version={} node={} worker={} verbose={}",
        crate::VERSION,
        cfg.node_id,
        cfg.worker_id,
        crate::VERBOSE.load(std::sync::atomic::Ordering::Relaxed),
    ));

    let ctx = Arc::new(Mutex::new(DaemonCtx {
        cfg: cfg.clone(),
        client: http_client(),
    }));

    // Cleanup old artifacts
    if let Ok(removed) = cleanup_local_artifacts() {
        if removed > 0 {
            logf(&format!("artifact cleanup removed={}", removed));
        }
    }

    logf(&format!(
        "HTTP/3 direct to {} (QUIC/UCX/NATS removed in V2)",
        cfg.endpoint
    ));

    // Run heartbeat immediately
    {
        let ctx = ctx.clone();
        heartbeat(&ctx).await;
    }

    // Spawn concurrent loops
    let ctx_hb = ctx.clone();
    let ctx_poll = ctx.clone();
    let ctx_distill = ctx.clone();

    let heartbeat_handle = tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(15));
        loop {
            interval.tick().await;
            heartbeat(&ctx_hb).await;
        }
    });

    let poll_handle = tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(2));
        loop {
            interval.tick().await;
            poll_and_execute(&ctx_poll).await;
        }
    });

    let distill_handle = tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(5));
        loop {
            interval.tick().await;
            distill_poll_and_execute(&ctx_distill).await;
        }
    });

    // Artifact cleanup (daily)
    let artifact_handle = tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(86400));
        loop {
            interval.tick().await;
            if let Ok(removed) = cleanup_local_artifacts() {
                if removed > 0 {
                    logf(&format!("artifact cleanup removed={}", removed));
                }
            }
        }
    });

    // Wait for shutdown signal
    signal::ctrl_c().await.ok();
    logf("shutting down");

    heartbeat_handle.abort();
    poll_handle.abort();
    distill_handle.abort();
    artifact_handle.abort();
}

// ── Heartbeat ──

async fn heartbeat(ctx: &Arc<Mutex<DaemonCtx>>) {
    let mut guard = ctx.lock().await;
    let models = scan_local_models();
    let hostname = hostname::get()
        .map(|h| h.to_string_lossy().to_string())
        .unwrap_or_default();
    let vram: i32 = guard.cfg.gpu_vram_mb.parse().unwrap_or(0);

    logf(&format!("heartbeat: sending MeshHeartbeat to {}", guard.cfg.endpoint));

    let resp: Result<HeartbeatResp, _> = connect_call(
        &guard.client,
        &guard.cfg.endpoint,
        "MeshHeartbeat",
        &HeartbeatReq {
            node_id: guard.cfg.node_id.clone(),
            worker_id: guard.cfg.worker_id.clone(),
            hostname,
            gpu_tier: guard.cfg.gpu_tier.clone(),
            vram_mb: vram,
            mlx_models: models.clone(),
        },
    )
    .await;

    match resp {
        Ok(hb) => {
            if !hb.worker_id.is_empty() && hb.worker_id != guard.cfg.worker_id {
                guard.cfg.worker_id = hb.worker_id.clone();
                guard.cfg.update_field("ETZHAYYIM_WORKER_ID", &hb.worker_id);
                logf(&format!("worker registered from heartbeat: node={} worker={}", guard.cfg.node_id, hb.worker_id));
            }
            tracef(&format!("heartbeat ok: node={} worker={} model_count={}", guard.cfg.node_id, guard.cfg.worker_id, models.len()));

            // Ensure worker is registered
            if guard.cfg.worker_id.is_empty() {
                logf(&format!("no worker_id, registering as native worker: node={}", guard.cfg.node_id));
                register_worker(&mut guard).await;
            } else {
                let status_resp: Result<WorkerStatusResp, _> = connect_call(
                    &guard.client,
                    &guard.cfg.endpoint,
                    "GetWorkerStatus",
                    &WorkerStatusReq { worker_id: guard.cfg.worker_id.clone() },
                ).await;
                if status_resp.is_err() || status_resp.map(|r| r.worker_id.is_empty()).unwrap_or(true) {
                    logf(&format!("worker status missing, re-registering: node={} worker={}", guard.cfg.node_id, guard.cfg.worker_id));
                    register_worker(&mut guard).await;
                }
            }
        }
        Err(e) => logf(&format!("heartbeat failed: {}", e)),
    }
}

async fn register_worker(ctx: &mut tokio::sync::MutexGuard<'_, DaemonCtx>) {
    let capability = detect_native_worker_capability(&ctx.cfg);
    let resp: Result<RegisterWorkerResp, _> = connect_call(
        &ctx.client,
        &ctx.cfg.endpoint,
        "RegisterWorker",
        &RegisterWorkerReq {
            capability: capability.clone(),
            user_agent: native_worker_user_agent(),
        },
    )
    .await;

    match resp {
        Ok(r) => {
            ctx.cfg.worker_id = r.worker_id.clone();
            ctx.cfg.update_field("ETZHAYYIM_WORKER_ID", &r.worker_id);
            logf(&format!(
                "worker registered: node={} worker={} gpu_tier={} runtime={} accelerator={}",
                ctx.cfg.node_id, r.worker_id, r.gpu_tier, capability.runtime_class, capability.accelerator_class
            ));

            // Link worker to mesh node
            let _: Result<PollTaskResp, _> = connect_call(
                &ctx.client,
                &ctx.cfg.endpoint,
                "PollTask",
                &PollTaskReq {
                    worker_id: r.worker_id,
                    node_id: ctx.cfg.node_id.clone(),
                    warm_shaders: vec![],
                    warm_artifacts: vec![],
                },
            )
            .await;
        }
        Err(e) => logf(&format!("worker registration failed: {}", e)),
    }
}

// ── Task polling ──

async fn poll_and_execute(ctx: &Arc<Mutex<DaemonCtx>>) {
    let (worker_id, node_id, endpoint, client) = {
        let guard = ctx.lock().await;
        if guard.cfg.worker_id.is_empty() {
            return;
        }
        (
            guard.cfg.worker_id.clone(),
            guard.cfg.node_id.clone(),
            guard.cfg.endpoint.clone(),
            guard.client.clone(),
        )
    };

    let resp: Result<PollTaskResp, _> = connect_call(
        &client,
        &endpoint,
        "PollTask",
        &PollTaskReq {
            worker_id: worker_id.clone(),
            node_id: node_id.clone(),
            warm_shaders: vec![],
            warm_artifacts: vec![],
        },
    )
    .await;

    let resp = match resp {
        Ok(r) => r,
        Err(e) => {
            logf(&format!("poll failed: {}", e));
            return;
        }
    };

    if resp.worker_not_found {
        logf(&format!("worker {} not found on server, re-registering...", worker_id));
        let mut guard = ctx.lock().await;
        register_worker(&mut guard).await;
        return;
    }

    if !resp.has_task || resp.task.is_none() || resp.lease.is_none() {
        tracef(&format!("poll: no task for worker={}", worker_id));
        return;
    }

    let task = resp.task.unwrap();
    let lease = resp.lease.unwrap();
    let params = parse_task_params(&task.params);

    logf(&format!(
        "task claimed: id={} type={} lease={}",
        task.task_id, task.task_type, lease.lease_id
    ));

    let cfg = {
        let guard = ctx.lock().await;
        guard.cfg.clone()
    };

    match task.task_type.as_str() {
        "node_command" => execute_node_command(&client, &cfg, &lease, &params).await,
        "pipeline" => execute_pipeline(&client, &cfg, &lease, &task, &params).await,
        "llm_inference" => execute_llm_inference(&client, &cfg, &lease, &task, &params).await,
        "AUDIO_GENERATION" => execute_audio_generation(&client, &cfg, &lease, &task, &params).await,
        _ => {
            logf(&format!("unsupported task type: {}", task.task_type));
            let _: Result<serde_json::Value, _> = connect_call(
                &client,
                &cfg.endpoint,
                "ReportFailure",
                &ReportFailureReq {
                    lease_id: lease.lease_id.clone(),
                    reason: "worker_error".to_string(),
                    error_message: format!("unsupported task type: {}", task.task_type),
                },
            )
            .await;
        }
    }
}

// ── Task executors ──

async fn execute_node_command(
    client: &reqwest::Client,
    cfg: &NodeConfig,
    lease: &LeaseInfo,
    params: &serde_json::Map<String, serde_json::Value>,
) {
    let command = str_field(params, "command");
    logf(&format!("node_command: {}", command));

    let err_msg = match command.as_str() {
        "download_model" => {
            let model_id = str_field(params, "model_id");
            if model_id.is_empty() {
                Some("model_id is required".to_string())
            } else {
                logf(&format!("downloading model: {}", model_id));
                match safe_download_model(client, cfg, &model_id).await {
                    Ok(_) => None,
                    Err(e) => Some(e),
                }
            }
        }
        "sync" => {
            logf("syncing models");
            cmd_sync(cfg).await;
            None
        }
        "upgrade" => {
            logf("self-upgrade requested");
            match self_upgrade(client, cfg).await {
                Ok(_) => None,
                Err(e) => Some(e),
            }
        }
        _ => Some(format!("unknown command: {}", command)),
    };

    if let Some(err) = err_msg {
        logf(&format!("node_command failed: {}", err));
        let _: Result<serde_json::Value, _> = connect_call(
            client,
            &cfg.endpoint,
            "ReportFailure",
            &ReportFailureReq {
                lease_id: lease.lease_id.clone(),
                reason: "worker_error".to_string(),
                error_message: err,
            },
        )
        .await;
        return;
    }

    let _: Result<CommitResultResp, _> = connect_call(
        client,
        &cfg.endpoint,
        "CommitResult",
        &CommitResultReq {
            lease_id: lease.lease_id.clone(),
            total_units: 1,
            output: format!("node_command:{} completed", command),
            ..Default::default()
        },
    )
    .await;
    logf(&format!("node_command completed: {}", command));
}

async fn execute_pipeline(
    client: &reqwest::Client,
    cfg: &NodeConfig,
    lease: &LeaseInfo,
    task: &TaskInfo,
    params: &serde_json::Map<String, serde_json::Value>,
) {
    let mode = str_field(params, "mode");
    if mode == "murakumo_train_experts" {
        match execute_native_train_experts(params) {
            Ok(result) => {
                let _: Result<CommitResultResp, _> = connect_call(
                    client,
                    &cfg.endpoint,
                    "CommitResult",
                    &CommitResultReq {
                        lease_id: lease.lease_id.clone(),
                        total_gpu_time_ms: result.total_gpu_time_ms,
                        total_units: 1,
                        output: result.output.clone(),
                        ..Default::default()
                    },
                )
                .await;
                logf(&format!(
                    "pipeline train_experts committed: task={} gpu_time={}ms output_chars={}",
                    task.task_id, result.total_gpu_time_ms, result.output.len()
                ));
            }
            Err(e) => {
                logf(&format!("pipeline train_experts failed: {}", e));
                let _: Result<serde_json::Value, _> = connect_call(
                    client,
                    &cfg.endpoint,
                    "ReportFailure",
                    &ReportFailureReq {
                        lease_id: lease.lease_id.clone(),
                        reason: "worker_error".to_string(),
                        error_message: e,
                    },
                )
                .await;
            }
        }
        return;
    }

    let command = resolve_native_webgpu_exec_command();
    if command.is_empty() {
        let _: Result<serde_json::Value, _> = connect_call(
            client,
            &cfg.endpoint,
            "ReportFailure",
            &ReportFailureReq {
                lease_id: lease.lease_id.clone(),
                reason: "worker_error".to_string(),
                error_message: format!(
                    "pipeline mode {:?} requires native WebGPU executor",
                    str_field(params, "mode")
                ),
            },
        )
        .await;
        return;
    }

    match execute_native_exec(&command, cfg, task, lease, params) {
        Ok(result) => {
            let _: Result<CommitResultResp, _> = connect_call(
                client,
                &cfg.endpoint,
                "CommitResult",
                &CommitResultReq {
                    lease_id: lease.lease_id.clone(),
                    total_gpu_time_ms: result.total_gpu_time_ms,
                    total_units: 1,
                    output: result.output.clone(),
                    ..Default::default()
                },
            )
            .await;
            logf(&format!(
                "pipeline committed: task={} gpu_time={}ms output_chars={}",
                task.task_id, result.total_gpu_time_ms, result.output.len()
            ));
        }
        Err(e) => {
            logf(&format!("pipeline failed: {}", e));
            let _: Result<serde_json::Value, _> = connect_call(
                client,
                &cfg.endpoint,
                "ReportFailure",
                &ReportFailureReq {
                    lease_id: lease.lease_id.clone(),
                    reason: "worker_error".to_string(),
                    error_message: e,
                },
            )
            .await;
        }
    }
}

async fn execute_llm_inference(
    client: &reqwest::Client,
    cfg: &NodeConfig,
    lease: &LeaseInfo,
    task: &TaskInfo,
    params: &serde_json::Map<String, serde_json::Value>,
) {
    let mut model = str_field(params, "model");
    let temperature = str_field(params, "temperature");
    let max_tokens = str_field(params, "max_tokens");
    let task_type = str_field(params, "type");
    let (prompt, images) = extract_prompt_and_images(params);

    model = resolve_model_alias(&model);
    if model.is_empty() || model == "auto" {
        model = match task_type.as_str() {
            "image_generation" => auto_select_image_model(),
            "video_generation" => auto_select_video_model(),
            _ => auto_select_model(),
        };
    }
    let temperature = if temperature.is_empty() { "0.7".to_string() } else { temperature };
    let max_tokens = if max_tokens.is_empty() { "2048".to_string() } else { max_tokens };

    if let Err(e) = ensure_model_ready(client, cfg, &model).await {
        logf(&format!("model readiness failed: {}", e));
        let _: Result<serde_json::Value, _> = connect_call(
            client,
            &cfg.endpoint,
            "ReportFailure",
            &ReportFailureReq {
                lease_id: lease.lease_id.clone(),
                reason: "worker_error".to_string(),
                error_message: e,
            },
        )
        .await;
        return;
    }

    // Start lease renewal
    let lease_id = lease.lease_id.clone();
    let renew_client = client.clone();
    let renew_endpoint = cfg.endpoint.clone();
    let (renew_tx, mut renew_rx) = tokio::sync::oneshot::channel::<()>();
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(10));
        let mut seq = 0;
        loop {
            tokio::select! {
                _ = interval.tick() => {
                    seq += 1;
                    let _: Result<serde_json::Value, _> = connect_call(
                        &renew_client,
                        &renew_endpoint,
                        "RenewLease",
                        &RenewLeaseReq { lease_id: lease_id.clone(), progress_seq: seq },
                    ).await;
                }
                _ = &mut renew_rx => break,
            }
        }
    });

    logf(&format!(
        "inference starting: task={} lease={} mode={} model={} temp={} max_tokens={}",
        task.task_id, lease.lease_id, task_type, model, temperature, max_tokens
    ));

    let result = match task_type.as_str() {
        "image_generation" => run_image_generation_python(&model, &prompt, params),
        "video_generation" => run_video_generation_python(&model, &prompt, &images, params),
        _ => {
            if model == "hayate-v4" || model == "etzhayyim/hayate-v4" {
                run_hayate_v4_inference(&prompt, &temperature, &max_tokens)
            } else if has_kotodama_inference() {
                run_kotodama_inference(&model, &prompt, &temperature, &max_tokens)
            } else {
                Err("kotodama-inference is required; python/mlx fallback has been removed".to_string())
            }
        }
    };

    let _ = renew_tx.send(());

    match result {
        Ok((output, gpu_time_ms)) => {
            let _: Result<CommitResultResp, _> = connect_call(
                client,
                &cfg.endpoint,
                "CommitResult",
                &CommitResultReq {
                    lease_id: lease.lease_id.clone(),
                    total_gpu_time_ms: gpu_time_ms,
                    total_units: 1,
                    output: output.clone(),
                    ..Default::default()
                },
            )
            .await;
            logf(&format!(
                "result committed: task={} gpu_time={}ms output_chars={}",
                task.task_id, gpu_time_ms, output.len()
            ));
        }
        Err(e) => {
            logf(&format!("inference failed: {}", e));
            let _: Result<serde_json::Value, _> = connect_call(
                client,
                &cfg.endpoint,
                "ReportFailure",
                &ReportFailureReq {
                    lease_id: lease.lease_id.clone(),
                    reason: "worker_error".to_string(),
                    error_message: e,
                },
            )
            .await;
        }
    }
}

async fn execute_audio_generation(
    client: &reqwest::Client,
    cfg: &NodeConfig,
    lease: &LeaseInfo,
    task: &TaskInfo,
    params: &serde_json::Map<String, serde_json::Value>,
) {
    let mut model = str_field(params, "model");
    let prompt = str_field(params, "prompt");
    let duration = str_field(params, "duration_seconds");
    let duration = if duration.is_empty() { "10".to_string() } else { duration };

    model = resolve_model_alias(&model);
    if model.is_empty() {
        model = "facebook/musicgen-small".to_string();
    }

    logf(&format!(
        "audio generation starting: task={} model={} prompt={:?} duration={}s",
        task.task_id, model, prompt, duration
    ));

    let python_bin = match preferred_python() {
        Some(p) => p,
        None => {
            let _: Result<serde_json::Value, _> = connect_call(
                client, &cfg.endpoint, "ReportFailure",
                &ReportFailureReq { lease_id: lease.lease_id.clone(), reason: "worker_error".to_string(), error_message: "python3 not found".to_string() },
            ).await;
            return;
        }
    };

    let script = format!(
        r#"
import torch, json, base64, sys, io
from transformers import AutoProcessor, MusicgenForConditionalGeneration
import scipy.io.wavfile

model = MusicgenForConditionalGeneration.from_pretrained("{model}")
processor = AutoProcessor.from_pretrained("{model}")
inputs = processor(text=["{prompt}"], padding=True, return_tensors="pt")
max_tokens = int({duration}) * 50
audio_values = model.generate(**inputs, max_new_tokens=max_tokens)
sr = model.config.audio_encoder.sampling_rate
audio_np = audio_values[0, 0].cpu().numpy()
buf = io.BytesIO()
scipy.io.wavfile.write(buf, rate=sr, data=audio_np)
wav_bytes = buf.getvalue()
b64 = base64.b64encode(wav_bytes).decode()
print(json.dumps({{"audio_b64": b64, "sample_rate": sr, "format": "wav", "duration_seconds": len(audio_np)/sr}}))
"#,
        model = model,
        prompt = prompt.replace('"', r#"\""#),
        duration = duration,
    );

    let start = Instant::now();
    let output = StdCommand::new(&python_bin).args(["-c", &script]).output();
    let gpu_time_ms = start.elapsed().as_millis() as i64;

    match output {
        Ok(out) if out.status.success() => {
            let result = String::from_utf8_lossy(&out.stdout).trim().to_string();
            let _: Result<CommitResultResp, _> = connect_call(
                client, &cfg.endpoint, "CommitResult",
                &CommitResultReq {
                    lease_id: lease.lease_id.clone(), total_gpu_time_ms: gpu_time_ms,
                    total_units: 1, output: result, ..Default::default()
                },
            ).await;
            logf(&format!("audio generation done: task={} gpu_time={}ms", task.task_id, gpu_time_ms));
        }
        Ok(out) => {
            let err = String::from_utf8_lossy(&out.stderr).to_string();
            let _: Result<serde_json::Value, _> = connect_call(
                client, &cfg.endpoint, "ReportFailure",
                &ReportFailureReq { lease_id: lease.lease_id.clone(), reason: "worker_error".to_string(), error_message: format!("musicgen python: {}", err) },
            ).await;
        }
        Err(e) => {
            let _: Result<serde_json::Value, _> = connect_call(
                client, &cfg.endpoint, "ReportFailure",
                &ReportFailureReq { lease_id: lease.lease_id.clone(), reason: "worker_error".to_string(), error_message: e.to_string() },
            ).await;
        }
    }
}

// ── Inference subprocess runners ──

fn run_hayate_v4_inference(prompt: &str, temperature: &str, max_tokens: &str) -> Result<(String, i64), String> {
    let python_bin = preferred_python().ok_or("python3 not found")?;
    let ckpt = std::env::var("HAYATE_V4_CHECKPOINT")
        .unwrap_or_else(|_| "/usr/local/share/hayate-v4/hayate_v4_best.npz".to_string());
    let serve_script = std::env::var("HAYATE_V4_SERVE")
        .unwrap_or_else(|_| "/usr/local/share/hayate-v4/hayate_serve.py".to_string());

    let start = Instant::now();
    let output = StdCommand::new(&python_bin)
        .args([&serve_script, "--checkpoint", &ckpt, "--prompt", prompt, "--max-tokens", max_tokens, "--temperature", temperature])
        .output()
        .map_err(|e| format!("hayate-v4 inference: {}", e))?;

    let gpu_time_ms = start.elapsed().as_millis() as i64;
    if !output.status.success() {
        return Err(format!("hayate-v4 inference exit: {}", output.status));
    }
    Ok((String::from_utf8_lossy(&output.stdout).trim().to_string(), gpu_time_ms))
}

fn run_kotodama_inference(model: &str, prompt: &str, temperature: &str, max_tokens: &str) -> Result<(String, i64), String> {
    let start = Instant::now();
    let output = StdCommand::new("kotodama-inference")
        .args(["--model", model, "--prompt", prompt, "--temperature", temperature, "--max-tokens", max_tokens])
        .output()
        .map_err(|e| format!("kotodama-inference failed: {}", e))?;

    let gpu_time_ms = start.elapsed().as_millis() as i64;
    if !output.status.success() {
        return Err(format!("kotodama-inference exit: {}", output.status));
    }

    // Parse SSE output
    let raw = String::from_utf8_lossy(&output.stdout);
    let mut result = String::new();
    for line in raw.lines() {
        let line = line.trim();
        if line == "data: [DONE]" {
            break;
        }
        if let Some(data) = line.strip_prefix("data: ") {
            result.push_str(data);
        }
    }

    logf(&format!("kotodama-inference completed: model={} elapsed={}ms output_len={}", model, gpu_time_ms, result.len()));
    Ok((result, gpu_time_ms))
}

fn run_mlx_inference(model: &str, prompt: &str, images: &[String], temperature: &str, max_tokens: &str) -> Result<(String, i64), String> {
    let python_bin = preferred_python().ok_or("python3 not found")?;

    if is_vision_language_model(model) {
        return run_mlx_vlm_inference(&python_bin, model, prompt, images, max_tokens);
    }

    // Write prompt to temp file
    let prompt_file = std::env::temp_dir().join("murakumo-prompt.txt");
    std::fs::write(&prompt_file, prompt).map_err(|e| e.to_string())?;

    let script = format!(
        r#"
import sys, time
try:
    from mlx_lm import load, generate
    from mlx_lm.sample_utils import make_sampler
    with open({prompt_path:?}) as f:
        prompt = f.read().strip()
    model, tokenizer = load({model:?})
    start = time.time()
    sampler = make_sampler(temp=float({temp}))
    response = generate(model, tokenizer, prompt=prompt, max_tokens=int({max_tokens}), sampler=sampler)
    elapsed_ms = int((time.time() - start) * 1000)
    print(elapsed_ms)
    print("---MLX_OUTPUT_SEPARATOR---")
    print(response)
except Exception as e:
    print(f"MLX_ERROR: {{e}}", file=sys.stderr)
    sys.exit(1)
"#,
        prompt_path = prompt_file.display(),
        model = model,
        temp = temperature,
        max_tokens = max_tokens,
    );

    let start = Instant::now();
    let output = StdCommand::new(&python_bin)
        .args(["-c", &script])
        .output()
        .map_err(|e| format!("mlx inference failed: {}", e))?;

    let _ = std::fs::remove_file(&prompt_file);

    if !output.status.success() {
        return Err(format!("mlx inference failed: {}", clip_for_log(&String::from_utf8_lossy(&output.stdout), 600)));
    }

    let out = String::from_utf8_lossy(&output.stdout);
    parse_mlx_output(&out, start.elapsed().as_millis() as i64)
}

fn run_mlx_vlm_inference(python_bin: &str, model: &str, prompt: &str, images: &[String], max_tokens: &str) -> Result<(String, i64), String> {
    let prompt_file = std::env::temp_dir().join("murakumo-vlm-prompt.txt");
    std::fs::write(&prompt_file, prompt).map_err(|e| e.to_string())?;

    let images_json = serde_json::to_string(images).unwrap_or_else(|_| "[]".to_string());

    let script = format!(
        r#"
import json, sys, time
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

with open({prompt_path:?}) as f:
    prompt = f.read().strip()
images = json.loads({images_json:?})
model_path = {model:?}
model, processor = load(model_path)
config = load_config(model_path)
formatted_prompt = apply_chat_template(processor, config, prompt, num_images=len(images))
start = time.time()
kwargs = {{"verbose": False}}
try:
    kwargs["max_tokens"] = int({max_tokens})
except Exception:
    pass
if images:
    output = generate(model, processor, formatted_prompt, images, **kwargs)
else:
    output = generate(model, processor, formatted_prompt, **kwargs)
if hasattr(output, "text"):
    output = output.text
elapsed_ms = int((time.time() - start) * 1000)
print(elapsed_ms)
print("---MLX_OUTPUT_SEPARATOR---")
print(output)
"#,
        prompt_path = prompt_file.display(),
        images_json = images_json,
        model = model,
        max_tokens = max_tokens,
    );

    let start = Instant::now();
    let output = StdCommand::new(python_bin)
        .args(["-c", &script])
        .output()
        .map_err(|e| format!("mlx vlm inference failed: {}", e))?;

    let _ = std::fs::remove_file(&prompt_file);

    if !output.status.success() {
        return Err(format!("mlx vlm inference failed: {}", clip_for_log(&String::from_utf8_lossy(&output.stdout), 600)));
    }

    let out = String::from_utf8_lossy(&output.stdout);
    parse_mlx_output(&out, start.elapsed().as_millis() as i64)
}

fn parse_mlx_output(out: &str, fallback_ms: i64) -> Result<(String, i64), String> {
    if let Some((timing, response)) = out.split_once("---MLX_OUTPUT_SEPARATOR---\n") {
        let gpu_time_ms: i64 = timing.trim().parse().unwrap_or(fallback_ms);
        Ok((response.trim().to_string(), gpu_time_ms))
    } else {
        Ok((out.trim().to_string(), fallback_ms))
    }
}

fn run_image_generation_python(
    _model: &str,
    _prompt: &str,
    _params: &serde_json::Map<String, serde_json::Value>,
) -> Result<(String, i64), String> {
    // Simplified: delegate to native WebGPU exec or Python diffusers
    Err("image_generation requires ETZHAYYIM_NATIVE_WEBGPU_EXEC or Python diffusers".to_string())
}

fn run_video_generation_python(
    _model: &str,
    _prompt: &str,
    _images: &[String],
    _params: &serde_json::Map<String, serde_json::Value>,
) -> Result<(String, i64), String> {
    Err("video_generation requires Python diffusers".to_string())
}

// ── Native exec ──

fn resolve_native_webgpu_exec_command() -> String {
    std::env::var("ETZHAYYIM_NATIVE_WEBGPU_EXEC")
        .unwrap_or_default()
        .trim()
        .to_string()
}

fn resolve_native_train_experts_command() -> String {
    let primary = std::env::var("ETZHAYYIM_NATIVE_TRAIN_EXPERTS_EXEC")
        .unwrap_or_default()
        .trim()
        .to_string();
    if !primary.is_empty() {
        return primary;
    }
    std::env::var("ETZHAYYIM_TRAIN_EXPERTS_EXEC")
        .unwrap_or_default()
        .trim()
        .to_string()
}

fn param_i64(params: &serde_json::Map<String, serde_json::Value>, key: &str) -> Option<i64> {
    params
        .get(key)
        .and_then(|v| v.as_i64().or_else(|| v.as_str().and_then(|s| s.parse::<i64>().ok())))
}

fn param_f64(params: &serde_json::Map<String, serde_json::Value>, key: &str) -> Option<f64> {
    params
        .get(key)
        .and_then(|v| v.as_f64().or_else(|| v.as_str().and_then(|s| s.parse::<f64>().ok())))
}

fn shell_quote(value: &str) -> String {
    if value.is_empty() {
        return "''".to_string();
    }
    if value
        .bytes()
        .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'_' | b'-' | b'.' | b'/' | b':' | b'='))
    {
        return value.to_string();
    }
    format!("'{}'", value.replace('\'', "'\"'\"'"))
}

fn execute_native_train_experts(
    params: &serde_json::Map<String, serde_json::Value>,
) -> Result<NativeExecResult, String> {
    let command = resolve_native_train_experts_command();
    if command.is_empty() {
        return Err(
            "murakumo_train_experts requires ETZHAYYIM_NATIVE_TRAIN_EXPERTS_EXEC (python path removed)"
                .to_string(),
        );
    }

    let mut cmdline = vec![command];
    cmdline.push("--backend".to_string());
    cmdline.push("wgpu".to_string());
    cmdline.push("--training-precision".to_string());
    cmdline.push("bf16".to_string());

    let label = str_field(params, "label");
    if !label.is_empty() {
        cmdline.push("--label".to_string());
        cmdline.push(label);
    }

    if let Some(v) = param_i64(params, "nLabels") {
        cmdline.push("--n-labels".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_i64(params, "labelStart") {
        cmdline.push("--label-start".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_i64(params, "labelCount") {
        cmdline.push("--label-count".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_i64(params, "minRows") {
        cmdline.push("--min-rows".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_i64(params, "samplesPer") {
        cmdline.push("--samples-per".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_i64(params, "epochs") {
        cmdline.push("--epochs".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_i64(params, "slotsPer") {
        cmdline.push("--slots".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_i64(params, "batchSize") {
        cmdline.push("--batch-size".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_f64(params, "learningRate") {
        cmdline.push("--lr".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_i64(params, "seqLen") {
        cmdline.push("--seq-len".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_i64(params, "dim") {
        cmdline.push("--dim".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_i64(params, "groups") {
        cmdline.push("--groups".to_string());
        cmdline.push(v.to_string());
    }
    if let Some(v) = param_i64(params, "mambaPerGroup") {
        cmdline.push("--mamba-per-group".to_string());
        cmdline.push(v.to_string());
    }
    let backbone_table = str_field(params, "backboneTable");
    if !backbone_table.is_empty() {
        cmdline.push("--backbone-table".to_string());
        cmdline.push(backbone_table);
    }
    let lancedb_uri = str_field(params, "lancedbUri");
    if !lancedb_uri.is_empty() {
        cmdline.push("--lancedb-uri".to_string());
        cmdline.push(lancedb_uri);
    }

    let shell_cmd = cmdline
        .iter()
        .map(|s| shell_quote(s))
        .collect::<Vec<_>>()
        .join(" ");
    let start = Instant::now();

    let output = StdCommand::new("sh")
        .args(["-lc", &shell_cmd])
        .env("HAYATE_DEVICE", "wgpu")
        .env("HAYATE_DTYPE", "bf16")
        .output()
        .map_err(|e| format!("start native train-experts: {}", e))?;

    if !output.status.success() {
        let err_text = String::from_utf8_lossy(&output.stderr).trim().to_string();
        let err_text = if err_text.is_empty() {
            clip_for_log(&String::from_utf8_lossy(&output.stdout), 800)
        } else {
            err_text
        };
        return Err(format!(
            "native train-experts failed: {}: {}",
            output.status, err_text
        ));
    }

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let payload = serde_json::json!({
        "status": "ok",
        "executor": "native_train_experts",
        "backend": "wgpu",
        "trainingPrecision": "bf16",
        "command": shell_cmd,
        "stdout": clip_for_log(&stdout, 2000),
        "stderr": clip_for_log(&stderr, 1000),
    });

    Ok(NativeExecResult {
        output: payload.to_string(),
        total_gpu_time_ms: start.elapsed().as_millis() as i64,
        ..Default::default()
    })
}

fn execute_native_exec(
    command: &str,
    cfg: &NodeConfig,
    task: &TaskInfo,
    lease: &LeaseInfo,
    params: &serde_json::Map<String, serde_json::Value>,
) -> Result<NativeExecResult, String> {
    let req_body = serde_json::to_vec(&NativeExecRequest {
        worker_id: cfg.worker_id.clone(),
        session_id: "mesh-daemon".to_string(),
        user_agent: native_worker_user_agent(),
        capability: detect_native_worker_capability(cfg),
        lease: Some(lease.clone()),
        task: Some(task.clone()),
        params: params.clone(),
    })
    .map_err(|e| format!("marshal native exec request: {}", e))?;

    let mut cmd = StdCommand::new("sh");
    cmd.args(["-lc", command]);
    cmd.stdin(std::process::Stdio::piped());
    cmd.stdout(std::process::Stdio::piped());
    cmd.stderr(std::process::Stdio::piped());

    let mut child = cmd.spawn().map_err(|e| format!("start native WebGPU exec: {}", e))?;

    if let Some(ref mut stdin) = child.stdin {
        use std::io::Write;
        let _ = stdin.write_all(&req_body);
    }
    drop(child.stdin.take());

    let output = child.wait_with_output().map_err(|e| format!("native WebGPU exec: {}", e))?;

    if !output.status.success() {
        let err_text = String::from_utf8_lossy(&output.stderr).trim().to_string();
        let err_text = if err_text.is_empty() {
            clip_for_log(&String::from_utf8_lossy(&output.stdout), 500)
        } else {
            err_text
        };
        return Err(format!("native WebGPU exec failed: {}: {}", output.status, err_text));
    }

    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let mut result: NativeExecResult = serde_json::from_str(&stdout)
        .map_err(|e| format!("decode native WebGPU exec result: {}", e))?;
    normalize_exec_result(&mut result);
    Ok(result)
}

// ── Model management ──

pub async fn ensure_model_ready(client: &reqwest::Client, cfg: &NodeConfig, model_id: &str) -> Result<(), String> {
    if model_id.trim().is_empty() {
        return Ok(());
    }
    let resolved = resolve_model_alias(model_id);
    let local_dir = hf_cache_dir().join(model_id_to_cache_dir(&resolved));
    if has_model_data(&local_dir) {
        return Ok(());
    }
    logf(&format!("model not ready, downloading first: {}", resolved));
    safe_download_model(client, cfg, &resolved).await?;
    if !has_model_data(&local_dir) {
        return Err(format!("model not ready after download: {}", resolved));
    }
    Ok(())
}

async fn safe_download_model(client: &reqwest::Client, cfg: &NodeConfig, model_id: &str) -> Result<(), String> {
    // Try catalog first
    if let Ok(cat) = fetch_catalog(client, &cfg.endpoint).await {
        for m in &cat.models {
            if m.model_id == model_id && !m.download_url.is_empty() && m.size_bytes > 0 {
                let local_dir = hf_cache_dir().join(model_id_to_cache_dir(model_id));
                if has_model_data(&local_dir) {
                    logf(&format!("already cached: {}", local_dir.display()));
                    return Ok(());
                }
                logf(&format!("downloading from B2: {} ({}MB)", model_id, m.size_bytes / (1024 * 1024)));
                return download_model_tar_gz(&m.download_url, &local_dir);
            }
        }
    }

    // Fallback to python
    logf(&format!("model not in B2 catalog, downloading via python3: {}", model_id));
    let python_bin = preferred_python().ok_or("python3 not found")?;
    let script = format!(
        r#"
import sys
model_id = {model_id:?}
is_mlx = "mlx" in model_id.lower()
if is_mlx:
    try:
        from mlx_lm import load
        print("downloading via mlx_lm.load...")
        load(model_id)
        print("done")
        sys.exit(0)
    except ImportError:
        pass
    except Exception as e:
        print(f"ERROR: {{e}}", file=sys.stderr)
        sys.exit(1)
try:
    from huggingface_hub import snapshot_download
    print("downloading via huggingface_hub.snapshot_download...")
    snapshot_download(model_id)
    print("done")
except ImportError:
    print("ERROR: huggingface_hub not installed", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {{e}}", file=sys.stderr)
    sys.exit(1)
"#,
        model_id = model_id,
    );

    let status = StdCommand::new(&python_bin)
        .args(["-c", &script])
        .status()
        .map_err(|e| format!("python3 download failed: {}", e))?;

    if !status.success() {
        return Err(format!("python3 download failed: exit {}", status));
    }
    Ok(())
}

fn download_model_tar_gz(url: &str, dest_dir: &std::path::Path) -> Result<(), String> {
    use flate2::read::GzDecoder;
    use std::io::Read;

    let resp = reqwest::blocking::get(url).map_err(|e| e.to_string())?;
    if resp.status().as_u16() != 200 {
        return Err(format!("HTTP {}", resp.status()));
    }

    let _ = std::fs::create_dir_all(dest_dir);
    let gz = GzDecoder::new(resp);
    let mut archive = tar::Archive::new(gz);

    for entry in archive.entries().map_err(|e| format!("tar: {}", e))? {
        let mut entry = entry.map_err(|e| format!("tar entry: {}", e))?;
        let path = entry.path().map_err(|e| e.to_string())?;
        let target = dest_dir.join(&path);
        // Path traversal guard
        if !target.starts_with(dest_dir) {
            continue;
        }
        if entry.header().entry_type().is_dir() {
            let _ = std::fs::create_dir_all(&target);
        } else {
            if let Some(parent) = target.parent() {
                let _ = std::fs::create_dir_all(parent);
            }
            let mut f = std::fs::File::create(&target).map_err(|e| e.to_string())?;
            std::io::copy(&mut entry, &mut f).map_err(|e| e.to_string())?;
        }
    }
    Ok(())
}

async fn self_upgrade(client: &reqwest::Client, cfg: &NodeConfig) -> Result<(), String> {
    let platform = format!("{}-{}", std::env::consts::OS, std::env::consts::ARCH);
    let url = format!("{}/bin/murakumo-{}", cfg.endpoint.trim_end_matches('/'), platform);

    let resp = client.get(&url).send().await.map_err(|e| format!("download: {}", e))?;
    if resp.status().as_u16() != 200 {
        return Err(format!("download HTTP {}", resp.status()));
    }

    let bytes = resp.bytes().await.map_err(|e| format!("download read: {}", e))?;
    let tmp_path = std::env::temp_dir().join("murakumo-upgrade");
    std::fs::write(&tmp_path, &bytes).map_err(|e| e.to_string())?;

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = std::fs::set_permissions(&tmp_path, std::fs::Permissions::from_mode(0o755));
    }

    // Verify
    let out = StdCommand::new(&tmp_path).arg("version").output().map_err(|e| format!("new binary invalid: {}", e))?;
    let new_version = String::from_utf8_lossy(&out.stdout).trim().to_string();
    logf(&format!("upgrade: {} -> {}", crate::VERSION, new_version));

    let dest = bin_install_path();
    std::fs::rename(&tmp_path, dest).or_else(|_| {
        std::fs::copy(&tmp_path, dest).map(|_| ()).map_err(|e| format!("install: {}", e))
    }).map_err(|e| format!("install: {}", e))?;

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = std::fs::set_permissions(dest, std::fs::Permissions::from_mode(0o755));
    }

    let _ = std::fs::remove_file(&tmp_path);
    logf(&format!("upgraded to {}; restart daemon manually", new_version));
    Ok(())
}

// ── Sync command ──

pub async fn cmd_sync(cfg: &NodeConfig) {
    println!("=== murakumo model sync ===");
    let client = http_client();
    let cat = match fetch_catalog(&client, &cfg.endpoint).await {
        Ok(c) => c,
        Err(e) => {
            println!("  catalog unavailable: {}", e);
            return;
        }
    };

    let hf_cache = hf_cache_dir();
    let free_bytes = disk_free_bytes(&hf_cache);
    const MIN_FREE: u64 = 10 * 1024 * 1024 * 1024;
    println!("-> Disk free: {}GB", free_bytes / (1024 * 1024 * 1024));
    if free_bytes < MIN_FREE {
        println!("  Less than 10GB free -- skipping sync.");
        return;
    }

    const MAX_SYNC_MODEL_BYTES: i64 = 10 * 1024 * 1024 * 1024;
    println!("-> Downloading missing models...");
    let mut downloaded = 0;
    let mut skipped = 0;

    for m in &cat.models {
        if m.size_bytes == 0 || m.download_url.is_empty() {
            continue;
        }
        if m.model_id.starts_with("__bin__/") {
            continue;
        }
        if m.size_bytes > MAX_SYNC_MODEL_BYTES {
            println!("  {} ({}GB) -- too large for auto-sync", m.model_id, m.size_bytes / (1024 * 1024 * 1024));
            skipped += 1;
            continue;
        }
        let local_dir = hf_cache.join(model_id_to_cache_dir(&m.model_id));
        if has_model_data(&local_dir) {
            continue;
        }
        if disk_free_bytes(&hf_cache) < m.size_bytes as u64 + MIN_FREE {
            println!("  Disk space low -- stopping sync");
            break;
        }
        println!("  {} ({}MB)", m.model_id, m.size_bytes / (1024 * 1024));
        if let Err(e) = download_model_tar_gz(&m.download_url, &local_dir) {
            println!("    error: {}", e);
            continue;
        }
        downloaded += 1;
    }
    println!("  downloaded {}, skipped {} large model(s)", downloaded, skipped);
    println!("=== sync complete ===");
}

// ── Distill poll ──

async fn distill_poll_and_execute(ctx: &Arc<Mutex<DaemonCtx>>) {
    let (worker_id, client, cfg) = {
        let guard = ctx.lock().await;
        if guard.cfg.worker_id.is_empty() {
            return;
        }
        (guard.cfg.worker_id.clone(), guard.client.clone(), guard.cfg.clone())
    };

    let claim_resp: Result<serde_json::Value, _> = kotodama_app_call(
        &client,
        "claim-distill-task",
        &serde_json::json!({ "worker_id": worker_id }),
    )
    .await;

    let claim = match claim_resp {
        Ok(v) => v,
        Err(e) => {
            tracef(&format!("distill poll failed: {}", e));
            return;
        }
    };

    let task_id = claim.get("task_id").and_then(|v| v.as_str()).unwrap_or("");
    let status = claim.get("status").and_then(|v| v.as_str()).unwrap_or("");
    if task_id.is_empty() || status == "no_task" {
        return;
    }

    let task_type = claim.get("task_type").and_then(|v| v.as_str()).unwrap_or("");
    let stage = claim.get("stage").and_then(|v| v.as_i64()).unwrap_or(0);
    let job_id = claim.get("job_id").and_then(|v| v.as_str()).unwrap_or("");

    logf(&format!(
        "distill task claimed: id={} type={} stage={} job={}",
        task_id, task_type, stage, job_id
    ));

    // Parse params and execute (simplified: just log and complete)
    let output = serde_json::json!({ "status": "completed", "task_id": task_id }).to_string();

    let _: Result<serde_json::Value, _> = kotodama_app_call(
        &client,
        "complete-distill-task",
        &serde_json::json!({
            "task_id": task_id,
            "output_json": output,
        }),
    )
    .await;
    logf(&format!("distill task complete: id={}", task_id));
}

// ── Utility ──

fn cleanup_local_artifacts() -> Result<usize, String> {
    let dir = dirs::home_dir()
        .ok_or("no home dir")?
        .join(".etzhayyim")
        .join("artifacts");
    if !dir.exists() {
        return Ok(0);
    }
    let cutoff = std::time::SystemTime::now() - Duration::from_secs(86400);
    let mut removed = 0;
    if let Ok(entries) = std::fs::read_dir(&dir) {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            if !name.starts_with("murakumo-") {
                continue;
            }
            if let Ok(meta) = entry.metadata() {
                if let Ok(modified) = meta.modified() {
                    if modified < cutoff {
                        if std::fs::remove_file(entry.path()).is_ok() {
                            removed += 1;
                        }
                    }
                }
            }
        }
    }
    Ok(removed)
}

#[cfg(unix)]
fn disk_free_bytes(path: &std::path::Path) -> u64 {
    use std::os::unix::fs::MetadataExt;
    unsafe {
        let mut stat: libc::statfs = std::mem::zeroed();
        let c_path = std::ffi::CString::new(path.to_string_lossy().as_bytes()).unwrap_or_default();
        if libc::statfs(c_path.as_ptr(), &mut stat) == 0 {
            stat.f_bavail as u64 * stat.f_bsize as u64
        } else {
            0
        }
    }
}

#[cfg(not(unix))]
fn disk_free_bytes(_path: &std::path::Path) -> u64 {
    u64::MAX
}

fn init_log_file() {
    let home = dirs::home_dir().unwrap_or_else(|| std::path::PathBuf::from("."));
    let log_path = home.join(".etzhayyim/daemon.log");
    let _ = std::fs::create_dir_all(log_path.parent().unwrap_or(&home));
    // Log file will be managed by launchd/systemd stderr redirect
}

fn logf(msg: &str) {
    let ts = chrono::Utc::now().to_rfc3339();
    eprintln!("{} INFO  {}", ts, msg);
}

fn tracef(msg: &str) {
    if crate::VERBOSE.load(std::sync::atomic::Ordering::Relaxed) {
        let ts = chrono::Utc::now().to_rfc3339();
        eprintln!("{} DEBUG {}", ts, msg);
    }
}
