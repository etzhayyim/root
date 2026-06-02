<script lang="ts">
	import { getActiveJobCount } from '$lib/stores/job-store.svelte';

	const baseUrl = typeof window !== 'undefined' && window.location.port === '1421'
		? 'http://localhost:8081' : '';

	let health = $state<{
		status: string;
		model: string;
		device: string;
		'model_loaded': boolean;
		'load_time_ms': number;
	}>({ status: 'loading', model: '', device: '', 'model_loaded': false, 'load_time_ms': 0 });

	let showTooltip = $state(false);

	function unsupportedHealthRPC(): never {
		throw new Error(
			`[UNSUPPORTED_RPC] ${baseUrl}/api/image-gen-health: connect-web descriptor/client is not available for this endpoint; fetch fallback is disabled`
		);
	}

	async function checkHealth() {
		try {
