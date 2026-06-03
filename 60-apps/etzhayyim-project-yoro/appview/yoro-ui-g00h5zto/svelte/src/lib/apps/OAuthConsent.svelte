<script lang="ts">
	import { cn } from '@etzhayyim/design-system';
	import { KNOWN_SCOPES, scopeDescription, installApp } from './installed-apps.js';

	interface Props {
		/** Whether the consent dialog is open. */
		open: boolean;
		/** App ID to install. */
		appId: string;
		/** App display name. */
		appName: string;
		/** App icon (emoji or URL). */
		appIcon: string;
		/** App URL. */
		appHref: string;
		/** Scopes the app requests. If empty, defaults to profile:read. */
		requestedScopes?: string[];
		/** Called when user completes or cancels the flow. */
		onclose: (result: { installed: boolean; installationId?: string }) => void;
	}

	let {
		open = $bindable(false),
		appId,
		appName,
		appIcon,
		appHref,
		requestedScopes = ['profile:read'],
		onclose
	}: Props = $props();

	let grantedScopes = $state<Set<string>>(new Set());
	let installing = $state(false);

	// Reset grants when dialog opens
	$effect(() => {
		if (open) {
			grantedScopes = new Set(requestedScopes);
		}
	});

	function toggleScope(scopeId: string) {
		const next = new Set(grantedScopes);
		if (next.has(scopeId)) {
			next.delete(scopeId);
		} else {
			next.add(scopeId);
		}
		grantedScopes = next;
	}

	async function handleInstall() {
		installing = true;
		const result = await installApp(appId, appName, appIcon, appHref, [...grantedScopes]);
		installing = false;
		open = false;
		onclose({ installed: result.ok, installationId: result.installationId });
	}

	function handleCancel() {
		open = false;
		onclose({ installed: false });
	}

	let scopeDetails = $derived(
		requestedScopes.map((id) => ({
			id,
			label: KNOWN_SCOPES.find((s) => s.id === id)?.label ?? id,
			description: scopeDescription(id),
			granted: grantedScopes.has(id)
		}))
	);
</script>

{#if open}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 z-[9998] bg-black/40"
		onclick={handleCancel}
		role="presentation"
	></div>

	<!-- Consent dialog (bottom sheet style on mobile) -->
	<div class="fixed bottom-0 left-0 right-0 z-[9999] flex justify-center safe-area-bottom">
		<div class="w-full max-w-[500px] rounded-t-2xl bg-white shadow-[0_-4px_24px_rgba(0,0,0,0.15)]">
			<!-- Drag handle -->
			<div class="flex justify-center pt-3 pb-1">
				<div class="w-10 h-1 rounded-full bg-gray-300"></div>
			</div>

			<!-- App info -->
			<div class="flex items-center gap-3 px-5 pb-4">
				<span class="flex items-center justify-center w-12 h-12 rounded-xl bg-etzhayyim-hover text-2xl">
					{appIcon}
				</span>
				<div>
					<h2 class="text-[17px] font-bold text-etzhayyim-text">{appName}</h2>
					<p class="text-[13px] text-etzhayyim-muted">wants access to your account</p>
				</div>
			</div>

			<!-- Scopes list -->
			<div class="px-5 pb-4">
				<p class="text-[12px] font-semibold text-etzhayyim-muted uppercase tracking-wider mb-3">Permissions</p>
				<div class="flex flex-col gap-1">
					{#each scopeDetails as scope}
						<button
							class={cn(
								'flex items-center gap-3 w-full px-4 py-3 rounded-xl text-left transition-colors touch-manipulation',
								scope.granted
									? 'bg-green-50 border border-green-200'
									: 'bg-gray-50 border border-gray-200'
							)}
							onclick={() => toggleScope(scope.id)}
						>
							<!-- Checkbox -->
							<div class={cn(
								'flex items-center justify-center w-5 h-5 rounded border-2 transition-colors shrink-0',
								scope.granted
									? 'bg-etzhayyim-accent border-etzhayyim-accent'
									: 'bg-white border-gray-300'
							)}>
								{#if scope.granted}
									<svg class="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
										<polyline points="20 6 9 17 4 12" />
									</svg>
								{/if}
							</div>
							<div class="min-w-0 flex-1">
								<p class="text-[14px] font-medium text-etzhayyim-text">{scope.label}</p>
								<p class="text-[12px] text-etzhayyim-muted">{scope.description}</p>
							</div>
						</button>
					{/each}
				</div>
			</div>

			<!-- Actions -->
			<div class="flex gap-3 px-5 pb-5">
				<button
					class="flex-1 py-3 rounded-xl border border-etzhayyim-border text-[15px] font-medium text-etzhayyim-secondary active:bg-etzhayyim-hover transition-colors touch-manipulation min-h-[48px]"
					onclick={handleCancel}
					disabled={installing}
				>
					Cancel
				</button>
				<button
					class={cn(
						'flex-1 py-3 rounded-xl text-[15px] font-medium text-white transition-colors touch-manipulation min-h-[48px]',
						installing ? 'bg-etzhayyim-accent/60' : 'bg-etzhayyim-accent active:bg-etzhayyim-accent/80'
					)}
					onclick={handleInstall}
					disabled={installing}
				>
					{installing ? 'Installing...' : 'Allow & Install'}
				</button>
			</div>
		</div>
	</div>
{/if}
