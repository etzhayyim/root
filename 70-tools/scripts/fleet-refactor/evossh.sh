#!/usr/bin/env bash
# evossh — EVO-X2 (gad) へ動的解決して ssh する。
#
# 再発防止: fleet.edn / ssh config の静的 IP は DHCP で腐る (.70→.22 と記録され、
# .22 は実際には Mac だった)。IP を埋めず、毎回 discover.py で能力同定して解決する。
#
#   ./evossh.sh                 # 対話ログイン
#   ./evossh.sh nvidia-smi      # リモートコマンド
#   EVO_IP=192.168.1.16 ./evossh.sh   # 解決をスキップ (既知時の高速パス)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
IP="${EVO_IP:-$(python3 "$HERE/discover.py" --evo)}"
if [ -z "$IP" ]; then echo "EVO not found on LAN (powered off?)" >&2; exit 1; fi
echo "evo → gad@$IP" >&2
exec ssh -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null \
     -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes "gad@$IP" "$@"
