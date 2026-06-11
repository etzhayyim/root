# comfyui-generation-actor

LangServer worker for ComfyUI/OpenAI-compatible generation requests.

Responsibilities:
- build ComfyUI txt2img/img2img workflows from OpenAI-compatible requests
- call RunPod Serverless or native ComfyUI
- poll long-running jobs outside Cloudflare edge
- return image artifacts in the LangServer result payload for downstream workflow consumers

The Cloudflare worker remains responsible for auth, adapter passthrough, and thin async dispatch metadata.
