#!/usr/bin/env python3
import http.server
import socketserver
import json
import subprocess
import uuid
import os
import signal
import sys
from urllib.parse import urlparse, parse_qs

# In-memory pod tracking
# { "pod_id": {"pid": 1234, "name": "...", "status": "RUNNING", "process": PopenObj} }
pods = {}

class MurakumoAgentHandler(http.server.SimpleHTTPRequestHandler):
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/v1/pods":
            # List pods
            pod_list = []
            for pid, info in pods.items():
                # Check if process is still running
                proc = info["process"]
                if proc.poll() is not None:
                    info["status"] = "EXITED"
                
                pod_list.append({
                    "id": pid,
                    "name": info["name"],
                    "desiredStatus": "RUNNING",
                    "currentStatus": info["status"],
                    "imageName": info.get("imageName", "local-mac-native")
                })
            self._send_json(200, {"pods": pod_list})
            
        elif path.startswith("/v1/pods/"):
            pod_id = path.split("/")[-1]
            if pod_id in pods:
                info = pods[pod_id]
                proc = info["process"]
                if proc.poll() is not None:
                    info["status"] = "EXITED"
                self._send_json(200, {
                    "id": pod_id,
                    "name": info["name"],
                    "desiredStatus": "RUNNING",
                    "currentStatus": info["status"],
                    "imageName": info.get("imageName", "local-mac-native")
                })
            else:
                self._send_json(404, {"error": "Pod not found"})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/v1/pods":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data)
            
            name = req.get("name", "unknown")
            cmd = req.get("dockerStartCmd") or req.get("dockerEntrypoint", [])
            env = req.get("env", {})
            
            # Merge env with current env
            run_env = os.environ.copy()
            run_env.update(env)
            
            if not cmd:
                self._send_json(400, {"error": "dockerStartCmd or dockerEntrypoint is required"})
                return
                
            pod_id = uuid.uuid4().hex[:12]
            
            print(f"[Agent] Starting pod {pod_id} ({name}) with cmd: {cmd}")
            
            # Start process in background
            try:
                # We use preexec_fn=os.setsid to create a process group so we can kill it easily
                proc = subprocess.Popen(
                    cmd, 
                    env=run_env, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
                pods[pod_id] = {
                    "pid": proc.pid,
                    "name": name,
                    "status": "RUNNING",
                    "process": proc,
                    "imageName": req.get("imageName", "mac-native")
                }
                
                self._send_json(200, {
                    "id": pod_id,
                    "name": name,
                    "desiredStatus": "RUNNING",
                    "currentStatus": "RUNNING",
                    "imageName": req.get("imageName", "")
                })
            except Exception as e:
                self._send_json(500, {"error": str(e)})
                
        elif path.endswith("/stop"):
            pod_id = path.split("/")[-2]
            if pod_id in pods:
                info = pods[pod_id]
                proc = info["process"]
                if proc.poll() is None:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    except:
                        proc.terminate()
                info["status"] = "EXITED"
                self._send_json(200, {"status": "stopped"})
            else:
                self._send_json(404, {"error": "Pod not found"})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path.startswith("/v1/pods/"):
            pod_id = path.split("/")[-1]
            if pod_id in pods:
                info = pods[pod_id]
                proc = info["process"]
                if proc.poll() is None:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except:
                        proc.kill()
                del pods[pod_id]
                self._send_json(200, {"status": "deleted"})
            else:
                self._send_json(404, {"error": "Pod not found"})
        else:
            self._send_json(404, {"error": "Not found"})

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    print(f"Murakumo Agent listening on port {port}...")
    with socketserver.TCPServer(("", port), MurakumoAgentHandler) as httpd:
        httpd.serve_forever()
