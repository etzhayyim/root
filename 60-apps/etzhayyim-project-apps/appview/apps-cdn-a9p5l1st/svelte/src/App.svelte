<script lang="ts">
  type AvailabilityConfig = { inStock?: string[]; outOfStock?: string[]; preorder?: string[] };
  type SelectorConfig = {
    title?: string[];
    price?: string[];
    merchantSku?: string[];
    availability?: AvailabilityConfig;
  };

  type MerchantForm = {
    endpoint: string;
    merchantName: string;
    domain: string;
    baseCurrency: string;
    shippingPolicy: string;
    reputationScore: string;
    selectorProfile: string;
    selectorConfigText: string;
  };
  type MerchantRow = {
    merchantId: string;
    did?: string;
    name: string;
    domain: string;
    baseCurrency?: string;
    shippingPolicy?: string;
    reputationScore?: number;
    selectorProfile?: string;
    selectorVersion?: number;
    selectorConfig?: SelectorConfig;
    selectorRollout?: number;
    activeRevisionId?: string;
    status?: string;
    updatedAt?: string;
  };
  type SelectorRevision = {
    revisionId: string;
    merchantId: string;
    selectorProfile?: string;
    selectorVersion?: number;
    selectorConfig?: SelectorConfig;
    rollout?: number;
    isActive?: boolean;
    reason?: string;
    createdAt?: string;
  };
  type IngestProbeResult = {
    status?: string;
    selectedRevisionId?: string;
    selectorPath?: string;
    rolloutBucket?: number;
    selectorProfile?: string;
    selectorVersion?: number;
    extractionMethod?: string;
    extractedPrice?: number;
    extractedName?: string;
    offerId?: string;
  };

  const presetConfigs: Record<string, { selectorProfile: string; selectorConfig: SelectorConfig }> = {
    yodobashi_com: {
      selectorProfile: "yodobashi-v1",
      selectorConfig: {
        title: [
          `<meta[^>]+property=["']og:title["'][^>]+content=["']([^"']+)["']`,
          `<h1[^>]*class=["'][^"']*pHeading_name[^"']*["'][^>]*>([\\s\\S]*?)<\\/h1>`,
        ],
        price: [
          `<meta[^>]+property=["']product:price:amount["'][^>]+content=["']([^"']+)["']`,
          `id=["']js_scl_unitPrice["'][^>]*>\\s*([0-9,]+)\\s*<`,
        ],
        availability: {
          inStock: ["在庫あり", "翌日までにお届け"],
          outOfStock: ["予定数の販売を終了しました", "売り切れ"],
        },
        merchantSku: [
          `itemCode["']?\\s*[:=]\\s*["']([^"']+)["']`,
        ],
      },
    },
    biccamera_com: {
      selectorProfile: "biccamera-v1",
      selectorConfig: {
        title: [`<meta[^>]+property=["']og:title["'][^>]+content=["']([^"']+)["']`],
        price: [
          `<meta[^>]+property=["']product:price:amount["'][^>]+content=["']([^"']+)["']`,
          `class=["'][^"']*bcs_price[^"']*["'][^>]*>\\s*[¥￥]?\\s*([0-9,]+)`,
        ],
        availability: {
          inStock: ["在庫あり", "店舗在庫あり"],
          outOfStock: ["在庫切れ", "販売を終了"],
        },
      },
    },
    rakuten_co_jp: {
      selectorProfile: "rakuten-v1",
      selectorConfig: {
        title: [`<meta[^>]+property=["']og:title["'][^>]+content=["']([^"']+)["']`],
        price: [
          `<meta[^>]+property=["']product:price:amount["'][^>]+content=["']([^"']+)["']`,
          `itemPrice["']?\\s*[:=]\\s*["']?([0-9,]+)`,
        ],
        availability: {
          inStock: ["すぐに購入", "在庫あり"],
          outOfStock: ["売り切れ", "在庫切れ"],
        },
      },
    },
    amazon_co_jp: {
      selectorProfile: "amazon-v1",
      selectorConfig: {
        title: [`id=["']productTitle["'][^>]*>\\s*([\\s\\S]*?)\\s*<\\/span>`],
        price: [
          `id=["']priceblock_ourprice["'][^>]*>\\s*[¥￥]?\\s*([0-9,]+)`,
          `id=["']priceblock_dealprice["'][^>]*>\\s*[¥￥]?\\s*([0-9,]+)`,
          `id=["']corePriceDisplay_desktop_feature_div["'][\\s\\S]{0,300}?[¥￥]\\s*([0-9,]+)`,
        ],
        availability: {
          inStock: ["在庫あり", "通常\\s*[\\d]+?\\s*点在庫あり"],
          outOfStock: ["一時的に在庫切れ", "現在在庫切れ"],
        },
        merchantSku: [`\\/dp\\/([A-Z0-9]{10})`, `data-asin=["']([A-Z0-9]{10})["']`],
      },
    },
  };

  const formatConfig = (config: SelectorConfig) => JSON.stringify(config, null, 2);
  const normalizeDomain = (input: string) =>
    input.trim().toLowerCase().replace(/^https?:\/\//, "").replace(/^www\./, "").replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  const stripTags = (value: string) => value.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();

  let form: MerchantForm = $state({
    endpoint: "https://atproto.etzhayyim.com",
    merchantName: "Yodobashi",
    domain: "www.yodobashi.com",
    baseCurrency: "JPY",
    shippingPolicy: "standard",
    reputationScore: "4.8",
    selectorProfile: "yodobashi-v1",
    selectorConfigText: formatConfig(presetConfigs.yodobashi_com.selectorConfig),
  });

  let sampleHtml = $state(`<html><head><meta property="og:title" content="Nintendo Switch 2"><meta property="product:price:amount" content="49800"></head><body><h1 class="pHeading_name">Nintendo Switch 2</h1><div id="js_scl_unitPrice">49,800</div><p>在庫あり</p><div data-debug='var itemCode = "4902370553023";'></div></body></html>`);
  let submitState = $state<"idle" | "saving" | "saved" | "error">("idle");
  let submitMessage = $state("");
  let merchantQuery = $state("");
  let merchantList = $state<MerchantRow[]>([]);
  let merchantLoadState = $state<"idle" | "loading" | "error">("idle");
  let merchantLoadMessage = $state("");
  let revisions = $state<SelectorRevision[]>([]);
  let revisionState = $state<"idle" | "loading" | "error">("idle");
  let revisionMessage = $state("");
  let probeUrl = $state("https://www.yodobashi.com/product/4902370553023/");
  let probeState = $state<"idle" | "loading" | "error">("idle");
  let probeMessage = $state("");
  let probeResult = $state<IngestProbeResult | null>(null);

  const parsedConfig = $derived.by(() => {
    try {
      return JSON.parse(form.selectorConfigText) as SelectorConfig;
    } catch {
      return null;
    }
  });

  const parseRegexList = (patterns?: string[]) =>
    (patterns || []).flatMap((pattern) => {
      try {
        return [new RegExp(pattern, "i")];
      } catch {
        return [];
      }
    });

  const pickFirst = (html: string, patterns?: string[]) => {
    for (const regex of parseRegexList(patterns)) {
      const match = html.match(regex);
      if (match?.[1]) return stripTags(match[1]);
    }
    return "";
  };

  const availabilityMatch = (html: string, config?: AvailabilityConfig) => {
    const groups: Array<[keyof AvailabilityConfig, string]> = [
      ["inStock", "in_stock"],
      ["outOfStock", "out_of_stock"],
      ["preorder", "preorder"],
    ];
    for (const [sourceKey, value] of groups) {
      for (const pattern of parseRegexList(config?.[sourceKey])) {
        if (pattern.test(html)) return value;
      }
    }
    return "unknown";
  };

  async function readJsonWithFallback<T>(resp: Response, fallback: T, context: string): Promise<T> {
    try {
      return await resp.json() as T;
    } catch (error) {
      console.warn(`Failed to parse JSON for ${context}`, error);
      return fallback;
    }
  }

  const preview = $derived.by(() => {
    if (!parsedConfig) {
      return { title: "", price: "", merchantSku: "", availability: "invalid_json", ready: false };
    }
    return {
      title: pickFirst(sampleHtml, parsedConfig.title),
      price: pickFirst(sampleHtml, parsedConfig.price),
      merchantSku: pickFirst(sampleHtml, parsedConfig.merchantSku),
      availability: availabilityMatch(sampleHtml, parsedConfig.availability),
      ready: true,
    };
  });

  function applyPreset(domainValue: string) {
    const preset = presetConfigs[normalizeDomain(domainValue)];
    if (!preset) return;
    form.selectorProfile = preset.selectorProfile;
    form.selectorConfigText = formatConfig(preset.selectorConfig);
  }

  function applyMerchant(row: MerchantRow) {
    form.merchantName = row.name || "";
    form.domain = row.domain || "";
    form.baseCurrency = row.baseCurrency || "";
    form.shippingPolicy = row.shippingPolicy || "";
    form.reputationScore = String(row.reputationScore ?? "");
    form.selectorProfile = row.selectorProfile || "";
    form.selectorConfigText = formatConfig(row.selectorConfig || {});
    void loadRevisions(row.merchantId);
  }

  async function loadRevisions(merchantId: string) {
    if (!merchantId) return;
    revisionState = "loading";
    revisionMessage = "";
    try {
      const resp = await fetch(`${form.endpoint.replace(/\/$/, "")}/xrpc/com.etzhayyim.apps.kakaku.listSelectorRevisions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ merchantId, limit: 20 }),
      });
      const data = await readJsonWithFallback(resp, { revisions: [] }, "listSelectorRevisions");
      if (!resp.ok) throw new Error((data as { error?: string; message?: string }).message || (data as { error?: string }).error || `HTTP ${resp.status}`);
      revisions = Array.isArray((data as { revisions?: SelectorRevision[] }).revisions) ? (data as { revisions: SelectorRevision[] }).revisions : [];
      revisionState = "idle";
      revisionMessage = revisions.length ? "" : "revision がありません。";
    } catch (error) {
      revisionState = "error";
      revisionMessage = error instanceof Error ? error.message : "revision load failed";
    }
  }

  async function activateRevision(revision: SelectorRevision) {
    revisionState = "loading";
    revisionMessage = "";
    try {
      const resp = await fetch(`${form.endpoint.replace(/\/$/, "")}/xrpc/com.etzhayyim.apps.kakaku.activateSelectorRevision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          merchantId: revision.merchantId,
          revisionId: revision.revisionId,
          rollout: revision.rollout ?? 1,
        }),
      });
      const data = await readJsonWithFallback(resp, {}, "activateSelectorRevision");
      if (!resp.ok) throw new Error((data as { error?: string; message?: string }).message || (data as { error?: string }).error || `HTTP ${resp.status}`);
      revisionMessage = `activated: ${revision.revisionId}`;
      revisionState = "idle";
      await loadMerchants();
      await loadRevisions(revision.merchantId);
    } catch (error) {
      revisionState = "error";
      revisionMessage = error instanceof Error ? error.message : "activate failed";
    }
  }

  async function loadMerchants() {
    merchantLoadState = "loading";
    merchantLoadMessage = "";
    try {
      const resp = await fetch(`${form.endpoint.replace(/\/$/, "")}/xrpc/com.etzhayyim.apps.kakaku.listMerchants`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q: merchantQuery, limit: 100 }),
      });
      const data = await readJsonWithFallback(resp, { merchants: [] }, "listMerchants");
      if (!resp.ok) throw new Error((data as { error?: string; message?: string }).message || (data as { error?: string }).error || `HTTP ${resp.status}`);
      merchantList = Array.isArray((data as { merchants?: MerchantRow[] }).merchants) ? (data as { merchants: MerchantRow[] }).merchants : [];
      merchantLoadState = "idle";
      merchantLoadMessage = merchantList.length ? "" : "merchant がありません。";
    } catch (error) {
      merchantLoadState = "error";
      merchantLoadMessage = error instanceof Error ? error.message : "load failed";
    }
  }

  async function runProbe() {
    probeState = "loading";
    probeMessage = "";
    probeResult = null;
    try {
      const resp = await fetch(`${form.endpoint.replace(/\/$/, "")}/xrpc/com.etzhayyim.apps.kakaku.ingestOfferFromUrl`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          productUrl: probeUrl,
          merchantName: form.merchantName,
          domain: form.domain,
          name: "",
          currency: form.baseCurrency,
        }),
      });
      const data = await readJsonWithFallback(resp, {}, "ingestOfferFromUrl");
      if (!resp.ok) throw new Error((data as { error?: string; message?: string }).message || (data as { error?: string }).error || `HTTP ${resp.status}`);
      probeResult = data as IngestProbeResult;
      probeState = "idle";
      probeMessage = "probe completed";
    } catch (error) {
      probeState = "error";
      probeMessage = error instanceof Error ? error.message : "probe failed";
    }
  }

  async function saveMerchant() {
    if (!parsedConfig) {
      submitState = "error";
      submitMessage = "selectorConfig JSON が不正です。";
      return;
    }
    submitState = "saving";
    submitMessage = "";
    try {
      const resp = await fetch(`${form.endpoint.replace(/\/$/, "")}/xrpc/com.etzhayyim.apps.kakaku.registerMerchant`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          merchantName: form.merchantName,
          domain: form.domain,
          baseCurrency: form.baseCurrency,
          shippingPolicy: form.shippingPolicy,
          reputationScore: Number(form.reputationScore || "0"),
          selectorProfile: form.selectorProfile,
          selectorConfig: parsedConfig,
          selectorRollout: 1,
          reason: "editor save",
        }),
      });
      const data = await readJsonWithFallback(resp, {}, "registerMerchant");
      if (!resp.ok) throw new Error((data as { error?: string; message?: string }).message || (data as { error?: string }).error || `HTTP ${resp.status}`);
      submitState = "saved";
      submitMessage = `saved: ${(data as { merchantId?: string }).merchantId || form.merchantName}`;
      await loadMerchants();
      const savedMerchantId = (data as { merchantId?: string }).merchantId || "";
      if (savedMerchantId) await loadRevisions(savedMerchantId);
    } catch (error) {
      submitState = "error";
      submitMessage = error instanceof Error ? error.message : "save failed";
    }
  }

  $effect(() => {
    void form.endpoint;
    loadMerchants();
  });
