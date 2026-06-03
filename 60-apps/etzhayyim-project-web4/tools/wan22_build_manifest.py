#!/usr/bin/env python3
"""
Build a Wan2.2 TI2V manifest using the shared expert-manifest generator.

This wrapper keeps Wan-specific defaults while allowing every option from
`qwen3_build_manifest.py` to be overridden on the CLI.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    script = Path(__file__).with_name("qwen3_build_manifest.py")
    cmd = [
        sys.executable,
        str(script),
        "--model-id",
        "etzhayyim/etzhayyim-distributed-ti2v-moe-260222",
        "--blob-prefix",
        "models/wan2.2-ti2v-5b/experts",
        "--host-attention-key",
        "models/wan2.2-ti2v-5b/host/attention.safetensors",
        "--host-router-key",
        "models/wan2.2-ti2v-5b/host/router.safetensors",
        "--host-embedding-key",
        "models/wan2.2-ti2v-5b/host/embedding.safetensors",
        "--host-total-size-mb",
        "3000",
        *sys.argv[1:],
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())

