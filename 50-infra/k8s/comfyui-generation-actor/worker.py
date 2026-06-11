"""LangServer actor for comfyui.etzhayyim.com generation jobs."""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import random
import sys
import time
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
import uvicorn


LOG = logging.getLogger("comfyui-generation-actor")
AGENTGATEWAY_MCP_URL = os.environ.get(
    "AGENTGATEWAY_MCP_URL",
    "http://agentgateway-mcp.mitama-udf.svc.cluster.local:8080",
)
PORT = int(os.environ.get("PORT", os.environ.get("HEALTH_PORT", "8080")))
TOOLS = {"comfyui.openai.generateImage", "comfyui.openai.editImage"}


def configure_logging() -> None:
    if LOG.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOG.addHandler(handler)
    LOG.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def parse_size(size: str | None) -> tuple[int, int]:
    if not size or "x" not in size.lower():
        return 832, 1216
    left, right = size.lower().split("x", 1)
    try:
        return max(64, int(left)), max(64, int(right))
    except ValueError:
        return 832, 1216


def build_txt2img_workflow(req: dict[str, Any], default_ckpt: str) -> dict[str, Any]:
    width, height = parse_size(req.get("size"))
    ckpt = req.get("model") or default_ckpt
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": req.get("seed") or random.randint(0, 2**32 - 1),
                "steps": req.get("steps") or 20,
                "cfg": req.get("cfg_scale") or 6.0,
                "sampler_name": req.get("sampler") or "euler",
                "scheduler": req.get("scheduler") or "normal",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": req.get("n") or 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": req.get("prompt") or "masterpiece, best quality", "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": req.get("negative_prompt") or "lowres, bad anatomy, text, watermark", "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "gw"}},
    }


def build_img2img_workflow(req: dict[str, Any], default_ckpt: str, image_name: str) -> dict[str, Any]:
    denoise = min(1, max(0, float(req.get("strength") or 0.7)))
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": req.get("model") or default_ckpt}},
        "2": {"class_type": "LoadImage", "inputs": {"image": image_name, "upload": "image"}},
        "3": {"class_type": "VAEEncode", "inputs": {"pixels": ["2", 0], "vae": ["1", 2]}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": req.get("prompt") or "masterpiece, best quality, anime", "clip": ["1", 1]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": req.get("negative_prompt") or "lowres, bad anatomy, bad hands, text, watermark, blurry, jpeg artifacts", "clip": ["1", 1]}},
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "seed": req.get("seed") or random.randint(0, 2**32 - 1),
                "steps": req.get("steps") or 20,
                "cfg": req.get("cfg_scale") or 7.0,
                "sampler_name": req.get("sampler") or "euler_ancestral",
                "scheduler": req.get("scheduler") or "normal",
                "denoise": denoise,
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["3", 0],
            },
        },
        "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
        "8": {"class_type": "SaveImage", "inputs": {"images": ["7", 0], "filename_prefix": "gw-i2i"}},
    }


def extract_images(data: dict[str, Any]) -> list[str]:
    output = data.get("output") or {}
    images: list[str] = []
    for img in output.get("images") or []:
        if isinstance(img, dict) and img.get("data"):
            images.append(str(img["data"]))
    if isinstance(output.get("image"), str):
        images.append(output["image"])
    return images


async def invoke_serverless(workflow: dict[str, Any]) -> dict[str, Any]:
    upstream = os.environ.get("COMFYUI_UPSTREAM_URL", "").rstrip("/")
    bearer = os.environ.get("COMFYUI_UPSTREAM_BEARER", "")
    if not upstream:
        return {"ok": False, "error": "COMFYUI_UPSTREAM_URL not set"}
    if not bearer:
        return {"ok": False, "error": "COMFYUI_UPSTREAM_BEARER not set"}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {bearer}"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        res = await client.post(f"{upstream}/runsync", json={"input": {"workflow": workflow}}, headers=headers)
    data = res.json()
    images = extract_images(data)
    if data.get("status") == "COMPLETED" and images:
        return {"ok": True, "images": images, "rawStatus": data.get("status")}
    job_id = data.get("id")
    if data.get("status") not in {"IN_QUEUE", "IN_PROGRESS"} or not job_id:
        return {"ok": False, "error": f"runsync status={data.get('status')}", "raw": data}
    deadline = time.time() + 300
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        while time.time() < deadline:
            await asyncio.sleep(5)
            status = await client.get(f"{upstream}/status/{job_id}", headers={"Authorization": f"Bearer {bearer}"})
            sd = status.json()
            if sd.get("status") == "COMPLETED":
                images = extract_images(sd)
                return {"ok": bool(images), "images": images, "rawStatus": sd.get("status"), "error": "" if images else "completed but no images"}
            if sd.get("status") == "FAILED":
                return {"ok": False, "error": "job failed", "raw": sd}
    return {"ok": False, "error": "poll timeout"}


