<script lang="ts">
  // opt-in form. submit 時に handleInboundReply ではなく registerProspect (inbound 経路) を kick。
  // opt-in source は 4 値固定。それ以外は backend で reject。
  let agencyType: "prefectural" | "npa" | "jc3" | "mlit" | "" = "";
  let department = "";
  let role = "";
  let nameSurname = "";
  let nameGiven = "";
  let email = "";
  let phone = "";
  let optInSource: "exhibition_list" | "lecture_host" | "referral" | "inbound" = "inbound";
  let optInEvidence = "";
  let useCasePitch: "fraud" | "missingPerson" | "streetCrime" | "" = "";
  let agree = false;
  let submitting = false;
  let resultMessage = "";
  let resultKind: "ok" | "err" | "" = "";

  async function onSubmit(e: SubmitEvent) {
    e.preventDefault();
    if (!agree) {
      resultKind = "err";
      resultMessage = "個人情報の取扱いへの同意が必要です。";
      return;
    }
    if (!nameSurname || !email) {
      resultKind = "err";
      resultMessage = "氏名 (姓) と メールアドレスは必須です。";
      return;
    }
    submitting = true;
    try {
      const payload = {
        prefecture: agencyType === "npa" ? "NPA" : agencyType === "jc3" ? "JC3" : agencyType === "mlit" ? "MLIT" : "",
        addresseeRole: role,
        // 平文を edge には送らない: backend で AES-256-GCM 暗号化 → addresseeCipher へ
        plaintextSurname: nameSurname,
        plaintextGiven: nameGiven,
        contactEmail: email,
        contactPhone: phone,
        department,
        optInSource,
        optInAt: new Date().toISOString(),
        optInEvidence: optInEvidence || `inbound:${window.location.host}/contact`,
        useCasePitch: useCasePitch || undefined,
      };
      const res = await fetch("/xrpc/com.etzhayyim.apps.mehikari.registerProspect", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const json = await res.json();
      if (json.status === "registered") {
        resultKind = "ok";
        resultMessage = "受領しました。担当 (amanomibashira) より平日 09:00-17:00 JST 内にご連絡します。";
      } else {
        resultKind = "err";
        resultMessage = json.error || `登録できませんでした (${json.status ?? "unknown"})。`;
      }
    } catch (err) {
      resultKind = "err";
      resultMessage = `送信エラー: ${(err as Error).message}`;
    } finally {
      submitting = false;
    }
  }
</script>

<svelte:head>
  <title>情報提供のご希望 — 眼光り (mehikari)</title>
  <meta name="robots" content="noindex, nofollow" />
</svelte:head>

<main>
  <h1>情報提供のご希望</h1>
  <p>本フォームは、貴機関ご自身の意思による情報提供希望 (opt-in) を取得するためのものです。<br/>送信後の連絡は amanomibashira (運営) 担当より、<strong>平日 09:00-17:00 JST</strong> 内にメールでお送りします。</p>

  <form on:submit={onSubmit} aria-busy={submitting}>
    <fieldset>
      <legend>所属</legend>

      <label>機関区分 <span class="req">必須</span>
        <select bind:value={agencyType} required>
          <option value="">— 選択してください —</option>
          <option value="prefectural">都道府県警察</option>
          <option value="npa">警察庁</option>
          <option value="jc3">JC3 (日本サイバー犯罪対策センター)</option>
          <option value="mlit">海上保安庁</option>
        </select>
      </label>

      <label>部署 <small>(例: 生活安全部サイバー犯罪対策課)</small>
        <input type="text" bind:value={department} maxlength="120" />
      </label>

      <label>役職 / 役割 <small>(例: 課長補佐, 警部, 一般職員)</small>
        <input type="text" bind:value={role} maxlength="60" />
      </label>
    </fieldset>

    <fieldset>
      <legend>ご連絡先</legend>

      <label>姓 <span class="req">必須</span>
        <input type="text" bind:value={nameSurname} required maxlength="60" autocomplete="family-name" />
      </label>

      <label>名
        <input type="text" bind:value={nameGiven} maxlength="60" autocomplete="given-name" />
      </label>

      <label>メールアドレス <span class="req">必須</span>
        <input type="email" bind:value={email} required maxlength="120" autocomplete="email" />
      </label>

      <label>電話番号 <small>(任意 — 必要時の折り返し用)</small>
        <input type="tel" bind:value={phone} maxlength="20" autocomplete="tel" />
      </label>
    </fieldset>

    <fieldset>
      <legend>情報提供希望の経緯 (opt-in source)</legend>
      <p class="hint">本サービスは特定電子メール法に基づき、以下 4 経路の opt-in 取得のみで連絡をお送りします。</p>

      <label class="radio"><input type="radio" bind:group={optInSource} value="exhibition_list" /> 展示会・公開イベントでお名刺を交換</label>
      <label class="radio"><input type="radio" bind:group={optInSource} value="lecture_host" /> 講演・研究発表の主催者経由でご紹介を受けた</label>
      <label class="radio"><input type="radio" bind:group={optInSource} value="referral" /> 知人・第三者からのご紹介</label>
      <label class="radio"><input type="radio" bind:group={optInSource} value="inbound" checked /> 本ページを直接ご覧になりお問合せ</label>

      <label>具体的経緯 <small>(任意 — 展示会名・紹介者名・参照したページ等)</small>
        <input type="text" bind:value={optInEvidence} maxlength="160" />
      </label>
    </fieldset>

    <fieldset>
      <legend>関心領域</legend>
      <p class="hint">どの用途に関心があるかご選択ください (情報提供の方向性を絞るためのみに使用)。</p>
      <label class="radio"><input type="radio" bind:group={useCasePitch} value="fraud" /> 特殊詐欺・組織犯罪</label>
      <label class="radio"><input type="radio" bind:group={useCasePitch} value="missingPerson" /> 行方不明者捜索</label>
      <label class="radio"><input type="radio" bind:group={useCasePitch} value="streetCrime" /> 街頭犯罪</label>
    </fieldset>

    <fieldset>
      <legend>個人情報の取扱い</legend>
      <p class="hint">
        本フォーム送信時に取得する情報は、amanomibashira (運営) が「特定電子メール法 §3 同意取得」「個人情報保護法 §17 利用目的特定」のもとで管理します。
        氏名は backend で AES-256-GCM 暗号化のうえ保管され、平文は Cloudflare 等のエッジ層に保存されません。
        オプトアウトは <a href="/unsubscribe">/unsubscribe</a> 又はメール末尾のリンクから即時可能です。
        詳細: <a href="/trust">プライバシー設計と法令準拠</a>
      </p>
      <label class="checkbox"><input type="checkbox" bind:checked={agree} /> 上記を理解し、情報提供を希望します。</label>
    </fieldset>

    <button type="submit" disabled={submitting}>{submitting ? "送信中…" : "送信"}</button>

    {#if resultMessage}
      <p class="result" class:ok={resultKind === "ok"} class:err={resultKind === "err"}>{resultMessage}</p>
    {/if}
  </form>

  <p class="back"><a href="/">← トップへ戻る</a></p>
</main>

<style>
  main { max-width: 640px; margin: 0 auto; padding: 2rem 1.25rem; font-family: -apple-system, "Hiragino Sans", sans-serif; line-height: 1.7; color: #1f2937; }
  h1 { font-size: 1.6rem; }
  form { display: flex; flex-direction: column; gap: 1.2rem; }
  fieldset { border: 1px solid #d1d5db; border-radius: 6px; padding: 1rem 1.2rem; }
  legend { padding: 0 0.4rem; font-weight: 600; color: #1f2937; }
  label { display: block; margin: 0.6rem 0; font-size: 0.95rem; color: #374151; }
  label small { color: #6b7280; font-weight: 400; }
  input[type="text"], input[type="email"], input[type="tel"], select { display: block; width: 100%; padding: 0.5rem 0.65rem; margin-top: 0.3rem; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 0.95rem; }
  .radio, .checkbox { display: flex; align-items: center; gap: 0.5rem; }
  .radio input, .checkbox input { width: auto; }
  .hint { font-size: 0.85rem; color: #6b7280; margin: 0.3rem 0; }
  .req { background: #fee2e2; color: #b91c1c; padding: 0 0.3rem; border-radius: 3px; font-size: 0.7rem; margin-left: 0.3rem; }
  button { background: #1f2937; color: #f9fafb; padding: 0.6rem 1.4rem; border: 0; border-radius: 5px; font-size: 0.95rem; cursor: pointer; align-self: flex-start; }
  button:disabled { opacity: 0.5; cursor: wait; }
  .result { padding: 0.7rem 1rem; border-radius: 4px; font-size: 0.9rem; }
  .result.ok { background: #ecfdf5; color: #065f46; border: 1px solid #6ee7b7; }
  .result.err { background: #fef2f2; color: #991b1b; border: 1px solid #fca5a5; }
  .back { margin-top: 2rem; font-size: 0.85rem; }
  .back a { color: #1d4ed8; }
</style>
