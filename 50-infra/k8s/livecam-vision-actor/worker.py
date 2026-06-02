"""LangServer actor for livecam.etzhayyim.com vision analysis."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import sys
import time
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
import uvicorn


LOG = logging.getLogger("livecam-vision-actor")
AGENTGATEWAY_MCP_URL = os.environ.get(
    "AGENTGATEWAY_MCP_URL",
    "http://agentgateway-mcp.mitama-udf.svc.cluster.local:8080",
)
PORT = int(os.environ.get("PORT", os.environ.get("HEALTH_PORT", "8080")))
TOOL_NAME = "livecam.vision.analyzeCamera"
PRIMARY_MODEL = os.environ.get("LIVECAM_VISION_MODEL_PRIMARY", "qwen3-vl-8b")
FALLBACK_MODEL = os.environ.get("LIVECAM_VISION_MODEL_FALLBACK", "gemma-3-12b")

VISION_PROMPT = """Analyze this traffic/surveillance camera image. Return ONLY valid JSON with this exact structure:
{
  "personCount": <number>,
  "vehicleCount": <number>,
  "persons": [{"ageClass":"adult|child|youth|elderly","genderApparent":"male|female|unknown","activity":"walking|running|standing|sitting|cycling|unknown","clothingUpperColor":"<color>","clothingLowerColor":"<color>"}],
  "vehicles": [{"vehicleType":"car|truck|bus|motorcycle|bicycle|van|suv|unknown","color":"black|white|silver|gray|red|blue|green|yellow|orange|brown|gold|beige|purple|pink","make":"<brand or empty>","model":"<model or empty>","confidence":0.0}]
}
Count ALL visible vehicles and persons. Be precise about colors and types. If unsure of make/model, leave empty string."""


def configure_logging() -> None:
    if LOG.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOG.addHandler(handler)
    LOG.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def gen_id(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000):x}"


def clean(value: Any) -> str:
    return "" if value is None else str(value)


def cohort_hash(prefix: str, parts: list[str]) -> str:
    canonical = "|".join(parts)
    h = 5381
    for ch in canonical:
        h = ((h * 33) + ord(ch)) & 0xFFFFFFFF
    return f"{prefix}{h:08x}{len(canonical):04x}"


def person_cohort_hash(d: dict[str, Any]) -> str:
    return cohort_hash(
        "p",
        [
            clean(d.get("country")),
            clean(d.get("region")),
            clean(d.get("zoneSlug")),
            clean(d.get("ageClass")),
            clean(d.get("genderApparent")),
            clean(d.get("clothingUpperColor")),
            clean(d.get("clothingLowerColor")),
            clean(d.get("activity")),
            clean(d.get("carrying")),
            clean(d.get("groupSize")),
            clean(d.get("timeSlot")),
            clean(d.get("dayOfWeek")),
        ],
    )


def vehicle_cohort_hash(d: dict[str, Any]) -> str:
    return cohort_hash(
        "v",
        [
            clean(d.get("country")),
            clean(d.get("region")),
            clean(d.get("zoneSlug")),
            clean(d.get("vehicleType")),
            clean(d.get("make")),
            clean(d.get("model")),
            clean(d.get("color")),
            clean(d.get("plateJurisdiction")),
            clean(d.get("timeSlot")),
            clean(d.get("dayOfWeek")),
        ],
    )


def time_slot() -> str:
    h = time.gmtime().tm_hour
    if 5 <= h < 7:
        return "dawn"
    if 7 <= h < 12:
        return "morning"
    if 12 <= h < 17:
        return "afternoon"
    if 17 <= h < 21:
        return "evening"
    return "night"


def day_of_week() -> str:
    return ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][time.gmtime().tm_wday]


async def image_to_base64(image_url: str, image_base64: str) -> tuple[str, int]:
    if image_base64:
        return image_base64.split(",", 1)[-1], int(len(image_base64) * 3 / 4)
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        res = await client.get(image_url)
    res.raise_for_status()
    content_type = res.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        raise ValueError(f"imageUrl did not return an image: {content_type}")
    return base64.b64encode(res.content).decode("ascii"), len(res.content)


async def call_vision_model(model: str, image_base64: str) -> str:
    url = os.environ.get("MURAKUMO_CHAT_COMPLETIONS_URL", "https://murakumo.etzhayyim.com/api/openai/v1/chat/completions")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {"type": "imageUrl", "imageUrl": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                ],
            }
        ],
        "maxTokens": 2000,
        "temperature": 0.1,
    }
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("MURAKUMO_BEARER", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
        res = await client.post(url, json=payload, headers=headers)
    res.raise_for_status()
    data = res.json()
    if data.get("error"):
        raise RuntimeError(json.dumps(data.get("error"))[:500])
    return clean(((data.get("choices") or [{}])[0].get("message") or {}).get("content"))


def parse_analysis(content: str) -> dict[str, Any]:
    text = re.sub(r"<think>[\s\S]*?</think>", "", content).strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text) or re.search(r"(\{[\s\S]*\})", text)
    if not match:
        raise ValueError("vision response did not contain JSON")
    parsed = json.loads(match.group(1).strip())
    if not isinstance(parsed, dict):
        raise ValueError("vision JSON was not an object")
    return parsed


def build_records(analysis: dict[str, Any], context: dict[str, str], model: str, image_size: int, inference_ms: int) -> dict[str, Any]:
    ts = now_iso()
    frame_ts = int(time.time() * 1000)
    detection_id = gen_id("det")
    detections: list[dict[str, Any]] = []
    person_cohorts: list[dict[str, Any]] = []
    vehicle_cohorts: list[dict[str, Any]] = []
    slot = time_slot()
    dow = day_of_week()

    for person in analysis.get("persons") or []:
        if not isinstance(person, dict):
            continue
        dims = {
            "country": context["country"],
            "region": context["region"],
            "zoneSlug": context["zoneSlug"],
            "ageClass": clean(person.get("ageClass") or "adult"),
            "genderApparent": clean(person.get("genderApparent") or "unknown"),
            "clothingUpperColor": clean(person.get("clothingUpperColor")),
            "clothingLowerColor": clean(person.get("clothingLowerColor")),
            "activity": clean(person.get("activity") or "unknown"),
            "carrying": "unknown",
            "groupSize": 1,
            "timeSlot": slot,
            "dayOfWeek": dow,
        }
        h = person_cohort_hash(dims)
        detections.append({"type": "person", "dimensions": dims, "cohortHash": h})
        person_cohorts.append(
            {
                "cohortHash": h,
                "did": f"did:web:livecam.etzhayyim.com:person:{h}",
                "zoneSlug": dims["zoneSlug"],
                "dimensionsJson": json.dumps(dims, separators=(",", ":")),
                "count": 1,
                "firstSeen": ts,
                "lastSeen": ts,
            }
        )

    for vehicle in analysis.get("vehicles") or []:
        if not isinstance(vehicle, dict):
            continue
        dims = {
            "country": context["country"],
            "region": context["region"],
            "zoneSlug": context["zoneSlug"],
            "vehicleType": clean(vehicle.get("vehicleType") or "car"),
            "make": clean(vehicle.get("make")),
            "model": clean(vehicle.get("model")),
            "color": clean(vehicle.get("color") or "white"),
            "plateJurisdiction": "",
            "timeSlot": slot,
            "dayOfWeek": dow,
        }
        h = vehicle_cohort_hash(dims)
        detections.append({"type": "vehicle", "dimensions": dims, "cohortHash": h, "confidence": vehicle.get("confidence")})
        vehicle_cohorts.append(
            {
                "cohortHash": h,
                "did": f"did:web:livecam.etzhayyim.com:vehicle:{h}",
                "zoneSlug": dims["zoneSlug"],
                "dimensionsJson": json.dumps(dims, separators=(",", ":")),
                "count": 1,
                "firstSeen": ts,
                "lastSeen": ts,
            }
        )

    person_count = int(analysis.get("personCount") or len(person_cohorts))
    vehicle_count = int(analysis.get("vehicleCount") or len(vehicle_cohorts))
    summary = ", ".join(
        [
            f"{(d.get('dimensions') or {}).get('color')} {(d.get('dimensions') or {}).get('vehicleType')}"
            if d.get("type") == "vehicle"
            else f"{(d.get('dimensions') or {}).get('ageClass')} {(d.get('dimensions') or {}).get('genderApparent')}"
            for d in detections
        ]
    )
    social = f"Camera {context['cameraSlug']}: {person_count} persons, {vehicle_count} vehicles detected."
    if summary:
        social = f"{social} [{summary}]"
    return {
        "detectionId": detection_id,
        "cameraSlug": context["cameraSlug"],
        "frameTs": frame_ts,
        "personCount": person_count,
        "vehicleCount": vehicle_count,
        "detections": detections,
        "personCohorts": person_cohorts,
        "vehicleCohorts": vehicle_cohorts,
        "modelVersion": model,
        "inferenceMs": inference_ms,
        "imageSizeBytes": image_size,
        "socialText": social,
    }


async def commit_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    url = os.environ.get("LIVECAM_COMMIT_ANALYSIS_URL", "https://livecam.etzhayyim.com/xrpc/com.etzhayyim.apps.livecam.commitAnalysis")
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        res = await client.post(url, json=payload)
    if res.status_code >= 400:
        raise RuntimeError(f"commitAnalysis {res.status_code}: {res.text[:500]}")
    return res.json()


async def analyze_camera(
    cameraSlug: str = "",
    imageUrl: str = "",
    imageBase64: str = "",
    zoneSlug: str = "",
    country: str = "US",
    region: str = "",
    **_: Any,
) -> dict[str, Any]:
    start = time.time()
    if not imageUrl and not imageBase64:
        return {"result": {"ok": False, "error": "imageUrl or imageBase64 required", "cameraSlug": cameraSlug, "ts": now_iso()}}
    context = {
        "cameraSlug": clean(cameraSlug),
        "zoneSlug": clean(zoneSlug),
        "country": clean(country or "US"),
        "region": clean(region),
    }
    first_error = ""
    model_used = ""
    payload: dict[str, Any] = {}
    commit: dict[str, Any] = {}
    try:
        img_b64, image_size = await image_to_base64(clean(imageUrl), clean(imageBase64))
        content = ""
        for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
            try:
                content = await call_vision_model(model, img_b64)
                model_used = model
                if content:
                    break
            except Exception as exc:  # noqa: BLE001
                LOG.warning("vision model failed model=%s error=%s", model, exc)
                first_error = str(exc)[:300]
        if not content:
            raise RuntimeError(first_error or "all vision models unavailable")
        analysis = parse_analysis(content)
        payload = build_records(analysis, context, model_used, image_size, int((time.time() - start) * 1000))
        commit = await commit_analysis(payload)
        if commit.get("error"):
            first_error = clean(commit.get("error"))[:300]
    except Exception as exc:  # noqa: BLE001
        LOG.exception("livecam analysis failed camera=%s", cameraSlug)
        first_error = str(exc)[:300]
    return {
        "result": {
            "ok": not first_error,
            "cameraSlug": cameraSlug,
            "detectionId": payload.get("detectionId", ""),
            "personCount": payload.get("personCount", 0),
            "vehicleCount": payload.get("vehicleCount", 0),
            "cohortsCreated": len(payload.get("personCohorts", [])) + len(payload.get("vehicleCohorts", [])),
            "modelVersion": model_used,
            "commit": commit,
            "firstError": first_error,
            "ts": now_iso(),
        }
    }


app = FastAPI(title="livecam-vision-actor", version="1.0.0")


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "ok": True,
        "runtimeKind": "k8s-langserver",
        "agentGatewayMcpUrl": AGENTGATEWAY_MCP_URL,
        "tools": [TOOL_NAME],
    }


@app.get("/tools")
async def tools() -> dict[str, Any]:
    return {"tools": [{"name": TOOL_NAME, "runtime": "langserver"}]}


async def _invoke_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name != TOOL_NAME:
        raise HTTPException(status_code=404, detail=f"unknown tool: {name}")
    return await analyze_camera(**arguments)


@app.post("/invoke")
async def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or payload.get("tool") or "")
    arguments = payload.get("arguments") or payload.get("input") or {}
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="arguments must be an object")
    return {"ok": True, "name": name, "result": await _invoke_tool(name, arguments)}


@app.post("/runs")
async def runs(payload: dict[str, Any]) -> dict[str, Any]:
    assistant_id = str(payload.get("assistant_id") or TOOL_NAME)
    arguments = payload.get("input") or payload.get("arguments") or {}
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="input must be an object")
    return {"status": "completed", "assistant_id": assistant_id, "output": await _invoke_tool(assistant_id, arguments)}


if __name__ == "__main__":
    configure_logging()
    LOG.info("livecam-vision-actor starting, runtime=k8s-langserver, agentgateway_mcp_url=%s", AGENTGATEWAY_MCP_URL)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
