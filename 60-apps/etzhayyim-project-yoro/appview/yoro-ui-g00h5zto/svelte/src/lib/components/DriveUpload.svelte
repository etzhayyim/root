<!--
  DriveUpload — file upload using AppShell blob upload (Blake3 + multipart).
-->
<script lang="ts">
	import { Button } from '@etzhayyim/design-system';
	import { uploadBlob, getCurrentDID, createRecord } from '$lib/atproto-agent';

	const COLLECTION = 'com.etzhayyim.apps.yoro.driveItem';

	interface Props {
		onUploaded: () => void;
		parentId: string;
	}

	const { onUploaded, parentId }: Props = $props();

	let uploading = $state(false);
	let uploadError = $state('');

	async function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		const files = input.files;
		if (!files || files.length === 0) return;

		uploading = true;
		uploadError = '';
		try {
			const did = await getCurrentDID();
			if (!did) {
				uploadError = 'Not signed in';
				return;
			}

			for (const file of Array.from(files)) {
				const blobResult = await uploadBlob(file);
				const blobKey = (blobResult as any)?.blob?.ref?.['$link']
					?? (blobResult as any)?.blobKey
					?? (blobResult as any)?.key
					?? '';
				if (!blobKey) {
					console.warn('Upload returned no blobKey for', file.name);
					continue;
				}
				const now = new Date().toISOString();
				await createRecord({
					repo: did,
					collection: COLLECTION,
					record: {
						name: file.name,
						parentId,
						itemType: 'file',
						contentType: file.type || 'application/octet-stream',
						size: file.size,
						blobKey,
						status: 'active',
						createdAt: now,
						updatedAt: now,
					},
				});
			}
			onUploaded();
		} catch (e: any) {
			uploadError = e?.message ?? 'Upload failed';
			console.warn('Drive upload error:', e);
		} finally {
			uploading = false;
			const el = document.getElementById('drive-file-input') as HTMLInputElement;
			if (el) el.value = '';
		}
	}
</script>

<div class="flex gap-2">
	<input
		id="drive-file-input"
		type="file"
		multiple
		class="hidden"
		onchange={handleFileSelect}
		disabled={uploading}
	/>
	<Button
		variant="primary"
		size="sm"
		disabled={uploading}
		onclick={() => document.getElementById('drive-file-input')?.click()}
	>
		{uploading ? 'Uploading...' : 'Upload'}
	</Button>
</div>
{#if uploadError}
	<div class="mt-1 text-xs text-red-500">{uploadError}</div>
{/if}
