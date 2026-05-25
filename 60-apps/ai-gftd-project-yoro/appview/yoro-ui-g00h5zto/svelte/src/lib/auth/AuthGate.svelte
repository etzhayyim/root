<script lang="ts">
	import type { Snippet } from 'svelte';
	import { Button } from '@etzhayyim/design-system';
	import { signIn, signUp } from './passkey.js';

	interface Props {
		signInUrl?: string;
		signUpUrl?: string;
		title?: string;
		tagline?: string;
		actions?: Snippet;
		class?: string;
	}

	const {
		signInUrl,
		signUpUrl,
		title = 'etzhayyim',
		tagline = 'AI Agent Platform — Register and manage your AI agents',
		actions,
		class: className = '',
	}: Props = $props();

	function goToSignIn() {
		if (!signInUrl) return;
		void signIn().catch((_err) => {
			const redirectUrl = encodeURIComponent(window.location.href);
			window.location.href = `${signInUrl}?redirect_url=${redirectUrl}`;
		});
	}

	function goToSignUp() {
		if (!signUpUrl) return;
		void signUp().catch((_err) => {
			const redirectUrl = encodeURIComponent(window.location.href);
			window.location.href = `${signUpUrl}?redirect_url=${redirectUrl}`;
		});
	}
</script>

<div class={`flex h-screen w-screen items-center justify-center bg-[var(--gv2-bg-primary,#1a1a1a)] ${className}`}>
	<div class="flex w-full max-w-[400px] flex-col items-center gap-8 px-6 py-12">
		<div class="text-center">
			<div class="mb-3 text-5xl font-bold tracking-[0.5rem] text-[var(--gv2-accent,#0031d8)]">{title}</div>
			<div class="text-sm tracking-[0.5px] text-[var(--gv2-text-muted,#666666)]">{tagline}</div>
		</div>

		<div class="flex w-full flex-col gap-3">
			<Button variant="solid-fill" size="lg" onclick={goToSignIn} class="w-full justify-center">Agent Login</Button>
			<Button variant="outline" size="lg" onclick={goToSignUp} class="w-full justify-center">Create Agent</Button>
		</div>

		{#if actions}
			{@render actions()}
		{/if}

		<div class="text-xs text-[var(--gv2-text-muted,#666666)]">
			<span>Powered by etzhayyim</span>
		</div>
	</div>
</div>
