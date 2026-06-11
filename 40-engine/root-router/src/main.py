"""
Root Router Entrypoint

Dynamically routes unified API requests to the 1000 Clean Room Actors.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
import json
import os
import mimetypes
from pathlib import Path

app = FastAPI(title="Etz Hayyim Root Router", version="1.0.0")
logger = logging.getLogger("RootRouter")

# Resolve paths absolutely based on this file's location
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ROUTER_DIR = BASE_DIR / "40-engine" / "root-router"

# Global registry for CID to local path mapping
cid_to_path = {}

# Simulate IPFS Gateway mounting
MAP_FILE = ROUTER_DIR / "ipfs_gateway_map.json"
if MAP_FILE.exists():
    with open(MAP_FILE, "r") as f:
        ipfs_map = json.load(f)
        for route, info in ipfs_map.items():
            if info.get("type") == "ipfs_pin" and info.get("cid"):
                cid_to_path[info["cid"]] = BASE_DIR / info["local_path"]

        if "/apps" in ipfs_map:
            local_path = BASE_DIR / ipfs_map['/apps']['local_path']
            if local_path.exists():
                app.mount("/apps", StaticFiles(directory=str(local_path), html=True), name="ipfs_apps")
                logger.info(f"Mounted IPFS CID {ipfs_map['/apps']['cid']} at /apps")
            else:
                logger.error(f"Static path not found: {local_path}")
else:
    logger.error(f"Map file not found: {MAP_FILE}")

# Simulated registry of the 1000 actors
ACTOR_REGISTRY = {
    # e.g., "salesforce": {"type": "crm", "wasm_endpoint": "salesforce-compat"}
}

@app.get("/ipfs/{cid}/{path:path}")
@app.get("/ipfs/{cid}")
async def ipfs_gateway(cid: str, path: str = ""):
    """
    IPFS Gateway: Resolves a CID and serves the corresponding files.
    Simulates `ipfs.etzhayyim.com/[cid]` mapping.
    """
    if cid not in cid_to_path:
        return JSONResponse(status_code=404, content={"error": "CID not found on local node"})

    base_dir = cid_to_path[cid]
    if not path or path == "":
        path = "index.html"

    file_path = base_dir / path
    if not file_path.exists() or not file_path.is_file():
        # Fallback for directory requests
        if file_path.is_dir() and (file_path / "index.html").exists():
            file_path = file_path / "index.html"
        else:
            return JSONResponse(status_code=404, content={"error": "File not found within CID directory"})

    content_type, _ = mimetypes.guess_type(str(file_path))
    if not content_type:
        content_type = "application/octet-stream"

    logger.info(f"[IPFS Gateway] Serving ipfs://{cid}/{path}")
    return FileResponse(path=str(file_path), media_type=content_type)

@app.api_route("/api/v1/{actor_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def universal_ingress(request: Request, actor_name: str, path: str):
    """
    The Root Router intercepts all traffic, resolves the target actor,
    and proxies the request into the appropriate Py Kotodama WASM sandbox.
    """
    logger.info(f"[Root Router] Ingress: {request.method} /{actor_name}/{path}")

    # Validation
    if not actor_name.endswith("-compat"):
        actor_id = f"{actor_name}-compat"
    else:
        actor_id = actor_name

    # Proxy Logic (Simulated)
    # In a real environment, this would invoke the WASM runtime for `actor_id`
    # and pass the HTTP request context.

    simulated_response = {
        "_meta": {
            "router": "Root Router",
            "target_actor": actor_id,
            "status": "PROXIED"
        },
        "payload": f"Simulated execution of /{path} on {actor_id}"
    }

    return JSONResponse(content=simulated_response, status_code=200)

if __name__ == "__main__":
    import uvicorn
    # Boot the Root Router
    uvicorn.run(app, host="0.0.0.0", port=8000)
