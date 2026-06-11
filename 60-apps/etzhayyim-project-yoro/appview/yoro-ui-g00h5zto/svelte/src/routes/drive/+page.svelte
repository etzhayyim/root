<!--
  /drive — File management integrated into yoro messenger.
  AT Protocol CQRS: createRecord/listRecords/deleteRecord on com.etzhayyim.apps.yoro.driveItem.
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { isSignedIn } from '$lib/auth';
	import { Button } from '@etzhayyim/design-system';
	import { fade } from 'svelte/transition';
	import { driveStore, type DriveItem } from '$lib/drive-store.svelte.js';
	import DriveFileList from '$lib/components/DriveFileList.svelte';
	import DriveUpload from '$lib/components/DriveUpload.svelte';

	const drive = driveStore();

	let showNewFolder = $state(false);
	let newFolderName = $state('');
	let creating = $state(false);
	let searchQuery = $state('');
	let searchMode = $state(false);

	onMount(() => {
		if ($isSignedIn) {
			drive.loadItems();
		}
	});

	$effect(() => {
		if ($isSignedIn && drive.items.length === 0 && !drive.loading) {
			drive.loadItems();
		}
	});

	async function handleCreateFolder() {
		if (!newFolderName.trim()) return;
		creating = true;
		try {
			await drive.createFolder(newFolderName.trim());
			newFolderName = '';
			showNewFolder = false;
		} catch (e: any) {
			console.warn('Create folder error:', e);
		} finally {
			creating = false;
		}
	}

	function handleOpenFolder(item: DriveItem) {
		searchMode = false;
		searchQuery = '';
		drive.navigateToFolder(item.rkey, item.name);
	}

	async function handleDeleteItem(item: DriveItem) {
		if (!confirm(`Delete "${item.name}"?`)) return;
		await drive.deleteItem(item.rkey);
	}

	async function handleSearch() {
		if (!searchQuery.trim()) {
			searchMode = false;
			drive.loadItems();
			return;
		}
		searchMode = true;
		await drive.searchItems(searchQuery.trim());
	}
</script>

<svelte:head>
	<title>Drive — YORO</title>
</svelte:head>

<div class="mx-auto max-w-[600px] px-4 py-4">
	{#if !$isSignedIn}
		<div class="py-20 text-center" in:fade={{ duration: 300 }}>
			<div class="flex mx-auto h-16 w-16 items-center justify-center rounded-full bg-[#1185FE]/10">
				<svg class="h-8 w-8 text-[#1185FE]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
				</svg>
			</div>
			<h2 class="mt-4 text-[17px] font-bold text-gv2-text-primary">Drive</h2>
			<p class="mt-1 text-[14px] text-gv2-text-muted">Sign in to access your files</p>
		</div>
	{:else}
		<!-- Header -->
		<div class="mb-4 flex items-center justify-between">
			<h1 class="text-lg font-bold text-gv2-text-primary">Drive</h1>
			<div class="flex gap-2">
				<Button variant="outline" size="sm" onclick={() => (showNewFolder = !showNewFolder)}>
					New Folder
				</Button>
				<DriveUpload parentId={drive.currentParentId} onUploaded={() => drive.loadItems()} />
			</div>
		</div>

		<!-- Search -->
		<div class="mb-3">
			<input
				type="text"
				placeholder="Search files..."
				class="w-full rounded-xl border border-gv2-border/50 bg-gv2-bg-secondary px-3 py-2 text-sm text-gv2-text-primary placeholder:text-gv2-text-muted focus:outline-none focus:ring-2 focus:ring-[#1185FE]/40"
				bind:value={searchQuery}
				onkeydown={(e) => e.key === 'Enter' && handleSearch()}
			/>
		</div>

		<!-- Breadcrumbs -->
		{#if !searchMode}
			<div class="mb-3 flex items-center gap-1 overflow-x-auto text-sm text-gv2-text-muted">
				{#each drive.breadcrumbs as crumb, i (crumb.id)}
					{#if i > 0}
						<span class="text-gv2-text-muted/50">/</span>
					{/if}
					<button
						type="button"
						class="whitespace-nowrap transition-colors active:text-[#1185FE] touch-manipulation"
						onclick={() => drive.navigateToFolder(crumb.id, crumb.name)}
					>
						{crumb.name}
					</button>
				{/each}
			</div>
		{/if}

		<!-- New Folder Input -->
		{#if showNewFolder}
			<div class="mb-3 flex gap-2" in:fade={{ duration: 150 }}>
				<input
					type="text"
					placeholder="Folder name"
					class="flex-1 rounded-xl border border-gv2-border/50 bg-gv2-bg-secondary px-3 py-2 text-sm text-gv2-text-primary placeholder:text-gv2-text-muted focus:outline-none focus:ring-2 focus:ring-[#1185FE]/40"
					bind:value={newFolderName}
					onkeydown={(e) => e.key === 'Enter' && handleCreateFolder()}
				/>
				<Button variant="solid-fill" size="sm" disabled={creating} onclick={handleCreateFolder}>
					{creating ? '...' : 'Create'}
				</Button>
			</div>
		{/if}

		<!-- Error -->
		{#if drive.error}
			<div class="mb-3 text-sm text-red-500">{drive.error}</div>
		{/if}

		<!-- Loading -->
		{#if drive.loading}
			<div class="py-8 text-center text-gv2-text-muted">Loading...</div>
		{:else}
			<DriveFileList
				items={drive.items}
				onOpenFolder={handleOpenFolder}
				onDeleteItem={handleDeleteItem}
			/>
		{/if}
	{/if}
</div>
