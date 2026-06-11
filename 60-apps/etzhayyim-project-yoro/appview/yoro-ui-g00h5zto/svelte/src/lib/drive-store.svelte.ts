/**
 * Drive state management — Svelte 5 runes.
 * Data access via AT Protocol Event Stream (createRecord/listRecords/deleteRecord).
 */

	import { createRecord, listRecords, deleteRecord, getCurrentDID } from '$lib/atproto-agent';

const COLLECTION = 'com.etzhayyim.apps.yoro.driveItem';

export interface DriveItem {
	rkey: string;
	name: string;
	parentId: string;
	itemType: 'file' | 'folder';
	contentType: string;
	size: number;
	blobKey: string;
	status: string;
	createdAt: string;
	updatedAt: string;
}

let items = $state<DriveItem[]>([]);
let currentParentId = $state('root');
let loading = $state(false);
let error = $state('');
let breadcrumbs = $state<{ id: string; name: string }[]>([{ id: 'root', name: 'Drive' }]);

function recordToItem(rec: any): DriveItem {
	const v = rec.value ?? rec;
	return {
		rkey: rec.uri?.split('/').pop() ?? rec.rkey ?? '',
		name: v.name ?? '',
		parentId: v.parentId ?? 'root',
		itemType: v.itemType ?? 'file',
		contentType: v.contentType ?? '',
		size: v.size ?? 0,
		blobKey: v.blobKey ?? '',
		status: v.status ?? 'active',
		createdAt: v.createdAt ?? '',
		updatedAt: v.updatedAt ?? '',
	};
}

export function driveStore() {
	async function loadItems(parentId?: string) {
		const pid = parentId ?? currentParentId;
		loading = true;
		error = '';
		try {
			const did = await getCurrentDID();
			if (!did) {
				error = 'Not signed in';
				return;
			}
			const res = await listRecords(did, COLLECTION, { limit: 100 });
			const records = (res as any)?.records ?? [];
			items = records
				.map(recordToItem)
				.filter((it: DriveItem) => it.parentId === pid && it.status !== 'deleted');
			currentParentId = pid;
		} catch (e: any) {
			error = e?.message ?? 'Failed to load';
			console.warn('drive loadItems error:', e);
		} finally {
			loading = false;
		}
	}

	async function navigateToFolder(folderId: string, folderName: string) {
		if (folderId === 'root') {
			breadcrumbs = [{ id: 'root', name: 'Drive' }];
		} else {
			const idx = breadcrumbs.findIndex((b) => b.id === folderId);
			if (idx >= 0) {
				breadcrumbs = breadcrumbs.slice(0, idx + 1);
			} else {
				breadcrumbs = [...breadcrumbs, { id: folderId, name: folderName }];
			}
		}
		await loadItems(folderId);
	}

	async function createFolder(name: string) {
		const did = await getCurrentDID();
		if (!did) return;
		const now = new Date().toISOString();
		const res = await createRecord(did, COLLECTION, {
				name,
				parentId: currentParentId,
				itemType: 'folder',
				contentType: '',
				size: 0,
				blobKey: '',
				status: 'active',
				createdAt: now,
				updatedAt: now,
			});
		await loadItems();
		return res;
	}

	async function uploadFile(name: string, blobKey: string, contentType: string, size: number) {
		const did = await getCurrentDID();
		if (!did) return;
		const now = new Date().toISOString();
		const res = await createRecord(did, COLLECTION, {
				name,
				parentId: currentParentId,
				itemType: 'file',
				contentType,
				size,
				blobKey,
				status: 'active',
				createdAt: now,
				updatedAt: now,
			});
		await loadItems();
		return res;
	}

	async function deleteItem(rkey: string) {
		const did = await getCurrentDID();
		if (!did) return;
		await deleteRecord(did, COLLECTION, rkey);
		await loadItems();
	}

	async function searchItems(query: string) {
		loading = true;
		error = '';
		try {
			const did = await getCurrentDID();
			if (!did) {
				error = 'Not signed in';
				return;
			}
			const res = await listRecords(did, COLLECTION, { limit: 100 });
			const records = (res as any)?.records ?? [];
			const q = query.toLowerCase();
			items = records
				.map(recordToItem)
				.filter((it: DriveItem) => it.status !== 'deleted' && it.name.toLowerCase().includes(q));
		} catch (e: any) {
			error = e?.message ?? 'Search failed';
			console.warn('drive search error:', e);
		} finally {
			loading = false;
		}
	}

	return {
		get items() { return items; },
		get currentParentId() { return currentParentId; },
		get loading() { return loading; },
		get error() { return error; },
		get breadcrumbs() { return breadcrumbs; },
		loadItems,
		navigateToFolder,
		createFolder,
		uploadFile,
		deleteItem,
		searchItems,
	};
}
