#!/usr/bin/env python3
"""discover — LAN を役割で掃いて fleet/EVO を同定する (DHCP 変動の再発防止)。

問題の根本原因: fleet.edn / ssh config の静的 IP が DHCP で陳腐化し、
EVO の IP (.70→.22 と記録) が実際には別マシン (Mac) を指していた。
IP ではなく **能力 (GPU 種別 + OS + Ollama models)** で同定する。

各 :11434 (Ollama) ホストを分類:
  - EVO  : ComfyUI device.type == "cuda"/"rocm" (RDNA gfx1151 / 32GiB) — 学習ボックス
  - mac  : ComfyUI device.type == "mps" — Mac mini fleet ノード
判定は MAC ベンダ + SSH バナー (Ubuntu vs macOS) でも裏取り。

Usage:
  python3 discover.py                 # 表形式で全 Ollama ホストを分類
  python3 discover.py --evo           # EVO の IP だけ出力 (見つからなければ exit 1)
  python3 discover.py --json          # 機械可読
  python3 discover.py --cidr 192.168.1.0/24
"""

from __future__ import annotations

import argparse
import concurrent.futures
import ipaddress
import json
import re
import socket
import subprocess
import sys
import urllib.request


def ping(ip: str) -> None:
    subprocess.run(["ping", "-c1", "-W1", ip],
                   capture_output=True, timeout=3)


def get_json(url: str, timeout: float = 2.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.load(r)
    except Exception:
        return None


def ssh_banner(ip: str, timeout: float = 2.0) -> str:
    try:
        with socket.create_connection((ip, 22), timeout) as s:
            s.settimeout(timeout)
            return s.recv(128).decode(errors="replace").strip()
    except Exception:
        return ""


def arp_mac(ip: str) -> str:
    try:
        out = subprocess.run(["arp", "-n", ip], capture_output=True,
                             text=True, timeout=3).stdout
        m = re.search(r"([0-9a-f]{1,2}(:[0-9a-f]{1,2}){5})", out, re.I)
        return m.group(1) if m else ""
    except Exception:
        return ""


def probe(ip: str) -> dict | None:
    # Ollama (:11434) か ComfyUI (:8188) のどちらかがあれば fleet/EVO 候補。
    # EVO は Ollama が idle で models 空のことがあるので ComfyUI を主シグナルにする。
    tags = get_json(f"http://{ip}:11434/api/tags", timeout=3.0)
    stats = get_json(f"http://{ip}:8188/system_stats", timeout=3.0)
    if tags is None and stats is None:
        return None
    models = [m["name"] for m in (tags or {}).get("models", [])]
    dev = (stats or {}).get("devices", [{}])
    dev = dev[0] if dev else {}
    dtype = dev.get("type", "")
    vram = int(dev.get("vram_total", 0)) // 2**30
    banner = ssh_banner(ip)
    os_kind = ("ubuntu" if "Ubuntu" in banner else
               "linux" if "Linux" in banner else
               "macos" if banner.startswith("SSH-2.0-OpenSSH_10") else "?")
    # 役割判定: mps/macOS は必ず Mac fleet (高 VRAM の Mac を EVO 誤判定しない — 本ツールの存在意義)。
    # cuda/rocm が EVO。VRAM>=24 は GPU 種別不明時の補助シグナルにとどめる。
    if dtype == "mps" or os_kind == "macos":
        role = "mac-fleet"
    elif dtype in ("cuda", "rocm") or (dtype == "" and os_kind in ("ubuntu", "linux") and vram >= 24):
        role = "evo"
    else:
        role = "unknown"
    return {"ip": ip, "role": role, "gpu": dtype or "?", "vram_gib": vram,
            "os": os_kind, "mac": arp_mac(ip),
            "models": models, "ssh": banner[:40]}


def scan(cidr: str) -> list[dict]:
    net = ipaddress.ip_network(cidr, strict=False)
    hosts = [str(h) for h in net.hosts()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=128) as ex:
        list(ex.map(ping, hosts))  # ARP を温める
    with concurrent.futures.ThreadPoolExecutor(max_workers=128) as ex:
        found = [r for r in ex.map(probe, hosts) if r]
    return sorted(found, key=lambda r: ipaddress.ip_address(r["ip"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cidr", default="192.168.1.0/24")
    ap.add_argument("--evo", action="store_true", help="EVO の IP だけ出力")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    hosts = scan(args.cidr)

    if args.evo:
        evo = [h for h in hosts if h["role"] == "evo"]
        if not evo:
            print("no EVO found on LAN", file=sys.stderr)
            return 1
        print(evo[0]["ip"])
        return 0
    if args.json:
        print(json.dumps(hosts, indent=2))
        return 0

    print(f"{'IP':<15} {'role':<10} {'gpu':<6} {'vram':>5} {'os':<7} models")
    for h in hosts:
        print(f"{h['ip']:<15} {h['role']:<10} {h['gpu']:<6} "
              f"{h['vram_gib']:>4}G {h['os']:<7} {','.join(h['models'])[:40]}")
    evo = [h for h in hosts if h["role"] == "evo"]
    macs = [h for h in hosts if h["role"] == "mac-fleet"]
    print(f"\n{len(macs)} mac-fleet, {len(evo)} EVO"
          + (f" @ {evo[0]['ip']}" if evo else " (NOT FOUND — powered off?)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
