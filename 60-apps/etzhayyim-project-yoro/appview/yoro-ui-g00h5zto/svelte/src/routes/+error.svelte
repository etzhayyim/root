<script lang="ts">
	import { page } from '$app/stores';
</script>

<div class="flex min-h-[60vh] flex-col items-center justify-center gap-4 p-8 text-center">
	<div class="text-[64px] font-black text-gv2-text-muted/20">{$page.status}</div>
	<h1 class="text-[22px] font-bold text-gv2-text-primary">
		{#if $page.status === 404}
			ページが見つかりません
		{:else}
			エラーが発生しました
		{/if}
	</h1>
	<p class="max-w-[400px] text-[14px] text-gv2-text-muted">
		{$page.error?.message || '予期しないエラーが発生しました。'}
	</p>
	<a
		href="/"
		class="mt-4 flex min-h-[44px] items-center rounded-full bg-[#1185FE] px-6 text-[15px] font-bold text-white no-underline touch-manipulation active:opacity-80"
	>
		ホームに戻る
	</a>
</div>
