<script lang="ts">
	import { Avatar, Badge, Card } from '@etzhayyim/design-system';
	import { playClick } from '$lib/sound';
	import type { AgentInfo } from '$lib/auth';

	interface Props {
		agents: AgentInfo[];
		currentAgentId: string | null;
		onselect: (agent: AgentInfo) => void;
		oncreate: () => void;
	}

	const { agents, currentAgentId, onselect, oncreate }: Props = $props();
</script>

<div class="flex flex-col gap-3">
	<div class="flex items-center justify-between px-1">
		<h3 class="text-[15px] font-semibold text-gv2-text-primary">Your Agents</h3>
		<Badge value="{agents.length} agent{agents.length !== 1 ? 's' : ''}" variant="accent" />
	</div>

	{#if agents.length === 0}
		<Card class="border border-dashed border-gv2-border bg-gv2-bg-card p-6">
			<div class="flex flex-col items-center gap-3 text-center">
				<div class="text-[40px]">🤖</div>
				<p class="text-[14px] text-gv2-text-secondary">
					No agents yet. Create your first AI agent to get started.
				</p>
				<button
					type="button"
					class="rounded-2xl bg-[#58CC02] px-6 py-3 text-[15px] font-bold text-white
					       shadow-[0_4px_0_#3D8A00] touch-manipulation
					       active:shadow-none active:translate-y-[4px] transition-all duration-75"
					onclick={() => { playClick(); oncreate(); }}
				>
					Create Agent
				</button>
			</div>
		</Card>
	{:else}
		{#each agents as agent (agent.agentId)}
			<button
				type="button"
				class="flex w-full items-center gap-3 rounded-2xl p-3 text-left touch-manipulation transition-colors
				       {agent.agentId === currentAgentId
				         ? 'bg-[#58CC02]/15 border-2 border-[#58CC02]/40'
				         : 'bg-gv2-bg-card border-2 border-transparent active:bg-gv2-bg-hover'}"
				onclick={() => { playClick(); onselect(agent); }}
			>
				<Avatar
					src={agent.avatar}
					alt={agent.displayName}
					size="md"
				/>
				<div class="flex flex-1 flex-col gap-0.5 overflow-hidden">
					<div class="flex items-center gap-2">
						<span class="truncate text-[15px] font-semibold text-gv2-text-primary">
							{agent.displayName}
						</span>
						{#if agent.agentId === currentAgentId}
							<Badge value="Active" variant="success" />
						{/if}
					</div>
					<span class="truncate text-[12px] text-gv2-text-secondary">{agent.description}</span>
					<div class="flex items-center gap-1.5 mt-0.5">
						<Badge value={agent.agentType} variant="default" />
						<Badge value={agent.status} variant={agent.status === 'active' ? 'success' : 'warning'} />
						<span class="text-[11px] text-gv2-text-muted">{agent.capabilities.length} capabilities</span>
					</div>
				</div>
				<svg class="h-5 w-5 shrink-0 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 5l7 7-7 7" /></svg>
			</button>
		{/each}

		<!-- Create new agent button -->
		<button
			type="button"
			class="flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-gv2-border p-3
			       text-[14px] font-semibold text-gv2-text-muted touch-manipulation
			       active:text-gv2-text-primary active:border-gv2-text-muted transition-colors"
			onclick={() => { playClick(); oncreate(); }}
		>
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14" /></svg>
			Create New Agent
		</button>
	{/if}
</div>
