<!--
  DriveFileList — file/folder list using UIKit components.
-->
<script lang="ts">
	import type { DriveItem } from '$lib/drive-store.svelte.js';

	interface Props {
		items: DriveItem[];
		onOpenFolder: (item: DriveItem) => void;
		onDeleteItem: (item: DriveItem) => void;
	}

	const { items, onOpenFolder, onDeleteItem }: Props = $props();

	function formatSize(bytes: number): string {
		if (bytes === 0) return '-';
		const units = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + ' ' + units[i];
	}

	function fileIcon(item: DriveItem): string {
		if (item.itemType === 'folder') return '\u{1F4C1}';
		const ct = item.contentType;
		if (ct.startsWith('image/')) return '\u{1F5BC}\uFE0F';
		if (ct.startsWith('video/')) return '\u{1F3AC}';
		if (ct.startsWith('audio/')) return '\u{1F3B5}';
		if (ct.includes('pdf')) return '\u{1F4D1}';
		if (ct.includes('spreadsheet') || ct.includes('csv')) return '\u{1F4CA}';
		if (ct.includes('document') || ct.includes('word')) return '\u{1F4DD}';
		return '\u{1F4C4}';
	}
</script>

{#if items.length === 0}
	<div class="py-12 text-center text-gv2-text-muted">No items</div>
{:else}
	<div class="flex flex-col gap-1">
		{#each items as item (item.rkey || item.name)}
			<div
				class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left transition-colors active:bg-gv2-bg-hover/40 touch-manipulation"
				role="button"
				tabindex="0"
				onclick={() => item.itemType === 'folder' ? onOpenFolder(item) : null}
				onkeydown={(e) => { if (e.key === 'Enter' && item.itemType === 'folder') onOpenFolder(item); }}
			>
				<span class="shrink-0 text-2xl">{fileIcon(item)}</span>
				<div class="min-w-0 flex-1">
					<div class="truncate text-sm font-medium text-gv2-text-primary">{item.name}</div>
					<div class="text-xs text-gv2-text-muted">
						{#if item.itemType === 'file'}
							{formatSize(item.size)} &middot; {item.contentType.split('/').pop()}
						{:else}
							Folder
						{/if}
					</div>
				</div>
				<button
					type="button"
					class="shrink-0 rounded-lg p-2 text-gv2-text-muted transition-colors active:bg-red-500/10 active:text-red-500 touch-manipulation"
					onclick={(e) => { e.stopPropagation(); onDeleteItem(item); }}
					aria-label="Delete {item.name}"
				>
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M3 6h18" /><path d="M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2" /><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6" />
					</svg>
				</button>
			</div>
		{/each}
	</div>
{/if}
