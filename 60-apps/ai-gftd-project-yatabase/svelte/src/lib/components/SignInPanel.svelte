<script lang="ts">
	import { Button, Input, Label, ErrorText, SupportText } from '@gftdcojp/design-system';
	import { apiKey, sessionError, sessionLoading, refreshSession } from '$lib/stores';

	let draft = $state($apiKey);

	async function save() {
		apiKey.set(draft.trim());
		await refreshSession();
	}
</script>

<div
	class="mx-auto max-w-xl rounded-2xl border border-gftd-border bg-gftd-card p-8 shadow-xl"
>
	<h1 class="text-2xl font-semibold text-gftd-text">Welcome to yatabase Studio</h1>
	<p class="mt-2 text-sm text-gftd-secondary">
		Paste the <code class="rounded bg-black/40 px-1 py-0.5 text-gftd-text"
			>sk_live_yata_*</code
		> API key you got when you signed up. It stays in your browser (localStorage); we don't
		send it anywhere except yatabase.gftd.ai itself.
	</p>

	<form
		class="mt-6 space-y-4"
		onsubmit={(e) => {
			e.preventDefault();
			void save();
		}}
	>
		<div>
			<Label for="apiKey" requirement={undefined}>API key</Label>
			<Input
				id="apiKey"
				type="password"
				placeholder="sk_live_yata_…"
				blockSize="lg"
				autocomplete="off"
				bind:value={draft}
				class="mt-1 w-full"
			/>
			{#if $sessionError}
				<ErrorText>{$sessionError}</ErrorText>
			{:else}
				<SupportText>Free tier: 1k req/day, no card. Get one at <code>/auth/v1/signup</code>.</SupportText>
			{/if}
		</div>

		<div class="flex items-center gap-3">
			<Button size="lg" variant="solid-fill" type="submit" aria-disabled={$sessionLoading}>
				{$sessionLoading ? 'Validating…' : 'Continue'}
			</Button>
			<a
				href="https://yatabase.gftd.ai/docs"
				class="text-sm text-gftd-accent underline underline-offset-4 hover:no-underline"
				>Read the docs</a
			>
		</div>
	</form>
</div>
