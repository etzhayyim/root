"""
Root Router Entrypoint

Dynamically routes unified API requests to the 1000 Clean Room Actors.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import json
import os

app = FastAPI(title="Etz Hayyim Root Router", version="1.0.0")
logger = logging.getLogger("RootRouter")

# Simulate IPFS Gateway mounting
MAP_FILE = "ipfs_gateway_map.json"
if os.path.exists(MAP_FILE):
    with open(MAP_FILE, "r") as f:
        ipfs_map = json.load(f)
        if "/apps" in ipfs_map:
            local_path = f"../../{ipfs_map['/apps']['local_path']}"
            app.mount("/apps", StaticFiles(directory=local_path, html=True), name="ipfs_apps")
            logger.info(f"Mounted IPFS CID {ipfs_map['/apps']['cid']} at /apps")

# Simulated registry of the 1000 actors
ACTOR_REGISTRY = {
    # e.g., "salesforce": {"type": "crm", "wasm_endpoint": "salesforce-compat"}
}

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
