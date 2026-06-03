<script lang="ts">
  let mobileOpen = $state(false);
  let selectedRobot = $state<'otete' | 'hitogata' | 'caterpillar'>('otete');
  let careLevel    = $state(3);
  let housingCost  = $state(1_500_000);

  const robotTabs = [
    { id: 'otete',       label: 'Otete',       emoji: '🦾', model: 'arm',         desc: '物品搬送・服薬管理・見守り巡回' },
    { id: 'hitogata',    label: 'Hitogata',    emoji: '🤖', model: 'hitogata',    desc: 'リハビリ補助・コミュニケーション' },
    { id: 'caterpillar', label: 'Caterpillar', emoji: '🚜', model: 'caterpillar', desc: '自律巡回・転倒検知・緊急通報' },
  ] as const;

  const robotDetails: Record<string, { h3: string; tag: string; items: string[] }> = {
    otete: {
      h3: 'Giemon Otete — 在宅 ADL 支援',
      tag: '初代製品 / 発売中',
      items: [
        '服薬ボックス・ペットボトルの搬送（可搬 500g）',
        '棚・床面への低姿勢アクセス（クローラー走行）',
        '部屋間の定期見守り巡回 + カメラ映像',
        'スマートフォン遠隔操作 + ROS2 自律制御',
        '転倒物検知 + 家族への通知',
        'ICS3.5 バスサーボ・全国産部品',
      ],
    },
    hitogata: {
      h3: 'Giemon Hitogata — リハビリ・交流',
      tag: '次期製品予告',
      items: [
        '17 軸全身動作によるリハビリ動作誘導',
        '毎日のバイタル確認 + 認知機能トレーニング',
        'Murakumo AI による会話・孤独感ケア',
        '運動機能評価（立ち上がり / 歩行ステップ）',
        '目標設定 + ガンバリ記録（Well-Becoming 5 軸）',
        'ケアマネジャーへの活動レポート自動送信',
      ],
    },
    caterpillar: {
      h3: 'Giemon Caterpillar — 自律見守り UGV',
      tag: '次期製品予告',
      items: [
        'LiDAR + ステレオカメラによる自律 SLAM 巡回',
        '転倒・異常姿勢を AI で検知 → 緊急通報',
        '夜間 IR カメラ / 音声インターフォン',
        '重装甲トラックで段差・玄関フロア対応',
        'Nav2 ルート指定 + 手動遠隔操作切替',
        '1 充電 8 時間連続巡回',
      ],
    },
  };

  const housingItems = [
    { icon: '🪜', title: '手すり設置',     desc: '廊下・トイレ・浴室・階段。転倒予防の基本。',       cost: '5〜15 万円' },
    { icon: '📐', title: '段差解消',       desc: '玄関・居室・浴室の段差をスロープ・埋め戻しで解消。', cost: '3〜20 万円' },
    { icon: '🚿', title: '浴室改修',       desc: 'すべり止め・折りたたみシャワーチェア・ドア改修。',   cost: '10〜50 万円' },
    { icon: '🚽', title: 'トイレ改修',     desc: '洋式化・自動開閉蓋・自立支援手すり。',             cost: '8〜30 万円' },
    { icon: '🚪', title: '引き戸改修',     desc: '開き戸 → 引き戸。車椅子・歩行器対応。',           cost: '6〜25 万円' },
    { icon: '🛗', title: '昇降機・スロープ', desc: '屋内外の段差に階段昇降機・スロープを設置。',        cost: '30〜100 万円' },
  ];

  const careSteps = [
    { step: '1', title: '要介護認定申請',   desc: '市区町村の介護保険担当窓口に申請。主治医意見書 + 認定調査 → 約 1 ヶ月で結果。', icon: '📋' },
    { step: '2', title: '要介護度決定',     desc: '要支援 1〜2 / 要介護 1〜5 の 7 段階。AI が認定結果を読み取りプランを提案。', icon: '📊' },
    { step: '3', title: 'ケアプラン作成',   desc: 'ケアマネジャーと相談。居宅サービス計画書を作成。Hitogata が活動ログを自動記録。', icon: '📝' },
    { step: '4', title: 'サービス開始',     desc: '訪問介護・通所介護・短期入所等のサービスを開始。ロボットがサービス間をつなぐ。', icon: '🤝' },
    { step: '5', title: 'モニタリング',     desc: 'ロボットのセンサーデータをケアマネに提供。状態変化を早期把握。', icon: '📡' },
    { step: '6', title: 'ケアプラン更新',   desc: '6 ヶ月ごとの見直し。AI がロボットの活動ログから要介護度変化を予測。', icon: '🔄' },
  ];

  const careLimits: Record<number, number> = { 1: 50_320, 2: 105_310, 3: 167_650, 4: 197_050, 5: 270_480 };

  const benefitCalc = $derived.by(() => {
    const limit = 200_000;
    const copayRatio = careLevel >= 3 ? 0.1 : 0.2;
    const covered = Math.min(housingCost, limit);
    const benefit = Math.round(covered * (1 - copayRatio));
    return { covered, benefit, copay: covered - benefit, selfPay: housingCost - covered };
  });

  const wellBeingAxes = [
    { axis: 'Engagement',   ja: '参加',   desc: 'ケア交換・サークル参加・外出',     },
    { axis: 'Competence',   ja: '能力',   desc: 'できること・教えられること',       },
    { axis: 'Contribution', ja: '貢献',   desc: '時間銀行・知恵アーカイブ',         },
    { axis: 'Growth',       ja: '成長',   desc: '新スキル習得・目標達成率',         },
    { axis: 'Resilience',   ja: '回復力', desc: 'バイタル安定性・サポートバッファ', },
  ];

  const plans = [
    {
      name: 'Basic',
      price: '¥9,800',
      priceNote: '月額・税込',
      features: ['介護保険費用シミュレーター', '施設・事業所マッチング', '住宅改修費給付 試算ツール', 'AI チャット（月 30 回）', 'ケアサークル参加（無料枠）'],
      cta: '無料で試す',
      ctaHref: '/signup',
      highlight: false,
    },
    {
      name: 'Robot Pro',
      price: '¥29,800',
      priceNote: '月額・税込',
      features: ['Basic の全機能', 'Giemon Otete 遠隔監視ダッシュボード', 'Hitogata バイタル連携 + AI 会話', 'Caterpillar 異常通知 + 巡回ログ', 'ケアマネジャー共有レポート', '24h 緊急サポートライン'],
      cta: '14 日間無料トライアル',
      ctaHref: '/signup?plan=pro',
      highlight: true,
    },
    {
      name: 'Facility',
      price: '要相談',
      priceNote: '施設・病院向け',
      features: ['ロボット複数台一括管理', 'EHR / カルテ連携 API', '入居者別 Well-Being ダッシュボード', 'スタッフ向けロボット操作研修', 'SLA 99.9% / 専任 CSM', '補助金申請支援'],
      cta: '無料相談を申し込む',
      ctaHref: 'mailto:kaigo@etzhayyim.com',
      highlight: false,
    },
  ];
