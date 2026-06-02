<script lang="ts">
  // /unsubscribe?t=<token> — 単発 token (mail 内 link) からの即時オプトアウト。
  import { onMount } from "svelte";

  let token = "";
  let reason = "";
  let status: "idle" | "submitting" | "done" | "error" = "idle";
  let message = "";

  onMount(() => {
    const u = new URL(window.location.href);
    token = u.searchParams.get("t") ?? "";
  });

  async function onSubmit(e: SubmitEvent) {
    e.preventDefault();
    if (!token) {
      status = "error";
      message = "オプトアウトリンクが不正です。メール末尾のリンクから再度アクセスしてください。";
      return;
    }
    status = "submitting";
    try {
      const res = await fetch("/xrpc/com.etzhayyim.apps.mehikari.unsubscribe", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ token, reason, userAgent: navigator.userAgent }),
      });
      const json = await res.json();
      if (json.status === "unsubscribed" || json.status === "alreadyUnsubscribed") {
        status = "done";
        message = "オプトアウトを承りました。今後 amanomibashira / etzhayyim Japan からの当該案件に関するメールはお送りしません。";
      } else if (json.status === "tokenExpired") {
        status = "error";
        message = "オプトアウトリンクの有効期限が切れています。お手数ですが mehikari-info@etzhayyim.com までご一報ください。";
      } else {
        status = "error";
        message = json.error || `処理できませんでした (${json.status ?? "unknown"})。`;
      }
    } catch (err) {
      status = "error";
      message = `送信エラー: ${(err as Error).message}`;
    }
  }
</script>

<svelte:head>
  <title>オプトアウト — 眼光り (mehikari)</title>
  <meta name="robots" content="noindex, nofollow" />
</svelte:head>

<main>
  <h1>オプトアウト</h1>
  <p>本フォームから即時にオプトアウトを承ります。<br/>特定電子メール法 §3 に基づき、以後 mehikari に関する営業連絡をお送りしません。</p>

  {#if status === "done"}
    <p class="result ok">{message}</p>
  {:else if status === "error"}
    <p class="result err">{message}</p>
  {/if}

  {#if status !== "done"}
    <form on:submit={onSubmit}>
      <label>オプトアウト理由 <small>(任意 — 改善のため)</small>
        <textarea bind:value={reason} maxlength="240" rows="3"></textarea>
      </label>
      <p class="hint">理由欄に個人を特定し得る情報を含めないでください (記載があった場合は backend で破棄します)。</p>
      <button type="submit" disabled={status === "submitting"}>{status === "submitting" ? "処理中…" : "オプトアウトする"}</button>
    </form>
  {/if}

  <p class="back"><a href="/">← トップへ戻る</a></p>
</main>

<style>
  main { max-width: 560px; margin: 0 auto; padding: 2rem 1.25rem; font-family: -apple-system, "Hiragino Sans", sans-serif; line-height: 1.7; color: #1f2937; }
  h1 { font-size: 1.4rem; }
  form { display: flex; flex-direction: column; gap: 1rem; margin-top: 1rem; }
  label { font-size: 0.9rem; color: #374151; }
  label small { color: #6b7280; font-weight: 400; }
  textarea { display: block; width: 100%; padding: 0.5rem; margin-top: 0.3rem; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 0.9rem; font-family: inherit; }
  .hint { font-size: 0.78rem; color: #6b7280; }
  button { background: #1f2937; color: #f9fafb; padding: 0.55rem 1.2rem; border: 0; border-radius: 4px; cursor: pointer; align-self: flex-start; }
  button:disabled { opacity: 0.5; cursor: wait; }
  .result { padding: 0.7rem 1rem; border-radius: 4px; }
  .result.ok { background: #ecfdf5; color: #065f46; border: 1px solid #6ee7b7; }
  .result.err { background: #fef2f2; color: #991b1b; border: 1px solid #fca5a5; }
  .back { margin-top: 2rem; font-size: 0.85rem; }
  .back a { color: #1d4ed8; }
</style>
