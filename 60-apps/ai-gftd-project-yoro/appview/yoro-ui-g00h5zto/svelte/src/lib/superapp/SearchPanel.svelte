<script lang="ts">
	import SearchActors from '../w/SearchActors.svelte';
	import { convos } from '../w/convo-store.svelte.js';

	interface Props {
		onClose?: () => void;
	}
	let { onClose }: Props = $props();

	function handleSelectMessage(convoId: string, _rkey: string) {
		if (convoId) convos.setActiveConvo(convoId);
		onClose?.();
	}

	function handleSelectConvo(convoId: string) {
		if (convoId) convos.setActiveConvo(convoId);
		onClose?.();
	}

	function handleSelectPage(url: string) {
		if (url) window.open(url, '_blank', 'noreferrer');
	}
</script>

<SearchActors
	onSelectMessage={handleSelectMessage}
	onSelectConvo={handleSelectConvo}
	onSelectPage={handleSelectPage}
/>
