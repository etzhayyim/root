<script lang="ts">
	import { Button } from '@etzhayyim/design-system';
	import type { CardConfirmationPayload } from '../w-types.js';

	interface Props {
		payload: CardConfirmationPayload;
		onAction?: (action: string) => void;
	}

	let { payload, onAction }: Props = $props();
</script>

<div class="rounded-2xl bg-gv2-bg-card border {payload.destructive ? 'border-red-500/30' : 'border-gv2-border/20'} p-4 space-y-3">
	<p class="text-[15px] font-bold text-gv2-text-primary">{payload.title}</p>
	<p class="text-[14px] text-gv2-text-muted leading-relaxed">{payload.message}</p>
	<div class="flex gap-2">
		<Button
			variant="outline"
			size="sm"
			class="flex-1"
			onclick={() => onAction?.('cancel')}
		>
			{payload.cancelLabel ?? 'Cancel'}
		</Button>
		<Button
			variant="solid-fill"
			size="sm"
			class="flex-1 {payload.destructive ? '!bg-red-500 !shadow-none' : ''}"
			onclick={() => onAction?.(payload.action)}
		>
			{payload.confirmLabel}
		</Button>
	</div>
</div>
