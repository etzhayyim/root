#!/bin/bash
# Download all comparison models to RunPod Network Volume.
# Run once after mounting the volume. Re-runnable (skips existing).
#
# Volume path: /workspace (RunPod default mount)
# Total disk: ~120GB required

set -euo pipefail

BASE=/workspace/models
mkdir -p "$BASE"

pip install -q "huggingface_hub[cli]"

# huggingface-cli is deprecated; use python API directly
DL="python3 -c \"
from huggingface_hub import snapshot_download
import sys
repo, local = sys.argv[1], sys.argv[2]
snapshot_download(repo_id=repo, local_dir=local, local_dir_use_symlinks=False)
print('done:', repo)
\" --"

echo "=== Qwen3-32B AWQ (~18GB) ==="
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('Qwen/Qwen3-32B-AWQ', local_dir='$BASE/qwen3-32b-awq', local_dir_use_symlinks=False)
print('done: Qwen3-32B-AWQ')
"

echo "=== Gemma 4 31B AWQ-4bit (~16GB) ==="
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('cyankiwi/gemma-4-31B-it-AWQ-4bit', local_dir='$BASE/gemma4-31b-awq', local_dir_use_symlinks=False)
print('done: gemma4-31b-awq')
"

echo "=== DeepSeek-R1-Distill-Qwen-32B AWQ (~18GB) ==="
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('casperhansen/deepseek-r1-distill-qwen-32b-awq', local_dir='$BASE/deepseek-r1-32b-awq', local_dir_use_symlinks=False)
print('done: deepseek-r1-32b-awq')
"

echo "=== Llama 4 Scout GGUF IQ3_XS (~47.5GB) ==="
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('bartowski/meta-llama_Llama-4-Scout-17B-16E-Instruct-GGUF',
  local_dir='$BASE/llama4-scout-gguf', local_dir_use_symlinks=False,
  allow_patterns=['*IQ3_XS*'])
print('done: llama4-scout-gguf')
"

echo ""
echo "Done. Disk usage:"
du -sh "$BASE"/*/
