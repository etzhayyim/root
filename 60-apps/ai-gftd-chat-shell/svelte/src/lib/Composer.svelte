<script lang="ts">
  import { m } from "../paraglide/messages.js";

  let { busy, onSend }: {
    busy: boolean;
    onSend: (text: string, tier: "fast" | "balanced" | "reasoning") => Promise<void>;
  } = $props();

  let text = $state("");
  let tier = $state<"fast" | "balanced" | "reasoning">("balanced");
  let area: HTMLTextAreaElement | undefined = $state();

  function autosize() {
    if (!area) return;
    area.style.height = "auto";
    area.style.height = Math.min(area.scrollHeight, 240) + "px";
  }

  async function submit() {
    const t = text.trim();
    if (!t || busy) return;
    text = "";
    autosize();
    await onSend(t, tier);
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      void submit();
    }
  }
</script>

<form class="composer" onsubmit={(e) => { e.preventDefault(); void submit(); }}>
  <textarea
    bind:this={area}
    bind:value={text}
    oninput={autosize}
    onkeydown={onKeydown}
    placeholder={m.composer_placeholder()}
    rows="1"
    aria-label="Message"
    disabled={busy}
  ></textarea>
  <div class="bar">
    <div class="tier">
      <label>
        <input type="radio" bind:group={tier} value="fast" />
        {m.tier_fast()}
      </label>
      <label>
        <input type="radio" bind:group={tier} value="balanced" />
        {m.tier_balanced()}
      </label>
      <label>
        <input type="radio" bind:group={tier} value="reasoning" />
        {m.tier_reasoning()}
      </label>
    </div>
    <button type="submit" disabled={busy || !text.trim()} aria-label={m.send()}>
      {busy ? m.sending() : m.send()}
    </button>
  </div>
</form>

<style>
  .composer {
    border-top: 1px solid #232735;
    padding: 10px 16px 14px;
    background: #0f1115;
  }
  textarea {
    width: 100%;
    background: #161922;
    color: #e6e7e9;
    border: 1px solid #2f3445;
    border-radius: 10px;
    padding: 12px;
    font-size: 14px;
    font-family: inherit;
    resize: none;
    line-height: 1.5;
    outline: none;
    max-height: 240px;
  }
  textarea:focus { border-color: #4a4f64; }
  textarea:disabled { opacity: 0.6; }
  .bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 6px;
  }
  .tier {
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: #8a8e9a;
  }
  .tier label { cursor: pointer; }
  button {
    background: #2e334a;
    color: #e6e7e9;
    border: 1px solid #3a405a;
    border-radius: 8px;
    padding: 6px 18px;
    font-size: 14px;
    cursor: pointer;
  }
  button:hover:not(:disabled) { background: #353b55; }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
