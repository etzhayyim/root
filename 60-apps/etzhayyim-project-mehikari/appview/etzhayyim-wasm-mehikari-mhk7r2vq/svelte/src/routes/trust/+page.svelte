<script lang="ts">
  // /trust — プライバシー設計と法令準拠の説明。法務確認後に refactor。
</script>

<svelte:head>
  <title>プライバシー設計と法令準拠 — 眼光り (mehikari)</title>
  <meta name="robots" content="noindex, nofollow" />
</svelte:head>

<main>
  <h1>プライバシー設計と法令準拠</h1>

  <section>
    <h2>1. 顔特徴量の取扱い</h2>
    <ul>
      <li>顔特徴量 (face template) は<strong>要配慮個人情報相当</strong>として扱います (個人情報保護委員会 生体識別子ガイドライン草案準拠)。</li>
      <li>抽出と保管は日本国内 GPU 拠点で完結します。Cloudflare / 外部 LLM / 海外推論基盤への送信は protocol レベルで遮断されています。</li>
      <li>保管時は AES-256-GCM 暗号化 + vault key rotation。Worker / R2 / edge storage 等のエッジ層には平文が一切到達しません。</li>
      <li>案件解決 1 年経過後、ciphertext + wrapped key を物理削除 (hard delete) します。soft delete は行いません。</li>
    </ul>
  </section>

  <section>
    <h2>2. 検索経路の分離</h2>
    <ul>
      <li>シーン記述検索 (色・服装・物体・行動) は人物特定情報を返さず、令状不要 (任意捜査範囲) で運用します。</li>
      <li>既知人物の再特定 (queryPerson) は、捜索差押許可状その他令状又は捜査関係事項照会書 番号の入力なしには起動しません。さらに上席 (supervisor) 承認が consent helper の二段ゲートを構成します。</li>
      <li>top-1 自動採用は不可能です。投資判断や逮捕等の処分につながる判定には、必ず investigator の人間判定を介在させ、その判定記録なしには証拠パケット出力 (exportEvidence) に進めません。</li>
    </ul>
  </section>

  <section>
    <h2>3. 通信・音声・車両情報</h2>
    <ul>
      <li>音声トラックは ingest 時点で破棄します (通信の秘密 / 電気通信事業法 4 条配慮)。</li>
      <li>OCR で取得した車両ナンバーは default で masked 表示とし、警察照会時のみ unmask します。</li>
      <li>カメラ所有者 (商業施設・自治体・鉄道等) との録画利用合意なしには ingest 経路で hard-reject します。</li>
    </ul>
  </section>

  <section>
    <h2>4. 監査と人間判断</h2>
    <ul>
      <li>各操作 (令状情報・操作者 DID・mTLS 指紋・IP) を append-only で記録します。保管期間 7 年 (法定)。</li>
      <li>都道府県警の監督部署は監査ログ照会権限を持ち、改ざんは設計上不可能 (sha256 chain で検証)。</li>
      <li>人間判断介在 (human review gate) は LangGraph の Conditional edge に組み込まれており、跳ばすことができません。</li>
    </ul>
  </section>

  <section>
    <h2>5. 営業連絡における opt-in</h2>
    <ul>
      <li>営業メールは「特定電子メール法 §3 同意取得」の 4 経路 (展示会名簿 / 講演主催者経由 / 紹介 / inbound 問合せ) のみから送信します。それ以外への送信は技術的にブロックされます。</li>
      <li>送信時間帯は平日 09:00-17:00 JST に制限されます。</li>
      <li>本文には必ずオプトアウト導線が含まれます。受信されたオプトアウトは即時処理し、関連 ciphertext + wrapped key を物理削除します。</li>
      <li>公務員相手の営業時に、招待・贈答・粗品・無料デモ提供等の利益供与に該当し得る文言は安全ゲートでブロックされます (公務員倫理規程配慮)。</li>
    </ul>
  </section>

  <section>
    <h2>6. 運営・実装責任</h2>
    <table>
      <tbody>
        <tr><th>運営主体 (operating entity)</th><td>amanomibashira</td></tr>
        <tr><th>実装受託 (vendor)</th><td>etzhayyim Japan株式会社</td></tr>
        <tr><th>個情法上の取扱事業者</th><td>amanomibashira</td></tr>
        <tr><th>顔特徴量管理責任者</th><td>amanomibashira CLO</td></tr>
        <tr><th>インシデント窓口</th><td>privacy@etzhayyim.com (24h 受付)</td></tr>
        <tr><th>外部弁護士監修</th><td>Phase 0 期間中、警察庁 / 個情委 practice 経験を持つ事務所と契約 (常時 monitoring 体制)</td></tr>
      </tbody>
    </table>
  </section>

  <p class="meta">本ページは警察庁通達 R6 公開草案 / 個人情報保護委員会 生体識別子ガイドライン草案を踏まえて記載しています。確定通達公開後 1 ヶ月以内に整合確認のうえ更新します。</p>

  <p class="back"><a href="/">← トップへ戻る</a></p>
</main>

<style>
  main { max-width: 760px; margin: 0 auto; padding: 2rem 1.25rem; font-family: -apple-system, "Hiragino Sans", sans-serif; line-height: 1.7; color: #1f2937; }
  h1 { font-size: 1.6rem; border-bottom: 1px solid #d1d5db; padding-bottom: 0.5rem; }
  h2 { font-size: 1.1rem; margin-top: 2rem; border-left: 3px solid #1f2937; padding-left: 0.6rem; }
  ul { padding-left: 1.2rem; }
  li { margin: 0.3rem 0; }
  table { border-collapse: collapse; width: 100%; margin-top: 0.5rem; }
  table th, table td { border-bottom: 1px dotted #d1d5db; padding: 0.5rem; text-align: left; font-weight: 400; }
  table th { color: #6b7280; width: 16rem; font-size: 0.9rem; }
  .meta { font-size: 0.78rem; color: #6b7280; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #d1d5db; }
  .back { margin-top: 2rem; font-size: 0.85rem; }
  .back a { color: #1d4ed8; }
</style>
