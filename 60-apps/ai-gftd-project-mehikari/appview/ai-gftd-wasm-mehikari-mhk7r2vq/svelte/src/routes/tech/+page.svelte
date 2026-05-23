<script lang="ts">
  // /tech — 技術仕様 (アーキテクチャ・推論経路・暗号化)。技術担当向け。
</script>

<svelte:head>
  <title>技術仕様 — 眼光り (mehikari)</title>
  <meta name="robots" content="noindex, nofollow" />
</svelte:head>

<main>
  <h1>技術仕様</h1>

  <section>
    <h2>1. アーキテクチャ概要</h2>
    <pre>
警察 LAN / VPN  ─ mTLS ─▶  CF Worker (mehikari.etzhayyim.com) [edge, 状態なし]
                              │
                              ▼ XRPC dispatch
                          bpmn-dispatcher (k8s, JP)
                              │
                              ▼
                          LangGraph Server (Granian L3, JP)
                              │
                              ▼ inference (国内拘束)
                          murakumo on-prem (JP DC, NVIDIA GPU)
                              │
                              ▼ canonical state
                          RisingWave (Vultr LAX, encrypted at rest)
    </pre>
    <p>CF Worker は state を持たず、edge から DB へ直接接続しません。全 read/write は XRPC → agentgateway MCP router 経由で JP 拠点に集約されます。</p>
  </section>

  <section>
    <h2>2. 推論経路 (国内拘束)</h2>
    <table>
      <thead>
        <tr><th>処理</th><th>場所</th><th>送信されるデータ</th></tr>
      </thead>
      <tbody>
        <tr><td>frame decode (ffmpeg + nvjpeg)</td><td>murakumo on-prem (JP)</td><td>raw mp4 (R2 から fetch, 揮発)</td></tr>
        <tr><td>face detection + arcface embedding</td><td>murakumo on-prem (JP)</td><td>frame jpeg (in-memory)</td></tr>
        <tr><td>person ReID (OSNet)</td><td>murakumo on-prem (JP)</td><td>frame jpeg (in-memory)</td></tr>
        <tr><td>scene CLIP encoding</td><td>murakumo on-prem (JP)</td><td>frame jpeg (in-memory)</td></tr>
        <tr><td>OCR (JP plate / sign)</td><td>murakumo on-prem (JP)</td><td>frame jpeg (in-memory)</td></tr>
        <tr><td>scene query 自然言語パース (テキストのみ)</td><td>RunPod US-KS-2 (vLLM gemma-4-26B-A4B)</td><td>シーン記述文字列のみ — PII 非含有</td></tr>
        <tr><td>sales draft 生成 + safety_review</td><td>RunPod US-KS-2</td><td>担当者氏名は暗号化済 ciphertext で template に embed しない</td></tr>
      </tbody>
    </table>
  </section>

  <section>
    <h2>3. 暗号化と vault</h2>
    <ul>
      <li>顔特徴量 (template) は AES-256-GCM (ciphertext + wrapped key + kid) で保管。master key は Cloudflare Secrets Store / KMS HSM の二系統で wrap。</li>
      <li>復号は murakumo on-prem の Trusted Compute エンクレーブ内でのみ。Worker / R2 / edge storage 経路には平文が物理的に存在しない設計。</li>
      <li>営業 lead の担当者氏名も同方式で暗号化保管。送信時のみ pod 内で展開 → message body に埋め込み → 送信後即 GC。</li>
    </ul>
  </section>

  <section>
    <h2>4. データ保管期間</h2>
    <table>
      <thead>
        <tr><th>データ</th><th>保管期間</th><th>破棄手段</th></tr>
      </thead>
      <tbody>
        <tr><td>Raw clip mp4</td><td>案件確定後 90 日</td><td>R2 lifecycle (hard delete)</td></tr>
        <tr><td>Frame jpeg (cache)</td><td>30 日</td><td>lifecycle</td></tr>
        <tr><td>face template (encrypted)</td><td>案件解決 1 年後</td><td>DELETE + key destruction</td></tr>
        <tr><td>Embeddings (clip / reid)</td><td>案件解決 1 年後</td><td>index rebuild w/o entry</td></tr>
        <tr><td>Audit log</td><td>7 年 (法定)</td><td>S3 archive</td></tr>
        <tr><td>Sales lead / consent</td><td>opt-out 即時 / 5 年</td><td>DELETE (root rule: soft delete 禁止)</td></tr>
      </tbody>
    </table>
  </section>

  <section>
    <h2>5. 関連 ADR</h2>
    <ul>
      <li>ADR-2605111200 — CF Worker = Edge-Only; RW 接続は K8s Pod のみ</li>
      <li>ADR-2605091400 — MCP as cell membrane; XRPC は内部 cytoplasmic wire</li>
      <li>ADR-0048 — RisingWave Vultr + B2 primary</li>
      <li>ADR-2605010000 — RunPod 6000 Ada (LLM inference SSoT, テキスト処理のみ)</li>
      <li>ADR-0036 — 3-Tier Write (Social / Domain / State)</li>
      <li>CLAUDE.md root rule — Vault zero-knowledge invariant (顔 template に拡張適用)</li>
    </ul>
  </section>

  <p class="back"><a href="/">← トップへ戻る</a></p>
</main>

<style>
  main { max-width: 820px; margin: 0 auto; padding: 2rem 1.25rem; font-family: -apple-system, "Hiragino Sans", sans-serif; line-height: 1.7; color: #1f2937; }
  h1 { font-size: 1.6rem; border-bottom: 1px solid #d1d5db; padding-bottom: 0.5rem; }
  h2 { font-size: 1.1rem; margin-top: 2rem; border-left: 3px solid #1f2937; padding-left: 0.6rem; }
  pre { background: #0f172a; color: #e2e8f0; padding: 1rem; border-radius: 6px; font-size: 0.8rem; overflow-x: auto; }
  ul { padding-left: 1.2rem; }
  li { margin: 0.3rem 0; }
  table { border-collapse: collapse; width: 100%; margin: 0.5rem 0; }
  table th, table td { border: 1px solid #e5e7eb; padding: 0.45rem 0.6rem; text-align: left; font-size: 0.88rem; vertical-align: top; }
  table th { background: #f3f4f6; color: #1f2937; font-weight: 600; }
  .back { margin-top: 2rem; font-size: 0.85rem; }
  .back a { color: #1d4ed8; }
</style>
