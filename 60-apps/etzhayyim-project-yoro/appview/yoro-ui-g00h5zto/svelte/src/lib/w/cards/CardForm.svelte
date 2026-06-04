<script lang="ts">
	import { Button, Toggle } from '@etzhayyim/design-system';
	import type { CardFormPayload } from '../w-types.js';

	interface Props {
		payload: CardFormPayload;
		onAction?: (action: string, data?: Record<string, unknown>) => void;
	}

	let { payload, onAction }: Props = $props();
	let values = $state<Record<string, string>>({});

	function handleSubmit() {
		onAction?.(payload.action, values);
	}
</script>

<div class="rounded-2xl bg-gv2-bg-card border border-gv2-border/20 p-4 space-y-3">
	{#if payload.title}
		<p class="text-[15px] font-bold text-gv2-text-primary">{payload.title}</p>
	{/if}
	{#each payload.fields as field (field.name)}
		<div class="space-y-1">
			<label class="text-[12px] font-semibold uppercase tracking-wider text-gv2-text-muted" for="card-{field.name}">
				{field.label}{field.required ? ' *' : ''}
			</label>
			{#if field.type === 'select' && field.options}
				<select
					id="card-{field.name}"
					class="w-full min-h-[44px] rounded-xl bg-gv2-bg-input px-3 py-2 text-[14px] text-gv2-text-primary border border-gv2-border outline-none"
					value={values[field.name] ?? field.value ?? ''}
					onchange={(e) => { values[field.name] = e.currentTarget.value; }}
				>
					{#each field.options as opt}<option value={opt.value}>{opt.label}</option>{/each}
				</select>
			{:else if field.type === 'textarea'}
				<textarea
					id="card-{field.name}"
					class="w-full min-h-[88px] rounded-xl bg-gv2-bg-input px-3 py-2 text-[14px] text-gv2-text-primary border border-gv2-border outline-none resize-none"
					placeholder={field.placeholder ?? ''}
					value={values[field.name] ?? field.value ?? ''}
					oninput={(e) => { values[field.name] = e.currentTarget.value; }}
				></textarea>
			{:else if field.type === 'toggle'}
				<Toggle
					checked={values[field.name] === 'true'}
					onchange={(checked) => { values[field.name] = String(checked); }}
				/>
			{:else}
				<input
					id="card-{field.name}"
					type={field.type}
					class="w-full min-h-[44px] rounded-xl bg-gv2-bg-input px-3 py-2 text-[14px] text-gv2-text-primary border border-gv2-border outline-none"
					placeholder={field.placeholder ?? ''}
					value={values[field.name] ?? field.value ?? ''}
					oninput={(e) => { values[field.name] = e.currentTarget.value; }}
				/>
			{/if}
		</div>
	{/each}
	<Button variant="solid-fill" size="md" class="w-full" onclick={handleSubmit}>
		{payload.submitLabel ?? 'Submit'}
	</Button>
</div>
