<script lang="ts">
	import { browser } from '$app/environment';
	import type { Snippet } from 'svelte';

	interface Label { val: string; }
	interface Props { labels?: Label[]; children?: Snippet; class?: string; }

	const WARN_LABELS = new Set(['nsfw', 'nudity', 'porn', 'sexual', 'gore', 'graphic-media', 'spoiler', '!warn']);
	const HIDE_LABELS = new Set(['!hide']);
	const ADULT_LABELS = new Set(['nsfw', 'nudity', 'porn', 'sexual']);

	const LABEL_TEXT: Record<string, string> = {
		nsfw: 'センシティブな内容', nudity: 'ヌード', porn: 'アダルトコンテンツ',
		sexual: '性的コンテンツ', gore: '暴力的コンテンツ', 'graphic-media': '過激な映像',
		spoiler: 'ネタバレ', '!warn': 'コンテンツ警告', '!hide': '非表示コンテンツ',
	};

	const CONSENT_KEY = 'yoro-adult-content-consent';
	const CONSENT_VERSION = '1.0';

	/** Check localStorage for prior adult content consent. */
	function hasAdultConsent(): boolean {
		if (!browser) return false;
		try {
			const raw = localStorage.getItem(CONSENT_KEY);
			if (!raw) return false;
			const data = JSON.parse(raw);
			return data.version === CONSENT_VERSION && data.agreed === true;
		} catch { return false; }
	}

	function saveAdultConsent(): void {
		if (!browser) return;
		localStorage.setItem(CONSENT_KEY, JSON.stringify({
			version: CONSENT_VERSION,
			agreed: true,
			timestamp: new Date().toISOString(),
		}));
	}

	let { labels = [], children, class: className = '' }: Props = $props();
	let revealed = $state(false);
	let step = $state<'initial' | 'terms' | 'confirm'>(hasAdultConsent() ? 'confirm' : 'initial');
	let globalConsented = $state(hasAdultConsent());

	const warnLabel = $derived(labels?.find(l => WARN_LABELS.has(l.val) || HIDE_LABELS.has(l.val)));
	const isHidden = $derived(labels?.some(l => HIDE_LABELS.has(l.val)) ?? false);
	const isAdult = $derived(labels?.some(l => ADULT_LABELS.has(l.val)) ?? false);
	const shouldWarn = $derived(!!warnLabel && !(revealed || (isAdult && globalConsented)));
	const labelText = $derived(warnLabel ? (LABEL_TEXT[warnLabel.val] || warnLabel.val) : '');

	function handleAgree() {
		saveAdultConsent();
		globalConsented = true;
		revealed = true;
	}
</script>

