<script lang="ts">
  // mehikari.etzhayyim.com トップ — 技術説明 (静的) + 問合せ動線。
  // Phase 0 段階は「公開しない」前提、Phase 1 (警察庁照会) 直前に公開判断。
</script>

<svelte:head>
  <title>眼光り (mehikari) — 監視カメラ シーン/人物検索 技術説明</title>
  <meta name="description" content="日本の警察捜査支援を目的とした監視カメラ映像の シーン記述検索 + 令状ゲート付き人物再特定の技術説明。運営: amanomibashira / 技術: etzhayyim Japan株式会社" />
  <meta name="robots" content="noindex, nofollow" />
</svelte:head>

<main>
  <header>
    <p class="kana">めひかり</p>
    <h1>眼光り <small>mehikari</small></h1>
    <p class="tagline">監視カメラ映像のシーン記述検索 + 令状ゲート付き人物再特定。<br/>日本の警察捜査支援を目的とした、プライバシー設計を最初に固めた技術です。</p>
  </header>

  <section class="constraints">
    <h2>設計の前提</h2>
    <ol>
      <li><strong>顔特徴量は国内 GPU 拠点内のみ。</strong>AES-256-GCM 暗号化で保管され、Cloudflare / 外部 LLM / 海外推論基盤への送信は protocol レベルで遮断されています。</li>
      <li><strong>シーン記述検索と人物再特定を経路レベルで分離。</strong>「赤い帽子・自転車・黒バックパック」のような<u>属性検索</u>は令状不要 (任意捜査範囲)、<u>既知人物の再特定</u>は令状又は捜査関係事項照会書 + 上席承認がハードゲートとして組み込まれています。</li>
      <li><strong>top-1 自動採用は不可能。</strong>人間判断介在義務 (human review gate) を Conditional edge で必須化、レビュー記録なしには証拠パケット出力に進めません。</li>
      <li><strong>音声トラックは ingest 時点で破棄。</strong>通信の秘密 (電気通信事業法4条) に配慮しています。</li>
      <li><strong>監査ログは 7 年保管。</strong>各操作 (令状情報・操作者・mTLS 指紋・IP) を append-only で記録します。</li>
    </ol>
  </section>

  <section class="pitch">
    <h2>想定利用シーン</h2>
    <dl>
      <dt>特殊詐欺の受け子同一性照合</dt>
      <dd>複数現場の街頭カメラから類似属性の人物クリップを抽出。再特定は令状ゲート経由で確定。</dd>
      <dt>行方不明者捜索</dt>
      <dd>家族同意 + 警察依頼に基づき、人物特定情報を入力した再特定検索を実行。</dd>
      <dt>街頭犯罪のシーン検索</dt>
      <dd>「黒いフード・自転車・午後10時前後」のような自然言語記述で時間帯横断のクリップを抽出。</dd>
    </dl>
  </section>

  <section class="entity">
    <h2>運営・実装責任</h2>
    <table>
      <tbody>
        <tr><th>運営主体</th><td>amanomibashira (operating entity)</td></tr>
        <tr><th>実装受託</th><td>etzhayyim Japan株式会社 (vendor)</td></tr>
        <tr><th>個人情報保護法上の取扱事業者</th><td>amanomibashira</td></tr>
        <tr><th>顔特徴量管理責任者</th><td>amanomibashira 法務最高責任者 (CLO)</td></tr>
        <tr><th>監査ログ保管期間</th><td>7 年 (法定)</td></tr>
      </tbody>
    </table>
  </section>

  <section class="nav">
    <h2>詳細</h2>
    <ul>
      <li><a href="/tech">技術仕様 (アーキテクチャ / 推論経路 / 暗号化)</a></li>
      <li><a href="/trust">プライバシー設計と法令準拠</a></li>
      <li><a href="/contact">情報提供をご希望の方 (opt-in form)</a></li>
    </ul>
  </section>

  <footer>
    <p class="disclaimer">本ページは公務員倫理規程・特定電子メール法に配慮し、招待・贈答・無料デモ提供等の利益供与に該当する文言を含みません。本サービスは警察庁通達 R6 公開草案 / 個人情報保護委員会 生体識別子ガイドライン草案を踏まえて設計されています。確定通達が公開され次第、技術仕様を再確認します。</p>
    <p class="copy">© amanomibashira (operating) / etzhayyim Japan株式会社 (vendor) — 2026</p>
  </footer>
</main>

<style>
  main { max-width: 760px; margin: 0 auto; padding: 2rem 1.25rem; font-family: -apple-system, "Hiragino Sans", sans-serif; line-height: 1.7; color: #1f2937; }
  header { border-bottom: 1px solid #d1d5db; padding-bottom: 1.5rem; margin-bottom: 1.5rem; }
  .kana { color: #6b7280; font-size: 0.85rem; letter-spacing: 0.2em; margin: 0; }
  h1 { margin: 0.25rem 0 0.5rem; font-size: 2.25rem; }
  h1 small { font-size: 1rem; color: #6b7280; margin-left: 0.5rem; font-weight: 400; letter-spacing: 0.1em; }
  .tagline { color: #374151; }
  h2 { font-size: 1.15rem; margin-top: 2.25rem; border-left: 3px solid #1f2937; padding-left: 0.6rem; }
  ol, dl { padding-left: 1.25rem; }
  dt { font-weight: 600; margin-top: 0.5rem; }
  dd { margin: 0.1rem 0 0.5rem; color: #4b5563; }
  table { border-collapse: collapse; width: 100%; }
  table th, table td { border-bottom: 1px dotted #d1d5db; padding: 0.5rem; text-align: left; font-weight: 400; }
  table th { color: #6b7280; width: 14rem; font-size: 0.9rem; }
  .nav ul { padding-left: 1.25rem; }
  .nav a { color: #1d4ed8; text-decoration: underline; }
  footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #d1d5db; }
  .disclaimer { font-size: 0.78rem; color: #6b7280; }
  .copy { font-size: 0.78rem; color: #9ca3af; }
  u { text-decoration: underline; text-underline-offset: 2px; }
</style>
