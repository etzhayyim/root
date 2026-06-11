"""training — ML training job management (LoRA, FP8, continuous metabolic training).

Full training orchestration runs via K8s pod. These commands call the training API.
"""

from __future__ import annotations

import json
import sys

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@click.group("training")
def training() -> None:
    """ML training job management (LoRA, FP8, continuous metabolic)."""


@training.command("list")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--status", "filter_status", default="", help="Filter by status")
def training_list(pds: str | None, json_out: bool, filter_status: str) -> None:
    """List training jobs."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    params = {}
    if filter_status:
        params["status"] = filter_status
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.training.listJobs",
                         params=params, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            jobs = data if isinstance(data, list) else data.get("jobs", [])
            for j in jobs:
                click.echo(f"  {j.get('id', '')}  {j.get('type', '')}  "
                           f"{j.get('status', '')}  model={j.get('model', '?')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@training.command("get")
@click.argument("job_id")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def training_get(job_id: str, pds: str | None, json_out: bool) -> None:
    """Get training job details."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.training.getJob",
                         params={"id": job_id}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


_TRAINING_NSID: dict[str, str] = {
    "sft": "com.etzhayyim.apps.training.runSft",
    "lora": "com.etzhayyim.apps.training.runLora",
    "distill": "com.etzhayyim.apps.training.runDistill",
}


@training.command("run")
@click.option("--kind", default="sft", show_default=True,
              type=click.Choice(["sft", "lora", "distill"]),
              help="Training kind: sft | lora | distill")
@click.option("--base", "base_model", default="",
              help="Base model HF ID (required for sft/lora)")
@click.option("--student-base", "student_base", default="",
              help="Student base model HF ID (required for distill)")
@click.option("--dataset", default="", help="Dataset name (required)")
@click.option("--label", default="", help="Optional dataset label filter")
@click.option("--run-id", "run_id", default="", help="Optional client-supplied run ID")
@click.option("--gpu", "gpu_target", default="", help="GPU pool name override")
@click.option("--seed", default=0, type=int, help="Random seed (0 = unset)")
@click.option("--hyperparams", default="", help="JSON-encoded hyperparams object")
@click.option("--eval-benches", "eval_benches", default="internal-loss", show_default=True,
              help="Comma-separated bench names for final-checkpoint eval")
@click.option("--rationale", default="", help="Free-form rationale (audit trail)")
@click.option("--teacher-kind", "teacher_kind", default="",
              help="distill only: run | actor | artifact")
@click.option("--teacher-run-id", "teacher_run_id", default="",
              help="distill teacher-kind=run: teacher runId")
@click.option("--teacher-actor", "teacher_actor", default="",
              help="distill teacher-kind=actor: teacher actor DID")
@click.option("--distill-method", "distill_method", default="soft-logits", show_default=True,
              help="distill only: hard-label | soft-logits | feature-match")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def training_run(kind: str, base_model: str, student_base: str, dataset: str,
                 label: str, run_id: str, gpu_target: str, seed: int,
                 hyperparams: str, eval_benches: str, rationale: str,
                 teacher_kind: str, teacher_run_id: str, teacher_actor: str,
                 distill_method: str, pds: str | None, json_out: bool) -> None:
    """Start a training run (sft | lora | distill) via com.etzhayyim.apps.training.*."""
    if not dataset:
        raise click.ClickException("--dataset is required")
    if kind in ("sft", "lora") and not base_model:
        raise click.ClickException(f"--base is required for kind={kind}")
    if kind == "distill" and not student_base:
        raise click.ClickException("--student-base is required for kind=distill")
    if kind == "distill" and not teacher_kind:
        raise click.ClickException("--teacher-kind is required for kind=distill (run | actor | artifact)")

    nsid = _TRAINING_NSID[kind]
    payload: dict = {"datasetName": dataset}
    if run_id:
        payload["runId"] = run_id
    if label:
        payload["datasetLabel"] = label
    if gpu_target:
        payload["gpuTarget"] = gpu_target
    if seed:
        payload["seed"] = seed
    if rationale:
        payload["rationale"] = rationale
    if eval_benches:
        payload["evalBenches"] = [b.strip() for b in eval_benches.split(",") if b.strip()]
    if hyperparams:
        try:
            payload["hyperparams"] = json.loads(hyperparams)
        except json.JSONDecodeError as exc:
            raise click.ClickException(f"--hyperparams is not valid JSON: {exc}")
    if kind in ("sft", "lora"):
        payload["baseModel"] = base_model
    elif kind == "distill":
        payload["studentBaseModel"] = student_base
        payload["teacherKind"] = teacher_kind
        if teacher_run_id:
            payload["teacherRunId"] = teacher_run_id
        if teacher_actor:
            payload["teacherActor"] = teacher_actor
        payload["distillMethod"] = distill_method

    _post_training_xrpc((pds or resolve_pds()).rstrip("/"), nsid, payload, json_out)


@training.command("start")
@click.option("--type", "job_type", default="lora", show_default=True,
              type=click.Choice(["lora", "fp8", "metabolic"]))
