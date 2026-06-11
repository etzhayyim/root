# UMU ゲームメタ管理

`umu` は Godot の Web Export 納品物を `static/play/<slug>/` に配置して配信します。
ゲーム固有の運用情報はこの配下にまとめます。

## 推奨ディレクトリ構成（slug ごと）

- `games/<slug>/project.godot`
- `games/<slug>/etzhayyim-discovery.yaml`
- `wasm/umu-godot-hub/static/play/<slug>/` へゲーム成果物を配置

## 受け入れ基準（手動チェック）

- `project.godot` が存在すること
- `static/play/<slug>/index.html` が存在すること
- `wasm/umu-godot-hub/static/index.html` のメニューやリンク更新を反映していること

## `etzhayyim-discovery.yaml` の最低項目例

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: umu-discovery-<slug>
  namespace: etzhayyim-performers
data:
  framework: godot-web
  slug: <slug>
  entry: /play/<slug>/
  mcp: etzhayyim:platform/etzhayyim-mcp@0.1.0
```

## 開発フロー（実運用）

1. Godot で `Web (HTML5)` エクスポート
2. `wasm/umu-godot-hub/static/play/<slug>/` へ配置
3. `project.godot` を `games/<slug>/` に追加
4. `games/<slug>/etzhayyim-discovery.yaml` を追加
5. `WADM_MANIFEST=60-apps/etzhayyim-project-umu/wasm/umu-godot-hub/wadm/umu-godot-hub.wadm.yaml mage Deploy`
