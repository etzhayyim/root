<script lang="ts">
	import YoroAuthGate from '$lib/components/YoroAuthGate.svelte';
	import NondualExperienceGuide from '$lib/components/NondualExperienceGuide.svelte';
	import { headerCacaoSignIn } from '$lib/auth';

	// ADR-2606061500: onboarding sign-in is the same-origin passkey → CACAO
	// ceremony — no authn.etzhayyim.com hop. `onAuth` overrides the legacy URLs.
	async function onAuth() {
		await headerCacaoSignIn();
	}

	// Charter §1.17.6 (ADR-2606071009): before the auth / vow gate, commend the
	// experiential core of 回心 (direct experience of 自他非分離). The seeker proceeds
	// to YoroAuthGate from the guide.
	let phase = $state<'guide' | 'auth'>('guide');
</script>

{#if phase === 'guide'}
	<NondualExperienceGuide onContinue={() => (phase = 'auth')} />
{:else}
	<YoroAuthGate {onAuth} />
{/if}