@click.option("--model", default="", help="Base model to train")
@click.option("--dataset", default="", help="Dataset ID or path")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def training_start(job_type: str, model: str, dataset: str, pds: str | None, json_out: bool) -> None:
    """Start a training job (legacy path; prefer 'training run')."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    payload = {"type": job_type, "model": model, "dataset": dataset}
    try:
        resp = httpx.post(f"{pds_url}/xrpc/com.etzhayyim.training.startJob",
                          json=payload, headers=_auth_headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"started job: {data.get('id', '')}  type={job_type}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@training.command("cancel")
@click.argument("job_id")
@click.option("--pds", default=None)
def training_cancel(job_id: str, pds: str | None) -> None:
    """Cancel a training job."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(f"{pds_url}/xrpc/com.etzhayyim.training.cancelJob",
                          json={"id": job_id}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        click.echo(f"cancelled: {job_id}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


def _post_training_xrpc(pds_url: str, nsid: str, payload: dict, json_out: bool) -> None:
    try:
        resp = httpx.post(f"{pds_url}/xrpc/{nsid}", json=payload,
                          headers=_auth_headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            if isinstance(data, dict):
                for k, v in data.items():
                    click.echo(f"  {k}: {v}")
            else:
                click.echo(json.dumps(data, ensure_ascii=False))
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@training.command("promote")
@click.argument("checkpoint_id")
@click.option("--alias", required=True, help="Serving alias (e.g. murakumo:gemma4-e4b-it@20260507)")
@click.option("--target", default="", help="Serving target hint (murakumo / runpod / vultr-gpu)")
@click.option("--by", default="", help="Promoting actor DID")
@click.option("--rationale", default="", help="Free-form rationale (audit trail)")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def training_promote(checkpoint_id: str, alias: str, target: str, by: str,
                     rationale: str, pds: str | None, json_out: bool) -> None:
    """Promote a checkpoint to a serving alias."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    payload: dict = {"checkpointId": checkpoint_id, "alias": alias}
    if target:
        payload["servingTarget"] = target
    if by:
        payload["promotedBy"] = by
    if rationale:
        payload["rationale"] = rationale
    _post_training_xrpc(pds_url, "com.etzhayyim.apps.training.promote", payload, json_out)


@training.command("eval")
@click.argument("checkpoint_id")
@click.option("--bench", default="internal-loss",
              help="Comma-separated bench names (e.g. mmlu,arc_challenge)")
@click.option("--eval-dataset", default="", help="Optional eval-only dataset snapshot name")
@click.option("--eval-revision", default="", help="Optional eval dataset revision")
@click.option("--limit", default=0, type=int, help="Cap samples per bench (0 = unbounded)")
@click.option("--gpu", default="", help="GPU pool name")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def training_eval(checkpoint_id: str, bench: str, eval_dataset: str,
                  eval_revision: str, limit: int, gpu: str,
                  pds: str | None, json_out: bool) -> None:
    """Run evaluation on a checkpoint."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    benches = [b.strip() for b in bench.split(",") if b.strip()]
    if not benches:
        raise click.ClickException("--bench must list at least one bench name")
    payload: dict = {"checkpointId": checkpoint_id, "benches": benches}
    if eval_dataset:
        payload["evalDatasetName"] = eval_dataset
    if eval_revision:
        payload["evalDatasetRevision"] = eval_revision
    if limit > 0:
        payload["sampleLimit"] = limit
    if gpu:
        payload["gpuTarget"] = gpu
    _post_training_xrpc(pds_url, "com.etzhayyim.apps.training.runEval", payload, json_out)


@training.command("list-runs")
@click.option("--kind", default="",
              type=click.Choice(["", "sft", "lora", "distill", "dpo", "pretrain"]),
              help="Filter by run kind")
@click.option("--status", "filter_status", default="",
              type=click.Choice(["", "queued", "running", "done", "failed"]),
              help="Filter by status")
@click.option("--limit", default=50, type=int, show_default=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def training_list_runs(kind: str, filter_status: str, limit: int,
                       pds: str | None, json_out: bool) -> None:
    """List training runs."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    payload: dict = {"limit": limit}
    if kind:
        payload["kind"] = kind
    if filter_status:
        payload["status"] = filter_status
    _post_training_xrpc(pds_url, "com.etzhayyim.apps.training.listRuns", payload, json_out)


@training.command("list-checkpoints")
@click.option("--run", default="", help="Filter to one runId")
@click.option("--only-final", is_flag=True, default=False,
              help="Return only is_final=true checkpoints")
@click.option("--limit", default=50, type=int, show_default=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def training_list_checkpoints(run: str, only_final: bool, limit: int,
                               pds: str | None, json_out: bool) -> None:
    """List training checkpoints."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    payload: dict = {"limit": limit, "onlyFinal": only_final}
    if run:
        payload["runId"] = run
    _post_training_xrpc(pds_url, "com.etzhayyim.apps.training.listCheckpoints", payload, json_out)


@training.command("list-snapshots")
@click.option("--dataset", default="", help="Filter to one datasetName (e.g. etzhayyim-corpus)")
@click.option("--status", "filter_status", default="",
              type=click.Choice(["", "frozen", "deprecated"]),
              help="Filter by status")
@click.option("--limit", default=50, type=int, show_default=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def training_list_snapshots(dataset: str, filter_status: str, limit: int,
                             pds: str | None, json_out: bool) -> None:
    """List training dataset snapshots."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    payload: dict = {"limit": limit}
    if dataset:
        payload["datasetName"] = dataset
    if filter_status:
        payload["status"] = filter_status
    _post_training_xrpc(pds_url, "com.etzhayyim.apps.training.listSnapshots", payload, json_out)


@training.command("coverage")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def training_coverage(pds: str | None, json_out: bool) -> None:
    """Training data coverage report."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    _post_training_xrpc(pds_url, "com.etzhayyim.apps.training.coverage", {}, json_out)


@training.command("serving")
@click.option("--alias", default="", help="Filter to alias substring")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def training_serving(alias: str, pds: str | None, json_out: bool) -> None:
    """List currently served model aliases."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    payload: dict = {}
    if alias:
        payload["alias"] = alias
    _post_training_xrpc(pds_url, "com.etzhayyim.apps.training.serving", payload, json_out)
