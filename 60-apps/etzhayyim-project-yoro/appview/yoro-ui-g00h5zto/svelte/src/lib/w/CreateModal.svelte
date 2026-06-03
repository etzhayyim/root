<script lang="ts">
	interface Props {
		title: string;
		description?: string;
		placeholder?: string;
		confirmLabel?: string;
		busy?: boolean;
		error?: string;
		open?: boolean;
		onConfirm?: (value: string) => void;
		onCancel?: () => void;
	}

	let {
		title,
		description = '',
		placeholder = '',
		confirmLabel = '作成',
		busy = false,
		error = '',
		open = true,
		onConfirm,
		onCancel,
	}: Props = $props();

	let value = $state('');

	function handleConfirm() {
		if (!value.trim() || busy) return;
		onConfirm?.(value.trim());
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') { e.preventDefault(); handleConfirm(); }
		if (e.key === 'Escape') onCancel?.();
	}
</script>

{#if open}
	<div class="fixed inset-0 z-50 flex items-end justify-center bg-black/60" role="dialog" aria-modal="true">
		<div class="w-full max-w-[600px] rounded-t-2xl bg-[var(--gv2-bg-card,#1e1e1e)] p-4 pb-safe-bottom">
			<h2 class="mb-1 text-[17px] font-bold text-gv2-text-primary">{title}</h2>
			{#if description}
				<p class="mb-3 text-[13px] text-gv2-text-muted">{description}</p>
			{/if}
			<input
				class="mb-3 w-full rounded-xl bg-[var(--gv2-bg-input,#2a2a2a)] px-4 py-3 text-[15px] outline-none text-gv2-text-primary"
				{placeholder}
				bind:value
				onkeydown={handleKeydown}
			/>
			{#if error}
				<p class="mb-2 text-[13px] text-red-400">{error}</p>
			{/if}
			<div class="flex gap-2">
				<button
					type="button"
					class="flex-1 rounded-xl bg-[var(--gv2-bg-hover,#2f2f2f)] py-3 text-[15px] font-semibold text-gv2-text-primary touch-manipulation active:opacity-80"
					onclick={onCancel}
				>キャンセル</button>
				<button
					type="button"
					class="flex-1 rounded-xl bg-[#58CC02] py-3 text-[15px] font-bold text-white shadow-[0_3px_0_#3D8A00] touch-manipulation active:shadow-none active:translate-y-[3px] transition-all disabled:opacity-50"
					disabled={busy || !value.trim()}
					onclick={handleConfirm}
				>{busy ? '処理中…' : confirmLabel}</button>
			</div>
		</div>
	</div>
{/if}
