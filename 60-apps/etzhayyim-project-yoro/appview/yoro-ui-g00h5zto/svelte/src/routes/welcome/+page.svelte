<script lang="ts">
	import YoroAuthGate from '$lib/components/YoroAuthGate.svelte';
	import { headerCacaoSignIn } from '$lib/auth';

	// ADR-2606061500: onboarding sign-in is the same-origin passkey → CACAO
	// ceremony — no authn.etzhayyim.com hop. `onAuth` overrides the legacy URLs.
	async function onAuth() {
		await headerCacaoSignIn();
	}
</script>

<YoroAuthGate {onAuth} />