async def upload_native_image(req: dict[str, Any]) -> str:
    upstream = os.environ.get("COMFYUI_UPSTREAM_URL", "").rstrip("/")
    raw = str(req.get("image") or "")
    pure = raw.split(",", 1)[-1]
    data = base64.b64decode(pure)
    files = {"image": ("sketch.png", data, "image/png")}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        res = await client.post(f"{upstream}/upload/image", files=files)
    res.raise_for_status()
    return str(res.json().get("name") or "sketch.png")


async def invoke_native(workflow: dict[str, Any]) -> dict[str, Any]:
    upstream = os.environ.get("COMFYUI_UPSTREAM_URL", "").rstrip("/")
    if not upstream:
        return {"ok": False, "error": "COMFYUI_UPSTREAM_URL not set"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        submit = await client.post(f"{upstream}/prompt", json={"prompt": workflow})
        submit.raise_for_status()
        prompt_id = submit.json().get("prompt_id")
        if not prompt_id:
            return {"ok": False, "error": "no prompt_id"}
        deadline = time.time() + 300
        entry: dict[str, Any] | None = None
        while time.time() < deadline:
            await asyncio.sleep(2)
            hist = await client.get(f"{upstream}/history/{prompt_id}")
            if not hist.is_success:
                continue
            entry = (hist.json() or {}).get(prompt_id)
            if entry and entry.get("outputs"):
                break
        if not entry:
            return {"ok": False, "error": "poll timeout"}
        refs: list[dict[str, str]] = []
        for node in (entry.get("outputs") or {}).values():
            refs.extend(node.get("images") or [])
        images: list[str] = []
        for ref in refs:
            params = {"filename": ref.get("filename", ""), "type": ref.get("type", "output")}
            if ref.get("subfolder"):
                params["subfolder"] = ref["subfolder"]
            img = await client.get(f"{upstream}/view", params=params)
            if img.is_success:
                images.append(base64.b64encode(img.content).decode("ascii"))
    return {"ok": bool(images), "images": images, "error": "" if images else "view fetch failed"}


async def generate(request: dict[str, Any], mode: str) -> dict[str, Any]:
    shape = os.environ.get("COMFYUI_UPSTREAM_SHAPE", "serverless")
    default_ckpt = os.environ.get("COMFYUI_DEFAULT_CKPT", "animagine-xl-4.0.safetensors")
    if mode == "edit":
        if shape != "comfyui-native":
            return {"ok": False, "error": "image edit requires comfyui-native shape"}
        image_name = await upload_native_image(request)
        workflow = build_img2img_workflow(request, default_ckpt, image_name)
    else:
        workflow = build_txt2img_workflow(request, default_ckpt)
    started = time.time()
    result = await (invoke_native(workflow) if shape == "comfyui-native" else invoke_serverless(workflow))
    return {
        "ok": bool(result.get("ok")),
        "mode": mode,
        "shape": shape,
        "imageCount": len(result.get("images") or []),
        "images": result.get("images") or [],
        "error": result.get("error", ""),
        "latencyMs": int((time.time() - started) * 1000),
        "ts": now_iso(),
    }


app = FastAPI(title="comfyui-generation-actor", version="1.0.0")


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "ok": True,
        "runtimeKind": "k8s-langserver",
        "agentGatewayMcpUrl": AGENTGATEWAY_MCP_URL,
        "tools": sorted(TOOLS),
    }


@app.get("/tools")
async def tools() -> dict[str, Any]:
    return {"tools": [{"name": name, "runtime": "langserver"} for name in sorted(TOOLS)]}


async def _invoke_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "comfyui.openai.generateImage":
        return {"result": await generate(arguments.get("request") or arguments, "generation")}
    if name == "comfyui.openai.editImage":
        return {"result": await generate(arguments.get("request") or arguments, "edit")}
    raise HTTPException(status_code=404, detail=f"unknown tool: {name}")


@app.post("/invoke")
async def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or payload.get("tool") or "")
    arguments = payload.get("arguments") or payload.get("input") or {}
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="arguments must be an object")
    return {"ok": True, "name": name, "result": await _invoke_tool(name, arguments)}


@app.post("/runs")
async def runs(payload: dict[str, Any]) -> dict[str, Any]:
    assistant_id = str(payload.get("assistant_id") or "")
    arguments = payload.get("input") or payload.get("arguments") or {}
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="input must be an object")
    return {"status": "completed", "assistant_id": assistant_id, "output": await _invoke_tool(assistant_id, arguments)}


if __name__ == "__main__":
    configure_logging()
    LOG.info("comfyui-generation-actor starting, runtime=k8s-langserver, agentgateway_mcp_url=%s", AGENTGATEWAY_MCP_URL)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