{#if shouldWarn}
	<div class="relative overflow-hidden rounded-xl {className}">
		{#if isAdult}
			<div class="flex flex-col items-center justify-center rounded-xl border border-gv2-border/20 bg-gv2-bg-card px-5 py-8">

				{#if step === 'initial'}
					<!-- Step 1: Warning -->
					<div class="flex h-12 w-12 items-center justify-center rounded-full bg-amber-500/10">
						<svg class="h-6 w-6 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
						</svg>
					</div>
					<p class="mt-3 text-[15px] font-bold text-gv2-text-primary">{labelText}</p>
					<p class="mt-1.5 text-center text-[13px] leading-snug text-gv2-text-muted">
						このコンテンツには成人向けの表現が含まれています。<br/>
						閲覧するには年齢確認への同意が必要です。
					</p>
					{#if !isHidden}
						<button
							type="button"
							class="mt-4 rounded-full bg-gv2-text-primary px-6 py-2 text-[14px] font-bold text-gv2-bg-primary touch-manipulation active:opacity-80"
							onclick={(e) => { e.stopPropagation(); step = 'terms'; }}
						>
							年齢確認へ進む
						</button>
					{/if}

				{:else if step === 'terms'}
					<!-- Step 2: Terms & Conditions -->
					<div class="w-full max-w-sm">
						<h3 class="text-[15px] font-bold text-gv2-text-primary text-center">成人向けコンテンツ閲覧同意</h3>
						<div class="mt-3 max-h-[240px] overflow-y-auto rounded-lg border border-gv2-border/20 bg-gv2-bg-primary/50 p-3 text-[12px] leading-relaxed text-gv2-text-muted">
							<p class="font-semibold text-gv2-text-primary">第1条（目的）</p>
							<p class="mt-1">本同意は、yoro.etzhayyim.com（以下「本サービス」）上の成人向けコンテンツ（NSFW、ヌード、性的表現を含むコンテンツ）の閲覧に関する利用者の同意を取得するものです。</p>

							<p class="mt-2 font-semibold text-gv2-text-primary">第2条（年齢要件）</p>
							<p class="mt-1">利用者は、以下の全てに該当することを確認します。</p>
							<ul class="mt-1 list-disc pl-4 space-y-0.5">
								<li>満18歳以上であること</li>
								<li>居住する国・地域の法令において成人向けコンテンツの閲覧が許可される年齢に達していること</li>
								<li>成人向けコンテンツの閲覧が法律で禁止されていない地域からアクセスしていること</li>
							</ul>

							<p class="mt-2 font-semibold text-gv2-text-primary">第3条（コンテンツの性質）</p>
							<p class="mt-1">成人向けコンテンツには、性的表現、ヌード、その他センシティブな表現が含まれます。これらのコンテンツは AI によって生成されたものを含み、実在の人物とは関係ありません。</p>

							<p class="mt-2 font-semibold text-gv2-text-primary">第4条（利用者の責任）</p>
							<ul class="mt-1 list-disc pl-4 space-y-0.5">
								<li>未成年者がアクセスできない環境で閲覧すること</li>
								<li>コンテンツの無断転載・再配布を行わないこと</li>
								<li>虚偽の年齢申告により生じた問題は利用者の責任とすること</li>
							</ul>

							<p class="mt-2 font-semibold text-gv2-text-primary">第5条（同意の記録）</p>
							<p class="mt-1">同意情報はブラウザの localStorage に保存され、同一デバイスでの再確認を省略します。同意はブラウザデータの消去により取消できます。</p>

							<p class="mt-2 font-semibold text-gv2-text-primary">第6条（準拠法）</p>
							<p class="mt-1">本同意は日本法に準拠し、東京地方裁判所を第一審の専属的合意管轄裁判所とします。</p>

							<p class="mt-2 text-[11px] text-gv2-text-muted/60">運営: etzhayyim.com — 施行日: 2026年3月28日 — Version {CONSENT_VERSION}</p>
						</div>
						<div class="mt-4 flex items-center justify-center gap-3">
							<button
								type="button"
								class="rounded-full border border-gv2-border px-5 py-2 text-[13px] font-semibold text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
								onclick={(e) => { e.stopPropagation(); step = 'initial'; }}
							>
								Back
							</button>
							<button
								type="button"
								class="rounded-full bg-amber-500 px-5 py-2 text-[13px] font-bold text-white touch-manipulation active:opacity-80"
								onclick={(e) => { e.stopPropagation(); step = 'confirm'; }}
							>
								I agree to the above
							</button>
						</div>
					</div>

				{:else if step === 'confirm'}
					<!-- Step 3: Final confirmation -->
					<div class="flex h-10 w-10 items-center justify-center rounded-full bg-red-500/10">
						<svg class="h-5 w-5 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
							<path d="M12 9v4" /><path d="M12 17h.01" />
							<path d="M3.6 15.4 10.3 4.2a2 2 0 0 1 3.4 0l6.7 11.2A2 2 0 0 1 18.7 18H5.3a2 2 0 0 1-1.7-2.6z" />
						</svg>
					</div>
					<p class="mt-2 text-[14px] font-bold text-gv2-text-primary">最終確認</p>
					<p class="mt-1 text-center text-[13px] text-gv2-text-muted">
						私は18歳以上であり、成人向けコンテンツの<br/>閲覧同意に合意します。
					</p>
					<div class="mt-4 flex items-center justify-center gap-3">
						<button
							type="button"
							class="rounded-full border border-gv2-border px-5 py-2 text-[13px] font-semibold text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
							onclick={(e) => { e.stopPropagation(); step = 'initial'; }}
						>
							キャンセル
						</button>
						<button
							type="button"
							class="rounded-full bg-red-500 px-5 py-2 text-[13px] font-bold text-white touch-manipulation active:opacity-80"
							onclick={(e) => { e.stopPropagation(); handleAgree(); }}
						>
							同意して表示する
						</button>
					</div>
				{/if}

			</div>
		{:else}
			<!-- Standard content warning -->
			<div class="flex flex-col items-center justify-center gap-2 rounded-xl border border-gv2-border/20 bg-gv2-bg-card py-8 px-4">
				<svg class="h-7 w-7 text-gv2-text-muted/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
					<line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
				</svg>
				<p class="text-[14px] font-semibold text-gv2-text-muted">{labelText}</p>
				{#if !isHidden}
					<button
						type="button"
						class="mt-1 rounded-full border border-gv2-border px-4 py-1.5 text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
						onclick={(e) => { e.stopPropagation(); revealed = true; }}
					>
						表示する
					</button>
				{/if}
			</div>
		{/if}
	</div>
{:else}
	{#if children}
		{@render children()}
	{/if}
{/if}