</script>

<svelte:head>
  <title>Kakaku Merchant Selector Editor</title>
</svelte:head>

<main class="shell">
  <section class="hero">
    <p class="eyebrow">kakaku.etzhayyim.com</p>
    <h1>Merchant Selector Editor</h1>
    <p class="lede">
      `KakakuMerchant` の `selectorProfile` と `selectorConfig` をその場で編集し、同じ画面で抽出 preview を見てから
      `registerMerchant` を叩けます。
    </p>
  </section>

  <section class="grid">
    <article class="panel">
      <div class="panel-head">
        <h2>Merchant</h2>
        <button class="ghost" type="button" onclick={() => applyPreset(form.domain)}>Load Domain Preset</button>
      </div>
      <div class="field-grid">
        <label>
          <span>Endpoint</span>
          <input bind:value={form.endpoint} />
        </label>
        <label>
          <span>Merchant Name</span>
          <input bind:value={form.merchantName} />
        </label>
        <label>
          <span>Domain</span>
          <input bind:value={form.domain} onblur={() => applyPreset(form.domain)} />
        </label>
        <label>
          <span>Base Currency</span>
          <input bind:value={form.baseCurrency} />
        </label>
        <label>
          <span>Shipping Policy</span>
          <input bind:value={form.shippingPolicy} />
        </label>
        <label>
          <span>Reputation</span>
          <input bind:value={form.reputationScore} />
        </label>
        <label class="full">
          <span>Selector Profile</span>
          <input bind:value={form.selectorProfile} />
        </label>
      </div>

      <label class="stack">
        <span>Selector Config JSON</span>
        <textarea bind:value={form.selectorConfigText} rows="18" spellcheck="false"></textarea>
      </label>

      <div class="actions">
        <button class="primary" type="button" onclick={saveMerchant} disabled={submitState === "saving"}>
          {submitState === "saving" ? "Saving..." : "Save Merchant Config"}
        </button>
        <span class:ok={submitState === "saved"} class:error={submitState === "error"}>{submitMessage}</span>
      </div>
    </article>

    <article class="panel accent">
      <div class="panel-head">
        <h2>Preview</h2>
        <p>selector を sample HTML に当てて抽出結果を即確認します。</p>
      </div>

      <div class="preview-cards">
        <div class="metric">
          <span>title</span>
          <strong>{preview.title || "—"}</strong>
        </div>
        <div class="metric">
          <span>price</span>
          <strong>{preview.price || "—"}</strong>
        </div>
        <div class="metric">
          <span>merchantSku</span>
          <strong>{preview.merchantSku || "—"}</strong>
        </div>
        <div class="metric">
          <span>availability</span>
          <strong>{preview.availability}</strong>
        </div>
      </div>

      <label class="stack">
        <span>Sample HTML</span>
        <textarea bind:value={sampleHtml} rows="18" spellcheck="false"></textarea>
      </label>

      <div class="tips">
        <p>Preset domains: `yodobashi.com`, `biccamera.com`, `rakuten.co.jp`, `amazon.co.jp`</p>
        <p>Regex は capture group 1 を返す前提です。</p>
      </div>
    </article>
  </section>

  <section class="panel merchant-list">
    <div class="panel-head">
      <div>
        <h2>Merchant Library</h2>
        <p>graph 上の `KakakuMerchant` を読んで、そのまま editor に戻せます。</p>
      </div>
      <div class="searchbar">
        <input bind:value={merchantQuery} placeholder="search merchant/domain" />
        <button class="ghost" type="button" onclick={loadMerchants} disabled={merchantLoadState === "loading"}>
          {merchantLoadState === "loading" ? "Loading..." : "Refresh"}
        </button>
      </div>
    </div>

    {#if merchantLoadMessage}
      <p class:error={merchantLoadState === "error"}>{merchantLoadMessage}</p>
    {/if}

    <div class="merchant-table">
      {#each merchantList as merchant}
        <button class="merchant-row" type="button" onclick={() => applyMerchant(merchant)}>
          <div>
            <strong>{merchant.name}</strong>
            <span>{merchant.domain}</span>
          </div>
          <div>
            <span>{merchant.selectorProfile || "custom"} / v{merchant.selectorVersion || 0}</span>
            <span>{merchant.updatedAt || merchant.status || "active"} / rollout {merchant.selectorRollout ?? 1}</span>
          </div>
        </button>
      {/each}
    </div>
  </section>

  <section class="panel merchant-list">
    <div class="panel-head">
      <div>
        <h2>Selector Revisions</h2>
        <p>active version の切替と rollout 確認用です。</p>
      </div>
    </div>

    {#if revisionMessage}
      <p class:error={revisionState === "error"}>{revisionMessage}</p>
    {/if}

    <div class="merchant-table">
      {#each revisions as revision}
        <div class:active-revision={revision.isActive} class="merchant-row revision-row">
          <div>
            <strong>{revision.revisionId}</strong>
            <span>{revision.selectorProfile || "custom"} / v{revision.selectorVersion || 0}</span>
          </div>
          <div>
            <span>{revision.reason || "manual update"}</span>
            <span>{revision.createdAt || ""} / rollout {revision.rollout ?? 1}</span>
          </div>
          <div class="revision-actions">
            <button class="ghost" type="button" onclick={() => {
              form.selectorProfile = revision.selectorProfile || "";
              form.selectorConfigText = formatConfig(revision.selectorConfig || {});
            }}>Load</button>
            <button class="primary" type="button" onclick={() => activateRevision(revision)} disabled={!!revision.isActive || revisionState === "loading"}>Activate</button>
          </div>
        </div>
      {/each}
    </div>
  </section>

  <section class="panel merchant-list">
    <div class="panel-head">
      <div>
        <h2>Canary Probe</h2>
        <p>`ingestOfferFromUrl` を直接叩いて `selectedRevisionId / selectorPath` を観測します。</p>
      </div>
    </div>

    <div class="field-grid">
      <label class="full">
        <span>Product URL</span>
        <input bind:value={probeUrl} />
      </label>
    </div>

    <div class="actions">
      <button class="primary" type="button" onclick={runProbe} disabled={probeState === "loading"}>
        {probeState === "loading" ? "Probing..." : "Run Probe"}
      </button>
      <span class:error={probeState === "error"} class:ok={probeState === "idle" && !!probeMessage}>{probeMessage}</span>
    </div>

    {#if probeResult}
      <div class="preview-cards probe-grid">
        <div class="metric">
          <span>selectedRevisionId</span>
          <strong>{probeResult.selectedRevisionId || "—"}</strong>
        </div>
        <div class="metric">
          <span>selectorPath</span>
          <strong>{probeResult.selectorPath || "—"}</strong>
        </div>
        <div class="metric">
          <span>rolloutBucket</span>
          <strong>{probeResult.rolloutBucket ?? "—"}</strong>
        </div>
        <div class="metric">
          <span>selectorProfile</span>
          <strong>{probeResult.selectorProfile || "—"}</strong>
        </div>
        <div class="metric">
          <span>selectorVersion</span>
          <strong>{probeResult.selectorVersion ?? "—"}</strong>
        </div>
        <div class="metric">
          <span>extractionMethod</span>
          <strong>{probeResult.extractionMethod || "—"}</strong>
        </div>
        <div class="metric">
          <span>extractedPrice</span>
          <strong>{probeResult.extractedPrice ?? "—"}</strong>
        </div>
        <div class="metric">
          <span>offerId</span>
          <strong>{probeResult.offerId || "—"}</strong>
        </div>
      </div>
    {/if}
  </section>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: "IBM Plex Sans", "Avenir Next", "Segoe UI", sans-serif;
    background:
      radial-gradient(circle at top left, rgba(255, 211, 97, 0.22), transparent 28%),
      radial-gradient(circle at bottom right, rgba(52, 211, 153, 0.18), transparent 30%),
      linear-gradient(180deg, #f4efe4 0%, #efe8db 100%);
    color: #1a1815;
  }

  .shell {
    max-width: 1320px;
    margin: 0 auto;
    padding: 40px 20px 56px;
  }

  .hero {
    margin-bottom: 24px;
  }

  .eyebrow {
    margin: 0 0 8px;
    font-size: 12px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #7c5b18;
  }

  h1 {
    margin: 0;
    font-size: clamp(2.2rem, 4vw, 4.5rem);
    line-height: 0.95;
    letter-spacing: -0.04em;
  }

  .lede {
    max-width: 780px;
    margin-top: 12px;
    font-size: 1rem;
    line-height: 1.7;
    color: #4b4439;
  }

  .grid {
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 20px;
  }

  .merchant-list {
    margin-top: 20px;
  }

  .panel {
    border: 1px solid rgba(72, 56, 24, 0.12);
    border-radius: 24px;
    background: rgba(255, 252, 247, 0.88);
    backdrop-filter: blur(12px);
    box-shadow: 0 18px 60px rgba(46, 31, 7, 0.08);
    padding: 20px;
  }

  .accent {
    background: linear-gradient(180deg, rgba(247, 255, 249, 0.94), rgba(245, 251, 255, 0.94));
  }

  .panel-head {
    display: flex;
    justify-content: space-between;
    align-items: start;
    gap: 16px;
    margin-bottom: 18px;
  }

  .panel-head h2,
  .panel-head p {
    margin: 0;
  }

  .panel-head p {
    font-size: 0.92rem;
    color: #5f5a52;
  }

  .field-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .full {
    grid-column: 1 / -1;
  }

  label {
    display: grid;
    gap: 6px;
  }

  label span {
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #675f52;
  }

  input,
  textarea,
  button {
    font: inherit;
  }

  input,
  textarea {
    width: 100%;
    border: 1px solid rgba(77, 63, 35, 0.18);
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.76);
    padding: 12px 14px;
    color: #17130f;
    box-sizing: border-box;
  }

  textarea {
    resize: vertical;
    min-height: 220px;
    font-family: "IBM Plex Mono", "SFMono-Regular", monospace;
    line-height: 1.5;
  }

  .stack {
    margin-top: 16px;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-top: 18px;
    flex-wrap: wrap;
  }

  button {
    border: 0;
    border-radius: 999px;
    padding: 12px 18px;
    cursor: pointer;
  }

  .primary {
    background: linear-gradient(135deg, #14532d, #0f766e);
    color: #f8fffb;
  }

  .ghost {
    background: rgba(255, 244, 210, 0.92);
    color: #6f5315;
  }

  .ok {
    color: #166534;
  }

  .error {
    color: #b91c1c;
  }

  .preview-cards {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 16px;
  }

  .probe-grid {
    margin-top: 16px;
  }

  .metric {
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.74);
    border: 1px solid rgba(56, 109, 83, 0.14);
    padding: 14px;
  }

  .metric span {
    display: block;
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6d6a62;
    margin-bottom: 6px;
  }

  .metric strong {
    display: block;
    word-break: break-word;
  }

  .tips {
    margin-top: 14px;
    font-size: 0.92rem;
    color: #5f5a52;
  }

  .tips p {
    margin: 0 0 6px;
  }

  .searchbar {
    display: flex;
    gap: 10px;
    align-items: center;
    width: min(460px, 100%);
  }

  .merchant-table {
    display: grid;
    gap: 10px;
    margin-top: 12px;
  }

  .merchant-row {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    text-align: left;
    width: 100%;
    border-radius: 18px;
    border: 1px solid rgba(77, 63, 35, 0.14);
    background: rgba(255, 255, 255, 0.76);
    padding: 14px 16px;
  }

  .revision-row {
    align-items: center;
  }

  .revision-actions {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .active-revision {
    outline: 2px solid rgba(16, 185, 129, 0.35);
  }

  .merchant-row div {
    display: grid;
    gap: 4px;
  }

  .merchant-row strong {
    font-size: 1rem;
  }

  .merchant-row span {
    color: #655f56;
    font-size: 0.9rem;
  }

  @media (max-width: 960px) {
    .grid {
      grid-template-columns: 1fr;
    }

    .field-grid,
    .preview-cards {
      grid-template-columns: 1fr;
    }

    .searchbar,
    .merchant-row {
      width: 100%;
    }

    .merchant-row {
      flex-direction: column;
    }

    .revision-actions {
      justify-content: flex-start;
    }
  }
</style>
