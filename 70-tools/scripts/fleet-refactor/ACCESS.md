# Fleet / EVO アクセス手順と再発防止

DHCP 変動・OS 再インストール・古い鍵で接続情報が腐るのを防ぐための運用ルール。

## ノードの見つけ方 — IP を信用しない

静的 IP (fleet.edn の `.70`、ssh config の `.22`) は **DHCP で腐る**。
実際 2026-06-12 時点で EVO の記録 IP は別マシン (Mac) を指していた。
**必ず能力ベースで動的同定する:**

```sh
./discover.py            # 全 Ollama/ComfyUI ホストを role 付きで一覧
./discover.py --evo      # EVO の現在 IP だけ (cuda GPU + Ubuntu で同定)
./evossh.sh [cmd]        # EVO へ動的解決して ssh (gad@<解決IP>)
```

同定キー: ComfyUI `device.type` (`cuda`/`rocm`=EVO, `mps`=Mac fleet) +
SSH バナー (Ubuntu vs macOS OpenSSH_10) + MAC ベンダ。

## EVO-X2 (gad)

- ハード: AMD Ryzen AI MAX+ 395 / Radeon 8060S iGPU (**gfx1151**, RDNA3.5) /
  62 GiB RAM / 591 GB disk。ROCm `/opt/rocm` 導入済。
- OS: **Ubuntu 24.04.2 LTS** (Windows から再インストール済 — だから host key が変化し、
  旧 Windows 前提の記述が全部腐っていた)。
- 同定: 2026-06-12 = `192.168.1.16` (要 `discover.py --evo` 再確認)。
- 認証: 公開鍵のみ運用 (`~/.ssh/id_ed25519` = jacob)。**孤児鍵を除去済**
  (旧 `jun784@gmail.com` / `junkawasaki@kyber-builder` を 2026-06-12 に削除、
  バックアップ `~/.ssh/authorized_keys.bak-*` を EVO 上に保存)。
- パスワード (緊急時): Apple Keychain の `com.microsoft.rdc.macos` (RDP) 項目に保管。
  `security find-generic-password -s com.microsoft.rdc.macos -a <acct> -w`。

## 鍵を再設置する場合 (新しいクライアントから)

EVO 端末で直接、または既存の鍵を持つマシンから:

```sh
# EVO 端末で:
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo '<新しい公開鍵>' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## 再発防止チェックリスト

1. **IP を設定ファイルに直書きしない** — `discover.py` で解決する。どうしても
   書くなら必ず「DHCP 変動・要再確認」コメントと同定日を併記。
2. **接続先の同一性を確認してから資格情報を送らない** — host key 変化時は
   「別マシンかも」を疑う (今回 .22 は Mac だった)。MAC ベンダ + OS バナー +
   GPU 種別で裏取り。
3. **authorized_keys は棚卸しする** — 出所不明・秘密鍵が手元に無い孤児鍵は除去。
4. **パスワード総当たりをしない** — ロックリスク。Keychain/1Password を先に探す。
5. fleet.edn の静的 IP は SSoT ではなく「最後に観測した値」と理解する。