</script>

<svelte:head>
  <title>Giemon Kaigo — ロボットが支える在宅介護・住宅改修・介護保険ナビ</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet" />
  <script type="application/ld+json">
    {JSON.stringify({
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": "Giemon Kaigo",
      "description": "Giemon ロボットを活用した在宅介護支援プラットフォーム。住宅改修・介護保険ナビ・Well-Becoming AI。",
      "applicationCategory": "HealthApplication",
      "operatingSystem": "Web",
      "brand": { "@type": "Brand", "name": "Giemon" }
    })}
  </script>
</svelte:head>

<!-- ─── Skip link ─── -->
<a href="#main" class="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-[#0017c1] focus:text-white focus:rounded">
  本文へスキップ
</a>

<!-- ─── グローバルヘッダー (DADS準拠) ─── -->
<header class="bg-white border-b border-[#e6e6e6] sticky top-0 z-50" role="banner">
  <!-- ユーティリティバー -->
  <div class="bg-[#f9f9f9] border-b border-[#e6e6e6]">
    <div class="max-w-6xl mx-auto px-4 h-8 flex items-center justify-between text-[11px] text-[#616161]">
      <span>Giemon Kaigo — 在宅介護ロボットプラットフォーム</span>
      <span>お問い合わせ: <a href="mailto:kaigo@etzhayyim.com" class="text-[#0017c1]">kaigo@etzhayyim.com</a></span>
    </div>
  </div>
  <!-- メインナビ -->
  <div class="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
    <a href="/" class="flex items-center gap-2 font-bold text-[#1a1a1a] text-[15px] no-underline hover:no-underline">
      <span class="text-xl" aria-hidden="true">🏠</span>
      <span>Giemon <span class="text-[#0017c1]">Kaigo</span></span>
    </a>
    <nav class="hidden md:flex items-center gap-1 text-[13px]" aria-label="サイトナビゲーション">
      {#each [['ロボット','#robots'],['住宅改修','#housing'],['介護保険','#insurance'],['ケアサークル','#circle'],['料金','#pricing']] as [l,h]}
        <a href={h} class="px-3 py-2 text-[#1a1a1a] rounded hover:bg-[#f2f2f2] no-underline hover:no-underline transition-colors">{l}</a>
      {/each}
      <a href="/signup"
         class="ml-2 px-4 py-2 bg-[#0017c1] hover:bg-[#0836a3] text-white font-medium rounded text-[13px] no-underline hover:no-underline transition-colors">
        無料で始める
      </a>
    </nav>
    <button
      class="md:hidden p-2 text-[#1a1a1a] hover:bg-[#f2f2f2] rounded border border-[#e6e6e6]"
      onclick={() => (mobileOpen = !mobileOpen)}
      aria-expanded={mobileOpen}
      aria-controls="mobile-nav"
      aria-label="メニューを開く"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
        {#if mobileOpen}
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        {:else}
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        {/if}
      </svg>
    </button>
  </div>
  {#if mobileOpen}
    <nav id="mobile-nav" class="md:hidden bg-white border-t border-[#e6e6e6] px-4 py-2" aria-label="モバイルナビゲーション">
      {#each [['ロボット','#robots'],['住宅改修','#housing'],['介護保険','#insurance'],['ケアサークル','#circle'],['料金','#pricing']] as [l,h]}
        <a href={h} class="block px-3 py-3 text-[#1a1a1a] text-sm border-b border-[#f2f2f2] no-underline hover:bg-[#f9f9f9]"
           onclick={() => (mobileOpen = false)}>{l}</a>
      {/each}
      <a href="/signup" class="block mt-3 mb-2 px-4 py-2.5 bg-[#0017c1] text-white text-sm font-medium rounded text-center no-underline"
         onclick={() => (mobileOpen = false)}>無料で始める</a>
    </nav>
  {/if}
</header>

<main id="main">

<!-- ─── ① ヒーロー ─── -->
<section class="bg-[#f9f9f9] border-b border-[#e6e6e6] py-16 px-4">
  <div class="max-w-5xl mx-auto">
    <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#e8f1fe] text-[#0017c1] text-[11px] font-medium mb-6">
      🇯🇵 Giemon ロボット応用 — 介護・住宅・Well-Being
    </div>
    <div class="grid md:grid-cols-2 gap-12 items-center">
      <div>
        <h1 class="text-[clamp(1.8rem,4vw,2.8rem)] font-bold text-[#1a1a1a] leading-tight mb-4">
          家で、もっと長く。<br />
          <span class="text-[#0017c1]">ロボットと一緒に。</span>
        </h1>
        <p class="text-[#464646] text-base leading-relaxed mb-6">
          Giemon ロボット（Otete・Hitogata・Caterpillar）× 介護保険ナビ × 住宅改修支援。<br />
          「できないこと」を測る欠損モデルではなく、<strong>「できること・なりたいこと」を育てる</strong> Well-Becoming モデル。
        </p>
        <div class="flex flex-wrap gap-3">
          <a href="/signup"
             class="px-6 py-3 bg-[#0017c1] hover:bg-[#0836a3] text-white font-medium rounded text-[15px] no-underline hover:no-underline transition-colors shadow-sm">
            無料で試す
          </a>
          <a href="#robots"
             class="px-6 py-3 border border-[#b2b2b2] hover:border-[#616161] text-[#1a1a1a] font-medium rounded text-[15px] no-underline hover:no-underline transition-colors">
            ロボットを見る →
          </a>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-4">
        {#each [
          ['3機種', 'ロボット対応', '🤖'],
          ['20万円', '住宅改修費上限', '🏠'],
          ['7段階', '介護度対応', '📋'],
          ['5軸', 'Well-Being 成長', '⭐'],
        ] as [v,l,icon]}
          <div class="bg-white border border-[#e6e6e6] rounded-lg px-5 py-5 text-center shadow-sm">
            <div class="text-2xl mb-2" aria-hidden="true">{icon}</div>
            <div class="text-[1.5rem] font-bold text-[#0017c1] leading-none">{v}</div>
            <div class="text-[11px] text-[#616161] mt-1">{l}</div>
          </div>
        {/each}
      </div>
    </div>
  </div>
</section>

<!-- ─── ② ロボットラインナップ ─── -->
<section class="py-16 px-4 bg-white" id="robots">
  <div class="max-w-5xl mx-auto">
    <div class="mb-2 text-[11px] font-medium text-[#0017c1] uppercase tracking-wider">Robot Lineup</div>
    <h2 class="text-[1.5rem] font-bold text-[#1a1a1a] mb-2">Giemon 介護ロボット 3 機種</h2>
    <p class="text-[#616161] text-sm mb-8">3D モデルで実物のサイズ感を確認できます</p>

    <!-- タブ -->
    <div class="flex gap-2 mb-6 flex-wrap border-b border-[#e6e6e6] pb-0" role="tablist" aria-label="ロボット選択">
      {#each robotTabs as tab}
        <button
          role="tab"
          aria-selected={selectedRobot === tab.id}
          onclick={() => (selectedRobot = tab.id)}
          class={[
            'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px',
            selectedRobot === tab.id
              ? 'border-[#0017c1] text-[#0017c1]'
              : 'border-transparent text-[#616161] hover:text-[#1a1a1a] hover:border-[#b2b2b2]'
          ].join(' ')}
        >
          <span aria-hidden="true">{tab.emoji}</span> {tab.label}
          <span class="ml-1.5 text-[10px] opacity-70 hidden sm:inline">{tab.desc}</span>
        </button>
      {/each}
    </div>

    <div class="grid md:grid-cols-2 gap-8 items-start" role="tabpanel">
      <!-- 3D ビューア -->
      <div class="relative bg-[#f2f2f2] border border-[#e6e6e6] rounded-lg overflow-hidden" style="aspect-ratio:16/10">
        <iframe
          src={`https://giemon.etzhayyim.com/viewer.htm?model=${robotTabs.find(t => t.id === selectedRobot)?.model}`}
          title={`Giemon ${selectedRobot} 3D ビューア`}
          class="absolute inset-0 w-full h-full border-0"
          loading="lazy"
          allow="accelerometer"
        ></iframe>
        <div class="absolute bottom-2 right-2 text-[9px] text-[#949494] pointer-events-none select-none bg-white/80 px-1.5 py-0.5 rounded">WebGPU / WebGL2</div>
      </div>
      <!-- 説明 -->
      <div>
        <div class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#e8f1fe] text-[#0017c1] text-[11px] font-medium mb-3">
          {robotDetails[selectedRobot].tag}
        </div>
        <h3 class="text-[1.1rem] font-bold text-[#1a1a1a] mb-4">{robotDetails[selectedRobot].h3}</h3>
        <ul class="space-y-2.5">
          {#each robotDetails[selectedRobot].items as item}
            <li class="flex items-start gap-2 text-[#464646] text-sm">
              <span class="text-[#259d63] mt-0.5 shrink-0 font-bold" aria-hidden="true">✓</span>
              {item}
            </li>
          {/each}
        </ul>
        <a href="https://giemon.etzhayyim.com" target="_blank" rel="noopener"
           class="mt-5 inline-flex items-center gap-1 text-[#0017c1] text-sm font-medium">
          Giemon 製品ページへ →
        </a>
      </div>
    </div>
  </div>
</section>

<!-- ─── ③ 住宅改修支援 ─── -->
<section class="py-16 px-4 bg-[#f9f9f9] border-t border-[#e6e6e6]" id="housing">
  <div class="max-w-5xl mx-auto">
    <div class="mb-2 text-[11px] font-medium text-[#0017c1] uppercase tracking-wider">Housing Reform</div>
    <h2 class="text-[1.5rem] font-bold text-[#1a1a1a] mb-2">住宅改修支援 + 給付金 AI 試算</h2>
    <p class="text-[#616161] text-sm max-w-xl mb-10">
      介護保険「住宅改修費」は要支援・要介護認定者に最大
      <strong class="text-[#1a1a1a]">20 万円</strong>が支給されます。
      Giemon Kaigo が対象工事・給付額・施工業者を一括サポート。
    </p>

    <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-12">
      {#each housingItems as item}
        <div class="bg-white border border-[#e6e6e6] rounded-lg px-5 py-4 hover:border-[#0017c1] transition-colors">
          <div class="text-2xl mb-2" aria-hidden="true">{item.icon}</div>
          <h3 class="text-[#1a1a1a] font-semibold text-sm mb-1">{item.title}</h3>
          <p class="text-[#616161] text-xs leading-relaxed mb-2">{item.desc}</p>
          <p class="text-[#0017c1] text-xs font-medium">目安: {item.cost}</p>
        </div>
      {/each}
    </div>

    <!-- 給付額試算 -->
    <div class="bg-white border border-[#e6e6e6] rounded-lg p-6 max-w-2xl">
      <h3 class="text-[#1a1a1a] font-bold text-base mb-5">住宅改修費 給付額 簡易試算</h3>
      <div class="grid sm:grid-cols-2 gap-6 mb-5">
        <fieldset class="border-0 p-0 m-0">
          <legend class="text-[#616161] text-xs mb-2">要介護度を選択</legend>
          <div class="flex gap-2 flex-wrap">
            {#each [1,2,3,4,5] as lv}
              <button
                onclick={() => (careLevel = lv)}
                aria-pressed={careLevel === lv}
                class={[
                  'w-10 h-10 rounded border text-sm font-medium transition-colors',
                  careLevel === lv
                    ? 'bg-[#0017c1] border-[#0017c1] text-white'
                    : 'bg-white border-[#b2b2b2] text-[#1a1a1a] hover:border-[#0017c1]'
                ].join(' ')}
              >{lv}</button>
            {/each}
          </div>
          <p class="text-[#616161] text-[10px] mt-2">自己負担割合: {careLevel >= 3 ? '1' : '2'} 割</p>
        </fieldset>
        <div>
          <label for="housing-cost" class="text-[#616161] text-xs block mb-2">工事費用: {housingCost.toLocaleString()} 円</label>
          <input
            id="housing-cost"
            type="range" min="50000" max="2000000" step="50000"
            bind:value={housingCost}
            class="w-full accent-[#0017c1]"
            aria-valuemin={50000} aria-valuemax={2000000} aria-valuenow={housingCost}
          />
          <div class="flex justify-between text-[10px] text-[#b2b2b2] mt-1">
            <span>5 万円</span><span>200 万円</span>
          </div>
        </div>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {#each [
          ['支給対象額', benefitCalc.covered.toLocaleString() + ' 円', '#0017c1'],
          ['支給額',     benefitCalc.benefit.toLocaleString() + ' 円', '#259d63'],
          ['自己負担（対象内）', benefitCalc.copay.toLocaleString() + ' 円', '#b78f00'],
          ['超過自己負担', benefitCalc.selfPay.toLocaleString() + ' 円', '#949494'],
        ] as [label, val, color]}
          <div class="bg-[#f9f9f9] border border-[#e6e6e6] rounded px-3 py-3 text-center">
            <p class="text-[10px] text-[#616161] mb-1">{label}</p>
            <p class="text-sm font-bold" style="color:{color}">{val}</p>
          </div>
        {/each}
      </div>
      <p class="mt-3 text-[10px] text-[#949494]">※ 概算値。実際の給付額は市区町村の審査により確定します。</p>
    </div>
  </div>
</section>

<!-- ─── ④ 介護保険ナビ ─── -->
<section class="py-16 px-4 bg-white border-t border-[#e6e6e6]" id="insurance">
  <div class="max-w-5xl mx-auto">
    <div class="mb-2 text-[11px] font-medium text-[#0017c1] uppercase tracking-wider">Care Insurance Navigator</div>
    <h2 class="text-[1.5rem] font-bold text-[#1a1a1a] mb-2">介護保険制度 ナビ</h2>
    <p class="text-[#616161] text-sm max-w-lg mb-10">
      複雑な介護保険の手続きを AI がステップごとに案内。
      認定申請からサービス事業所マッチングまでサポートします。
    </p>

    <ol class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-12" aria-label="介護保険手続きの流れ">
      {#each careSteps as s}
        <li class="bg-[#f9f9f9] border border-[#e6e6e6] rounded-lg px-5 py-4 list-none">
          <div class="flex items-center gap-2 mb-2">
            <span class="w-6 h-6 rounded-full bg-[#0017c1] text-white text-[11px] font-bold flex items-center justify-center shrink-0"
                  aria-label={`ステップ ${s.step}`}>{s.step}</span>
            <span class="text-[#1a1a1a] font-semibold text-sm">{s.title}</span>
          </div>
          <p class="text-[#616161] text-xs leading-relaxed">{s.desc}</p>
        </li>
      {/each}
    </ol>

    <!-- 支給限度額早見表 -->
    <div class="bg-[#f9f9f9] border border-[#e6e6e6] rounded-lg p-6 max-w-2xl">
      <h3 class="text-[#1a1a1a] font-bold text-base mb-4">月額支給限度額 早見表（1 割負担）</h3>
      <div class="space-y-3" role="list" aria-label="要介護度別支給限度額">
        {#each Object.entries(careLimits) as [lv, limit]}
          <div class="flex items-center gap-3" role="listitem">
            <span class="text-xs text-[#616161] w-14 shrink-0">要介護 {lv}</span>
            <div class="flex-1 bg-[#e6e6e6] rounded-full h-2 overflow-hidden" role="progressbar"
                 aria-valuenow={limit} aria-valuemin={0} aria-valuemax={270480}>
              <div class="h-full bg-[#0017c1] rounded-full transition-all"
                   style="width:{(limit / 270_480) * 100}%"></div>
            </div>
            <span class="text-xs text-[#1a1a1a] font-semibold w-28 text-right shrink-0">{limit.toLocaleString()} 円/月</span>
          </div>
        {/each}
      </div>
      <p class="mt-3 text-[10px] text-[#949494]">※ 2024 年度介護報酬改定後の値。2・3 割負担の方は所得に応じて異なります。</p>
    </div>
  </div>
</section>

<!-- ─── ⑤ Well-Becoming ─── -->
<section class="py-16 px-4 bg-[#f9f9f9] border-t border-[#e6e6e6]" id="circle">
  <div class="max-w-5xl mx-auto">
    <div class="mb-2 text-[11px] font-medium text-[#0017c1] uppercase tracking-wider">Well-Becoming</div>
    <h2 class="text-[1.5rem] font-bold text-[#1a1a1a] mb-3">欠損モデルから、能力成長モデルへ。</h2>
    <p class="text-[#616161] text-sm max-w-xl mb-10">
      公的介護は「できないこと」を測り給付する受動モデル。
      Giemon Kaigo は「できること・なりたいこと」を育てる <strong class="text-[#1a1a1a]">Well-Becoming</strong> モデルで動きます。
    </p>

    <div class="grid md:grid-cols-2 gap-10 items-start">
      <div>
        <h3 class="text-[#1a1a1a] font-semibold text-base mb-4">Well-Becoming 5 軸</h3>
        <dl class="space-y-3">
          {#each wellBeingAxes as ax}
            <div class="flex items-start gap-3 p-3 bg-white border border-[#e6e6e6] rounded-lg">
              <div class="w-1 self-stretch rounded-full bg-[#0017c1] shrink-0"></div>
              <div>
                <dt class="text-[#1a1a1a] text-sm font-semibold">
                  {ax.ja}
                  <span class="text-[#949494] text-[10px] ml-1.5 font-normal">{ax.axis}</span>
                </dt>
                <dd class="text-[#616161] text-xs mt-0.5">{ax.desc}</dd>
              </div>
            </div>
          {/each}
        </dl>
      </div>

      <div class="bg-white border border-[#e6e6e6] rounded-lg p-6">
        <h3 class="text-[#1a1a1a] font-semibold text-base mb-5">成長螺旋モデル</h3>
        <ol class="space-y-4 list-none p-0 m-0">
          {#each [
            ['能力発見', '「できること」マップを AI と一緒に作る', '🌱'],
            ['ケア交換', '近隣サークルで得意なことを提供・受取', '🤝'],
            ['信頼蓄積', '時間銀行に記録。実績が信頼に変わる', '⭐'],
            ['能力拡張', 'ロボット + AI で新しい活動に挑戦', '🚀'],
            ['豊かなケア', 'より質の高いケア交換が生まれる', '✨'],
          ] as [title, desc, icon], i}
            <li class="flex items-start gap-3">
              <div class="flex flex-col items-center shrink-0">
                <div class="w-8 h-8 rounded-full bg-[#e8f1fe] border border-[#9cbdfa] flex items-center justify-center text-sm"
                     aria-hidden="true">{icon}</div>
                {#if i < 4}
                  <div class="w-px h-4 bg-[#e6e6e6] mt-1"></div>
                {/if}
              </div>
              <div class="pt-1">
                <p class="text-[#1a1a1a] text-sm font-semibold">{title}</p>
                <p class="text-[#616161] text-xs mt-0.5">{desc}</p>
              </div>
            </li>
          {/each}
        </ol>

        <div class="mt-5 p-3 bg-[#f9f9f9] border border-[#e6e6e6] rounded text-xs text-[#616161] leading-relaxed">
          <strong class="text-[#0017c1]">ケアサークル</strong>
          は近隣 5〜8 人のインフォーマルな互助グループ。
          時間銀行（TimeBank）で非貨幣的なケア交換を記録します。
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ─── ⑥ 料金プラン ─── -->
<section class="py-16 px-4 bg-white border-t border-[#e6e6e6]" id="pricing">
  <div class="max-w-5xl mx-auto">
    <h2 class="text-[1.5rem] font-bold text-[#1a1a1a] mb-2">料金プラン</h2>
    <p class="text-[#616161] text-sm mb-10">全プラン 14 日間無料トライアルあり。クレジットカード不要。</p>
    <div class="grid md:grid-cols-3 gap-5">
      {#each plans as p}
        <div class={[
          'relative flex flex-col rounded-lg border p-6',
          p.highlight
            ? 'border-[#0017c1] bg-white shadow-md'
            : 'border-[#e6e6e6] bg-white'
        ].join(' ')}>
          {#if p.highlight}
            <div class="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-[#0017c1] text-white text-[11px] font-bold rounded-full whitespace-nowrap">
              おすすめ
            </div>
          {/if}
          <p class="text-[#616161] text-sm font-medium">{p.name}</p>
          <div class="mt-2 flex items-baseline gap-1">
            <span class="text-[1.75rem] font-bold text-[#1a1a1a] leading-none">{p.price}</span>
            <span class="text-[#949494] text-xs">{p.priceNote}</span>
          </div>
          <ul class="mt-5 space-y-2.5 flex-1" aria-label={`${p.name}プランの機能`}>
            {#each p.features as feat}
              <li class="flex items-start gap-2 text-[#464646] text-sm">
                <span class="text-[#259d63] shrink-0 mt-0.5 font-bold" aria-hidden="true">✓</span>{feat}
              </li>
            {/each}
          </ul>
          <a
            href={p.ctaHref}
            class={[
              'mt-6 block text-center py-2.5 rounded text-sm font-medium transition-colors no-underline hover:no-underline',
              p.highlight
                ? 'bg-[#0017c1] hover:bg-[#0836a3] text-white'
                : 'border border-[#b2b2b2] hover:border-[#0017c1] text-[#0017c1]'
            ].join(' ')}
          >{p.cta}</a>
        </div>
      {/each}
    </div>
    <p class="mt-6 text-[#949494] text-xs text-center">
      介護保険適用事業者・医療機関向けプランは別途ご相談ください。
    </p>
  </div>
</section>

<!-- ─── ⑦ FAQ ─── -->
<section class="py-16 px-4 bg-[#f9f9f9] border-t border-[#e6e6e6]">
  <div class="max-w-3xl mx-auto">
    <h2 class="text-[1.3rem] font-bold text-[#1a1a1a] mb-8">よくある質問</h2>
    <div class="space-y-2">
      {#each [
        ['ロボットを持っていなくても使えますか？','はい。介護保険ナビ・住宅改修試算・施設マッチング・ケアサークル機能は Basic プランでロボットなしでご利用いただけます。'],
        ['Giemon Otete を在宅介護に使うには何が必要ですか？','インターネット接続環境と、スマートフォンまたは PC があれば遠隔操作・見守りが可能です。Wi-Fi 設定は初期設定ガイドで案内します。'],
        ['介護保険の住宅改修費給付を受けるには？','要支援 1 以上の認定を受けた後、ケアマネジャーと相談して改修計画書を作成します。Giemon Kaigo が申請書類の作成をサポートします。'],
        ['ケアサークルとはどのような仕組みですか？','近隣 5〜8 人が互いの得意なことを提供・受け取ります。「時間」を単位に記録し、AI が活動提案・マッチングを担います。'],
        ['施設・病院向けのカスタマイズは可能ですか？','Facility プランでは EHR / カルテシステム連携・複数ロボット管理・スタッフ研修を含む法人向けカスタマイズが可能です。'],
      ] as [q, a]}
        <details class="bg-white border border-[#e6e6e6] rounded-lg overflow-hidden group">
          <summary class="px-5 py-4 text-[#1a1a1a] text-sm font-medium cursor-pointer flex items-center justify-between list-none">
            {q}
            <svg class="w-4 h-4 text-[#0017c1] shrink-0 ml-3 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="m6 9 6 6 6-6" />
            </svg>
          </summary>
          <div class="px-5 pb-4 text-[#464646] text-sm leading-relaxed border-t border-[#f2f2f2]">{a}</div>
        </details>
      {/each}
    </div>
  </div>
</section>

</main>

<!-- ─── フッター (DADS準拠) ─── -->
<footer class="bg-[#1a1a1a] text-[#d2d2d2] py-12 px-4" role="contentinfo">
  <div class="max-w-5xl mx-auto grid sm:grid-cols-3 gap-8 text-sm">
    <div>
      <p class="text-white font-bold mb-3 flex items-center gap-2">
        <span aria-hidden="true">🏠</span>Giemon Kaigo
      </p>
      <p class="text-[#949494] text-xs leading-relaxed">
        ロボットが支える在宅介護プラットフォーム。<br />
        住宅改修・介護保険ナビ・Well-Becoming AI。<br />
        開発元: etzhayyim Japan株式会社 / amanomibashira
      </p>
      <p class="mt-3 text-[10px] text-[#616161]">
        Powered by <a href="https://giemon.etzhayyim.com" class="text-[#6ea0f7]">Giemon ロボット</a>
      </p>
    </div>
    <div>
      <p class="text-white font-semibold text-sm mb-3">サービス</p>
      <ul class="space-y-1.5 text-xs">
        {#each [['ロボット紹介','#robots'],['住宅改修支援','#housing'],['介護保険ナビ','#insurance'],['ケアサークル','#circle'],['料金プラン','#pricing'],['導入事例','/cases'],['施設向け相談','mailto:kaigo@etzhayyim.com']] as [l,h]}
          <li><a href={h} class="text-[#949494] hover:text-white no-underline hover:underline">{l}</a></li>
        {/each}
      </ul>
    </div>
    <div>
      <p class="text-white font-semibold text-sm mb-3">リンク</p>
      <ul class="space-y-1.5 text-xs">
        <li><a href="https://giemon.etzhayyim.com" target="_blank" rel="noopener" class="text-[#949494] hover:text-white no-underline hover:underline">Giemon 公式サイト</a></li>
        <li><a href="https://github.com/etzhayyim/otete" target="_blank" rel="noopener" class="text-[#949494] hover:text-white no-underline hover:underline">GitHub (オープンソース)</a></li>
        <li><a href="mailto:kaigo@etzhayyim.com" class="text-[#949494] hover:text-white no-underline hover:underline">お問い合わせ</a></li>
        <li><a href="/privacy" class="text-[#949494] hover:text-white no-underline hover:underline">プライバシーポリシー</a></li>
        <li><a href="/terms" class="text-[#949494] hover:text-white no-underline hover:underline">利用規約</a></li>
      </ul>
    </div>
  </div>
  <div class="max-w-5xl mx-auto mt-8 pt-6 border-t border-[#282828] flex flex-wrap gap-4 items-center justify-between text-[11px] text-[#616161]">
    <span>© 2026 amanomibashira. All rights reserved.</span>
    <span>本サービスは介護保険給付の申請を代行するものではありません。</span>
  </div>
</footer>
